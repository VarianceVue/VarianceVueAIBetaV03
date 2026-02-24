"""
Stage 1: Ingestion & Normalization — NLP Document Intelligence Pipeline.
Extract text from PDF, DOCX, XLSX, TXT; normalize metadata; deduplicate by content hash;
output a single document store (raw text + metadata) for Stage 2.
"""
from schedule_agent_web.ingestion.pipeline import ingest_document
from schedule_agent_web.ingestion.doc_store import (
    list_ingested_documents,
    get_ingested_document,
    NormalizedDocument,
)

__all__ = [
    "ingest_document",
    "list_ingested_documents",
    "get_ingested_document",
    "NormalizedDocument",
]
