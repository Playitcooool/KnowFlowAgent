from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path


@dataclass
class DocumentMetadata:
    id: str
    path: str
    title: str
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    departments: list[str] = field(default_factory=list)
    doc_type: str = "document"
    source: str | None = None
    updated_at: str | None = None
    primary_category: str = "general"
    secondary_categories: list[str] = field(default_factory=list)

    @property
    def all_categories(self) -> set[str]:
        return {self.primary_category, *self.secondary_categories}

    def normalized_path(self) -> str:
        return str(Path(self.path))


@dataclass
class Manifest:
    documents: list[DocumentMetadata] = field(default_factory=list)

    def model_dump(self) -> dict:
        return asdict(self)

    @classmethod
    def model_validate_json(cls, text: str) -> "Manifest":
        data = json.loads(text)
        return cls(documents=[DocumentMetadata(**item) for item in data.get("documents", [])])
