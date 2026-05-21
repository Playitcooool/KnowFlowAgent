from __future__ import annotations

from pathlib import Path

from app.schemas.document import Manifest
from app.text_utils import score_text, tokenize, top_terms


class QueryRewriter:
    def __init__(self, knowledge_base_dir: Path | None = None, manifest: Manifest | None = None):
        self.knowledge_base_dir = knowledge_base_dir
        self.manifest = manifest or Manifest()

    def rewrite(
        self,
        query: str,
        target_dirs: list[str] | None = None,
        n: int = 5,
        retry_level: int = 1,
    ) -> list[str]:
        terms = tokenize(query)
        queries = [query]
        if terms:
            queries.append(" ".join(terms))

        context_terms = self._context_terms(query, target_dirs or [], limit=12 if retry_level < 3 else 20)
        if context_terms:
            queries.append(" ".join(dict.fromkeys([*terms, *context_terms[:6]])))
            queries.extend(context_terms[:3])

        if retry_level >= 2 and terms:
            queries.extend(terms)
        if retry_level >= 3 and context_terms:
            queries.extend(context_terms[3:8])
        if retry_level >= 4:
            queries.append(" ".join(terms[: max(1, len(terms) // 2)]))
        return self._unique(queries)[:n]

    def _context_terms(self, query: str, target_dirs: list[str], limit: int) -> list[str]:
        query_terms = set(tokenize(query))
        ranked_docs = []
        target_set = set(target_dirs)
        for doc in self.manifest.documents:
            path_parts = Path(doc.path).parts
            in_target = bool(target_set & doc.all_categories) or bool(path_parts and path_parts[0] in target_set)
            if target_set and not in_target:
                continue
            text = " ".join(
                [
                    doc.title,
                    doc.summary,
                    *doc.tags,
                    *doc.departments,
                    doc.doc_type,
                    doc.primary_category,
                    *doc.secondary_categories,
                ]
            )
            ranked_docs.append((score_text(query_terms, text), text))

        ranked_docs.sort(key=lambda item: item[0], reverse=True)
        source_text = " ".join(text for _, text in ranked_docs[:8])
        source_text = " ".join([source_text, self._index_text(target_dirs)])
        terms = [term for term in top_terms(source_text, limit=limit * 2) if term not in query_terms]
        return terms[:limit]

    def _index_text(self, target_dirs: list[str]) -> str:
        if not self.knowledge_base_dir:
            return ""
        chunks = []
        for directory in target_dirs:
            local_index = self.knowledge_base_dir / directory / "local_index.md"
            if local_index.exists():
                chunks.append(local_index.read_text(encoding="utf-8", errors="replace"))
        return "\n".join(chunks)

    def _unique(self, values: list[str]) -> list[str]:
        seen = set()
        out = []
        for value in values:
            normalized = " ".join(value.split())
            if normalized and normalized.lower() not in seen:
                seen.add(normalized.lower())
                out.append(normalized)
        return out
