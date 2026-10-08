import requests
import time

API_URL = "http://localhost:8000"

def test_flow():
    # 1. Login as admin
    login_res = requests.post(f"{API_URL}/api/v1/auth/login", json={"username": "steward_admin", "password": "DevSec_D1I6hALEJYSYhoLsYpWwkPc0"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check active status
    status_res = requests.get(f"{API_URL}/api/v1/matching/status/active", headers=headers)
    print("Initial Active Status:", status_res.json())

    # 3. Trigger SIH Demo Run
    print("Triggering SIH Demo Run...")
    run_res = requests.post(
        f"{API_URL}/api/v1/matching/runs?async_mode=true",
        headers=headers,
        json={"scope": {"is_demo": True, "demo": True}, "mode": "SIH_DEMO"}
    )
    print("Run Trigger Status Code:", run_res.status_code)
    assert run_res.status_code == 202, f"Expected 202, got {run_res.status_code}: {run_res.text}"
    run_data = run_res.json()
    run_id = run_data["id"]
    print("Started Run ID:", run_id, "Status:", run_data["status"])

    # 4. Poll progress (up to 40 seconds)
    for i in range(80):
        poll_res = requests.get(f"{API_URL}/api/v1/matching/runs/{run_id}", headers=headers)
        data = poll_res.json()
        stats = data.get("stats") or {}
        print(f"[{i+1}] Status: {data['status']}, Processed: {stats.get('materials_processed')}/{stats.get('total_materials')}, Comparisons: {stats.get('comparisons_performed')}, Duration: {stats.get('duration_ms')}ms")
        if data["status"] in ["COMPLETED", "FAILED"]:
            break
        time.sleep(0.5)

    assert data["status"] == "COMPLETED", f"Expected COMPLETED, got {data['status']}"
    print("\nSUCCESS! Matching run completed with stats:")
    print(data["stats"])

if __name__ == "__main__":
    test_flow()
