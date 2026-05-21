from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import Settings, settings
from app.ingestion.converter import DocumentConverter
from app.ingestion.index_builder import IndexBuilder, load_manifest
from app.schemas.answer import Answer
from app.schemas.document import Manifest
from app.workflow import KnowFlowWorkflow


app = FastAPI(title="KnowFlow Agent", version="0.1.0")


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)


class IngestRequest(BaseModel):
    raw_dir: str | None = None
    markdown_dir: str | None = None
    knowledge_base_dir: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/manifest", response_model=Manifest)
def manifest() -> Manifest:
    return load_manifest(settings.knowledge_base_dir)


@app.post("/ingest", response_model=Manifest)
def ingest(request: IngestRequest) -> Manifest:
    runtime = Settings(
        raw_dir=Path(request.raw_dir) if request.raw_dir else settings.raw_dir,
        markdown_dir=Path(request.markdown_dir) if request.markdown_dir else settings.markdown_dir,
        knowledge_base_dir=Path(request.knowledge_base_dir) if request.knowledge_base_dir else settings.knowledge_base_dir,
    )
    converter = DocumentConverter()
    converter.convert_directory(runtime.raw_dir, runtime.markdown_dir)
    return IndexBuilder(runtime.knowledge_base_dir).build_from_markdown(runtime.markdown_dir)


@app.post("/query", response_model=Answer)
async def query(request: QueryRequest) -> Answer:
    if not settings.knowledge_base_dir.exists():
        raise HTTPException(status_code=404, detail="knowledge_base directory does not exist")
    workflow = KnowFlowWorkflow(settings)
    return await workflow.answer_query(request.query)

