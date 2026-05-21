from __future__ import annotations

from pathlib import Path

from app.llm import LLMClient
from app.schemas.document import Manifest
from app.text_utils import score_text, tokenize


class FileRouter:
    def __init__(self, knowledge_base_dir: Path, manifest: Manifest, llm: LLMClient | None = None):
        self.knowledge_base_dir = knowledge_base_dir
        self.manifest = manifest
        self.llm = llm

    async def route(self, query: str, target_dirs: list[str], retry_level: int = 1) -> list[str]:
        if self.llm and self.llm.available:
            files = await self._llm_route(query, target_dirs, retry_level)
            if files:
                return files
        return self._heuristic_route(query, target_dirs, retry_level)

    def _heuristic_route(self, query: str, target_dirs: list[str], retry_level: int = 1) -> list[str]:
        query_terms = set(tokenize(query))
        candidates: list[tuple[float, str]] = []
        for doc in self.manifest.documents:
            path = Path(doc.path)
            in_target = path.parts and path.parts[0] in target_dirs
            categorized = bool(doc.all_categories & set(target_dirs))
            if not (in_target or categorized):
                continue
            text = " ".join([doc.title, doc.summary, *doc.tags, *doc.departments, doc.doc_type])
            candidates.append((score_text(query_terms, text), doc.normalized_path()))

        if not candidates:
            for directory in target_dirs:
                for path in (self.knowledge_base_dir / directory).glob("*.md"):
                    if path.name != "local_index.md":
                        candidates.append((0.0, str(path.relative_to(self.knowledge_base_dir))))

        candidates.sort(reverse=True)
        if retry_level >= 3:
            return [path for _, path in candidates]
        selected = [path for score, path in candidates if score > 0]
        return selected[:6] or [path for _, path in candidates[:6]]

    async def _llm_route(self, query: str, target_dirs: list[str], retry_level: int) -> list[str]:
        candidates = []
        target_set = set(target_dirs)
        for doc in self.manifest.documents:
            path = Path(doc.path)
            if target_set and not (path.parts and path.parts[0] in target_set) and not (doc.all_categories & target_set):
                continue
            candidates.append(
                {
                    "path": doc.normalized_path(),
                    "title": doc.title,
                    "summary": doc.summary,
                    "tags": doc.tags,
                    "categories": sorted(doc.all_categories),
                }
            )
        if not candidates:
            return []
        result = await self.llm.complete_json(
            system=(
                "You select the most relevant Markdown files for a question. "
                "Return only JSON with key target_files as an array of candidate paths."
            ),
            user=str(
                {
                    "query": query,
                    "retry_level": retry_level,
                    "target_dirs": target_dirs,
                    "candidate_files": candidates[:80],
                }
            ),
        )
        if not isinstance(result, dict):
            return []
        allowed = {item["path"] for item in candidates}
        files = [path for path in result.get("target_files", []) if path in allowed]
        return files if retry_level >= 3 else files[:6]
