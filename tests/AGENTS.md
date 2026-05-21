# Tests Guide

`tests/` contains focused pytest coverage for ingestion, retrieval, context expansion, and end-to-end workflow behavior.

## Local Rules

- Use `tmp_path` for generated Markdown and knowledge-base fixtures.
- Keep tests deterministic and independent of external services.
- Prefer small inline Markdown fixtures that exercise file paths, metadata, routing, and citations.
- When behavior changes, assert user-visible outputs plus the trace or citation fields that explain them.

## Commands

- Full suite: `rtk pytest`
- Single test file: `rtk pytest tests/test_workflow.py`

