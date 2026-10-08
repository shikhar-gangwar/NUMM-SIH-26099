"""
Real Public Dataset Ingestion Script
SIH 2026 PS 26099 — CPSE Material Code Harmonisation

Dataset:
"SIH 26099 — Collected Dataset" (Hugging Face: Prasenjeet25/sih26099-cpse-material-codes)
Total rows: 21,513
Organizations: Oil India Limited, NTPC Limited, Indian Oil Corporation Limited
License: CC BY 4.0
Provenance: REAL_PUBLIC
"""

import os
import sys
import hashlib
import time
import pandas as pd
from datetime import datetime, timezone

# Ensure backend is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

# Default to port 5433 if running on host against container
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5433/sih_master"

from app.db.session import SessionLocal
from app.db.models import Cpse, ImportBatch, Material, MaterialAttribute, Classification, AppUser
from app.normalization.uom import normalize_uom
from app.normalization.text import normalize_text
from app.extraction.extractor import detect_category, extract_attributes
from app.core.ids import generate_uuidv7

CORPUS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "real", "material_description_corpus.csv"))

ORG_MAP = {
    "Oil India Limited": {
        "code": "OIL_INDIA",
        "name": "Oil India Limited",
        "sector": "Upstream Oil & Gas"
    },
    "NTPC Limited": {
        "code": "NTPC",
        "name": "NTPC Limited",
        "sector": "Power Generation"
    },
    "Indian Oil Corporation Limited": {
        "code": "IOCL",
        "name": "Indian Oil Corporation Limited",
        "sector": "Downstream Oil & Refining"
    }
}

