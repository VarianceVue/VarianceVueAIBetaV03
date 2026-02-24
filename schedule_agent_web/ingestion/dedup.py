"""
Stage 1 deduplication: content hash (SHA-256) of normalized text.
"""
from __future__ import annotations

import hashlib


def normalize_for_hash(text: str) -> str:
    """Normalize text before hashing: strip, collapse whitespace, optional lower (we keep case for now)."""
    if not text:
        return ""
    t = " ".join(text.split())
    return t.strip()


def content_hash(raw_text: str) -> str:
    """SHA-256 of normalized content for deduplication."""
    normalized = normalize_for_hash(raw_text or "")
    return hashlib.sha256(normalized.encode("utf-8", errors="replace")).hexdigest()
