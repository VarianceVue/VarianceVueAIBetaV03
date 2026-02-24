"""
Stage 5: Alerts — notify when high-priority signals are written (webhook: Slack/Teams).
"""
from __future__ import annotations

import os
import json
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def _get_webhook_url() -> str | None:
    url = os.environ.get("ALERT_WEBHOOK_URL") or os.environ.get("SLACK_WEBHOOK_URL") or os.environ.get("TEAMS_WEBHOOK_URL")
    return (url or "").strip() or None


def send_alert(
    session_id: str,
    signal_type: str,
    doc_id: str,
    text_snippet: str = "",
    source: str = "rule",
) -> bool:
    """
    POST to configured webhook (Slack/Teams) when a high-priority signal is saved.
    Returns True if request succeeded. No-op if ALERT_WEBHOOK_URL (or SLACK_WEBHOOK_URL) not set.
    """
    url = _get_webhook_url()
    if not url:
        return False
    payload: dict[str, Any] = {
        "session_id": session_id,
        "signal_type": signal_type,
        "doc_id": doc_id,
        "source": source,
        "snippet": (text_snippet or "")[:500],
    }
    # Slack expects { "text": "..." }; Teams can use summary/text or adaptive card
    body = json.dumps({"text": f"[Stage 5 Alert] {signal_type}: doc={doc_id} | {payload.get('snippet', '')[:200]}"}).encode("utf-8")
    try:
        req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        urlopen(req, timeout=10)
        return True
    except (URLError, HTTPError, OSError):
        return False
