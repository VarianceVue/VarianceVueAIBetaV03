"""
Stage 3: Document/section classification — doc type, risk/change signals (LLM).
"""
from __future__ import annotations

import json
import re
from typing import Dict, Any, List

from schedule_agent_web.nlp.llm_utils import call_llm


def classify_document(text: str, max_chars: int = 8000) -> Dict[str, Any]:
    """
    Classify document: document_type, risk_signal (bool), change_signal (bool), confidence.
    Uses LLM with structured prompt. Returns dict; on LLM failure returns defaults.
    """
    if not (text or "").strip():
        return {"document_type": "unknown", "risk_signal": False, "change_signal": False, "confidence": 0}
    sample = (text or "")[:max_chars]
    system = (
        "You are a project controls analyst. Classify the following document excerpt. "
        "Respond with ONLY a JSON object, no other text. Use this exact shape: "
        '{"document_type": "scope|schedule|rfi|risk|change_order|report|other", '
        '"risk_signal": true or false, "change_signal": true or false, "confidence": 0.0 to 1.0}. '
        "risk_signal: true if the text indicates risk, delay, or dispute. "
        "change_signal: true if the text indicates a change order, PCO, or scope change."
    )
    reply, err = call_llm(system, f"Classify this document:\n\n{sample}", max_tokens=256)
    if err:
        return {"document_type": "unknown", "risk_signal": False, "change_signal": False, "confidence": 0, "error": err}
    data = _parse_json(reply)
    if not data:
        return {"document_type": "unknown", "risk_signal": False, "change_signal": False, "confidence": 0}
    return {
        "document_type": str(data.get("document_type", "other"))[:50],
        "risk_signal": bool(data.get("risk_signal", False)),
        "change_signal": bool(data.get("change_signal", False)),
        "confidence": min(1.0, max(0.0, float(data.get("confidence", 0)))),
    }


def _parse_json(s: str) -> dict | None:
    s = (s or "").strip()
    m = re.search(r"\{[^{}]*\}", s, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    try:
        return json.loads(s)
    except Exception:
        return None
