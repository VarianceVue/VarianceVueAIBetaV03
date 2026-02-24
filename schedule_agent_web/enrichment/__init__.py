"""
Stage 2: Preprocessing & Enrichment — NLP Document Intelligence Pipeline.
Cleaning, language detection, segmentation, structure, vocabulary normalization.
"""
from schedule_agent_web.enrichment.pipeline import enrich_document
from schedule_agent_web.enrichment.enriched_store import (
    EnrichedDocument,
    list_enriched_documents,
    get_enriched_document,
)

__all__ = [
    "enrich_document",
    "list_enriched_documents",
    "get_enriched_document",
    "EnrichedDocument",
]
