"""
Stage 2 enriched document store: cleaned text, lang, sentences, structure, normalized text (Redis + file fallback).
"""
from __future__ import annotations

import os
import json
from dataclasses import dataclass, asdict
from typing import Any, List

from schedule_agent_web.store import _get_redis, _file_store_dir, _safe_session

ENRICHED_PREFIX = "vuelogic:enriched:"
ENRICHED_LIST_SUFFIX = ":list"
MAX_CONTENT_SIZE = 500 * 1024 * 1024  # 500MB (no practical limit)


def _safe_id(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in (s or ""))


@dataclass
class EnrichedDocument:
    doc_id: str  # references Stage 1 ingested doc
    session_id: str
    cleaned_text: str
    lang: str
    sentences: List[str]
    structure: List[dict]
    normalized_text: str
    term_replacements: List[dict]
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "EnrichedDocument":
        return cls(
            doc_id=d.get("doc_id", ""),
            session_id=d.get("session_id", ""),
            cleaned_text=d.get("cleaned_text", ""),
            lang=d.get("lang", ""),
            sentences=d.get("sentences") or [],
            structure=d.get("structure") or [],
            normalized_text=d.get("normalized_text", ""),
            term_replacements=d.get("term_replacements") or [],
            created_at=d.get("created_at", ""),
        )


def _enriched_dir(session_id: str) -> str:
    return os.path.join(_file_store_dir(), _safe_session(session_id), "enriched")


def _enriched_list_path(session_id: str) -> str:
    return os.path.join(_enriched_dir(session_id), "meta.json")


def _enriched_doc_path(session_id: str, doc_id: str) -> str:
    return os.path.join(_enriched_dir(session_id), f"{_safe_id(doc_id)}.json")


def _enriched_local_list(session_id: str) -> list:
    if not session_id:
        return []
    try:
        path = _enriched_list_path(session_id)
        if not os.path.isfile(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_enriched_document(enriched: EnrichedDocument) -> bool:
    if len((enriched.cleaned_text or "").encode("utf-8")) > MAX_CONTENT_SIZE:
        return False
    r = _get_redis()
    if r:
        try:
            key_list = ENRICHED_PREFIX + enriched.session_id + ENRICHED_LIST_SUFFIX
            key_doc = ENRICHED_PREFIX + enriched.session_id + ":" + enriched.doc_id
            raw_list = r.get(key_list)
            meta_list = json.loads(raw_list) if raw_list else []
            meta_list = [m for m in meta_list if m.get("doc_id") != enriched.doc_id]
            meta_list.append({
                "doc_id": enriched.doc_id,
                "lang": enriched.lang,
                "sentence_count": len(enriched.sentences),
                "structure_count": len(enriched.structure),
                "created_at": enriched.created_at,
            })
            r.set(key_list, json.dumps(meta_list))
            r.set(key_doc, json.dumps(enriched.to_dict()))
            return True
        except Exception:
            return False
    try:
        root = _enriched_dir(enriched.session_id)
        os.makedirs(root, exist_ok=True)
        with open(_enriched_doc_path(enriched.session_id, enriched.doc_id), "w", encoding="utf-8") as f:
            json.dump(enriched.to_dict(), f, ensure_ascii=False, indent=0)
        list_path = _enriched_list_path(enriched.session_id)
        meta_list = _enriched_local_list(enriched.session_id)
        meta_list = [m for m in meta_list if m.get("doc_id") != enriched.doc_id]
        meta_list.append({
            "doc_id": enriched.doc_id,
            "lang": enriched.lang,
            "sentence_count": len(enriched.sentences),
            "structure_count": len(enriched.structure),
            "created_at": enriched.created_at,
        })
        with open(list_path, "w", encoding="utf-8") as f:
            json.dump(meta_list, f, ensure_ascii=False, indent=0)
        return True
    except Exception:
        return False


def list_enriched_documents(session_id: str) -> list:
    if not session_id:
        return []
    r = _get_redis()
    if r:
        try:
            raw = r.get(ENRICHED_PREFIX + session_id + ENRICHED_LIST_SUFFIX)
            return json.loads(raw) if raw else []
        except Exception:
            return []
    return _enriched_local_list(session_id)


def get_enriched_document(session_id: str, doc_id: str) -> EnrichedDocument | None:
    if not session_id or not doc_id:
        return None
    r = _get_redis()
    if r:
        try:
            raw = r.get(ENRICHED_PREFIX + session_id + ":" + doc_id)
            if not raw:
                return None
            return EnrichedDocument.from_dict(json.loads(raw))
        except Exception:
            return None
    try:
        path = _enriched_doc_path(session_id, doc_id)
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return EnrichedDocument.from_dict(json.load(f))
    except Exception:
        return None
