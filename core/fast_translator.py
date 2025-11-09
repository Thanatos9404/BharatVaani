# BharatVaani/core/fast_translator.py

"""
Fast translation using Google Translate (googletrans library)
Much faster than IndicTrans2 model
"""

import logging
from googletrans import Translator, LANGUAGES

# Initialize Google Translator
translator = Translator()

# Language code mapping from our codes to Google Translate codes
LANGUAGE_MAP = {
    'hi': 'hi',  # Hindi
    'bn': 'bn',  # Bengali
    'te': 'te',  # Telugu
    'mr': 'mr',  # Marathi
    'ta': 'ta',  # Tamil
    'gu': 'gu',  # Gujarati
    'kn': 'kn',  # Kannada
    'ml': 'ml',  # Malayalam
    'pa': 'pa',  # Punjabi
    'or': 'or',  # Odia
    'as': 'as',  # Assamese
    'ur': 'ur',  # Urdu
    'en': 'en',  # English
}


def fast_translate(text: str, target_language: str) -> str:
    """
    Fast translation using Google Translate API
    
    Args:
        text: Text to translate
        target_language: Target language code (hi, bn, te, etc.)
    
    Returns:
        Translated text
    """
    try:
        if not text or not text.strip():
            logging.warning("Empty text provided for translation")
            return ""
        
        # Map to Google Translate language code
        google_lang_code = LANGUAGE_MAP.get(target_language, target_language)
        
        if google_lang_code not in LANGUAGES.values():
            logging.error(f"Unsupported language code: {google_lang_code}")
            return text
        
        # Perform translation
        logging.info(f"Translating text to {google_lang_code} using Google Translate...")
        result = translator.translate(text, dest=google_lang_code, src='auto')
        
        if result and result.text:
            logging.info(f"Translation successful to {google_lang_code}")
            return result.text
        else:
            logging.warning(f"Translation returned empty result")
            return text
            
    except Exception as e:
        logging.error(f"Translation error: {e}", exc_info=True)
        return text


def is_google_translate_available() -> bool:
    """Check if Google Translate is available"""
    try:
        test_result = translator.translate("test", dest='hi')
        return test_result is not None
    except Exception as e:
        logging.error(f"Google Translate not available: {e}")
        return False
