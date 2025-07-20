# BharatVaani/core/summarizer.py

from transformers import pipeline
import logging

from config.settings import SUMMARIZER_MODEL_NAME
from .utils import clean_text

# Global summarization pipeline instance
summarizer_pipeline = None

def load_summarizer_pipeline():
    """Loads and caches the Hugging Face summarization pipeline."""
    global summarizer_pipeline
    if summarizer_pipeline is None:
        try:
            logging.info(f"Loading summarization model: {SUMMARIZER_MODEL_NAME}")
            summarizer_pipeline = pipeline("summarization", model=SUMMARIZER_MODEL_NAME)
            logging.info(f"Summarization model {SUMMARIZER_MODEL_NAME} loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading summarization model {SUMMARIZER_MODEL_NAME}: {e}")
            summarizer_pipeline = None # Ensure it's None if loading fails
    return summarizer_pipeline

def summarize_text(text: str) -> str:
    """
    Summarizes the given text into 2-3 bullet points using the loaded Hugging Face model.
    Handles empty or malformed inputs gracefully.
    """
    if summarizer_pipeline is None:
        logging.error("Summarizer pipeline not loaded.")
        return "Summary not available (AI model failed to load)."

    cleaned_text = clean_text(text)
    if not cleaned_text.strip() or len(cleaned_text.strip()) < 30:
        logging.warning(f"Text too short to summarize: {cleaned_text[:50]}...")
        return "Summary not available for this article."

    max_input_length = summarizer_pipeline.tokenizer.model_max_length if hasattr(summarizer_pipeline.tokenizer, 'model_max_length') else 1024
    if len(cleaned_text.split()) > max_input_length:
        cleaned_text = " ".join(cleaned_text.split()[:max_input_length])

    try:
        summary_result = summarizer_pipeline(
            cleaned_text,
            max_length=100,
            min_length=30,
            do_sample=False,
            truncation=True
        )
        summary = summary_result[0].get('summary_text', '')
        if not summary.strip():
            raise ValueError("Empty summary returned from model.")

        sentences = summary.split('.')
        bullet_points = [f"• {s.strip()}" for s in sentences if s.strip()]
        return "\n".join(bullet_points[:3]) if bullet_points else "Summary not available."
    except Exception as e:
        logging.error(f"Error during summarization: {e}")
        return "Summary generation failed. Please try again later."

# Call load_summarizer_pipeline once when the module is imported
load_summarizer_pipeline()
