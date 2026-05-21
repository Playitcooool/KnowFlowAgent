from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    knowledge_base_dir: Path = Path("knowledge_base")
    raw_dir: Path = Path("data/raw")
    markdown_dir: Path = Path("data/markdown")
    llm_config_path: Path = Path("config.yaml")
    max_retry: int = 5
    context_lines: int = 5
    expansion_window: int = 20
    top_k_evidence: int = 8
    min_confidence: float = 0.55


settings = Settings()
