# ============================================
# FakeGuardAI - Flask Backend Server
# Yeh main server hai jo frontend se requests leta hai aur AI model se results dilwata hai.
# Now with MongoDB authentication, feedback store, and text analysis!
# ============================================

import os
import re
import json
import time
import urllib.parse
import requests as req
from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from bs4 import BeautifulSoup
from model import FactifyModel as FakeNewsDetector, SUSPICIOUS_DOMAINS
from image_analyzer import (
    validate_image, save_temp_file, strip_exif_and_resize,
    extract_with_gemini, build_image_groq_prompt,
    calculate_image_trust_modifier, cleanup_temp_file,
    cleanup_old_temp_files
)

import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# 1. Flask app initialize karo.
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload size

# 2. AI model ko initialize karo.
detector = FakeNewsDetector()

# 3. MongoDB connection setup
try:
    print("Connecting to MongoDB...")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['factify_db']
    users_col = db['users']
    feedbacks_col = db['feedbacks']
    contacts_col = db['contacts']
    analyses_col = db['analyses']
    # Create unique index on email
    users_col.create_index('email', unique=True)
    
    # Securely initialize single admin account
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@factify.com')
    admin_pass = os.environ.get('ADMIN_PASSWORD', 'AdminSecret2026!')
    if not users_col.find_one({'role': 'admin'}):
        hashed = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt())
        users_col.insert_one({
            'name': 'System Administrator',
            'email': admin_email,
            'password_hash': hashed,
            'role': 'admin',
            'created_at': datetime.now(timezone.utc)
        })
        print(f"[OK] Default Admin created: {admin_email}")

    print("[OK] Successfully connected to MongoDB!")
except Exception as e:
    print(f"[ERROR] Failed to connect to MongoDB: {e}")

# JWT Secret Key
JWT_SECRET = os.environ.get('JWT_SECRET', 'fakeguard_super_secret_key_2026')

# 4. Rate limiting tracker.
request_counts = {}

def check_rate_limit(ip, limit=30, window=60):
    if ip == '127.0.0.1': return True
    now = time.time()
    if ip not in request_counts:
        request_counts[ip] = []
    request_counts[ip] = [t for t in request_counts[ip] if now - t < window]
    if len(request_counts[ip]) >= limit:
        return False
    request_counts[ip].append(now)
    return True

def sanitize_input(text):
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    return text[:50000]

# ===== AUTHENTICATION MIDDLEWARE =====
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Authentication token is missing.'}), 401
            
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            g.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token.'}), 401
            
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Authentication token is missing.'}), 401
            
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            if payload.get('role') != 'admin':
                return jsonify({'error': 'Administrator access required.'}), 403
            g.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token.'}), 401
            
        return f(*args, **kwargs)
    return decorated

# ===== FRONTEND SERVE =====
@app.route('/')
def serve_frontend():
    return send_from_directory(str(app.static_folder), 'index.html')

@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory(str(app.static_folder), 'dashboard.html')

@app.route('/admin')
@app.route('/admin/dashboard')
def serve_admin():
    return send_from_directory(str(app.static_folder), 'admin_dashboard.html')

# ===== SERVER HEALTH CHECK =====
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'model_trained': detector.is_trained,
        'message': 'FakeGuardAI is running! ≡ƒ¢í∩╕Å'
    })

