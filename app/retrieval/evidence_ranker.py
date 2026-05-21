from __future__ import annotations

from dataclasses import replace

from app.schemas.document import Manifest
from app.schemas.retrieval import Evidence
from app.text_utils import score_text, tokenize


class EvidenceRanker:
    def __init__(self, manifest: Manifest | None = None):
        self.manifest = manifest or Manifest()
        self.metadata_by_path = {doc.normalized_path(): doc for doc in self.manifest.documents}

    def rank(self, query: str, evidence: list[Evidence], top_k: int = 8) -> list[Evidence]:
        query_terms = set(tokenize(query))
        deduped = self._dedupe(evidence)
        ranked: list[Evidence] = []
        for item in deduped:
            keyword_score = score_text(query_terms, item.text)
            coverage_bonus = len(set(item.matched_terms) & query_terms) / max(len(query_terms), 1)
            metadata_bonus = self._metadata_bonus(item.file, query_terms)
            score = min(1.0, keyword_score * 0.65 + coverage_bonus * 0.25 + metadata_bonus * 0.10)
            ranked.append(replace(item, score=round(score, 4)))
        ranked.sort(key=lambda item: (item.score, len(item.matched_terms)), reverse=True)
        return ranked[:top_k]

    def _metadata_bonus(self, file: str, query_terms: set[str]) -> float:
        meta = self.metadata_by_path.get(file)
        if not meta:
            return 0.0
        text = " ".join([meta.title, meta.summary, *meta.tags, meta.primary_category, *meta.secondary_categories])
        return score_text(query_terms, text)

    def _dedupe(self, evidence: list[Evidence]) -> list[Evidence]:
        seen: set[tuple[str, int, int]] = set()
        out: list[Evidence] = []
        for item in evidence:
            key = (item.file, item.line_start, item.line_end)
            if key not in seen:
                seen.add(key)
                out.append(item)
        return out
