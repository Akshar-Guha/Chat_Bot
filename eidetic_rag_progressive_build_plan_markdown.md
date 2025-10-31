# EideticRAG — Progressive Build Plan (Markdown)

Boss — this is a step‑by‑step, incrementally testable plan for building **EideticRAG**. No code snippets here — just a clear, practical roadmap that walks you from foundation to frontend, with explicit gating tests and acceptance criteria before moving forward.

---

## Quick summary

**Goal:** Build a retrieval-augmented system that *remembers*, *reflects*, and *adapts* — with transparent provenance, user-editable memory, and a verifier that reduces hallucinations. This plan is organized as sequential stages; each stage includes deliverables, tests you must pass before continuing, and acceptance criteria.

---

## Prerequisites & assumptions

- You have a development laptop or server (local-first). Hybrid/cloud options are supported later.
- Familiarity with Python and common ML/NLP tools (you’ll avoid heavy infra early).
- You will start with modest local models and may optionally add cloud LLMs later.
- All sensitive user data must be treatable as deletable/exportable.

---

# Stage 0 — Planning & Setup (Gate 0)

**Purpose:** define scope, sample dataset, metrics, and minimum viable features.

**Deliverables:**
- Project README (vision + non-goals).
- Small sample corpus (2–10 PDFs or web pages) for iterative testing.
- Test dataset with ground-truth Q→chunk mappings for retrieval evaluation.
- List of required libraries and offline models to test with.

**Must-pass tests before Stage 1:**
- You can ingest a sample doc and locate a known sentence by character offsets from the extracted text.
- Retrieval ground-truth file loads and is readable by the test harness.

**Acceptance criteria:**
- Project basics documented. Sample dataset ingested manually and verifiable.

---

# Stage 1 — Core Foundation: Ingest, Chunk, Embed, Index (Gate 1)

**Purpose:** establish reliable, reproducible pipelines for converting raw documents into indexed vectors with provenance.

**Deliverables:**
- Ingestor that handles PDFs and plain text (text + page + offsets metadata).
- Chunker with configurable chunk size & overlap; chunk metadata schema.
- Embedding generator using a small transformer-based embedder.
- Local vector index (FAISS/Chroma) with persistent storage of embeddings + metadata.
- Basic CLI/utility to reindex and inspect index contents.

**Tests before moving on:**
1. **Chunk integrity test:** for each sample doc, randomly pick a chunk_id and verify that the chunk's `start_char`/`end_char` correspond to the extracted original text.
2. **Embedding stability test:** generate embeddings for the same chunk twice (same environment) and assert near-identical vectors (cosine similarity within expected tolerance).
3. **Index retrieval test:** run a known-query that should return a known chunk_id in top-k.

**Acceptance criteria:**
- Index persists to disk and can be reloaded.
- All three tests pass reliably.

**Rollback plan:**
- If chunking is inconsistent, revert to simpler whitespace/token-based chunking rules and retest.

---

# Stage 2 — Baseline RAG (Gate 2)

**Purpose:** wire up generation so that queries produce answers using retrieved local context. Keep this minimal: retrieval + prompt → generator → answer.

**Deliverables:**
- Minimal API: `POST /query` that returns `answer + top_k_chunks + provenance`.
- Small local LLM or cloud fallback configured and callable.
- Basic UI (Streamlit/Gradio) to ask queries and show returned chunks.

**Tests before moving on:**
1. **End-to-end test:** query a question with a known expected answer; the returned answer must cite one of the ground-truth chunks and include accurate provenance.
2. **Latency sanity check:** simple queries complete without crashing the app (ensure memory limits respected).
3. **Edge-case handling:** broken PDF or empty input results in graceful error and helpful message.

**Acceptance criteria:**
- E2E tests pass for the sample dataset and the system remains stable under several sequential queries.

**Risks & mitigations:**
- If the generator hallucinate on obvious factual queries: lower generation temperature or rely more on extractive summarization from chunks.

---

# Stage 3 — Retriever Controller & Intent Classification (Gate 3)

**Purpose:** make retrieval behavior adaptive based on query intent (factual, comparative, causal, code, etc.).

**Deliverables:**
- Intent classifier (lightweight) that tags incoming queries into predefined buckets.
- Retrieval policies per intent (k, depth, multi-hop toggle, embedding type preference).
- Integration test harness to simulate different intent types and assert retrieval changes.

**Tests before moving on:**
1. **Policy selection test:** for a set of labeled queries, confirm the controller chooses the expected policy.
2. **Policy effect test:** same query with different policies should yield measurable differences in retrieved sets (e.g., factual→tighter set; comparative→broader).

