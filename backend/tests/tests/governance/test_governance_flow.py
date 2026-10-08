import pytest
import secrets
from app.db.models import Cpse, ImportBatch, Material, MaterialMatch, Classification, NationalMaterial, LegacyMapping, Review, AppUser
from app.governance.nmc import compute_iso7064_mod37_36, validate_nmc, generate_nmc, compute_spec_fingerprint
from app.governance.service import GovernanceService
from app.audit.service import AuditService
from app.core.ids import generate_uuidv7

def test_iso7064_check_digit_and_validation():
    payload = "BOLT00000042"
    chk = compute_iso7064_mod37_36(payload)
    nmc = f"NMC-BOLT-00000042-{chk}"
    assert validate_nmc(nmc) is True
    assert validate_nmc("NMC-BOLT-00000042-Z") is False
    assert validate_nmc("INVALID") is False

def test_nmc_generator_uniqueness(db_session):
    nmc1 = generate_nmc(db_session, "PIPE")
    nmc2 = generate_nmc(db_session, "PIPE")
    assert nmc1 != nmc2
    assert validate_nmc(nmc1) is True
    assert validate_nmc(nmc2) is True

def test_spec_fingerprint_guard():
    attrs1 = [{"key": "DIAMETER", "canonical_value": "4", "unit": "INCH"}, {"key": "SCHEDULE", "canonical_value": "SCH 40"}]
    attrs2 = [{"key": "SCHEDULE", "canonical_value": "SCH 40"}, {"key": "DIAMETER", "canonical_value": "4", "unit": "INCH"}]
    assert compute_spec_fingerprint("PIPE", attrs1) == compute_spec_fingerprint("PIPE", attrs2)

def test_governance_approval_flow(db_session, sample_user):
    cpse = Cpse(id=str(generate_uuidv7()), code="CPSE_GOV_TEST", name="Gov CPSE", is_synthetic=True)
    db_session.add(cpse)
    batch = ImportBatch(
        id=str(generate_uuidv7()), cpse_id=cpse.id, kind="MATERIAL", filename="gov.csv",
        sha256="dummy_gov", uploaded_by=sample_user.id
    )
    db_session.add(batch)
    db_session.commit()

    run_tag = secrets.token_hex(4)
    m1 = Material(
        id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id, source_code=f"GOV-01-{run_tag}",
        raw_description="PIPE 4 INCH SCH 40 A106 GR B", raw_uom="MTR", normalized_text="PIPE 4 INCH SCH 40 A106 GR B"
    )
    m2 = Material(
        id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id, source_code=f"GOV-02-{run_tag}",
        raw_description="PIPE CS 4 IN SCH 40 GR B", raw_uom="MTR", normalized_text="PIPE CS 4 IN SCH 40 GR B"
    )
    db_session.add_all([m1, m2])
    db_session.commit()

    cls1 = Classification(id=str(generate_uuidv7()), material_id=m1.id, category_code="PIPE", confidence=1.0, method="RULE_KEYWORD", input_hash="h1", is_current=True)
    cls2 = Classification(id=str(generate_uuidv7()), material_id=m2.id, category_code="PIPE", confidence=1.0, method="RULE_KEYWORD", input_hash="h2", is_current=True)
    db_session.add_all([cls1, cls2])

    match_pair = MaterialMatch(
        id=str(generate_uuidv7()), run_id="run_dummy", material_a_id=m1.id, material_b_id=m2.id,
        relationship="FUNCTIONALLY_EQUIVALENT", equivalence_confidence=0.96, raw_score=0.96,
        signals={"A": 1.0, "S": 0.96}, veto={"applied": False}, explanation="Pipe match",
        review_status="PROPOSED", input_hash=f"hash_{run_tag}"
    )
    db_session.add(match_pair)
    db_session.commit()

    rev, nat, legs = GovernanceService.approve_match_pair(
        db=db_session,
        match_id=match_pair.id,
        user_id=sample_user.id,
        comment="Unit test approval"
    )

    assert rev.status == "APPROVED"
    assert validate_nmc(nat.nmc) is True
    assert len(legs) == 2
    assert match_pair.review_status == "APPROVED"

def test_governance_rejection_flow(db_session, sample_user):
    cpse = db_session.query(Cpse).filter_by(code="CPSE_GOV_TEST").first()
    if not cpse:
        cpse = Cpse(id=str(generate_uuidv7()), code="CPSE_GOV_TEST", name="Gov CPSE", is_synthetic=True)
        db_session.add(cpse)
        db_session.commit()

    batch = db_session.query(ImportBatch).filter_by(cpse_id=cpse.id).first()
    if not batch:
        batch = ImportBatch(
            id=str(generate_uuidv7()), cpse_id=cpse.id, kind="MATERIAL", filename="gov.csv",
            sha256="dummy_gov_rej", uploaded_by=sample_user.id
        )
        db_session.add(batch)
        db_session.commit()

    run_tag = secrets.token_hex(4)

    m1 = Material(id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id, source_code=f"REJ-01-{run_tag}", raw_description="PIPE SCH 40", raw_uom="MTR")
    m2 = Material(id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id, source_code=f"REJ-02-{run_tag}", raw_description="PIPE SCH 80", raw_uom="MTR")
    db_session.add_all([m1, m2])
    db_session.commit()

    match_pair = MaterialMatch(
        id=str(generate_uuidv7()), run_id="run_dummy", material_a_id=m1.id, material_b_id=m2.id,
        relationship="NOT_EQUIVALENT", equivalence_confidence=0.0, raw_score=0.0,
        signals={"A": 0.0, "S": 0.90}, veto={"applied": True, "gate_id": "G2"}, explanation="Pipe schedule conflict",
        review_status="PROPOSED", input_hash=f"hash_rej_{run_tag}"
    )
    db_session.add(match_pair)
    db_session.commit()

    rev = GovernanceService.reject_match_pair(
        db=db_session,
        match_id=match_pair.id,
        user_id=sample_user.id,
        reason_code="SCHEDULE_MISMATCH",
        comment="Different pipe wall thickness"
    )

    assert rev.status == "REJECTED"
    assert match_pair.review_status == "REJECTED"
