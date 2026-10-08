import os
import sys

# CPU Safety settings MUST be configured before importing PyTorch
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import torch

try:
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
except Exception:
    pass

import argparse
import json
import time
from typing import Dict, Any, List, Tuple

# Ensure root directory is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

# Database default connection fallback if not provided in environment
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5433/sih_master"

from app.db.session import SessionLocal
from app.db.models import Material, Cpse
from app.ai.nlp.pipeline import nlp_pipeline
from app.ai.embeddings.embedder import get_cpu_embedder, compute_cosine_similarity
from app.ai.embeddings.cache import embedding_cache

MAX_ALLOWED_LIMIT = 50
DEFAULT_SAMPLE_SIZE = 10
BATCH_SIZE = 8

def parse_args():
    env_default = int(os.getenv("NLP_SAMPLE_SIZE", str(DEFAULT_SAMPLE_SIZE)))
    parser = argparse.ArgumentParser(
        description="CPU-safe real-data NLP inference sample runner for CPSE material records."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=env_default,
        help=f"Number of material records to process (default: {env_default}, max: {MAX_ALLOWED_LIMIT})"
    )
    return parser.parse_parse_args() if hasattr(parser, 'parse_parse_args') else parser.parse_args()

def evaluate_engineering_status(mat_a: Dict[str, Any], mat_b: Dict[str, Any], sim_score: float) -> str:
    """
    Safely attempts to run engineering veto logic if available,
    otherwise returns fallback message as per specification.
    """
    try:
        from app.matching.engine import evaluate_material_pair
        mat_dict_a = {
            "id": mat_a["id"],
            "raw_description": mat_a["raw_description"],
            "normalized_text": mat_a["normalized_text"],
            "category_code": mat_a["extracted_attributes"].get("material_type", "UNCLASSIFIED"),
            "attributes": [
                {"key": k, "value_text": str(v), "value_num": float(v) if isinstance(v, (int, float)) else None}
                for k, v in mat_a["extracted_attributes"].items()
            ]
        }
        mat_dict_b = {
            "id": mat_b["id"],
            "raw_description": mat_b["raw_description"],
            "normalized_text": mat_b["normalized_text"],
            "category_code": mat_b["extracted_attributes"].get("material_type", "UNCLASSIFIED"),
            "attributes": [
                {"key": k, "value_text": str(v), "value_num": float(v) if isinstance(v, (int, float)) else None}
                for k, v in mat_b["extracted_attributes"].items()
            ]
        }
        pair_res = evaluate_material_pair(mat_dict_a, mat_dict_b, semantic_score_override=sim_score)
        if pair_res.veto and pair_res.veto.get("applied"):
            rel_ceiling = pair_res.veto.get("relationship_ceiling") or pair_res.relationship
            if rel_ceiling == "NOT_EQUIVALENT":
                return "VETO"
            return "REVIEW"
        else:
            if pair_res.relationship in ["EXACT_DUPLICATE", "NEAR_DUPLICATE", "FUNCTIONALLY_EQUIVALENT"]:
                return "SAFE"
            elif pair_res.relationship == "NOT_EQUIVALENT":
                return "VETO"
            elif pair_res.relationship == "REVIEW_REQUIRED":
                return "REVIEW"
            else:
                return "UNKNOWN"
    except Exception:
        return "NOT AVAILABLE IN SAMPLE RUNNER"

