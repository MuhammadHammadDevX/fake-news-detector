# ============================================
# Factify - AI Model Logic
# Is file mein AI ka sara dimagh (logic) hai.
# Yahan training, text cleaning, aur prediction ka sara kaam hota hai.
# ============================================

import re
import os
import pickle
import numpy as np
from collections import Counter
from urllib.parse import urlparse

# 1. Check karo ke machine learning library (sklearn) installed hai ya nahi.
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import PassiveAggressiveClassifier, LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Model aur vectorizer ko save karne ke liye paths.
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, 'model.pkl')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'vectorizer.pkl')

# ===== DOMAIN REPUTATION LISTS =====
TRUSTED_DOMAINS = [
    'bbc.com', 'bbc.co.uk', 'reuters.com', 'apnews.com', 'nytimes.com', 
    'wsj.com', 'theguardian.com', 'aljazeera.com', 'bloomberg.com',
    'npr.org', 'economist.com', 'nature.com', 'science.org', 'nasa.gov',
    'un.org', 'who.int', 'dw.com', 'france24.com', 'cnn.com'
]

SUSPICIOUS_DOMAINS = [
    'naturalnews.com', 'infowars.com', 'dailymail.co.uk', 'breitbart.com',
    'rt.com', 'sputniknews.com', 'thegatewaypundit.com', 'zerohedge.com',
    'worldnewsdailyreport.com', 'now8news.com', 'abcnews.com.co', 'dailybuzzlive.com'
]

# ===== CLICKBAIT DETECTION WORDS =====
CLICKBAIT_WORDS = [
    'shocking', 'must see', 'exposed', 'secret', 'breaking', 'urgent',
    'leaked', 'banned', 'you won\'t believe', 'mind blowing', 'incredible',
    'unbelievable', 'outrageous', 'insane', 'jaw dropping', 'bombshell',
    'exclusive', 'alert', 'warning', 'revealed', 'conspiracy', 'cover up',
    'anonymous', 'whistleblower', 'hidden', 'immortal', 'eternal life',
    'miracle', 'cure', 'they don\'t want', 'share before', 'gets deleted',
    'reverse aging', 'big pharma', 'suppressing'
]

# ===== EMOTIONAL / FEAR WORDS =====
EMOTION_WORDS = {
    'fear': ['terrifying', 'dangerous', 'threat', 'deadly', 'catastrophe', 'disaster',
             'panic', 'horror', 'nightmare', 'apocalypse', 'collapse', 'crisis', 'alarming'],
    'anger': ['outrage', 'fury', 'disgusting', 'corrupt', 'betrayal', 'scandal',
              'criminal', 'evil', 'despicable', 'shameful', 'infuriating'],
    'manipulation': ['they don\'t want you to know', 'wake up', 'open your eyes',
                     'mainstream media', 'deep state', 'big pharma', 'cover up',
                     'suppressed', 'silenced', 'censored', 'before it gets deleted',
                     'share this', 'spread the word']
}

# ===== PROPAGANDA INDICATORS =====
PROPAGANDA_WORDS = [
    'regime', 'puppet', 'traitor', 'enemy of the people', 'radical',
    'extremist', 'socialist', 'fascist', 'deep state', 'globalist',
    'patriot', 'freedom fighter', 'fake news media', 'witch hunt'
]


def preprocess_text(text):
    if not text:
        return ''
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def detect_clickbait(text):
    lower_text = text.lower()
    found = [word for word in CLICKBAIT_WORDS if word in lower_text]
    
    words = text.split()
    caps_count = sum(1 for w in words if w.isupper() and len(w) > 2)
    caps_ratio = caps_count / max(len(words), 1)

    score = min(len(found) * 15 + int(caps_ratio * 50), 100)
    return {'score': score, 'found_words': found, 'is_clickbait': score > 40}


