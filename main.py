# main.py

from flask import Flask, redirect, request, session, url_for, jsonify, render_template, send_file, flash
import os, json, logging, re, hashlib, io
from datetime import datetime, timedelta  # Import timedelta
from typing import Dict
import uuid
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import requests  # Import requests for Gemini API calls

from core.utils import load_cached_articles, save_cached_articles
from core.utils import generate_unique_id
from core.translator import translate_text


from gtts import gTTS
import base64
from io import BytesIO

from dotenv import load_dotenv

# from openai import OpenAI # Removed as we are switching to Gemini API directly

# Load environment variables at the very top
load_dotenv()

# --- Configuration ---
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_super_secret_fallback_key_please_change_in_prod")

if not app.secret_key:
    # This will now raise an error if FLASK_SECRET_KEY is not set in .env
    raise RuntimeError(
        "FLASK_SECRET_KEY not set in environment variables. Please set a strong, random key in your .env file."
    )

# Set session to be permanent and define its lifetime
app.permanent_session_lifetime = timedelta(minutes=30)  # Sessions will last for 30 minutes

# Explicitly set session cookie domain and path for localhost
# This can sometimes resolve issues with cookie visibility across redirects
app.config['SESSION_COOKIE_DOMAIN'] = 'localhost'
app.config['SESSION_COOKIE_PATH'] = '/'
# If you are using 127.0.0.1 instead of localhost, change the domain accordingly:
# app.config['SESSION_COOKIE_DOMAIN'] = '127.00.1'


CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # New: Get Gemini API Key

if not CLIENT_ID or not CLIENT_SECRET:
    logging.error("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set as environment variables.")
    # In a production app, you might want to handle this more gracefully, e.g., redirect to an error page.
    # For now, it will raise an error if not found.

if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY is not set. Gemini API features may not work.")

REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/oauth2callback')
FLASK_APP_BASE_URL = os.getenv('FLASK_APP_BASE_URL', 'http://localhost:5000')

