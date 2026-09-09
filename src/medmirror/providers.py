"""官方 OpenAI-compatible API 的最小配置层。

本模块只负责配置和请求体构造；默认不发网络请求。真实调用必须由后续 runner
在预算预留成功后显式触发。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelConfig:
    model_id: str
    vendor: str
    base_url: str
    api_key_env: str
    api_style: str
    confirmed: bool
    price_status: str

    @property
    def endpoint(self) -> str:
        return self.base_url.rstrip("/") + "/chat/completions"


def load_local_env(path: Path | None = None) -> None:
    """加载项目根目录的 .env.local；已有进程环境变量优先。"""
    path = path or Path(__file__).resolve().parents[2] / ".env.local"
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    path = path or Path(__file__).resolve().parents[2] / "configs/models.json"
    return json.loads(path.read_text())


def model_registry(path: Path | None = None) -> dict[str, ModelConfig]:
    load_local_env()
    catalog = load_catalog(path)
    registry: dict[str, ModelConfig] = {}
    for item in catalog["models"]:
        model_id = os.getenv(item.get("model_env", ""), item["id"])
        base_url = os.getenv(item.get("base_url_env", ""), item["base_url"])
        overridden = model_id != item["id"] or base_url != item["base_url"]
        registry[item["id"]] = ModelConfig(
            model_id=model_id,
            vendor=item["vendor"],
            base_url=base_url,
            api_key_env=item["api_key_env"],
            api_style=item["api_style"],
            confirmed=bool(item["confirmed"]) and not overridden,
            price_status=item["price_status"],
        )
    return registry


def build_chat_payload(
    config: ModelConfig,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 800,
    thinking_mode: str | None = None,
    reasoning_effort: str | None = None,
) -> dict[str, Any]:
    payload = {
        "model": config.model_id,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if thinking_mode:
        payload["thinking"] = {"type": thinking_mode}
    if reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort
    return payload


def config_status(registry: dict[str, ModelConfig] | None = None) -> list[dict[str, Any]]:
    load_local_env()
    registry = registry or model_registry()
    return [
        {
            "model": config.model_id,
            "vendor": config.vendor,
            "endpoint": config.endpoint,
            "confirmed": config.confirmed,
            "price_status": config.price_status,
            "key_present": bool(os.getenv(config.api_key_env)),
        }
        for config in registry.values()
    ]
