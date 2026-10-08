import pytest
from app.core.security import hash_password, create_access_token
from app.db.models import AppUser

def test_reviewer_login_and_rbac(client, db_session):
    # 1. Ensure reviewer_demo user exists in test db session
    reviewer = db_session.query(AppUser).filter_by(username="reviewer_demo").first()
    if not reviewer:
        reviewer = AppUser(
            username="reviewer_demo",
            password_hash=hash_password("NUMM-Demo-Reviewer-2026!"),
            role="REVIEWER",
            is_active=True
        )
        db_session.add(reviewer)
        db_session.commit()

    # 2. Test wrong login for reviewer fails
    wrong_res = client.post("/api/v1/auth/login", json={
        "username": "reviewer_demo",
        "password": "WrongPassword123!"
    })
    assert wrong_res.status_code == 401

    # 3. Test correct login for reviewer succeeds
    login_res = client.post("/api/v1/auth/login", json={
        "username": "reviewer_demo",
        "password": "NUMM-Demo-Reviewer-2026!"
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "REVIEWER"
    
    token = data["access_token"]
    reviewer_headers = {"Authorization": f"Bearer {token}"}

    # 4. Reviewer CAN access review queue and summary counts
    rev_res = client.get("/api/v1/reviews?limit=10", headers=reviewer_headers)
    assert rev_res.status_code == 200

    counts_res = client.get("/api/v1/reviews/summary/counts", headers=reviewer_headers)
    assert counts_res.status_code == 200

    # 5. Reviewer CAN view materials master
    mat_res = client.get("/api/v1/materials?limit=5", headers=reviewer_headers)
    assert mat_res.status_code == 200

    # 6. Reviewer is FORBIDDEN (403) from launching match runs (requires DATA_STEWARD or SUPER_ADMIN)
    match_run_res = client.post(
        "/api/v1/matching/runs",
        headers=reviewer_headers,
        json={"scope": {"all": True}}
    )
    assert match_run_res.status_code == 403

    # 7. Reviewer is FORBIDDEN (403) from inspecting audit logs (requires DATA_STEWARD or SUPER_ADMIN)
    audit_res = client.get("/api/v1/audit", headers=reviewer_headers)
    assert audit_res.status_code == 403

    # 8. Reviewer is FORBIDDEN (403) from triggering ERP sync (requires DATA_STEWARD or SUPER_ADMIN)
    sync_res = client.post("/api/v1/integration/sap/sync", headers=reviewer_headers, json={})
    assert sync_res.status_code == 403

    # 9. Reviewer is FORBIDDEN (403) from approving match pairs (requires DATA_STEWARD or SUPER_ADMIN)
    approve_res = client.post("/api/v1/reviews/dummy-match-id/approve", headers=reviewer_headers, json={})
    assert approve_res.status_code == 403

    # 10. Reviewer is FORBIDDEN (403) from rejecting match pairs (requires DATA_STEWARD or SUPER_ADMIN)
    reject_res = client.post("/api/v1/reviews/dummy-match-id/reject", headers=reviewer_headers, json={"reason_code": "TECHNICAL_MISMATCH"})
    assert reject_res.status_code == 403

    # 11. Reviewer is FORBIDDEN (403) from remapping match pairs (requires DATA_STEWARD or SUPER_ADMIN)
    remap_res = client.post("/api/v1/reviews/dummy-match-id/remap", headers=reviewer_headers, json={"target_nmc": "NMC-TEST-0001"})
    assert remap_res.status_code == 403

    # 12. Reviewer is FORBIDDEN (403) from uploading file imports (requires DATA_STEWARD or SUPER_ADMIN)
    files = {"file": ("test.csv", b"dummy,data", "text/csv")}
    upload_res = client.post("/api/v1/imports/upload", headers=reviewer_headers, files=files)
    assert upload_res.status_code == 403
