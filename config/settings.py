# --- OAuth / Server Configuration ---
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# OAuth Redirect
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/oauth2callback')
FLASK_APP_BASE_URL = os.getenv('FLASK_APP_BASE_URL', 'http://localhost:5000')

# Required Google OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

APP_NAME = "BharatVaani"
APP_VERSION = "2.0"
APP_DESCRIPTION = "Your AI-Powered, Localized News Companion for India. Empowering Every Bharat Citizen with Simplified, Localized News Access via AI."

FUTURE_PLANS = [
    "More Regional News Sources: Integrate RSS feeds or APIs from local Indian newspapers and regional news outlets.",
    "Personalized Feeds: Implement user profiles and interest tracking to deliver highly personalized news content (requires database integration).",
    "Offline Mode: Cache summaries and audio for offline access, crucial for areas with intermittent internet connectivity.",
    "Advanced Sentiment Analysis: Develop or integrate models specifically trained on Indian languages and cultural nuances for more accurate sentiment detection.",
    "Voice Commands: Allow users to navigate the app and control audio playback using voice commands, further improving accessibility.",
    "User Feedback Loop: Implement a system for users to rate summaries or translations, helping to improve AI models over time."
]

# --- News Categories and Language Settings ---
NEWS_CATEGORIES = [
    "General", "Business", "Entertainment", "Health", "Science", "Sports", "Technology"
]

# Mapping of language codes to display names for Indian languages
INDIAN_LANGUAGES = {
    "hi": "Hindi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "ne": "Nepali",
    "or": "Odia",
    "pa": "Punjabi",
    "sa": "Sanskrit",
    "ta": "Tamil",
    "te": "Telugu",
    "ur": "Urdu"
}


DEFAULT_NEWS_CATEGORY = "General"
DEFAULT_TARGET_LANGUAGE = "en" # Default to English
DEFAULT_ARTICLE_LIMIT = 10 # Default number of articles to fetch

# --- RSS Feeds Configuration ---
# Moved from ai_news.py
RSS_FEEDS = {
    "India News": ["https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
                   "https://indianexpress.com/section/india/feed/",
                   "https://www.thehindu.com/news/national/feeder/default.rss",
                   "https://www.indiatoday.in/rss/home",
                   "https://www.hindustantimes.com/feeds/rss/india-news/index.xml",
                   "https://www.indiatvnews.com/rssfeed"
                  ],
    "World News": ["http://feeds.bbci.co.uk/news/world/rss.xml",
                   "https://www.aljazeera.com/xml/rss/all.xml",
                   "https://rss.dw.com/rdf/rss-en-all",
                   "https://feeds.skynews.com/feeds/rss/world.xml",
                   "https://www.theguardian.com/world/rss",
                   "http://rss.cnn.com/rss/cnn_topstories.rss",
                   "http://feeds.reuters.com/Reuters/worldNews",
                   "http://hosted.ap.org/lineups/WORLDHEADS.rss",
                   "http://www.huffingtonpost.com/feeds/verticals/world/index.xml"
                  ],
    "Technology": ["https://feeds.feedburner.com/TechCrunch",
                   "https://www.theverge.com/rss/index.xml",
                   "https://feeds.arstechnica.com/arstechnica/index",
                   "https://www.wired.com/feed/rss",
                   "https://www.computerweekly.com/rss",
                   "https://techxplore.com/rss-news/",
                   "https://www.zdnet.com/news/rss.xml",
                   "https://www.gadgets360.com/rss",
                   "https://www.techradar.com/rss"
                  ],
    "Business": ["https://feeds.feedburner.com/wsj/xml/rss/3_7455.xml",
                 "https://feeds.bloomberg.com/markets/news.rss",
                 "https://www.livemint.com/rss/markets",
                 "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
                 "https://www.business-standard.com/rss-feeds/markets-104",
                 "https://moxie.foxbusiness.com/google-publisher/markets.xml",
                 "https://www.morningstar.com/feeds/finance.rss",
                 "https://www.investing.com/rss/news.rss",
                 "https://www.marketwatch.com/feeds/rss/latest/bulletins.xml"
                ]
}

