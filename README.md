# KnowFlow Agent

KnowFlow Agent is an explainable enterprise knowledge QA system built around Markdown files, generated indexes, keyword query rewriting, parallel `ripgrep` retrieval, context expansion, evidence ranking, verification, and adaptive retry.

The implementation is filesystem-first and works without a vector database. LLM-style components are isolated as agents with deterministic defaults, so the project runs locally and can later be swapped to hosted model calls.

## Project Structure

```text
app/
  main.py                 FastAPI API
  cli.py                  Command-line entrypoint
  workflow.py             Adaptive query workflow
  agents/                 Router, rewriter, answer, verifier
  retrieval/              Grep, context expansion, evidence ranking
  ingestion/              Conversion, metadata extraction, index builder
  schemas/                Pydantic models
knowledge_base/           Generated Markdown KB and indexes
eval_set/                 Evaluation examples
tests/                    Unit tests
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ingestion]"
```

`ripgrep` is recommended. If `rg` is unavailable, KnowFlow falls back to a Python searcher.

## Ingest Documents

Place raw files under `data/raw/`, then run:

```bash
knowflow ingest --raw-dir data/raw --markdown-dir data/markdown --kb-dir knowledge_base
```

Supported inputs include Markdown, text, HTML, JSON, PDF, and DOCX. PDF and DOCX conversion use optional dependencies and fall back to an explanatory Markdown file if those dependencies are missing.

The ingestion pipeline generates:

```text
knowledge_base/index.md
knowledge_base/manifest.json
knowledge_base/<category>/local_index.md
knowledge_base/<category>/<document>.md
```

## Ask Questions

```bash
knowflow ask "Who approves travel reimbursement over 5000 yuan?"
knowflow ask "How do new employees request GitHub repository access?" --json
```

## Run API

```bash
uvicorn app.main:app --reload
```

Endpoints:

- `GET /health`
- `GET /manifest`
- `POST /ingest`
- `POST /query` with `{"query": "..."}`

## Design Coverage

Implemented MVP components:

- Document conversion into Markdown
- Metadata extraction and multi-label categorization
- Root and folder-level index generation
- Manifest generation
- Query router and file router
- Query rewriting
- Parallel grep/ripgrep retrieval
- Context expansion with line numbers
- Evidence ranking and deduplication
- Grounded answers with file-line citations
- Evidence verification and adaptive retry

