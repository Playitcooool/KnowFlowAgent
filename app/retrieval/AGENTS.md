# Retrieval Package Guide

`app/retrieval/` turns rewritten queries into traceable evidence snippets.

## Components

- `grep_retriever.py`: async parallel search over Markdown files using `rg` when available, with a Python fallback.
- `context_reader.py`: expands matched lines into nearby line-numbered evidence blocks.
- `evidence_ranker.py`: deduplicates and scores evidence using query-term coverage and manifest metadata.

## Local Rules

- Preserve Markdown-only search unless a broader file contract is intentionally added.
- Keep returned file paths relative to the knowledge-base root whenever possible.
- Do not drop line numbers. Citations depend on stable `line_start` and `line_end` values.
- Treat `rg` output parsing carefully; context lines may use `-` separators while matches use `:`.
- Keep async retrieval bounded and predictable. Avoid unbounded subprocess fanout.

## Testing Notes

- Use temporary directories and small Markdown fixtures.
- Test both matching behavior and expanded evidence text when changing retrieval semantics.

