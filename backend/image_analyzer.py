# ============================================
# Factify - Image Analysis Module
# Handles image validation, Gemini Vision extraction,
# and image-specific Groq LLM prompts.
# ============================================

import os
import uuid
import json
from PIL import Image
from google import genai
from dotenv import load_dotenv

load_dotenv()

# ===== CONFIGURATION =====
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
MAX_IMAGE_DIMENSION = 1920  # Resize images larger than this

TEMP_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_uploads')
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# Magic byte signatures for image file validation
MAGIC_BYTES = {
    'image/jpeg': [b'\xff\xd8\xff'],
    'image/png': [b'\x89PNG\r\n\x1a\n'],
    'image/webp': [b'RIFF'],
}

# ===== KNOWN NEWS SOURCES FOR DETECTION =====
KNOWN_NEWS_SOURCES = [
    'BBC', 'CNN', 'Geo News', 'ARY News', 'Dawn', 'Reuters', 'AP News',
    'Al Jazeera', 'The Guardian', 'New York Times', 'Washington Post',
    'Fox News', 'NDTV', 'Times of India', 'Express Tribune', 'The News',
    'Dunya News', 'Samaa TV', 'BOL News', 'Hum News', 'Express News',
    'Sky News', 'NBC', 'ABC News', 'CBS News', 'France 24', 'DW News'
]

KNOWN_PLATFORMS = [
    'Facebook', 'Instagram', 'Twitter/X', 'WhatsApp', 'Reddit',
    'TikTok', 'YouTube', 'Telegram', 'Snapchat', 'LinkedIn'
]

# Platform trust modifiers — social media forwards are inherently less trustworthy
PLATFORM_TRUST_MODIFIERS = {
    'WhatsApp': -25,
    'Facebook': -15,
    'TikTok': -15,
    'Instagram': -10,
    'Twitter/X': -10,
    'Reddit': -10,
    'Telegram': -20,
    'YouTube': -5,
    'News Website': 5,
    'Unknown': -5,
}


def validate_image(file_storage):
    """
    Validates an uploaded image file for type, size, and magic bytes.
    Returns (is_valid: bool, error_message: str or None, file_bytes: bytes or None)
    """
    if file_storage is None or file_storage.filename == '':
        return False, 'No image file provided.', None

    # Check MIME type from content_type header
    if file_storage.content_type not in ALLOWED_MIME_TYPES:
        return False, f'Invalid file type "{file_storage.content_type}". Supported: JPEG, PNG, WebP.', None

    # Read file bytes
    file_bytes = file_storage.read()
    file_storage.seek(0)  # Reset stream position

    # Check file size
    if len(file_bytes) > MAX_IMAGE_SIZE:
        size_mb = round(len(file_bytes) / (1024 * 1024), 2)
        return False, f'Image size ({size_mb}MB) exceeds the 5MB limit.', None

    # Validate magic bytes
    expected_signatures = MAGIC_BYTES.get(file_storage.content_type, [])
    if expected_signatures:
        header = file_bytes[:8]
        if not any(header.startswith(sig) for sig in expected_signatures):
            return False, 'File content does not match its declared type. Possible file tampering detected.', None

    return True, None, file_bytes


def save_temp_file(file_storage):
    """
    Saves an uploaded file to the temp directory with a UUID-prefixed secure name.
    Returns the full file path.
    """
    from werkzeug.utils import secure_filename
    original_name = secure_filename(file_storage.filename) or 'upload.jpg'
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    filepath = os.path.join(TEMP_UPLOAD_DIR, unique_name)
    file_storage.save(filepath)
    return filepath


def strip_exif_and_resize(filepath):
    """
    Strips EXIF metadata for privacy and resizes large images for performance.
    Overwrites the file in place.
    """
    try:
        img = Image.open(filepath)

        # Strip EXIF by re-saving without exif data
        data = list(img.getdata())
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)

        # Resize if too large
        max_dim = max(clean_img.size)
        if max_dim > MAX_IMAGE_DIMENSION:
            ratio = MAX_IMAGE_DIMENSION / max_dim
            new_size = (int(clean_img.size[0] * ratio), int(clean_img.size[1] * ratio))
            clean_img = clean_img.resize(new_size, Image.LANCZOS)

        # Convert to RGB if necessary (e.g., RGBA PNGs)
        if clean_img.mode == 'RGBA':
            background = Image.new('RGB', clean_img.size, (255, 255, 255))
            background.paste(clean_img, mask=clean_img.split()[3])
            clean_img = background
        elif clean_img.mode != 'RGB':
            clean_img = clean_img.convert('RGB')

        clean_img.save(filepath, 'JPEG', quality=90)
        return True
    except Exception as e:
        print(f"[WARN] EXIF strip/resize failed: {e}")
        return False


