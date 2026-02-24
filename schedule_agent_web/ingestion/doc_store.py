"""
Stage 1 normalized document store: one place for raw text + metadata (Redis + file fallback).
"""
from __future__ import annotations

import os
import json
import time
from dataclasses import dataclass, asdict
from typing import Any

# Reuse store's Redis and file_store layout
from schedule_agent_web.store import _get_redis, _file_store_dir, _safe_session


INGESTED_PREFIX = "vuelogic:ingested:"
INGESTED_LIST_SUFFIX = ":list"
MAX_CONTENT_SIZE = 500 * 1024 * 1024  # 500MB (no practical limit)


def _safe_id(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in (s or ""))


@dataclass
class NormalizedDocument:
    id: str
    session_id: str
    source: str
    format: str
    filename: str
    raw_text: str
    metadata: dict[str, Any]
    content_hash: str
    created_at: str

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "NormalizedDocument":
        return cls(
            id=d.get("id", ""),
            session_id=d.get("session_id", ""),
            source=d.get("source", "upload"),
            format=d.get("format", ""),
            filename=d.get("filename", ""),
            raw_text=d.get("raw_text", ""),
            metadata=d.get("metadata") or {},
            content_hash=d.get("content_hash", ""),
            created_at=d.get("created_at", ""),
        )


def _generate_doc_id() -> str:
    return f"ing-{int(time.time() * 1000)}-{os.urandom(4).hex()}"


# --- Local file fallback ---
def _ingested_dir(session_id: str) -> str:
    return os.path.join(_file_store_dir(), _safe_session(session_id), "ingested")


def _ingested_list_path(session_id: str) -> str:
    return os.path.join(_ingested_dir(session_id), "meta.json")


def _ingested_doc_path(session_id: str, doc_id: str) -> str:
    return os.path.join(_ingested_dir(session_id), f"{_safe_id(doc_id)}.json")


def _ingested_local_list(session_id: str) -> list:
    if not session_id:
        return []
    try:
        path = _ingested_list_path(session_id)
        if not os.path.isfile(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _ingested_local_get(session_id: str, doc_id: str) -> NormalizedDocument | None:
    if not session_id or not doc_id:
        return None
    try:
        path = _ingested_doc_path(session_id, doc_id)
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return NormalizedDocument.from_dict(json.load(f))
    except Exception:
        return None


def _ingested_local_save(doc: NormalizedDocument) -> bool:
    if not doc.session_id or not doc.id:
        return False
    try:
        root = _ingested_dir(doc.session_id)
        os.makedirs(root, exist_ok=True)
        path = _ingested_doc_path(doc.session_id, doc.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc.to_dict(), f, ensure_ascii=False, indent=0)
        list_path = _ingested_list_path(doc.session_id)
        meta_list = _ingested_local_list(doc.session_id)
        meta_list = [m for m in meta_list if m.get("id") != doc.id]
        meta_list.append({
            "id": doc.id,
            "filename": doc.filename,
            "format": doc.format,
            "content_hash": doc.content_hash,
            "metadata": doc.metadata,
            "created_at": doc.created_at,
        })
        with open(list_path, "w", encoding="utf-8") as f:
            json.dump(meta_list, f, ensure_ascii=False, indent=0)
        return True
    except Exception:
        return False


def _find_by_content_hash(session_id: str, content_hash: str, ingestion_group: str | None = None) -> str | None:
    """Return existing doc id if this content_hash already stored in this session (optionally in this group)."""
    r = _get_redis()
    if r:
        try:
            raw = r.get(INGESTED_PREFIX + session_id + INGESTED_LIST_SUFFIX)
            if not raw:
                return None
            data = json.loads(raw) if isinstance(raw, str) else raw
            for m in data:
                if m.get("content_hash") != content_hash:
                    continue
                if ingestion_group is not None and (m.get("metadata") or {}).get("ingestion_group") != ingestion_group:
                    continue
                return m.get("id")
        except Exception:
            pass
        return None
    for m in _ingested_local_list(session_id):
        if m.get("content_hash") != content_hash:
            continue
        if ingestion_group is not None and (m.get("metadata") or {}).get("ingestion_group") != ingestion_group:
            continue
        return m.get("id")
    return None


def save_ingested_document(doc: NormalizedDocument) -> bool:
    """Persist one normalized document. Returns True on success."""
    if len((doc.raw_text or "").encode("utf-8")) > MAX_CONTENT_SIZE:
        return False
    r = _get_redis()
    if r:
        try:
            key_list = INGESTED_PREFIX + doc.session_id + INGESTED_LIST_SUFFIX
            key_doc = INGESTED_PREFIX + doc.session_id + ":" + doc.id
            raw_list = r.get(key_list)
            meta_list = json.loads(raw_list) if raw_list else []
            meta_list = [m for m in meta_list if m.get("id") != doc.id]
            meta_list.append({
                "id": doc.id,
                "filename": doc.filename,
                "format": doc.format,
                "content_hash": doc.content_hash,
                "metadata": doc.metadata,
                "created_at": doc.created_at,
            })
            r.set(key_list, json.dumps(meta_list))
            r.set(key_doc, json.dumps(doc.to_dict()))
            return True
        except Exception:
            return False
    return _ingested_local_save(doc)


def list_ingested_documents(session_id: str, ingestion_group: str | None = None) -> list[dict]:
    """Return list of ingested doc summaries. Optional ingestion_group filters to that group only."""
    if not session_id:
        return []
    r = _get_redis()
    if r:
        try:
            raw = r.get(INGESTED_PREFIX + session_id + INGESTED_LIST_SUFFIX)
            if not raw:
                return []
            data = json.loads(raw) if isinstance(raw, str) else raw
            if ingestion_group:
                data = [m for m in data if (m.get("metadata") or {}).get("ingestion_group") == ingestion_group]
            return data
        except Exception:
            return []
    data = _ingested_local_list(session_id)
    if ingestion_group:
        data = [m for m in data if (m.get("metadata") or {}).get("ingestion_group") == ingestion_group]
    return data


def get_ingested_document(session_id: str, doc_id: str) -> NormalizedDocument | None:
    """Return full normalized document or None."""
    if not session_id or not doc_id:
        return None
    r = _get_redis()
    if r:
        try:
            raw = r.get(INGESTED_PREFIX + session_id + ":" + doc_id)
            if not raw:
                return None
            return NormalizedDocument.from_dict(json.loads(raw))
        except Exception:
            return None
    return _ingested_local_get(session_id, doc_id)


def content_hash_exists_in_session(session_id: str, content_hash: str, ingestion_group: str | None = None) -> str | None:
    """If this content_hash is already stored in session (in this group), return existing doc id; else None."""
    return _find_by_content_hash(session_id, content_hash, ingestion_group)
