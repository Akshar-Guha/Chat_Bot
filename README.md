# EideticRAG - Retrieval-Augmented Generation System

EideticRAG is a modular Retrieval-Augmented Generation (RAG) stack that combines
document ingestion, semantic search, optional memory persistence, and multiple
generation back-ends. The repository currently contains both the production
pipeline (under `src/`) and an in-progress FastAPI refactor (under
`eidetic_rag/backend/`).

## 🏗️ Architecture Overview

### High-level layout

```text
src/
├── api/             # FastAPI application (current production entrypoint)
├── core/            # Document ingestion, chunking, embeddings, vector index
├── generation/      # RAG pipeline and LLM generator integrations
├── memory/          # SQLite-backed long-term memory manager
├── orchestration/   # End-to-end controller (retrieval + reflection + memory)
├── reflection/      # Verification and reflection agent
├── retrieval/       # Intent-aware retrieval controller
└── frontend/        # React dashboard (CRA-based)

eidetic_rag/backend/ # New FastAPI service under active development
```

Key data flow:

1. `core.ingestor.DocumentIngestor` loads PDF/TXT/HTML/Markdown sources and
   returns structured documents (@src/core/ingestor.py#1-134).
2. `core.chunker.TextChunker` splits documents into overlapping chunks with rich
   metadata (@src/core/chunker.py#1-246).
3. `core.embeddings.EmbeddingGenerator` embeds chunks via
   `sentence-transformers` and persists cached vectors
   (@src/core/embeddings.py#1-209).
4. `core.vector_index.VectorIndex` stores embeddings in ChromaDB for semantic
   retrieval (@src/core/vector_index.py#1-315).
5. `generation.rag_pipeline.RAGPipeline` orchestrates retrieval,
   generation, and provenance formatting (@src/generation/rag_pipeline.py#1-278).
6. Optional modules extend the pipeline with intent-aware retrieval
   (@src/retrieval/retrieval_controller.py#1-431), reflection-driven
   verification (@src/reflection/reflection_agent.py#1-355), and persistent
   memory via SQLite/SQLAlchemy (@src/memory/memory_manager.py#1-517).

### FastAPI backends

* **Current API** – `python -m src.api.main`
  * Endpoints: `/query`, `/ingest`, `/stats`, `/model/info`, `/index/clear`
  * Uses the orchestration pipeline (`generation.rag_pipeline.RAGPipeline`) for
    inference.

* **Refactor (WIP)** – `eidetic_rag/backend/app/main.py`
  * Domain-driven module layout with dependency-managed services and Pydantic
    schemas. This backend is still being wired into the production pipeline.

## 🚀 Key Features

### Core capabilities

* **Multi-format ingestion** – TXT, Markdown, HTML, and PDF via
  `DocumentIngestor`.
* **Configurable chunking** – Paragraph-aware splitting with overlap and
  metadata capture.
* **Semantic retrieval** – Persistent ChromaDB index with collection recovery
  safeguards.
* **LLM integration** – Local Ollama, Hugging Face endpoints, or mock mode via
  `generation.generator.LLMGenerator`.
* **Optional reflection** – Verification engine evaluates hallucination score
  and can trigger regeneration or refusal.

* **Persistent memory** – SQLite database managed through SQLAlchemy models for
  storing past Q&A pairs.

### Frontend

* React 18 + TypeScript single-page app (Create React App) located in
  `src/frontend/` with Material UI components.
* Proxy configured to hit the FastAPI backend during development.

## 🛠️ Quick Start

### Prerequisites

* Python 3.9+
* Node.js 16+
* (Optional) [Ollama](https://ollama.ai/) for local LLM inference

### Backend setup (current pipeline)

```bash
# From the project root
python -m venv .venv
.venv\Scripts\activate  # On Windows

pip install -r requirements.txt

# Launch FastAPI
python -m src.api.main
```

* API docs: http://localhost:8000/docs
* RAG endpoints exposed under the root path.

### Backend setup (experimental refactor)

```bash
# Optional: run the new service once dependencies are installed
python -m uvicorn eidetic_rag.backend.app.main:app --reload
```
The refactor currently boots with mock services until the orchestration layer is
fully integrated.

### Frontend setup

```bash
cd src/frontend
npm install
npm start
```

The development server proxies API calls to <http://localhost:8000>.

## 📚 CLI Utilities

`src/core/cli.py` exposes ingestion, reindex, inspect, and search commands.
Example:

```bash
python -m src.core.cli ingest data/sample_documents/sample1.txt
python -m src.core.cli search "What is machine learning?"
```

## 🧪 Testing

The `tests/` directory contains staged integration suites covering ingestion,
retrieval, reflection, orchestration, and frontend smoke checks.

```bash
python -m pytest tests -v
```

Individual stage modules (e.g., `tests/test_stage5.py`) exercise dedicated
subsystems such as the reflection agent.

## ⚙️ Configuration Notes

* Environment variables for the legacy API are read via `python-dotenv` in
  `src/api/main.py`. Override behaviour with:
  * `RAG_GENERATOR_TYPE`, `RAG_MODEL_NAME`, `RAG_API_KEY`, `RAG_API_BASE`,
    `RAG_TEMPERATURE`, `RAG_TOP_P`, `RAG_MAX_TOKENS`.
* The new backend loads settings from `.env` using
  `eidetic_rag.backend.config.settings.Settings`.
* Memory persistence defaults to `./memory.db`. Delete the file to reset stored
  conversations.

## 🔄 Project Status

* **Stable**: Core ingestion, embedding, indexing, RAG pipeline, CLI, legacy
  FastAPI API, React frontend, staged test harness.
* **In progress**: Integration between the new FastAPI service (`eidetic_rag`)
  and the production pipeline, expanded model metadata endpoints, streaming
  responses.

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch.
3. Make changes and add/adjust tests.
4. Submit a pull request describing the affected pipeline stage(s).

## 📄 License

This project is licensed under the MIT License.
