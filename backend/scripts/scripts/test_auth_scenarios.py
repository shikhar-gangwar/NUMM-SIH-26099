import requests

def test_auth():
    api = 'http://localhost:8000/api/v1/auth'

    # 1. Super Admin
    r_admin = requests.post(f'{api}/login', json={'username': 'steward_admin', 'password': 'DevSec_D1I6hALEJYSYhoLsYpWwkPc0'})
    assert r_admin.status_code == 200, f'Admin login failed: {r_admin.text}'
    admin_data = r_admin.json()
    assert admin_data['user']['role'] == 'SUPER_ADMIN'
    print('[PASS] SUPER_ADMIN login successful:', admin_data['user']['username'])

    # 2. Reviewer
    r_rev = requests.post(f'{api}/login', json={'username': 'reviewer_demo', 'password': 'NUMM-Demo-Reviewer-2026!'})
    assert r_rev.status_code == 200, f'Reviewer login failed: {r_rev.text}'
    rev_data = r_rev.json()
    assert rev_data['user']['role'] == 'REVIEWER'
    print('[PASS] REVIEWER login successful:', rev_data['user']['username'])

    # 3. Invalid password
    r_bad_pw = requests.post(f'{api}/login', json={'username': 'steward_admin', 'password': 'WrongPassword123!'})
    assert r_bad_pw.status_code == 401, f'Expected 401, got {r_bad_pw.status_code}'
    print('[PASS] Invalid password rejected with HTTP 401:', r_bad_pw.json())

    # 4. Invalid username
    r_bad_user = requests.post(f'{api}/login', json={'username': 'nonexistent_user', 'password': 'any_password'})
    assert r_bad_user.status_code == 401, f'Expected 401, got {r_bad_user.status_code}'
    print('[PASS] Nonexistent user rejected with HTTP 401:', r_bad_user.json())

    # 5. Auth /me endpoint check
    r_me = requests.get(f'{api}/me', headers={'Authorization': f"Bearer {admin_data['access_token']}"})
    assert r_me.status_code == 200, f'/me failed: {r_me.text}'
    print('[PASS] /me endpoint verified for token holder:', r_me.json()['username'])

    print('\nALL AUTH SCENARIOS VERIFIED 100%')

if __name__ == '__main__':
    test_auth()
