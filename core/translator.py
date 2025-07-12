# BharatVaani/core/translator.py

import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from config.settings import INDIAN_LANGUAGES

# Global model and tokenizer instances
tokenizer = None
model = None

def init_translator():
    """
    Loads IndicTrans2 model and tokenizer into memory.
    """
    global tokenizer, model
    if tokenizer is None or model is None:
        try:
            logging.info("Initializing IndicTrans2 model...")
            model_name = "ai4bharat/indictrans2-en-indic-1B"
            tokenizer_local = AutoTokenizer.from_pretrained(
                model_name,
                use_fast=False,
                trust_remote_code=True
            )
            model_local = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            tokenizer = tokenizer_local
            model = model_local
            logging.info("IndicTrans2 initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing IndicTrans2: {e}", exc_info=True)
            tokenizer = None
            model = None
    return tokenizer, model


def translate_text(text: str, target_lang_code: str) -> str:
    tokenizer_local, model_local = init_translator()
    if tokenizer_local is None or model_local is None:
        logging.error("Translation service unavailable. Model is not loaded.")
        return "[Translation service unavailable]"

    if not text or not text.strip():
        return ""

    if target_lang_code == 'en':
        return text

    lang_tag_map = {
        "hi": "hin_Deva",
        "bn": "ben_Beng",
        "gu": "guj_Gujr",
        "kn": "kan_Knda",
        "ml": "mal_Mlym",
        "mr": "mar_Deva",
        "ne": "npi_Deva",
        "or": "ory_Orya",
        "pa": "pan_Guru",
        "sa": "san_Deva",
        "ta": "tam_Taml",
        "te": "tel_Telu",
        "ur": "urd_Arab"
    }

    if target_lang_code not in lang_tag_map:
        logging.warning(f"Invalid target language code: '{target_lang_code}'.")
        return text

    src_lang_tag = "eng_Latn"
    tgt_lang_tag = lang_tag_map[target_lang_code]

    try:
        logging.info(f"Translating text to {target_lang_code} using IndicTrans2.")

        # ✅ Proper format: "<src_tag> <tgt_tag> text"
        tagged_text = f"{src_lang_tag} {tgt_lang_tag} {text}"

        inputs = tokenizer_local(
            tagged_text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )

        generated_tokens = model_local.generate(
            **inputs,
            max_length=512,
        )

        translation = tokenizer_local.batch_decode(
            generated_tokens,
            skip_special_tokens=True
        )[0]

        logging.info(f"Translation successful to {target_lang_code}.")
        return translation

    except Exception as e:
        logging.error(f"Error during IndicTrans2 translation: {e}", exc_info=True)
        return f"[Translation error to {target_lang_code}: {e}]"

# Call init_translator once on import
init_translator()