**Acceptance criteria:**
- Intent classification accuracy sufficient to change retrieval behavior meaningfully on sample dataset.

**Note:** continue to log classifier decisions for future offline analysis.

---

# Stage 4 — Memory Layer (Gate 4)

**Purpose:** persist conversation-level artifacts (queries, selected chunks, answer, feedback) as a first-class memory store which can be used in future queries.

**Deliverables:**
- Memory schema for persistent storage (query text, timestamp, retrieved chunk ids, answer, feedback, importance score).
- APIs to list, edit, delete, and export memory entries.
- UI view (Memory Inspector) allowing manual promotion/demotion of items into persistent memory.

**Tests before moving on:**
1. **CRUD test:** create, read, update, delete memory entries and ensure persistence across restarts.
2. **Recall test:** a repeated query that should benefit from memory returns improved retrieval ranking (as defined by simple heuristic).
3. **Privacy test:** deletion removes memory from index and disk; exported memory matches the expected structure.

**Acceptance criteria:**
- Memory CRUD operations are reliable and deletion/export behaviors are auditable.

**Important gating rule:** do not allow automatic memory promotion until manual promotion & feedback loops are verified.

---

# Stage 5 — Reflection Agent & Verification (Gate 5)

**Purpose:** introduce a verifier that checks generator outputs against retrieved sources and triggers regeneration or escalation when discrepancies are detected.

**Deliverables:**
- Reflection module that: analyzes claims in the answer, computes coverage against retrieved chunks, and returns a verification result with unsupported sentence highlights.
- Regeneration policy and fallback escalation (e.g., broaden retrieval, call stronger model, or answer "I don't know").
- UI annotations showing which sentence is unsupported and which chunk would support it (if any).

**Tests before moving on:**
1. **Detection test:** deliberately craft questions that induce hallucination and verify the reflection agent flags unsupported claims.
2. **Regeneration test:** when flagged, confirm regeneration uses broadened retrieval and either corrects the answer or gracefully refuses.
3. **False positive check:** ensure the reflection agent does not overflag correct, paraphrased answers as unsupported.

**Acceptance criteria:**
- The reflection agent reduces measurable hallucination on the test set vs. the baseline RAG (use your defined metric: hallucination rate or factuality score).

**NOTE:** reflection logic should be explainable and deterministic for auditability.

---

# Stage 6 — Orchestration, Caching & Logging (Gate 6)

**Purpose:** make the pipeline robust, observable, and performant via caching and async orchestration.

**Deliverables:**
- Orchestrator that sequences ingestion, retrieval, generation, reflection, and memory updates.
- Cache layer for embeddings, retrieval results, and recent queries.
- Structured logs and traces for every query (intent, retrieved chunk ids, model used, reflection verdict).

**Tests before moving on:**
1. **Cache correctness test:** repeated identical queries should hit cache and return identical results.
2. **Failure recovery test:** simulate partial failure (embedding service down) and verify graceful fallback/retry.
3. **Trace completeness test:** for a sample of queries, logs must include required fields for debugging.

**Acceptance criteria:**
- Orchestration handles concurrent queries without undefined states; logs are complete and searchable.

---

# Stage 7 — Frontend & UX (Gate 7)

**Purpose:** deliver a usable interface that showcases provenance, memory editing, and the reflection workflow.

**Deliverables:**
- Query UI with: answer panel, provenance panel (chunk snippets + source links + similarity scores), and feedback buttons.
- Memory Inspector: timeline view, edit, export, delete.
- Explain button: show retrieval reasoning and why chunks were chosen.
- Correction flow: user highlights wrong sentence → system logs correction, reruns reflection/regeneration.

**Tests before moving on:**
1. **UX flow test:** follow a defined scenario (ingest → query → flag hallucination → correct) and ensure all UI states work and backend changes are correct.
2. **Accessibility & responsiveness check:** UI usable on typical screen sizes, and essential controls reachable.
3. **Security test:** ensure UI actions require auth and cannot access other users' memory.

**Acceptance criteria:**
- Key user flows are smooth and audit trails exist for edits and corrections.

---

# Stage 8 — Security, Privacy & Compliance (Gate 8)

**Purpose:** harden the product to protect private memory and provide legal compliance controls.

**Deliverables:**
- Encryption at rest for memory and sensitive files.
- HTTPS for remote access; token/JWT-based auth for APIs.
- Memory export and permanent deletion tools (auditable).
- Configurable privacy policy: allow user to opt-in/opt-out of web ingestion and cloud LLM usage.

