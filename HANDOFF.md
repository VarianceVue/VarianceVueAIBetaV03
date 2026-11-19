# VueLogic Prototype Handoff Document

**Date:** November 2026
**Purpose:** Complete handoff for rebuilding VueLogic from scratch. Written for a senior engineer who has never seen this project.
**Labels used:** **[REQ]** = Requirement (must be true of any version). **[IMPL]** = Implementation detail (how the prototype did it). **[UNKNOWN]** = Uncertain whether deliberate or accidental.

---

## 1. Product

### What it does

VueLogic is a web application for AI-driven project controls in construction and infrastructure. It sits between a project controls manager (PCM) and a contractor's schedule submissions. The core job: the PCM uploads a contractor's Primavera P6 schedule (XER file), contract specifications, and a schedule narrative. VueLogic's AI reads all three, then produces a structured baseline review — a formal spreadsheet of comments citing specific spec sections, logic deficiencies, DCMA 14-Point violations, and actionable recommendations. That review is something that currently takes a senior scheduler 2–4 days to produce manually.

Beyond the review, VueLogic provides:
- An AI chat assistant that answers questions about the project's uploaded documents, using RAG (retrieval-augmented generation) over vectorized project files.
- A governance configuration panel where the PCM defines DCMA thresholds, logic rules, and narrative tone — and those settings are injected into every AI review and chat response.
- A schedule intelligence dashboard that parses an XER and produces a DCMA 14-Point scorecard, critical path analysis, and relationship distribution metrics — all computed locally, no LLM needed.
- A document knowledge library with vectorization and conversation review workflows.

### Who uses it

Primary user: **Project Controls Managers (PCMs)** at owner organizations who manage contractor schedules on large construction/infrastructure projects (data centers, power plants, industrial facilities). These are people who know Primavera P6, CPM scheduling, DCMA 14-Point assessments, and EVM.

Secondary user: **Project directors and executives** who want AI-generated summaries and dashboards without touching P6 directly.

### What a day of using it looks like

