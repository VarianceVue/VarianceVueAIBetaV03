"""
Stage 5: Audit trail — link answers and signals to doc + passage (traceable to source).
"""
from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Any, List

from schedule_agent_web.store import _get_redis, _file_store_dir, _safe_session

AUDIT_PREFIX = "vuelogic:audit:"
AUDIT_MAX_ENTRIES = 500


def _audit_path(session_id: str) -> str:
    return os.path.join(_file_store_dir(), _safe_session(session_id), "audit.json")


def append_audit(session_id: str, entry_type: str, payload: dict) -> bool:
    """Append one audit entry. entry_type: 'answer' | 'signal' | 'report'. payload: doc_id, sources, snippet, etc."""
    if not session_id:
        return False
    entry = {
        "type": entry_type,
        "at": datetime.utcnow().isoformat() + "Z",
        **payload,
    }
    r = _get_redis()
    if r:
        try:
            key = AUDIT_PREFIX + session_id
            raw = r.get(key)
            entries = json.loads(raw) if raw else []
            entries.append(entry)
            entries = entries[-AUDIT_MAX_ENTRIES:]
            r.set(key, json.dumps(entries))
            return True
        except Exception:
            return False
    try:
        path = _audit_path(session_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        entries = []
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                entries = json.load(f)
        entries.append(entry)
        entries = entries[-AUDIT_MAX_ENTRIES:]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=0)
        return True
    except Exception:
        return False


def get_audit_trail(session_id: str, limit: int = 100, entry_type: str | None = None) -> List[dict]:
    """Return recent audit entries; optional filter by entry_type."""
    if not session_id:
        return []
    r = _get_redis()
    if r:
        try:
            raw = r.get(AUDIT_PREFIX + session_id)
            entries = json.loads(raw) if raw else []
        except Exception:
            return []
    else:
        try:
            path = _audit_path(session_id)
            if not os.path.isfile(path):
                return []
            with open(path, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except Exception:
            return []
    if entry_type:
        entries = [e for e in entries if e.get("type") == entry_type]
    return list(reversed(entries[-limit:]))
