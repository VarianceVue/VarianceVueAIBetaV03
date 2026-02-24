"""
Stage 4: Trend analytics — store NLP/signal events; aggregate by time bucket.
"""
from __future__ import annotations

import os
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any

from schedule_agent_web.store import _get_redis, _file_store_dir, _safe_session

ANALYTICS_PREFIX = "vuelogic:analytics:"
ANALYTICS_EVENTS_SUFFIX = ":events"


def _analytics_dir(session_id: str) -> str:
    return os.path.join(_file_store_dir(), _safe_session(session_id), "analytics")


def _analytics_events_path(session_id: str) -> str:
    return os.path.join(_analytics_dir(session_id), "events.json")


def record_event(session_id: str, doc_id: str, event_type: str, payload: dict | None = None) -> bool:
    """Record one event: event_type in ('nlp_processed', 'risk_signal', 'change_signal', 'dispute_signal')."""
    if not session_id:
        return False
    at = datetime.utcnow().isoformat() + "Z"
    event = {"doc_id": doc_id, "event_type": event_type, "at": at, "payload": payload or {}}
    r = _get_redis()
    if r:
        try:
            key = ANALYTICS_PREFIX + session_id + ANALYTICS_EVENTS_SUFFIX
            raw = r.get(key)
            events = json.loads(raw) if raw else []
            events.append(event)
            r.set(key, json.dumps(events))
            return True
        except Exception:
            return False
    try:
        os.makedirs(_analytics_dir(session_id), exist_ok=True)
        path = _analytics_events_path(session_id)
        events = []
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                events = json.load(f)
        events.append(event)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=0)
        return True
    except Exception:
        return False


def get_trends(
    session_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
    bucket_days: int = 7,
) -> List[Dict[str, Any]]:
    """
    Aggregate events by time bucket. Returns list of { bucket_start, counts: { event_type: n } }.
    from_date/to_date: ISO date strings (YYYY-MM-DD). Default: last 90 days.
    """
    if not session_id:
        return []
    r = _get_redis()
    if r:
        try:
            raw = r.get(ANALYTICS_PREFIX + session_id + ANALYTICS_EVENTS_SUFFIX)
            events = json.loads(raw) if raw else []
        except Exception:
            return []
    else:
        try:
            path = _analytics_events_path(session_id)
            if not os.path.isfile(path):
                return []
            with open(path, "r", encoding="utf-8") as f:
                events = json.load(f)
        except Exception:
            return []
    now = datetime.utcnow()
    to_d = now.date()
    from_d = (now - timedelta(days=90)).date()
    if to_date:
        try:
            to_d = datetime.fromisoformat(to_date.replace("Z", "+00:00")).date()
        except Exception:
            pass
    if from_date:
        try:
            from_d = datetime.fromisoformat(from_date.replace("Z", "+00:00")).date()
        except Exception:
            pass
    buckets = defaultdict(lambda: defaultdict(int))
    for ev in events:
        at_str = ev.get("at") or ""
        try:
            dt = datetime.fromisoformat(at_str.replace("Z", "+00:00"))
            d = dt.date()
        except Exception:
            continue
        if d < from_d or d > to_d:
            continue
        delta = (d - from_d).days
        bucket_idx = delta // bucket_days
        bucket_start = from_d + timedelta(days=bucket_idx * bucket_days)
        key = bucket_start.isoformat()
        t = ev.get("event_type") or "unknown"
        buckets[key][t] += 1
    out = [{"bucket_start": k, "counts": dict(v)} for k, v in sorted(buckets.items())]
    return out