# Keywords for categorizing articles (used for both NewsAPI and RSS)
CATEGORY_KEYWORDS = {
    "General": ["news", "current events", "headlines", "breaking"], # Added a general category for broader matching
    "National": [
        "india", "modi", "delhi", "government", "parliament", "supreme court",
        "indian", "mumbai", "bengaluru", "chennai", "kolkata", "lok sabha",
        "rajya sabha", "ministry", "policy", "law", "judiciary", "states",
        "union territory", "budget", "aadhar", "gst", "demonetization", "ayodhya",
        "kashmir", "punjab", "haryana", "uttar pradesh", "maharashtra", "gujarat",
        "karnataka", "tamil nadu", "west bengal", "bihar", "madhya pradesh",
        "kerala", "andhra pradesh", "telangana", "uttarakhand", "himachal pradesh",
        "goa", "northeast india", "election commission", "cabinet", "raj Bhavan",
        "high court", "constitution", "citizenship", "public sector", "swachh bharat",
        "make in india", "digital india", "bharat", "population", "census"
    ],
    "Business": [
        "stock market", "sensex", "nifty", "ipo", "startup", "rbi", "gdp",
        "economy", "finance", "investment", "trade", "company", "shares",
        "market cap", "inflation", "interest rates", "banks", "nse", "bse",
        "adani", "ambani", "tata", "reliance industries", "hcl tech", "wipro",
        "infosys", "profits", "revenue", "loss", "merger", "acquisition",
        "venture capital", "private equity", "fiscal policy", "monetary policy",
        "nirmala sitharaman", "sebi", "forex", "commodities", "gold prices",
        "oil prices", "cryptocurrency", "bitcoin", "ethereum", "fintech",
        "ecommerce", "taxation", "corporate", "shareholders", "dividend",
        "bonds", "mutual funds", "loan", "credit", "banking sector", "fdi",
        "supply chain", "logistics", "manufacturing", "exports", "imports",
        "employment", "unemployment", "job market", "remittances", "currency"
    ],
    "Politics": [ # Renamed from 'National' in some contexts to 'Politics' for clarity
        "election", "campaign", "voter", "foreign policy", "biden", "putin", "un",
        "elections", "political party", "congress", "bjp", "aap", "trinamool congress",
        "legislature", "diplomacy", "international relations", "summit meeting",
        "treaty", "democracy", "autocracy", "prime minister", "president", "mp",
        "mla", "cabinet minister", "amit shah", "rahul gandhi", "narendra modi",
        "united nations", "nato", "eu", "g20", "g7", "saarc", "bri", "quad",
        "resolution", "bill", "vote", "constituency", "parliamentary session",
        "opposition", "ruling party", "geopolitics", "sanctions", "peace talks",
        "diplomat", "ambassador", "public policy", "governance", "referendum",
        "coalition", "by-election", "manifesto", "party leader", "chief minister",
        "governor", "speaker", "political crisis", "election commission of india",
        "human rights", "international law", "geopolitical"
    ],
    "Technology": [
        "ai", "chatgpt", "google", "apple", "microsoft", "meta", "5g",
        "tech", "technology", "software", "hardware", "artificial intelligence",
        "digital transformation", "internet of things", "iot", "cybersecurity",
        "gadget", "app development", "mobile technology", "computer science",
        "innovation", "data science", "blockchain", "metaverse", "robotics",
        "automation", "web3", "quantum computing", "semiconductor", "chip manufacturing",
        "smartphone", "laptop", "tablet", "wearable tech", "biotech", "spacex",
        "nasa", "tesla motors", "amazon web services", "aws", "samsung electronics",
        "nvidia", "intel corp", "chipset", "developers", "coding", "programming",
        "data analytics", "cloud computing", "virtual reality", "augmented reality",
        "machine learning", "deep learning", "neural networks", "algorithms",
        "patent", "research & development", "tech startup", "silicon valley",
        "software update", "firmware", "bug fix", "developer conference",
        "cyberattack", "data breach", "encryption", "server", "network", "broadband"
    ],
    "Sports": [
        "cricket", "ipl", "bcci", "football", "fifa", "olympics", "virat kohli",
        "sports", "game", "match", "team", "player", "tournament", "championship",
        "world cup", "formula 1", "f1", "tennis", "badminton", "hockey", "kabaddi",
        "athletics", "medal tally", "stadium", "score", "league", "premier league",
        "laliga", "seria a", "nba", "basketball", "messi", "ronaldo", "rohit sharma",
        "ms dhoni", "neeraj chopra", "pv sindhu", "saina nehwal", "odi", "test match",
        "t20", "grand slam", "wimbledon", "french open", "us open tennis",
        "australian open tennis", "icc", "bpl", "psl", "cpl", "mls", "uefa", "ipl auction",
        "fifa world cup", "olympic games", "asian games", "commonwealth games",
        "national games", "sporting event", "athlete", "coach", "umpire", "referee",
        "fixture", "points table", "rankings", "record breaker", "gold medal", "silver medal",
        "bronze medal", "training", "fitness", "sportsmanship", "league table"
    ],
    "Entertainment": [
        "bollywood", "movie", "box office", "netflix", "ott", "shah rukh khan",
        "film", "cinema", "hollywood", "music", "song", "album", "artist",
        "singer", "actor", "actress", "director", "producer", "tv show", "series",
        "streaming platform", "prime video", "disney+ hotstar", "zee5", "sonyliv",
        "concert", "music festival", "award show", "grammy awards", "oscar awards",
        "cannes film festival", "sundance film festival", "deepika padukone",
        "salman khan", "ranbir kapoor", "alaya f", "web series", "celebrity gossip",
        "fashion", "culture", "art", "theatre", "stand-up comedy", "red carpet",
        "trailer launch", "film review", "music video", "reality show", "talent show",
        "talk show", "podcast", "radio", "dj", "band", "album launch", "hit song",
        "blockbuster", "indie film", "documentary", "animation", "visual effects",
        "premiere", "casting", "script", "soundtrack", "pop culture", "bhajan", "ghazal", "folk music"
    ],
    "Health": [
        "health", "medical", "disease", "hospital", "doctor", "medicine", "wellness",
        "fitness", "nutrition", "diet", "mental health", "vaccine", "pandemic",
        "virus", "healthcare", "research", "cure", "treatment", "patient", "therapy",
        "public health", "epidemic", "diagnosis", "surgery", "pharmaceutical",
        "clinical trial", "fda", "who", "cdc", "ayurveda", "yoga", "alternative medicine",
        "covid-19", "cancer", "diabetes", "heart disease", "blood pressure", "immunity",
        "vitamins", "supplements", "exercise", "sleep", "stress", "meditation",
        "dietitian", "physiotherapy", "rehabilitation", "medical device", "drug development",
        "health policy", "insurance", "hospitals", "clinics", "emergency", "first aid"
    ],
    "Science": [
        "science", "research", "discovery", "astronomy", "physics", "chemistry",
        "biology", "space", "universe", "galaxy", "planet", "nasa", "isro",
        "experiment", "data", "theory", "breakthrough", "innovation", "scientist",
        "telescope", "microscope", "genetics", "dna", "evolution", "environment",
        "climate change", "global warming", "ecology", "conservation", "biodiversity",
        "renewable energy", "solar power", "wind power", "nuclear energy",
        "quantum physics", "particle physics", "biotechnology", "nanotechnology",
        "robotics", "artificial intelligence", "machine learning", "algorithm",
        "data science", "astrophysics", "cosmology", "geology", "meteorology",
        "paleontology", "archaeology", "neuroscience", "psychology", "ecology",
        "oceanography", "climatology", "genomics", "proteomics", "stem cells",
        "crispr", "vaccine development", "drug discovery", "medical research"
    ]
}

