@/Users/weiciruan/.codex/RTK.md

# KnowFlow Agent Repository Guide

KnowFlow Agent is a filesystem-first, explainable enterprise QA system. The primary implementation is now TypeScript/Node with Pi SDK-backed agent stages. It converts source documents to Markdown, builds a human-readable knowledge base, routes questions to likely folders/files, retrieves evidence with ripgrep or a Node fallback, expands line context, ranks evidence, composes an answer, verifies support, and retries with broader search when needed.

## Core Flow

1. `src/ingestion/converter.ts` converts raw files to Markdown.
2. `src/ingestion/indexBuilder.ts` copies Markdown into `knowledge_base/`, writes `index.md`, folder `local_index.md` files, and `manifest.json`.
3. `src/workflow.ts` orchestrates routing, rewriting, retrieval, context expansion, ranking, answer generation, verification, and retry.
4. `src/piAgentClient.ts` wraps `@earendil-works/pi-coding-agent`.
5. `src/cli.ts` exposes the `knowflow ingest` and `knowflow ask` commands.

## Engineering Conventions

- Use Node 22+ and keep dependencies aligned with `package.json`.
- Prefer Pi SDK-backed agent behavior with deterministic local fallbacks.
- Preserve line-level traceability. Retrieval and answers should keep file paths and line ranges stable.
- Keep generated knowledge-base files plain Markdown or JSON.
- Keep shared TypeScript interfaces in `src/types.ts`.
- Run shell commands with the `rtk` prefix.

## Verification

- Run `rtk npm test` for the TypeScript test suite.
- For ingestion or retrieval changes, add or update focused tests under `src/__tests__/`.
- For API changes, verify both the HTTP server route and the underlying workflow behavior.

## Important Files

- `README.md`: user-facing overview and commands.
- `knowflow_agent_design.md`: architecture and design rationale.
- `package.json`: Node package metadata, dependencies, CLI bin, and scripts.
- `config.yaml`: provider API-key configuration template; do not hardcode real secrets.
