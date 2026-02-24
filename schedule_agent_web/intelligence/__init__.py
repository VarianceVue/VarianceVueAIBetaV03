"""
Stage 4: Intelligence layer — semantic search, signals, knowledge graph, trend analytics.
"""
from schedule_agent_web.intelligence.signal_store import list_signals, save_signal
from schedule_agent_web.intelligence.signals import scan_document_for_signals
from schedule_agent_web.intelligence.graph_store import save_edges, get_related
from schedule_agent_web.intelligence.analytics import record_event, get_trends

__all__ = [
    "list_signals",
    "save_signal",
    "scan_document_for_signals",
    "save_edges",
    "get_related",
    "record_event",
    "get_trends",
]
