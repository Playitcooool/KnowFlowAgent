from __future__ import annotations

import asyncio
from pathlib import Path

from app.retrieval.context_reader import ContextReader
from app.retrieval.grep_retriever import GrepRetriever


def test_grep_retriever_and_context_reader(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    finance = kb / "finance"
    finance.mkdir(parents=True)
    (finance / "policy.md").write_text(
        "# Policy\n\nSmall expenses need team lead approval.\nLarge expenses need finance manager approval.\n",
        encoding="utf-8",
    )

    hits = asyncio.run(GrepRetriever(kb).search(["finance manager approval"], [finance]))
    assert hits
    assert hits[0].file == "finance/policy.md"

    evidence = ContextReader(kb).expand(hits, window_size=4)
    assert evidence
    assert "finance manager" in evidence[0].text

