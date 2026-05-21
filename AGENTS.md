@/Users/weiciruan/.codex/RTK.md

# KnowFlow Agent Repository Guide

KnowFlow Agent is a filesystem-first, explainable enterprise QA system. It converts source documents to Markdown, builds a human-readable knowledge base, routes questions to likely folders/files, retrieves evidence with ripgrep or a Python fallback, expands line context, ranks evidence, composes an answer, verifies support, and retries with broader search when needed.

## Core Flow

1. `app.ingestion.converter.DocumentConverter` converts raw files to Markdown.
2. `app.ingestion.index_builder.IndexBuilder` copies Markdown into `knowledge_base/`, writes `index.md`, folder `local_index.md` files, and `manifest.json`.
3. `app.workflow.KnowFlowWorkflow` orchestrates routing, rewriting, retrieval, context expansion, ranking, answer generation, verification, and retry.
4. `app.main` exposes FastAPI endpoints.
5. `app.cli` exposes the `knowflow ingest` and `knowflow ask` commands.

## Engineering Conventions

- Use Python 3.13+ and keep dependencies aligned with `pyproject.toml`.
- Prefer deterministic, local behavior. LLM-like components currently use simple heuristics and should remain swappable behind small classes.
- Preserve line-level traceability. Retrieval and answers should keep file paths and line ranges stable.
- Keep generated knowledge-base files plain Markdown or JSON.
- Use dataclass schemas in `app/schemas` unless intentionally migrating the entire boundary.
- Run shell commands with the `rtk` prefix.

## Verification

- Run `rtk pytest` for the full test suite.
- For ingestion or retrieval changes, add or update focused tests under `tests/`.
- For API changes, verify both the FastAPI route and the underlying workflow behavior.

## Important Files

- `README.md`: user-facing overview and commands.
- `knowflow_agent_design.md`: architecture and design rationale.
- `pyproject.toml`: package metadata, dependencies, console script, pytest config.
- `config.yaml`: provider API-key configuration template; do not hardcode real secrets.
