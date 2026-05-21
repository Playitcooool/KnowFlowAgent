from __future__ import annotations

import json
import shutil
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

from app.ingestion.classifier import MetadataExtractor
from app.schemas.document import DocumentMetadata, Manifest
from app.text_utils import CATEGORY_KEYWORDS, slugify


class IndexBuilder:
    def __init__(self, knowledge_base_dir: Path):
        self.knowledge_base_dir = knowledge_base_dir
        self.extractor = MetadataExtractor()

    def build_from_markdown(self, markdown_dir: Path) -> Manifest:
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        documents: list[DocumentMetadata] = []
        for source in sorted(markdown_dir.rglob("*.md")):
            extracted = self.extractor.extract(source, source=str(source))
            category = slugify(extracted.primary_category)
            target = self.knowledge_base_dir / category / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            metadata = replace(extracted, path=str(target.relative_to(self.knowledge_base_dir)))
            documents.append(metadata)
        manifest = Manifest(documents=documents)
        self.write_indexes(manifest)
        return manifest

    def write_indexes(self, manifest: Manifest) -> None:
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        grouped: dict[str, list[DocumentMetadata]] = defaultdict(list)
        for doc in manifest.documents:
            for category in doc.all_categories:
                grouped[category].append(doc)
        for category, docs in grouped.items():
            folder = self.knowledge_base_dir / category
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "local_index.md").write_text(self._local_index(category, docs), encoding="utf-8")
        (self.knowledge_base_dir / "index.md").write_text(self._root_index(grouped), encoding="utf-8")
        (self.knowledge_base_dir / "manifest.json").write_text(
            json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _root_index(self, grouped: dict[str, list[DocumentMetadata]]) -> str:
        lines = ["# Enterprise Knowledge Base Index", ""]
        for category in sorted(grouped):
            docs = grouped[category]
            summaries = " ".join(doc.summary for doc in docs if doc.summary)
            keywords = sorted({tag for doc in docs for tag in doc.tags} | CATEGORY_KEYWORDS.get(category, set()))
            lines.extend(
                [
                    f"## {category}",
                    "",
                    summaries[:500] or f"Documents related to {category}.",
                    "",
                    f"Typical keywords: {', '.join(keywords[:20])}.",
                    "",
                ]
            )
        return "\n".join(lines)

    def _local_index(self, category: str, docs: list[DocumentMetadata]) -> str:
        lines = [f"# {category.title()} Local Index", ""]
        for doc in sorted(docs, key=lambda item: item.path):
            lines.extend([f"## {Path(doc.path).name}", doc.summary or doc.title, ""])
        return "\n".join(lines)


def load_manifest(knowledge_base_dir: Path) -> Manifest:
    path = knowledge_base_dir / "manifest.json"
    if not path.exists():
        return Manifest()
    return Manifest.model_validate_json(path.read_text(encoding="utf-8"))
