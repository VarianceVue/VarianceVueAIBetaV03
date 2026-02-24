"""
Stage 5: Dashboard / insights — aggregate NLP outputs, signals, summaries for UI widgets.
"""
from __future__ import annotations

from typing import Any


def get_dashboard(session_id: str, recent_limit: int = 10) -> dict[str, Any]:
    """
    Return payload for dashboard widgets: signals count, recent signals, NLP summaries,
    ingested doc count, trend buckets. Used by GET /api/dashboard.
    """
    if not session_id:
        return {"signals_count": 0, "recent_signals": [], "nlp_summaries": [], "ingested_count": 0, "trends": []}
    out = {"signals_count": 0, "recent_signals": [], "nlp_summaries": [], "ingested_count": 0, "trends": []}
    try:
        from schedule_agent_web.intelligence import list_signals, get_trends
        signals = list_signals(session_id)
        out["signals_count"] = len(signals)
        out["recent_signals"] = list(reversed(signals[-recent_limit:]))
    except Exception:
        pass
    try:
        from schedule_agent_web.nlp import list_nlp_documents, get_nlp_document
        nlp_list = list_nlp_documents(session_id)
        for item in nlp_list[-recent_limit:]:
            doc_id = item.get("doc_id")
            doc = get_nlp_document(session_id, doc_id) if doc_id else None
            if doc and doc.summary:
                out["nlp_summaries"].append({"doc_id": doc_id, "summary": doc.summary[:300], "created_at": doc.created_at})
    except Exception:
        pass
    try:
        from schedule_agent_web.ingestion import list_ingested_documents
        out["ingested_count"] = len(list_ingested_documents(session_id))
    except Exception:
        pass
    try:
        from schedule_agent_web.intelligence import get_trends
        out["trends"] = get_trends(session_id, bucket_days=7)[-12:]
    except Exception:
        pass
    return out
