# Schemas Package Guide

`app/schemas/` defines the contracts passed between ingestion, retrieval, agents, workflow, CLI, and API.

## Current Model Style

- Schemas are Python dataclasses, not Pydantic models.
- Some classes implement compatibility helpers such as `model_dump`, `model_copy`, and `model_validate_json`.

## Local Rules

- Keep schema fields serializable to plain JSON-compatible values.
- Preserve backward-compatible field names used by tests, API response models, and `manifest.json`.
- If adding fields, provide defaults when possible so existing manifests remain readable.
- Keep citation fields explicit: file, start line, and end line.
- Do not move scoring or routing logic into schemas.