SCOPES = [
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Import Modular Functions ---
# Ensure these imports are correct based on your file structure (e.g., 'core' vs 'modules')
# Assuming your structure is now 'core' as per the provided snippets
try:
    from config.settings import (
        APP_NAME, APP_VERSION, APP_DESCRIPTION, FUTURE_PLANS,
        NEWS_CATEGORIES, INDIAN_LANGUAGES, DEFAULT_NEWS_CATEGORY,
        DEFAULT_TARGET_LANGUAGE, DEFAULT_ARTICLE_LIMIT, RSS_FEEDS,
        WHAT_IF_MODELS, WHAT_IF_MODEL_TRAITS, CATEGORY_KEYWORDS,
        get_google_client_config, SUMMARIZER_MODEL_NAME
    )
except ImportError as e:
    logging.critical(f"Failed to import from config.settings: {e}. Ensure config/settings.py is correct.")
    raise

try:
    from core.fetcher import fetch_top_headlines, assign_categories_to_articles
except ImportError as e:
    logging.critical(f"Failed to import from core.fetcher: {e}. Ensure core/fetcher.py is correct.")
    raise

try:
    from core.summarizer import summarize_text
except ImportError as e:
    logging.critical(f"Failed to import from core.summarizer: {e}. Ensure core/summarizer.py is correct.")
    raise

try:
    from core.translator import translate_text
except ImportError as e:
    logging.critical(f"Failed to import from core.translator: {e}. Ensure core/translator.py is correct.")
    raise

try:
    from core.audio import generate_audio_data
except ImportError as e:
    logging.critical(f"Failed to import from core.audio: {e}. Ensure core/audio.py is correct.")
    raise

try:
    from core.utils import analyze_sentiment, clean_text, get_hash_key
except ImportError as e:
    logging.critical(f"Failed to import from core.utils: {e}. Ensure core/utils.py is correct.")
    raise

# --- Global/Cached Instances ---
# Removed OpenAI client, now directly using requests for Gemini API
# openai_client_for_what_if = None
# openai_api_key = os.getenv("OPENAI_API_KEY")
# if openai_api_key:
#     try:
#         openai_client_for_what_if = OpenAI(api_key=openai_api_key, base_url="https://openrouter.ai/api/v1")
#     except Exception as e:
#         logging.error(f"Failed to initialize OpenAI client for What If scenarios: {e}")

# File-based user preferences
PREF_DIR = "data"
PREF_FILE_PATH = os.path.join(PREF_DIR, "user_preferences.json")

# Ensure the data directory exists
os.makedirs(PREF_DIR, exist_ok=True)


def load_preferences() -> dict:
    if os.path.exists(PREF_FILE_PATH):
        try:
            with open(PREF_FILE_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from preferences file: {e}. Returning empty preferences.")
            return {}
        except Exception as e:
            logging.error(f"Error loading preferences from {PREF_FILE_PATH}: {e}")
            return {}
    return {}


# Initialize global cache for user preferences
user_prefs_cache = load_preferences()


def save_preferences(preferences: dict):
    global user_prefs_cache
    try:
        # Only save if there are actual changes to avoid unnecessary disk writes
        if preferences != user_prefs_cache:
            with open(PREF_FILE_PATH, 'w') as f:
                json.dump(preferences, f, indent=4)
            user_prefs_cache = preferences.copy()  # Update cache after saving
            logging.info("Preferences updated and saved.")
    except Exception as e:
        logging.error(f"Error saving preferences to {PREF_FILE_PATH}: {e}")


def update_preference(key, value):
    user_prefs_cache[key] = value
    save_preferences(user_prefs_cache)


def get_app_state():
    # Ensure session is marked permanent only once when app_state is first created
    if 'app_state' not in session:
        session['app_state'] = {
            'logged_in': False,
            'user_email': None,
            'user_name': None,
            'user_picture': None,  # New: Add user_picture to app_state
            'selected_category': user_prefs_cache.get('selected_category', DEFAULT_NEWS_CATEGORY),
            'selected_language': user_prefs_cache.get('selected_language', DEFAULT_TARGET_LANGUAGE),
            'article_limit': user_prefs_cache.get('article_limit', DEFAULT_ARTICLE_LIMIT),
            'selected_trait': list(WHAT_IF_MODEL_TRAITS.keys())[0],
            'current_context': '',
            'hypothetical_change': '',
            'scenario_result': None,
            'selected_scope': user_prefs_cache.get('selected_scope', 'India News'),
            'sort_by': user_prefs_cache.get('sort_by', 'date_desc')  # New: Default sort by date descending
        }
        session.permanent = True  # Make the session permanent upon creation
        session.modified = True

    # Robustly add 'user_picture' if it's missing from an existing session
    if 'user_picture' not in session['app_state']:
        session['app_state']['user_picture'] = None
        session.modified = True  # Mark session modified if a new key is added

    return session['app_state']


def mark_as_read(article_id):
    read_articles_set = set(user_prefs_cache.get('read_articles', []))
    read_articles_set.add(article_id)
    user_prefs_cache['read_articles'] = list(read_articles_set)
    save_preferences(user_prefs_cache)
    # No need for session.modified here as user_prefs_cache is global and saved externally


def is_article_read(article_id):
    return article_id in user_prefs_cache.get('read_articles', [])


def get_reading_progress():
    return set(user_prefs_cache.get('read_articles', []))


# --- Flask Routes ---

@app.before_request
def before_request_log_session():
    # Log session contents before processing each request
    # This helps debug what's in the session *before* any route logic runs
    if 'state' in session:
        logging.debug(f"BEFORE_REQUEST: Session contains 'state': {session.get('state')}")
    else:
        logging.debug("BEFORE_REQUEST: Session does NOT contain 'state'.")
    logging.debug(f"BEFORE_REQUEST: Session contents: {dict(session)}")


@app.route('/')
def root():
    app_state = get_app_state()
    if not app_state['logged_in']:
        return render_template('login.html', backend_url=FLASK_APP_BASE_URL, app_version=APP_VERSION,
                               app_description=APP_DESCRIPTION)
    return redirect(url_for('dashboard'))


@app.route('/login')
def login_google():
    client_config = get_google_client_config()
    flow = Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    session.modified = True
    logging.info(f"Redirecting to Google for authorization. Session state set: {state}.")
    logging.debug(f"LOGIN: Session after setting state: {dict(session)}")
    return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Retrieve state from session without popping it immediately
    expected_state = session.get('state')
    received_state = request.args.get('state')

    logging.info(f"OAuth2 Callback: Expected State (from session): {expected_state}")
    logging.info(f"OAuth2 Callback: Received State (from URL): {received_state}")
    logging.debug(f"OAUTH2_CALLBACK: Session at start: {dict(session)}")

    if not expected_state or expected_state != received_state:
        logging.error(
            f"State mismatch or missing state. Expected: {expected_state}, Received: {received_state}. Possible CSRF attack detected.")
        flash('Security error: State mismatch during login. Please try again.', 'error')
        # Clear the potentially invalid state from session
        if 'state' in session:
            session.pop('state')
            session.modified = True
        return redirect(url_for('root'))

    # If states match, then pop it from session
    session.pop('state', None)
    session.modified = True  # Mark session modified after popping state

    flow = Flow.from_client_config(get_google_client_config(), scopes=SCOPES, state=received_state,
                                   redirect_uri=REDIRECT_URI)

    try:
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)

        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'id_token': credentials.id_token
        }
        # Update app_state directly after successful authentication
        app_state = get_app_state()  # Get the mutable app_state from session
        app_state['logged_in'] = True
        app_state['user_name'] = id_token.verify_oauth2_token(
            credentials.id_token, google_requests.Request(), CLIENT_ID
        ).get('name', 'User')
        app_state['user_email'] = id_token.verify_oauth2_token(
            credentials.id_token, google_requests.Request(), CLIENT_ID
        ).get('email')
        app_state['user_picture'] = id_token.verify_oauth2_token(  # New: Get user picture
            credentials.id_token, google_requests.Request(), CLIENT_ID
        ).get('picture')

        session['user'] = {  # Store user info in session for easy templates access
            'name': app_state['user_name'],
            'email': app_state['user_email'],
            'picture': app_state['user_picture']  # New: Store picture in session['user']
        }
        # session.permanent is already set in get_app_state when 'app_state' is first created
        session.modified = True  # Crucial: Mark session modified after updating app_state and session['user']

        logging.info(f"User {app_state['user_email']} logged in successfully. Redirecting to dashboard.")
        logging.debug(f"OAUTH2_CALLBACK: Session before redirect: {dict(session)}")
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))  # Redirect to dashboard after successful login

    except Exception as e:
        logging.error(f"OAuth2 callback error: {e}", exc_info=True)
        flash(f'Login failed: {e}', 'error')
        return redirect(url_for('root'))


