# BharatVaani/core/utils.py

import hashlib
import re
from textblob import TextBlob
import nltk
import os
import json

# Download NLTK data required by TextBlob (only if not already present)
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    print("NLTK 'vader_lexicon' not found. Downloading...")
    nltk.download('vader_lexicon', quiet=True)
    print("NLTK 'vader_lexicon' downloaded successfully.")
except Exception as e:
    print(f"NLTK download check failed: {e}")

PREFS_FILE = os.path.join(os.getcwd(), "BharatVaani", "data", "user_preferences.json")


def load_user_preferences():
    if not os.path.exists(PREFS_FILE):
        return {}
    with open(PREFS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_preferences(prefs):
    os.makedirs(os.path.dirname(PREFS_FILE), exist_ok=True)
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)


def clean_text(text: str) -> str:
    """Removes common HTML tags, extra whitespace, and emojis from text."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
    text = re.sub(r'\s+', ' ', text).strip()  # Replace multiple spaces with single space
    # Remove emojis (basic regex, might not catch all)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub(r'', text)
    return text


def get_hash_key(text: str) -> str:
    """Generates a consistent hash key for a given text."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:10]


def analyze_sentiment(text: str) -> dict:
    """
    Performs sentiment analysis on the given text using TextBlob.
    Returns a dictionary with label, score, emoji, and color.
    """
    if not isinstance(text, str) or not text.strip():
        return {"label": "Unknown", "score": 0, "emoji": "❓", "color": "#6c757d"}

    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity # -1.0 to +1.0

        if polarity > 0.1:
            return {"label": "Positive", "score": polarity, "emoji": "😊", "color": "#28a745"} # Green
        elif polarity < -0.1:
            return {"label": "Negative", "score": polarity, "emoji": "😟", "color": "#dc3545"} # Red
        else:
            return {"label": "Neutral", "score": polarity, "emoji": "😐", "color": "#6c757d"} # Gray
    except Exception as e:
        print(f"Sentiment analysis failed: {e}") # Log to console for debugging
        return {"label": "Error", "score": 0, "emoji": "⚠️", "color": "#ffc107"} # Yellow for error


CACHE_FILE = os.path.join(os.getcwd(), "BharatVaani", "data", "latest_articles.json")

def save_cached_articles(articles):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

def load_cached_articles():
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_unique_id(article):
    """
    Generate a unique ID for the article based on title + URL.
    """
    base = (article.get("title", "") + article.get("url", "")).strip()
    if base:
        return hashlib.sha256(base.encode("utf-8")).hexdigest()
    else:
        # fallback: random ID if title/url missing
        return hashlib.sha256(os.urandom(16)).hexdigest()

