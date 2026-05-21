# TypeScript Implementation Guide

`src/` is the primary KnowFlow implementation.

## Responsibilities

- `cli.ts`: command-line entrypoint.
- `server.ts`: small HTTP API.
- `workflow.ts`: adaptive QA orchestration.
- `piAgentClient.ts`: Pi SDK adapter loaded from `config.yaml`.
- `agents/`: Pi SDK-backed router, file router, rewriter, answerer, and verifier.
- `ingestion/`: document conversion, metadata extraction, and KB index building.
- `retrieval/`: ripgrep search, context expansion, and evidence ranking.
- `types.ts`: shared runtime contracts.

## Local Rules

- Agent stages should use `PiAgentClient` and preserve deterministic fallback behavior.
- Keep generated KB paths relative to the knowledge-base root.
- Preserve file-line citations through retrieval, ranking, answering, and verification.
- Do not read API keys directly in agents; `PiAgentClient` owns config and environment access.
- Use `npm run build` and `npm test` before handing off behavior changes.
