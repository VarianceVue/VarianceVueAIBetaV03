"""
Stage 3 NLP output store: entities, relations, classification, dates, summary (Redis + file fallback).
"""
from __future__ import annotations

import os
import json
from dataclasses import dataclass, asdict
from typing import Any, List

from schedule_agent_web.store import _get_redis, _file_store_dir, _safe_session

NLP_PREFIX = "vuelogic:nlp:"
NLP_LIST_SUFFIX = ":list"


def _safe_id(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in (s or ""))


@dataclass
class NLPDocument:
    doc_id: str
    session_id: str
    entities: List[dict]
    relations: List[dict]
    classification: dict
    dates: List[dict]
    summary: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "NLPDocument":
        return cls(
            doc_id=d.get("doc_id", ""),
            session_id=d.get("session_id", ""),
            entities=d.get("entities") or [],
            relations=d.get("relations") or [],
            classification=d.get("classification") or {},
            dates=d.get("dates") or [],
            summary=d.get("summary", ""),
            created_at=d.get("created_at", ""),
        )


def _nlp_dir(session_id: str) -> str:
    return os.path.join(_file_store_dir(), _safe_session(session_id), "nlp")


def _nlp_list_path(session_id: str) -> str:
    return os.path.join(_nlp_dir(session_id), "meta.json")


def _nlp_doc_path(session_id: str, doc_id: str) -> str:
    return os.path.join(_nlp_dir(session_id), f"{_safe_id(doc_id)}.json")


def _nlp_local_list(session_id: str) -> list:
    if not session_id:
        return []
    try:
        path = _nlp_list_path(session_id)
        if not os.path.isfile(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_nlp_document(nlp_doc: NLPDocument) -> bool:
    r = _get_redis()
    if r:
        try:
            key_list = NLP_PREFIX + nlp_doc.session_id + NLP_LIST_SUFFIX
            key_doc = NLP_PREFIX + nlp_doc.session_id + ":" + nlp_doc.doc_id
            raw_list = r.get(key_list)
            meta_list = json.loads(raw_list) if raw_list else []
            meta_list = [m for m in meta_list if m.get("doc_id") != nlp_doc.doc_id]
            meta_list.append({
                "doc_id": nlp_doc.doc_id,
                "entity_count": len(nlp_doc.entities),
                "relation_count": len(nlp_doc.relations),
                "created_at": nlp_doc.created_at,
            })
            r.set(key_list, json.dumps(meta_list))
            r.set(key_doc, json.dumps(nlp_doc.to_dict()))
            return True
        except Exception:
            return False
    try:
        root = _nlp_dir(nlp_doc.session_id)
        os.makedirs(root, exist_ok=True)
        with open(_nlp_doc_path(nlp_doc.session_id, nlp_doc.doc_id), "w", encoding="utf-8") as f:
            json.dump(nlp_doc.to_dict(), f, ensure_ascii=False, indent=0)
        list_path = _nlp_list_path(nlp_doc.session_id)
        meta_list = _nlp_local_list(nlp_doc.session_id)
        meta_list = [m for m in meta_list if m.get("doc_id") != nlp_doc.doc_id]
        meta_list.append({
            "doc_id": nlp_doc.doc_id,
            "entity_count": len(nlp_doc.entities),
            "relation_count": len(nlp_doc.relations),
            "created_at": nlp_doc.created_at,
        })
        with open(list_path, "w", encoding="utf-8") as f:
            json.dump(meta_list, f, ensure_ascii=False, indent=0)
        return True
    except Exception:
        return False


def list_nlp_documents(session_id: str) -> list:
    if not session_id:
        return []
    r = _get_redis()
    if r:
        try:
            raw = r.get(NLP_PREFIX + session_id + NLP_LIST_SUFFIX)
            return json.loads(raw) if raw else []
        except Exception:
            return []
    return _nlp_local_list(session_id)


def get_nlp_document(session_id: str, doc_id: str) -> NLPDocument | None:
    if not session_id or not doc_id:
        return None
    r = _get_redis()
    if r:
        try:
            raw = r.get(NLP_PREFIX + session_id + ":" + doc_id)
            if not raw:
                return None
            return NLPDocument.from_dict(json.loads(raw))
        except Exception:
            return None
    try:
        path = _nlp_doc_path(session_id, doc_id)
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return NLPDocument.from_dict(json.load(f))
    except Exception:
        return None
