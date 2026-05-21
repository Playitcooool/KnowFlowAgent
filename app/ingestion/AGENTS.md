# Ingestion Package Guide

`app/ingestion/` converts source documents into Markdown and builds the searchable knowledge base.

## Components

- `converter.py`: converts Markdown, text, HTML, JSON, PDF, and DOCX into Markdown. PDF and DOCX dependencies are optional.
- `classifier.py`: extracts metadata from front matter and document text.
- `index_builder.py`: copies Markdown into category folders and writes root/local indexes plus `manifest.json`.

## Local Rules

- Keep ingestion best-effort. Optional conversion failures should produce explanatory Markdown rather than crashing the whole pipeline.
- Preserve front matter support for `title`, `summary`, `tags`, `departments`, `doc_type`, `categories`, `primary_category`, `source`, and `updated_at`.
- Use `slugify` for category and path-safe names.
- Keep `manifest.json` consistent with files copied into `knowledge_base/`.
- Avoid deleting existing generated files unless the command explicitly owns a full rebuild behavior.

## Testing Notes

- Prefer temporary raw, markdown, and knowledge-base directories.
- Cover metadata extraction and index output when changing categorization.

