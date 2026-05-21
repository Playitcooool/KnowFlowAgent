# App Package Guide

`app/` contains the runtime implementation for the KnowFlow Agent package.

## Responsibilities

- `main.py`: FastAPI application and HTTP request/response models.
- `cli.py`: console entrypoint registered as `knowflow`.
- `workflow.py`: top-level adaptive QA orchestration.
- `config.py`: lightweight runtime settings dataclass.
- `text_utils.py`: shared tokenization, scoring, category inference, and Markdown helpers.
- `agents/`: deterministic routing, rewriting, answering, and verification components.
- `retrieval/`: grep search, context expansion, and evidence ranking.
- `ingestion/`: source conversion, metadata extraction, and index writing.
- `schemas/`: dataclass contracts shared across components.

## Local Rules

- Keep imports absolute from `app...` unless there is a strong local reason.
- Avoid putting business logic in `main.py` or `cli.py`; delegate to workflow or package classes.
- Keep `KnowFlowWorkflow` as the composition root for query answering.
- When adding settings, update `Settings` and all CLI/API call sites that need override behavior.
- Do not introduce heavyweight runtime services unless the project explicitly opts into them.

## Testing Notes

- Workflow changes should be covered with temporary knowledge bases in tests.
- API handlers should stay thin enough that most behavior can be tested without starting a server.

