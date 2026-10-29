#!/usr/bin/env python3
"""Factify - Full System Verification Script (v2)"""
import requests
import json
import sys
import time

BASE = 'http://127.0.0.1:5002'
PASS = 0
FAIL = 0
RESULTS = []

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        icon = "[PASS]"
    else:
        FAIL += 1
        icon = "[FAIL]"
    msg = f"  {icon} {name}"
    if detail:
        msg += f"  ->  {detail}"
    print(msg)
    RESULTS.append((name, icon, detail))

print("=" * 65)
print("  FACTIFY AI - FULL SYSTEM VERIFICATION")
print("=" * 65)

# 1. HEALTH CHECK
print("\n-- 1. Health Check --")
try:
    r = requests.get(f"{BASE}/health", timeout=10)
    data = r.json()
    test("Health endpoint reachable", r.status_code == 200, f"Status: {data.get('status')}")
except Exception as e:
    test("Health endpoint reachable", False, str(e))
    print("Server unreachable - aborting.")
    sys.exit(1)

# 2. FRONTEND PAGES
print("\n-- 2. Frontend Pages --")
for path, label in [("/", "index.html"), ("/dashboard", "dashboard.html"), ("/admin/dashboard", "admin_dashboard.html")]:
    r = requests.get(f"{BASE}{path}", timeout=10)
    test(f"{label} serves correctly", r.status_code == 200 and len(r.text) > 1000, f"{len(r.text)} bytes")

# 3. STATIC ASSETS
print("\n-- 3. Static Assets (CSS/JS) --")
assets = ["base.css", "style.css", "components.css", "user_dashboard.css", "admin.css", "script.js", "i18n.js", "admin.js"]
for a in assets:
    r = requests.get(f"{BASE}/{a}", timeout=10)
    test(f"Asset {a}", r.status_code == 200 and len(r.content) > 50, f"{len(r.content)} bytes")

# 4. AUTH
print("\n-- 4. Authentication --")
unique = str(int(time.time()))
signup_data = {"name": "TestBot", "email": f"test_{unique}@factify.com", "password": "SecurePass123!"}
r = requests.post(f"{BASE}/api/auth/signup", json=signup_data, timeout=10)
test("User signup", r.status_code == 201 and "token" in r.json(), f"Status {r.status_code}")
user_token = r.json().get("token", "")

login_data = {"email": signup_data["email"], "password": signup_data["password"]}
r = requests.post(f"{BASE}/api/auth/login", json=login_data, timeout=10)
test("User login", r.status_code == 200 and "token" in r.json(), f"Status {r.status_code}")
user_token = r.json().get("token", user_token)

headers = {"Authorization": f"Bearer {user_token}"}
r = requests.get(f"{BASE}/api/auth/me", headers=headers, timeout=10)
d = r.json()
email_found = d.get("email") or (d.get("user", {}) or {}).get("email", "")
test("GET /api/auth/me (profile)", r.status_code == 200 and email_found == signup_data["email"], email_found)

admin_data = {"email": "admin@factify.com", "password": "AdminSecure2026!"}
r = requests.post(f"{BASE}/api/auth/login", json=admin_data, timeout=10)
admin_ok = r.status_code == 200 and "token" in r.json()
test("Admin login", admin_ok, f"Status {r.status_code}")
admin_token = r.json().get("token", "") if admin_ok else ""
admin_headers = {"Authorization": f"Bearer {admin_token}"}

# 5. TEXT ANALYSIS
print("\n-- 5. Text Analysis Engine --")
fake_text = "SHOCKING leaked document proves government banned miracle cure! Big pharma is suppressing reverse aging technology before it gets deleted. Scientists have been silenced by a deep state conspiracy."
r = requests.post(f"{BASE}/api/analyze-text", json={"text": fake_text}, headers=headers, timeout=15)
d = r.json()
prediction = (d.get("prediction") or "").upper()
test("Fake news detection", r.status_code == 200 and prediction in ["FAKE", "SUSPICIOUS"],
     f"Verdict: {d.get('prediction')} | Confidence: {d.get('confidence')}%")
test("Emotions analysis present", "emotions" in d or "emotion_analysis" in d)
test("Manipulation score present", "manipulation" in d or "clickbait_score" in d)
test("Suspicious sentences present", "suspicious_sentences" in d, f"Count: {len(d.get('suspicious_sentences', []))}")
test("Credibility score present", "credibility" in d or "trust_score" in d, f"Credibility: {d.get('credibility') or d.get('trust_score')}")
test("Analysis reasoning present", "reason" in d or "reasoning" in d)

