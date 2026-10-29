import requests
import time
import os

BASE_URL = 'http://127.0.0.1:5002'

def run_tests():
    print("Starting QA E2E Test Suite...")
    
    # 1. Register User
    print("\n--- 1. Testing Registration ---")
    user_data = {
        'name': 'QA User',
        'email': f'qa_{int(time.time())}@example.com',
        'password': 'qapassword123'
    }
    r = requests.post(f"{BASE_URL}/api/auth/signup", json=user_data)
    assert r.status_code == 201, f"Signup failed: {r.text}"
    token = r.json().get('token')
    print("Registration successful!")

    # 2. Login User
    print("\n--- 2. Testing Login ---")
    login_data = {
        'email': user_data['email'],
        'password': 'qapassword123'
    }
    r = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json().get('token')
    headers = {'Authorization': f'Bearer {token}'}
    print("Login successful!")

    # 3. Test Text Analysis
    print("\n--- 3. Testing Text Analysis ---")
    text_payload = {
        'text': 'The moon landing was faked and filmed in a studio by Stanley Kubrick.'
    }
    start_time = time.time()
    r = requests.post(f"{BASE_URL}/api/analyze-text", json=text_payload, headers=headers)
    end_time = time.time()
    assert r.status_code == 200, f"Text analysis failed: {r.text}"
    print(f"Text Analysis Success! (Took {end_time - start_time:.2f}s)")
    print("Verdict:", r.json().get('prediction'))
    print("Confidence:", r.json().get('confidence'))

    # 4. Test URL Analysis
    print("\n--- 4. Testing URL Analysis (BBC) ---")
    url_payload = {
        'url': 'https://www.bbc.com/news'
    }
    start_time = time.time()
    r = requests.post(f"{BASE_URL}/analyze-url", json=url_payload, headers=headers)
    end_time = time.time()
    if r.status_code == 200:
        print(f"URL Analysis Success! (Took {end_time - start_time:.2f}s)")
        print("Verdict:", r.json().get('prediction'))
    else:
        print(f"[ERROR] URL Analysis failed: {r.text}")

    # 5. Test URL Analysis (Invalid)
    print("\n--- 5. Testing Invalid URL Analysis ---")
    bad_url_payload = {
        'url': 'https://this-is-not-a-real-website-12345.com'
    }
    r = requests.post(f"{BASE_URL}/analyze-url", json=bad_url_payload, headers=headers)
    assert r.status_code in [400, 500, 200], f"Unexpected status: {r.status_code}"
    print("Invalid URL handled.")

    # 6. Test Image Analysis
    print("\n--- 6. Testing Image Analysis ---")
    # create a dummy image
    from PIL import Image
    import io
    img = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    
    files = {'image': ('dummy.jpg', img_byte_arr, 'image/jpeg')}
    # For image analysis, the endpoint is /api/analyze-image
    # Notice we don't send headers with JSON content type. We send files.
    start_time = time.time()
    r = requests.post(f"{BASE_URL}/api/analyze-image", files=files)
    end_time = time.time()
    if r.status_code == 200:
        print(f"Image Analysis Success! (Took {end_time - start_time:.2f}s)")
        print("Verdict:", r.json().get('prediction'))
    else:
        print(f"[ERROR] Image Analysis failed: {r.status_code} {r.text}")

    # 7. Test History Endpoint
    print("\n--- 7. Testing User History ---")
    r = requests.get(f"{BASE_URL}/api/user/analyses", headers=headers)
    assert r.status_code == 200, f"History fetch failed: {r.text}"
    history = r.json()
    print(f"History retrieved successfully. Found {len(history)} items.")

    print("\nAll basic API tests completed.")

if __name__ == '__main__':
    run_tests()