# --- Summarizer Model ---
SUMMARIZER_MODEL_NAME = "sshleifer/distilbart-cnn-12-6" # Added this line

# --- What If Scenario Models (OpenRouter.ai) ---
# These are free models available via OpenRouter.ai
WHAT_IF_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "google/gemma-2-9b-it:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "huggingface/zephyr-7b-beta:free",
    "mistralai/mistral-7b-instruct:free",
    "openchat/openchat-3.5-1210:free",
    "gryphe/mythomist-7b:free",
]

# Model traits mapping with working models for "What If Scenarios"
WHAT_IF_MODEL_TRAITS = {
    "Balanced & Insightful": "meta-llama/llama-3.1-8b-instruct:free",
    "Creative & Dramatic": "gryphe/mythomist-7b:free",
    "Technical & Precise": "microsoft/phi-3-mini-128k-instruct:free",
    "Fast & Efficient": "meta-llama/llama-3.2-3b-instruct:free",
    "Conversational & Helpful": "openchat/openchat-3.5-1210:free",
    "Analytical & Structured": "google/gemma-2-9b-it:free",
    "Versatile & Reliable": "huggingface/zephyr-7b-beta:free"
}


def get_google_client_config():
    return {
        "web": {
            "client_id": CLIENT_ID,
            "project_id": "bharatvaani-news",  # optional, for consistency
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": CLIENT_SECRET,
            "redirect_uris": [REDIRECT_URI]
        }
    }

