# NLP Document Intelligence Pipeline — Tech Stack Advice

Recommendations aligned with the plan in *NLP Doc Intel Pipeline.docx* and with your existing ECEPCS/VueLogic stack (FastAPI, Qdrant, Redis, Claude/OpenAI).

---

## Stage 1: Ingestion & Normalization

| Need | Recommended stack | Notes |
|------|-------------------|--------|
| **Format diversity** (PDF, DOCX, XLSX, images, email, HTML) | **Unstructured.io** (Python) or **LangChain document loaders** | Unstructured is purpose-built for messy enterprise docs; you already use pypdf/pymupdf for PDF. Add `python-docx`, `openpyxl` for DOCX/XLSX. |
| **Source connectors** (SharePoint, Procore, Aconex, email, drives) | **Custom FastAPI ingest endpoints** + **Celery** or **Dramatiq** for async jobs; optional **Apache Airflow** for orchestration | Start with “upload + watch folder” and REST APIs; add connectors incrementally. |
| **OCR** (scanned docs, forms, drawings) | **Tesseract** (free) for basic; **Azure Document Intelligence** or **AWS Textract** for tables/forms | Use Tesseract first; add cloud OCR when you need higher accuracy (cost vs. quality). |
| **Metadata extraction** | **Custom rules + regex** or **LLM** (Claude/GPT) for “document type, author, date” from first page or filename | Store in your existing file store + Redis or Postgres. |
| **Deduplication** | **Content hash** (e.g. SHA-256 of normalized text) in DB; **minhash/LSH** if you need fuzzy dupes | Store hashes in Redis or Postgres; skip re-processing duplicates. |
| **Output store** | **PostgreSQL** (e.g. `documents` table: id, session_id, source, format, raw_text, metadata JSON, content_hash) or **existing file_store + metadata in Redis/Postgres** | Keeps raw text + metadata in one place for Stage 2. |

**Stack summary (Stage 1):** Python 3.11+, FastAPI, Unstructured.io (or LangChain loaders), pypdf/pymupdf, python-docx, openpyxl, Tesseract (optional Azure/AWS OCR), Redis or Postgres for metadata/dedup, optional Celery/Dramatiq for queues.

---

## Stage 2: Preprocessing & Enrichment

| Need | Recommended stack | Notes |
|------|-------------------|--------|
| **Text cleaning** | **Unstructured** (already does a lot), **regex**, custom **header/footer/boilerplate** removal | You can add a small “clean” step after Unstructured. |
| **Language detection** | **langdetect** or **fastText** (Python) | One call per document; store `lang` in metadata. |
| **Sentence/token segmentation** | **spaCy** or **NLTK** | spaCy gives you tokens + sentences + POS; use for NER later. |
| **Document structure** (sections, headings, tables, lists) | **Unstructured** (outputs elements with types); **LlamaParse** or **Docling** if you need deeper structure | Unstructured is a strong default; you already have “chunk by section” potential. |
| **Domain vocabulary normalization** | **Custom mapping table** (PCO / potential change order / pending change → canonical) + optional **embedding similarity** (sentence-transformers) to suggest synonyms | Start with a CSV/JSON map; expand with embeddings later. |

**Stack summary (Stage 2):** Unstructured.io, spaCy (or NLTK), langdetect, custom normalization table; output = cleaned, segmented text + structure tags, stored per document.

---

## Stage 3: Core NLP Processing

| Need | Recommended stack | Notes |
|------|-------------------|--------|
| **Named Entity Recognition (NER)** | **spaCy** (transformer pipeline, e.g. `en_core_web_trf`) + **fine-tuning** on your labels (project codes, WBS, drawing refs, etc.) with **Prodigy** or **spaCy’s training API** | Start with off-the-shelf NER; add project-controls entities via fine-tuning. |
| **Classification** (doc type, sentiment, risk/change signals) | **Transformers** (Hugging Face): **BERT/DeBERTa** or **setfit** for small labels; or **LLM** (Claude/GPT) with few-shot prompts | Use SetFit or a small BERT for fast, cheap classification; use LLM when you need flexibility. |
| **Relation extraction** | **OpenAI/Claude** with structured prompts (“extract relations: subject, object, relation type”) or **triple extraction** (e.g. **OpenIE**, **ReBEL**) | LLM is practical for “Contractor X claims delay due to Y”; store as (subject, relation, object) in DB or graph. |
| **Temporal extraction** | **HeidelTime**, **dateparser**, or **LLM** for “last month” → absolute date | Combine rule-based + LLM for schedule-impact phrases. |
| **Summarization** | **Extractive:** **sentence-transformers** (embed, rank sentences). **Abstractive:** **Claude/GPT** or **BART/T5** (Hugging Face) | You already use LLM for chat; reuse for summaries with “summarize in 2 sentences” prompts. |

