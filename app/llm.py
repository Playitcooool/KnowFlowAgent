from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import yaml


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    type: str
    api_key_env: str
    base_url: str
    default_model: str


@dataclass(frozen=True)
class LLMConfig:
    provider: ProviderConfig
    timeout_seconds: float = 60
    max_retries: int = 3


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = os.getenv(config.provider.api_key_env, "")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def complete(self, system: str, user: str, temperature: float = 0.0) -> str | None:
        if not self.available:
            return None
        if self.config.provider.type == "anthropic":
            return await self._anthropic(system, user, temperature)
        return await self._openai_compatible(system, user, temperature)

    async def complete_json(self, system: str, user: str, temperature: float = 0.0) -> Any | None:
        text = await self.complete(system, user, temperature=temperature)
        if not text:
            return None
        try:
            return json.loads(_extract_json(text))
        except json.JSONDecodeError:
            return None

    async def _openai_compatible(self, system: str, user: str, temperature: float) -> str | None:
        url = _join_url(self.config.provider.base_url, "chat/completions")
        payload = {
            "model": self.config.provider.default_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = await self._post(url, payload, headers)
        if not data:
            return None
        return data.get("choices", [{}])[0].get("message", {}).get("content")

    async def _anthropic(self, system: str, user: str, temperature: float) -> str | None:
        url = _join_url(self.config.provider.base_url, "v1/messages")
        payload = {
            "model": self.config.provider.default_model,
            "max_tokens": 1200,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        data = await self._post(url, payload, headers)
        if not data:
            return None
        content = data.get("content", [])
        if content and isinstance(content[0], dict):
            return content[0].get("text")
        return None

    async def _post(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any] | None:
        last_error: Exception | None = None
        timeout = self.config.timeout_seconds
        for _ in range(max(1, self.config.max_retries)):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                last_error = exc
        if last_error:
            return None
        return None


def load_llm_client(config_path: Path = Path("config.yaml")) -> LLMClient | None:
    config = load_llm_config(config_path)
    return LLMClient(config) if config else None


def load_llm_config(config_path: Path = Path("config.yaml")) -> LLMConfig | None:
    if not config_path.exists():
        return None
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    runtime = data.get("runtime", {})
    providers = data.get("providers", {})
    provider_name = runtime.get("default_provider")
    provider_data = providers.get(provider_name or "")
    if not provider_name or not isinstance(provider_data, dict):
        return None
    api_key_env = provider_data.get("api_key_env")
    if isinstance(api_key_env, list):
        api_key_env = next((name for name in api_key_env if os.getenv(name)), api_key_env[0] if api_key_env else "")
    provider = ProviderConfig(
        name=provider_name,
        type=provider_data.get("type", "openai_compatible"),
        api_key_env=str(api_key_env or ""),
        base_url=provider_data.get("base_url", ""),
        default_model=provider_data.get("default_model", ""),
    )
    return LLMConfig(
        provider=provider,
        timeout_seconds=float(runtime.get("timeout_seconds", 60)),
        max_retries=int(runtime.get("max_retries", 3)),
    )


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _extract_json(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    start = min((idx for idx in [stripped.find("{"), stripped.find("[")] if idx >= 0), default=0)
    end = max(stripped.rfind("}"), stripped.rfind("]"))
    return stripped[start : end + 1] if end >= start else stripped
