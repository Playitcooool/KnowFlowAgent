from __future__ import annotations

from pathlib import Path

from app.llm import LLMClient
from app.schemas.document import Manifest
from app.text_utils import score_text, tokenize, top_terms


class QueryRewriter:
    def __init__(
        self,
        knowledge_base_dir: Path | None = None,
        manifest: Manifest | None = None,
        llm: LLMClient | None = None,
    ):
        self.knowledge_base_dir = knowledge_base_dir
        self.manifest = manifest or Manifest()
        self.llm = llm

    async def rewrite(
        self,
        query: str,
        target_dirs: list[str] | None = None,
        n: int = 5,
        retry_level: int = 1,
    ) -> list[str]:
        if self.llm and self.llm.available:
            queries = await self._llm_rewrite(query, target_dirs or [], n, retry_level)
            if queries:
                return queries
        return self._heuristic_rewrite(query, target_dirs, n, retry_level)

    def _heuristic_rewrite(
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

    async def _llm_rewrite(self, query: str, target_dirs: list[str], n: int, retry_level: int) -> list[str]:
        result = await self.llm.complete_json(
            system=(
                "You rewrite a user question into concise keyword search queries for ripgrep over Markdown. "
                "Use the supplied knowledge-base metadata and return only a JSON array of strings. "
                "Include the original user query first."
            ),
            user=str(
                {
                    "query": query,
                    "target_dirs": target_dirs,
                    "retry_level": retry_level,
                    "max_queries": n,
                    "manifest_context": self._manifest_context(target_dirs),
                    "index_context": self._index_text(target_dirs)[:6000],
                }
            ),
        )
        if not isinstance(result, list):
            return []
        queries = [str(item) for item in result]
        if query not in queries:
            queries.insert(0, query)
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

    def _manifest_context(self, target_dirs: list[str]) -> list[dict[str, object]]:
        target_set = set(target_dirs)
        context = []
        for doc in self.manifest.documents:
            path_parts = Path(doc.path).parts
            in_target = bool(target_set & doc.all_categories) or bool(path_parts and path_parts[0] in target_set)
            if target_set and not in_target:
                continue
            context.append(
                {
                    "path": doc.normalized_path(),
                    "title": doc.title,
                    "summary": doc.summary,
                    "tags": doc.tags,
                    "categories": sorted(doc.all_categories),
                }
            )
        return context[:80]

    def _unique(self, values: list[str]) -> list[str]:
        seen = set()
        out = []
        for value in values:
            normalized = " ".join(value.split())
            if normalized and normalized.lower() not in seen:
                seen.add(normalized.lower())
                out.append(normalized)
        return out
