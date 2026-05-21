from __future__ import annotations

from pathlib import Path

from app.schemas.document import Manifest
from app.schemas.retrieval import RouteDecision
from app.text_utils import score_text, slugify, tokenize


class QueryRouter:
    def __init__(self, knowledge_base_dir: Path, manifest: Manifest):
        self.knowledge_base_dir = knowledge_base_dir
        self.manifest = manifest

    def route(self, query: str, retry_level: int = 1) -> RouteDecision:
        query_terms = set(tokenize(query))
        candidates: dict[str, float] = {}
        for folder in self._indexed_dirs():
            text = self._read_index_text(folder)
            scores = [score_text(query_terms, text)]
            for doc in self.manifest.documents:
                if folder in doc.all_categories or Path(doc.path).parts[:1] == (folder,):
                    scores.append(score_text(query_terms, " ".join([doc.title, doc.summary, *doc.tags])))
            candidates[folder] = max(scores or [0.0])

        ranked = sorted(candidates.items(), key=lambda item: item[1], reverse=True)
        if retry_level >= 4:
            dirs = [name for name, _ in ranked] or self._fallback_dirs()
            reason = "Full indexed-folder search because retry level requests a broader scope."
        else:
            limit = 2 if retry_level <= 1 else 4
            dirs = [name for name, score in ranked if score > 0][:limit]
            if not dirs:
                dirs = [name for name, _ in ranked[:limit]] or self._fallback_dirs()
            reason = "Selected folders from the root index by matching index text and manifest metadata."
        return RouteDecision(target_dirs=dirs, reason=reason)

    def _read_index_text(self, folder: str) -> str:
        chunks = [folder]
        local_index = self.knowledge_base_dir / folder / "local_index.md"
        root_section = self._root_index_section(folder)
        if root_section:
            chunks.append(root_section)
        if local_index.exists():
            chunks.append(local_index.read_text(encoding="utf-8", errors="replace"))
        return "\n".join(chunks)

    def _indexed_dirs(self) -> list[str]:
        root_index = self.knowledge_base_dir / "index.md"
        if not root_index.exists():
            return self._fallback_dirs()
        dirs = []
        for line in root_index.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("## ") and not stripped.startswith("### "):
                name = slugify(stripped.lstrip("#").strip())
                if name:
                    dirs.append(name)
        return list(dict.fromkeys(dirs)) or self._fallback_dirs()

    def _root_index_section(self, folder: str) -> str:
        root_index = self.knowledge_base_dir / "index.md"
        if not root_index.exists():
            return ""
        lines = root_index.read_text(encoding="utf-8", errors="replace").splitlines()
        section: list[str] = []
        in_section = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## ") and not stripped.startswith("### "):
                heading = slugify(stripped.lstrip("#").strip())
                if in_section:
                    break
                in_section = heading == folder
            if in_section:
                section.append(line)
        return "\n".join(section)

    def _fallback_dirs(self) -> list[str]:
        if not self.knowledge_base_dir.exists():
            return []
        return sorted(path.name for path in self.knowledge_base_dir.iterdir() if path.is_dir())
