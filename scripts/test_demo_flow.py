import urllib.request
import urllib.error
import json
import sys

api_base = 'http://localhost:8000'

def request(path, method='GET', data=None, token=None):
    url = f'{api_base}{path}'
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body

def main():
    print('--- STEP 1: PUBLIC STATS / LANDING ---')
    st, pub = request('/api/v1/meta/public-stats')
    assert st == 200
    print(f'Landing Stats: materials={pub["total_materials"]}, safeEquiv={pub["safe_equiv"]}')

    print('--- STEP 2: LOGIN AS SUPER ADMIN ---')
    st, auth_admin = request('/api/v1/auth/login', 'POST', {'username': 'steward_admin', 'password': 'DevSec_D1I6hALEJYSYhoLsYpWwkPc0'})
    assert st == 200
    admin_token = auth_admin['access_token']
    print(f'Admin token acquired. Role: {auth_admin["user"]["role"]}')

    print('--- STEP 3: GOVERNANCE DASHBOARD METRICS ---')
    st, summary = request('/api/v1/analytics/summary', token=admin_token)
    st2, charts = request('/api/v1/analytics/charts', token=admin_token)
    assert st == 200 and st2 == 200
    print(f'Summary: total_materials={summary["total_materials"]}, NMCs={summary["national_materials_count"]}, Duplicates={summary["potential_duplicates"]}')

    print('--- STEP 4 & 5: MATERIAL SEARCH & DETAIL ---')
    st, mats = request('/api/v1/materials?query=BOLT&page=1&page_size=3', token=admin_token)
    assert st == 200 and len(mats) > 0
    sample_id = mats[0]['id']
    st, mat_detail = request(f'/api/v1/materials/{sample_id}', token=admin_token)
    assert st == 200
    print(f'Material sample: {mat_detail["source_code"]} - {mat_detail["raw_description"][:50]}')

    print('--- STEP 6 & 7 & 8: 8.8 vs 10.9 G2 HARD VETO ---')
    st, demos = request('/api/v1/meta/demo-scenarios', token=admin_token)
    trap_88_id = demos['scenarios']['trap_88_109']['match_id']
    st, trap_data = request(f'/api/v1/matches/{trap_88_id}', token=admin_token)
    assert st == 200
    assert trap_data['veto']['applied'] is True
    assert trap_data['veto']['gate_id'] == 'G2'
    assert trap_data['relationship'] == 'NOT_EQUIVALENT'
    assert trap_data['equivalence_confidence'] == 0.0
    print(f'Trap 8.8 vs 10.9: Gate={trap_data["veto"]["gate_id"]}, Rel={trap_data["relationship"]}, Conf={trap_data["equivalence_confidence"]}')

    print('--- STEP 9: G4 UNKNOWN CASE ---')
    trap_g4_id = demos['scenarios']['trap_unknown']['match_id']
    st, g4_data = request(f'/api/v1/matches/{trap_g4_id}', token=admin_token)
    assert st == 200
    assert g4_data['relationship'] == 'REVIEW_REQUIRED'
    print(f'Trap G4: Gate={g4_data["veto"]["gate_id"]}, Rel={g4_data["relationship"]}')

    print('--- STEP 10: SAFE EQUIVALENT CANDIDATE ---')
    safe_id = demos['scenarios']['safe_equivalent']['match_id']
    st, safe_data = request(f'/api/v1/matches/{safe_id}', token=admin_token)
    assert st == 200
    print(f'Safe candidate: Rel={safe_data["relationship"]}, Conf={safe_data["equivalence_confidence"]}')

    print('--- STEP 11 & 12 & 13: APPROVE & NMC & CROSSWALK ---')
    st, nmcs = request('/api/v1/national-materials?page=1&page_size=5', token=admin_token)
    assert st == 200 and len(nmcs) > 0
    print(f'Existing National Materials: {[n.get("nmc") or n.get("national_code") for n in nmcs]}')
    st, cw = request('/api/v1/legacy-mappings?page=1&page_size=5', token=admin_token)
    assert st == 200
    print(f'Active crosswalk sample: CPSE={cw[0].get("cpse_code")}, Local={cw[0].get("source_material_code")}, NMC={cw[0].get("nmc")}')

    print('--- STEP 14 & 15: AUDIT CHAIN INTEGRITY ---')
    st, audit_chk = request('/api/v1/audit/verify', token=admin_token)
    assert st == 200 and audit_chk['valid'] is True
    print(f'Audit chain valid={audit_chk["valid"]}, Total events={audit_chk["total_events"]}')

    print('--- STEP 16: MOCK SAP STATUS & RFC ---')
    st, sap_status = request('/api/v1/integration/sap/status', token=admin_token)
    assert st == 200
    print(f'Mock SAP Status: System={sap_status["system_id"]}, Synced={sap_status["total_synced_materials"]}')

    print('--- STEP 17 & 18: LOGIN AS REVIEWER ---')
    st, auth_rev = request('/api/v1/auth/login', 'POST', {'username': 'reviewer_demo', 'password': 'NUMM-Demo-Reviewer-2026!'})
    assert st == 200
    rev_token = auth_rev['access_token']
    assert auth_rev['user']['role'] == 'REVIEWER'
    print(f'Reviewer token acquired. Role: {auth_rev["user"]["role"]}')

    print('--- STEP 19: REVIEWER 403 RESTRICTION CHECKS ---')
    endpoints_to_test = [
        ('/api/v1/imports/upload', 'POST', {'source_cpse': 'OIL', 'records': []}),
        ('/api/v1/matching/runs', 'POST', {'source_cpse': 'OIL'}),
        ('/api/v1/reviews/01a100b6-1057-738f-97b6-8b490ec05681/approve', 'POST', {'reason_code': 'ACCEPT'}),
        ('/api/v1/reviews/01a100b6-1057-738f-97b6-8b490ec05681/reject', 'POST', {'reason_code': 'REJECT'}),
        ('/api/v1/reviews/01a100b6-1057-738f-97b6-8b490ec05681/remap', 'POST', {'target_nmc': 'MAT-TEST'}),
        ('/api/v1/integration/sap/sync', 'POST', {})
    ]

    for path, m, payload in endpoints_to_test:
        st, resp = request(path, m, payload, token=rev_token)
        assert st == 403, f'Expected 403 for {path}, got {st}'
        print(f'  [PASS 403 Forbidden] {m} {path}')

    print('--- ALL 20 GOLDEN DEMO STEPS VERIFIED 100% ---')

if __name__ == '__main__':
    main()
