#!/usr/bin/env python3
"""
M5 Verification Script — Governance Review Workflow, NMC Generator & Legacy Mapping Engine.
SIH 2026 PS 26099 — National Unified Material Master Framework.
"""

import sys
import os
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.db.session import SessionLocal
from app.db.models import Cpse, ImportBatch, Material, MatchRun, MaterialMatch, Review, NationalMaterial, LegacyMapping, AppUser, Classification
from app.governance.nmc import compute_iso7064_mod37_36, validate_nmc, generate_nmc, compute_spec_fingerprint
from app.governance.service import GovernanceService
from app.audit.service import AuditService
from app.core.ids import generate_uuidv7
from app.matching.orchestrator import run_matching
from generate_synthetic import generate_synthetic_dataset

def main():
    print("==================================================")
    print("RUNNING M5 VERIFICATION — GOVERNANCE REVIEW, NMC & LEGACY MAPPING")
    print("==================================================")

    db = SessionLocal()
    try:
        # 1. Test ISO 7064 MOD 37,36 Check Character & NMC Validation
        print("\n[Step 1] Verifying ISO 7064 MOD 37,36 & NMC Validation...")
        payload = "BOLT00000042"
        chk = compute_iso7064_mod37_36(payload)
        nmc_str = f"NMC-BOLT-00000042-{chk}"
        assert validate_nmc(nmc_str) is True, f"NMC '{nmc_str}' failed validation"
        assert validate_nmc("NMC-BOLT-00000042-Z") is False, "Invalid check character should fail validation"
        print(f"  -> Generated NMC: {nmc_str}")
        print("  -> ISO 7064 MOD 37,36 Check Character Algorithm: PASSED")

        # 2. Test NMC Counter & Deterministic Generation
        print("\n[Step 2] Verifying Per-Category NMC Generator...")
        nmc1 = generate_nmc(db, "BOLT")
        nmc2 = generate_nmc(db, "BOLT")
        assert nmc1 != nmc2, "Consecutive NMCs must be unique"
        assert validate_nmc(nmc1) is True, f"NMC1 {nmc1} invalid"
        assert validate_nmc(nmc2) is True, f"NMC2 {nmc2} invalid"
        print(f"  -> NMC 1: {nmc1}")
        print(f"  -> NMC 2: {nmc2}")
        print("  -> Per-Category NMC Generator: PASSED")

        # 3. Test Spec-Fingerprint Guard
        print("\n[Step 3] Verifying Spec-Fingerprint Guard...")
        attrs = [{"key": "SIZE", "canonical_value": "M12", "unit": "MM"}, {"key": "GRADE", "canonical_value": "10.9"}]
        fp1 = compute_spec_fingerprint("BOLT", attrs)
        fp2 = compute_spec_fingerprint("BOLT", reversed(attrs))
        assert fp1 == fp2, "Fingerprint must be deterministic regardless of attribute order"
        print(f"  -> Spec Fingerprint: {fp1}")
        print("  -> Spec-Fingerprint Guard: PASSED")

        # 4. Ingest Fixture Materials & Create Match Pair
        print("\n[Step 4] Setting up Test Materials & Candidate Match Pair...")
        cpse_a = db.query(Cpse).filter_by(code="CPSE-A").first()
        if not cpse_a:
            cpse_a = db.query(Cpse).first()
        cpse_b = db.query(Cpse).filter_by(code="CPSE-B").first()
        if not cpse_b:
            cpse_b = cpse_a

        user = db.query(AppUser).first()
        if not user:
            user = AppUser(id=str(generate_uuidv7()), username="m5_steward", password_hash="hash", role="SUPER_ADMIN")
            db.add(user)
            db.commit()

        batch = ImportBatch(
            id=str(generate_uuidv7()), cpse_id=cpse_a.id, kind="MATERIAL", filename="m5_test.csv",
            sha256="dummy_hash_m5", uploaded_by=user.id
        )
        db.add(batch)
        db.commit()

        import secrets
        run_tag = secrets.token_hex(6)

        m1 = Material(
            id=str(generate_uuidv7()), cpse_id=cpse_a.id, batch_id=batch.id, source_code=f"M5-BOLT-01-{run_tag}",
            raw_description="HEX BOLT M16 X 80 SS316 GR 10.9", raw_uom="NOS", normalized_text="HEX BOLT M16 X 80 SS316 GR 10.9"
        )
        m2 = Material(
            id=str(generate_uuidv7()), cpse_id=cpse_b.id, batch_id=batch.id, source_code=f"M5-BOLT-02-{run_tag}",
            raw_description="BOLT HEX M16X80 SS 316 10.9", raw_uom="EA", normalized_text="BOLT HEX M16X80 SS 316 10.9"
        )
        db.add_all([m1, m2])
        db.commit()

        # Classify materials
        cls1 = Classification(id=str(generate_uuidv7()), material_id=m1.id, category_code="BOLT", confidence=1.0, method="RULE_KEYWORD", input_hash="hash1", is_current=True)
        cls2 = Classification(id=str(generate_uuidv7()), material_id=m2.id, category_code="BOLT", confidence=1.0, method="RULE_KEYWORD", input_hash="hash2", is_current=True)
        db.add_all([cls1, cls2])

        match_run = MatchRun(id=str(generate_uuidv7()), scope={"all": True}, mode="LIVE", status="COMPLETED")
        db.add(match_run)
        
        match_pair = MaterialMatch(
            id=str(generate_uuidv7()),
            run_id=match_run.id,
            material_a_id=m1.id,
            material_b_id=m2.id,
            relationship="FUNCTIONALLY_EQUIVALENT",
            equivalence_confidence=0.98,
            raw_score=0.98,
            signals={"A": 1.0, "S": 0.98, "L": 0.95, "C": 1.0},
            veto={"applied": False},
            explanation="Matching M16 x 80 Grade 10.9 SS316 Hex Bolts",
            review_status="PROPOSED",
            input_hash=f"dummy_m5_hash_{run_tag}"
        )
        db.add(match_pair)
        db.commit()

        # 5. Test Approval Workflow (Single Atomic Transaction)
        print("\n[Step 5] Testing Steward Approval Transaction (Single Transaction)...")
        review_obj, nat_obj, legacy_mappings = GovernanceService.approve_match_pair(
            db=db,
            match_id=match_pair.id,
            user_id=user.id,
            comment="Approved by steward after verifying technical attributes"
        )
        assert review_obj.status == "APPROVED"
        assert validate_nmc(nat_obj.nmc) is True
        assert len(legacy_mappings) == 2
        assert match_pair.review_status == "APPROVED"
        print(f"  -> Approved Review ID:     {review_obj.id}")
        print(f"  -> Generated NMC Code:     {nat_obj.nmc}")
        print(f"  -> Legacy Mappings Created: {len(legacy_mappings)}")
        print("  -> Single-Transaction Approval & NMC Generation: PASSED")

        # 6. Test Rejection Workflow
        print("\n[Step 6] Testing Steward Rejection Flow...")
        m3 = Material(id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id, source_code=f"M5-REJ-01-{run_tag}", raw_description="HEX BOLT M10 X 40 8.8", raw_uom="NOS")
        m4 = Material(id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id, source_code=f"M5-REJ-02-{run_tag}", raw_description="HEX BOLT M10 X 40 10.9", raw_uom="NOS")
        db.add_all([m3, m4])
        db.commit()

        match_pair_rej = MaterialMatch(
            id=str(generate_uuidv7()),
            run_id=match_run.id,
            material_a_id=m3.id,
            material_b_id=m4.id,
            relationship="NOT_EQUIVALENT",
            equivalence_confidence=0.0,
            raw_score=0.0,
            signals={"A": 0.0, "S": 0.95, "L": 0.90, "C": 1.0},
            veto={"applied": True, "gate_id": "G2", "reason": "PROPERTY_CLASS_CONFLICT"},
            explanation="Conflict in property class 8.8 vs 10.9",
            review_status="PROPOSED",
            input_hash="dummy_rej_hash"
        )
        db.add(match_pair_rej)
        db.commit()

        rev_rej = GovernanceService.reject_match_pair(
            db=db,
            match_id=match_pair_rej.id,
            user_id=user.id,
            reason_code="TECHNICAL_MISMATCH",
            comment="Property class 8.8 and 10.9 cannot be merged."
        )
        assert rev_rej.status == "REJECTED"
        assert match_pair_rej.review_status == "REJECTED"
        print(f"  -> Rejection Review ID: {rev_rej.id}")
        print("  -> Steward Rejection Flow: PASSED")

        # 7. Test Audit Hash Chain Integrity
        print("\n[Step 7] Verifying Audit Trail & Cryptographic Hash Chain Integrity...")
        is_chain_valid, bad_seq = AuditService.verify_all(db=db)
        assert is_chain_valid is True, f"Audit hash chain verification failed at seq {bad_seq}"
        print("  -> Audit Hash Chain Verification: PASSED (Chain intact)")

        print("\n==================================================")
        print("M5 VERIFICATION SUCCESSFUL — ALL GOVERNANCE GATES PASSED!")
        print("==================================================\n")

    finally:
        db.close()

if __name__ == "__main__":
    main()