# ===== USER AUTHENTICATION ENDPOINTS =====
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Name, email, and password are required.'}), 400
    
    name = data['name'].strip()
    email = data['email'].strip().lower()
    password = data['password']
    
    if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return jsonify({'error': 'Invalid email format.'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400
        
    try:
        # Check if email exists
        if users_col.find_one({'email': email}):
            return jsonify({'error': 'Email is already registered.'}), 400
            
        # Registration MUST ALWAYS create normal users
        role = 'user'
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_doc = {
            'name': name,
            'email': email,
            'password_hash': hashed_password,
            'role': role,
            'created_at': datetime.now(timezone.utc)
        }
        
        result = users_col.insert_one(user_doc)
        user_id = str(result.inserted_id)
        
        # Generate token
        token = jwt.encode({
            'user_id': user_id,
            'role': role,
            'email': email,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, JWT_SECRET, algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': {
                'id': user_id,
                'name': name,
                'email': email,
                'role': role
            }
        }), 201
    except Exception as e:
        return jsonify({'error': f'Failed to create user: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required.'}), 400
        
    email = data['email'].strip().lower()
    password = data['password']
    
    try:
        user = users_col.find_one({'email': email})
        if not user:
            return jsonify({'error': 'Invalid email or password.'}), 401
            
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            return jsonify({'error': 'Invalid email or password.'}), 401
            
        user_id = str(user['_id'])
        role = user.get('role', 'user')
        
        token = jwt.encode({
            'user_id': user_id,
            'role': role,
            'email': email,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, JWT_SECRET, algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': {
                'id': user_id,
                'name': user['name'],
                'email': email,
                'role': role
            }
        }), 200
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/api/auth/me', methods=['GET'])
@login_required
def get_me():
    user_id = g.user.get('user_id')
    try:
        user = users_col.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found.'}), 404
        return jsonify({
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'role': user.get('role', 'user')
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== CHATBOT ENDPOINT =====
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or not data.get('message'):
        return jsonify({'reply': "I didn't quite catch that. Could you repeat?"}), 400
        
    msg = data['message']
    
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return jsonify({'reply': "Chatbot is currently down due to missing API key."}), 500
            
        client = Groq(api_key=api_key)
        
        system_prompt = """You are FakeGuard AI, an intelligent website assistant and misinformation detection bot.
Your primary goals:
1. Help users navigate the FakeGuard AI website (e.g., explaining how to verify a news article, contact support, check history, etc.). FakeGuard AI is free, built by a dedicated team, provides high accuracy via machine learning, linguistic pattern analysis, and emotional load assessment.
2. Answer short questions about whether specific news or rumors are fake or real (e.g., "Is Trump dead?"). When answering news queries, give a brief, factual verdict based on your general knowledge.
3. Keep responses concise, helpful, friendly, and under 3-4 sentences. Do not use extremely long paragraphs."""
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": msg}
            ],
            model=os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b"),
            temperature=0.6,
            max_tokens=300,
        )
        
        reply = chat_completion.choices[0].message.content
        return jsonify({'reply': reply}), 200
        
    except Exception as e:
        print(f"Groq API Error: {e}")
        return jsonify({'reply': "I'm currently experiencing technical difficulties connecting to my AI brain. Please try again later."}), 500

# ===== CONTACT / FEEDBACK ENDPOINTS =====
@app.route('/api/feedback', methods=['POST'])
@login_required
def submit_feedback():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email') or not data.get('subject') or not data.get('message') or 'rating' not in data:
        return jsonify({'error': 'All fields (name, email, subject, message, rating) are required.'}), 400
        
    try:
        rating = int(data['rating'])
        if rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5.'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid rating format.'}), 400
        
    try:
        feedback_doc = {
            'name': sanitize_input(data['name']),
            'email': sanitize_input(data['email']),
            'subject': sanitize_input(data['subject']),
            'message': sanitize_input(data['message']),
            'rating': rating,
            'created_at': datetime.now(timezone.utc)
        }
        
        feedbacks_col.insert_one(feedback_doc)
        return jsonify({'message': 'Feedback submitted successfully.'}), 201
    except Exception as e:
        return jsonify({'error': f'Failed to save feedback: {str(e)}'}), 500

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email') or not data.get('subject') or not data.get('message'):
        return jsonify({'error': 'All fields (name, email, subject, message) are required.'}), 400
        
    try:
        contact_doc = {
            'name': sanitize_input(data['name']),
            'email': sanitize_input(data['email']),
            'subject': sanitize_input(data['subject']),
            'message': sanitize_input(data['message']),
            'created_at': datetime.now(timezone.utc)
        }
        
        contacts_col.insert_one(contact_doc)
        return jsonify({'message': 'Message sent successfully.'}), 201
    except Exception as e:
        return jsonify({'error': f'Failed to send message: {str(e)}'}), 500

@app.route('/api/feedback', methods=['GET'])
def get_feedbacks():
    try:
        feedbacks = list(feedbacks_col.find().sort('created_at', -1).limit(20))
        for fb in feedbacks:
            fb['_id'] = str(fb['_id'])
            if 'created_at' in fb and fb['created_at']:
                fb['created_at'] = fb['created_at'].isoformat()
        return jsonify(feedbacks), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== SEARCH-BASED FACT-CHECKING & PLATFORM SCRAPERS =====
FACT_CHECKERS = [
    'snopes.com', 'politifact.com', 'factcheck.org', 'reuters.com/fact-check', 'reuters.com/news/archive/factCheckNew',
    'apnews.com/ap-fact-check', 'fullfact.org', 'climatefeedback.org', 'leadstories.com', 'factcheck.afp.com',
    'hoax-slayer.net', 'altnews.in', 'boomlive.in', 'factly.in'
]

