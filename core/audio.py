# BharatVaani/core/audio.py

from gtts import gTTS
import io
import logging
from typing import Optional

from config.settings import INDIAN_LANGUAGES

def generate_audio_data(text: str, lang_code: str) -> Optional[io.BytesIO]:
    """
    Generates audio from text using gTTS and returns it as a BytesIO object.
    """
    if not text or not text.strip():
        logging.warning("No text to generate audio for.")
        return None

    if lang_code not in INDIAN_LANGUAGES:
        logging.error(f"Audio generation not supported for language code: {lang_code}")
        return None

    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp
    except Exception as e:
        logging.error(f"Error generating audio for language {lang_code}: {e}")
        return None