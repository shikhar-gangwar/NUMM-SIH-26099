import urllib.request
import urllib.parse
import json
import time
import concurrent.futures
import statistics
import sys

API_BASE = "http://localhost:8000"

def get_auth_token(username, password):
    payload = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/api/v1/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.loads(res.read().decode())
        return data["access_token"]

def make_request(method, path, headers=None, data=None):
    url = f"{API_BASE}{path}"
    body = None
    hdrs = headers or {}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=15) as res:
        content = res.read()
        duration_ms = (time.perf_counter() - start) * 1000
        return res.status, duration_ms, len(content)

def run_stress_test():
    print("==================================================")
    print("NUMM SUSTAINED LOAD & CONCURRENCY STRESS SUITE")
    print("==================================================")
    
    # 1. Acquire Admin & Reviewer Tokens
    print("\n--- PHASE 1: TOKEN ACQUISITION & WARMUP ---")
    admin_token = get_auth_token("steward_admin", "DevSec_D1I6hALEJYSYhoLsYpWwkPc0")
    reviewer_token = get_auth_token("reviewer_demo", "NUMM-Demo-Reviewer-2026!")
    print(f"[PASS] Acquired Admin and Reviewer bearer tokens.")

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_reviewer = {"Authorization": f"Bearer {reviewer_token}"}

    # 2. Test Endpoints Under Sustained Concurrent Load
    # We will dispatch 200 concurrent requests across 20 worker threads
    endpoints = [
        ("GET", "/health", None),
        ("GET", "/api/v1/meta/public-stats", None),
        ("GET", "/api/v1/analytics/summary", headers_admin),
        ("GET", "/api/v1/analytics/charts", headers_admin),
        ("GET", "/api/v1/materials?query=BOLT&page=1&page_size=10", headers_admin),
        ("GET", "/api/v1/materials?category=PIPE&page=1&page_size=10", headers_admin),
        ("GET", "/api/v1/reviews?page=1&page_size=20", headers_admin),
        ("GET", "/api/v1/audit/verify", headers_admin),
        ("GET", "/api/v1/integration/sap/status", headers_admin),
        ("GET", "/api/v1/integration/sap/materials?page=1&page_size=5", headers_admin),
        ("GET", "/api/v1/exports/crosswalk.csv", headers_admin),
        ("GET", "/api/v1/matches/01a100b6-1057-738f-97b6-8b490ec05681", headers_admin),  # 8.8 vs 10.9 Trap
        ("GET", "/api/v1/national-materials?page=1&page_size=5", headers_reviewer),
    ]

    total_requests = 200
    concurrency = 20

    print(f"\n--- PHASE 2: SUSTAINED HIGH-CONCURRENCY STRESS ({total_requests} requests, concurrency={concurrency}) ---")
    
    latencies = []
    status_counts = {}
    errors = []

    start_suite = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(total_requests):
            ep = endpoints[i % len(endpoints)]
            futures.append(executor.submit(make_request, ep[0], ep[1], ep[2]))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                status_code, dur_ms, content_len = future.result()
                latencies.append(dur_ms)
                status_counts[status_code] = status_counts.get(status_code, 0) + 1
            except Exception as e:
                errors.append(str(e))

    total_duration_sec = time.perf_counter() - start_suite
    throughput = len(latencies) / total_duration_sec

    print(f"Total Requests Completed: {len(latencies)} / {total_requests}")
    print(f"Status Code Breakdown:    {status_counts}")
    print(f"Total Elapsed Time:       {total_duration_sec:.2f}s")
    print(f"Sustained Throughput:     {throughput:.1f} req/sec")

    if latencies:
        p50 = statistics.median(latencies)
        p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        p99 = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
        print(f"Latency Percentiles:")
        print(f"    P50 (Median): {p50:.2f} ms")
        print(f"    P95:          {p95:.2f} ms")
        print(f"    P99:          {p99:.2f} ms")
        print(f"    Min:          {min(latencies):.2f} ms")
        print(f"    Max:          {max(latencies):.2f} ms")

    if errors:
        print(f"\n[FAIL] Encountered {len(errors)} request errors during stress test:")
        for err in errors[:5]:
            print(f"    - {err}")
        sys.exit(1)
    else:
        print(f"\n[PASS] Zero HTTP errors, zero connection timeouts, zero pool exhaustion.")

    # 3. Sustained Pipeline Veto Invariant Check Under Pressure
    print("\n--- PHASE 3: SAFETY VETO LATTICE INVARIANT CHECK UNDER STRESS ---")
    trap_status, trap_dur, _ = make_request("GET", "/api/v1/matches/01a100b6-1057-738f-97b6-8b490ec05681", headers_admin)
    assert trap_status == 200, f"Expected 200, got {trap_status}"
    
    req = urllib.request.Request(f"{API_BASE}/api/v1/matches/01a100b6-1057-738f-97b6-8b490ec05681", headers=headers_admin)
    with urllib.request.urlopen(req) as res:
        trap = json.loads(res.read().decode())
        assert trap["relationship"] == "NOT_EQUIVALENT", f"Breached! Expected NOT_EQUIVALENT, got {trap['relationship']}"
        assert trap["veto"]["applied"] is True, f"Breached! Veto not applied!"
        assert trap["veto"]["gate_id"] == "G2", f"Breached! Expected Gate G2, got {trap['veto']['gate_id']}"
        assert trap["equivalence_confidence"] == 0.0, f"Breached! Confidence not 0.0"
        print("[PASS] Gate G2 Hard Veto (8.8 vs 10.9) strictly sustained under load.")

    # 4. Cryptographic Hash Chain Audit Under Sustained Use
    print("\n--- PHASE 4: AUDIT HASH CHAIN TAMPER VERIFICATION ---")
    req = urllib.request.Request(f"{API_BASE}/api/v1/audit/verify", headers=headers_admin)
    with urllib.request.urlopen(req) as res:
        audit = json.loads(res.read().decode())
        assert audit["valid"] is True, "Audit chain verification failed!"
        print(f"[PASS] Cryptographic SHA-256 Chain is valid across all {audit['total_events']} events.")

    # 5. SAP Idempotent Sync Test Under Repeated Execution
    print("\n--- PHASE 5: SAP S/4HANA IDEMPOTENT SYNC STRESS ---")
    for cycle in range(3):
        post_req = urllib.request.Request(f"{API_BASE}/api/v1/integration/sap/sync", data=b"{}", headers=headers_admin)
        with urllib.request.urlopen(post_req) as res:
            sync_res = json.loads(res.read().decode())
            assert sync_res["status"] == "COMPLETED"
    print("[PASS] 3 consecutive SAP S/4HANA sync executions completed with 0 UniqueViolation collisions.")

    print("\n==================================================")
    print("ALL SUSTAINED LOAD & INTEGRITY CHECKS PASSED (100%)")
    print("==================================================")

if __name__ == "__main__":
    run_stress_test()
