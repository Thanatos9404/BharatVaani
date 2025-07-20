# BharatVaani/core/fetcher.py

import requests
from datetime import datetime, timedelta
import feedparser  # New import for RSS parsing
from requests.adapters import HTTPAdapter  # For retries
from urllib3.util.retry import Retry  # For retries
import re
import io  # For image thumbnail processing
from PIL import Image  # For image thumbnail processing
import base64  # For image thumbnail encoding
from urllib.parse import urljoin, urlparse  # For URL handling

from typing import List, Dict
import logging

# Import from your config and utils
from config.settings import CATEGORY_KEYWORDS, RSS_FEEDS  # Now importing RSS_FEEDS
from .utils import clean_text, get_hash_key, analyze_sentiment  # Ensure these are correctly imported

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- Helper Functions for RSS Fetching ---

def create_session():
    """Creates a requests session with retry strategy."""
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def extract_image_from_rss(entry, base_url=""):
    """
    Extracts an image URL from an RSS entry.
    Checks media_thumbnail, media_content, enclosures, and then parses content/summary.
    """
    image_url = None
    try:
        if hasattr(entry, 'media_thumbnail'):
            image_url = entry.media_thumbnail[0]['url']
        elif hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if media.get('medium') == 'image':
                    image_url = media['url']
                    break
        elif hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                if enclosure.type and 'image' in enclosure.type:
                    image_url = enclosure.href
                    break
        elif hasattr(entry, 'content'):
            content = entry.content[0].value if entry.content else ""
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)', content)
            if img_match:
                image_url = img_match.group(1)
        elif hasattr(entry, 'summary'):
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)', entry.summary)
            if img_match:
                image_url = img_match.group(1)

        # Handle relative URLs
        if image_url and not image_url.startswith('http'):
            if base_url:
                image_url = urljoin(base_url, image_url)
        return image_url
    except Exception as e:
        logging.debug(f"Error extracting image from RSS entry: {e}")
        return None


def get_image_thumbnail(image_url, size=(150, 100)):
    """
    Fetches an image from a URL, creates a thumbnail, and returns it as a base64 encoded string.
    """
    try:
        if not image_url:
            return None
        response = requests.get(image_url, timeout=10, stream=True)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        img = Image.open(io.BytesIO(response.content))
        img.thumbnail(size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except requests.exceptions.RequestException as e:
        logging.warning(f"Failed to fetch image {image_url}: {e}")
        return None
    except Exception as e:
        logging.warning(f"Error processing image thumbnail from {image_url}: {e}")
        return None


# --- Main News Fetching Function (now using RSS) ---

def fetch_top_headlines(category: str = "general", country: str = "in", page_size: int = 20,
                        selected_scope: str = "India News") -> List[Dict]:
    """
    Fetches news from RSS feeds based on selected scope. Ensures articles have valid summary/content.
    """
    news = []
    seen_ids = set()
    session = create_session()
    feeds_to_fetch = RSS_FEEDS.get(selected_scope, RSS_FEEDS["India News"])  # fallback to default if missing

    logging.info(f"Attempting to fetch news from RSS feeds for scope: {selected_scope}")

    for url in feeds_to_fetch:
        try:
            logging.info(f"Fetching from RSS feed: {url}")
            response = session.get(url, timeout=15)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)

            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

            for entry in parsed.entries:
                if len(news) >= page_size:
                    break

                title = clean_text(getattr(entry, 'title', '')).strip()
                summary = clean_text(getattr(entry, 'summary', '')).strip()
                content = ''
                if hasattr(entry, 'content') and entry.content and isinstance(entry.content, list):
                    content = clean_text(entry.content[0].get('value', '')).strip()

                link = getattr(entry, 'link', '').strip()

                if not title or not link or len(title) < 10:
                    continue

                # Skip articles missing both content and summary
                if not summary and not content:
                    logging.debug(f"Skipping article with title '{title}' due to missing content and summary.")
                    continue

                # Use summary or content (whichever is available)
                main_text = summary if summary else content

                dedup_id = getattr(entry, 'id', getattr(entry, 'guid', None)) or link or (title + getattr(entry, 'published', ''))
                dedup_id = get_hash_key(dedup_id)

                if dedup_id in seen_ids:
                    continue
                seen_ids.add(dedup_id)

                published_date = "Unknown"
                try:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_dt = datetime(*entry.published_parsed[:6])
                        if datetime.now() - pub_dt > timedelta(days=7):
                            continue
                        published_date = pub_dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

                full_text_for_ai = f"{title}. {main_text}"

                article_data = {
                    'id': dedup_id,
                    'title': title,
                    'summary': summary,
                    'content': content,
                    'url': link,
                    'published': published_date,
                    'source': getattr(entry, 'source', {}).get('title', urlparse(url).netloc.replace('www.', '')),
                    'image_url': extract_image_from_rss(entry, base_url),
                    'sentiment_data': analyze_sentiment(full_text_for_ai),
                    'full_text_for_ai': full_text_for_ai
                }

                news.append(article_data)

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error fetching from RSS feed {url}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during fetch from {url}: {e}", exc_info=True)

    logging.info(f"Finished fetching RSS news. Total articles collected: {len(news)}")
    return news


def assign_categories_to_articles(articles: List[Dict], category_keywords: Dict[str, List[str]]) -> List[Dict]:
    """
    Assigns categories and sentiment to articles based on provided keywords.
    Modified to accept category_keywords as an argument.
    """
    for article in articles:
        # Category assignment
        article['category'] = "Uncategorized"
        text_content = (article.get('title', '') + " " + article.get('summary', '')).lower()

        for category, keywords in category_keywords.items(): # Use passed category_keywords
            if any(keyword.lower() in text_content for keyword in keywords):
                article['category'] = category
                break

        # Sentiment analysis (already done in fetch_top_headlines, but keep for robustness)
        if 'sentiment_data' not in article:  # Ensure sentiment_data key is present
            text_for_sentiment = article.get('summary', '') or article.get('title', '')
            article['sentiment_data'] = analyze_sentiment(text_for_sentiment)

    return articles


def categorize_news(news: List[Dict], category: str, category_keywords: Dict[str, List[str]]) -> List[Dict]:
    """
    Filters news by category based on provided keywords.
    Modified to accept category_keywords as an argument.
    """
    if category == "All":
        return news

    if category not in category_keywords: # Use passed category_keywords
        logging.warning(f"Category '{category}' not found in CATEGORY_KEYWORDS. Returning all news.")
        return news

    keywords = category_keywords[category] # Use passed category_keywords
    categorized = []
    for article in news:
        text_content = (article.get('title', '') + " " + article.get('summary', '')).lower()
        if any(keyword.lower() in text_content for keyword in keywords):
            categorized.append(article)
    return categorized

