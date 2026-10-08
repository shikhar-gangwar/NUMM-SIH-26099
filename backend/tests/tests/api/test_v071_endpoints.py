import pytest
from app.db.models import Cpse, ImportBatch, Material, MatchRun
from app.core.ids import generate_uuidv7
from datetime import datetime, timezone

def test_v071_material_detail_and_active_status(client, auth_headers, db_session, sample_user):
    cpse = Cpse(id=str(generate_uuidv7()), code="CPSE_TEST_071", name="CPSE 071 Test")
    db_session.add(cpse)
    batch = ImportBatch(
        id=str(generate_uuidv7()), cpse_id=cpse.id, kind="MATERIAL", filename="mat071.csv",
        sha256="dummy_hash_071", uploaded_by=sample_user.id
    )
    db_session.add(batch)

    m = Material(
        id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id,
        source_code="MAT-071-01", raw_description="HEX BOLT M16 X 75 GR 8.8 GALVANIZED", raw_uom="NOS",
        category_hint="BOLT", manufacturer="UNIBOLT", part_number="UB-M16-75"
    )
    db_session.add(m)
    db_session.commit()

    # 1. Test GET /api/v1/materials/{id} returns MaterialDetailDTO
    resp = client.get(f"/api/v1/materials/{m.id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == m.id
    assert data["source_code"] == "MAT-071-01"
    assert data["raw_description"] == "HEX BOLT M16 X 75 GR 8.8 GALVANIZED"
    assert data["manufacturer"] == "UNIBOLT"
    assert data["part_number"] == "UB-M16-75"
    assert "matches_count" in data
    assert "recent_matches" in data
    assert "audit_events" in data

    # 2. Test GET /api/v1/matching/status/active returns active status
    resp_status = client.get("/api/v1/matching/status/active", headers=auth_headers)
    assert resp_status.status_code == 200
    status_data = resp_status.json()
    assert "is_active" in status_data
    assert isinstance(status_data["is_active"], bool)

def test_v071_concurrency_lock(client, auth_headers, db_session, sample_user):
    # Create an active run in PROCESSING state
    run_id = str(generate_uuidv7())
    active_run = MatchRun(
        id=run_id,
        scope={"all": True},
        mode="LIVE",
        status="PROCESSING",
        started_by=sample_user.id,
        started_at=datetime.now(timezone.utc)
    )
    db_session.add(active_run)
    db_session.commit()

    # Attempting to trigger another run must raise 409 CONCURRENT_RUN_IN_PROGRESS
    resp = client.post(
        "/api/v1/matching/runs",
        json={"scope": {"all": True}},
        headers=auth_headers
    )
    assert resp.status_code == 409
    err = resp.json()["detail"]
    assert err["code"] == "CONCURRENT_RUN_IN_PROGRESS"

    # Cleanup active run
    active_run.status = "COMPLETED"
    active_run.finished_at = datetime.now(timezone.utc)
    db_session.commit()
