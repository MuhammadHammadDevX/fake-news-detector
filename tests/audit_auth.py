import requests
import json
import os

BASE_URL = "http://127.0.0.1:5002"

def run_tests():
    print("--- STARTING AUTHENTICATION AUDIT ---")
    
    # 1. Registration always creates 'user'
    print("[1] Testing Registration...")
    res = requests.post(f"{BASE_URL}/api/auth/signup", json={
        "name": "Audit User",
        "email": "audit1@example.com",
        "password": "Password123"
    })
    if res.status_code == 201:
        data = res.json()
        assert data['user']['role'] == 'user', f"Expected role 'user', got {data['user']['role']}"
        user_token = data['token']
        print("    [PASS] Registration creates normal user successfully.")
    else:
        print(f"    [FAIL] Registration failed: {res.text}")
        
    # 2. Login returns correct role
    print("[2] Testing Login...")
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "audit1@example.com",
        "password": "Password123"
    })
    assert res.status_code == 200, "Login failed"
    print("    [PASS] Login works for normal user.")
    
    # 3. Test predefined admin login (admin@factify.com)
    print("[3] Testing Admin Predefined Initialization...")
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@factify.com",
        "password": "AdminSecret2026!"
    })
    assert res.status_code == 200, "Admin login failed. Init script may not have run."
    admin_token = res.json()['token']
    assert res.json()['user']['role'] == 'admin', "Admin role not correct."
    print("    [PASS] Predefined Admin exists and has 'admin' role.")
    
    # 4. JWT & Admin Middleware Route Protection
    print("[4] Testing Backend Middleware Route Protection...")
    # Normal user accessing admin route
    res = requests.get(f"{BASE_URL}/api/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}"
    print("    [PASS] Normal user blocked from Admin API (403 Forbidden).")
    
    # Admin accessing admin route
    res = requests.get(f"{BASE_URL}/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200, f"Expected 200 OK, got {res.status_code}"
    print("    [PASS] Admin user allowed on Admin API.")
    
    # 5. Unauthorized access missing JWT
    res = requests.get(f"{BASE_URL}/api/admin/stats")
    assert res.status_code == 401, f"Expected 401 Unauthorized, got {res.status_code}"
    print("    [PASS] Missing JWT blocks access (401 Unauthorized).")

    # 6. Frontend Route serving
    print("[6] Testing Frontend Route Serving...")
    res = requests.get(f"{BASE_URL}/admin/dashboard")
    assert res.status_code == 200
    assert "factify_user" in res.text, "Admin dashboard HTML not served correctly."
    print("    [PASS] Admin HTML served on /admin/dashboard successfully with inline protection script.")
    
    print("--- ALL TESTS PASSED ---")

if __name__ == "__main__":
    run_tests()
