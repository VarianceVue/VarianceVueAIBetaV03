"""
Vector store for uploaded files: Qdrant (REST API via httpx) + embeddings.
Uses OpenAI if OPENAI_API_KEY is set; otherwise uses hash-based embeddings
(no torch/sentence-transformers needed — works on Python 3.14 ARM64).
Optional GraphRAG integration for hybrid retrieval.
"""
import hashlib
import math
import os
import re
import struct
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

COLLECTION_NAME = "vuelogic_docs"
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

HASH_EMBED_DIM = 384
_embedding_dim: Optional[int] = None

_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did will would "
    "shall should may might can could of in to for on with at by from as into "
    "through during before after above below between under and but or nor not "
    "so yet both either neither each every all any few more most other some such "
    "no only own same than too very just because if when while where how what "
    "which who whom whose this that these those it its i me my we us our you your "
    "he him his she her they them their".split()
)


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    if not text or not text.strip():
        return []
    chunks = []
    start = 0
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            break_at = max(
                text.rfind("\n", start, end + 1),
                text.rfind(". ", start, end + 1),
                text.rfind(" ", start, end + 1),
                end,
            )
            end = break_at + 1 if break_at > start else end
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap if overlap < end - start else end
    return chunks


def _tokenize(text: str) -> list[str]:
    """Word tokenizer: lowercase, keeps decimal numbers (3.1, 3.2), removes stop words."""
    words = re.findall(r"[a-z0-9]+(?:\.[0-9]+)*", text.lower())
    return [w for w in words if w not in _STOP_WORDS and len(w) > 1]


