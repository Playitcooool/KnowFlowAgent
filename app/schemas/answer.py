from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace

from app.schemas.retrieval import SearchTrace


@dataclass
class Citation:
    file: str
    line_start: int
    line_end: int


@dataclass
class Verification:
    answerable: bool
    confidence: float
    evidence_files: list[str] = field(default_factory=list)
    missing_info: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class Answer:
    query: str
    answer: str
    citations: list[Citation] = field(default_factory=list)
    confidence: float = 0.0
    answerable: bool = False
    trace: list[SearchTrace] = field(default_factory=list)

    def model_copy(self, update: dict | None = None) -> "Answer":
        return replace(self, **(update or {}))

    def model_dump(self) -> dict:
        return asdict(self)
