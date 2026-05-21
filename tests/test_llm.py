from __future__ import annotations

from pathlib import Path

from app.llm import load_llm_client, load_llm_config


def test_load_llm_config_from_yaml(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        """
providers:
  anthropic:
    type: anthropic
    api_key_env: ANTHROPIC_AUTH_TOKEN
    base_url: https://api.example.com/anthropic
    default_model: example-model
runtime:
  default_provider: anthropic
  timeout_seconds: 12
  max_retries: 2
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "test-token")

    llm_config = load_llm_config(config)
    client = load_llm_client(config)

    assert llm_config is not None
    assert llm_config.provider.name == "anthropic"
    assert llm_config.provider.default_model == "example-model"
    assert llm_config.timeout_seconds == 12
    assert client is not None
    assert client.available
