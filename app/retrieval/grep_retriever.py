from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from app.schemas.retrieval import GrepHit
from app.text_utils import tokenize


class GrepRetriever:
    def __init__(self, knowledge_base_dir: Path):
        self.knowledge_base_dir = knowledge_base_dir
        self.has_rg = shutil.which("rg") is not None

    async def search(
        self,
        queries: list[str],
        targets: list[Path],
        context_lines: int = 0,
        max_hits_per_query: int = 80,
    ) -> list[GrepHit]:
        if not targets or not queries:
            return []
        tasks = [
            self._search_one(query, targets, context_lines, max_hits_per_query)
            for query in queries
        ]
        results = await asyncio.gather(*tasks)
        return [hit for batch in results for hit in batch]

    async def _search_one(
        self,
        query: str,
        targets: list[Path],
        context_lines: int,
        max_hits: int,
    ) -> list[GrepHit]:
        terms = tokenize(query)
        if not terms:
            return []
        if self.has_rg:
            return await self._rg(query, terms, targets, context_lines, max_hits)
        return await asyncio.to_thread(self._python_search, query, terms, targets, max_hits)

    async def _rg(
        self,
        query: str,
        terms: list[str],
        targets: list[Path],
        context_lines: int,
        max_hits: int,
    ) -> list[GrepHit]:
        pattern = "|".join(terms)
        cmd = [
            "rg",
            "--line-number",
            "--ignore-case",
            "--no-heading",
            "--glob",
            "*.md",
            "-C",
            str(context_lines),
            pattern,
            *[str(target) for target in targets],
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        hits: list[GrepHit] = []
        for raw in stdout.decode(errors="replace").splitlines():
            parsed = self._parse_rg_line(raw)
            if not parsed:
                continue
            file, line_number, line_text = parsed
            matched = [term for term in terms if term.lower() in line_text.lower()]
            if matched:
                hits.append(
                    GrepHit(
                        file=self._relative(file),
                        line_number=line_number,
                        line_text=line_text,
                        query=query,
                        matched_terms=matched,
                    )
                )
            if len(hits) >= max_hits:
                break
        return hits

    def _python_search(self, query: str, terms: list[str], targets: list[Path], max_hits: int) -> list[GrepHit]:
        files: list[Path] = []
        for target in targets:
            if target.is_file() and target.suffix == ".md":
                files.append(target)
            elif target.is_dir():
                files.extend(target.rglob("*.md"))
        hits: list[GrepHit] = []
        for path in files:
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                lines = path.read_text(errors="replace").splitlines()
            for idx, line in enumerate(lines, start=1):
                matched = [term for term in terms if term.lower() in line.lower()]
                if matched:
                    hits.append(
                        GrepHit(
                            file=self._relative(path),
                            line_number=idx,
                            line_text=line,
                            query=query,
                            matched_terms=matched,
                        )
                    )
                if len(hits) >= max_hits:
                    return hits
        return hits

    def _parse_rg_line(self, raw: str) -> tuple[Path, int, str] | None:
        separator = ":" if ":" in raw else "-"
        parts = raw.split(separator, 2)
        if len(parts) != 3:
            return None
        file_raw, line_raw, line_text = parts
        try:
            line_number = int(line_raw)
        except ValueError:
            return None
        return Path(file_raw), line_number, line_text

    def _relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.knowledge_base_dir.resolve()))
        except ValueError:
            return str(path)