REPUTABLE_NEWS = [
    'bbc.com', 'bbc.co.uk', 'reuters.com', 'apnews.com', 'nytimes.com', 
    'wsj.com', 'theguardian.com', 'aljazeera.com', 'bloomberg.com',
    'npr.org', 'economist.com', 'nature.com', 'science.org', 'nasa.gov',
    'un.org', 'who.int', 'dw.com', 'france24.com', 'cnn.com', 'cnbc.com',
    'forbes.com', 'time.com', 'washingtonpost.com', 'independent.co.uk'
]

def extract_search_query(text, title=None):
    if title and len(title.strip()) > 10:
        return title
    # Split by punctuation and take the first sentence
    sentences = re.split(r'[.!?\n]+', text)
    for s in sentences:
        s = s.strip()
        if len(s) > 15:
            return s
    return text[:100]

def search_web_fact_check(query):
    """
    Search GNews API to check the claims.
    Returns a list of cross_references: {'title', 'url', 'snippet', 'category'}.
    """
    if not query or len(query.strip()) < 10:
        return []
        
    words = query.strip().split()
    search_query = " ".join(words[:20])
    
    api_key = os.environ.get('GNEWS_API_KEY')
    if not api_key:
        print("[WARN] GNEWS_API_KEY not found in environment. Returning empty search results.")
        return []

    encoded_query = urllib.parse.quote_plus(search_query)
    url = f"https://gnews.io/api/v4/search?q={encoded_query}&apikey={api_key}&lang=en&max=8"
    
    cross_references = []
    try:
        r = req.get(url, timeout=8)
        if r.status_code != 200:
            print(f"[WARN] GNews API returned status code {r.status_code}")
            return []
            
        data = r.json()
        articles = data.get('articles', [])
        
        for article in articles:
            title = article.get('title', '')
            link = article.get('url', '')
            snippet = article.get('description', '')
            source_obj = article.get('source', {})
            source_name = source_obj.get('name', '')
            domain = urllib.parse.urlparse(link).netloc.lower().replace('www.', '')
            
            category = 'Unverified Source'
            is_fc = False
            for fc in FACT_CHECKERS:
                if fc in domain or domain in fc:
                    is_fc = True
                    break
            
            if is_fc:
                combined_text = f"{title.lower()} {snippet.lower()}"
                if any(w in combined_text for w in ['false', 'fake', 'debunked', 'hoax', 'misleading', 'incorrect', 'untrue']):
                    category = 'Fact Check (Debunked)'
                elif any(w in combined_text for w in ['true', 'verified', 'correct', 'accurate']):
                    category = 'Fact Check (Verified)'
                else:
                    category = 'Fact Check (Debunked)'
            else:
                is_news = False
                for news in REPUTABLE_NEWS:
                    if news in domain or domain in news:
                        is_news = True
                        break
                if is_news or source_name in REPUTABLE_NEWS:
                    category = 'Reputable News'
                    
            cross_references.append({
                'title': title,
                'url': link,
                'snippet': snippet,
                'category': category
            })
        return cross_references
    except Exception as e:
        print(f"Fact checking search failed: {e}")
        return []

