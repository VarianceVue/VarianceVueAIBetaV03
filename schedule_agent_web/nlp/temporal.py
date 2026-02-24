"""
Stage 3: Temporal extraction — parse dates (absolute and relative).
"""
from __future__ import annotations

import re
from typing import List, Dict, Any
from datetime import datetime


def extract_dates(text: str) -> List[Dict[str, Any]]:
    """
    Extract date mentions. Uses dateparser for flexible parsing; also regex for ISO and common formats.
    Returns list of { "raw": str, "normalized": "YYYY-MM-DD" or null, "start": int, "end": int }.
    """
    if not text:
        return []
    results = []
    # ISO and simple numeric
    for m in re.finditer(r"\b(\d{4}-\d{2}-\d{2})\b", text):
        results.append({
            "raw": m.group(1),
            "normalized": m.group(1),
            "start": m.start(),
            "end": m.end(),
        })
    # US style MM/DD/YYYY, DD/MM/YYYY
    for m in re.finditer(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", text):
        raw = m.group(0)
        try:
            from dateparser import parse as dp_parse
            parsed = dp_parse(raw)
            if parsed:
                results.append({
                    "raw": raw,
                    "normalized": parsed.strftime("%Y-%m-%d"),
                    "start": m.start(),
                    "end": m.end(),
                })
            else:
                results.append({"raw": raw, "normalized": None, "start": m.start(), "end": m.end()})
        except Exception:
            results.append({"raw": raw, "normalized": None, "start": m.start(), "end": m.end()})
    # Month name + day + year, e.g. January 15, 2024
    for m in re.finditer(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b", text, re.IGNORECASE):
        raw = m.group(0)
        try:
            from dateparser import parse as dp_parse
            parsed = dp_parse(raw)
            if parsed:
                results.append({
                    "raw": raw,
                    "normalized": parsed.strftime("%Y-%m-%d"),
                    "start": m.start(),
                    "end": m.end(),
                })
            else:
                results.append({"raw": raw, "normalized": None, "start": m.start(), "end": m.end()})
        except Exception:
            results.append({"raw": raw, "normalized": None, "start": m.start(), "end": m.end()})
    # Dedupe by span
    seen = set()
    out = []
    for r in results:
        k = (r["start"], r["end"])
        if k not in seen:
            seen.add(k)
            out.append(r)
    out.sort(key=lambda x: x["start"])
    return out
