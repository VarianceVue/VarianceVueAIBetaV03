"""
Stage 2: Text cleaning — header/footer removal, whitespace normalization, boilerplate patterns.
"""
import re
from typing import List


# Common boilerplate patterns (regex); removed when they appear at line start/end
HEADER_FOOTER_PATTERNS = [
    r"^\s*page\s+\d+\s+of\s+\d+\s*$",
    r"^\s*\d+\s+of\s+\d+\s*$",
    r"^\s*-\s*\d+\s*-\s*$",
    r"^\s*confidential\s*$",
    r"^\s*©\s*[\w\s\.]+\s*$",
    r"^\s*http[s]?://\S+\s*$",
]


def _normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace to single space; strip lines and trim."""
    if not text:
        return ""
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(" ".join(ln.split()) for ln in lines if ln).strip()


def _remove_repeated_first_last_lines(text: str, max_repeats: int = 3) -> str:
    """Remove lines that repeat at the very start or end (e.g. headers/footers)."""
    if not text or max_repeats < 1:
        return text
    lines = text.splitlines()
    if len(lines) <= max_repeats * 2:
        return text
    # Strip leading repeated line(s)
    first = lines[0].strip()
    start = 0
    for i in range(1, min(max_repeats + 1, len(lines))):
        if lines[i].strip() == first:
            start = i
        else:
            break
    if start > 0:
        lines = lines[start + 1 :]
    if not lines:
        return ""
    # Strip trailing repeated line(s)
    last = lines[-1].strip()
    end = len(lines) - 1
    for i in range(len(lines) - 2, max(-1, end - max_repeats - 1), -1):
        if lines[i].strip() == last:
            end = i
        else:
            break
    if end < len(lines) - 1:
        lines = lines[: end]
    return "\n".join(lines).strip()


def _remove_boilerplate_lines(text: str) -> str:
    """Drop lines that match common header/footer boilerplate."""
    out = []
    for line in text.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            out.append("")
            continue
        skip = False
        for pat in HEADER_FOOTER_PATTERNS:
            if re.match(pat, line_stripped, re.IGNORECASE):
                skip = True
                break
        if not skip:
            out.append(line)
    return "\n".join(out).strip()


def clean_text(raw_text: str) -> str:
    """
    Clean raw text: normalize whitespace, remove repeated header/footer lines,
    remove common boilerplate lines. Returns cleaned string.
    """
    if not raw_text:
        return ""
    t = _normalize_whitespace(raw_text)
    t = _remove_repeated_first_last_lines(t, max_repeats=2)
    t = _remove_boilerplate_lines(t)
    return _normalize_whitespace(t)
