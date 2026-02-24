"""
Stage 2: Domain vocabulary normalization — map terms to canonical form (project controls).
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Default path for project-controlled term mapping (JSON: { "alias": "canonical" })
_VOCAB_DIR = Path(__file__).resolve().parent
DEFAULT_VOCAB_PATH = _VOCAB_DIR / "vocabulary_map.json"


def load_vocabulary_map(path: str | Path | None = None) -> Dict[str, str]:
    """Load alias -> canonical map from JSON file. Returns dict; empty if file missing."""
    p = path or DEFAULT_VOCAB_PATH
    if not os.path.isfile(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return dict(data) if isinstance(data, dict) else {}
    except Exception:
        return {}


def normalize_text_with_vocabulary(
    text: str,
    vocab: Dict[str, str] | None = None,
    word_boundary: bool = True,
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Replace aliases with canonical terms. Returns (normalized_text, list of {from, to} replacements).
    If word_boundary is True, only replace whole words (regex \b).
    """
    if not text:
        return "", []
    vocab = vocab or load_vocabulary_map()
    if not vocab:
        return text, []
    replacements = []
    out = text
    for alias, canonical in sorted(vocab.items(), key=lambda x: -len(x[0])):
        if not alias or alias == canonical:
            continue
        if word_boundary:
            pattern = r"\b" + re.escape(alias) + r"\b"
        else:
            pattern = re.escape(alias)
        count = 0
        def repl(m):
            nonlocal count
            count += 1
            return canonical
        new_out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
        if new_out != out:
            replacements.append({"from": alias, "to": canonical})
            out = new_out
    return out, replacements
