import sys
import os
import secrets
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
from app.db.session import SessionLocal
from app.db.models import AppUser
from app.core.security import create_access_token, hash_password

def run_m6_verification():
    print("=" * 50)
    print("RUNNING M6 VERIFICATION — EXPORTS, PROCUREMENT & AUDIT UI")
    print("=" * 50)

    db = SessionLocal()
    client = TestClient(app)

    try:
        # 1. Authenticate test admin
        print("\n[Step 1] Authenticating Super Admin User...")
        admin = db.query(AppUser).filter_by(role="SUPER_ADMIN").first()
        if not admin:
            admin = AppUser(
                username=f"m6_admin_{secrets.token_hex(4)}",
                role="SUPER_ADMIN",
                password_hash=hash_password("TestPass123!"),
                is_active=True
            )
            db.add(admin)
            db.commit()

        token = create_access_token({"sub": admin.username, "role": admin.role})
        headers = {"Authorization": f"Bearer {token}"}
        print("  -> Auth token generated: PASSED")

        # 2. Test Crosswalk CSV Export
        print("\n[Step 2] Testing Crosswalk CSV Export (GET /api/v1/exports/crosswalk.csv)...")
        res = client.get("/api/v1/exports/crosswalk.csv", headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert "text/csv" in res.headers["content-type"], "Expected text/csv content type"
        assert "NMC,National_UID,CPSE_Code" in res.text, "Expected CSV header"
        print("  -> Crosswalk CSV Export: PASSED")

        # 3. Test Procurement Intelligence Endpoint
        print("\n[Step 3] Testing Procurement Intelligence (GET /api/v1/analytics/procurement)...")
        res = client.get("/api/v1/analytics/procurement", headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert "cpse_sharing_nmc_count" in data, "Missing cpse_sharing_nmc_count"
        assert "duplicate_materials_count" in data, "Missing duplicate_materials_count"
        assert "top_consolidation_opportunities" in data, "Missing top_consolidation_opportunities"
        assert "demonstration_notes" in data, "Missing demonstration_notes"
        print(f"  -> Shared NMCs Across CPSEs: {data['cpse_sharing_nmc_count']}")
        print(f"  -> Mapped Items Coverage: {data['mapping_coverage_pct']}%")
        print("  -> Procurement Analytics Endpoint: PASSED")

        # 4. Test Materials Listing Endpoint
        print("\n[Step 4] Testing Material Master Explorer API (GET /api/v1/materials)...")
        res = client.get("/api/v1/materials?page=1&page_size=10", headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        mats = res.json()
        assert isinstance(mats, list), "Expected list of materials"
        print(f"  -> Materials Retrieved: {len(mats)}")
        print("  -> Material Master Explorer API: PASSED")

        # 5. Test Audit Verification API
        print("\n[Step 5] Testing Cryptographic Audit Verification API (GET /api/v1/audit/verify)...")
        res = client.get("/api/v1/audit/verify", headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        audit_res = res.json()
        assert audit_res["valid"] is True, "Expected audit chain to be valid"
        print(f"  -> Verified Events: {audit_res['total_events']}")
        print("  -> Audit Chain Verification API: PASSED")

        print("\n" + "=" * 50)
        print("M6 VERIFICATION SUCCESSFUL — ALL CAPABILITIES VERIFIED!")
        print("=" * 50)

    finally:
        db.close()

if __name__ == "__main__":
    run_m6_verification()
