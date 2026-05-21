from __future__ import annotations

from pathlib import Path

from app.schemas.document import Manifest
from app.schemas.retrieval import RouteDecision
from app.text_utils import CATEGORY_KEYWORDS, score_text, tokenize


class QueryRouter:
    def __init__(self, knowledge_base_dir: Path, manifest: Manifest):
        self.knowledge_base_dir = knowledge_base_dir
        self.manifest = manifest

    def route(self, query: str, retry_level: int = 1) -> RouteDecision:
        query_terms = set(tokenize(query))
        candidates: dict[str, float] = {}
        for path in self.knowledge_base_dir.iterdir() if self.knowledge_base_dir.exists() else []:
            if path.is_dir():
                text = self._read_index_text(path)
                scores = [
                    score_text(query_terms, text),
                    len(query_terms & CATEGORY_KEYWORDS.get(path.name, set())) / max(len(query_terms), 1),
                ]
                for doc in self.manifest.documents:
                    if path.name in doc.all_categories:
                        scores.append(score_text(query_terms, " ".join([doc.title, doc.summary, *doc.tags])))
                candidates[path.name] = max(scores or [0.0])

        ranked = sorted(candidates.items(), key=lambda item: item[1], reverse=True)
        if retry_level >= 4:
            dirs = [name for name, _ in ranked] or self._all_dirs()
            reason = "Full knowledge-base search because retry level requests a broader scope."
        else:
            limit = 2 if retry_level <= 1 else 4
            dirs = [name for name, score in ranked if score > 0][:limit]
            if not dirs:
                dirs = [name for name, _ in ranked[:limit]] or self._all_dirs()
            reason = "Selected folders by matching the query against root/local indexes and manifest metadata."
        return RouteDecision(target_dirs=dirs, reason=reason)

    def _read_index_text(self, folder: Path) -> str:
        chunks = [folder.name]
        root_index = self.knowledge_base_dir / "index.md"
        local_index = folder / "local_index.md"
        for path in (root_index, local_index):
            if path.exists():
                chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        return "\n".join(chunks)

    def _all_dirs(self) -> list[str]:
        if not self.knowledge_base_dir.exists():
            return []
        return sorted(path.name for path in self.knowledge_base_dir.iterdir() if path.is_dir())

