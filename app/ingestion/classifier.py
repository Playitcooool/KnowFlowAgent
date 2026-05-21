from __future__ import annotations

import hashlib
from pathlib import Path

from app.schemas.document import DocumentMetadata
from app.text_utils import infer_categories, slugify, summarize_markdown, title_from_markdown, top_terms


class MetadataExtractor:
    def extract(self, path: Path, source: str | None = None) -> DocumentMetadata:
        text = path.read_text(encoding="utf-8", errors="replace")
        front_matter = self._front_matter(text)
        title = front_matter.get("title") or title_from_markdown(path, text)
        summary = front_matter.get("summary") or summarize_markdown(text)
        tags = self._list_value(front_matter.get("tags")) or top_terms(text, limit=10)
        departments = self._list_value(front_matter.get("departments"))
        doc_type = front_matter.get("doc_type") or "document"
        categories = self._list_value(front_matter.get("categories")) or infer_categories(" ".join([title, summary, *tags, text[:4000]]))
        primary = front_matter.get("primary_category") or categories[0]
        secondary = [category for category in categories if category != primary]
        doc_id = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
        return DocumentMetadata(
            id=f"doc_{doc_id}",
            path=str(path),
            title=title,
            summary=summary,
            tags=tags,
            departments=departments,
            doc_type=doc_type,
            source=front_matter.get("source") or source,
            updated_at=front_matter.get("updated_at"),
            primary_category=slugify(primary),
            secondary_categories=[slugify(item) for item in secondary],
        )

    def _front_matter(self, text: str) -> dict[str, str]:
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return {}
        data: dict[str, str] = {}
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip().strip("\"'")
        return data

    def _list_value(self, value: str | None) -> list[str]:
        if not value:
            return []
        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            stripped = stripped[1:-1]
        return [item.strip().strip("\"'") for item in stripped.split(",") if item.strip()]

