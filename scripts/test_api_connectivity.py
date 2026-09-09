#!/usr/bin/env python3
"""对已配置的三家模型各发起一次最小请求，不打印密钥或回答正文。"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medmirror.providers import build_chat_payload, load_local_env, model_registry


def run_one(config) -> dict[str, object]:
    key = __import__("os").getenv(config.api_key_env)
    if not key:
        return {"model": config.model_id, "vendor": config.vendor, "status": "skipped_key_missing"}

    payload = build_chat_payload(
        config,
        [{"role": "user", "content": "请只回复 OK。"}],
        temperature=0,
        max_tokens=int(__import__("os").getenv("MEDMIRROR_MAX_TOKENS", "8")),
        thinking_mode=__import__("os").getenv(f"MEDMIRROR_{config.vendor.upper()}_THINKING_MODE"),
        reasoning_effort=__import__("os").getenv(f"MEDMIRROR_{config.vendor.upper()}_REASONING_EFFORT"),
    )
    request = urllib.request.Request(
        config.endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        choice = body.get("choices", [{}])[0] if body.get("choices") else {}
        message = choice.get("message", {}) if isinstance(choice, dict) else {}
        content = message.get("content") if isinstance(message, dict) else None
        reasoning = message.get("reasoning_content") if isinstance(message, dict) else None
        return {
            "model": config.model_id,
            "vendor": config.vendor,
            "status": "ok",
            "http_status": response.status,
            "elapsed_ms": elapsed_ms,
            "choices": isinstance(body.get("choices"), list),
            "usage": isinstance(body.get("usage"), dict),
            "choice_keys": sorted(choice) if isinstance(choice, dict) else [],
            "message_keys": sorted(message) if isinstance(message, dict) else [],
            "content_type": type(content).__name__,
            "content_len": len(content) if isinstance(content, (str, list, dict)) else 0,
            "reasoning_content_len": len(reasoning) if isinstance(reasoning, str) else 0,
        }
    except urllib.error.HTTPError as error:
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            "model": config.model_id,
            "vendor": config.vendor,
            "status": "http_error",
            "http_status": error.code,
            "elapsed_ms": elapsed_ms,
        }
    except urllib.error.URLError as error:
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            "model": config.model_id,
            "vendor": config.vendor,
            "status": "network_error",
            "error_type": type(error.reason).__name__,
            "elapsed_ms": elapsed_ms,
        }
    except (TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as error:
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            "model": config.model_id,
            "vendor": config.vendor,
            "status": "response_error",
            "error_type": type(error).__name__,
            "elapsed_ms": elapsed_ms,
        }


def main() -> int:
    load_local_env()
    results = [run_one(config) for config in model_registry().values()]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(item["status"] == "ok" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
