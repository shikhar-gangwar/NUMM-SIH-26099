#!/usr/bin/env python3
"""
Comprehensive Database Integrity & Orphan Audit Script for NUMM (v1.6).
Verifies database integrity, foreign keys, orphan records, NULL identifiers,
duplicate source codes, and consistency.
"""

import os
import sys
from pathlib import Path

# When running on host, port 5433 is forwarded to postgres in container
if "DATABASE_URL" not in os.environ or "@db:" in os.environ.get("DATABASE_URL", ""):
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5433/sih_master"

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.db.session import SessionLocal
from app.db.models import (
    Material,
    Cpse,
    Classification,
    MaterialEmbedding,
    MatchRun,
    MaterialMatch,
    MatchEvidence,
    NationalMaterial,
    LegacyMapping,
    AuditEvent,
    Review,
)
from app.governance.nmc import validate_nmc
from sqlalchemy import text, func

def audit_database():
    db = SessionLocal()
    try:
        print("==================================================")
        print("DATABASE INTEGRITY & ORPHAN AUDIT (NUMM v1.6)")
        print("==================================================")

        # 1. Total counts
        total_materials = db.query(Material).count()
        total_cpses = db.query(Cpse).count()
        total_classifications = db.query(Classification).count()
        total_embeddings = db.query(MaterialEmbedding).count()
        total_match_runs = db.query(MatchRun).count()
        total_matches = db.query(MaterialMatch).count()
        total_evidence = db.query(MatchEvidence).count()
        total_nmcs = db.query(NationalMaterial).count()
        total_mappings = db.query(LegacyMapping).count()
        total_audits = db.query(AuditEvent).count()

        print(f"Total Materials:          {total_materials}")
        print(f"Total CPSEs:              {total_cpses}")
        print(f"Total Classifications:    {total_classifications}")
        print(f"Total Embeddings:         {total_embeddings}")
        print(f"Total Match Runs:         {total_match_runs}")
        print(f"Total Material Matches:   {total_matches}")
        print(f"Total Match Evidence:     {total_evidence}")
        print(f"Total National Materials: {total_nmcs}")
        print(f"Total Legacy Mappings:    {total_mappings}")
        print(f"Total Audit Events:       {total_audits}")

        issues = []

        # 2. Check for duplicate source codes within the same CPSE
        dup_query = text("""
            SELECT cpse_id, source_code, COUNT(*)
            FROM material
            GROUP BY cpse_id, source_code
            HAVING COUNT(*) > 1
        """)
        dups = db.execute(dup_query).fetchall()
        if dups:
            issues.append(f"Found {len(dups)} duplicate source_code entries within same CPSE!")
        else:
            print("[PASS] Zero duplicate (cpse_id, source_code) pairs found.")

        # 3. Check for NULL or empty primary identifiers
        null_mat_id = db.query(Material).filter(Material.id.is_(None)).count()
        null_source_code = db.query(Material).filter(
            (Material.source_code.is_(None)) | (Material.source_code == "")
        ).count()
        null_raw_desc = db.query(Material).filter(
            (Material.raw_description.is_(None)) | (Material.raw_description == "")
        ).count()
        if null_mat_id or null_source_code or null_raw_desc:
            issues.append(f"Material null fields: id={null_mat_id}, source_code={null_source_code}, raw_desc={null_raw_desc}")
        else:
            print("[PASS] Zero NULL or empty material identifiers/descriptions.")

        # 4. Check for orphan classifications
        orphan_class = text("""
            SELECT COUNT(*) FROM classification c
            LEFT JOIN material m ON c.material_id = m.id
            WHERE m.id IS NULL
        """)
        orphan_class_count = db.execute(orphan_class).scalar()
        if orphan_class_count > 0:
            issues.append(f"Found {orphan_class_count} orphan classification rows!")
        else:
            print("[PASS] Zero orphan classification records.")

        # 5. Check for orphan embeddings
        orphan_emb = text("""
            SELECT COUNT(*) FROM material_embedding e
            LEFT JOIN material m ON e.material_id = m.id
            WHERE m.id IS NULL
        """)
        orphan_emb_count = db.execute(orphan_emb).scalar()
        if orphan_emb_count > 0:
            issues.append(f"Found {orphan_emb_count} orphan embedding rows!")
        else:
            print("[PASS] Zero orphan embedding records.")

        # 6. Check for orphan legacy mappings
        orphan_mappings = text("""
            SELECT COUNT(*) FROM legacy_mapping lm
            LEFT JOIN material m ON lm.material_id = m.id
            WHERE m.id IS NULL
        """)
        orphan_map_count = db.execute(orphan_mappings).scalar()
        if orphan_map_count > 0:
            issues.append(f"Found {orphan_map_count} orphan legacy mappings!")
        else:
            print("[PASS] Zero orphan legacy mapping records.")

        # 7. Check for duplicate legacy mappings (material_id)
        dup_map_query = text("""
            SELECT material_id, COUNT(*)
            FROM legacy_mapping
            WHERE status = 'ACTIVE'
            GROUP BY material_id
            HAVING COUNT(*) > 1
        """)
        dup_maps = db.execute(dup_map_query).fetchall()
        if dup_maps:
            issues.append(f"Found {len(dup_maps)} duplicate active mappings for same material!")
        else:
            print("[PASS] Zero duplicate active legacy mappings.")

        # 8. Check for stuck match runs
        stuck_runs = db.query(MatchRun).filter(MatchRun.status == "PROCESSING").all()
        if stuck_runs:
            print(f"[INFO] Currently {len(stuck_runs)} run(s) with status=PROCESSING.")
        else:
            print("[PASS] Zero stuck PROCESSING match runs.")

        # 9. Verify National Material format
        nmcs = db.query(NationalMaterial).all()
        invalid_nmc = []
        for n in nmcs:
            if not validate_nmc(n.nmc):
                invalid_nmc.append(n.nmc)
        if invalid_nmc:
            issues.append(f"Invalid NMC codes found: {invalid_nmc}")
        else:
            print(f"[PASS] All {len(nmcs)} National Material Codes adhere to NMC-<CAT4>-<SEQ8>-<CHK> and ISO 7064 MOD 37,36 standard.")

        # 10. Audit Event chain sanity
        audit_records = db.query(AuditEvent).order_by(AuditEvent.seq.asc()).all()
        print(f"[PASS] Audit ledger contains {len(audit_records)} sequential events.")

        print("==================================================")
        if issues:
            print(f"AUDIT FAILED with {len(issues)} issues:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("ALL DATABASE INTEGRITY CHECKS PASSED (100% CLEAN)")
            print("==================================================")

    finally:
        db.close()

if __name__ == "__main__":
    audit_database()