def _hash_embed(text: str, dim: int = HASH_EMBED_DIM) -> list[float]:
    """
    Hash-based embedding: feature hashing / random projection.
    Each token contributes to multiple vector positions via different hash seeds.
    Cosine similarity on these vectors approximates bag-of-words similarity.
    """
    vec = [0.0] * dim
    tokens = _tokenize(text)
    if not tokens:
        return vec
    n_hashes = 4
    for token in tokens:
        for seed in range(n_hashes):
            h = hashlib.md5(f"{seed}:{token}".encode()).digest()
            pos = struct.unpack("<H", h[:2])[0] % dim
            sign = 1.0 if h[2] & 1 else -1.0
            vec[pos] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Get embeddings: OpenAI if OPENAI_API_KEY set, else hash-based fallback.
    """
    global _embedding_dim
    if not texts:
        return []
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY_FILE")
    if key and Path(key).exists():
        key = Path(key).read_text().strip()
    if key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            resp = client.embeddings.create(input=texts, model=model)
            vecs = [e.embedding for e in resp.data]
            _embedding_dim = len(vecs[0]) if vecs else 1536
            return vecs
        except Exception:
            pass
    _embedding_dim = HASH_EMBED_DIM
    return [_hash_embed(t) for t in texts]


# --------------- Qdrant REST API helpers ---------------

def _qdrant_base_url() -> Optional[str]:
    url = os.environ.get("QDRANT_URL") or os.environ.get("QDRANT_HOST")
    if not url:
        return None
    if "://" not in url:
        port = os.environ.get("QDRANT_PORT", "6333")
        url = f"http://{url}:{port}"
    return url.rstrip("/")


def _qdrant_headers() -> dict[str, str]:
    api_key = os.environ.get("QDRANT_API_KEY")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["api-key"] = api_key
    return headers


def _qdrant_request(method: str, path: str, json_body: dict | None = None, timeout: float = 30) -> dict | None:
    """Make a REST request to Qdrant. Returns parsed JSON or None on failure."""
    base = _qdrant_base_url()
    if not base:
        return None
    url = f"{base}{path}"
    try:
        r = httpx.request(method, url, json=json_body, headers=_qdrant_headers(), timeout=timeout)
        if r.status_code < 300:
            return r.json()
        return None
    except Exception:
        return None


def is_qdrant_available() -> bool:
    """Check if Qdrant is configured and reachable."""
    base = _qdrant_base_url()
    if not base:
        return False
    try:
        r = httpx.get(f"{base}/collections", headers=_qdrant_headers(), timeout=10)
        return r.status_code < 300
    except Exception:
        return False


def _get_embedding_dim() -> int:
    global _embedding_dim
    if _embedding_dim is not None:
        return _embedding_dim
    _get_embeddings(["probe"])
    return _embedding_dim or HASH_EMBED_DIM


def ensure_collection() -> bool:
    """Create collection if it does not exist; also ensure payload indexes."""
    base = _qdrant_base_url()
    if not base:
        return False
    dim = _get_embedding_dim()
    try:
        r = httpx.get(
            f"{base}/collections/{COLLECTION_NAME}",
            headers=_qdrant_headers(),
            timeout=10,
        )
        if r.status_code != 200:
            body = {
                "vectors": {
                    "size": dim,
                    "distance": "Cosine",
                }
            }
            r2 = httpx.put(
                f"{base}/collections/{COLLECTION_NAME}",
                json=body,
                headers=_qdrant_headers(),
                timeout=15,
            )
            if r2.status_code >= 300:
                return False
        for field in ("session_id", "filename", "ingestion_group"):
            _qdrant_request("PUT", f"/collections/{COLLECTION_NAME}/index", {
                "field_name": field,
                "field_schema": "keyword",
            })
        return True
    except Exception:
        return False


def _normalize_pdf_text(text: str) -> str:
    """Fix common PDF extraction artifacts like split section numbers (3. 1 -> 3.1)."""
    text = re.sub(r"(\d+)\.\s+(\d+)", r"\1.\2", text)
    text = re.sub(r"(\d+\.\d+)\.\s+(\d+)", r"\1.\2", text)
    return text


_pdf_text_cache: dict[int, str] = {}


def _extract_text_from_pdf_bytes(raw: str) -> str:
    """If content is base64-encoded PDF, decode and extract text via PyPDF2. Caches by content hash."""
    import base64 as _b64
    if not raw or raw.startswith("%T") or raw.startswith("ERMHDR"):
        return raw

    cache_key = hash(raw[:500])
    if cache_key in _pdf_text_cache:
        return _pdf_text_cache[cache_key]

    try:
        decoded = _b64.b64decode(raw)
    except Exception:
        return raw
    if not decoded[:5].startswith(b"%PDF"):
        return raw
    try:
        import io
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(decoded))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(_normalize_pdf_text(text))
        result = "\n\n".join(pages) if pages else raw
        _pdf_text_cache[cache_key] = result
        return result
    except Exception:
        return raw


def index_file(session_id: str, filename: str, content: str, ingestion_group: str | None = None) -> bool:
    """Chunk file content, embed, upsert to Qdrant."""
    if not _qdrant_base_url():
        return False
    if not ensure_collection():
        return False
    if filename.lower().endswith(".pdf"):
        content = _extract_text_from_pdf_bytes(content)
    chunks = _chunk_text(content)
    if not chunks:
        return True
    vectors = _get_embeddings(chunks)
    if len(vectors) != len(chunks):
        return False
    points = []
    for i, vec in enumerate(vectors):
        payload = {
            "session_id": session_id,
            "filename": filename,
            "chunk_index": i,
            "text": chunks[i],
        }
        if ingestion_group:
            payload["ingestion_group"] = ingestion_group
        points.append({"id": str(uuid.uuid4()), "vector": vec, "payload": payload})
    batch_size = 64
    for start in range(0, len(points), batch_size):
        batch = points[start : start + batch_size]
        result = _qdrant_request("PUT", f"/collections/{COLLECTION_NAME}/points", {"points": batch}, timeout=60)
        if result is None:
            return False
    return True


def count_file_vectors(session_id: str, filename: str) -> int:
    """Return number of vector points stored in Qdrant for this session_id + filename."""
    body = {
        "filter": {
            "must": [
                {"key": "session_id", "match": {"value": session_id}},
                {"key": "filename", "match": {"value": filename}},
            ]
        },
        "exact": True,
    }
    result = _qdrant_request("POST", f"/collections/{COLLECTION_NAME}/points/count", body, timeout=15)
    if result is None:
        return -1  # Qdrant unreachable
    return result.get("result", {}).get("count", 0)


def delete_file_vectors(session_id: str, filename: str) -> bool:
    """Remove all vectors for this session_id + filename."""
    body = {
        "filter": {
            "must": [
                {"key": "session_id", "match": {"value": session_id}},
                {"key": "filename", "match": {"value": filename}},
            ]
        }
    }
    result = _qdrant_request("POST", f"/collections/{COLLECTION_NAME}/points/delete", body, timeout=30)
    return result is not None


def index_conversation_turn(session_id: str, user_message: str, assistant_reply: str) -> bool:
    """Vectorize one chat turn and upsert to Qdrant."""
    if not _qdrant_base_url():
        return False
    if not ensure_collection():
        return False
    combined = f"User: {user_message}\n\nAssistant: {assistant_reply}".strip()
    if not combined:
        return True
    chunks = _chunk_text(combined)
    if not chunks:
        return True
    vectors = _get_embeddings(chunks)
    if len(vectors) != len(chunks):
        return False
    turn_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    points = []
    for i, vec in enumerate(vectors):
        points.append({
            "id": str(uuid.uuid4()),
            "vector": vec,
            "payload": {
                "session_id": session_id,
                "filename": "conversation",
                "source": "conversation",
                "turn_id": turn_id,
                "chunk_index": i,
                "text": chunks[i],
                "created_at": created_at,
            },
        })
    result = _qdrant_request("PUT", f"/collections/{COLLECTION_NAME}/points", {"points": points}, timeout=30)
    return result is not None


def search(
    session_id: Optional[str],
    query: str,
    top_k: int = 6,
    ingestion_group: Optional[str] = None,
) -> list[dict]:
    """Embed query, search Qdrant, return list of {text, filename, score, ingestion_group?}."""
    if not _qdrant_base_url():
        return []
    vecs = _get_embeddings([query])
    if not vecs:
        return []
    must: list[dict] = []
    if session_id:
        must.append({"key": "session_id", "match": {"value": session_id}})
    if ingestion_group:
        must.append({"key": "ingestion_group", "match": {"value": ingestion_group}})
    body: dict = {
        "vector": vecs[0],
        "limit": top_k,
        "with_payload": True,
    }
    if must:
        body["filter"] = {"must": must}
    result = _qdrant_request("POST", f"/collections/{COLLECTION_NAME}/points/search", body, timeout=15)
    if not result:
        return []
    hits = result.get("result", [])
    return [
        {
            "text": (h.get("payload") or {}).get("text", ""),
            "filename": (h.get("payload") or {}).get("filename", ""),
            "score": h.get("score", 0.0),
            "ingestion_group": (h.get("payload") or {}).get("ingestion_group"),
        }
        for h in hits
    ]


# --- File-based fallback search (when Qdrant is unavailable) ---

_fallback_cache: dict[str, list[tuple[str, list[str]]]] = {}
_fallback_cache_ts: dict[str, float] = {}
_FALLBACK_CACHE_TTL = 300  # 5 minutes

def _get_fallback_chunks(session_id: str) -> list[tuple[str, list[str]]]:
    """Return cached list of (filename, [chunks]) for a session. Extracts PDF text once."""
    import time
    now = time.time()
    if session_id in _fallback_cache and (now - _fallback_cache_ts.get(session_id, 0)) < _FALLBACK_CACHE_TTL:
        return _fallback_cache[session_id]

    try:
        from schedule_agent_web.store import get_files, get_file_content
    except ImportError:
        return []

    files = get_files(session_id)
    result: list[tuple[str, list[str]]] = []
    for f in files:
        fname = f.get("filename", "")
        if fname == "conversation" or fname.startswith("_"):
            continue
        content = get_file_content(session_id, fname)
        if not content:
            continue
        if fname.lower().endswith(".pdf"):
            content = _extract_text_from_pdf_bytes(content)
        if not content or len(content) < 20:
            continue
        chunks = _chunk_text(content, chunk_size=1500, overlap=200)
        if chunks:
            result.append((fname, chunks))

    _fallback_cache[session_id] = result
    _fallback_cache_ts[session_id] = now
    return result


def _file_search_fallback(session_id: str, query: str, top_k: int = 6) -> list[dict]:
    """Keyword-based search over stored file contents when Qdrant is not available.

    Uses token overlap scoring boosted by:
    - Exact phrase / substring matches in the chunk text
    - Filename relevance (if query mentions words present in the filename)
    """
    all_chunks = _get_fallback_chunks(session_id)
    if not all_chunks:
        return []

    query_lower = query.lower()
    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return []

    phrase_fragments = re.findall(r"section\s+\d+(?:\.\d+)*", query_lower)
    phrase_fragments += re.findall(r"\d+\.\d+(?:\.\d+)*", query_lower)

    fname_tokens = set()
    for kw in ("narrative", "baseline", "update", "spec", "technical", "provisions", "xer", "schedule"):
        if kw in query_lower:
            fname_tokens.add(kw)

    scored: list[tuple[float, str, str]] = []
    for fname, chunks in all_chunks:
        fname_lower = fname.lower()
        fname_boost = 1.0
        if fname_tokens:
            matches = sum(1 for t in fname_tokens if t in fname_lower)
            fname_boost = 1.0 + 0.3 * matches

        for chunk in chunks:
            chunk_lower = chunk.lower()
            chunk_tokens = set(_tokenize(chunk))
            if not chunk_tokens:
                continue
            overlap = len(query_tokens & chunk_tokens)
            if overlap == 0:
                continue
            score = overlap / max(len(query_tokens), 1)

            phrase_bonus = 0.0
            for frag in phrase_fragments:
                if frag in chunk_lower:
                    phrase_bonus += 0.5
            score = (score + phrase_bonus) * fname_boost
            scored.append((score, fname, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {"text": chunk, "filename": fname, "score": score, "ingestion_group": None}
        for score, fname, chunk in scored[:top_k]
    ]


# --- Optional GraphRAG ---
def _graphrag_project_path() -> Optional[Path]:
    path = os.environ.get("GRAPHRAG_PROJECT_DIR")
    if path:
        return Path(path)
    return Path(__file__).resolve().parent.parent / "graphrag_project"


def is_graphrag_available() -> bool:
    try:
        from graphrag.config.load_config import load_config
        path = _graphrag_project_path()
        if not path.exists():
            return False
        output = path / "output"
        if not (output / "entities.parquet").exists():
            return False
        load_config(path)
        return True
    except Exception:
        return False


def graphrag_search(query: str, top_k: int = 3) -> list[str]:
    import asyncio
    try:
        import graphrag.api as api
        from graphrag.config.load_config import load_config
        import pandas as pd
        path = _graphrag_project_path()
        if not path.exists():
            return []
        config = load_config(path)
        output = path / "output"
        if not (output / "entities.parquet").exists():
            return []
        entities = pd.read_parquet(output / "entities.parquet")
        communities = pd.read_parquet(output / "communities.parquet")
        community_reports = pd.read_parquet(output / "community_reports.parquet")

        async def _search():
            response, context = await api.global_search(
                config=config,
                entities=entities,
                communities=communities,
                community_reports=community_reports,
                community_level=2,
                dynamic_community_selection=False,
                response_type="Multiple Paragraphs",
                query=query,
            )
            return response if isinstance(response, str) else str(getattr(response, "answer", response))

        answer = asyncio.run(_search())
        return [answer] if answer else []
    except Exception:
        return []