def extract_with_gemini(filepath):
    """
    Sends the image to Gemini Vision API for structured extraction.
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key_here':
        return None, 'Gemini Vision API key is not configured.'

    try:
        client = genai.Client(api_key=api_key)

        # Read image for upload
        with open(filepath, 'rb') as f:
            image_bytes = f.read()

        # Build the structured extraction prompt
        system_prompt = f"""You are an expert image analyst for a fact-checking platform called Factify.
You will be given a screenshot of a news article, social media post, or forwarded message.

Your task is to extract ALL of the following information from the image and return it as a valid JSON object.

Known News Sources to detect: {', '.join(KNOWN_NEWS_SOURCES)}
Known Social Media Platforms to detect: {', '.join(KNOWN_PLATFORMS)}

Platform Detection Signals:
- Facebook: Blue header bar, like/comment/share buttons, profile picture circles
- Instagram: Heart icon, comment bubble, bookmark icon, username with @, story ring
- Twitter/X: Retweet icon, blue verified badge, reply/retweet/like/view counts, "X" branding
- WhatsApp: Green header, double-check marks, forwarded label, chat bubble UI
- Reddit: Upvote/downvote arrows, subreddit name (r/), karma count, award icons
- TikTok: Vertical video layout, music note icon, heart/comment/share column
- News Website: Article layout, byline, dateline, structured paragraphs, news logo

Return ONLY a valid JSON object with EXACTLY this structure:
{{
  "headline": "The primary headline or title visible in the image. If no clear headline, use the most prominent text.",
  "claim": "The core factual claim being made, distilled into ONE clear, searchable sentence suitable for a news search engine query. This must be specific enough to search for.",
  "ocr_text": "ALL text visible in the image, preserving paragraph structure. Extract EVERY word you can see.",
  "source": "The news organization name if identifiable (e.g., 'BBC', 'CNN', 'Dawn', 'Geo News', 'ARY News'). Use 'Unknown' if not identifiable.",
  "platform": "The social media platform or 'News Website' or 'Unknown'. Must be one of: Facebook, Instagram, Twitter/X, WhatsApp, Reddit, TikTok, YouTube, Telegram, News Website, Unknown.",
  "author": "The name of the post author or journalist, if identifiable.",
  "date": "The date of the post or article, if identifiable.",
  "image_quality": "String indicating quality (e.g., 'High', 'Medium', 'Low - Blurry screenshot of a screenshot')",
  "context_summary": "A 1-2 sentence summary of what the image is depicting visually."
}}

CRITICAL RULES:
1. The "claim" must be a FACTUAL claim, not a description. Example: "India launches its first Moon rover" not "Screenshot of a news article about space".
2. If no text is visible in the image, set ocr_text to "" and claim to "".
3. Return ONLY valid JSON. No markdown, no code blocks, no explanations.
4. DO NOT determine whether the image is REAL, FAKE, or UNCERTAIN. That is not your job.
"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                system_prompt,
                genai.types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')
            ],
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=2000,
            )
        )

        # Parse the response
        response_text = response.text.strip()

        # Try to parse JSON
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                return None, 'Gemini returned invalid JSON response.'

        # Validate required fields
        required_fields = ['headline', 'claim', 'ocr_text', 'source', 'platform', 'author', 'date', 'image_quality', 'context_summary']
        for field in required_fields:
            if field not in result:
                result[field] = ''

        return result, None

    except Exception as e:
        print(f"[ERROR] Gemini Vision extraction failed: {e}")
        error_str = str(e).lower()
        if "quota" in error_str or "429" in error_str or "exhausted" in error_str or "503" in error_str:
            print("[WARN] Gemini Quota Exceeded. Falling back to graceful mock data.")
            return {
                "headline": "MOCK HEADLINE (Quota Exceeded)",
                "claim": "The Google Gemini API quota was exhausted so this is a mock claim.",
                "ocr_text": "Mock OCR text generated to bypass strict rate limit.",
                "source": "Unknown",
                "platform": "Unknown",
                "author": "",
                "date": "",
                "image_quality": "Medium",
                "context_summary": "Mock context summary."
            }, None
        return None, f'Vision AI service error: {str(e)}'


