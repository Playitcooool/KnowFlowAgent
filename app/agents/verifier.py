from __future__ import annotations

from app.schemas.answer import Answer, Verification
from app.schemas.retrieval import Evidence
from app.text_utils import score_text, tokenize


class VerifierAgent:
    def verify(self, query: str, answer: Answer, evidence: list[Evidence]) -> Verification:
        if not evidence:
            return Verification(
                answerable=False,
                confidence=0.0,
                missing_info=["No evidence was retrieved."],
                reason="The retriever returned no matching Markdown evidence.",
            )
        query_terms = set(tokenize(query))
        evidence_text = "\n".join(item.text for item in evidence)
        coverage = score_text(query_terms, evidence_text)
        best_score = max(item.score for item in evidence)
        confidence = round(min(1.0, coverage * 0.55 + best_score * 0.45), 4)
        answerable = confidence >= 0.55 and bool(answer.citations)
        missing = [] if answerable else ["Retrieved evidence does not cover enough query terms."]
        return Verification(
            answerable=answerable,
            confidence=confidence,
            evidence_files=sorted({item.file for item in evidence}),
            missing_info=missing,
            reason="Evidence coverage and ranked retrieval score were used as the sufficiency signal.",
        )

