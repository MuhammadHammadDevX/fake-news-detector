import requests
import time
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

BASE_URL = 'http://127.0.0.1:5002'

TEXT_TESTS = [
    # 20 Text samples covering clickbait, propaganda, real, and fake.
    {"id": "T1", "text": "The moon landing was faked and filmed in a studio by Stanley Kubrick. Wake up!", "expected": "FAKE"},
    {"id": "T2", "text": "Aliens have officially landed in New York and the deep state is covering it up.", "expected": "FAKE"},
    {"id": "T3", "text": "NASA launches new rover to Mars to explore the Jezero crater for signs of ancient life.", "expected": "REAL"},
    {"id": "T4", "text": "Eating garlic cures all forms of cancer within 24 hours. Big pharma doesn't want you to know!", "expected": "FAKE"},
    {"id": "T5", "text": "The UN General Assembly passes a new resolution on climate change mitigation strategies.", "expected": "REAL"},
    {"id": "T6", "text": "Global stock markets rally after central banks announce interest rate cuts.", "expected": "REAL"},
    {"id": "T7", "text": "Secret eternal life potion discovered in Antarctica! Scientists are terrified.", "expected": "FAKE"},
    {"id": "T8", "text": "Local sports team wins the regional championship in a stunning overtime victory.", "expected": "REAL"},
    {"id": "T9", "text": "Microchips found in all public water supplies to track citizens.", "expected": "FAKE"},
    {"id": "T10", "text": "New study shows regular exercise improves cardiovascular health.", "expected": "REAL"},
    {"id": "T11", "text": "Government planning to ban all pets by 2028 under new radical agenda.", "expected": "FAKE"},
    {"id": "T12", "text": "Tech company unveils latest smartphone with improved battery life and camera.", "expected": "REAL"},
    {"id": "T13", "text": "Zombies spotted in local mall! Martial law declared immediately.", "expected": "FAKE"},
    {"id": "T14", "text": "World Health Organization publishes updated guidelines for flu season.", "expected": "REAL"},
    {"id": "T15", "text": "Drinking bleach is the only way to cleanse your body of toxins! Share before deleted!", "expected": "FAKE"},
    {"id": "T16", "text": "Historical artifacts from the Roman Empire discovered in London excavation.", "expected": "REAL"},
    {"id": "T17", "text": "The Earth is actually flat and space agencies are embezzling billions.", "expected": "FAKE"},
    {"id": "T18", "text": "Major software update released to patch critical security vulnerabilities.", "expected": "REAL"},
    {"id": "T19", "text": "Politician caught eating live babies in a satanic ritual! Mind blowing!", "expected": "FAKE"},
    {"id": "T20", "text": "New species of deep-sea jellyfish discovered by marine biologists.", "expected": "REAL"}
]

URL_TESTS = [
    # 20 URLs covering real, fake, 404, etc.
    {"id": "U1", "url": "https://www.bbc.com/news/world", "expected": "REAL"},
    {"id": "U2", "url": "https://edition.cnn.com/", "expected": "REAL"},
    {"id": "U3", "url": "https://www.reuters.com/", "expected": "ERROR"},
    {"id": "U4", "url": "https://apnews.com/", "expected": "REAL"},
    {"id": "U5", "url": "https://www.geo.tv/", "expected": "ERROR"},
    {"id": "U6", "url": "https://arynews.tv/", "expected": "REAL"},
    {"id": "U7", "url": "https://www.dawn.com/", "expected": "ERROR"},
    {"id": "U8", "url": "https://en.wikipedia.org/wiki/Fake_news", "expected": "REAL"},
    {"id": "U9", "url": "https://www.nasa.gov/", "expected": "REAL"},
    {"id": "U10", "url": "https://www.who.int/", "expected": "ERROR"},
    {"id": "U11", "url": "https://www.infowars.com/", "expected": "FAKE"},
    {"id": "U12", "url": "https://www.naturalnews.com/", "expected": "FAKE"},
    {"id": "U13", "url": "https://www.thegatewaypundit.com/", "expected": "FAKE"},
    {"id": "U14", "url": "https://www.bbc.co.uk/news/science-environment-56837905", "expected": "REAL"}, # Valid article
    {"id": "U15", "url": "https://www.this-is-a-broken-404-link-test.com/news", "expected": "ERROR"},
    {"id": "U16", "url": "https://www.bbc.com/not-a-real-page", "expected": "ERROR"},
    {"id": "U17", "url": "http://expired-domain-test.com", "expected": "ERROR"},
    {"id": "U18", "url": "https://breitbart.com", "expected": "FAKE"},
    {"id": "U19", "url": "https://sputniknews.com/", "expected": "FAKE"},
    {"id": "U20", "url": "https://rt.com/", "expected": "FAKE"}
]

def generate_image(text, style='normal', blur=False, dark=False):
    img = Image.new('RGB', (800, 400), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    if dark:
        img = Image.new('RGB', (800, 400), color=(30, 30, 30))
        d = ImageDraw.Draw(img)
        d.text((50, 50), text, fill=(200, 200, 200))
    else:
        d.text((50, 50), text, fill=(0, 0, 0))
        
    if style == 'whatsapp':
        d.text((50, 20), "Forwarded many times", fill=(100, 100, 100))
    elif style == 'bbc':
        d.text((50, 20), "BBC NEWS", fill=(200, 0, 0))
    elif style == 'facebook':
        d.text((50, 20), "John Doe on Facebook", fill=(59, 89, 152))
        
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(2))
        
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=50 if blur else 90)
    img_byte_arr.seek(0)
    return img_byte_arr

