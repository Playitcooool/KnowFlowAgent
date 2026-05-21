from __future__ import annotations

from pathlib import Path

from app.schemas.document import Manifest
from app.text_utils import score_text, tokenize


class FileRouter:
    def __init__(self, knowledge_base_dir: Path, manifest: Manifest):
        self.knowledge_base_dir = knowledge_base_dir
        self.manifest = manifest

    def route(self, query: str, target_dirs: list[str], retry_level: int = 1) -> list[str]:
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

