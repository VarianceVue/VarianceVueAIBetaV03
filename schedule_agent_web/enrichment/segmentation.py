"""
Stage 2: Sentence and token segmentation (NLTK).
"""
from typing import List


def _ensure_nltk_punkt() -> None:
    try:
        import nltk
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
    except Exception:
        pass


def segment_sentences(text: str) -> List[str]:
    """
    Split text into sentences. Uses NLTK sentence tokenizer.
    Returns list of non-empty sentence strings.
    """
    if not (text or "").strip():
        return []
    _ensure_nltk_punkt()
    try:
        import nltk
        sentences = nltk.sent_tokenize(text.strip())
        return [s.strip() for s in sentences if s.strip()]
    except Exception:
        # Fallback: split on sentence-ending punctuation
        import re
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        return [p.strip() for p in parts if p.strip()]


def segment_tokens(text: str) -> List[str]:
    """
    Tokenize text into words (NLTK word_tokenize). Returns list of tokens.
    """
    if not (text or "").strip():
        return []
    _ensure_nltk_punkt()
    try:
        import nltk
        return nltk.word_tokenize(text.strip())
    except Exception:
        return text.strip().split()