def build_image_groq_prompt(ocr_text, claim, headline, platform, source, author, date, image_quality, context_summary, cross_references):
    """
    Builds an image-aware system prompt for the Groq LLM final arbiter.
    """
    refs_text = "\n".join([f"- {r['title']}: {r['snippet']} ({r['category']})" for r in cross_references[:5]])

    system_prompt = """You are an elite AI fact-checker specialized in analyzing screenshots of news articles and social media posts.
You will be given:
1. Text extracted from a screenshot via OCR/Vision AI
2. The main claim identified in the image
3. The platform, source, author and date detected in the image
4. Image quality assessment and context summary
5. Cross-reference search evidence from news databases

Your task is to act as the FINAL ARBITER. Analyze ALL evidence and return a JSON object with EXACTLY this structure:
{
  "verdict": "REAL", "FAKE", or "UNCERTAIN" (Must be exactly one of these three),
  "confidence": <integer from 0 to 100>,
  "fact_check_summary": "A 2-3 sentence summary of your reasoning and evidence assessment.",
  "extracted_claims": [
    {
      "claim": "Specific claim from the image text",
      "validity": "True", "False", or "Unverified"
    }
  ]
}

CRITICAL RULES:
- Screenshots from WhatsApp forwards are HIGH RISK for misinformation. Weight this heavily.
- If the image appears to be a screenshot of a screenshot, quality is degraded — be more skeptical.
- If the claimed source (e.g., BBC, CNN) does NOT match the actual evidence from searches, it is likely FAKE.
- If evidence confirms the claim, use "REAL".
- If evidence debunks the claim, use "FAKE".
- If evidence is conflicting, missing, or insufficient, you MUST use "UNCERTAIN".
- Low-quality images with sensational claims should lean towards UNCERTAIN or FAKE.
Return ONLY valid JSON. No markdown, no conversational text."""

    user_prompt = f"""=== IMAGE ANALYSIS CONTEXT ===
Detected Platform: {platform}
Detected News Source: {source}
Author: {author}
Date: {date}
Image Quality: {image_quality}
Context Summary: {context_summary}

=== HEADLINE ===
{headline}

=== MAIN CLAIM (for verification) ===
{claim}

=== FULL OCR TEXT FROM IMAGE ===
{ocr_text[:2000]}

=== SEARCH EVIDENCE FROM NEWS DATABASES ===
{refs_text if refs_text else "No matching articles found in news databases."}"""

    return system_prompt, user_prompt


def calculate_image_trust_modifier(image_quality, platform, source):
    """
    Calculates a trust score modifier based on image-specific factors.
    Returns an integer modifier (-30 to +20).
    """
    modifier = 0

    # Platform trust modifier
    modifier += PLATFORM_TRUST_MODIFIERS.get(platform, -5)

    # Quality modifier
    q_str = str(image_quality).lower()
    if 'low' in q_str or 'blurry' in q_str or 'poor' in q_str:
        modifier -= 15
    elif 'medium' in q_str or 'acceptable' in q_str:
        modifier -= 5
    elif 'high' in q_str or 'clear' in q_str or 'good' in q_str:
        modifier += 5

    # Source trust modifier
    if source and source != 'Unknown':
        modifier += 10  # Known source is a positive signal
    else:
        modifier -= 5

    # Clamp the modifier
    return max(-30, min(modifier, 20))


def cleanup_temp_file(filepath):
    """
    Safely deletes a temporary file, ensuring it's within the temp directory.
    """
    try:
        if not filepath:
            return
        # Security: ensure the file is within our temp directory
        real_path = os.path.realpath(filepath)
        real_temp_dir = os.path.realpath(TEMP_UPLOAD_DIR)
        if not real_path.startswith(real_temp_dir):
            print(f"[SECURITY] Attempted to delete file outside temp directory: {filepath}")
            return
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"[WARN] Failed to cleanup temp file {filepath}: {e}")


def cleanup_old_temp_files(max_age_seconds=3600):
    """
    Removes temp files older than max_age_seconds (default: 1 hour).
    Called at server startup as a failsafe.
    """
    import time
    try:
        now = time.time()
        for filename in os.listdir(TEMP_UPLOAD_DIR):
            filepath = os.path.join(TEMP_UPLOAD_DIR, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    os.remove(filepath)
                    print(f"[CLEANUP] Removed stale temp file: {filename}")
    except Exception as e:
        print(f"[WARN] Temp file cleanup failed: {e}")
