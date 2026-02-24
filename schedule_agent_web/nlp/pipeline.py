"""
Stage 3 pipeline: NER → classification → relations → temporal → summarization → save.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from schedule_agent_web.nlp.ner import extract_entities
from schedule_agent_web.nlp.classification import classify_document
from schedule_agent_web.nlp.relations import extract_relations
from schedule_agent_web.nlp.temporal import extract_dates
from schedule_agent_web.nlp.summarization import summarize_text
from schedule_agent_web.nlp.nlp_store import NLPDocument, save_nlp_document


def process_document(session_id: str, doc_id: str, text: str, use_spacy_ner: bool = False) -> dict[str, Any]:
    """
    Run Stage 3 NLP on text (from Stage 1 or Stage 2). Saves to nlp store.
    Returns { status, doc_id, entity_count, relation_count, ... } or { status: "error", error: "..." }.
    """
    if not session_id or not doc_id:
        return {"status": "error", "error": "session_id and doc_id required"}
    text = text or ""
    entities = extract_entities(text, use_spacy=use_spacy_ner)
    classification = classify_document(text)
    relations = extract_relations(text)
    dates = extract_dates(text)
    summary = summarize_text(text)
    created_at = datetime.utcnow().isoformat() + "Z"
    nlp_doc = NLPDocument(
        doc_id=doc_id,
        session_id=session_id,
        entities=entities,
        relations=relations,
        classification=classification,
        dates=dates,
        summary=summary,
        created_at=created_at,
    )
    ok = save_nlp_document(nlp_doc)
    if not ok:
        return {"status": "error", "error": "Failed to save NLP document"}
    return {
        "status": "ok",
        "doc_id": doc_id,
        "entity_count": len(entities),
        "relation_count": len(relations),
        "dates_count": len(dates),
        "classification": classification,
        "summary_preview": (summary or "")[:200],
        "created_at": created_at,
    }