def extract_content_from_url(url):
    """
    Extracts structured content from a given URL based on the platform.
    Returns a dict with: 'title', 'content', 'meta_desc', 'platform'.
    """
    url = url.strip()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }

    # Reddit Check
    reddit_match = re.match(r'https?://(?:[a-zA-Z0-9-]+\.)?reddit\.com/r/([^/]+)/comments/([^/]+)', url, re.IGNORECASE)
    if reddit_match:
        try:
            clean_url = url.rstrip('/')
            json_url = f"{clean_url}.json"
            reddit_headers = {'User-Agent': 'FakeGuardAI/0.2 (by /u/FakeGuardAI)'}
            res = req.get(json_url, headers=reddit_headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                post_data = data[0]['data']['children'][0]['data']
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                subreddit = post_data.get('subreddit', '')
                
                comments = []
                if len(data) > 1:
                    comment_children = data[1]['data']['children']
                    for child in comment_children[:5]:
                        if child['kind'] == 't1':
                            c_body = child['data'].get('body', '')
                            if c_body and c_body != '[deleted]' and c_body != '[removed]':
                                comments.append(c_body)
                                
                combined_content = f"Post: {selftext}\n\nTop Comments/Discussion:\n" + "\n---\n".join(comments)
                return {
                    'title': f"[Reddit r/{subreddit}] {title}",
                    'content': combined_content,
                    'meta_desc': f"Reddit post in r/{subreddit} with {len(comments)} top comments analyzed.",
                    'platform': 'Reddit'
                }
        except Exception as e:
            print(f"Reddit scraping failed: {e}")

    # YouTube Check
    yt_match = re.search(r'(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/|\/watch\?v=)([^#\&\?]+)', url, re.IGNORECASE)
    if yt_match or 'youtube.com' in url or 'youtu.be' in url:
        video_id = yt_match.group(1) if yt_match else None
        title = "YouTube Video"
        description = ""
        transcript = ""
        try:
            res = req.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True).replace(' - YouTube', '')
                
                desc_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
                if desc_tag:
                    description = desc_tag.get('content', '')
        except Exception as e:
            print(f"YouTube page scrape failed: {e}")

        if video_id:
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                ytt_api = YouTubeTranscriptApi()
                transcript_list = ytt_api.fetch(video_id)
                transcript = " ".join([t.text for t in transcript_list])
            except Exception as e:
                print(f"YouTube transcript fetch failed: {e}")
        
        combined_content = f"Video Description: {description}\n\nSpeech Transcript:\n{transcript}" if transcript else f"Video Description: {description}"
        return {
            'title': title,
            'content': combined_content,
            'meta_desc': (description[:300] if description else ''),
            'platform': 'YouTube'
        }

    # Twitter/X Check
    twitter_match = re.search(r'https?://(?:www\.)?(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)', url, re.IGNORECASE)
    if twitter_match:
        username = twitter_match.group(1)
        status_id = twitter_match.group(2)
        bot_headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        }
        try:
            res = req.get(url, headers=bot_headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                tweet_text = ""
                desc_tag = (soup.find('meta', attrs={'property': 'og:description'}) or 
                            soup.find('meta', attrs={'name': 'twitter:description'}) or 
                            soup.find('meta', attrs={'name': 'description'}))
                if desc_tag:
                    tweet_text = desc_tag.get('content', '')
                
                title = f"Tweet by @{username}"
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                
                if tweet_text:
                    return {
                        'title': title,
                        'content': tweet_text,
                        'meta_desc': f"Twitter post by @{username}",
                        'platform': 'Twitter/X'
                    }
        except Exception as e:
            print(f"Twitter scraping failed: {e}")
            
        return {
            'title': f"Tweet by @{username}",
            'content': f"Tweet by user @{username}. Status ID: {status_id}. Direct scraping was blocked by Twitter/X. Use the search-based verification to cross-reference this claim.",
            'meta_desc': f"Twitter post by @{username}",
            'platform': 'Twitter/X'
        }

    # Wikipedia Check
    if 'wikipedia.org' in url:
        try:
            res = req.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                h1_tag = soup.find('h1', id='firstHeading')
                title = h1_tag.get_text(strip=True) if h1_tag else 'Wikipedia Article'
                content_div = soup.find('div', id='mw-content-text')
                paragraphs = content_div.find_all('p') if content_div else soup.find_all('p')
                text = ' '.join(p.get_text() for p in paragraphs if len(p.get_text()) > 20)
                return {
                    'title': title,
                    'content': sanitize_input(text),
                    'meta_desc': f"Wikipedia article: {title}",
                    'platform': 'Wikipedia'
                }
        except Exception as e:
            print(f"Wikipedia scrape failed: {e}")

    # Generic Scraper
    res = req.get(url, timeout=12, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    
    title = ""
    if soup.title:
        title = soup.title.string
    if not title:
        h1 = soup.find('h1')
        if h1: title = h1.get_text()
        
    meta_desc = ""
    desc_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    if desc_tag:
        meta_desc = desc_tag.get('content', '')

    article_body = soup.find('article')
    if article_body:
        paragraphs = article_body.find_all('p')
    else:
        paragraphs = soup.find_all('p')
        
    text = ' '.join(p.get_text() for p in paragraphs if len(p.get_text()) > 20)
    text = sanitize_input(text)
    
    return {
        'title': sanitize_input(title or "Web Page"),
        'content': text,
        'meta_desc': sanitize_input(meta_desc),
        'platform': 'Website'
    }

def blend_prediction(result, cross_references, platform=None):
    """
    Blends the style-based ML prediction with real-time web search evidence.
    Modifies the result dict in-place and adds 'cross_references'.
    """
    result['cross_references'] = cross_references
    
    debunked_count = sum(1 for r in cross_references if r['category'] == 'Fact Check (Debunked)')
    verified_count = sum(1 for r in cross_references if r['category'] == 'Fact Check (Verified)')
    news_count = sum(1 for r in cross_references if r['category'] == 'Reputable News')
    
    original_pred = result['prediction']
    original_conf = result['confidence']
    original_reason = result['reason']
    
    # 1. Fact check debunked override
    if debunked_count > 0:
        result['prediction'] = 'Fake'
        result['confidence'] = max(original_conf, min(85 + debunked_count * 5, 98))
        result['credibility'] = max(5, min(15 - debunked_count * 2, 25))
        
        debunkers = list(set([urllib.parse.urlparse(r['url']).netloc.lower().replace('www.', '') for r in cross_references if r['category'] == 'Fact Check (Debunked)']))
        debunkers_str = ", ".join(debunkers[:3])
        result['reason'] = f"This claim has been flagged as fake or misleading by fact-checking organizations (including {debunkers_str}). " + original_reason
        
        # Add to suggestions
        if 'suggestions' not in result or not result['suggestions']:
            result['suggestions'] = []
        if '[TIP] Verify with reputable outlets like Reuters or BBC.' in result.get('suggestions', []):
            result['suggestions'].remove('[TIP] Verify with reputable outlets like Reuters or BBC.')
        result['suggestions'].insert(0, '[WARNING] Avoid sharing this content as it has been verified as false.')
        
    # 2. Fact check verified override
    elif verified_count > 0:
        result['prediction'] = 'Real'
        result['confidence'] = max(original_conf, min(80 + verified_count * 5, 98))
        result['credibility'] = min(98, max(85, original_conf))
        
        verifiers = list(set([urllib.parse.urlparse(r['url']).netloc.lower().replace('www.', '') for r in cross_references if r['category'] == 'Fact Check (Verified)']))
        verifiers_str = ", ".join(verifiers[:3])
        result['reason'] = f"This claim has been confirmed as accurate by fact-checkers (including {verifiers_str}). " + original_reason
        
    # 3. Reputable News coverage check
    elif news_count >= 2:
        if original_pred == 'Fake':
            result['prediction'] = 'Real'
            result['confidence'] = 75
            result['credibility'] = 80
            result['reason'] = "Although the text contains dramatic/sensationalist linguistic patterns, the claim itself is currently reported by multiple reputable news organizations. " + original_reason
        elif original_pred == 'Misleading':
            result['prediction'] = 'Real'
            result['confidence'] = 80
            result['credibility'] = 85
            result['reason'] = "This news is widely reported by mainstream news outlets, suggesting high factual credibility despite minor emotional or biased framing. " + original_reason
        else:
            result['confidence'] = max(original_conf, 85)
            result['credibility'] = max(result['credibility'], 88)
            result['reason'] = "This story is widely covered by reputable news networks, validating its authenticity. " + original_reason
            
    # 4. No fact-checks or reputable news
    else:
        if platform in ['Reddit', 'Twitter/X', 'YouTube'] and result['credibility'] > 50:
            result['credibility'] = max(40, result['credibility'] - 15)
            result['reason'] = f"This is a {platform} post with no matching coverage from reputable news or fact-checking agencies. Please handle with care. " + original_reason
        else:
            result['reason'] = "No direct matches found in fact-checking databases or reputable news sites. Verdict is based on style and tone analysis. " + original_reason
            
    return result

# ===== ENHANCED URL ANALYSIS ENDPOINT =====
@app.route('/analyze-url', methods=['POST'])
@login_required
def analyze_url():
    if not check_rate_limit(request.remote_addr):
        return jsonify({'error': 'Too many requests. Please wait.'}), 429

    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided.'}), 400

    url = data['url'].strip()
    if not re.match(r'https?://[^\s]+', url):
        return jsonify({'error': 'Invalid URL format.'}), 400

    try:
        extracted = extract_content_from_url(url)
        title = extracted['title']
        text = extracted['content']
        meta_desc = extracted['meta_desc']
        platform = extracted['platform']

        if len(text.strip()) < 50:
            return jsonify({'error': f'Could not extract enough readable text from this {platform}. The site might be protected or use heavy Javascript.'}), 400

        result = detector.predict(
            text=text, 
            url=url, 
            title=title, 
            meta_desc=meta_desc
        )

        # Search-based fact-checking
        search_query = extract_search_query(text, title)
        cross_references = search_web_fact_check(search_query)

        # Blend ML predictions with search findings
        result = blend_prediction(result, cross_references, platform)

        # Check if user is logged in to save history
        token = None
        user_email = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if token:
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                user_email = payload.get('email')
            except Exception:
                pass
                
        # Save to DB
        analysis_doc = {
            'user_email': user_email,
            'type': 'url',
            'input': url,
            'prediction': result['prediction'],
            'confidence': result['confidence'],
            'created_at': datetime.now(timezone.utc)
        }
        analyses_col.insert_one(analysis_doc)

        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch or parse URL: {str(e)}'}), 500

# ===== TEXT ANALYSIS ENDPOINT =====
@app.route('/api/analyze-text', methods=['POST'])
@login_required
def analyze_text():
    if not check_rate_limit(request.remote_addr):
        return jsonify({'error': 'Too many requests. Please wait.'}), 429

    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided.'}), 400

    text = data['text'].strip()
    text = sanitize_input(text)

    if len(text.strip()) < 50:
        return jsonify({'error': 'Please enter at least 50 characters of text.'}), 400

    try:
        result = detector.predict(text=text)
        
        # Search-based fact-checking
        search_query = extract_search_query(text)
        cross_references = search_web_fact_check(search_query)
        
        # Blend
        result = blend_prediction(result, cross_references, 'Text')
        
        # Check if user is logged in to save history
        token = None
        user_email = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if token:
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                user_email = payload.get('email')
            except Exception:
                pass
                
        # Save to DB
        analysis_doc = {
            'user_email': user_email,
            'type': 'text',
            'input': text[:200] + '...' if len(text) > 200 else text,
            'prediction': result['prediction'],
            'confidence': result['confidence'],
            'created_at': datetime.now(timezone.utc)
        }
        analyses_col.insert_one(analysis_doc)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Failed to analyze text: {str(e)}'}), 500

# ===== USER HISTORY ENDPOINTS =====
@app.route('/api/user/analyses', methods=['GET'])
@login_required
def get_user_analyses():
    user_email = g.user.get('email')
    try:
        analyses = list(analyses_col.find({'user_email': user_email}).sort('created_at', -1).limit(20))
        for a in analyses:
            a['_id'] = str(a['_id'])
            if 'created_at' in a and a['created_at']:
                a['created_at'] = a['created_at'].isoformat()
        return jsonify(analyses), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/analyses', methods=['DELETE'])
@login_required
def clear_user_analyses():
    user_email = g.user.get('email')
    try:
        analyses_col.delete_many({'user_email': user_email})
        return jsonify({'message': 'History cleared successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== GLOBAL NEWS ENDPOINT =====
@app.route('/api/news', methods=['GET'])
@login_required
def get_news():
    category = request.args.get('category', 'general')
    urls = {
        'general': 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
        'technology': 'https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en',
        'science': 'https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=en-US&gl=US&ceid=US:en',
        'health': 'https://news.google.com/rss/headlines/section/topic/HEALTH?hl=en-US&gl=US&ceid=US:en',
        'business': 'https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en'
    }
    url = urls.get(category, urls['general'])
    try:
        r = req.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
        if r.status_code != 200:
            return jsonify({'error': 'Failed to fetch global news.'}), 500
        
        try:
            soup = BeautifulSoup(r.content, 'xml')
        except Exception:
            soup = BeautifulSoup(r.content, 'html.parser')
            
        items = soup.find_all('item')
        news_list = []
        
        for item in items[:15]:
            title_tag = item.find('title')
            link_tag = item.find('link')
            pub_date_tag = item.find('pubdate') or item.find('pubDate')
            source_tag = item.find('source')
            
            title = title_tag.get_text() if title_tag else ''
            link = link_tag.get_text() if link_tag else ''
            pub_date = pub_date_tag.get_text() if pub_date_tag else ''
            source = source_tag.get_text() if source_tag else 'Unknown'
            
            # Clean title
            if source and title.endswith(f" - {source}"):
                title = title[:-len(f" - {source}")].strip()
            elif " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0].strip()
                if source == 'Unknown':
                    source = parts[1].strip()
            
            domain = urllib.parse.urlparse(link).netloc.lower().replace('www.', '')
            
            is_reputable = False
            for rep in REPUTABLE_NEWS:
                if rep in domain or domain in rep or rep.lower() in source.lower():
                    is_reputable = True
                    break
            
            is_suspicious = False
            for susp in SUSPICIOUS_DOMAINS:
                if susp in domain or domain in susp:
                    is_suspicious = True
                    break
                    
            if is_suspicious:
                trust_score = 15 + (len(title) % 20)
                tag = 'low'
            elif is_reputable:
                trust_score = 85 + (len(title) % 12)
                tag = 'high'
            else:
                trust_score = 60 + (len(title) % 18)
                tag = 'medium'
                
            news_list.append({
                'title': title,
                'link': link,
                'source': source,
                'pubDate': pub_date,
                'trust': trust_score,
                'tag': tag
            })
            
        return jsonify(news_list), 200
    except Exception as e:
        return jsonify({'error': f'Failed to load news: {str(e)}'}), 500

# ===== ADMIN ENDPOINTS =====
@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def get_admin_stats():
    try:
        total_users = users_col.count_documents({})
        total_feedbacks = feedbacks_col.count_documents({})
        total_contacts = contacts_col.count_documents({})
        total_analyses = analyses_col.count_documents({})
        return jsonify({
            'total_users': total_users,
            'total_feedbacks': total_feedbacks,
            'total_contacts': total_contacts,
            'total_analyses': total_analyses
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_admin_users():
    try:
        users = list(users_col.find({}, {'password_hash': 0}).sort('created_at', -1))
        for u in users:
            u['_id'] = str(u['_id'])
            if 'created_at' in u and u['created_at']:
                u['created_at'] = u['created_at'].isoformat()
        return jsonify(users), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/feedbacks', methods=['GET'])
@admin_required
def get_admin_feedbacks():
    try:
        feedbacks = list(feedbacks_col.find().sort('created_at', -1))
        for f in feedbacks:
            f['_id'] = str(f['_id'])
            if 'created_at' in f and f['created_at']:
                f['created_at'] = f['created_at'].isoformat()
        return jsonify(feedbacks), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/contacts', methods=['GET'])
@admin_required
def get_admin_contacts():
    try:
        contacts = list(contacts_col.find().sort('created_at', -1))
        for c in contacts:
            c['_id'] = str(c['_id'])
            if 'created_at' in c and c['created_at']:
                c['created_at'] = c['created_at'].isoformat()
        return jsonify(contacts), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/analyses', methods=['GET'])
@admin_required
def get_admin_analyses():
    try:
        analyses = list(analyses_col.find().sort('created_at', -1).limit(100))
        for a in analyses:
            a['_id'] = str(a['_id'])
            if 'created_at' in a and a['created_at']:
                a['created_at'] = a['created_at'].isoformat()
        return jsonify(analyses), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/user/<id>', methods=['DELETE'])
@admin_required
def delete_user(id):
    try:
        res = users_col.delete_one({'_id': ObjectId(id)})
        if res.deleted_count == 0:
            return jsonify({'error': 'User not found.'}), 404
        return jsonify({'message': 'User deleted successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/feedback/<id>', methods=['DELETE'])
@admin_required
def delete_feedback(id):
    try:
        res = feedbacks_col.delete_one({'_id': ObjectId(id)})
        if res.deleted_count == 0:
            return jsonify({'error': 'Feedback not found.'}), 404
        return jsonify({'message': 'Feedback deleted successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/contact/<id>', methods=['DELETE'])
@admin_required
def delete_contact(id):
    try:
        res = contacts_col.delete_one({'_id': ObjectId(id)})
        if res.deleted_count == 0:
            return jsonify({'error': 'Contact not found.'}), 404
        return jsonify({'message': 'Contact deleted successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== IMAGE ANALYSIS ENDPOINT =====
@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file uploaded.'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected.'}), 400

    # validate_image returns (is_valid, error_msg, file_bytes)
    is_valid, validation_error, _ = validate_image(file)
    if not is_valid:
        return jsonify({'error': validation_error}), 400

    temp_path = save_temp_file(file)
    if not temp_path:
        return jsonify({'error': 'Failed to process image file.'}), 500

    try:
        # Cleanup stale temp files from previous runs
        cleanup_old_temp_files()

        # Step 1: Privacy — strip EXIF and resize (modifies file in-place)
        if not strip_exif_and_resize(temp_path):
            return jsonify({'error': 'Image is corrupt or unsupported format.'}), 400

        # Step 2: Gemini Vision Extraction — returns (result_dict, error_string)
        gemini_result, gemini_error = extract_with_gemini(temp_path)

        if gemini_error or gemini_result is None:
            return jsonify({'error': gemini_error or 'Gemini Vision extraction returned no data.'}), 500

        # Normalize field names for the rest of the pipeline
        ocr_text = gemini_result.get('ocr_text', '')
        headline = gemini_result.get('headline', '')
        main_claim = gemini_result.get('claim', '')
        detected_source = gemini_result.get('source', 'Unknown')
        detected_platform = gemini_result.get('platform', 'Unknown')
        author = gemini_result.get('author', 'Unknown')
        date = gemini_result.get('date', 'Unknown')
        image_quality = gemini_result.get('image_quality', 'Medium')
        context_summary = gemini_result.get('context_summary', '')

        # Build a clean extraction summary for frontend
        extraction_result = {
            'ocr_text': ocr_text,
            'headline': headline,
            'claim_to_check': main_claim,
            'source': detected_source,
            'platform': detected_platform,
            'author': author,
            'date': date,
            'image_quality': image_quality,
            'context_summary': context_summary,
            'is_news': bool(main_claim and len(main_claim) > 10)
        }

        # Step 3: Fast Track — no verifiable claim
        if not main_claim or len(main_claim.strip()) < 10:
            return jsonify({
                'prediction': 'Uncertain',
                'confidence': 'N/A',
                'reasoning': 'Could not extract a clear verifiable claim from the image. It may be a meme, personal photo, or non-news content.',
                'image_analysis': extraction_result
            }), 200

        # Step 4: Web Search for Evidence using the extracted claim
        search_query = f'"{main_claim}" fact check'
        search_results = search_web_fact_check(search_query)

        # Step 5: Final Groq Reasoning
        system_prompt, user_prompt = build_image_groq_prompt(
            ocr_text=ocr_text,
            claim=main_claim,
            headline=headline,
            platform=detected_platform,
            source=detected_source,
            author=author,
            date=date,
            image_quality=image_quality,
            context_summary=context_summary,
            cross_references=search_results
        )

        try:
            groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            completion = groq_client.chat.completions.create(
                model=os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            groq_response = completion.choices[0].message.content
        except Exception as e:
            print("Groq Error in Image Analysis:", e)
            return jsonify({'error': 'AI reasoning engine failed. Please try again.'}), 500

        # Parse Groq JSON response
        prediction = 'Uncertain'
        confidence = 50.0
        reasoning = groq_response
        llm_claims = []

        try:
            groq_json = json.loads(groq_response)
            verdict = groq_json.get('verdict', 'UNCERTAIN').upper()
            if verdict == 'REAL':
                prediction = 'Real'
            elif verdict == 'FAKE':
                prediction = 'Fake'
            else:
                prediction = 'Uncertain'

            confidence = float(groq_json.get('confidence', 50))
            reasoning = groq_json.get('fact_check_summary', groq_response)
            llm_claims = groq_json.get('extracted_claims', [])
        except (json.JSONDecodeError, ValueError, TypeError):
            # Fallback: try regex parsing
            prediction_match = re.search(r'"verdict"\s*:\s*"(REAL|FAKE|UNCERTAIN)"', groq_response, re.IGNORECASE)
            if prediction_match:
                prediction = prediction_match.group(1).capitalize()
            confidence_match = re.search(r'"confidence"\s*:\s*(\d+)', groq_response)
            if confidence_match:
                confidence = float(confidence_match.group(1))

        # Step 6: Apply trust modifier based on image context
        trust_modifier = calculate_image_trust_modifier(image_quality, detected_platform, detected_source)
        confidence = confidence + trust_modifier

        # Clamp and round confidence
        confidence = round(min(max(confidence, 5), 98), 1)
        confidence_text = f"{confidence}%"

        # Record in history if user is logged in
        user_email = None
        inserted_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                decoded = jwt.decode(token, os.getenv("JWT_SECRET", "super-secret-key"), algorithms=["HS256"])
                user_email = decoded['email']
            except Exception:
                inserted_id = None

        if user_email:
            # Store exact fields specified by user requirements
            result = analyses_col.insert_one({
                'user_email': user_email,
                'input': f"Image Upload: {headline or 'Unknown'}",
                'prediction': prediction,
                'confidence': confidence_text,
                'created_at': datetime.now(timezone.utc),
                'type': 'image',
                'image_filename': file.filename,
                'image_type': file.content_type,
                'ocr_text': ocr_text,
                'headline': headline,
                'claim': main_claim,
                'platform': detected_platform,
                'source': detected_source,
                'author': author,
                'date': date,
                'image_quality': image_quality,
                'context_summary': context_summary
            })
            inserted_id = str(result.inserted_id)

        # Build response
        response_data = {
            'prediction': prediction,
            'confidence': confidence,
            'credibility': max(5, min(int(confidence + trust_modifier), 98)),
            'reason': reasoning,
            'reasoning': reasoning,
            'cross_references': search_results,
            'image_analysis': extraction_result,
            'manipulation': [],
            'emotions': {},
            'suspicious_sentences': [],
            'suggestions': [
                '[TIP] Verify with reputable outlets like Reuters or BBC.',
                '[TIP] Check fact-checking sites like Snopes or PolitiFact.',
                '[TIP] Reverse image search to verify authenticity.'
            ],
            'llm_analysis': {
                'fact_check_summary': reasoning,
                'extracted_claims': llm_claims
            }
        }

        if inserted_id:
            response_data['inserted_id'] = inserted_id

        return jsonify(response_data), 200

    except Exception as e:
        print("Image Analysis Error:", e)
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to analyze image: {str(e)}'}), 500

    finally:
        cleanup_temp_file(temp_path)

# ===== MAIN ENTRY POINT =====
if __name__ == '__main__':
    print('FakeGuardAI Server Starting (With Auth & Database Mode)...')
    print(f'Model trained: {detector.is_trained}')
    print('Open http://127.0.0.1:5002 in your browser')
    app.run(debug=True, host='0.0.0.0', port=5002)
