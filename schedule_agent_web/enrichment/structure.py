"""
Stage 2: Document structure — detect sections/headings (regex-based).
"""
import re
from typing import List, Dict, Any


def detect_structure(text: str) -> List[Dict[str, Any]]:
    """
    Detect sections/headings in text. Returns list of
    { "title": str, "level": int (1=top), "start": char index, "end": char index }.
    Patterns: "1. Title", "1.1 Title", "## Title", "Section Title" (ALL CAPS), "PART I".
    """
    if not (text or "").strip():
        return []
    sections = []
    lines = text.splitlines()
    pos = 0
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            pos += len(line) + 1
            continue
        level = 1
        title = None
        # Numbered: "1. ", "1.1 ", "1.1.1 "
        m = re.match(r"^(\d+(?:\.\d+)*)\.\s+(.+)", line_stripped)
        if m:
            level = m.group(1).count(".") + 1
            title = m.group(2).strip()
        # Markdown ##
        if title is None and line_stripped.startswith("#"):
            m = re.match(r"^(#+)\s*(.+)", line_stripped)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
        # ALL CAPS line (short) as section header
        if title is None and len(line_stripped) < 80 and line_stripped.isupper():
            title = line_stripped
        # "PART I", "Section A"
        if title is None:
            m = re.match(r"^(PART|SECTION|CHAPTER|APPENDIX)\s+[\w\d]+\s*:?\s*(.*)", line_stripped, re.IGNORECASE)
            if m:
                title = line_stripped
        if title:
            start = pos
            end = pos + len(line)
            sections.append({"title": title, "level": min(level, 4), "start": start, "end": end})
        pos += len(line) + 1
    return sections