@app.route('/logout')
def logout():
    # Clear session data
    logging.info(f"Logging out user.")
    logging.debug(f"LOGOUT: Session before clear: {dict(session)}")
    session.pop('state', None)
    session.pop('credentials', None)
    session.pop('user', None)
    if 'app_state' in session:
        session['app_state']['logged_in'] = False
        session['app_state']['user_name'] = None
        session['app_state']['user_email'] = None
        session['app_state']['user_picture'] = None  # New: Clear user picture on logout
    session.clear()  # Clear all session data
    session.modified = True
    logging.info("User logged out. Session cleared.")
    logging.debug(f"LOGOUT: Session after clear: {dict(session)}")
    flash('You have been logged out.', 'info')
    return redirect(url_for('root'))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    app_state = get_app_state()
    if not app_state['logged_in']:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('root'))

    selected_category = request.args.get('category', app_state['selected_category'])
    selected_language = request.args.get('language', app_state['selected_language'])
    article_limit = int(request.args.get('limit', app_state['article_limit']))
    search_query = request.args.get('search_query', '')
    selected_scope = request.args.get('scope', app_state.get('selected_scope', 'India News'))
    sort_by = request.args.get('sort_by', app_state.get('sort_by', 'date_desc'))  # New: Get sort_by parameter

    # Update app_state and user_prefs_cache for selected filters
    app_state.update({
        'selected_category': selected_category,
        'selected_language': selected_language,
        'article_limit': article_limit,
        'selected_scope': selected_scope,
        'sort_by': sort_by  # New: Update sort_by in app_state
    })
    user_prefs_cache['selected_category'] = selected_category
    user_prefs_cache['selected_language'] = selected_language
    user_prefs_cache['article_limit'] = article_limit
    user_prefs_cache['selected_scope'] = selected_scope
    user_prefs_cache['sort_by'] = sort_by  # New: Save sort_by to preferences
    save_preferences(user_prefs_cache)  # Save updated preferences
    session.modified = True

    news_data = fetch_top_headlines(category=selected_category, country="in", page_size=article_limit,
                                    selected_scope=selected_scope)

    # Pass CATEGORY_KEYWORDS to assign_categories_to_articles
    news_data = assign_categories_to_articles(news_data, CATEGORY_KEYWORDS)

    for article in news_data:
        if not article.get("id"):
            article["id"] = generate_unique_id(article)

    save_cached_articles(news_data)

    # Initialize analytics data structures
    categories_count = {}
    sentiments_count = {'Positive': 0, 'Neutral': 0, 'Negative': 0, 'Unknown': 0,
                        'Error': 0}  # Added 'Unknown' and 'Error'
    top_entities_map = {}  # Initialize top_entities_map here

    if news_data:
        for article in news_data:
            # Date parsing
            if 'published' in article and isinstance(article['published'], str):
                try:
                    # Handle multiple date formats
                    if 'T' in article['published'] and 'Z' in article['published']:  # ISO format
                        article['published'] = datetime.strptime(article['published'], "%Y-%m-%dT%H:%M:%SZ")
                    elif re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", article['published']):  # YYYY-MM-DD HH:MM
                        article['published'] = datetime.strptime(article['published'], "%Y-%m-%d %H:%M")
                    else:  # Try parsing as a generic date string
                        try:
                            article['published'] = datetime.fromisoformat(article['published'].replace('Z', '+00:00'))
                        except ValueError:
                            article['published'] = None  # Fallback if parsing fails
                except ValueError:
                    logging.warning(f"Could not parse date string: {article['published']}")
                    article['published'] = None

            # Assign categories and sentiment for analytics
            cat = article.get('category', 'Uncategorized')
            categories_count[cat] = categories_count.get(cat, 0) + 1

            sentiment_result = analyze_sentiment(article.get('summary', ''))
            article['sentiment_data'] = sentiment_result
            # Ensure the label exists in sentiments_count, add if not
            label = sentiment_result.get('label', 'Unknown')
            sentiments_count[label] = sentiments_count.get(label, 0) + 1

            # Extract entities for analytics
            entities = re.findall(r'\b[A-Z][a-z]+\s(?:[A-Z][a-z]+)?\b', article.get('summary', ''))
            for ent in entities:
                top_entities_map[ent] = top_entities_map.get(ent, 0) + 1

        # Apply search filter after all processing
        if search_query:
            news_data = [
                article for article in news_data
                if search_query.lower() in article.get('title', '').lower()
                   or search_query.lower() in article.get('summary', '').lower()
            ]

        # Apply sorting based on 'sort_by' parameter
        if sort_by == 'date_desc':
            news_data.sort(key=lambda x: x['published'] if isinstance(x['published'], datetime) else datetime.min,
                           reverse=True)
        elif sort_by == 'date_asc':
            news_data.sort(key=lambda x: x['published'] if isinstance(x['published'], datetime) else datetime.max,
                           reverse=False)
        elif sort_by == 'sentiment_pos':
            # Sort by sentiment score, positive first (highest score first)
            news_data.sort(key=lambda x: x.get('sentiment_data', {}).get('score', -2.0),
                           reverse=True)  # Default to -2.0 for unknown/error
        elif sort_by == 'sentiment_neg':
            # Sort by sentiment score, negative first (lowest score first)
            news_data.sort(key=lambda x: x.get('sentiment_data', {}).get('score', 2.0),
                           reverse=False)  # Default to 2.0 for unknown/error

    # Prepare data for templates
    bookmarked_articles_for_template = set(user_prefs_cache.get('bookmarked_articles', []))
    read_articles_for_template = set(user_prefs_cache.get('read_articles', []))

    return render_template(
        'index.html',
        user_name=app_state['user_name'],
        user_picture=app_state['user_picture'],  # New: Pass user_picture to template
        backend_url=FLASK_APP_BASE_URL,
        news_categories=NEWS_CATEGORIES,
        indian_languages=INDIAN_LANGUAGES,
        selected_category=selected_category,
        selected_language=selected_language,
        article_limit=article_limit,
        selected_scope=selected_scope,
        sort_by=sort_by,  # Pass sort_by to template
        articles=news_data,
        bookmarked_articles=bookmarked_articles_for_template,
        read_articles=read_articles_for_template,
        search_query=search_query,
        page_title="News Feed",
        active_tab="news_feed",
        future_plans=FUTURE_PLANS,
        RSS_FEEDS=RSS_FEEDS,
        categories_count=categories_count,
        sentiments_count=sentiments_count,
        total_articles=len(news_data),
        read_articles_count=len(read_articles_for_template),
        bookmark_count=len(bookmarked_articles_for_template),
        top_entities=sorted(top_entities_map.items(), key=lambda x: x[1], reverse=True)[:10],
        now=datetime.now(),  # Pass datetime.now() to the template
        what_if_model_traits=WHAT_IF_MODEL_TRAITS  # Pass what_if_model_traits
    )


