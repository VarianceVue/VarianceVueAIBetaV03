"""
Stage 2: Language detection — store lang code in metadata.
"""
from typing import Optional


def detect_language(text: str) -> str:
    """
    Detect language of text. Returns ISO 639-1 code (e.g. 'en', 'es') or 'unknown' if failed.
    Uses langdetect; falls back to 'en' for very short or empty text.
    """
    if not (text or "").strip():
        return "en"
    text_sample = (text or "")[: 5000].strip()
    if len(text_sample) < 20:
        return "en"
    try:
        import langdetect
        return langdetect.detect(text_sample)
    except Exception:
        return "unknown"