real_text = "The United Nations Security Council held a meeting on Tuesday to discuss the ongoing humanitarian crisis. Representatives from 15 member states participated in the session, which resulted in a joint statement calling for increased aid delivery to affected regions."
r = requests.post(f"{BASE}/api/analyze-text", json={"text": real_text}, headers=headers, timeout=15)
d = r.json()
prediction = (d.get("prediction") or "").upper()
test("Real news detection", r.status_code == 200 and prediction in ["REAL", "LIKELY REAL", "UNCERTAIN"],
     f"Verdict: {d.get('prediction')} | Confidence: {d.get('confidence')}%")

# 6. URL ANALYSIS
print("\n-- 6. URL Analysis Engine --")
r = requests.post(f"{BASE}/analyze-url", json={"url": "https://www.bbc.com/news"}, headers=headers, timeout=20)
test("URL analysis endpoint", r.status_code == 200, f"Status: {r.status_code}")

# 7. FEEDBACK
print("\n-- 7. Feedback System --")
fb = {"name": "TestBot", "email": signup_data["email"], "subject": "Review", "rating": 5, "message": "Great tool for fact-checking!"}
r = requests.post(f"{BASE}/api/feedback", json=fb, headers=headers, timeout=10)
test("Submit feedback (auth)", r.status_code in [200, 201], f"Status {r.status_code}")

r = requests.get(f"{BASE}/api/feedback", timeout=10)
test("Get public feedback list", r.status_code == 200 and isinstance(r.json(), list), f"Count: {len(r.json())}")

# 8. CONTACT
print("\n-- 8. Contact Form --")
contact = {"name": "TestBot", "email": signup_data["email"], "subject": "Test", "message": "Automated test message"}
r = requests.post(f"{BASE}/api/contact", json=contact, timeout=10)
test("Submit contact form", r.status_code in [200, 201], f"Status {r.status_code}")

# 9. USER DASHBOARD
print("\n-- 9. User Dashboard --")
r = requests.get(f"{BASE}/api/user/analyses", headers=headers, timeout=10)
test("Get user scan history", r.status_code == 200, f"Records: {len(r.json()) if isinstance(r.json(), list) else 'N/A'}")

# 10. CHATBOT
print("\n-- 10. Chatbot Assistant --")
r = requests.post(f"{BASE}/api/chat", json={"message": "What is Factify?"}, timeout=15)
has_reply = r.status_code == 200 and ("reply" in r.json() or "response" in r.json())
reply_text = r.json().get("reply") or r.json().get("response", "")
test("Chatbot responds", has_reply and len(reply_text) > 10, f"Reply length: {len(reply_text)} chars")

# 11. ADMIN
print("\n-- 11. Admin Endpoints --")
if admin_token:
    r = requests.get(f"{BASE}/api/admin/stats", headers=admin_headers, timeout=10)
    test("Admin stats", r.status_code == 200, f"Users: {r.json().get('total_users', '?')}")

    r = requests.get(f"{BASE}/api/admin/users", headers=admin_headers, timeout=10)
    test("Admin list users", r.status_code == 200 and isinstance(r.json(), list), f"Count: {len(r.json())}")

    r = requests.get(f"{BASE}/api/admin/analyses", headers=admin_headers, timeout=10)
    test("Admin list analyses", r.status_code == 200, f"Count: {len(r.json()) if isinstance(r.json(), list) else '?'}")

    r = requests.get(f"{BASE}/api/admin/feedbacks", headers=admin_headers, timeout=10)
    test("Admin list feedbacks", r.status_code == 200, f"Count: {len(r.json()) if isinstance(r.json(), list) else '?'}")

    r = requests.get(f"{BASE}/api/admin/contacts", headers=admin_headers, timeout=10)
    test("Admin list contacts", r.status_code == 200, f"Count: {len(r.json()) if isinstance(r.json(), list) else '?'}")

    # RBAC check
    r = requests.get(f"{BASE}/api/admin/stats", headers=headers, timeout=10)
    test("RBAC: Regular user blocked from admin", r.status_code == 403, f"Status: {r.status_code}")

# 12. NEWS
print("\n-- 12. Live News API --")
r = requests.get(f"{BASE}/api/news", headers=admin_headers, timeout=15)
test("GET /api/news (trending headlines)", r.status_code == 200, f"Status: {r.status_code}")

# SUMMARY
print("\n" + "=" * 65)
total = PASS + FAIL
print(f"  RESULTS: {PASS}/{total} passed  |  {FAIL} failed")
if FAIL == 0:
    print("  ALL TESTS PASSED - Project is fully operational!")
else:
    print(f"  {FAIL} test(s) need attention:")
    for name, status, detail in RESULTS:
        if status == "[FAIL]":
            print(f"     X {name}: {detail}")
print("=" * 65)
