# KnowFlow Agent

KnowFlow Agent is an explainable enterprise knowledge QA system built around Markdown files, generated indexes, Pi SDK-backed agent stages, parallel `ripgrep` retrieval, context expansion, evidence ranking, verification, and adaptive retry.

The primary implementation is TypeScript/Node and uses `@earendil-works/pi-coding-agent` as the agent SDK. Agent stages fall back to deterministic local logic when no configured API key is available.

## Project Structure

```text
src/
  cli.ts                  Command-line entrypoint
  server.ts               HTTP API
  workflow.ts             Adaptive query workflow
  piAgentClient.ts        Pi SDK adapter
  agents/                 Router, rewriter, answer, verifier
  retrieval/              Grep, context expansion, evidence ranking
  ingestion/              Conversion, metadata extraction, index builder
knowledge_base/           Generated Markdown KB and indexes
eval_set/                 Evaluation examples
```

## Install

```bash
npm install
npm run build
```

`ripgrep` is recommended. If `rg` is unavailable, KnowFlow falls back to a Node-based Markdown searcher.

## Ingest Documents

Place raw files under `data/raw/`, then run:

```bash
npm run dev -- ingest --raw-dir data/raw --markdown-dir data/markdown --kb-dir knowledge_base
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
npm run dev -- ask "Who approves travel reimbursement over 5000 yuan?"
npm run dev -- ask "How do new employees request GitHub repository access?" --json
```

## Run API

```bash
npm run build
node -e 'import("./dist/server.js").then(({ createServer }) => createServer().listen(8000))'
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
- Pi SDK-backed query router and file router
- Pi SDK-backed query rewriting
- Parallel grep/ripgrep retrieval
- Context expansion with line numbers
- Evidence ranking and deduplication
- Pi SDK-backed grounded answers with file-line citations
- Pi SDK-backed evidence verification and adaptive retry
