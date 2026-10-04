import urllib.request
import urllib.parse
import json
import sys

def run_verification():
    print("==================================================")
    print("VERIFYING NUMM FULL PLATFORM ENDPOINTS & ROUTES")
    print("==================================================")
    
    api_base = "http://localhost:8000"
    web_base = "http://localhost:3000"
    
    # 1. Health check
    req = urllib.request.Request(f"{api_base}/health")
    with urllib.request.urlopen(req) as res:
        health = json.loads(res.read().decode())
        print(f"[PASS] API Health: {health}")
        assert health["status"] == "ok"
        
    # 2. Login as steward_admin
    pwd = "DevSec_D1I6hALEJYSYhoLsYpWwkPc0"
    login_data = json.dumps({"username": "steward_admin", "password": pwd}).encode()
    req = urllib.request.Request(f"{api_base}/api/v1/auth/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        auth_data = json.loads(res.read().decode())
        token = auth_data["access_token"]
        print(f"[PASS] Auth Login: Token acquired for user {auth_data['user']['username']} (Role: {auth_data['user']['role']})")
        
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2b. Login as reviewer_demo
    rev_login_data = json.dumps({"username": "reviewer_demo", "password": "NUMM-Demo-Reviewer-2026!"}).encode()
    req_rev = urllib.request.Request(f"{api_base}/api/v1/auth/login", data=rev_login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_rev) as res:
        rev_auth_data = json.loads(res.read().decode())
        print(f"[PASS] Reviewer Auth Login: Acquired for {rev_auth_data['user']['username']} (Role: {rev_auth_data['user']['role']})")
        assert rev_auth_data["user"]["role"] == "REVIEWER"

    # 2c. Review Queue Summary Counts (All 4 states visible)
    req_counts = urllib.request.Request(f"{api_base}/api/v1/reviews/summary/counts", headers=auth_headers)
    with urllib.request.urlopen(req_counts) as res:
        counts = json.loads(res.read().decode())
        print(f"[PASS] Review Queue Summary Counts: Total={counts['total']}, Safe={counts['safe_equiv']}, Conflict={counts['conflict']}, Unknown={counts['unknown']}, LowConf={counts['low_conf']}")
        assert counts["total"] > 0
        assert counts["safe_equiv"] > 0
        assert counts["conflict"] > 0
        assert counts["unknown"] > 0

    # 3. Demo Scenarios
    req = urllib.request.Request(f"{api_base}/api/v1/meta/demo-scenarios", headers=auth_headers)
    with urllib.request.urlopen(req) as res:
        demo_data = json.loads(res.read().decode())
        scenarios = demo_data["scenarios"]
        print(f"[PASS] Demo Scenarios: 8.8 vs 10.9 Trap={scenarios['trap_88_109']['match_id']}, Gate={scenarios['trap_88_109']['gate']}")
        print(f"    G4 Missing Grade Trap={scenarios['trap_unknown']['match_id']}, Gate={scenarios['trap_unknown']['gate']}")
        print(f"    Safe Equivalence={scenarios['safe_equivalent']['match_id']}")
        
    # 4. Inspect 8.8 vs 10.9 trap
    trap_id = scenarios['trap_88_109']['match_id']
    req = urllib.request.Request(f"{api_base}/api/v1/matches/{trap_id}", headers=auth_headers)
    with urllib.request.urlopen(req) as res:
        match_data = json.loads(res.read().decode())
        assert match_data["veto"]["applied"] is True
        assert match_data["veto"]["gate_id"] == "G2"
        assert match_data["relationship"] == "NOT_EQUIVALENT"
        assert match_data["equivalence_confidence"] == 0.0
        print(f"[PASS] Veto Gate G2 Verified: {match_data['veto']['reason']}")
        print(f"    Material A: {match_data['material_a']['raw_description']}")
        print(f"    Material B: {match_data['material_b']['raw_description']}")
        
    # 5. Materials listing & detail
    req = urllib.request.Request(f"{api_base}/api/v1/materials?page=1&page_size=5", headers=auth_headers)
    with urllib.request.urlopen(req) as res:
        materials = json.loads(res.read().decode())
        sample_mat = materials[0]
        print(f"[PASS] Materials Listing: Retrieved {len(materials)} materials. Sample: {sample_mat['id']}")
        
    req = urllib.request.Request(f"{api_base}/api/v1/materials/{sample_mat['id']}", headers=auth_headers)
    with urllib.request.urlopen(req) as res:
        mat_detail = json.loads(res.read().decode())
        print(f"[PASS] Material Detail: {mat_detail['source_code']} - {mat_detail['raw_description']}")
        print(f"    Extracted attributes count: {len(mat_detail['attributes'])}")
        print(f"    Recent matches count: {len(mat_detail['recent_matches'])}")
        
    # 6. Mock SAP Sync
    req = urllib.request.Request(f"{api_base}/api/v1/integration/sap/sync", data=b"{}", headers={"Content-Type": "application/json", **auth_headers})
    with urllib.request.urlopen(req) as res:
        sync_result = json.loads(res.read().decode())
        print(f"[PASS] Mock SAP Sync: Job {sync_result['sync_id']} status={sync_result['status']}, processed={sync_result['records_exported']}")
        
    # 7. Mock SAP Status & Materials
    req = urllib.request.Request(f"{api_base}/api/v1/integration/sap/status", headers=auth_headers)
    with urllib.request.urlopen(req) as res:
        sap_status = json.loads(res.read().decode())
        print(f"[PASS] Mock SAP Hub Status: S/4HANA System={sap_status['system_id']}, Synced Materials={sap_status['total_synced_materials']}")
        
    req = urllib.request.Request(f"{api_base}/api/v1/integration/sap/materials?page=1&page_size=5", headers=auth_headers)
    with urllib.request.urlopen(req) as res:
        sap_mats = json.loads(res.read().decode())
        print(f"[PASS] Mock SAP Materials: Sample MATNR={sap_mats[0]['sap_product_id']}, MAKTX={sap_mats[0]['product_description']}")
        
    # 8. Procurement Analytics
    req = urllib.request.Request(f"{api_base}/api/v1/analytics/procurement", headers=auth_headers)
    with urllib.request.urlopen(req) as res:
        analytics = json.loads(res.read().decode())
        print(f"[PASS] Procurement Analytics: Shared NMCs={analytics['cpse_sharing_nmc_count']}, Total Duplicates={analytics['duplicate_materials_count']}")
        print(f"    Top Consolidation Categories: {[c['category_code'] for c in analytics['top_consolidation_opportunities']]}")
        
    # 9. Audit Chain Verification
    req = urllib.request.Request(f"{api_base}/api/v1/audit/verify", headers=auth_headers)
    with urllib.request.urlopen(req) as res:
        audit_verify = json.loads(res.read().decode())
        print(f"[PASS] Audit Chain Verification: Valid={audit_verify['valid']}, Total Events={audit_verify['total_events']}")
        assert audit_verify["valid"] is True
        
    # 10. Crosswalk Export
    req = urllib.request.Request(f"{api_base}/api/v1/exports/crosswalk.csv", headers=auth_headers)
    with urllib.request.urlopen(req) as res:
        crosswalk_csv = res.read().decode()
        lines = crosswalk_csv.strip().splitlines()
        print(f"[PASS] Crosswalk CSV Export: Generated {len(lines)} lines (Header: {lines[0]})")
        
    # 11. Frontend Routes
    routes = ["/", "/login", "/governance", "/matching", "/reviews", "/materials", "/national-materials", "/analytics", "/audit", "/integration"]
    for route in routes:
        req = urllib.request.Request(f"{web_base}{route}")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            print(f"[PASS] Web Route {route} is UP (HTTP 200)")
            
    print("\n==================================================")
    print("ALL NUMM GOLDEN PATH RUNTIME CHECKS PASSED (100%)")
    print("==================================================")

if __name__ == "__main__":
    run_verification()