def main():
    start_total_time = time.perf_counter()
    args = parse_args()
    requested_limit = args.limit

    # Enforce CPU Safety Maximum Limit
    if requested_limit > MAX_ALLOWED_LIMIT:
        print(f"\n[ERROR] Requested sample limit ({requested_limit}) exceeds maximum safety limit of {MAX_ALLOWED_LIMIT}.")
        print(f"Please specify a limit <= {MAX_ALLOWED_LIMIT} to avoid CPU overload and laptop overheating.")
        sys.exit(1)

    print("=" * 80)
    print("CPSE REAL-DATA NLP INFERENCE SAMPLE RUNNER (CPU-SAFE)")
    print("=" * 80)
    print(f"Requested Sample Size : {requested_limit}")
    print(f"CPU Limits Configured  : OMP_NUM_THREADS=1 | MKL_NUM_THREADS=1 | Torch Threads=1, Interop=1")
    print(f"Batch Size            : {BATCH_SIZE}")
    print(f"Target Model          : sentence-transformers/all-MiniLM-L6-v2")
    print("=" * 80 + "\n")

    # Fetch materials from database (READ-ONLY)
    records = []
    db = None
    try:
        db = SessionLocal()
        # Fetch CPSE mapping for displaying provenance / CPSE info
        cpse_map = {str(c.id): f"{c.code} ({c.name})" for c in db.query(Cpse).all()}
        
        db_materials = (
            db.query(Material)
            .filter(Material.raw_description.isnot(None), Material.raw_description != "")
            .limit(requested_limit)
            .all()
        )
        for m in db_materials:
            cpse_id_str = str(m.cpse_id) if m.cpse_id else ""
            cpse_info = cpse_map.get(cpse_id_str, cpse_id_str or "UNKNOWN")
            records.append({
                "id": str(m.id),
                "cpse": cpse_info,
                "raw_description": str(m.raw_description or ""),
                "source_code": str(m.source_code or ""),
                "provenance": str(getattr(m, "provenance", "UNKNOWN"))
            })
    except Exception as e:
        print(f"[ERROR] Database connection or query failed: {e}")
    finally:
        if db is not None:
            db.close()

    if not records:
        print("[WARNING] No valid material records found in database to process.")
        print("-" * 50)
        print("NLP SAMPLE PERFORMANCE")
        print("-" * 50)
        print(f"Records requested: {requested_limit}")
        print("Records processed: 0")
        print("Model: all-MiniLM-L6-v2")
        print("Embedding dimension: 384")
        print("Cache hits: 0")
        print("Cache misses: 0")
        print(f"Embedding time: 0.0000s")
        print(f"Total execution time: {time.perf_counter() - start_total_time:.4f}s")
        print("\nCPU configuration:")
        print("OMP_NUM_THREADS=2")
        print("MKL_NUM_THREADS=2")
        print("Torch threads=2")
        print("Torch interop threads=1")
        print(f"Batch size={BATCH_SIZE}")
        print("-" * 50)
        return

    processed_count = len(records)
    print(f"[INFO] Fetched {processed_count} material records from existing database.\n")

    # Initialize Embedder (CPU explicit)
    try:
        embedder = get_cpu_embedder()
    except Exception as e:
        print(f"[FATAL] Failed to load embedding model: {e}")
        sys.exit(1)

    processed_materials: List[Dict[str, Any]] = []
    cache_hits = 0
    cache_misses = 0

    embedding_start_time = time.perf_counter()

    with torch.inference_mode():
        for mat in records:
            raw_desc: str = mat["raw_description"]
            mat_id: str = mat["id"]
            # Step 4: Run description through EXISTING NLP pipeline
            parsed = nlp_pipeline.process(raw_desc)
            text_hash = parsed["text_hash"]
            norm_text = parsed["normalized_text"]
            attrs = parsed["extracted_attributes"]

            # Step 6: Use EXISTING embedding cache implementation
            cached_entry = embedding_cache.get(text_hash)
            if cached_entry:
                embedding_vec = cached_entry["embedding"]
                cache_status = "CACHE HIT"
                cache_hits += 1
            else:
                embedding_vec = embedder.embed_single(norm_text)
                embedding_cache.put(text_hash, norm_text, embedding_vec, material_id=mat_id)
                cache_status = "CACHE MISS"
                cache_misses += 1

            mat_entry = {
                "id": mat["id"],
                "cpse": mat["cpse"],
                "raw_description": raw_desc,
                "normalized_text": norm_text,
                "extracted_attributes": attrs,
                "embedding_dimension": len(embedding_vec),
                "embedding": embedding_vec,
                "cache_status": cache_status
            }
            processed_materials.append(mat_entry)

    embedding_total_time = time.perf_counter() - embedding_start_time

    # Step 4: Display Output for Each Material
    print("=" * 80)
    print("INDIVIDUAL MATERIAL NLP PROCESSING RESULTS")
    print("=" * 80)
    for mat in processed_materials:
        print("-" * 50)
        print(f"Material ID: {mat['id']}")
        print(f"CPSE: {mat['cpse']}")
        print(f"Raw Description:\n{mat['raw_description']}\n")
        print(f"Normalized Description:\n{mat['normalized_text']}\n")
        print(f"Extracted Attributes:\n{json.dumps(mat['extracted_attributes'], indent=2)}\n")
        print(f"Embedding Dimension: {mat['embedding_dimension']}")
        print(f"Cache Status: {mat['cache_status']}")
        print("-" * 50)

    # Step 5: Similarity Results (Pairwise Cosine Similarity)
    print("\n" + "=" * 80)
    print("PAIRWISE SEMANTIC SIMILARITY RESULTS (TOP 10 MATCHES)")
    print("=" * 80)

    pair_similarities: List[Tuple[Dict[str, Any], Dict[str, Any], float]] = []
    n = len(processed_materials)

    for i in range(n):
        for j in range(i + 1, n):
            mat_a = processed_materials[i]
            mat_b = processed_materials[j]
            sim = compute_cosine_similarity(mat_a["embedding"], mat_b["embedding"])
            pair_similarities.append((mat_a, mat_b, sim))

    # Sort descending by cosine similarity
    pair_similarities.sort(key=lambda x: x[2], reverse=True)
    top_matches = pair_similarities[:10]

    if not top_matches:
        print("\nNot enough materials to compute pairwise similarities.")
    else:
        for idx, (mat_a, mat_b, sim_score) in enumerate(top_matches, 1):
            eng_status = evaluate_engineering_status(mat_a, mat_b, sim_score)
            print("\n==================================================")
            print(f"TOP SEMANTIC MATCH #{idx}")
            print("==================================================")
            print(f"A:\nMaterial ID: {mat_a['id']}\n{mat_a['raw_description']}\n")
            print(f"B:\nMaterial ID: {mat_b['id']}\n{mat_b['raw_description']}\n")
            print(f"Cosine similarity: {sim_score:.4f}\n")
            print(f"A attributes:\n{json.dumps(mat_a['extracted_attributes'], indent=2)}\n")
            print(f"B attributes:\n{json.dumps(mat_b['extracted_attributes'], indent=2)}\n")
            print(f"Engineering status:\n{eng_status}")
            print("==================================================")

    total_execution_time = time.perf_counter() - start_total_time

    # Step 10: Performance Report
    print("\n" + "-" * 50)
    print("NLP SAMPLE PERFORMANCE")
    print("-" * 50)
    print(f"Records requested: {requested_limit}")
    print(f"Records processed: {processed_count}\n")
    print("Model:\nall-MiniLM-L6-v2\n")
    print(f"Embedding dimension: 384\n")
    print(f"Cache hits: {cache_hits}")
    print(f"Cache misses: {cache_misses}\n")
    print(f"Embedding time: {embedding_total_time:.4f}s")
    print(f"Total execution time: {total_execution_time:.4f}s\n")
    print("CPU configuration:")
    print("OMP_NUM_THREADS=1")
    print("MKL_NUM_THREADS=1")
    print("Torch threads=1")
    print("Torch interop threads=1")
    print(f"Batch size={BATCH_SIZE}")
    print("-" * 50 + "\n")

if __name__ == "__main__":
    main()
