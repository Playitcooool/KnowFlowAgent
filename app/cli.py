from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.config import Settings
from app.ingestion.converter import DocumentConverter
from app.ingestion.index_builder import IndexBuilder
from app.workflow import KnowFlowWorkflow


def main() -> None:
    parser = argparse.ArgumentParser(description="KnowFlow Agent CLI")
    subcommands = parser.add_subparsers(dest="command", required=True)

    ingest = subcommands.add_parser("ingest", help="Convert raw files and build Markdown KB indexes.")
    ingest.add_argument("--raw-dir", default="data/raw")
    ingest.add_argument("--markdown-dir", default="data/markdown")
    ingest.add_argument("--kb-dir", default="knowledge_base")

    ask = subcommands.add_parser("ask", help="Ask a question against the knowledge base.")
    ask.add_argument("query")
    ask.add_argument("--kb-dir", default="knowledge_base")
    ask.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if args.command == "ingest":
        converter = DocumentConverter()
        markdown_files = converter.convert_directory(Path(args.raw_dir), Path(args.markdown_dir))
        manifest = IndexBuilder(Path(args.kb_dir)).build_from_markdown(Path(args.markdown_dir))
        print(f"Converted {len(markdown_files)} files and indexed {len(manifest.documents)} documents.")
    elif args.command == "ask":
        settings = Settings(knowledge_base_dir=Path(args.kb_dir))
        answer = asyncio.run(KnowFlowWorkflow(settings).answer_query(args.query))
        if args.json:
            print(json.dumps(answer.model_dump(), ensure_ascii=False, indent=2))
        else:
            print(answer.answer)
            print(f"\nConfidence: {answer.confidence:.2f}")


if __name__ == "__main__":
    main()

