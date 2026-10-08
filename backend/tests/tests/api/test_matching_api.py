import pytest
from app.db.models import Cpse, ImportBatch, Material
from app.core.ids import generate_uuidv7

def test_matching_api_flow(client, auth_headers, db_session, sample_user):
    cpse = Cpse(id=str(generate_uuidv7()), code="CPSE_API_M4", name="API Test CPSE")
    db_session.add(cpse)
    batch = ImportBatch(
        id=str(generate_uuidv7()), cpse_id=cpse.id, kind="MATERIAL", filename="api.csv",
        sha256="dummy_hash_api", uploaded_by=sample_user.id
    )
    db_session.add(batch)

    m1 = Material(
        id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id,
        source_code="API-001", raw_description="HEX BOLT M12 X 60 SS316 10.9", raw_uom="NOS",
        category_hint="BOLT"
    )
    m2 = Material(
        id=str(generate_uuidv7()), cpse_id=cpse.id, batch_id=batch.id,
        source_code="API-002", raw_description="BOLT HEX M12X60 SS 316 GR10.9", raw_uom="EA",
        category_hint="BOLT"
    )
    db_session.add_all([m1, m2])
    db_session.commit()

    # 1. Trigger Match Run POST /api/v1/matching/runs
    payload = {
        "scope": {"batch_id": batch.id},
        "mode": "LIVE"
    }
    resp = client.post("/api/v1/matching/runs", json=payload, headers=auth_headers)
    assert resp.status_code == 202
    run_data = resp.json()
    assert run_data["status"] == "COMPLETED"
    run_id = run_data["id"]

    # 2. Get Match Run Details GET /api/v1/matching/runs/{id}
    resp_run = client.get(f"/api/v1/matching/runs/{run_id}", headers=auth_headers)
    assert resp_run.status_code == 200
    assert resp_run.json()["id"] == run_id

    # 3. List Match Runs GET /api/v1/matching/runs
    resp_list_runs = client.get("/api/v1/matching/runs", headers=auth_headers)
    assert resp_list_runs.status_code == 200
    assert len(resp_list_runs.json()) >= 1

    # 4. List Matches GET /api/v1/matches
    resp_matches = client.get(f"/api/v1/matches?run_id={run_id}", headers=auth_headers)
    assert resp_matches.status_code == 200
    match_list = resp_matches.json()
    assert len(match_list) >= 1

    match_id = match_list[0]["id"]
    assert match_list[0]["material_a"]["raw_description"] is not None
    assert match_list[0]["material_b"]["raw_description"] is not None

    # 5. Get Match Evidence Ledger GET /api/v1/matches/{id}
    resp_detail = client.get(f"/api/v1/matches/{match_id}", headers=auth_headers)
    assert resp_detail.status_code == 200
    detail = resp_detail.json()
    assert detail["id"] == match_id
    assert "signals" in detail
    assert "veto" in detail
    assert "evidence" in detail
    assert len(detail["evidence"]) >= 4
