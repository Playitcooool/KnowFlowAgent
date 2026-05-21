# Knowledge Base Guide

`knowledge_base/` is the generated, searchable Markdown knowledge base.

## Expected Generated Structure

- `index.md`: root topic index used by routing.
- `manifest.json`: serialized document metadata used by routing and ranking.
- `<category>/local_index.md`: category-level index.
- `<category>/<document>.md`: searchable Markdown source documents.

## Local Rules

- Treat this folder as generated output from `knowflow ingest` or `IndexBuilder`.
- Keep document files Markdown and indexes human-readable.
- Preserve relative paths because citations and manifest entries depend on them.
- Do not put raw source documents here; raw inputs belong under a raw data directory before ingestion.
- If editing fixtures manually, update `manifest.json` and indexes so routing remains coherent.

