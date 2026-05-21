from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from app.schemas.retrieval import Evidence, GrepHit


class ContextReader:
    def __init__(self, knowledge_base_dir: Path):
        self.knowledge_base_dir = knowledge_base_dir

    def expand(self, hits: list[GrepHit], window_size: int = 20) -> list[Evidence]:
        grouped: dict[str, list[GrepHit]] = defaultdict(list)
        for hit in hits:
            grouped[hit.file].append(hit)

        evidence: list[Evidence] = []
        radius = max(1, window_size // 2)
        for file, file_hits in grouped.items():
            path = self.knowledge_base_dir / file
            if not path.exists():
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            ranges = []
            for hit in file_hits:
                start = max(1, hit.line_number - radius)
                end = min(len(lines), hit.line_number + radius)
                ranges.append((start, end, set(hit.matched_terms)))
            for start, end, terms in self._merge_ranges(ranges):
                text = "\n".join(f"{idx}: {lines[idx - 1]}" for idx in range(start, end + 1))
                evidence.append(
                    Evidence(
                        file=file,
                        line_start=start,
                        line_end=end,
                        score=0.0,
                        matched_terms=sorted(terms),
                        text=text,
                    )
                )
        return evidence

    def _merge_ranges(self, ranges: list[tuple[int, int, set[str]]]) -> list[tuple[int, int, set[str]]]:
        merged: list[tuple[int, int, set[str]]] = []
        for start, end, terms in sorted(ranges):
            if not merged or start > merged[-1][1] + 1:
                merged.append((start, end, set(terms)))
            else:
                old_start, old_end, old_terms = merged[-1]
                merged[-1] = (old_start, max(old_end, end), old_terms | terms)
        return merged