**Stack summary (Stage 3):** spaCy (NER + tokens), Hugging Face Transformers (classification, optional summarization), Claude/OpenAI (relations, temporal, abstractive summary); output = entities, relations, classes, dates, summaries per doc/section.

---

## Stage 4: Intelligence Layer

| Need | Recommended stack | Notes |
|------|-------------------|--------|
| **Semantic search** | **Qdrant** (you have it) + **OpenAI embeddings** or **sentence-transformers** (e.g. all-MiniLM-L6-v2) | Same as current VueLogic RAG: chunk → embed → Qdrant; filter by project/session. |
| **RAG Q&A** | **FastAPI + Claude/OpenAI** (you have this); **LangChain** or **LlamaIndex** optional for chains and tooling | Your existing `/api/chat` + vector search is the core; add “cite source doc” in the prompt. |
| **Anomaly / signal detection** | **Rules** (keywords + NER) + **LLM** (“does this passage indicate risk/claim/dispute?”); store signals in **Redis** or **Postgres** with doc_id + passage | Batch new docs through classifier + LLM; write results to a `signals` table. |
| **Knowledge graph** | **Neo4j** (or **Neptune**) for full graph; or **Postgres** (nodes + edges tables) + **recursive CTEs** for “everything connected to CO-042” | Start with Postgres if you want one DB; add Neo4j when traversal and graph queries become central. |
| **Trend analytics** | **Postgres** (or **ClickHouse**) with time-bucketed aggregates on NLP outputs (e.g. “count risk signals per week”); **Metabase** or **Grafana** for dashboards | Store events (doc_id, type, date, project); aggregate in SQL or a small analytics service. |

**Stack summary (Stage 4):** Qdrant + OpenAI/sentence-transformers (already in place), FastAPI + Claude/OpenAI for RAG, Postgres (or Redis) for signals and graph edges, optional Neo4j, optional Metabase/Grafana.

---

## Stage 5: Delivery & Integration

| Need | Recommended stack | Notes |
|------|-------------------|--------|
| **Dashboard** | **VueLogic UI** (React) or **Streamlit** for internal tools; embed “NLP insights” widgets (signals, summaries, links to source docs) | Reuse your existing dashboard and add cards/sections that call NLP APIs. |
| **Alerts** | **Celery** or **Dramatiq** + **email** (SendGrid/SES) or **Slack/Teams** webhooks | When pipeline writes “high-priority signal”, enqueue a task to send alert. |
| **Report drafting** | **LLM** (Claude/GPT) with template + retrieved chunks (RAG) and structured NLP outputs (entities, risks, changes) | Same pattern as “extract activities”: prompt + context → structured or narrative output. |
| **API layer** | **FastAPI** (you already have it); add routes e.g. `/api/documents/search`, `/api/documents/qa`, `/api/signals`, `/api/graph/related` | Keep REST + optional WebSocket for live updates. |
| **Audit trail** | **Postgres**: `nlp_outputs` (id, doc_id, passage_id, output_type, payload, model, created_at); link every answer and signal to doc + passage | Required for “traceable back to source”; store in same DB as documents. |

**Stack summary (Stage 5):** FastAPI, existing VueLogic front end, Celery/Dramatiq + email/Slack for alerts, Postgres for audit and reporting inputs.

---

## End-to-end stack (concise)

- **Runtime:** Python 3.11+
- **API / app:** FastAPI (existing)
- **Documents:** Unstructured.io (+ pypdf, pymupdf, python-docx, openpyxl); Tesseract or Azure/AWS OCR
- **Preprocessing:** spaCy, langdetect, custom normalization
- **NLP:** spaCy (NER), Hugging Face (classification/summarization), Claude/OpenAI (relations, temporal, summaries)
- **Vectors & RAG:** Qdrant, OpenAI or sentence-transformers (existing)
- **Storage:** Postgres (documents, metadata, signals, graph edges, audit); Redis (cache, queues, sessions)
- **Queues / jobs:** Celery or Dramatiq (ingest, batch NLP, alerts)
- **Front end:** VueLogic (React) + optional Streamlit for ops
- **Optional:** Neo4j (graph), Airflow (orchestration), Metabase/Grafana (analytics)

---

## Fit with your current ECEPCS setup

- You already have **FastAPI**, **Qdrant**, **Redis**, **file store**, **Claude/OpenAI** chat and RAG. The pipeline extends this with:
  - **Structured ingest** (Stage 1) and **preprocessing** (Stage 2) before chunks go to Qdrant.
  - **Explicit NER/classification/signals** (Stage 3) and **signals/graph/trends** (Stage 4) on top of current RAG.
  - **Alerts and report drafting** (Stage 5) as new FastAPI + queue jobs.

Implement in order: **ingest + normalize (1)** → **chunk + embed + Qdrant (reuse current RAG)** → **preprocessing (2)** and **NER/classification (3)** → **signals + graph (4)** → **dashboard + alerts + API (5)**.
