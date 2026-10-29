import requests
import json

BASE = 'http://127.0.0.1:5002'

print("=" * 60)
print("  FACTIFY - FULL FEATURE TEST")
print("=" * 60)

# 1. HEALTH
print("\n[1] HEALTH CHECK")
r = requests.get(f'{BASE}/health')
h = r.json()
print(f"    Status: {r.status_code} | Server: {h.get('status')} | Model Trained: {h.get('model_trained')}")

# 2. LOGIN
print("\n[2] LOGIN")
r = requests.post(f'{BASE}/api/auth/login', json={'email': 'test@factify.com', 'password': 'test123456'})
data = r.json()
token = data.get('token', '')
user = data.get('user', {})
print(f"    Status: {r.status_code} | User: {user.get('name')} | Role: {user.get('role')}")
if not token:
    print("    ERROR: No token received - cannot continue tests")
    exit(1)

HEADERS = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# 3. FAKE NEWS TEXT
print("\n[3] ANALYZE FAKE NEWS (Text Mode)")
fake_text = ('SHOCKING: Scientists PROVE that drinking bleach cures COVID-19 instantly! '
             'The government is HIDING this secret cure from the public! '
             'Share before they DELETE this! Thousands of doctors have been SILENCED!')
r = requests.post(f'{BASE}/api/analyze-text', json={'text': fake_text}, headers=HEADERS)
res = r.json()
print(f"    Status: {r.status_code}")
print(f"    Prediction:  {res.get('prediction')}")
print(f"    Confidence:  {res.get('confidence')}%")
print(f"    Credibility: {res.get('credibility')}%")
print(f"    Manipulation: {res.get('manipulation')}")
print(f"    Emotions:    {res.get('emotions')}")
print(f"    Suspicious sentences: {len(res.get('suspicious_sentences', []))}")
print(f"    Cross-references:     {len(res.get('cross_references', []))}")
print(f"    Reason (preview): {str(res.get('reason',''))[:120]}...")

# 4. REAL NEWS TEXT
print("\n[4] ANALYZE REAL NEWS (Text Mode)")
real_text = ('The World Health Organization released its annual health report indicating '
             'a 12 percent decline in global malaria cases compared to the previous year. '
             'The report attributed progress to improved access to antimalarial drugs in '
             'sub-Saharan Africa. Health officials emphasized the need for continued investment.')
r = requests.post(f'{BASE}/api/analyze-text', json={'text': real_text}, headers=HEADERS)
res = r.json()
print(f"    Status: {r.status_code}")
print(f"    Prediction:  {res.get('prediction')}")
print(f"    Confidence:  {res.get('confidence')}%")
print(f"    Credibility: {res.get('credibility')}%")
print(f"    Reason (preview): {str(res.get('reason',''))[:120]}...")

# 5. URL ANALYSIS
print("\n[5] ANALYZE URL")
r = requests.post(f'{BASE}/analyze-url', json={'url': 'https://www.bbc.com/news'}, headers=HEADERS, timeout=20)
print(f"    Status: {r.status_code}")
if r.ok:
    res = r.json()
    print(f"    Prediction: {res.get('prediction')} | Confidence: {res.get('confidence')}%")
else:
    print(f"    Error: {r.json().get('error', 'Unknown')[:100]}")

# 6. FEEDBACK - WITHOUT TOKEN (BUG CHECK)
print("\n[6] FEEDBACK FORM - BUG CHECK")
r_no_auth = requests.post(f'{BASE}/api/feedback',
    json={'name': 'Tester', 'email': 'test@factify.com', 'subject': 'Great!', 'message': 'Excellent tool!', 'rating': 5})
print(f"    Without token: Status={r_no_auth.status_code} -> Expected 401, Got: {r_no_auth.json().get('error','OK')}")

r_with_auth = requests.post(f'{BASE}/api/feedback',
    json={'name': 'Tester', 'email': 'test@factify.com', 'subject': 'Great!', 'message': 'Excellent tool!', 'rating': 5},
    headers=HEADERS)
print(f"    With token:    Status={r_with_auth.status_code} -> {r_with_auth.json().get('message', r_with_auth.json().get('error',''))}")

# 7. NEWS FEED
print("\n[7] LIVE NEWS FEED")
r = requests.get(f'{BASE}/api/news?category=general', headers=HEADERS, timeout=15)
print(f"    Status: {r.status_code}")
if r.ok:
    news = r.json()
    print(f"    Articles loaded: {len(news)}")
    if news:
        first = news[0]
        print(f"    First headline: {str(first.get('title',''))[:70]}")
        print(f"    Trust score: {first.get('trust')}% ({first.get('tag')})")
else:
    print(f"    Error: {r.json().get('error','')[:100]}")

# 8. USER HISTORY
print("\n[8] USER HISTORY (MongoDB)")
r = requests.get(f'{BASE}/api/user/analyses', headers=HEADERS)
print(f"    Status: {r.status_code}")
if r.ok:
    hist = r.json()
    print(f"    Records in history: {len(hist)}")
else:
    print(f"    Error: {r.json().get('error','')[:100]}")

# 9. TESTIMONIALS (no auth needed)
print("\n[9] TESTIMONIALS (Public)")
r = requests.get(f'{BASE}/api/feedback')
print(f"    Status: {r.status_code} | Items: {len(r.json()) if r.ok else 'ERROR'}")

# SUMMARY
print("\n" + "=" * 60)
print("  BUG FOUND: Feedback form in frontend sends no auth token!")
print("  The /api/feedback POST requires login, but script.js")
print("  does NOT include the Authorization header in feedbackForm.")
print("=" * 60)
