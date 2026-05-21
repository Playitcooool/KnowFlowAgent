from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path


class DocumentConverter:
    """Convert common text-like inputs into Markdown.

    PDF and DOCX support is best-effort through optional dependencies. The
    converter keeps the project usable without heavy document tooling.
    """

    def convert_directory(self, raw_dir: Path, markdown_dir: Path) -> list[Path]:
        markdown_dir.mkdir(parents=True, exist_ok=True)
        outputs: list[Path] = []
        if not raw_dir.exists():
            return outputs
        for path in sorted(raw_dir.rglob("*")):
            if path.is_file():
                output = markdown_dir / f"{path.stem}.md"
                self.convert_file(path, output)
                outputs.append(output)
        return outputs

    def convert_file(self, source: Path, output: Path) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        suffix = source.suffix.lower()
        if suffix == ".md":
            if source.resolve() != output.resolve():
                shutil.copyfile(source, output)
        elif suffix in {".txt", ".rst"}:
            output.write_text(source.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        elif suffix in {".html", ".htm"}:
            output.write_text(self._html_to_markdown(source.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
        elif suffix == ".json":
            output.write_text(self._json_to_markdown(source), encoding="utf-8")
        elif suffix == ".pdf":
            output.write_text(self._pdf_to_markdown(source), encoding="utf-8")
        elif suffix == ".docx":
            output.write_text(self._docx_to_markdown(source), encoding="utf-8")
        else:
            output.write_text(source.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        return output

    def _html_to_markdown(self, text: str) -> str:
        try:
            from markdownify import markdownify as md

            return md(text)
        except Exception:
            text = re.sub(r"<\s*h([1-6])[^>]*>(.*?)<\s*/\s*h\1\s*>", lambda m: "#" * int(m.group(1)) + " " + m.group(2), text, flags=re.I | re.S)
            text = re.sub(r"<[^>]+>", " ", text)
            return html.unescape(re.sub(r"\s+\n", "\n", text))

    def _json_to_markdown(self, source: Path) -> str:
        data = json.loads(source.read_text(encoding="utf-8"))
        if isinstance(data, list):
            chunks = [f"# {source.stem.replace('_', ' ').title()}"]
            for idx, item in enumerate(data, start=1):
                chunks.append(f"\n## Item {idx}\n\n```json\n{json.dumps(item, ensure_ascii=False, indent=2)}\n```")
            return "\n".join(chunks)
        return f"# {source.stem.replace('_', ' ').title()}\n\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"

    def _pdf_to_markdown(self, source: Path) -> str:
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(source))
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
            return f"# {source.stem.replace('_', ' ').title()}\n\n{text.strip()}\n"
        except Exception as exc:
            return f"# {source.stem.replace('_', ' ').title()}\n\nPDF conversion unavailable: {exc}\n"

    def _docx_to_markdown(self, source: Path) -> str:
        try:
            from docx import Document

            doc = Document(str(source))
            lines = [f"# {source.stem.replace('_', ' ').title()}"]
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    lines.append(text)
            return "\n\n".join(lines) + "\n"
        except Exception as exc:
            return f"# {source.stem.replace('_', ' ').title()}\n\nDOCX conversion unavailable: {exc}\n"
