"""
Stage 4: Signal store — persist risk/change/dispute signals (Redis + file fallback).
"""
from __future__ import annotations

import os
import json
from typing import List

from schedule_agent_web.store import _get_redis, _file_store_dir, _safe_session

SIGNALS_PREFIX = "vuelogic:signals:"
SIGNALS_LIST_SUFFIX = ":list"


def _signals_dir(session_id: str) -> str:
    return os.path.join(_file_store_dir(), _safe_session(session_id), "signals")


def _signals_meta_path(session_id: str) -> str:
    return os.path.join(_signals_dir(session_id), "meta.json")


def save_signal(session_id: str, signal: dict) -> bool:
    """Append one signal. signal: doc_id, session_id, signal_type, source, text_snippet, created_at."""
    if not session_id:
        return False
    r = _get_redis()
    if r:
        try:
            key = SIGNALS_PREFIX + session_id + SIGNALS_LIST_SUFFIX
            raw = r.get(key)
            signals = json.loads(raw) if raw else []
            signals.append(signal)
            r.set(key, json.dumps(signals))
            return True
        except Exception:
            return False
    try:
        os.makedirs(_signals_dir(session_id), exist_ok=True)
        path = _signals_meta_path(session_id)
        signals = []
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                signals = json.load(f)
        signals.append(signal)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(signals, f, ensure_ascii=False, indent=0)
        return True
    except Exception:
        return False


def list_signals(session_id: str, signal_type: str | None = None) -> List[dict]:
    """Return all signals for session; optionally filter by signal_type (risk, change, dispute)."""
    if not session_id:
        return []
    r = _get_redis()
    if r:
        try:
            raw = r.get(SIGNALS_PREFIX + session_id + SIGNALS_LIST_SUFFIX)
            signals = json.loads(raw) if raw else []
        except Exception:
            return []
    else:
        try:
            path = _signals_meta_path(session_id)
            if not os.path.isfile(path):
                return []
            with open(path, "r", encoding="utf-8") as f:
                signals = json.load(f)
        except Exception:
            return []
    if signal_type:
        signals = [s for s in signals if s.get("signal_type") == signal_type]
    return signals