**Tests before moving on:**
1. **Encryption validation:** decryptable only by authorized process.
2. **Auth test:** unauthenticated requests denied; role-based access control enforced.
3. **GDPR-style test:** request memory export & deletion; confirm completion and logs.

**Acceptance criteria:**
- Security controls pass threat-model checklist and privacy controls operate as intended.

---

# Stage 9 — Observability & Metrics (Gate 9)

**Purpose:** measure system health and model quality; provide dashboards and alerts.

**Deliverables:**
- Dashboard for: query volume, median latency, hallucination rate, memory growth, cache hit rate.
- Alerts for errors, storage saturation, and abnormal hallucination spikes.
- Scheduled offline job for periodic evaluation on the testset to track factuality improvements.

**Tests before moving on:**
- Dashboard reflects live metrics; scheduled evaluation completes and stores results.

**Acceptance criteria:**
- Stakeholders can view trends for production decisions and QA.

---

# Stage 10 — Deployment & Remote Access (Gate 10)

**Purpose:** allow remote access without keeping your laptop on, while enforcing offline/private memory rules.

**Deliverables:**
- Deployment option(s) documented: self-hosted VM, containerized deployment, or hybrid.
- Remote access via HTTPS + API keys; local memory remains encrypted on server volume.
- Configurable web-fetch rules: auto-fetch on low-confidence, manual-fetch by user, or disabled.

**Tests before moving on:**
1. **Remote connectivity test:** access the service from an external network and perform full query flows.
2. **Privacy test:** remote query does NOT transmit private memory outside the server and web-fetched docs are transient unless explicitly ingested.

**Acceptance criteria:**
- Secure, remote access working and privacy controls verified.

---

# Stage 11 — Scaling & Optimization (Gate 11)

**Purpose:** prepare EideticRAG to handle larger data volumes and more users.

**Deliverables & tactics:**
- Vector index sharding or migration path to managed DB (Weaviate/Milvus) if needed.
- Model offload strategies: CPU/GPU hybrid, quantized models, or cloud LLM for heavy loads.
- Batched embedding and async backfill jobs for large ingestion.

**Tests before moving on:**
- Stress test with synthetic load to validate index performance & cache behavior.

**Acceptance criteria:**
- System demonstrates acceptable behavior under the defined load thresholds.

---

# Stage 12 — Final QA, Documentation & Demo (Gate 12)

**Purpose:** polish, document, and prepare for a public demo or handoff.

**Deliverables:**
- Comprehensive README, architecture diagram, and runbook.
- Demo script that showcases ingest → query → memory edit → reflection → export.
- Example metrics comparing baseline RAG vs EideticRAG factuality/hallucination.

**Final tests:**
- Full E2E demo executed by a third party using the provided runbook.

**Acceptance criteria:**
- Demo succeeds end-to-end and stakeholders confirm acceptance criteria.

---

# Cross-stage: Testing strategy (applies at all gates)

1. **Unit tests** for each component (ingestor, chunker, embeddings, memory CRUD).
2. **Integration tests** for component interactions (ingest → index → retrieve → generate).
3. **E2E tests** for user flows (ingest → query → reflection → memory). Maintain a small CI harness to run critical tests on code changes.
4. **Regression & evaluation**: maintain a benchmark set with labeled expected chunk ids and answers; run nightly/before merges to detect regressions.

**Metrics to collect:** retrieval precision@k, factuality (percent of answer sentences with source support), latency P50/P95, user feedback % helpful, memory growth rate.

---

# Operational & governance checklist

- Encryption keys management plan.
- Backup strategy for indexes and memory (encrypted snapshots).
- Incident response plan for accidental data leaks.
- Clear user-facing docs about what is stored and how to delete/export it.

---

# Minimal viable acceptance checklist (short)

Before you call a build "MVP":
- Ingested docs can be retrieved deterministically.
- Query endpoint returns answers with provenance.
- Reflection agent flags unsupported claims and triggers regeneration.
- Memory CRUD exists with delete/export functionality.
- Secure remote access configured (if you want remote use).

---

# Next actions I can take immediately (tell me which one):
- Convert this plan into a short PRD (product requirements doc) with stakeholder-focused language.
- Create a starter checklist + sample dataset so you can begin Stage 1 instantly.
- Scaffold a repo structure and file templates (no code) to map to the plan.

---

*End of plan.*

If you want this as a downloadable markdown file or want me to scaffold the repo templates now, say which option and I’ll generate it.

