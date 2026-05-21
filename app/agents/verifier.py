from __future__ import annotations

from app.llm import LLMClient
from app.schemas.answer import Answer, Verification
from app.schemas.retrieval import Evidence
from app.text_utils import score_text, tokenize


class VerifierAgent:
    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm

    async def verify(self, query: str, answer: Answer, evidence: list[Evidence]) -> Verification:
        if self.llm and self.llm.available:
            verification = await self._llm_verify(query, answer, evidence)
            if verification:
                return verification
        return self._heuristic_verify(query, answer, evidence)

    def _heuristic_verify(self, query: str, answer: Answer, evidence: list[Evidence]) -> Verification:
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

    async def _llm_verify(self, query: str, answer: Answer, evidence: list[Evidence]) -> Verification | None:
        evidence_text = "\n\n".join(f"{item.citation()}\n{item.text}" for item in evidence[:8])
        result = await self.llm.complete_json(
            system=(
                "You verify whether an answer is fully supported by supplied evidence. "
                "Return only JSON with keys answerable, confidence, missing_info, reason."
            ),
            user=str(
                {
                    "query": query,
                    "answer": answer.answer,
                    "citations": [citation.__dict__ for citation in answer.citations],
                    "evidence": evidence_text[:10000],
                }
            ),
        )
        if not isinstance(result, dict):
            return None
        try:
            confidence = max(0.0, min(1.0, float(result.get("confidence", 0.0))))
        except (TypeError, ValueError):
            confidence = 0.0
        missing = result.get("missing_info", [])
        if isinstance(missing, str):
            missing = [missing]
        return Verification(
            answerable=bool(result.get("answerable")),
            confidence=round(confidence, 4),
            evidence_files=sorted({item.file for item in evidence}),
            missing_info=[str(item) for item in missing],
            reason=str(result.get("reason") or "Verified with configured LLM."),
        )
