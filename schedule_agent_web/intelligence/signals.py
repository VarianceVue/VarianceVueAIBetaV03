"""
Stage 4: Anomaly / signal detection — rules + optional LLM for risk/claim/dispute.
"""
from __future__ import annotations

import re
from typing import List, Dict, Any
from datetime import datetime

from schedule_agent_web.intelligence.signal_store import save_signal, list_signals
from schedule_agent_web.nlp.llm_utils import call_llm

# Rule-based keyword sets (case-insensitive)
RISK_KEYWORDS = [
    "delay", "late", "behind schedule", "at risk", "critical path", "float erosion",
    "dispute", "claim", "variance", "overrun", "shortage", "shortfall",
]
CHANGE_KEYWORDS = [
    "change order", "pco", "potential change", "scope change", "scope creep",
    "rfi", "request for information", "change request", "variation",
]
DISPUTE_KEYWORDS = [
    "dispute", "claim", "entitlement", "compensation", "delay claim",
    "disagreement", "reject", "rejection", "contested",
]


def _rule_signals(text: str, doc_id: str, session_id: str) -> List[Dict[str, Any]]:
    """Detect signals from keyword rules. Returns list of { type, snippet, start }."""
    if not text:
        return []
    text_lower = text.lower()
    signals = []
    for kw in RISK_KEYWORDS:
        for m in re.finditer(re.escape(kw), text_lower, re.IGNORECASE):
            start = max(0, m.start() - 80)
            end = min(len(text), m.end() + 120)
            snippet = text[start:end].replace("\n", " ")
            signals.append({"type": "risk", "snippet": snippet[:200], "keyword": kw})
    for kw in CHANGE_KEYWORDS:
        for m in re.finditer(re.escape(kw), text_lower, re.IGNORECASE):
            start = max(0, m.start() - 80)
            end = min(len(text), m.end() + 120)
            snippet = text[start:end].replace("\n", " ")
            signals.append({"type": "change", "snippet": snippet[:200], "keyword": kw})
    for kw in DISPUTE_KEYWORDS:
        for m in re.finditer(re.escape(kw), text_lower, re.IGNORECASE):
            start = max(0, m.start() - 80)
            end = min(len(text), m.end() + 120)
            snippet = text[start:end].replace("\n", " ")
            signals.append({"type": "dispute", "snippet": snippet[:200], "keyword": kw})
    return signals


def _llm_signal_check(passage: str) -> Dict[str, Any]:
    """Ask LLM if passage indicates risk/claim/dispute. Returns { risk, change, dispute } bools."""
    if not passage or len(passage) < 20:
        return {"risk": False, "change": False, "dispute": False}
    system = (
        "You are a project controls analyst. Does the following passage indicate "
        "risk (schedule/cost risk), change (change order/scope change), or dispute (claim/disagreement)? "
        "Reply with ONLY a JSON object: {\"risk\": true/false, \"change\": true/false, \"dispute\": true/false}. No other text."
    )
    reply, err = call_llm(system, passage[:1500], max_tokens=64)
    if err:
        return {"risk": False, "change": False, "dispute": False}
    import json
    try:
        d = json.loads(reply.strip())
        return {
            "risk": bool(d.get("risk", False)),
            "change": bool(d.get("change", False)),
            "dispute": bool(d.get("dispute", False)),
        }
    except Exception:
        return {"risk": False, "change": False, "dispute": False}


def scan_document_for_signals(
    session_id: str,
    doc_id: str,
    text: str,
    use_llm: bool = False,
    max_llm_passages: int = 5,
) -> List[Dict[str, Any]]:
    """
    Run rule-based signal detection on text; optionally run LLM on top passages.
    Saves each signal to signal store and returns list of saved signals.
    """
    if not session_id or not doc_id:
        return []
    rule_hits = _rule_signals(text or "", doc_id, session_id)
    saved = []
    seen_snippets = set()
    for s in rule_hits:
        snippet = (s.get("snippet") or "").strip()
        if not snippet or snippet in seen_snippets:
            continue
        seen_snippets.add(snippet)
        sig = {
            "doc_id": doc_id,
            "session_id": session_id,
            "signal_type": s.get("type", "risk"),
            "source": "rule",
            "text_snippet": snippet[:500],
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        if save_signal(session_id, sig):
            saved.append(sig)
    if use_llm and saved and len(saved) <= max_llm_passages * 3:
        for s in saved[:max_llm_passages]:
            llm_result = _llm_signal_check(s.get("text_snippet", ""))
            for key in ("risk", "change", "dispute"):
                if llm_result.get(key):
                    extra = {
                        "doc_id": doc_id,
                        "session_id": session_id,
                        "signal_type": key,
                        "source": "llm",
                        "text_snippet": (s.get("text_snippet", ""))[:500],
                        "created_at": datetime.utcnow().isoformat() + "Z",
                    }
                    if save_signal(session_id, extra):
                        saved.append(extra)
    return saved
