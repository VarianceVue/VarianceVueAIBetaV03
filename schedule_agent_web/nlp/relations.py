"""
Stage 3: Relation extraction — (subject, relation, object) triples via LLM.
"""
from __future__ import annotations

import json
import re
from typing import List, Dict, Any

from schedule_agent_web.nlp.llm_utils import call_llm


def extract_relations(text: str, max_chars: int = 6000) -> List[Dict[str, Any]]:
    """
    Extract relation triples: subject, relation, object. Uses LLM.
    Returns list of { "subject": str, "relation": str, "object": str }.
    """
    if not (text or "").strip():
        return []
    sample = (text or "")[:max_chars]
    system = (
        "You are a project controls analyst. From the following text, extract relation triples: "
        "(subject, relation, object). Focus on: who is responsible, what causes delay, what is affected, "
        "contractor-owner relations, scope-change causes. "
        "Respond with ONLY a JSON array of objects, each with keys: subject, relation, object. "
        "Example: [{\"subject\": \"Contractor X\", \"relation\": \"claims delay due to\", \"object\": \"late delivery\"}]. "
        "No other text, no markdown."
    )
    reply, err = call_llm(system, f"Extract relation triples from:\n\n{sample}", max_tokens=1024)
    if err:
        return []
    data = _parse_json_array(reply)
    if not isinstance(data, list):
        return []
    out = []
    for item in data:
        if isinstance(item, dict) and item.get("subject") and item.get("object"):
            out.append({
                "subject": str(item.get("subject", ""))[:200],
                "relation": str(item.get("relation", ""))[:200],
                "object": str(item.get("object", ""))[:200],
            })
    return out


def _parse_json_array(s: str) -> list:
    s = (s or "").strip()
    m = re.search(r"\[[\s\S]*\]", s)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    try:
        return json.loads(s)
    except Exception:
        return []
