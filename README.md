# 🇮🇳 BharatVaani: Your AI-Powered, Localized News Companion

> **Empowering Every Bharat Citizen with Simplified, Localized News Access via AI**

---

## 🚩 Problem Statement

In India, particularly in Tier 2 and Tier 3 regions, access to timely and relevant news is often hindered by significant language barriers and varying levels of digital literacy. While English news is abundant, concise, easy-to-understand content in regional languages is scarce. Traditional news consumption methods may not be accessible for everyone, highlighting a critical need for simplified, localized, and audio-friendly news delivery.

**BharatVaani** directly addresses this challenge by providing an intuitive, AI-powered platform that democratizes news access. Our solution ensures that every citizen, regardless of their linguistic background or reading proficiency, can effortlessly engage with top trending news.

---

## Demo

> https://youtu.be/wvOa9x7HVoI

---

## ✨ Features Designed for Impact

- ### **📰 AI-Powered News Fetching**
  - Dynamically fetches top trending news headlines from NewsAPI.org across diverse categories (General, Business, Entertainment, Health, Science, Sports, Technology), with a default focus on India-centric content.

- ### **🤖 Intelligent AI Summarization**
  - Utilizes Hugging Face's distilbart-cnn-12-6 model to distill lengthy English articles into concise, easy-to-digest 2-3 bullet point summaries.

- ### **🌐 Multi-Language Translation (Indic Languages)**
  - Seamlessly translates news summaries into popular Indian languages, including Hindi (hi), Tamil (ta), Bengali (bn), Gujarati (gu), Marathi (mr), Telugu (te), Kannada (kn), Malayalam (ml), and Punjabi (pa).

- ### **🗣️ Accessible Text-to-Speech (TTS)**
  - Converts translated (or English) summaries into natural-sounding audio using gTTS, aiding visually impaired users or those who prefer auditory learning.

- ### **🧠 AI Sentiment Analysis**
  - Integrates TextBlob to analyze the emotional tone (Positive, Neutral, Negative) of news headlines.

- ### **✨ AI-Powered Text Simplification **
  - Simplifies complex news summaries into language understandable by a 5-year-old, enhancing digital literacy and comprehension.

- ### **🔮 What-If Scenario Analysis **
  - Allows users to explore hypothetical geopolitical and economic scenarios using AI-generated future news headlines and concise articles.

- ### **⬇️ Summary Download**
  - Enables users to download generated summaries as `.txt` files for offline access or sharing.

- ### **💖 Personalized Reading List & Bookmarking**
  - Users can bookmark articles for later reading, creating a personalized news experience.

- ### **📊 Comprehensive News Analytics**
  - Provides dashboards displaying reading activity, sentiment distribution, and categorized coverage.

- ### **🔒 Secure Google OAuth 2.0 Authentication**
  - Ensures secure login and user data protection.

- ### **🎨 Clean & Intuitive UI (Flask & Tailwind CSS)**
  - Responsive frontend built with Jinja2 templates and Tailwind CSS.

- ### **🛠️ Modular & Maintainable Codebase**
  - Organized into maintainable Python modules for easy future enhancements.

---

## 🛠️ Technologies Used

| Technology                 | Purpose                                                           |
|----------------------------|-------------------------------------------------------------------|
| **Python 3.9+**           | Core programming language powering the backend logic              |
| **Flask**                  | Lightweight web backend framework for building web applications   |
| **Jinja2**                 | HTML templating engine integrated with Flask                      |
| **Tailwind CSS**           | Utility-first CSS framework for fast, modern, and responsive UI   |
| **HTML5 / CSS3 / JS**     | Frontend foundation for structure, styling, and interactivity     |
| **NewsAPI.org**            | Fetches latest news headlines and articles                        |
| **Hugging Face Transformers** | Text summarization using pretrained distilbart-cnn-12-6 model  |
| **TextBlob**               | Sentiment analysis of text                                        |
| **NLTK**                   | Natural Language Toolkit (dependency for TextBlob)                |
| **deep-translator**        | Translation to Indian languages using Google Translate            |
| **IndicTrans2 (AI4Bharat)** | Advanced translation between English and Indic languages         |
| **gTTS**                   | Text-to-Speech audio generation                                   |
| **google-auth-oauthlib**   | Google OAuth 2.0 login and authentication flow                    |
| **Google Gemini API**      | Text simplification and hypothetical scenario generation         |
| **requests**               | HTTP requests for interacting with APIs                           |
| **python-dotenv**          | Environment variable management                                   |
| **re (Regex)**             | Extracts named entities for analytics                             |
| **datetime**               | Date/time parsing and formatting                                  |
| **logging**                | Application logging and error tracking                            |
| **Pillow (PIL)**           | Image handling and processing (e.g., icons, logos)                |
| **sonner.js / toasts**     | Displays toast notifications in the frontend (optional UI lib)    |
| **Framer Motion**          | Frontend animations for React UI (from your React experiments)    |
| **Lucide-react**           | Icon library used in your React sample UI                         |
| **venv**                   | Python virtual environment management                             |
| **git**                    | Version control and collaboration                                 |
| **VS Code / PyCharm**     | Recommended development IDEs                                      |

---

## 🚀 Setup and Installation (Local Development)

### Prerequisites

- Python 3.9+
- pip
- git

---

### Steps

#### 1. Clone the repository:

```bash

git clone https://github.com/Thanatos9404/BharatVaani.git
cd BharatVaani
```

#### 2. Create and activate a virtual environment
Create a Python virtual environment:

```bash

python -m venv venv
```
On Windows:

```bash

.\venv\Scripts\activate
```
On macOS/Linux:

```bash

source venv/bin/activate
```

#### 3. Install dependencies
Install all required Python libraries:

```bash

pip install -r requirements.txt
```

#### 4. Download NLTK Data
TextBlob requires NLTK’s vader_lexicon for sentiment analysis:

```bash

python -c "import nltk; nltk.download('vader_lexicon')"
```

#### 5. Get Your API Keys
**NewsAPI Key**: Sign up at NewsAPI.org and generate your API key.

Google OAuth 2.0 Credentials:

Go to Google Cloud Console.

- Create a new project.

- Enable OAuth 2.0 credentials.

- Set Authorized Redirect URI to:

```bash

http://localhost:5000/oauth2callback
```
**Google Gemini API Key:**

- Sign up at Google AI Studio or Google Cloud Console.

- Generate your Gemini API key.

#### 6. Create .env File
In your project root, create a file named .env with the following contents:

```
FLASK_SECRET_KEY="YOUR_STRONG_RANDOM_FLASK_SECRET_KEY"
NEWS_API_KEY="YOUR_NEWS_API_KEY_HERE"
GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID_HERE"
GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_CLIENT_SECRET_HERE"
REDIRECT_URI="http://localhost:5000/oauth2callback"
FLASK_APP_BASE_URL="http://localhost:5000"
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
```
> **Important: Don’t commit your .env file to version control (add it to .gitignore).**

#### 7. Run the Application
Run the Flask app:

```bash

python main.py
```
The app will be available at:
```
http://localhost:5000
```
---
