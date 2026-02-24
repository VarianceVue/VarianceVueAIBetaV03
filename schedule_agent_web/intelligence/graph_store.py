"""
Stage 4: Knowledge graph — store Stage 3 relations as edges; query related entities.
"""
from __future__ import annotations

import os
import json
from typing import List, Dict, Any

from schedule_agent_web.store import _get_redis, _file_store_dir, _safe_session

GRAPH_PREFIX = "vuelogic:graph:"
GRAPH_EDGES_SUFFIX = ":edges"


def _graph_dir(session_id: str) -> str:
    return os.path.join(_file_store_dir(), _safe_session(session_id), "graph")


def _graph_edges_path(session_id: str) -> str:
    return os.path.join(_graph_dir(session_id), "edges.json")


def save_edges(session_id: str, doc_id: str, relations: List[Dict[str, Any]]) -> bool:
    """Store relation triples (subject, relation, object) for this doc. Appends to session edges."""
    if not session_id:
        return False
    edges = [
        {"subject": r.get("subject"), "relation": r.get("relation"), "object": r.get("object"), "doc_id": doc_id}
        for r in (relations or []) if isinstance(r, dict) and r.get("subject") and r.get("object")
    ]
    if not edges:
        return True
    r = _get_redis()
    if r:
        try:
            key = GRAPH_PREFIX + session_id + GRAPH_EDGES_SUFFIX
            raw = r.get(key)
            all_edges = json.loads(raw) if raw else []
            all_edges.extend(edges)
            r.set(key, json.dumps(all_edges))
            return True
        except Exception:
            return False
    try:
        os.makedirs(_graph_dir(session_id), exist_ok=True)
        path = _graph_edges_path(session_id)
        all_edges = []
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                all_edges = json.load(f)
        all_edges.extend(edges)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(all_edges, f, ensure_ascii=False, indent=0)
        return True
    except Exception:
        return False


def get_related(session_id: str, entity: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Return edges where subject or object matches entity (case-insensitive substring).
    Returns list of { subject, relation, object, doc_id }.
    """
    if not session_id or not (entity or "").strip():
        return []
    entity_lower = entity.strip().lower()
    r = _get_redis()
    if r:
        try:
            raw = r.get(GRAPH_PREFIX + session_id + GRAPH_EDGES_SUFFIX)
            all_edges = json.loads(raw) if raw else []
        except Exception:
            return []
    else:
        try:
            path = _graph_edges_path(session_id)
            if not os.path.isfile(path):
                return []
            with open(path, "r", encoding="utf-8") as f:
                all_edges = json.load(f)
        except Exception:
            return []
    out = []
    for e in all_edges:
        sub = (e.get("subject") or "").lower()
        obj = (e.get("object") or "").lower()
        if entity_lower in sub or entity_lower in obj:
            out.append(e)
        if len(out) >= limit:
            break
    return out
