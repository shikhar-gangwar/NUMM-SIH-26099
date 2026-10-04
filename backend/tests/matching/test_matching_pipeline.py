import pytest
from app.db.models import Cpse, ImportBatch, Material, MatchRun, MaterialMatch, MatchEvidence, MaterialEmbedding
from app.matching.embedding_store import ensure_material_embeddings
from app.matching.blocking import get_candidate_materials
from app.matching.orchestrator import run_matching
from app.core.ids import generate_uuidv7

def test_embedding_store_and_blocking(db_session, sample_user):
    cpse = Cpse(id=str(generate_uuidv7()), code="CPSE_TEST_M4", name="M4 Test CPSE")
    db_session.add(cpse)
    batch = ImportBatch(
        id=str(generate_uuidv7()), cpse_id=cpse.id, kind="MATERIAL", filename="test.csv",
        sha256="dummy_hash", uploaded_by=sample_user.id
    )
    db_session.add(batch)

    m1 = Material(
        id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id,
        source_code="M4-001", raw_description="HEX BOLT M12 X 60 SS316 10.9", raw_uom="NOS",
        category_hint="BOLT"
    )
    m2 = Material(
        id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id,
        source_code="M4-002", raw_description="BOLT HEX M12X60 SS 316 GR10.9", raw_uom="EA",
        category_hint="BOLT"
    )
    m3 = Material(
        id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id,
        source_code="M4-003", raw_description="HEX BOLT M12 X 60 SS316 8.8", raw_uom="NOS",
        category_hint="BOLT"
    )
    db_session.add_all([m1, m2, m3])
    db_session.commit()

    # 1. Test embedding generation
    count, model_ver = ensure_material_embeddings(db_session, [m1, m2, m3])
    assert count == 3
    emb_count = db_session.query(MaterialEmbedding).filter_by(model_version_id=model_ver.id).count()
    assert emb_count == 3

    # 2. Test candidate blocking
    candidates, method = get_candidate_materials(db_session, m1, category_code="BOLT", candidate_cap=10)
    assert len(candidates) >= 1
    cand_ids = [c.id for c in candidates]
    assert m1.id not in cand_ids
    assert m2.id in cand_ids or m3.id in cand_ids

def test_run_matching_orchestrator(db_session, sample_user):
    cpse = Cpse(id=str(generate_uuidv7()), code="CPSE_M4_RUN", name="M4 Run CPSE")
    db_session.add(cpse)
    batch = ImportBatch(
        id=str(generate_uuidv7()), cpse_id=cpse.id, kind="MATERIAL", filename="run.csv",
        sha256="dummy_hash_run", uploaded_by=sample_user.id
    )
    db_session.add(batch)

    m1 = Material(
        id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id,
        source_code="RUN-001", raw_description="HEX BOLT M12 X 60 SS316 10.9", raw_uom="NOS",
        category_hint="BOLT"
    )
    m2 = Material(
        id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id,
        source_code="RUN-002", raw_description="HEX BOLT M12 X 60 SS316 8.8", raw_uom="NOS",
        category_hint="BOLT"
    )
    db_session.add_all([m1, m2])
    db_session.commit()

    # Execute match run
    scope = {"batch_id": batch.id}
    match_run = run_matching(db_session, scope=scope, mode="LIVE", user_id=sample_user.id)

    assert match_run.status == "COMPLETED"
    assert match_run.stats["total_materials"] == 2
    assert match_run.stats["comparisons_performed"] >= 1

    # Verify material_match persistence
    match_rows = db_session.query(MaterialMatch).filter_by(run_id=match_run.id).all()
    assert len(match_rows) >= 1
    match_item = match_rows[0]

    # Verify 8.8 vs 10.9 veto in DB
    assert match_item.relationship == "NOT_EQUIVALENT"
    assert match_item.equivalence_confidence == 0.0
    assert match_item.veto["applied"] is True

    # Verify match_evidence persistence
    ev_count = db_session.query(MatchEvidence).filter_by(match_id=match_item.id).count()
    assert ev_count >= 4