def compute_file_sha256(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def ensure_cpses(db) -> dict[str, Cpse]:
    cpse_objects = {}
    for org_name, info in ORG_MAP.items():
        cpse = db.query(Cpse).filter_by(code=info["code"]).first()
        if not cpse:
            cpse = Cpse(
                code=info["code"],
                name=info["name"],
                sector=info["sector"],
                is_synthetic=False,
                status="ACTIVE"
            )
            db.add(cpse)
            db.flush()
            print(f"Created real CPSE: {info['code']} ({info['name']})")
        else:
            cpse.is_synthetic = False
            db.flush()
        cpse_objects[org_name] = cpse
    return cpse_objects

def ingest_dataset():
    if not os.path.exists(CORPUS_PATH):
        print(f"Error: Corpus file not found at {CORPUS_PATH}")
        sys.exit(1)

    file_sha = compute_file_sha256(CORPUS_PATH)
    print(f"Loading corpus from: {CORPUS_PATH} (SHA256: {file_sha[:16]}...)")

    df = pd.read_csv(CORPUS_PATH)
    total_records = len(df)
    print(f"Loaded {total_records:,} records across organizations:")
    print(df["organization"].value_counts().to_string())

    db = SessionLocal()
    try:
        cpses = ensure_cpses(db)

        # Get steward user for audit
        admin_user = db.query(AppUser).filter_by(username="steward_admin").first()
        if not admin_user:
            admin_user = db.query(AppUser).first()
        user_id = admin_user.id if admin_user else str(generate_uuidv7())

        # Check existing materials by source_code to be idempotent
        existing_codes = set(
            row[0] for row in db.query(Material.source_code).filter(Material.provenance == "REAL_PUBLIC").all()
        )
        print(f"Found {len(existing_codes):,} already imported REAL_PUBLIC materials.")

        # Create ImportBatch per CPSE
        batches = {}
        for org_name, cpse in cpses.items():
            org_df = df[df["organization"] == org_name]
            batch = ImportBatch(
                cpse_id=cpse.id,
                kind="MATERIAL",
                filename="material_description_corpus.csv",
                sha256=file_sha,
                total_rows=len(org_df),
                accepted_rows=0,
                rejected_rows=0,
                warning_rows=0,
                status="PROCESSING",
                uploaded_by=user_id
            )
            db.add(batch)
            db.flush()
            batches[org_name] = batch

        print("\nStarting batch ingestion with attribute extraction and categorization...")
        t_start = time.time()
        
        batch_size = 500
        materials_to_insert = []
        classifications_to_insert = []
        attributes_to_insert = []
        
        imported_count = 0
        skipped_count = 0
        category_counts = {}

        for idx, row in df.iterrows():
            corpus_id = str(row["corpus_id"]).strip()
            if corpus_id in existing_codes:
                skipped_count += 1
                continue

            org_name = str(row["organization"]).strip()
            cpse = cpses.get(org_name)
            if not cpse:
                continue

            raw_desc = str(row["description"]).strip() if pd.notna(row["description"]) else ""
            if not raw_desc:
                skipped_count += 1
                continue

            raw_uom = str(row["unit"]).strip() if pd.notna(row["unit"]) and str(row["unit"]).strip() else "EA"
            cat_hint = str(row["item_type_hint"]).strip() if pd.notna(row["item_type_hint"]) else None
            prod_cat = str(row["product_category"]).strip() if pd.notna(row["product_category"]) else None
            
            # Normalization
            canon_uom, uom_dim, uom_flags = normalize_uom(raw_uom)
            norm_res = normalize_text(raw_desc)
            
            # Category detection
            effective_hint = cat_hint or prod_cat
            cat_code = detect_category(norm_res.text, hint=effective_hint)
            category_counts[cat_code] = category_counts.get(cat_code, 0) + 1

            # Extract technical attributes
            extracted_attrs = extract_attributes(norm_res.text, cat_code)

            # Safe quantity parsing
            qty_val = None
            if pd.notna(row["quantity"]):
                try:
                    qty_val = float(str(row["quantity"]).replace(",", "").strip())
                except Exception:
                    qty_val = None

            # Metadata preservation
            provenance_meta = {
                "provenance": "REAL_PUBLIC",
                "dataset": "SIH 26099 — CPSE Material Code Harmonisation Dataset",
                "huggingface": "https://huggingface.co/datasets/Prasenjeet25/sih26099-cpse-material-codes",
                "license": "CC BY 4.0",
                "organization": org_name,
                "source_system": str(row["source_system"]) if pd.notna(row["source_system"]) else None,
                "tender_reference": str(row["tender_reference"]) if pd.notna(row["tender_reference"]) else None,
                "tender_id": str(row["tender_id"]) if pd.notna(row["tender_id"]) else None,
                "quantity": qty_val,
                "location": str(row["location"]) if pd.notna(row["location"]) else None,
                "document_url": str(row["document_url"]) if pd.notna(row["document_url"]) else None,
                "source_url": str(row["source_url"]) if pd.notna(row["source_url"]) else None
            }

            mat_id = str(generate_uuidv7())
            mat = Material(
                id=mat_id,
                cpse_id=cpse.id,
                source_code=corpus_id,
                raw_description=raw_desc,
                raw_uom=raw_uom,
                category_hint=effective_hint,
                batch_id=batches[org_name].id,
                normalized_text=norm_res.text,
                uom_canonical=canon_uom,
                uom_dimension=uom_dim,
                norm_flags=norm_res.flags + uom_flags,
                provenance="REAL_PUBLIC",
                provenance_metadata=provenance_meta,
                status="ACTIVE"
            )
            materials_to_insert.append(mat)

            cls_rec = Classification(
                id=str(generate_uuidv7()),
                material_id=mat_id,
                category_code=cat_code,
                confidence=1.0 if cat_code != "UNCLASSIFIED" else 0.5,
                method="RULE",
                input_hash=hashlib.sha256(norm_res.text.encode("utf-8")).hexdigest(),
                is_current=True
            )
            classifications_to_insert.append(cls_rec)

            for ea in extracted_attrs:
                attr_rec = MaterialAttribute(
                    id=str(generate_uuidv7()),
                    material_id=mat_id,
                    key=ea.key,
                    raw_text=ea.raw_text,
                    value_text=ea.value_text,
                    value_num=ea.value_num,
                    unit=ea.unit,
                    canonical_value=ea.canonical_value,
                    source=ea.source,
                    confidence=ea.confidence,
                    assumed=ea.assumed,
                    internal_conflict=ea.internal_conflict,
                    span=ea.span,
                    rule_id=ea.rule_id,
                    is_current=True
                )
                attributes_to_insert.append(attr_rec)

            imported_count += 1

            if len(materials_to_insert) >= batch_size:
                db.add_all(materials_to_insert)
                db.flush()
                db.add_all(classifications_to_insert)
                if attributes_to_insert:
                    db.add_all(attributes_to_insert)
                db.commit()
                materials_to_insert.clear()
                classifications_to_insert.clear()
                attributes_to_insert.clear()
                
                rate = imported_count / (time.time() - t_start)
                print(f"  Ingested {imported_count:,}/{total_records:,} rows ({rate:.1f} rows/s)...")

        # Flush any remaining rows
        if materials_to_insert:
            db.add_all(materials_to_insert)
            db.flush()
            db.add_all(classifications_to_insert)
            if attributes_to_insert:
                db.add_all(attributes_to_insert)
            db.commit()

        # Update batch statuses
        for org_name, batch in batches.items():
            accepted = db.query(Material).filter_by(batch_id=batch.id).count()
            batch.accepted_rows = accepted
            batch.status = "COMPLETED"
        db.commit()

        elapsed = time.time() - t_start
        print(f"\n=======================================================")
        print(f"INGESTION COMPLETE IN {elapsed:.2f} SECONDS")
        print(f"Total newly imported: {imported_count:,}")
        print(f"Total skipped/existing: {skipped_count:,}")
        print(f"Total in database: {db.query(Material).count():,}")
        print("Category breakdown of imported items:")
        for cat, cnt in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat:15}: {cnt:,}")
        print(f"=======================================================\n")

    except Exception as e:
        db.rollback()
        print(f"Error during ingestion: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    ingest_dataset()
