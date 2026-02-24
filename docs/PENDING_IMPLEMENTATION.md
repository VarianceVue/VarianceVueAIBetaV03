# Pending implementation — running list

Items to implement later for the NLP Document Intelligence Pipeline and ECEPCS. Update this file as things get done or new items are added.

---

## Stage 1 — deferred / later

| Item | Notes |
|------|--------|
| **OCR for scanned PDFs/images** | Tesseract (basic) or Azure Document Intelligence / AWS Textract for complex layouts. Use when extracted text is empty or very short. |
| **Binary .xls (old Excel)** | Currently .xls is treated as plain text. Add `xlrd` or similar to parse real .xls if needed. |
| **Email (.eml) as dedicated format** | Parse .eml for body + attachments; extract text and metadata. |
| **HTML as dedicated extractor** | Currently HTML is decoded as text. Add proper HTML parsing (e.g. BeautifulSoup) to strip tags and get main content. |
| **Source connectors** | SharePoint, Procore, Aconex, watch folder, etc. — beyond upload API. |
| **Global deduplication** | Stage 1 dedup is per-session only. Add optional global content_hash index (e.g. Redis set) to skip duplicates across sessions. |

---

## Stage 2 — Preprocessing & enrichment (implemented)

| Item | Status |
|------|--------|
| Text cleaning | Done: header/footer/boilerplate removal, whitespace normalization (`enrichment/cleaning.py`). |
| Language detection | Done: langdetect; store `lang` in enriched doc (`enrichment/language.py`). |
| Sentence/token segmentation | Done: NLTK sentence + word tokenizer (`enrichment/segmentation.py`). |
| Document structure | Done: regex-based sections/headings (numbered, markdown, ALL CAPS) (`enrichment/structure.py`). |
| Domain vocabulary normalization | Done: JSON mapping table (`vocabulary_map.json`), word-boundary replace (`enrichment/vocabulary.py`). |
| *Optional later* | Unstructured/LlamaParse for deeper structure; embedding-based synonym suggestions. |

---

## Stage 3 — Core NLP (implemented)

| Item | Status |
|------|--------|
| Named Entity Recognition (NER) | Done: regex (WBS, DRAWING, PROJECT_CODE, ACTIVITY_ID) + optional spaCy `en_core_web_sm` (PER/ORG/LOC) (`nlp/ner.py`). Run `python -m spacy download en_core_web_sm`. |
| Classification | Done: LLM-based doc type + risk_signal + change_signal + confidence (`nlp/classification.py`). |
| Relation extraction | Done: LLM (subject, relation, object) triples (`nlp/relations.py`). |
| Temporal extraction | Done: dateparser + regex for ISO/numeric/month dates (`nlp/temporal.py`). |
| Summarization | Done: LLM 2–4 sentence summary (`nlp/summarization.py`). |
| *Optional later* | Fine-tune NER for project-controls labels; SetFit/BERT for classification; HeidelTime for relative dates. |

---

## Stage 4 — Intelligence layer (implemented)

| Item | Status |
|------|--------|
| Semantic search | Done: GET `/api/documents/search` (Qdrant); Stage 1 ingest indexes to vector store. |
| RAG Q&A | Done: Chat uses vector search; response includes sources for citation. “cite source doc” where needed. |
| Anomaly / signal detection | Done: Rules + optional LLM; POST `/api/signals/scan`, GET `/api/signals`. |
| Knowledge graph | Done: Stage 3 relations saved as edges; GET /api/graph/related. Optional: “everything connected to CO-042”. |
| Trend analytics | Done: GET `/api/analytics/trends`; Redis/file store. |
| *Optional later* | Neo4j; Metabase/Grafana dashboards. |

---

## Pending from Stages 1, 2, 3, 4, 5 (running list)

| Stage | Item | Notes |
|-------|------|--------|
| **1** | OCR for scanned PDFs/images | Tesseract (basic) or Azure Document Intelligence / AWS Textract when extracted text is empty or very short. |
| **1** | Binary .xls (old Excel) | Add xlrd or similar to parse real .xls; currently .xls is treated as plain text. |
| **1** | Email (.eml) as dedicated format | Parse .eml for body + attachments; extract text and metadata. |
| **1** | HTML as dedicated extractor | Proper HTML parsing (e.g. BeautifulSoup) to strip tags and get main content; currently decoded as text only. |
| **1** | Source connectors | SharePoint, Procore, Aconex, watch folder, etc. — beyond upload API. |
| **1** | Global deduplication | Optional global content_hash index (e.g. Redis set) to skip duplicates across sessions; currently per-session only. |
| **2** | Unstructured.io or LlamaParse | Deeper document structure (sections, tables, lists) instead of regex-only. |
| **2** | Embedding-based synonym suggestions | Use sentence-transformers similarity to suggest/add terms to vocabulary map. |
| **3** | Fine-tune NER for project-controls labels | Train spaCy/Prodigy on project codes, WBS, drawing refs, activity IDs. |
| **3** | SetFit or BERT for classification | Fast, cheap doc/section classification as alternative or complement to LLM. |
| **3** | HeidelTime or LLM for relative dates | Resolve "last month", "Q3", "end of year" to absolute dates in temporal extraction. |
| **4** | Dedicated /api/documents/qa endpoint | Optional standalone Q&A over docs (in addition to chat RAG). |
| **4** | Neo4j (or Postgres graph) for knowledge graph | Full graph DB for traversal and "everything connected to X" queries. |
| **4** | Metabase or Grafana for trend analytics | Dashboards over event counts and NLP outputs. |
| **5** | Celery/Dramatiq + email for alerts | Async alert jobs; SendGrid/SES for email (webhook is sync). |
| **5** | Postgres for audit trail | Optional upgrade from Redis/file for audit (traceable to source). |

---

## Stage 5 — Delivery & integration (implemented)

| Item | Status |
|------|--------|
| Dashboard | Done: GET `/api/dashboard` (signals_count, recent_signals, nlp_summaries, ingested_count, trends). |
| Alerts | Done: Webhook (ALERT_WEBHOOK_URL or SLACK_WEBHOOK_URL) on risk/dispute signals from `/api/signals/scan`. |
| Report drafting | Done: POST `/api/reports/draft` (session_id, title, template); LLM + signals + NLP summaries. |
| API routes | Done: `/api/documents/qa`, `/api/dashboard`, `/api/reports/draft`, `/api/audit/trail`. |
| Audit trail | Done: Redis/file; append on chat answer, signal, report; GET `/api/audit/trail`. |
| *Optional later* | Celery/Dramatiq for async alerts; email (SendGrid/SES); Postgres for audit. |

---

## Other / general

| Item | Notes |
|------|--------|
| Unstructured.io (or LangChain loaders) | Optional replacement or complement to current PDF/DOCX/XLSX extractors for messy docs. |
| Async ingest jobs | Celery or Dramatiq for large batches / connector sync. |

---

*Last updated: when Stage 1 was completed and this list was created.*