@app.route('/api/summarize', methods=['POST'])
def api_summarize():
    data = request.get_json()
    full_text = data.get('full_text')
    target_language = data.get('target_language', 'en')

    if not full_text:
        return jsonify({'success': False, 'error': 'No text provided.'}), 400

    summary = summarize_text(full_text)
    if target_language != 'en':
        summary = translate_text(summary, target_language)

    return jsonify({'success': True, 'summary': summary})


@app.route('/api/translate', methods=['POST'])
def api_translate():
    data = request.get_json()
    text = data.get('text')
    target_language = data.get('target_language')
    article_id = data.get('article_id')

    if not text or not target_language or not article_id:
        return jsonify({'success': False, 'error': 'Missing text, language, or article_id.'}), 400

    translated = translate_text(text, target_language)

    # Store translated text in session for later audio playback
    session.setdefault("translated_texts", {})
    session["translated_texts"][article_id] = {
        "text": translated,
        "language": target_language
    }
    session.modified = True  # Mark session as modified

    user_prefs_cache.setdefault("translations", {})
    user_prefs_cache["translations"][article_id] = {
        "text": translated,
        "language": target_language
    }
    save_preferences(user_prefs_cache)

    return jsonify({'success': True, 'translated_text': translated})


@app.route('/api/audio', methods=['POST'])
def api_audio():
    data = request.get_json()
    article_id = data.get('article_id')  # Get article_id to retrieve translated text
    original_text = data.get('text')  # Original text from the button's data-audio-text
    lang_code = data.get('lang_code', 'en')  # use 'lang_code' to match frontend

    text_to_speak = original_text

    # Check if a translated version of this article exists in the session for the current language
    if article_id and lang_code != 'en' and session.get("translated_texts", {}).get(article_id, {}).get(
            "language") == lang_code:
        text_to_speak = session["translated_texts"][article_id]["text"]
        logging.info(f"Using translated text for audio for article {article_id} in {lang_code}.")
    else:
        logging.info(f"Using original text for audio for article {article_id} in {lang_code}.")

    if not text_to_speak:
        return jsonify({'success': False, 'error': 'No text provided for audio generation'}), 400

    try:
        # Generate audio file
        # gTTS supports ISO 639-1 language codes, which match our INDIAN_LANGUAGES keys
        tts = gTTS(text=text_to_speak, lang=lang_code, slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)

        audio_base64 = base64.b64encode(audio_fp.read()).decode("utf-8")

        return jsonify({
            "success": True,
            "audio_base64": audio_base64
        })

    except Exception as e:
        logging.error(f"Error generating audio for language {lang_code}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f"Audio generation failed for {lang_code}: {str(e)}."}), 500


@app.route('/api/download_summary', methods=['POST'])
def api_download_summary():
    data = request.get_json()
    summary = data.get('summary_text')
    article_id = data.get('article_id', 'unknown')
    target_language = data.get('target_language', 'en')

    if not summary:
        return jsonify({'success': False, 'error': 'No summary text provided.'}), 400

    filename = f"bharatvaani_summary_{article_id}_{target_language}.txt"
    io_buffer = io.BytesIO(summary.encode('utf-8'))
    return send_file(io_buffer, mimetype='text/plain', as_attachment=True, download_name=filename)


@app.route('/api/toggle_bookmark', methods=['POST'])
def api_toggle_bookmark():
    app_state = get_app_state()
    if not app_state['logged_in']:
        return jsonify({'success': False, 'error': 'Login required.'}), 401

    data = request.get_json()
    article_id = data.get('article_id')
    if not article_id:
        return jsonify({'success': False, 'error': 'Invalid article ID.'}), 400

    # Load persistent preferences from disk
    from core.utils import load_user_preferences, save_user_preferences

    prefs = load_user_preferences()
    bookmarks = set(prefs.get('bookmarked_articles', []))

    if article_id in bookmarks:
        bookmarks.remove(article_id)
        message, is_bookmarked = 'Removed from bookmarks.', False
    else:
        bookmarks.add(article_id)
        message, is_bookmarked = 'Bookmarked successfully.', True

    # Save updated bookmarks both:
    # 1. To the persistent JSON file
    # 2. To in-memory user_prefs_cache (if used elsewhere)
    prefs['bookmarked_articles'] = list(bookmarks)
    save_user_preferences(prefs)

    user_prefs_cache['bookmarked_articles'] = list(bookmarks)

    return jsonify({
        'success': True,
        'message': message,
        'is_bookmarked': is_bookmarked,
        'bookmarked_articles': list(bookmarks)
    })


@app.route('/api/mark_read', methods=['POST'])
def mark_article_read():
    app_state = get_app_state()
    if not app_state['logged_in']:
        return jsonify({'success': False, 'error': 'Login required.'}), 401

    data = request.get_json()
    article_id = data.get('article_id')
    if not article_id:
        return jsonify({'success': False, 'error': 'Invalid article ID.'}), 400

    read_set = set(user_prefs_cache.get('read_articles', []))
    read_set.add(article_id)
    user_prefs_cache['read_articles'] = list(read_set)

    save_preferences(user_prefs_cache)
    # No need for session.modified here as user_prefs_cache is global and saved externally

    return jsonify({'success': True})


@app.route('/reading-list')
def reading_list():
    app_state = get_app_state()
    if not app_state['logged_in']:
        flash('Please log in to view your reading list.', 'error')
        return redirect(url_for('root'))

    bookmarked_ids = set(user_prefs_cache.get('bookmarked_articles', []))
    read_ids = set(user_prefs_cache.get('read_articles', []))

    # Load cached articles
    all_news = load_cached_articles()

    # Filter bookmarked articles
    bookmarked_news = [article for article in all_news if article['id'] in bookmarked_ids]

    # Sort bookmarked news by date
    try:
        bookmarked_news.sort(
            key=lambda x: x['published'] if isinstance(x['published'], datetime) else datetime.min,
            reverse=True
        )
    except Exception as e:
        logging.warning(f"Failed to sort bookmarked news by date: {e}")

    # Compute stats
    categories_count = {}
    sentiments_count = {'Positive': 0, 'Neutral': 0, 'Negative': 0, 'Unknown': 0, 'Error': 0}
    top_entities_map = {}

    for article in bookmarked_news:
        # Ensure 'published' is a datetime object for sorting and display
        if 'published' in article and isinstance(article['published'], str):
            try:
                if 'T' in article['published'] and 'Z' in article['published']:  # ISO format
                    article['published'] = datetime.strptime(article['published'], "%Y-%m-%dT%H:%M:%SZ")
                elif re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", article['published']):  # YYYY-MM-DD HH:MM
                    article['published'] = datetime.strptime(article['published'], "%Y-%m-%d %H:%M")
                else:
                    try:
                        article['published'] = datetime.fromisoformat(article['published'].replace('Z', '+00:00'))
                    except ValueError:
                        article['published'] = None
            except ValueError:
                logging.warning(f"Could not parse date string in reading list: {article['published']}")
                article['published'] = None

        category = article.get('category', 'Uncategorized')
        categories_count[category] = categories_count.get(category, 0) + 1

        sentiment = article.get('sentiment_data', analyze_sentiment(article.get('summary', '')))
        label = sentiment.get('label', 'Unknown')
        sentiments_count[label] = sentiments_count.get(label, 0) + 1

        entities = re.findall(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\b', article.get('summary', ''))
        for ent in entities:
            top_entities_map[ent] = top_entities_map.get(ent, 0) + 1

    return render_template(
        'index.html',
        user_name=session['user']['name'] if 'user' in session else 'Guest',
        user_picture=session['user']['picture'] if 'user' in session else None,  # New: Pass user_picture to template
        backend_url=FLASK_APP_BASE_URL,
        articles=bookmarked_news,
        bookmarked_articles=bookmarked_ids,
        read_articles=read_ids,
        page_title="Your Reading List",
        active_tab="reading_list",
        news_categories=NEWS_CATEGORIES,
        indian_languages=INDIAN_LANGUAGES,
        selected_category=app_state['selected_category'],
        selected_language=app_state['selected_language'],
        article_limit=app_state['article_limit'],
        sort_by=app_state['sort_by'],  # Pass sort_by to template
        future_plans=FUTURE_PLANS,
        RSS_FEEDS=RSS_FEEDS,
        categories_count=categories_count,
        sentiments_count=sentiments_count,
        total_articles=len(bookmarked_news),
        read_articles_count=len(read_ids),
        bookmark_count=len(bookmarked_ids),
        top_entities=sorted(top_entities_map.items(), key=lambda x: x[1], reverse=True)[:10],
        now=datetime.now(),  # Pass datetime.now() to the template
        what_if_model_traits=WHAT_IF_MODEL_TRAITS  # Pass what_if_model_traits
    )


@app.route('/analytics')
def analytics():
    app_state = get_app_state()
    if not app_state['logged_in']:
        flash('Login required.', 'error')
        return redirect(url_for('root'))

    # Fetch news for analytics (can be a larger set than dashboard)
    news_data = fetch_top_headlines(category="General", country="in", page_size=50)
    # Pass CATEGORY_KEYWORDS to assign_categories_to_articles
    news_data = assign_categories_to_articles(news_data, CATEGORY_KEYWORDS)

    categories_count = {}
    sentiments_count = {'Positive': 0, 'Neutral': 0, 'Negative': 0, 'Unknown': 0,
                        'Error': 0}  # Added 'Unknown' and 'Error'
    top_entities_map = {}

    for article in news_data:
        # Category counting
        cat = article.get('category', 'Uncategorized')
        categories_count[cat] = categories_count.get(cat, 0) + 1

        # Sentiment counting
        sentiment_result = article.get('sentiment_data', analyze_sentiment(article.get('summary', '')))
        label = sentiment_result.get('label', 'Unknown')
        sentiments_count[label] = sentiments_count.get(label, 0) + 1

        # Entity extraction (simple regex for capitalized words/phrases)
        entities = re.findall(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\b', article.get('summary', ''))
        for ent in entities:
            top_entities_map[ent] = top_entities_map.get(ent, 0) + 1

    total_articles_count = len(news_data)
    read_articles_count = len(get_reading_progress())
    bookmark_count = len(user_prefs_cache.get('bookmarked_articles', []))

    return render_template(
        'index.html',  # Render index.html for analytics tab
        user_name=session['user']['name'] if 'user' in session else 'Guest',
        user_picture=session['user']['picture'] if 'user' in session else None,  # New: Pass user_picture to template
        backend_url=FLASK_APP_BASE_URL,
        page_title="News Analytics",
        active_tab="analytics",
        categories_count=categories_count,
        sentiments_count=sentiments_count,
        total_articles=total_articles_count,
        read_articles_count=read_articles_count,
        bookmark_count=bookmark_count,
        top_entities=sorted(top_entities_map.items(), key=lambda x: x[1], reverse=True)[:10],
        news_categories=NEWS_CATEGORIES,
        indian_languages=INDIAN_LANGUAGES,
        selected_category=app_state['selected_category'],
        selected_language=app_state['selected_language'],
        article_limit=app_state['article_limit'],
        sort_by=app_state['sort_by'],  # Pass sort_by to template
        future_plans=FUTURE_PLANS,
        RSS_FEEDS=RSS_FEEDS,
        now=datetime.now(),  # Pass datetime.now() to the template
        what_if_model_traits=WHAT_IF_MODEL_TRAITS  # Pass what_if_model_traits
    )


@app.route('/settings')
def settings():
    app_state = get_app_state()
    if not app_state['logged_in']:
        flash('Login required.', 'error')
        return redirect(url_for('root'))

    # These are initialized to empty/zero as they are not calculated on the settings page
    categories_count = {}
    sentiments_count = {'Positive': 0, 'Neutral': 0, 'Negative': 0, 'Unknown': 0,
                        'Error': 0}  # Added 'Unknown' and 'Error'
    top_entities_map = {}

    return render_template(
        'index.html',  # Render index.html for settings tab
        user_name=session['user']['name'] if 'user' in session else 'Guest',
        user_picture=session['user']['picture'] if 'user' in session else None,  # New: Pass user_picture to template
        backend_url=FLASK_APP_BASE_URL,
        page_title="Settings",
        active_tab="settings",
        news_categories=NEWS_CATEGORIES,
        indian_languages=INDIAN_LANGUAGES,
        selected_category=app_state['selected_category'],
        selected_language=app_state['selected_language'],
        article_limit=app_state['article_limit'],
        sort_by=app_state['sort_by'],  # Pass sort_by to template
        future_plans=FUTURE_PLANS,
        RSS_FEEDS=RSS_FEEDS,
        categories_count=categories_count,
        sentiments_count=sentiments_count,
        total_articles=0,  # Default to 0 for settings page
        read_articles_count=len(user_prefs_cache.get('read_articles', [])),
        bookmark_count=len(user_prefs_cache.get('bookmarked_articles', [])),
        top_entities=[],  # Default to empty list for settings page
        now=datetime.now(),  # Pass datetime.now() to the template
        what_if_model_traits=WHAT_IF_MODEL_TRAITS  # Pass what_if_model_traits
    )


@app.route('/clear_reading_progress', methods=['POST'])
def clear_reading_progress():
    user_prefs_cache['read_articles'] = []
    save_preferences(user_prefs_cache)
    session.modified = True
    flash('Reading progress cleared!', 'success')
    return redirect(url_for('settings'))


@app.route('/clear_bookmarks', methods=['POST'])
def clear_bookmarks():
    user_prefs_cache['bookmarked_articles'] = []
    save_preferences(user_prefs_cache)
    session.modified = True
    flash('Bookmarks cleared!', 'success')
    return redirect(url_for('settings'))


@app.route('/what_if_scenarios', methods=['GET', 'POST'])
def what_if_scenarios():
    app_state = get_app_state()
    if not app_state['logged_in']:
        flash('Login required.', 'error')
        return redirect(url_for('root'))

    # If this is a POST request, it's likely for updating the selected trait
    if request.method == 'POST':
        selected_trait = request.form.get('selected_model_trait', list(WHAT_IF_MODEL_TRAITS.keys())[0])
        app_state['selected_trait'] = selected_trait
        session.modified = True
        flash('AI Model trait updated.', 'info')
        # Redirect back to GET to clear form submission and display updated trait
        return redirect(url_for('what_if_scenarios'))

    # For GET requests or after a POST redirect
    # Initialize analytics variables with default values for what_if_scenarios view
    categories_count = {}
    sentiments_count = {'Positive': 0, 'Neutral': 0, 'Negative': 0, 'Unknown': 0, 'Error': 0}
    total_articles_analytics = 0
    read_articles_count_analytics = len(get_reading_progress())
    bookmark_count_analytics = len(user_prefs_cache.get('bookmarked_articles', []))
    top_entities = {}

    return render_template(
        'index.html',  # Render index.html for what-if tab
        user_name=session['user']['name'] if 'user' in session else 'Guest',
        user_picture=session['user']['picture'] if 'user' in session else None,  # New: Pass user_picture to template
        backend_url=FLASK_APP_BASE_URL,
        what_if_model_traits=WHAT_IF_MODEL_TRAITS,
        selected_trait=app_state.get('selected_trait'),
        current_context=app_state.get('current_context', ''),
        hypothetical_change=app_state.get('hypothetical_change', ''),
        scenario_result=app_state.get('scenario_result', None),
        active_tab="what_if_scenarios",
        # Pass necessary analytics variables, even if empty, to prevent template errors
        categories_count=categories_count,
        sentiments_count=sentiments_count,
        total_articles=total_articles_analytics,
        read_articles_count=read_articles_count_analytics,
        bookmark_count=bookmark_count_analytics,
        top_entities=top_entities,
        sort_by=app_state['sort_by'],  # Pass sort_by to template
        now=datetime.now(),  # Pass datetime.now() to the template
        # ADDED: Pass all filter-related variables to the template
        news_categories=NEWS_CATEGORIES,
        indian_languages=INDIAN_LANGUAGES,
        selected_category=app_state['selected_category'],
        selected_language=app_state['selected_language'],
        article_limit=app_state['article_limit'],
        RSS_FEEDS=RSS_FEEDS,
        selected_scope=app_state['selected_scope']
    )


@app.route('/generate_what_if', methods=['POST'])
def generate_what_if():
    app_state = get_app_state()
    context = request.form['current_context']
    change = request.form['hypothetical_change']
    trait = request.form.get('selected_model_trait', list(WHAT_IF_MODEL_TRAITS.keys())[0])  # Get trait from form

    app_state.update({
        'current_context': context,
        'hypothetical_change': change,
        'selected_trait': trait  # Store the trait name, not the model ID
    })
    session.modified = True

    if not context or not change:
        flash('Both "Current Situation / Context" and "Hypothetical Change / Scenario" are required!', 'error')
        return redirect(url_for('what_if_scenarios'))

    def _generate_what_if_scenario_llm(current_context: str, hypothetical_change: str, selected_trait: str) -> Dict:
        if not GEMINI_API_KEY:
            return {"error": "Gemini API Key is not configured. Please set GEMINI_API_KEY in your .env file."}

        # Select model based on trait (though for Gemini Flash, it's consistent)
        # We can adjust prompt slightly based on trait if needed, but for now, base prompt is sufficient.
        # model_name = WHAT_IF_MODEL_TRAITS.get(selected_trait, "gemini-2.0-flash") # Fallback to default
        model_name = "gemini-2.0-flash"  # Sticking to gemini-2.0-flash as per previous instruction

        prompt = f"""
        You are an expert geopolitical and economic analyst. Your task is to generate plausible future news headlines and a concise news article summarizing a hypothetical scenario.
        The analysis should be {selected_trait.lower()}.

        Current Situation/Context:
        "{current_context}"

        Hypothetical Change/Event:
        "{hypothetical_change}"

        Based on the above, generate ONE plausible future news HEADLINE and ONE NEWS ARTICLE (approximately 3-5 sentences) that describes the immediate implications of this hypothetical change.
        Ensure the article is detailed and explains everything properly from the context to the possibilities.

        Format your response strictly as follows:
        HEADLINE: [Generated Headline]
        ARTICLE: [Generated News Article]
        """

        # Gemini API call
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 400,  # Increased max output tokens for more detailed article
                "temperature": 0.7,
            }
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            result = response.json()

            if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0][
                'content'].get('parts'):
                generated_text = result['candidates'][0]['content']['parts'][0]['text'].strip()

                headline_match = re.search(r"HEADLINE:\s*(.*)", generated_text, re.IGNORECASE)
                article_match = re.search(r"ARTICLE:\s*(.*)", generated_text, re.IGNORECASE | re.DOTALL)

                headline = headline_match.group(1).strip() if headline_match else "Could not extract headline."
                article_content = article_match.group(
                    1).strip() if article_match else "Could not extract article content."

                return {"headline": headline, "article": article_content}
            else:
                logging.error(f"Gemini API response did not contain expected content: {result}")
                return {"error": "Failed to generate scenario. Unexpected API response structure. Please try again."}

        except requests.exceptions.RequestException as e:
            logging.error(f"Error calling Gemini API for What-If scenario: {e}")
            return {
                "error": f"Failed to connect to AI model: {e}. Please check your GEMINI_API_KEY and network connection."}
        except Exception as e:
            logging.error(f"An unexpected error occurred during Gemini API call: {e}")
            return {"error": f"An unexpected error occurred: {e}. Check server logs."}

    scenario_result_data = _generate_what_if_scenario_llm(context, change, trait)

    app_state['scenario_result'] = scenario_result_data
    session.modified = True

    if scenario_result_data.get("error"):
        flash(scenario_result_data['error'], 'error')
    else:
        flash('Scenario generated successfully!', 'success')
    return redirect(url_for('what_if_scenarios'))


@app.route('/api/simplify_text', methods=['POST'])
def api_simplify_text():
    data = request.get_json()
    text_to_simplify = data.get('text')

    if not text_to_simplify:
        return jsonify({'success': False, 'error': 'No text provided for simplification.'}), 400

    if not GEMINI_API_KEY:
        return jsonify({"success": False, "error": "Gemini API Key is not configured."}), 500

    prompt = f"""
    Simplify the following text so that a 5-year-old can understand it. Use simple words and short sentences.
    Text: "{text_to_simplify}"
    Simplified Text:
    """

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 150,
            "temperature": 0.5,
        }
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0][
            'content'].get('parts'):
            simplified_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            return jsonify({'success': True, 'simplified_text': simplified_text})
        else:
            logging.error(f"Gemini API response for simplify_text did not contain expected content: {result}")
            return jsonify(
                {"success": False, "error": "Failed to simplify text. Unexpected API response structure."}), 500

    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling Gemini API for simplify_text: {e}")
        return jsonify({"success": False, "error": f"Failed to connect to AI model: {e}"}), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred during Gemini API call for simplify_text: {e}")
        return jsonify({"success": False, "error": f"An unexpected error occurred: {e}"}), 500


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Ensure the data directory exists for preferences
    os.makedirs(PREF_DIR, exist_ok=True)
    os.makedirs("static/audio", exist_ok=True)

    # TEMPORARY: Run analytics test once at startup (Optional, for dev only)
    try:
        print("Running startup analytics test...")
        news_data_test = fetch_top_headlines(category="General", country="in", page_size=10)
        news_data_test = assign_categories_to_articles(news_data_test, CATEGORY_KEYWORDS)  # Pass CATEGORY_KEYWORDS

        categories_count_test = {}
        # Initialize sentiments_count_test with 'Unknown' and 'Error' keys
        sentiments_count_test = {'Positive': 0, 'Neutral': 0, 'Negative': 0, 'Unknown': 0, 'Error': 0}
        top_entities_map_test = {}

        for article in news_data_test:
            category = article.get('category', 'Uncategorized')
            categories_count_test[category] = categories_count_test.get(category, 0) + 1

            sentiment_result = analyze_sentiment(article.get('summary', ''))
            # Access label safely, defaulting to 'Unknown' if not present
            label = sentiment_result.get('label', 'Unknown')
            sentiments_count_test[label] = sentiments_count_test.get(label, 0) + 1

            entities = re.findall(r'\b[A-Z][a-z]+\s(?:[A-Z][a-z]+)?\b', article.get('summary', ''))
            for ent in entities:
                top_entities_map_test[ent] = top_entities_map_test.get(ent, 0) + 1

        print("[✓] Analytics Test Complete")
        print(f"Categories: {categories_count_test}")
        print(f"Sentiments: {sentiments_count_test}")
        print(f"Top Entities: {sorted(top_entities_map_test.items(), key=lambda x: x[1], reverse=True)[:5]}")
    except Exception as e:
        print(f"[x] Analytics test failed: {e}")
        logging.error(f"Startup analytics test failed: {e}", exc_info=True)

    app.run(port=5000, debug=True)
