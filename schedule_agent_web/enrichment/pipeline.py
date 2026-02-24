"""
Stage 2 pipeline: clean → language → segment → structure → vocabulary → save enriched store.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from schedule_agent_web.enrichment.cleaning import clean_text
from schedule_agent_web.enrichment.language import detect_language
from schedule_agent_web.enrichment.segmentation import segment_sentences
from schedule_agent_web.enrichment.structure import detect_structure
from schedule_agent_web.enrichment.vocabulary import normalize_text_with_vocabulary
from schedule_agent_web.enrichment.enriched_store import EnrichedDocument, save_enriched_document


def enrich_document(session_id: str, doc_id: str, raw_text: str) -> dict[str, Any]:
    """
    Run Stage 2 on raw text (from Stage 1 doc). Saves to enriched store.
    Returns { status, doc_id, lang, sentence_count, structure_count } or { status: "error", error: "..." }.
    """
    if not session_id or not doc_id:
        return {"status": "error", "error": "session_id and doc_id required"}
    if raw_text is None:
        raw_text = ""
    cleaned = clean_text(raw_text)
    lang = detect_language(cleaned)
    sentences = segment_sentences(cleaned)
    structure = detect_structure(cleaned)
    normalized_text, term_replacements = normalize_text_with_vocabulary(cleaned)
    created_at = datetime.utcnow().isoformat() + "Z"
    enriched = EnrichedDocument(
        doc_id=doc_id,
        session_id=session_id,
        cleaned_text=cleaned,
        lang=lang,
        sentences=sentences,
        structure=structure,
        normalized_text=normalized_text,
        term_replacements=term_replacements,
        created_at=created_at,
    )
    ok = save_enriched_document(enriched)
    if not ok:
        return {"status": "error", "error": "Failed to save enriched document"}
    return {
        "status": "ok",
        "doc_id": doc_id,
        "lang": lang,
        "sentence_count": len(sentences),
        "structure_count": len(structure),
        "term_replacements_count": len(term_replacements),
        "created_at": created_at,
    }
