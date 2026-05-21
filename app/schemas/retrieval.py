from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RouteDecision:
    target_dirs: list[str] = field(default_factory=list)
    target_files: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class GrepHit:
    file: str
    line_number: int
    line_text: str
    query: str
    matched_terms: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    file: str
    line_start: int
    line_end: int
    score: float
    text: str
    matched_terms: list[str] = field(default_factory=list)

    def citation(self) -> str:
        if self.line_start == self.line_end:
            return f"{self.file}:{self.line_start}"
        return f"{self.file}:{self.line_start}-{self.line_end}"


@dataclass
class SearchTrace:
    retry_level: int
    target_dirs: list[str] = field(default_factory=list)
    target_files: list[str] = field(default_factory=list)
    rewritten_queries: list[str] = field(default_factory=list)
    evidence_count: int = 0
    reason: str = ""
