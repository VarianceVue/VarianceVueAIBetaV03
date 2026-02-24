"""
Stage 1 pipeline: extract text → metadata → content hash → dedup check → save to normalized store.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from schedule_agent_web.ingestion.extractors import extract_text, detect_format
from schedule_agent_web.ingestion.metadata import extract_metadata
from schedule_agent_web.ingestion.dedup import content_hash
from schedule_agent_web.ingestion.doc_store import (
    NormalizedDocument,
    save_ingested_document,
    content_hash_exists_in_session,
    _generate_doc_id,
)


# Ingestion groups for the ingestion page (contract docs, sample schedule, site progress)
INGESTION_GROUP_CONTRACT_SPECS = "contract_specs"
INGESTION_GROUP_SAMPLE_SCHEDULE = "sample_schedule"
INGESTION_GROUP_SITE_PROGRESS = "site_progress"
INGESTION_GROUPS = [
    {"id": INGESTION_GROUP_CONTRACT_SPECS, "label": "Contract documents & specifications", "accepted_formats": "PDF, DOCX, XLSX, XER, TXT, CSV; site images (JPEG, PNG, GIF, WebP) — described via Claude vision if ANTHROPIC_API_KEY set"},
    {"id": INGESTION_GROUP_SAMPLE_SCHEDULE, "label": "Sample schedule (reference for building new schedule)", "accepted_formats": "Excel (.xlsx), XER (Primavera P6)"},
    {"id": INGESTION_GROUP_SITE_PROGRESS, "label": "Site pictures & daily logs", "accepted_formats": "Site photos: JPEG, PNG, GIF, WebP (Claude vision); Daily logs: PDF, TXT, DOCX"},
]


def ingest_document(
    session_id: str,
    filename: str,
    bytes_in: bytes,
    source: str = "upload",
    ingestion_group: str | None = None,
) -> dict[str, Any]:
    """
    Run Stage 1: extract text, metadata, hash; dedup (per group); save.
    ingestion_group: "contract_specs" | "sample_schedule" for grouping on ingestion page.
    Returns:
      - status: "created" | "duplicate"
      - doc_id: id of the (new or existing) document
      - format: detected format
      - content_hash: SHA-256 of normalized text
      - ingestion_group: group the doc was stored under
      - duplicate_of: if status is duplicate, the existing doc id
    """
    if not session_id or not filename:
        return {"status": "error", "error": "session_id and filename required"}

    # Normalize group (allow only known groups)
    group = (ingestion_group or "").strip() or INGESTION_GROUP_CONTRACT_SPECS
    if group not in (INGESTION_GROUP_CONTRACT_SPECS, INGESTION_GROUP_SAMPLE_SCHEDULE, INGESTION_GROUP_SITE_PROGRESS):
        group = INGESTION_GROUP_CONTRACT_SPECS

    # Extract
    raw_text, fmt = extract_text(bytes_in, filename)
    size_bytes = len(bytes_in)

    # Metadata (include ingestion_group so list/search can filter)
    meta = extract_metadata(filename, size_bytes, fmt, source=source, raw_text_preview=raw_text[:500])
    meta["ingestion_group"] = group

    # Hash and dedup (per group: same content in different groups = separate docs)
    ch = content_hash(raw_text)
    existing_id = content_hash_exists_in_session(session_id, ch, ingestion_group=group)
    if existing_id:
        return {
            "status": "duplicate",
            "doc_id": existing_id,
            "format": fmt,
            "content_hash": ch,
            "ingestion_group": group,
            "duplicate_of": existing_id,
        }

    # Create and save
    doc_id = _generate_doc_id()
    created_at = datetime.utcnow().isoformat() + "Z"
    doc = NormalizedDocument(
        id=doc_id,
        session_id=session_id,
        source=source,
        format=fmt,
        filename=filename,
        raw_text=raw_text,
        metadata=meta,
        content_hash=ch,
        created_at=created_at,
    )
    ok = save_ingested_document(doc)
    if not ok:
        return {"status": "error", "error": "Failed to save document"}

    return {
        "status": "created",
        "doc_id": doc_id,
        "format": fmt,
        "content_hash": ch,
        "ingestion_group": group,
        "metadata": meta,
    }
