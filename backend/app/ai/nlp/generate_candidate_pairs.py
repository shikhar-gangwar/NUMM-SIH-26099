"""
CPU-Safe Candidate-Pair Generator for SIH 26099 CPSE Material Matching
Prioritizing Cross-Organisation Semantic Candidates (IOCL ↔ OIL ↔ NTPC)

Usage:
    python -m app.ai.nlp.generate_candidate_pairs --limit 100
"""

import os
import sys

# Conservative CPU thread limits MUST be set before PyTorch import
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import torch

try:
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
except Exception:
    pass

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

# Defer imports of NLP and Embedding pipeline modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from app.ai.nlp.pipeline import nlp_pipeline
from app.ai.embeddings.embedder import get_cpu_embedder, compute_cosine_similarity
from app.ai.embeddings.cache import embedding_cache

MAX_DESCRIPTIONS = 100
DEFAULT_LIMIT = 100


def parse_args():
    parser = argparse.ArgumentParser(
        description="CPU-safe candidate-pair generator for SIH 26099 CPSE material matching."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Number of unique descriptions to process (default: {DEFAULT_LIMIT}, max: {MAX_DESCRIPTIONS})"
    )
    args = parser.parse_args()
    if args.limit > MAX_DESCRIPTIONS:
        print(f"[ERROR] Requested --limit {args.limit} exceeds maximum allowed limit of {MAX_DESCRIPTIONS}. Refusing execution.")
        sys.exit(1)
    return args


def locate_dataset_csv() -> Path | None:
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parents[2]

    candidate_paths = [
        project_root / "backend" / "data" / "real" / "material_description_corpus.csv",
        project_root / "data" / "real" / "material_description_corpus.csv",
        Path("backend/data/real/material_description_corpus.csv").resolve(),
        Path("data/real/material_description_corpus.csv").resolve(),
    ]

    for path in candidate_paths:
        if path.exists() and path.is_file():
            return path
    return None


