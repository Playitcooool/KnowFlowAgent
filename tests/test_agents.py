from __future__ import annotations

import asyncio
from pathlib import Path

from app.agents.query_rewriter import QueryRewriter
from app.agents.query_router import QueryRouter
from app.schemas.document import DocumentMetadata, Manifest


def test_query_router_uses_root_index_items_as_folder_candidates(tmp_path: Path) -> None:
    kb = tmp_path / "knowledge_base"
    kb.mkdir()
    (kb / "finance").mkdir()
    (kb / "hr").mkdir()
    (kb / "index.md").write_text(
        "# Enterprise Knowledge Base Index\n\n"
        "## finance\n\n"
        "Invoice approval and travel reimbursement policy.\n",
        encoding="utf-8",
    )
    (kb / "hr" / "local_index.md").write_text("Payroll and onboarding policy.", encoding="utf-8")

    manifest = Manifest(
        documents=[
            DocumentMetadata(
                id="doc_finance",
                path="finance/reimbursement.md",
                title="Travel Reimbursement",
                summary="Invoice approval and reimbursement rules.",
                primary_category="finance",
            ),
            DocumentMetadata(
                id="doc_hr",
                path="hr/payroll.md",
                title="Payroll",
                summary="Payroll policy.",
                primary_category="hr",
            ),
        ]
    )

    route = asyncio.run(QueryRouter(kb, manifest).route("How are payroll approvals handled?"))

    assert route.target_dirs == ["finance"]
    assert "root index" in route.reason


def test_query_rewriter_expands_from_manifest_context_not_static_synonyms() -> None:
    manifest = Manifest(
        documents=[
            DocumentMetadata(
                id="doc_finance",
                path="finance/reimbursement.md",
                title="Travel Reimbursement Policy",
                summary="Employees submit invoices before finance manager approval.",
                tags=["finance", "reimbursement", "travel", "invoice"],
                primary_category="finance",
            )
        ]
    )

    queries = asyncio.run(
        QueryRewriter(manifest=manifest).rewrite(
            "Who approves travel spending?",
            target_dirs=["finance"],
            n=5,
        )
    )

    assert queries[0] == "Who approves travel spending?"
    assert any("reimbursement" in query for query in queries)
