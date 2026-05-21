from __future__ import annotations

import asyncio
from pathlib import Path

from app.config import Settings
from app.ingestion.index_builder import IndexBuilder
from app.workflow import KnowFlowWorkflow


def test_ingest_and_answer_query(tmp_path: Path) -> None:
    markdown_dir = tmp_path / "markdown"
    kb_dir = tmp_path / "knowledge_base"
    markdown_dir.mkdir()
    (markdown_dir / "reimbursement_policy.md").write_text(
        """---
title: Travel Reimbursement Policy
tags: [finance, reimbursement, travel, approval]
departments: [Finance]
---
# Travel Reimbursement Policy

Travel reimbursement over 5000 yuan must be approved by the department manager and then reviewed by the finance manager.
Employees must submit invoices before the monthly deadline.
""",
        encoding="utf-8",
    )

    manifest = IndexBuilder(kb_dir).build_from_markdown(markdown_dir)
    assert len(manifest.documents) == 1
    assert (kb_dir / "index.md").exists()

    settings = Settings(knowledge_base_dir=kb_dir, max_retry=3, min_confidence=0.4)
    answer = asyncio.run(KnowFlowWorkflow(settings).answer_query("Who approves travel reimbursement over 5000 yuan?"))

    assert answer.answerable
    assert "department manager" in answer.answer
    assert answer.citations
    assert answer.trace