def evaluate_feature_matches(attr_a: Dict[str, Any], attr_b: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    """
    Evaluates explicit comparison flags and overall attribute_status.
    Returns: (product_type_match, standard_match, measurement_match, uom_match, attribute_status)
    """
    # 1. Product Type Match
    pt_a = attr_a.get("product_type")
    pt_b = attr_b.get("product_type")
    if pt_a and pt_b:
        product_type_match = "MATCH" if str(pt_a).upper() == str(pt_b).upper() else "MISMATCH"
    else:
        product_type_match = "UNKNOWN"

    # 2. Standard Match
    st_a = set(attr_a.get("standards", []))
    st_b = set(attr_b.get("standards", []))
    if st_a and st_b:
        standard_match = "MATCH" if st_a.intersection(st_b) else "MISMATCH"
    elif st_a or st_b:
        standard_match = "MISMATCH"
    else:
        standard_match = "UNKNOWN"

    # 3. UOM Match
    uom_a = attr_a.get("uom")
    uom_b = attr_b.get("uom")
    if uom_a and uom_b:
        uom_match = "MATCH" if str(uom_a).upper() == str(uom_b).upper() else "MISMATCH"
    else:
        uom_match = "UNKNOWN"

    # 4. Measurement Match
    meas_a = attr_a.get("measurements", [])
    meas_b = attr_b.get("measurements", [])

    if meas_a and meas_b:
        units_a = {m["unit"]: float(m["value"]) for m in meas_a if isinstance(m, dict) and "unit" in m and "value" in m}
        units_b = {m["unit"]: float(m["value"]) for m in meas_b if isinstance(m, dict) and "unit" in m and "value" in m}
        shared_units = set(units_a.keys()).intersection(set(units_b.keys()))

        if shared_units:
            has_conflict = False
            has_match = False
            for u in shared_units:
                if abs(units_a[u] - units_b[u]) < 1e-5:
                    has_match = True
                else:
                    has_conflict = True
            if has_conflict:
                measurement_match = "CONFLICT"
            elif has_match:
                measurement_match = "MATCH"
            else:
                measurement_match = "PARTIAL"
        else:
            measurement_match = "PARTIAL"
    elif meas_a or meas_b:
        measurement_match = "PARTIAL"
    else:
        measurement_match = "UNKNOWN"

    # 5. Overall Attribute Status
    conflicts = []
    if measurement_match == "CONFLICT":
        conflicts.append("measurement_conflict")
    if standard_match == "MISMATCH":
        conflicts.append("standard_mismatch")
    if product_type_match == "MISMATCH":
        conflicts.append("product_type_mismatch")

    # Check other shared top-level keys like grade, pressure_class, material, size
    shared_keys = set(attr_a.keys()).intersection(set(attr_b.keys())) - {"measurements", "standards", "product_type", "material_type"}
    for k in shared_keys:
        val_a = str(attr_a[k]).strip().lower()
        val_b = str(attr_b[k]).strip().lower()
        if val_a != val_b:
            conflicts.append(k)

    if conflicts:
        attribute_status = "CONFLICT"
    elif not attr_a and not attr_b:
        attribute_status = "UNKNOWN"
    elif measurement_match in ("MATCH", "UNKNOWN") and standard_match in ("MATCH", "UNKNOWN") and product_type_match in ("MATCH", "UNKNOWN"):
        attribute_status = "COMPATIBLE"
    else:
        attribute_status = "PARTIAL"

    return product_type_match, standard_match, measurement_match, uom_match, attribute_status


def select_candidate_records(df: pd.DataFrame, limit: int) -> List[Dict[str, Any]]:
    """
    Select candidate records balancing across all 3 organizations (OIL, NTPC, IOCL).
    """
    valid_df = df[df['description'].fillna('').astype(str).str.strip() != ''].copy()

    # Priority 1: Pick cross-organization exact anchor descriptions
    desc_org_counts: pd.Series = pd.Series(valid_df.groupby('description')['organization'].nunique())
    cross_org_descriptions: List[str] = [str(x) for x in desc_org_counts[desc_org_counts > 1].index.tolist()]


    selected_records: List[Dict[str, Any]] = []
    seen_descriptions = set()

    for desc in cross_org_descriptions:
        if len(selected_records) >= limit:
            break
        matching_rows = valid_df[valid_df['description'] == desc]
        for _, row in matching_rows.iterrows():
            if len(selected_records) >= limit:
                break
            key = (row['organization'], str(row['description']).strip())
            if key not in seen_descriptions:
                seen_descriptions.add(key)
                selected_records.append({
                    "corpus_id": row.get('corpus_id', f"M_{len(selected_records):06d}"),
                    "organization": str(row.get('organization', 'UNSPECIFIED')),
                    "raw_description": str(row['description']).strip()
                })

    # Priority 2: Round-robin sampling across available organizations
    if len(selected_records) < limit:
        orgs = ['Oil India Limited', 'NTPC Limited', 'Indian Oil Corporation Limited']
        remaining_df = valid_df[~valid_df['description'].isin([r['raw_description'] for r in selected_records])]
        org_dfs = {org: remaining_df[remaining_df['organization'] == org] for org in orgs}
        org_iters = {org: org_dfs[org].iterrows() for org in orgs}

        while len(selected_records) < limit:
            added_any = False
            for org in orgs:
                if len(selected_records) >= limit:
                    break
                try:
                    _, row = next(org_iters[org])
                    raw_desc = str(row['description']).strip()
                    key = (row['organization'], raw_desc)
                    if key not in seen_descriptions:
                        seen_descriptions.add(key)
                        selected_records.append({
                            "corpus_id": row.get('corpus_id', f"M_{len(selected_records):06d}"),
                            "organization": str(row.get('organization', 'UNSPECIFIED')),
                            "raw_description": raw_desc
                        })
                        added_any = True
                except StopIteration:
                    continue
            if not added_any:
                break

    return selected_records[:limit]


def run_candidate_generation():
    args = parse_args()
    limit = args.limit

    print("==================================================")
    print("SIH 26099 CROSS-ORGANISATION CANDIDATE PAIR GENERATOR")
    print("==================================================")
    print()

    csv_path = locate_dataset_csv()
    if csv_path is None:
        print("[ERROR] Dataset CSV not found.")
        sys.exit(1)

    print(f"Dataset             : {csv_path}")
    print(f"Limit               : {limit} unique descriptions (MAX={MAX_DESCRIPTIONS})")
    print(f"Model               : sentence-transformers/all-MiniLM-L6-v2")
    print(f"Embedding Dimension : 384")
    print(f"CPU Config          : OMP_NUM_THREADS=1, MKL_NUM_THREADS=1, torch=1, interop=1")
    print()

    # Load dataset
    df = pd.read_csv(csv_path, low_memory=False)

    # Select candidate records
    records = select_candidate_records(df, limit)
    total_processed = len(records)
    orgs_represented = sorted(list(set(r['organization'] for r in records)))

    print(f"Descriptions selected       : {total_processed}")
    print(f"Organizations represented   : {', '.join(orgs_represented)}")
    print()

    # Process with NLP Pipeline & generate embeddings
    embedder = get_cpu_embedder()
    processed_items = []

    for r in records:
        pipeline_res = nlp_pipeline.process(r['raw_description'])
        text_hash = pipeline_res['text_hash']
        norm_text = pipeline_res['normalized_text']

        # Embedding cache check
        cached_entry = embedding_cache.get(text_hash)
        if cached_entry is not None and "embedding" in cached_entry:
            vec = cached_entry["embedding"]
        else:
            vec = embedder.embed_single(norm_text)
            embedding_cache.put(text_hash, norm_text, vec, material_id=r['corpus_id'])

        processed_items.append({
            "corpus_id": r['corpus_id'],
            "organization": r['organization'],
            "raw_description": r['raw_description'],
            "normalized_text": norm_text,
            "extracted_attributes": pipeline_res['extracted_attributes'],
            "text_hash": text_hash,
            "vector": vec
        })

    # Generate candidate pairs
    all_pairs = []
    n = len(processed_items)

    for i in range(n):
        for j in range(i + 1, n):
            item_a = processed_items[i]
            item_b = processed_items[j]

            # Filter out identical raw descriptions OR identical normalized descriptions
            if item_a['raw_description'] == item_b['raw_description'] or \
               item_a['normalized_text'] == item_b['normalized_text']:
                continue

            sim_score = compute_cosine_similarity(item_a['vector'], item_b['vector'])
            attr_a: Dict[str, Any] = dict(item_a['extracted_attributes'])
            attr_b: Dict[str, Any] = dict(item_b['extracted_attributes'])
            pt_match, std_match, meas_match, uom_match, attr_status = evaluate_feature_matches(
                attr_a, attr_b
            )


            all_pairs.append({
                "organization_a": item_a['organization'],
                "organization_b": item_b['organization'],
                "description_a": item_a['raw_description'],
                "description_b": item_b['raw_description'],
                "normalized_a": item_a['normalized_text'],
                "normalized_b": item_b['normalized_text'],
                "cosine_similarity": float(sim_score),
                "attributes_a": item_a['extracted_attributes'],
                "attributes_b": item_b['extracted_attributes'],
                "product_type_match": pt_match,
                "standard_match": std_match,
                "measurement_match": meas_match,
                "uom_match": uom_match,
                "attribute_status": attr_status,
                "is_cross_org": item_a['organization'] != item_b['organization']
            })

    # Separate cross-org vs same-org pairs
    cross_org_pairs = [p for p in all_pairs if p['is_cross_org']]
    same_org_pairs = [p for p in all_pairs if not p['is_cross_org']]

    # Sort both descending by cosine similarity
    cross_org_pairs.sort(key=lambda x: x['cosine_similarity'], reverse=True)
    same_org_pairs.sort(key=lambda x: x['cosine_similarity'], reverse=True)

    top_30_cross_org = cross_org_pairs[:30]
    top_10_same_org = same_org_pairs[:10]

    # Print Top Cross-Organisation Candidates
    print("==================================================")
    print("TOP 30 CROSS-ORGANISATION SEMANTIC CANDIDATES")
    print("==================================================")
    print()

    for idx, pair in enumerate(top_30_cross_org, 1):
        print(f"Candidate #{idx}")
        print(f"Organization A   : {pair['organization_a']}")
        print(f"Description A    : {pair['description_a']}")
        print(f"Organization B   : {pair['organization_b']}")
        print(f"Description B    : {pair['description_b']}")
        print(f"Cosine similarity: {pair['cosine_similarity']:.4f}")
        print(f"Product Type Match: {pair['product_type_match']} | Standard Match: {pair['standard_match']}")
        print(f"Measurement Match: {pair['measurement_match']} | UOM Match: {pair['uom_match']}")
        print(f"Attribute status : {pair['attribute_status']}")
        print("Semantic status  : CANDIDATE ONLY")
        print("-" * 50)

    # Print Diagnostic Top 10 Same-Organisation Candidates
    print()
    print("==================================================")
    print("TOP 10 SAME-ORGANISATION CANDIDATES (DIAGNOSTIC)")
    print("==================================================")
    print()

    for idx, pair in enumerate(top_10_same_org, 1):
        print(f"Same-Org Candidate #{idx}")
        print(f"  [{pair['organization_a']}]")
        print(f"  Sim: {pair['cosine_similarity']:.4f} | Attr Status: {pair['attribute_status']}")
        print(f"  A: {pair['description_a']}")
        print(f"  B: {pair['description_b']}")
        print()

    # Calculate metrics for Cross-Org Top 30
    compatible_cnt = sum(1 for p in top_30_cross_org if p['attribute_status'] == 'COMPATIBLE')
    conflict_cnt = sum(1 for p in top_30_cross_org if p['attribute_status'] == 'CONFLICT')
    partial_cnt = sum(1 for p in top_30_cross_org if p['attribute_status'] == 'PARTIAL')
    unknown_cnt = sum(1 for p in top_30_cross_org if p['attribute_status'] == 'UNKNOWN')

    pt_match_cnt = sum(1 for p in top_30_cross_org if p['product_type_match'] == 'MATCH')
    pt_diff_cnt = sum(1 for p in top_30_cross_org if p['product_type_match'] == 'MISMATCH')

    std_match_cnt = sum(1 for p in top_30_cross_org if p['standard_match'] == 'MATCH')
    std_diff_cnt = sum(1 for p in top_30_cross_org if p['standard_match'] == 'MISMATCH')

    meas_compat_cnt = sum(1 for p in top_30_cross_org if p['measurement_match'] == 'MATCH')
    meas_conflict_cnt = sum(1 for p in top_30_cross_org if p['measurement_match'] == 'CONFLICT')
    meas_unk_cnt = sum(1 for p in top_30_cross_org if p['measurement_match'] in ('UNKNOWN', 'PARTIAL'))

    print("==================================================")
    print("SUMMARY")
    print("==================================================")
    print(f"Total descriptions processed : {total_processed}")
    print(f"Organizations represented   : {len(orgs_represented)}")
    print(f"Cross-organisation pairs    : {len(cross_org_pairs):,}")
    print(f"Same-organisation pairs     : {len(same_org_pairs):,}")
    print()
    print("Top 30 Cross-Organisation Attribute Status Breakdown:")
    print(f"  COMPATIBLE : {compatible_cnt}")
    print(f"  CONFLICT   : {conflict_cnt}")
    print(f"  PARTIAL    : {partial_cnt}")
    print(f"  UNKNOWN    : {unknown_cnt}")
    print()
    print("Feature Comparison Flags (Top 30 Cross-Org):")
    print(f"  Same Product Type         : {pt_match_cnt}")
    print(f"  Different Product Type    : {pt_diff_cnt}")
    print(f"  Same Standard             : {std_match_cnt}")
    print(f"  Different Standard        : {std_diff_cnt}")
    print(f"  Compatible Measurements   : {meas_compat_cnt}")
    print(f"  Conflicting Measurements  : {meas_conflict_cnt}")
    print(f"  Unknown/Partial Measurements: {meas_unk_cnt}")
    print()
    print("==================================================")
    print("IMPORTANT")
    print("==================================================")
    print("Semantic similarity is NOT engineering equivalence.")
    print("All candidates require engineering validation through the existing")
    print("matching/governance layer.")
    print()

    # Save outputs to backend/data/experiments/cross_org_candidate_pairs_top30.csv
    exp_dir = csv_path.parent.parent / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)

    csv_out_path = exp_dir / "cross_org_candidate_pairs_top30.csv"

    # Save CSV
    with open(csv_out_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank", "organization_a", "organization_b",
            "description_a", "description_b", "normalized_a", "normalized_b",
            "cosine_similarity", "attributes_a", "attributes_b",
            "product_type_match", "standard_match", "measurement_match", "uom_match",
            "attribute_status"
        ])
        for rank, pair in enumerate(top_30_cross_org, 1):
            writer.writerow([
                rank,
                pair['organization_a'],
                pair['organization_b'],
                pair['description_a'],
                pair['description_b'],
                pair['normalized_a'],
                pair['normalized_b'],
                f"{pair['cosine_similarity']:.4f}",
                json.dumps(pair['attributes_a']),
                json.dumps(pair['attributes_b']),
                pair['product_type_match'],
                pair['standard_match'],
                pair['measurement_match'],
                pair['uom_match'],
                pair['attribute_status']
            ])

    print(f"Saved TOP 30 Cross-Organisation candidates to CSV: {csv_out_path}")
    print()


if __name__ == "__main__":
    run_candidate_generation()