def detect_emotions(text):
    lower_text = text.lower()
    results = {}
    for emotion, words in EMOTION_WORDS.items():
        found = [w for w in words if w in lower_text]
        score = min(len(found) * 20, 95)
        results[emotion] = score
    
    results['hope'] = max(5, 100 - results.get('fear', 0) - results.get('anger', 0)) // 3
    results['sadness'] = min(results.get('fear', 0) // 2 + 10, 60)
    return results


def detect_propaganda(text):
    lower_text = text.lower()
    found = [w for w in PROPAGANDA_WORDS if w in lower_text]
    score = min(len(found) * 18, 95)
    return {'score': score, 'found_words': found, 'has_propaganda': score > 30}


def check_domain_reputation(url):
    """Checks if the URL domain is in our trusted or suspicious lists."""
    if not url:
        return 0, 'Unknown'
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
            
        is_trusted = any(domain == d or domain.endswith('.' + d) for d in TRUSTED_DOMAINS)
        is_suspicious = any(domain == d or domain.endswith('.' + d) for d in SUSPICIOUS_DOMAINS)

        if is_trusted:
            return 40, 'Trusted Source'
        if is_suspicious:
            return -50, 'Suspicious Source'
        return 0, 'Neutral Source'
    except:
        return 0, 'Unknown'


def check_title_consistency(title, content):
    """Checks if the title matches the content logic."""
    if not title or not content:
        return 0
    t_clean = preprocess_text(title).split()
    c_clean = preprocess_text(content)
    
    if not t_clean: return 0
    
    # Check how many title words are in the content
    matches = sum(1 for word in t_clean if word in c_clean)
    match_ratio = matches / len(t_clean)
    
    # Improve logic: check for 'not' contradictions
    title_lower = title.lower().split()
    content_lower = content.lower().split()
    title_has_not = 'not' in title_lower or "n't" in title.lower()
    content_has_not = 'not' in content_lower or "n't" in content.lower()
    
    if title_has_not != content_has_not and match_ratio > 0:
        return -40 # Strong indicator of contradiction
    
    # If match ratio is very low, it might be clickbait/misleading
    if match_ratio < 0.2:
        return -30
    return 10


def calculate_credibility(text, prediction, confidence, domain_score, consistency_score):
    base_score = 50
    clickbait = detect_clickbait(text)
    emotions = detect_emotions(text)
    propaganda = detect_propaganda(text)

    base_score -= clickbait['score'] * 0.3
    base_score -= max(emotions.values()) * 0.2
    base_score -= propaganda['score'] * 0.25
    
    base_score += domain_score
    base_score += consistency_score

    if prediction == 'REAL':
        base_score += 20
    elif prediction == 'UNCERTAIN':
        base_score -= 15
    else:
        base_score -= 30

    return max(5, min(int(base_score), 98))


def generate_reason(prediction, clickbait_data, emotion_data, propaganda_data, domain_label, consistency_score):
    reasons = []
    
    if domain_label == 'Trusted Source':
        reasons.append('The source domain is a highly reputable news organization.')
    elif domain_label == 'Suspicious Source':
        reasons.append('The source domain is known for spreading misinformation or biased content.')

    if consistency_score < -20:
        reasons.append('Significant mismatch between the headline and actual article content detected.')

    if prediction == 'FAKE':
        reasons.append(f'Our AI model classified this content as likely misinformation.')
        if clickbait_data['is_clickbait']:
            reasons.append(f'Clickbait patterns found: {", ".join(clickbait_data["found_words"][:2])}.')
        if propaganda_data['has_propaganda']:
            reasons.append('Propaganda-style language was identified.')
    elif prediction == 'UNCERTAIN':
        reasons.append('Evidence is insufficient to make a definitive ruling.')
    else:
        reasons.append('Content structure and tone align with factual reporting standards.')

    return ' '.join(reasons)


class FactifyModel:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.is_trained = False
        self._load_model()

    def _load_model(self):
        try:
            if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
                with open(MODEL_PATH, 'rb') as f:
                    self.model = pickle.load(f)
                with open(VECTORIZER_PATH, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                self.is_trained = True
                print('✅ Model loaded successfully!')
        except Exception as e:
            print(f'⚠️ Model load failed: {e}')
            self.is_trained = False

    def predict(self, text, url=None, title=None, meta_desc=None):
        """Enhanced prediction using URL, Title, and Metadata."""
        if not text:
            return self._rule_based_analysis('', url, title)

        full_text = f"{title or ''} {meta_desc or ''} {text}"
        
        if self.is_trained and self.model and self.vectorizer:
            return self._model_prediction(full_text, url, title, text)
        else:
            return self._rule_based_analysis(full_text, url, title)

    def _model_prediction(self, full_text, url, title, body):
        clean = preprocess_text(full_text)
        X = self.vectorizer.transform([clean])

        decision = self.model.decision_function(X)[0]
        confidence = min(int(abs(decision) * 20 + 55), 98)
        pred = self.model.predict(X)[0]
        prediction = 'REAL' if pred == 1 else 'FAKE'

        # Insufficient evidence logic
        if confidence < 65:
            prediction = 'UNCERTAIN'

        # Rule-based overrides for higher accuracy
        domain_score, domain_label = check_domain_reputation(url)
        consistency_score = check_title_consistency(title, body)
        
        if domain_label == 'Trusted Source' and prediction == 'FAKE' and confidence < 75:
            prediction = 'UNCERTAIN' # Trust the domain more if AI is unsure
            confidence -= 10
        
        if domain_label == 'Suspicious Source' and prediction == 'REAL':
            prediction = 'UNCERTAIN'
            confidence = 65

        clickbait = detect_clickbait(title or body)
        emotions = detect_emotions(body)
        propaganda = detect_propaganda(body)
        credibility = calculate_credibility(body, prediction, confidence, domain_score, consistency_score)
        reason = generate_reason(prediction, clickbait, emotions, propaganda, domain_label, consistency_score)
        
        return {
            'prediction': prediction,
            'confidence': confidence,
            'reason': reason,
            'manipulation': get_manipulation_labels(clickbait, emotions, propaganda),
            'credibility': credibility,
            'emotions': emotions,
            'suspicious_sentences': find_suspicious_sentences(body),
            'suggestions': generate_suggestions(prediction, clickbait, propaganda),
            'metadata': {'domain': domain_label, 'consistency': consistency_score}
        }

    def _rule_based_analysis(self, text, url=None, title=None):
        clickbait = detect_clickbait(title or text)
        emotions = detect_emotions(text)
        propaganda = detect_propaganda(text)
        domain_score, domain_label = check_domain_reputation(url)
        consistency_score = check_title_consistency(title, text)

        suspicion = (clickbait['score'] * 0.4 + max(emotions.values()) * 0.2 + propaganda['score'] * 0.2 - domain_score * 0.5)

        if suspicion > 20: prediction = 'FAKE'
        elif suspicion > 8: prediction = 'UNCERTAIN'
        else: prediction = 'REAL'
        
        confidence = min(int(abs(suspicion) + 50), 95)
        
        if confidence < 65:
            prediction = 'UNCERTAIN'
        credibility = calculate_credibility(text, prediction, confidence, domain_score, consistency_score)
        reason = generate_reason(prediction, clickbait, emotions, propaganda, domain_label, consistency_score)

        return {
            'prediction': prediction,
            'confidence': confidence,
            'reason': reason,
            'manipulation': get_manipulation_labels(clickbait, emotions, propaganda),
            'credibility': credibility,
            'emotions': emotions,
            'suspicious_sentences': find_suspicious_sentences(text),
            'suggestions': generate_suggestions(prediction, clickbait, propaganda),
            'metadata': {'domain': domain_label, 'consistency': consistency_score}
        }

# Helper functions for labels and suggestions
def find_suspicious_sentences(text):
    sentences = re.split(r'[.!?]+', text)
    suspicious = []
    all_bad_words = CLICKBAIT_WORDS + PROPAGANDA_WORDS
    for emotion_words in EMOTION_WORDS.values():
        all_bad_words.extend(emotion_words)

    for sentence in sentences:
        s = sentence.strip()
        if not s or len(s) < 15: continue
        lower_s = s.lower()
        if any(w in lower_s for w in all_bad_words) or (sum(1 for c in s if c.isupper()) > len(s) * 0.4):
            suspicious.append(s)
    return suspicious[:5] if suspicious else ['No highly suspicious sentences detected.']

def get_manipulation_labels(clickbait_data, emotion_data, propaganda_data):
    labels = []
    if clickbait_data['is_clickbait']: labels.append('Clickbait')
    if emotion_data.get('fear', 0) > 30: labels.append('Fear Tactics')
    if emotion_data.get('anger', 0) > 30: labels.append('Emotional Language')
    if propaganda_data['has_propaganda']: labels.append('Political Bias')
    return labels if labels else ['None Detected']

def generate_suggestions(prediction, clickbait_data, propaganda_data):
    suggestions = [
        '[TIP] Verify with reputable outlets like Reuters or BBC.',
        '[TIP] Check fact-checking sites like Snopes or PolitiFact.'
    ]
    if prediction in ('FAKE', 'UNCERTAIN'):
        suggestions.extend([
            '[CAUTION] Be cautious of high-arousal emotional language.',
            '[ACTION] Search for the claim in reverse to find debunks.'
        ])
    return suggestions

