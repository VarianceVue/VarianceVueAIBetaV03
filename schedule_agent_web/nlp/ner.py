"""
Stage 3: Named Entity Recognition — regex for project-controls entities + optional spaCy.
"""
from __future__ import annotations

import re
from typing import List, Dict, Any


def _regex_entities(text: str) -> List[Dict[str, Any]]:
    """Extract WBS codes, drawing refs, project codes, and similar via regex."""
    entities = []
    # WBS: 1.1, 1.2.3, 2.1.1.1
    for m in re.finditer(r"\b(\d+(?:\.\d+)+)\b", text):
        entities.append({"text": m.group(1), "label": "WBS", "start": m.start(), "end": m.end()})
    # Drawing / doc refs: DWG-123, 12345-A-01, A-101, Rev 2
    for m in re.finditer(r"\b([A-Z]{1,4}[-_]?\d{2,}(?:[-_][A-Z0-9]+)*(?:\s+Rev\.?\s*\d+)?)\b", text, re.IGNORECASE):
        s = m.group(1)
        if re.match(r"^\d+(?:\.\d+)+$", s):
            continue
        entities.append({"text": s, "label": "DRAWING", "start": m.start(), "end": m.end()})
    # Project code: PRJ-001, 12345, ECEPCS
    for m in re.finditer(r"\b([A-Z]{2,6}[-_]?\d{3,}|\d{5,})\b", text):
        s = m.group(1)
        if re.match(r"^\d+(?:\.\d+)+$", s):
            continue
        entities.append({"text": s, "label": "PROJECT_CODE", "start": m.start(), "end": m.end()})
    # Activity-like IDs: ACT-001, TASK-123
    for m in re.finditer(r"\b(ACT|TASK|WP)[-_]?\d+\b", text, re.IGNORECASE):
        entities.append({"text": m.group(0), "label": "ACTIVITY_ID", "start": m.start(), "end": m.end()})
    # Dedupe by (start, label)
    seen = set()
    out = []
    for e in entities:
        k = (e["start"], e["label"])
        if k not in seen:
            seen.add(k)
            out.append(e)
    return out


def _spacy_entities(text: str) -> List[Dict[str, Any]]:
    """Extract PER, ORG, LOC, etc. via spaCy if available. Run: python -m spacy download en_core_web_sm"""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text[:100000])
        return [
            {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
            for ent in doc.ents
        ]
    except Exception:
        return []


def extract_entities(text: str, use_spacy: bool = True) -> List[Dict[str, Any]]:
    """
    Extract named entities. Always runs regex (WBS, DRAWING, PROJECT_CODE, ACTIVITY_ID).
    If use_spacy and spaCy is installed, adds PER/ORG/LOC etc. Returns list of {text, label, start, end}.
    """
    result = _regex_entities(text or "")
    if use_spacy:
        spacy_ents = _spacy_entities(text or "")
        for e in spacy_ents:
            result.append(e)
    result.sort(key=lambda x: (x["start"], x["label"]))
    return result