1. PCM logs in, sees the dashboard with a context-aware greeting ("Baseline V1 has been submitted but not yet reviewed. Ready to run the AI-powered review?").
2. Navigates to Contractor Baseline Review, uploads an XER file and a schedule narrative, clicks "Submit Baseline V1."
3. Goes to Governance Center, adjusts the high-float threshold from 44 to 60 days (owner's preference for this project), confirms SF relationships are banned.
4. Clicks "Execute Review." VueLogic sends the XER + specs + narrative + governance rules to the LLM and gets back a JSON array of 30–80+ review comments. These are saved as a formatted Excel workbook.
5. Downloads the Excel, sends it to the contractor. The contractor fills in the "Contractor Response" column and returns it.
6. PCM uploads the response as part of a V2 submission. VueLogic generates a new review and an **exception report** — comments where the contractor claimed "addressed" but the XER evidence shows otherwise.
7. Between reviews, the PCM uses the chat to ask questions like "What does section 3.2 of the technical provisions say about commissioning?" and VueLogic answers using RAG over the uploaded spec PDFs.

### Why it was built

Manual baseline schedule reviews are expensive, inconsistent, and slow. A senior scheduler costs $150–200/hr and takes 2–4 days per review. Different reviewers catch different things. VueLogic automates the first pass, producing a consistent, spec-referenced, DCMA-compliant review in minutes. The PCM still makes the final call (human-in-the-loop), but the AI does the heavy lifting.

---

## 2. Functional Requirements

### Core (product does not work without these)

| # | Capability | Label |
|---|-----------|-------|
| F1 | **AI chat with project context** — User sends a message, VueLogic responds using the scheduling agent skill as system prompt, with RAG over uploaded documents and conversation history. | [REQ] |
| F2 | **Contractor Baseline Review** — Upload XER + narrative + specs → AI generates structured review comments as a downloadable Excel workbook with specific columns (Comment ID, WBS Reference, Comment Description, Spec Section Reference, Priority, Logic Flag, Recommendation, Contractor Response, Comment Status, Addressed Y/N). | [REQ] |
| F3 | **Schedule philosophy / governance configuration** — PCM defines DCMA thresholds (missing logic %, high float days, high duration days, negative lag tolerance, hard constraint %), logic compliance rules (lead ban, SF ban, hard constraint audit, calendar check, FS-preferred), compliance standard (DCMA/AACE/Custom), and narrative tone (Executive/Technical/Aggressive/Conservative). These settings inject into all LLM prompts. | [REQ] |
| F4 | **XER parsing and schedule intelligence** — Parse P6 XER files into structured data (TASK, TASKPRED, PROJWBS, CALENDAR, TASKRSRC tables). Compute DCMA 14-Point scorecard, relationship distribution, critical path ranking — entirely locally, no LLM call. | [REQ] |
| F5 | **Authentication and multi-tenancy** — Users register with business email, login with JWT, are associated with a client (company). Each client can have multiple projects. Users see only their client's projects. | [REQ] |
| F6 | **Project document library** — Upload files (PDF, DOCX, XER, TXT, XLSX), categorize them, vectorize for semantic search. Track vectorization status per file. | [REQ] |
| F7 | **Version-managed baseline submissions** — Each project has auto-versioned baseline submissions (V1, V2, V3…). V2+ requires a contractor response file. Each version can have one AI review. Reviews can be deleted and re-run. | [REQ] |

### Important (significant value, not blocking)

| # | Capability | Label |
|---|-----------|-------|
| F8 | **Exception report** — After V2+ submission with contractor response, AI identifies comments where contractor claimed "addressed" but XER evidence shows otherwise. Generates a separate Excel with different column structure. | [REQ] |
| F9 | **Schedule Basis Document Builder** — Guided workflow to produce a formal Schedule Basis Memorandum per AACE 38R-06. Captures delivery method, NTP/completion dates, WBS driver, work week, calendar, milestones, logic rationale, cost loading. | [REQ] |
| F10 | **Baseline Review Playbook** — Configure review standards (approve-as-noted, full approval, reject-resubmit), rejection thresholds (max defects, missing scope %), required review checks, and required owner activities that must appear in the schedule. | [REQ] |
| F11 | **Conversation review / digest** — Chat conversations are queued as "pending review." PCM can approve (vectorize for future RAG) or discard (30-day retention). AI summarizes and categorizes conversations. FYI/Remember messages get priority flagging. | [REQ] |
| F12 | **Trust score (HITL)** — Track approvals vs total proposals. AI_Agency_Score = (Approvals / Total_Proposals) × Historical_Accuracy. Score ≥ 0.8 enables Level 1 (autonomous) actions; below 0.8 reverts to full human control. | [REQ] |
| F13 | **Dynamic dashboard greeting** — Context-aware greeting that reports library status, pending reviews, unreviewed baselines, pending vectorization items. | [REQ] |
| F14 | **Activity List and Gantt View** — Parse XER into visual activity list with predecessors, float, critical path indicators. Gantt timeline with critical path highlighting. | [REQ] |
| F15 | **Contractor Update Review** — Same workflow as baseline review, but for schedule updates (separate submission type, separate versioning). | [REQ] |

### Nice-to-Have (built in prototype, may not carry forward)

| # | Capability | Label |
|---|-----------|-------|
| F16 | **Lessons Learned** — Append and retrieve lesson entries (event, what happened, outcome, lesson, recommendation). Injected into LLM context when proposing options. | [REQ] |
| F17 | **Vision API** — Upload site photos, describe via Claude vision, ingest descriptions into the document store. | [IMPL] |
| F18 | **Admin role** — Admin users can see and delete internal files (prefixed with `_`). Regular users cannot. | [REQ] |
| F19 | **Document Q&A** — Standalone RAG + LLM endpoint separate from the main chat. Returns answer + sources with audit trail. | [IMPL] |
| F20 | **Report drafting** — Generate report drafts from NLP summaries and signals using LLM. | [IMPL] |

### Experimental (built but UI mostly not exposed)

| # | Capability | Label |
|---|-----------|-------|
| F21 | **5-stage NLP Document Intelligence Pipeline** — Stage 1: Ingestion (extract text, metadata, dedup). Stage 2: Enrichment (cleaning, language detection, segmentation, structure, vocabulary). Stage 3: Core NLP (NER, classification, relations, temporal, summarization). Stage 4: Intelligence (signals, knowledge graph, analytics). Stage 5: Delivery (dashboard, alerts, audit trail, reports). | [IMPL] — This was built as a complete backend pipeline but only the ingestion stage is meaningfully exercised through the UI. Stages 2-5 have API endpoints but no frontend integration beyond basic dashboards. |
| F22 | **Signal detection** — Rule-based keyword scanning for risk, change, and dispute signals with optional LLM verification. | [IMPL] |
| F23 | **Knowledge graph** — Store subject-relation-object edges from NLP processing. Query related entities. | [IMPL] |
| F24 | **GraphRAG integration** — Hybrid retrieval using knowledge graph + vector search. Requires external graphrag setup with parquet files. | [IMPL] |

---

## 3. User Flows

### 3.1 Registration

1. User clicks "Create an account" on the login page.
2. Fills in: First Name, Last Name, Email, Company, Password, Confirm Password.
3. **Validation:** Email must not be a personal domain (gmail, outlook, etc. — ~30 domains blocked). Password must be ≥ 8 chars, contain uppercase, lowercase, and digit. No special character requirement. **[REQ]**
4. **Client association:** If the email domain is in the domain-client map (currently only `variancevue.com` → `VARIANCEVUE`), the user is auto-associated with that client. Otherwise, `client_id` is NULL. **[IMPL]** — Current approach, not binding. The rebuild should support a proper client onboarding flow.
5. On success: JWT token returned, user is logged in, redirected to project selector.
6. **Error states:** "An account with this email already exists." "Personal email addresses are not allowed." Various password validation messages.

### 3.2 Login

1. User enters email + password.
2. On success: JWT token (24hr expiry) stored in localStorage, redirect to project selector.
3. On failure: "Invalid email or password."
4. **No password reset flow exists.** [IMPL] — Shortcut.

### 3.3 Project Selection

1. After login, user sees "Select Project" with a list of their client's projects.
2. User can click an existing project or create a new one (enter Project ID, click "+ Create").
3. **Creating a project requires `client_id` on the user.** If `client_id` is NULL (domain not mapped), user sees "No company associated with your account." **[REQ]** — This is a deliberate gate, but the mechanism for associating clients to new domains is missing. Currently only variancevue.com is mapped.
4. **Project ID rules:** 2+ chars, uppercase, alphanumeric + hyphens + underscores only. Auto-uppercased, spaces replaced with underscores. **[REQ]**

### 3.4 Dashboard

1. Main landing page after project selection.
2. Shows: Project Controls Assistant (chat widget), Project Knowledge Library (file upload + vectorization), Conversation Review (pending/approved/discarded tabs).
3. Chat widget shows a dynamic greeting based on project state.
4. User types a message → sends to `/api/chat` → AI responds with formatted markdown.
5. **If LLM call fails:** User sees "No response received from the server." **[IMPL]** — Should show a friendlier message.

### 3.5 Contractor Baseline Review (Full Workflow)

1. **Prerequisites:** Upload contract specs (one-time, immutable) OR have scope documents in the library.
2. **Upload XER + Narrative:** Drag-and-drop or browse. XER must have `.xer` extension.
3. **Click "Submit Baseline V1."** Files stored with prefixed names (`baseline_v1_filename.xer`).
4. **Click "Execute Review."** The following happens:
   a. System loads: specs content, XER content (summarized), narrative content, governance settings.
   b. Builds a system prompt with detailed instructions for column structure, logic flag types, priority definitions, philosophy settings.
   c. Sends to LLM with high max_tokens (65536 on local, 12000 on Vercel).
   d. Parses JSON array from response. If parsing fails, retries once with "output only JSON" instruction.
   e. Re-numbers comment IDs sequentially from where the last review left off (BLR-001, BLR-002…).
   f. Saves as formatted Excel workbook with styled headers, color-coded logic flags, auto-filters.
   g. Also saves as text and vectorizes for future RAG.
5. **View review on screen** or **download Excel.**
6. **V2+ flow:** Must include contractor's filled response file. AI generates new comments AND verifies prior responses (Addressed Yes/No column).
7. **Exception report (optional):** After V2+ with response, click to generate. Separate LLM call that identifies discrepancies between contractor claims and XER evidence.

### 3.6 Schedule Philosophy (4 sub-modules)

1. **Governance Center:** Sliders for thresholds + toggles for rules + narrative tone selector + compliance standard buttons. Saves to JSON file per project.
2. **Basis Document Builder:** Form fields for delivery method, NTP/completion dates, WBS config, work calendar, milestones, logic rationale, cost loading. Saves as part of philosophy settings.
3. **Review Playbook:** Review standard (approve-as-noted/full/reject), thresholds, required checks, owner activities with durations. Saves as part of philosophy settings.
4. **Intelligence Dashboard:** Reads uploaded XER, computes DCMA scorecard live. Shows pass/warn/fail per criterion, relationship distribution pie chart, critical path top 10. No LLM call needed.

### 3.7 Error and Empty States

- **No XER uploaded:** "Upload an XER schedule to see intelligence data."
- **No specs uploaded:** Yellow banner: "Upload contract specs or scope documents before submitting a baseline."
- **No review results:** "No review results yet. Execute a review from the Contractor Baseline Review page."
- **Empty library:** "No files in the project library yet. Upload documents above to build the project knowledge base."
- **No conversations pending:** "No pending conversations to review."
- **LLM returns invalid JSON:** Retries once, then: "AI returned invalid JSON. Try again."
- **LLM rate limited:** Error message includes suggestion to use Claude instead of OpenAI.
- **Qdrant unavailable:** Gracefully falls back to keyword search. User never sees an error.

---

## 4. Domain Model

### Users

| Field | Type | Constraints | Business Meaning |
|-------|------|-------------|------------------|
| `id` | integer | PK, auto-increment | Internal identifier. |
| `first_name` | text | NOT NULL | Display name for greetings. User-editable at registration only. |
| `last_name` | text | NOT NULL | Display name. User-editable at registration only. |
| `email` | text | NOT NULL, UNIQUE, NOCASE | Login identifier. Validated against blocked domains. Immutable after registration. |
| `company` | text | NOT NULL | Self-reported company name. Informational only — not used for authorization. |
| `password` | text | NOT NULL | bcrypt hash (or PBKDF2 fallback). |
| `client_id` | text | FK → clients, nullable | Derived at registration from email domain → `_DOMAIN_CLIENT_MAP`. NULL if domain not mapped. Determines which projects the user can access. |
| `role` | text | DEFAULT 'user' | 'user' or 'admin'. Admin can access `/api/admin/*` endpoints. |
| `created_at` | text | auto | ISO datetime. |

### Clients

| Field | Type | Constraints | Business Meaning |
|-------|------|-------------|------------------|
| `client_id` | text | PK | Short code like "VARIANCEVUE". Used as FK in projects and users. [REQ] |
| `name` | text | NOT NULL | Display name of the company. |
| `created_at` | text | auto | ISO datetime. |

### Projects

| Field | Type | Constraints | Business Meaning |
|-------|------|-------------|------------------|
| `project_id` | text | PK | User-chosen ID, e.g., "DEMO", "BLDG-A". Must be 2+ chars, uppercase alphanumeric + hyphens + underscores. [REQ] Also used as `session_id` throughout the system. |
| `name` | text | NOT NULL | Display name, e.g., "Demo Project". |
| `client_id` | text | FK → clients, NOT NULL | Owning company. |
| `created_at` | text | auto | ISO datetime. |

**Critical note:** The `project_id` is used everywhere as `session_id` in the store, vector store, baseline, and all file operations. This is the single partition key for all project data. **[IMPL]** — This conflation of project_id and session_id was a prototype shortcut. A rebuild should separate these concepts.

### Baseline Submissions

| Field | Type | Constraints | Business Meaning |
|-------|------|-------------|------------------|
| `session_id` | text | NOT NULL | Project this belongs to. |
| `submission_type` | text | 'baseline' or 'update' | Two parallel version tracks. |
| `version` | integer | auto-incremented per (session_id, submission_type) | V1, V2, V3… |
| `xer_filename` | text | nullable | Original filename of the P6 XER export. |
| `xer_size` | integer | DEFAULT 0 | Bytes. |
| `narr_filename` | text | nullable | Schedule narrative document. |
| `narr_size` | integer | DEFAULT 0 | Bytes. |
| `resp_filename` | text | nullable | Contractor's filled comment response file. Required for V2+. |
| `resp_size` | integer | DEFAULT 0 | Bytes. |
| `submitted_at` | text | NOT NULL | ISO datetime. |
| `status` | text | DEFAULT 'Under Review' | Not used in any state machine currently. **[UNKNOWN]** — May have been intended for a workflow status. |

### Contract Specs

| Field | Type | Constraints | Business Meaning |
|-------|------|-------------|------------------|
| `session_id` | text | UNIQUE | One set of specs per project. |
| `filename` | text | NOT NULL | Original filename. |
| `size` | integer | DEFAULT 0 | Bytes. |
| `uploaded_at` | text | NOT NULL | ISO datetime. |

**[REQ]** Specs are immutable once uploaded — cannot be replaced. This is deliberate: specs represent the contractual baseline.

### Review Results

| Field | Type | Business Meaning |
|-------|------|------------------|
| `session_id` | text | Project. |
| `version` | integer | Which baseline version this review is for. |
| `columns` | text (JSON array) | Column names used in this review. Version-specific columns get ` vN` suffix. |
| `comment_count` | integer | Number of review comments. |
| `last_comment_num` | integer | Highest BLR-NNN number used. Next review starts numbering from `last_comment_num + 1`. [REQ] |
| `exception_count` | integer | Number of exception findings. |
| `exception_filepath` | text | Path to exception Excel. |
| `filepath` | text | Path to review Excel. |
| `created_at` | text | ISO datetime. |

### Files (Project Library)

Stored per session as a metadata JSON + content files. Each file has:

| Field | Type | Business Meaning |
|-------|------|------------------|
| `filename` | text | Storage key. May be prefixed (e.g., `baseline_v1_schedule.xer`, `_baseline_review_v1`). |
| `size` | integer | Bytes. |
| `uploaded_at` | text | ISO datetime. |
| `category` | text | User-assigned or auto-detected (e.g., "Contract Specifications", "Baseline Schedule (XER)", "Baseline Narrative"). |
| `vectorized` | boolean | Whether this file has been indexed in the vector store. |

**File naming convention (internal):** `{baseline|update}_v{N}_{original_filename}`. Response files: `{baseline|update}_v{N}_resp_{filename}`. Review results: `_baseline_review_v{N}`. Exception reports: `_baseline_exception_v{N}`.

**Visibility rules:** Files starting with `_` are hidden from regular users, except: `_baseline_review_v*`, `_baseline_exception_v*`, `_baseline_v*_*`, `_specs_*`. [REQ]

### Philosophy Settings

Stored as a JSON file per project with three sections: `governance`, `basis`, `playbook`. See the defaults in section 5 below.

### Conversation Digest Items

| Field | Type | Business Meaning |
|-------|------|------------------|
| `id` | text | Derived from timestamp + content hash. Format: `turn-{iso_ts}-{hash:08x}`. |
| `timestamp` | text | When the message was sent. |
| `user_message` | text | The user's question/statement. |
| `assistant_response` | text | The AI's answer. |
| `priority` | text | 'normal' or 'fyi'. FYI if message starts with "fyi" or "remember this". [REQ] |
| `status` | text | 'pending' → 'approved' or 'discarded'. |
| `topic` | text | AI-generated short title (≤60 chars), or truncated message if LLM unavailable. |
| `summary` | text | AI-generated 1-2 sentence summary, or truncated message. |
| `category` | text | One of: Schedule Analysis, Cost & EVM, Risk, Baseline Review, Document Query, System Query, General. |

---

## 5. Business Logic and Rules

### Authentication

- **[REQ]** Personal email domains are blocked (30 domains: gmail, outlook, yahoo, protonmail, etc.). Business email only.
- **[REQ]** Password rules: ≥ 8 chars, 1 uppercase, 1 lowercase, 1 digit. No special character required.
- **[IMPL]** JWT tokens expire after 24 hours. Algorithm: HS256. Secret: auto-generated and persisted to `.jwt_secret` file if not set via env var.
- **[IMPL]** If PyJWT is not installed, a homebrew HMAC-SHA256 token scheme is used as fallback.
- **[IMPL]** Client association is via a hardcoded `_DOMAIN_CLIENT_MAP` (`variancevue.com` → `VARIANCEVUE`). Any other domain gets `client_id = NULL`. This means new customers cannot create projects without code changes. **Current approach, not binding.**

### Baseline Review

- **[REQ]** Contract specs or scope documents must be uploaded before any baseline submission.
- **[REQ]** V2+ submissions require a contractor response file.
- **[REQ]** Review comment IDs are globally sequential across all versions. V1 might use BLR-001 through BLR-045. V2 starts at BLR-046. This ensures no ID reuse.
- **[REQ]** Review columns are version-tagged: "Comment Description v1", "Comment Description v2", etc. for `VERSIONED_COLS` (Comment Description, Recommendation for Correction, Contractor Response).
- **[REQ]** Logic Flag must be one of: Missing Hard Logic, Preferential Cross-WBS, Dangling Logic, Redundant Logic, Incorrect Relationship Type, or empty string.
- **[REQ]** Priority must be Mandatory or Recommendation. Mandatory for spec violations, logic errors, DCMA failures. Recommendation for best-practice improvements.
- **[REQ]** Comment Status must be "Open" for all new comments. Contractor Response must be empty (for contractor to fill in).
- **[REQ]** The review prompt instructs the LLM to generate "as many comments as the schedule warrants" with "no limit." A thorough review of a real schedule typically produces 30–100+ comments.
- **[IMPL]** XER content is truncated to 80,000 chars (25,000 on Vercel). Specs to 12,000 (6,000 on Vercel). Narrative to 8,000 (5,000 on Vercel). Max output tokens: 65,536 (12,000 on Vercel). These limits exist because of LLM context windows and Vercel's 60-second serverless timeout.
- **[IMPL]** If LLM returns invalid JSON, one retry is attempted with a "JSON only" instruction.
- **[REQ]** Exception report only fires when there's a contractor response file. It specifically looks for comments where contractor claimed "addressed" but XER contradicts the claim.

### Schedule Intelligence (DCMA Scorecard)

All thresholds configurable via governance settings. Defaults:

| Metric | Target | Default Threshold |
|--------|--------|-------------------|
| Missing Logic | ≤ N% | 5% |
| High Float | ≤ N days | 44 days |
| High Duration | ≤ N days | 20 days |
| Negative Lags | ≤ N | 0 |
| Hard Constraints | ≤ N% | 5% |
| FS Relationship % | ≥ 80% | 80% |

**[UNKNOWN]** The 44-day high-float default. This is common in construction scheduling but the origin of this specific number in this project is undocumented.

**Status calculation:**
- Pass: actual ≤ threshold
- Warn: actual ≤ threshold × 1.5
- Fail: actual > threshold × 1.5
- For "higher is better" metrics (FS%, Resource Loaded%, Calendar%), the logic inverts.

**[IMPL]** XER hours are converted to days by dividing by 8 (8-hour workday assumed). This is hardcoded and not configurable.

### Conversation Digest

- **[REQ]** Every chat turn is queued to "pending" for PCM review.
- **[REQ]** Messages starting with "fyi" or "remember this" are flagged as priority.
- **[REQ]** Discarded items have 30-day retention before purge.
- **[IMPL]** Digest generation uses LLM to summarize and categorize. Falls back to message truncation if no API key.
- **[IMPL]** Category assignment: keyword-based fallback when LLM unavailable. Keywords map to categories (e.g., "baseline" → "Baseline Review", "cost" → "Cost & EVM").

### Trust Score

- **[REQ]** Formula: `AI_Agency_Score = (Approvals / Total_Proposals) × Historical_Accuracy`
- **[REQ]** Score ≥ 0.8 enables Level 1 (autonomous). Below 0.8 = full human control.
- **[IMPL]** Historical_Accuracy defaults to 1.0. No mechanism to feed back rework data.
- **[IMPL]** Trust score stored in Redis only; not available with local file store.

### Poison Phrase Filtering

- **[REQ]** Chat responses containing phrases like "don't have access to", "cannot access", "outside my scope" are detected as "poisoned" — the AI incorrectly claiming it lacks document access.
- **[IMPL]** Poisoned responses are replaced in conversation history with a system note. Poisoned turns are stripped from the LLM context on subsequent messages. About 12 phrases are checked.

### Philosophy Defaults

Governance defaults: Missing logic 5%, high float 44d, high duration 20d, negative lag 0, hard constraint 5%. DCMA standard. Executive tone. Rules: lead restriction ON, SF ban ON, hard constraint audit ON, calendar check OFF, FS-preferred OFF.

Basis defaults: Design-Build delivery, area-driven WBS, 4 levels, 5-day week, 8 hrs/day, 1 shift.

Playbook defaults: Approve-as-Noted standard, 20 max defects before rejection, 10% missing scope threshold. 5 required owner activities (Permit Approvals 30d, Design Reviews 14d, Inspections 5d, Third-Party Coordination 21d [not required], Utility Coordination 45d).

### File Category Auto-Detection

Files are auto-categorized based on filename keywords:
- `.xer` → "Baseline Schedule (XER)"
- "spec", "provision", "technical" → "Contract Specifications"
- "narrative", "baseline schedule" → "Baseline Narrative"
- "scope", "sow" → "Scope Documents"
- "rfi", "submittal" → "RFI / Submittals"
- etc. (~15 categories total)

---

## 6. Edge Cases and Failure Modes

### Actually encountered

1. **Client association gap.** Users who register with non-variancevue.com emails get `client_id = NULL` and cannot create projects. They see "No company associated with your account." This blocks any demo with a new email domain. **[REQ]** for multi-tenancy, but the mechanism is broken.

2. **LLM returning invalid JSON for review comments.** The review prompt asks for a JSON array. Claude sometimes wraps it in markdown code fences or adds explanatory text. The code strips markdown fences, cleans trailing commas, and retries once. Still fails occasionally with very long reviews.

3. **XER encoding issues.** Some XER files are uploaded as base64-encoded binary (from the browser FileReader API). The code detects this pattern and base64-decodes. Some XER files start with `%T` (text), some start with `ERMHDR` (binary header). Both are handled.

4. **PDF extraction failures.** Some PDFs are image-only (scanned). pypdf returns empty text. The code falls back to pymupdf (if installed). If both fail, returns a message: "This PDF could not be read as text." OCR is not implemented.

5. **Conversation "poisoning."** The LLM sometimes says "I don't have access to your documents" even when documents are present in the RAG context. This led to a cascading problem: the false statement gets stored in conversation history, and future prompts include it, reinforcing the error. Fixed by poison phrase detection and stripping.

6. **Vercel timeout (60s).** Baseline reviews with large XER files and 65K max tokens exceed the Vercel serverless timeout. The code has separate Vercel limits (lower max_tokens, truncated inputs, fast model preference). Even so, complex reviews sometimes timeout.

7. **SQLite schema migration.** The code uses `ALTER TABLE ADD COLUMN` wrapped in try/except for schema evolution. This is fragile and runs on every connection.

8. **Redis vs local file store inconsistency.** The system checks for Redis first, falls back to local file. On Vercel with Redis, some operations write to both (submissions), some write to Redis only (lessons, trust score). On restart, local-only data is lost. This caused "Review file not found" errors after Vercel cold starts.

9. **Hardcoded demo data in React bundle.** The minified React JavaScript contains a hardcoded project named "Integrated Industrial Complex" with demo activities. This shows up if users navigate to the Health Audit or Schedule Philosophy React tabs.

10. **Browser session persistence.** Auth tokens are in localStorage. Changing a password in the backend doesn't invalidate existing tokens until JWT expiry (24 hours).

---

## 7. Data

### XER Files (Primary Data Source)

**Format:** Primavera P6 XER export. Tab-delimited text with `%T` (table name), `%F` (field names), `%R` (row data), `%E` (end of table) markers.

**Key tables:**
- `TASK` — Activities. Fields: task_id, task_code, task_name, wbs_id, task_type, total_float_hr_cnt, target_drtn_hr_cnt, remain_drtn_hr_cnt, target_start_date, target_end_date, status_code, phys_complete_pct, cstr_type, cstr_type2, clndr_id.
- `TASKPRED` — Relationships. Fields: task_id, pred_task_id, pred_type (PR_FS/PR_SS/PR_FF/PR_SF), lag_hr_cnt.
- `PROJWBS` — WBS hierarchy. Fields: wbs_id, wbs_short_name, wbs_name, parent_wbs_id.
- `CALENDAR` — Calendar definitions. Fields: clndr_id, clndr_name.
- `TASKRSRC` — Resource assignments. Fields: task_id, rsrc_id, target_qty, target_cost, remain_qty, remain_cost.
- `PROJECT` — Project metadata. Fields: proj_short_name.

**Typical volumes:** 500–5,000 activities, 800–10,000 relationships, 50–200 WBS elements. Largest XER seen: ~15,000 activities.

**Quality issues:**
- Hours are in 8-hour-day units (hardcoded assumption).
- task_type values include TT_Task, TT_Mile, TT_FinMile, TT_WBS, TT_LOE — the code must filter out non-work types for many metrics.
- Some XER files omit fields (e.g., no total_float_hr_cnt). The code defaults to 0.
- Pred_type uses P6 internal codes (PR_FS) which must be mapped to standard abbreviations (FS).

### PDF Documents

Contract specs and narratives. Typically 10–200 pages. Some are image-only scans (cannot extract text). Text extraction uses pypdf with pymupdf fallback. A common artifact: PDF extraction produces split section numbers ("3. 1" instead of "3.1") which is fixed by regex normalization.

### Data Storage

**[IMPL]** All data is stored as JSON files in `schedule_agent_web/file_store/{session_id}/`. Conversation history: `conversation.json`. Files: `meta.json` + `contents/{filename}`. Philosophy: `philosophy.json`. Digests: `digests/pending.json`, `approved.json`, `discarded.json`. Schedule: `schedule.json`. Generated docs: `generated_docs/meta.json` + `{doc_id}.md`.

When Redis is available (Vercel), data is duplicated to Redis with key prefixes like `vuelogic:conv:`, `vuelogic:files:`, etc.

### Sample Record (Altered Values)

XER TASK row:
```
task_id=12345  task_code=ACT-2010  task_name="Install Level 2 Switchgear"
wbs_id=50  task_type=TT_Task  total_float_hr_cnt=24  target_drtn_hr_cnt=80
remain_drtn_hr_cnt=80  target_start_date="2026-04-15"  target_end_date="2026-04-29"
status_code=TK_NotStart  phys_complete_pct=0  clndr_id=3
```

Review comment:
```json
{
  "Comment ID": "BLR-012",
  "WBS Reference": "2.1 Electrical",
  "Comment Description v1": "Activity ACT-2010 'Install Level 2 Switchgear' has no successor. Per DCMA 14-Point, all activities should have at least one successor.",
  "Spec Section Reference": "Section 3.2.1",
  "Priority": "Mandatory",
  "Logic Flag": "Dangling Logic",
  "Recommendation for Correction v1": "Add a Finish-to-Start successor to the downstream testing activity.",
  "Contractor Response v1": "",
  "Comment Status": "Open",
  "Addressed (Yes/No)": null
}
```

---

## 8. Integrations and External Dependencies

### LLM Providers

| Provider | Purpose | Auth | Failure Mode |
|----------|---------|------|-------------|
| **Anthropic Claude** (primary) | Chat, baseline review, exception report, digest summarization, signal detection, classification, summarization | `ANTHROPIC_API_KEY` env var | Returns error string. Falls back through model list: claude-sonnet-4 → claude-3.5-sonnet → claude-3.5-haiku → claude-3-haiku. 404 errors trigger fallback to next model. |
| **OpenAI** (secondary) | Same purposes. Used only if Anthropic key not set. Also used for embeddings (text-embedding-3-small). | `OPENAI_API_KEY` env var | Returns error string. Rate limit errors include suggestion to switch to Claude. |

**[REQ]** At least one LLM provider must be configured. Claude preferred when both are set.
**[IMPL]** Claude streaming is used for large reviews (>8192 tokens). OpenAI uses non-streaming.

### Vector Store

| Service | Purpose | Auth | Failure Mode |
|---------|---------|------|-------------|
| **Qdrant** (optional) | Semantic search over documents and conversations | `QDRANT_URL` + `QDRANT_API_KEY` env vars | Graceful degradation to keyword-based fallback search. No user-visible error. |

**[IMPL]** Collection name: `vuelogic_docs`. Vectors: Cosine distance. Embedding dim: 384 (hash-based) or 1536 (OpenAI). Chunks: 1200 chars with 200 overlap. Batch upsert: 64 points per batch.

### Persistence

| Service | Purpose | Auth | Failure Mode |
|---------|---------|------|-------------|
| **Upstash Redis** (optional) | Persistent KV store for Vercel deployment | `UPSTASH_REDIS_REST_URL` + `UPSTASH_REDIS_REST_TOKEN` env vars | Falls back to local file system. Lessons and trust score are Redis-only (lost without it). |

### Libraries

| Library | Purpose | Required? |
|---------|---------|-----------|
| `fastapi` + `uvicorn` | Web framework + dev server | Yes |
| `anthropic` | Claude API client | Yes (one of) |
| `openai` | OpenAI API client | Yes (one of) |
| `PyJWT` | JWT creation/verification | Yes (fallback exists) |
| `bcrypt` | Password hashing | Yes (PBKDF2 fallback exists) |
| `pypdf` | PDF text extraction | Yes |
| `openpyxl` | Excel workbook generation for reviews | Yes |
| `fpdf2` | PDF generation (unused in prototype?) | Installed but **[UNKNOWN]** if actually used |
| `httpx` | HTTP client for Qdrant API | Yes (for Qdrant) |
| `langdetect` | Language detection in enrichment pipeline | Optional |
| `dateparser` | Date extraction in temporal NLP | Optional |
| `python-dotenv` | Load .env file | Yes |
| `upstash-redis` | Redis client for Vercel KV | Optional |
| `python-multipart` | File upload handling | Yes |

---

## 9. Decisions and Reasoning

| Decision | What was chosen | What was rejected | Why |
|----------|----------------|-------------------|-----|
| **LLM provider** | Claude as primary, OpenAI as fallback | OpenAI-only | Claude's longer context window (200K) handles large XER files better. Claude's structured output is more reliable for JSON review comments. |
| **Vector store** | Qdrant via REST API | In-process vector DB (ChromaDB, FAISS) | Qdrant runs externally, avoids Python dependency issues (especially on ARM64/Vercel). REST API means no native binary deps. |
| **Hash-based embeddings** | Custom feature-hashing as fallback when OpenAI unavailable | sentence-transformers | sentence-transformers requires torch (~2GB) which breaks Vercel's 250MB limit. Hash embeddings provide bag-of-words-level similarity with zero dependencies. |
| **Single-file frontend** | 4800-line index.html with inline JS + CDN React | npm/webpack build | Prototype speed. No build step, no node_modules, instant deployment. |
| **SQLite + JSON files** | Local persistence with Redis overlay | PostgreSQL | Prototype simplicity. SQLite for auth (structured), JSON files for everything else (flexible schema). Redis for Vercel persistence. |
| **Review output as Excel** | openpyxl-generated .xlsx | PDF, CSV | Excel is the industry standard for schedule review comments. Contractors expect to fill in the "Contractor Response" column in Excel. |
| **XER parsing: custom parser** | Custom tab-delimited parser | python-xer-reader library | The XER format is simple enough that a 20-line parser handles it. No external dependency needed. |
| **Immutable contract specs** | One upload, cannot replace | Allow re-upload | Deliberate: specs represent the contractual baseline. If specs change, that's a contract modification, not a UI operation. |
| **Comment ID continuity** | BLR-NNN sequential across all versions | Reset per version | Deliberate: when V2 review references V1's BLR-012, there's no ambiguity. The contractor can trace comment history. |

### Owner pushed back on / changed mid-build

**[UNKNOWN]** — I cannot determine from the code or conversation history what specific decisions the owner pushed back on. The conversation record shows the owner requested a password change (user1 from VarianceVu3Tr14l to VivekVueTr14l) and asked about cleanup for a client presentation. No other pushback is documented in this session.

---

## 10. Known Shortcuts and Tech Debt

| Shortcut | Why it was acceptable | What it takes to fix |
|----------|----------------------|---------------------|
| **Single 3800-line main.py** | Prototype speed. Everything in one file means no import headaches. | Split into route modules: auth, chat, baseline, library, philosophy, ingestion, admin. Use FastAPI routers. |
| **4800-line single HTML file** | No build step needed. CDN-loaded React. | Proper React project with components, routing, state management. |
| **SQLite for auth, JSON files for everything else** | Works for single-server, single-user prototype. | PostgreSQL with proper migrations (Alembic). |
| **Hardcoded domain-client map** | Only one client (VarianceVue) during prototype. | Client self-registration or admin-managed client setup. |
| **Hardcoded seed users with passwords in source** | Demo convenience. | Remove seed data. Add proper onboarding flow. Use env vars for initial admin credentials. |
| **CORS allow_origins=["*"]** | Prototype running on localhost. | Restrict to specific domains. |
| **API docs publicly accessible** | Useful during development. | Disable `/docs` and `/redoc` in production or auth-gate them. |
| **No password reset flow** | Not needed for prototype. | Email-based reset or admin override. |
| **No email verification** | Not needed for prototype. | Send verification email, block login until confirmed. |
| **Trust score Redis-only** | Redis was available on Vercel. | Persist to database. |
| **Lessons learned Redis-only** | Same. | Persist to database. |
| **8-hour-day hardcoded** | Standard assumption in construction scheduling. | Make configurable via philosophy settings (hours_per_day already exists in basis but isn't used in calculations). |
| **No rate limiting** | Prototype with few users. | Add rate limiting per user/IP for chat and review endpoints. |
| **No file size validation on frontend** | Didn't hit issues in testing. | Add client-side file size limits. |
| **Review Excel files on disk only** | Works for single server. | Store in object storage (S3) or generate on-demand. |
| **"Soon" badges on 6 sidebar modules** | Placeholder for future features (Cost, EVM, Risk, Cx, Change Control, PCM Priorities). | Either implement or remove from navigation. |
| **Hardcoded demo data in React bundle** | Bundled for demo purposes. | Remove or replace with API-driven data. |
| **`except Exception: pass` in seed** | Avoids crash on startup if DB is locked. | Proper error handling and logging. |
| **No automated tests** | Prototype speed. | Add test suite covering at least: auth, chat, baseline review, XER parsing, philosophy save/load. |

---

## 11. Non-Functional Observations

### Performance

- **Chat response time:** 2–5 seconds for simple questions. 10–15 seconds when RAG context is large (many uploaded files).
- **Baseline review execution:** 30–90 seconds depending on XER size and number of comments generated. Claude sonnet-4 with 65K max tokens.
- **XER parsing:** Instant (<100ms) for 5,000 activities. The custom parser is fast.
- **DCMA scorecard computation:** Instant (<200ms). Pure Python, no LLM.
- **PDF text extraction:** 1–3 seconds for 100-page PDFs.
- **Vectorization:** 2–10 seconds per file depending on size and whether using OpenAI embeddings vs hash-based.

### Memory

- **Uvicorn process:** ~80MB baseline. Grows with uploaded file content held in memory during processing.
- **XER summarization:** Builds a complete string of all activities and relationships. For 10,000 activities, this can be 5–10MB of text.
- **System prompt with context:** Can reach 200KB+ when multiple large files are uploaded (XER content + PDF previews + philosophy + RAG hits).
- **No streaming for chat responses.** The full response is generated server-side before returning to the client. This means the user sees no intermediate output.

### Concurrency

- **SQLite:** Uses WAL mode but is fundamentally single-writer. Multiple simultaneous baseline reviews on the same project could conflict.
- **File store:** No file locking. Concurrent writes to the same JSON file could corrupt data.
- **Redis:** Thread-safe, but the read-modify-write pattern (get list → append → save) is not atomic.

### Vercel-specific

- **60-second timeout** for serverless functions. Long reviews may exceed this.
- **250MB package limit.** No room for heavy ML dependencies (torch, sentence-transformers, spacy).
- **Ephemeral filesystem.** Files written to disk are lost on cold start. This is why Redis persistence is critical for Vercel.

---

## 12. Open Questions

1. **Is the blocked-email-domain list a requirement or a prototype shortcut?** The list blocks all personal email providers. In a paid product, what's the onboarding flow for a new company? Admin creates client → invites users? Or is self-registration with domain auto-mapping the intended pattern?

2. **What is the intended multi-tenancy model?** Currently: `Client → Projects → Users`. Is this sufficient, or do we need teams, roles beyond user/admin, project-level permissions?

3. **Should the "Soon" modules (Cost & Financials, EVM Intelligence, Risk & QRAs, Cx & Turnover, Change Control, PCM Priorities) be included in the rebuild scope?** They have no backend implementation. Are there specs or requirements for these?

4. **What is the intended persistence layer?** The prototype uses SQLite + JSON files + optional Redis + optional Qdrant. Is the rebuild targeting PostgreSQL? What about the vector store — self-hosted Qdrant, managed Qdrant Cloud, or a different solution (Pinecone, pgvector)?

5. **Is Vercel still the deployment target?** The 60-second timeout and 250MB limit are significant constraints. Would a containerized deployment (AWS ECS, Railway, Fly.io) remove the need for the Vercel-specific workarounds?

6. **How should client/company creation work?** Currently, companies exist only if seeded in code or if a matching domain exists in the hardcoded map. There's no admin UI for managing clients.

7. **What is the role of the NLP Document Intelligence Pipeline (Stages 2–5)?** It was built as a complete backend but has minimal frontend integration. Should the rebuild include it, simplify it, or drop it?

8. **What drove the 44-day high-float threshold default?** Is this an industry standard (GAO says 44 working days ≈ 2 months) or a project-specific number?

9. **Should the system support multiple concurrent XER files per project?** Currently, the "latest XER" is used for intelligence dashboard. What about tracking schedule progress across monthly updates?

10. **Is the Review Playbook's "required owner activities" list (Permit Approvals 30d, Design Reviews 14d, etc.) a product default, or was it configured for a specific project type?** Should it be empty by default?

11. **What is the intended behavior for the `status` field on baseline submissions?** It's always "Under Review" and never changes. Was a state machine planned?

12. **Should chat history persist across project switches?** Currently, each project has its own conversation. If a user switches from project ALPHA to project BETA and back, they see ALPHA's history. Is this correct?

13. **The `fpdf2` library is installed but I could not find where it's used in the core flow.** Was it intended for generating PDF review reports?

14. **The `vision.py` module uses a hardcoded model (`claude-3-5-sonnet-20241022`) that differs from the main chat's model selection logic.** Should these be unified?

15. **The prototype has no webhook, email, or Slack integration for alerts.** The `send_alert` function in the delivery module is a no-op stub. Was real-time alerting planned?

---

## Uncertainties (Explicit List)

These are things I am **not confident** about — they may be deliberate decisions, accidents, or artifacts of prototype evolution:

- Whether the "Schedule Workspace" React integration (Activity List, Gantt, Health Audit) was working or just scaffolded. The React bundle has hardcoded demo data and the integration uses `activateReactTab()` which hides the custom sidebar.
- Whether the `submission_type` field ("baseline" vs "update") distinction is important to the owner, or if it was added speculatively.
- Whether the hash-based embedding fallback produces acceptable search quality for real documents, or if it was only a "something is better than nothing" stopgap.
- Whether the `philosophy.json` shape (governance/basis/playbook) was deliberately designed or evolved incrementally.
- Whether the frontend's "Conversation Review" workflow (approve → vectorize) is considered core UX or an experimental feature.
- Whether the owner considers Upstash Redis a permanent dependency or would prefer everything in one database.
- Whether the `_POISON_PHRASES` list is complete or if new phrases will need to be added for different LLM models.
- Whether the 100-message conversation history limit (`CONV_MAX_LEN = 100`) was a deliberate choice or arbitrary.
- Whether the 40-message LLM context window (last 20 turns) is optimal or was picked without testing.
- Whether the owner wants to keep the "Contractor Update Review" as a separate submission type track, or merge it with baseline.