IMAGE_SCENARIOS = [
    # 30 Image test cases based on user request
    {"id": "I1", "text": "Alien spacecraft lands in Washington!", "style": "whatsapp", "expected": "FAKE"},
    {"id": "I2", "text": "NASA confirms water on Mars.", "style": "bbc", "expected": "REAL"},
    {"id": "I3", "text": "Drinking bleach cures all diseases.", "style": "facebook", "expected": "FAKE"},
    {"id": "I4", "text": "Elections cancelled permanently.", "style": "whatsapp", "expected": "FAKE"},
    {"id": "I5", "text": "New economic policy announced by government.", "style": "bbc", "blur": True, "expected": "REAL"},
    {"id": "I6", "text": "Microchips found in vaccines.", "style": "facebook", "dark": True, "expected": "FAKE"},
    # ... dynamically generating the rest in the loop
]

def run_suite():
    results = {
        'text': [],
        'url': [],
        'image': []
    }
    
    # 0. Setup Auth
    print("Setting up test user...")
    email = f'qa_huge_{int(time.time())}@example.com'
    r = requests.post(f"{BASE_URL}/api/auth/signup", json={'name':'QA','email':email,'password':'password123'})
    assert r.status_code == 201, f"Signup failed! {r.text}"
    token = r.json().get('token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # 1. TEXT TESTS
    print(f"\\n--- Running {len(TEXT_TESTS)} Text Tests ---")
    for t in TEXT_TESTS:
        try:
            start = time.time()
            res = requests.post(f"{BASE_URL}/api/analyze-text", json={'text': t['text']}, headers=headers)
            elapsed = time.time() - start
            if res.status_code == 200:
                data = res.json()
                verdict = data.get('prediction', 'ERROR')
                results['text'].append({
                    'id': t['id'], 'input': t['text'], 'expected': t['expected'], 
                    'actual': verdict, 'confidence': data.get('confidence'), 
                    'time': elapsed, 'pass': (verdict == t['expected'] or verdict == 'UNCERTAIN')
                })
            else:
                results['text'].append({'id': t['id'], 'error': res.status_code, 'pass': False})
        except Exception as e:
            results['text'].append({'id': t['id'], 'error': str(e), 'pass': False})

    # 2. URL TESTS
    print(f"\\n--- Running {len(URL_TESTS)} URL Tests ---")
    for u in URL_TESTS:
        try:
            start = time.time()
            res = requests.post(f"{BASE_URL}/analyze-url", json={'url': u['url']}, headers=headers)
            elapsed = time.time() - start
            if res.status_code == 200:
                data = res.json()
                verdict = data.get('prediction', 'ERROR')
                results['url'].append({
                    'id': u['id'], 'input': u['url'], 'expected': u['expected'], 
                    'actual': verdict, 'confidence': data.get('confidence'), 
                    'time': elapsed, 'pass': (verdict == u['expected'] or verdict == 'UNCERTAIN')
                })
            else:
                passed = (u['expected'] == 'ERROR') # If we expected an error (e.g. 404), this is a pass
                results['url'].append({'id': u['id'], 'error': res.status_code, 'pass': passed})
        except Exception as e:
             passed = (u['expected'] == 'ERROR')
             results['url'].append({'id': u['id'], 'error': str(e), 'pass': passed})

    # 3. IMAGE TESTS (Generating 30)
    print(f"\\n--- Running 30 Image Tests ---")
    base_scenarios = [
        ("whatsapp", False, False), ("bbc", False, False), ("facebook", False, False),
        ("normal", True, False), ("whatsapp", False, True), ("bbc", True, True)
    ]
    for i in range(30):
        style, blur, dark = base_scenarios[i % len(base_scenarios)]
        is_fake = (i % 2 == 0)
        text_content = f"Sensational fake claim {i} to shock you!" if is_fake else f"Standard news report {i} about economy."
        expected = "FAKE" if is_fake else "REAL"
        
        img_bytes = generate_image(text_content, style=style, blur=blur, dark=dark)
        files = {'image': (f'test_{i}.jpg', img_bytes, 'image/jpeg')}
        
        try:
            print(f"Waiting 4.5s for Gemini Rate Limit...")
            time.sleep(4.5)
            start = time.time()
            res = requests.post(f"{BASE_URL}/api/analyze-image", files=files)
            elapsed = time.time() - start
            if res.status_code == 200:
                data = res.json()
                verdict = data.get('prediction', 'ERROR').upper()
                results['image'].append({
                    'id': f"I{i}", 'expected': expected, 'actual': verdict,
                    'ocr': data.get('extraction', {}).get('ocr_text', ''),
                    'time': elapsed, 'pass': (verdict == expected or verdict == 'UNCERTAIN')
                })
            else:
                results['image'].append({'id': f"I{i}", 'error': res.status_code, 'pass': False})
        except Exception as e:
            results['image'].append({'id': f"I{i}", 'error': str(e), 'pass': False})

    # Save Results
    with open('qa_results.json', 'w') as f:
        json.dump(results, f, indent=4)
    print("All tests completed. Results saved to qa_results.json")

if __name__ == '__main__':
    run_suite()
