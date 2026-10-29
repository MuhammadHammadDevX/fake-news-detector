import requests
import sys
import pymongo

BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5002')

def clear_db():
    print("Clearing database collections to ensure a clean test run...")
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['factify_db']
    db.users.delete_many({})
    db.feedbacks.delete_many({})
    db.analyses.delete_many({})
    print("Database cleared!")

def run_tests():
    print("Starting API Integration Tests...")
    
    # 1. Register first user (should become admin)
    print("\n--- 1. Registering Admin User ---")
    admin_signup_data = {
        'name': 'Admin User',
        'email': 'admin@example.com',
        'password': 'adminpassword'
    }
    r = requests.post(f"{BASE_URL}/api/auth/signup", json=admin_signup_data)
    assert r.status_code == 201, f"Admin signup failed: {r.text}"
    admin_data = r.json()
    print("Admin registration successful!")
    print("User info:", admin_data['user'])
    admin_token = admin_data['token']
    assert admin_data['user']['role'] == 'admin', "First user should be admin"

    # 2. Login as Admin
    print("\n--- 2. Logging in as Admin ---")
    admin_login_data = {
        'email': 'admin@example.com',
        'password': 'adminpassword'
    }
    r = requests.post(f"{BASE_URL}/api/auth/login", json=admin_login_data)
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    admin_login_res = r.json()
    print("Admin login successful!")
    assert 'token' in admin_login_res, "Login response must contain a token"

    # 3. Check Admin Stats (should show 1 user, 0 feedback, 0 analyses)
    print("\n--- 3. Checking Admin Stats (Initial) ---")
    headers = {'Authorization': f"Bearer {admin_login_res['token']}"}
    r = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
    assert r.status_code == 200, f"Admin stats failed: {r.text}"
    stats = r.json()
    print("Stats:", stats)
    assert stats['total_users'] == 1
    assert stats['total_feedbacks'] == 0
    assert stats['total_analyses'] == 0

    # 4. Register second user (should be a regular user)
    print("\n--- 4. Registering Regular User ---")
    user_signup_data = {
        'name': 'Regular User',
        'email': 'user@example.com',
        'password': 'userpassword'
    }
    r = requests.post(f"{BASE_URL}/api/auth/signup", json=user_signup_data)
    assert r.status_code == 201, f"User signup failed: {r.text}"
    user_data = r.json()
    print("User registration successful!")
    print("User info:", user_data['user'])
    user_token = user_data['token']
    assert user_data['user']['role'] == 'user', "Second user should be a regular user"

    # 5. Non-admin trying to access admin stats (should be forbidden)
    print("\n--- 5. Testing Forbidden Access ---")
    user_headers = {'Authorization': f"Bearer {user_token}"}
    r = requests.get(f"{BASE_URL}/api/admin/stats", headers=user_headers)
    assert r.status_code == 403, f"Expected 403 Forbidden, got {r.status_code}: {r.text}"
    print("Correctly received 403 Forbidden for non-admin")

    # 6. Submit Feedback
    print("\n--- 6. Submitting Feedback ---")
    feedback_data = {
        'name': 'Regular User',
        'email': 'user@example.com',
        'subject': 'Great App!',
        'message': 'This is a fantastic tool to detect fake news. Keep up the good work!',
        'rating': 5
    }
    r = requests.post(f"{BASE_URL}/api/feedback", json=feedback_data)
    assert r.status_code == 201, f"Feedback submission failed: {r.text}"
    print("Feedback submitted successfully!")

    # 7. Get feedbacks (public list)
    print("\n--- 7. Fetching Public Feedbacks ---")
    r = requests.get(f"{BASE_URL}/api/feedback")
    assert r.status_code == 200, f"Get feedbacks failed: {r.text}"
    feedbacks = r.json()
    print(f"Retrieved {len(feedbacks)} feedbacks")
    assert len(feedbacks) == 1
    assert feedbacks[0]['rating'] == 5
    feedback_id = feedbacks[0]['_id']

    # 8. Run Text Analysis (without auth first - optional but saves as anonymous)
    print("\n--- 8. Running Text Analysis (Anonymous) ---")
    text_data = {
        'text': 'Breaking: Scientists discover a new species of flying cats in the Amazon rainforest.'
    }
    r = requests.post(f"{BASE_URL}/api/analyze-text", json=text_data)
    assert r.status_code == 200, f"Text analysis failed: {r.text}"
    analysis_res = r.json()
    print("Text analysis completed successfully! Prediction:", analysis_res.get('prediction'))
    assert 'prediction' in analysis_res
    assert 'confidence' in analysis_res
    assert 'cross_references' in analysis_res, "Response must contain 'cross_references'"

    # 9. Run Text Analysis with Auth (saves with user email)
    print("\n--- 9. Running Text Analysis (Authenticated) ---")
    r = requests.post(f"{BASE_URL}/api/analyze-text", json=text_data, headers=user_headers)
    assert r.status_code == 200, f"Text analysis with auth failed: {r.text}"
    analysis_res_auth = r.json()
    assert 'cross_references' in analysis_res_auth, "Response must contain 'cross_references'"
    print("Authenticated text analysis completed!")

    # 10. Run URL Analysis (use local homepage URL so we don't need internet)
    print("\n--- 10. Running URL Analysis ---")
    url_data = {
        'url': f"{BASE_URL}/"
    }
    r = requests.post(f"{BASE_URL}/analyze-url", json=url_data, headers=user_headers)
    assert r.status_code == 200, f"URL analysis failed: {r.text}"
    url_res = r.json()
    print("URL analysis completed successfully! Prediction:", url_res.get('prediction'))
    assert 'prediction' in url_res
    assert 'cross_references' in url_res, "Response must contain 'cross_references'"

    # Keep track of expected successful analyses saved in MongoDB
    expected_analyses = 3

    # 10a. Run URL Analysis on YouTube
    print("\n--- 10a. Running YouTube URL Analysis ---")
    yt_data = {
        'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    }
    r = requests.post(f"{BASE_URL}/analyze-url", json=yt_data, headers=user_headers)
    assert r.status_code in [200, 400], f"YouTube analysis crashed or failed: {r.text}"
    if r.status_code == 200:
        expected_analyses += 1
        yt_res = r.json()
        assert 'prediction' in yt_res
        assert 'cross_references' in yt_res
        print("YouTube analysis completed successfully! Prediction:", yt_res.get('prediction'))
    else:
        print("YouTube analysis returned 400 (expected behavior if scraping/transcript failed), which is handled.")

    # 10b. Run URL Analysis on Reddit
    print("\n--- 10b. Running Reddit URL Analysis ---")
    reddit_data = {
        'url': 'https://www.reddit.com/r/news/comments/123456/test_post/'
    }
    r = requests.post(f"{BASE_URL}/analyze-url", json=reddit_data, headers=user_headers)
    assert r.status_code in [200, 400], f"Reddit analysis crashed or failed: {r.text}"
    if r.status_code == 200:
        expected_analyses += 1
        reddit_res = r.json()
        assert 'prediction' in reddit_res
        assert 'cross_references' in reddit_res
        print("Reddit analysis completed successfully! Prediction:", reddit_res.get('prediction'))
    else:
        print("Reddit analysis returned 400 (expected behavior if scraping post data failed), which is handled.")

    # 10c. Run Analysis on Known Fake Claim (Pope Francis endorses Donald Trump)
    print("\n--- 10c. Running Known Fake Claim Analysis ---")
    fake_claim_data = {
        'text': 'Pope Francis has shocked the world by endorsing Donald Trump for president.'
    }
    r = requests.post(f"{BASE_URL}/api/analyze-text", json=fake_claim_data, headers=user_headers)
    assert r.status_code == 200, f"Fake claim analysis failed: {r.text}"
    expected_analyses += 1
    fake_res = r.json()
    print("Fake claim analysis completed! Prediction:", fake_res.get('prediction'))
    assert 'prediction' in fake_res
    assert 'cross_references' in fake_res
    
    # Check if we got debunked cross-references
    has_debunked = any(ref['category'] == 'Fact Check (Debunked)' for ref in fake_res.get('cross_references', []))
    print(f"Has debunked cross-references: {has_debunked}")
    if has_debunked:
        assert fake_res['prediction'] == 'Fake', "Should be overridden to Fake"
        print("Successfully verified: Fake claim got overridden to Fake by search results!")

    # 11. Check Admin Stats (should show 2 users, 1 feedback, expected_analyses)
    print("\n--- 11. Checking Admin Stats (Updated) ---")
    r = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
    assert r.status_code == 200, f"Admin stats failed: {r.text}"
    stats = r.json()
    print("Updated Stats:", stats)
    assert stats['total_users'] == 2
    assert stats['total_feedbacks'] == 1
    assert stats['total_analyses'] == expected_analyses

    # 12. Check Admin Lists (Users, Feedbacks, Analyses)
    print("\n--- 12. Retrieving Admin Panels Data ---")
    r_users = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
    assert r_users.status_code == 200
    users_list = r_users.json()
    print(f"Admin Users list count: {len(users_list)}")
    assert len(users_list) == 2

    r_feedbacks = requests.get(f"{BASE_URL}/api/admin/feedbacks", headers=headers)
    assert r_feedbacks.status_code == 200
    feedbacks_list = r_feedbacks.json()
    print(f"Admin Feedbacks list count: {len(feedbacks_list)}")
    assert len(feedbacks_list) == 1

    r_analyses = requests.get(f"{BASE_URL}/api/admin/analyses", headers=headers)
    assert r_analyses.status_code == 200
    analyses_list = r_analyses.json()
    print(f"Admin Analyses list count: {len(analyses_list)}")
    assert len(analyses_list) == expected_analyses

    # 13. Delete Feedback
    print("\n--- 13. Deleting Feedback ---")
    r = requests.delete(f"{BASE_URL}/api/admin/feedback/{feedback_id}", headers=headers)
    assert r.status_code == 200, f"Feedback deletion failed: {r.text}"
    print("Feedback deleted successfully!")

    # Verify feedback count is now 0
    r = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
    assert r.json()['total_feedbacks'] == 0
    print("Verified feedback count is 0 in stats!")

    # 14. Delete User
    print("\n--- 14. Deleting Regular User ---")
    regular_user_id = user_data['user']['id']
    r = requests.delete(f"{BASE_URL}/api/admin/user/{regular_user_id}", headers=headers)
    assert r.status_code == 200, f"User deletion failed: {r.text}"
    print("User deleted successfully!")

    # Verify user count is now 1
    r = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
    assert r.json()['total_users'] == 1
    print("Verified user count is 1 in stats!")

    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    try:
        clear_db()
        run_tests()
    except AssertionError as e:
        print(f"\nTEST FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        sys.exit(1)
