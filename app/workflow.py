from __future__ import annotations

from pathlib import Path

from app.agents.answer_agent import AnswerAgent
from app.agents.file_router import FileRouter
from app.agents.query_rewriter import QueryRewriter
from app.agents.query_router import QueryRouter
from app.agents.verifier import VerifierAgent
from app.config import Settings
from app.ingestion.index_builder import load_manifest
from app.retrieval.context_reader import ContextReader
from app.retrieval.evidence_ranker import EvidenceRanker
from app.retrieval.grep_retriever import GrepRetriever
from app.schemas.answer import Answer
from app.schemas.retrieval import SearchTrace


class KnowFlowWorkflow:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.knowledge_base_dir = settings.knowledge_base_dir

    async def answer_query(self, query: str) -> Answer:
        manifest = load_manifest(self.knowledge_base_dir)
        query_router = QueryRouter(self.knowledge_base_dir, manifest)
        file_router = FileRouter(self.knowledge_base_dir, manifest)
        rewriter = QueryRewriter()
        retriever = GrepRetriever(self.knowledge_base_dir)
        context_reader = ContextReader(self.knowledge_base_dir)
        ranker = EvidenceRanker(manifest)
        answer_agent = AnswerAgent()
        verifier = VerifierAgent()

        trace: list[SearchTrace] = []
        best_answer: Answer | None = None

        for retry_level in range(1, self.settings.max_retry + 1):
            route = query_router.route(query, retry_level=retry_level)
            target_files = file_router.route(query, route.target_dirs, retry_level=retry_level)
            targets = self._targets(route.target_dirs, target_files, retry_level)
            rewritten_queries = rewriter.rewrite(query, n=5 if retry_level < 3 else 8, retry_level=retry_level)

            hits = await retriever.search(
                queries=rewritten_queries,
                targets=targets,
                context_lines=self.settings.context_lines,
            )
            expanded = context_reader.expand(hits, window_size=self.settings.expansion_window)
            evidence = ranker.rank(query, expanded, top_k=self.settings.top_k_evidence)

            trace.append(
                SearchTrace(
                    retry_level=retry_level,
                    target_dirs=route.target_dirs,
                    target_files=target_files,
                    rewritten_queries=rewritten_queries,
                    evidence_count=len(evidence),
                    reason=route.reason,
                )
            )

            answer = answer_agent.generate(query, evidence, trace.copy())
            verification = verifier.verify(query, answer, evidence)
            answer = answer.model_copy(
                update={
                    "confidence": verification.confidence,
                    "answerable": verification.answerable,
                }
            )
            if best_answer is None or answer.confidence > best_answer.confidence:
                best_answer = answer
            if verification.answerable and verification.confidence >= self.settings.min_confidence:
                return answer

        if best_answer:
            return best_answer.model_copy(
                update={
                    "answerable": False,
                    "answer": (
                        best_answer.answer
                        + "\n\nThe available evidence was not strong enough for a fully supported answer."
                    ),
                }
            )
        return Answer(query=query, answer="No searchable knowledge base was found.", confidence=0.0, answerable=False)

    def _targets(self, target_dirs: list[str], target_files: list[str], retry_level: int) -> list[Path]:
        if retry_level >= 4:
            return [self.knowledge_base_dir]
        file_paths = [self.knowledge_base_dir / path for path in target_files]
        existing_files = [path for path in file_paths if path.exists()]
        if existing_files and retry_level <= 2:
            return existing_files
        dirs = [self.knowledge_base_dir / directory for directory in target_dirs]
        return [path for path in dirs if path.exists()] or [self.knowledge_base_dir]

