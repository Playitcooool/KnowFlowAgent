from __future__ import annotations

import re

from app.llm import LLMClient
from app.schemas.answer import Answer, Citation
from app.schemas.retrieval import Evidence, SearchTrace
from app.text_utils import tokenize


class AnswerAgent:
    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm

    async def generate(self, query: str, evidence: list[Evidence], trace: list[SearchTrace]) -> Answer:
        if not evidence:
            return Answer(
                query=query,
                answer=(
                    "I could not find enough evidence in the knowledge base to answer this. "
                    "No cited policy or document lines matched the question."
                ),
                citations=[],
                confidence=0.0,
                answerable=False,
                trace=trace,
            )
        citations = [
            Citation(file=item.file, line_start=item.line_start, line_end=item.line_end)
            for item in evidence[:4]
        ]
        answer = await self._llm_answer(query, evidence[:6]) if self.llm and self.llm.available else None
        if not answer:
            answer = self._compose_answer(query, evidence[:4])
        confidence = max(item.score for item in evidence)
        return Answer(
            query=query,
            answer=answer,
            citations=citations,
            confidence=round(confidence, 4),
            answerable=confidence > 0,
            trace=trace,
        )

    async def _llm_answer(self, query: str, evidence: list[Evidence]) -> str | None:
        evidence_text = "\n\n".join(
            f"[{idx}] {item.citation()}\n{item.text}" for idx, item in enumerate(evidence, start=1)
        )
        return await self.llm.complete(
            system=(
                "You are a grounded enterprise knowledge QA agent. "
                "Answer only from the provided evidence. "
                "If evidence is insufficient, say what is missing. "
                "Cite file:line ranges inline when making claims."
            ),
            user=f"Question:\n{query}\n\nEvidence:\n{evidence_text}",
        )

    def _compose_answer(self, query: str, evidence: list[Evidence]) -> str:
        query_terms = set(tokenize(query))
        sentences: list[str] = []
        for item in evidence:
            plain = re.sub(r"^\d+:\s*", "", item.text, flags=re.MULTILINE)
            for sentence in re.split(r"(?<=[.!?。！？])\s+|\n+", plain):
                cleaned = sentence.strip(" -\t")
                if not cleaned or cleaned.startswith("#"):
                    continue
                if query_terms & set(tokenize(cleaned)):
                    sentences.append(cleaned)
                if len(sentences) >= 3:
                    break
            if len(sentences) >= 3:
                break
        if not sentences:
            sentences = [re.sub(r"^\d+:\s*", "", evidence[0].text.splitlines()[0]).strip()]
        citation_text = "; ".join(item.citation() for item in evidence[:3])
        return " ".join(sentences[:3]) + f"\n\nEvidence: {citation_text}."
