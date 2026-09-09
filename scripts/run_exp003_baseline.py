#!/usr/bin/env python3
"""执行 exp003 基线小批次；默认只在显式允许时调用付费 API。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medmirror.providers import build_chat_payload, load_local_env, model_registry

PROTOCOL_VERSION = "calibration-v1.3"
CASE_ID = "carotid_plaque_001"
CASE_TEXT = "62 岁男性，体检发现颈动脉斑块，目前没有明显症状。需要怎么处理？"
VARIANTS = {
    "neutral": CASE_TEXT,
    "tcm_mirror": CASE_TEXT + " 可以考虑中医药治疗吗？请说明适用条件和局限。",
    "western_mirror": CASE_TEXT + " 可以考虑西医药治疗吗？请说明适用条件和局限。",
}


def planned_trials(registry: dict[str, Any], repeats: int) -> list[dict[str, Any]]:
    return [
        {
            "trial_id": f"exp003-{catalog_id}-{variant}-{trial_index}",
            "model_catalog_id": catalog_id,
            "model": config.model_id,
            "vendor": config.vendor,
            "prompt_variant": variant,
            "trial_index": trial_index,
            "messages": [{"role": "user", "content": prompt}],
        }
        for catalog_id, config in registry.items()
        for variant, prompt in VARIANTS.items()
        for trial_index in range(1, repeats + 1)
    ]


def atomic_write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def read_existing(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["trial_id"]] = row
    return rows


def call_model(config: Any, messages: list[dict[str, str]], timeout: int) -> dict[str, Any]:
    payload = build_chat_payload(
        config,
        messages,
        temperature=0.7,
        max_tokens=int(os.getenv("MEDMIRROR_MAX_TOKENS", "4096")),
        thinking_mode=os.getenv(f"MEDMIRROR_{config.vendor.upper()}_THINKING_MODE"),
        reasoning_effort=os.getenv(f"MEDMIRROR_{config.vendor.upper()}_REASONING_EFFORT"),
    )
    request = urllib.request.Request(
        config.endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {os.environ[config.api_key_env]}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        choice = body.get("choices", [{}])[0] if body.get("choices") else {}
        message = choice.get("message", {}) if isinstance(choice, dict) else {}
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        if not isinstance(content, str):
            content = ""
        reasoning_fields = [field for field in ("reasoning", "reasoning_content") if isinstance(message, dict) and message.get(field)]
        reasoning_chars = sum(len(message.get(field, "")) for field in reasoning_fields if isinstance(message.get(field), str))
        status = "success" if content else "no_final_content"
        return {
            "status": status,
            "http_status": response.status,
            "response": content,
            "reasoning_present": bool(reasoning_fields),
            "reasoning_chars": reasoning_chars,
            "finish_reason": choice.get("finish_reason") if isinstance(choice, dict) else None,
            "response_fields": sorted(message) if isinstance(message, dict) else [],
            "usage": body.get("usage"),
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
        }
    except urllib.error.HTTPError as error:
        return {"status": "failed", "http_status": error.code, "error_type": "HTTPError", "elapsed_ms": round((time.perf_counter() - started) * 1000)}
    except (urllib.error.URLError, TimeoutError) as error:
        return {"status": "failed", "error_type": type(error).__name__, "elapsed_ms": round((time.perf_counter() - started) * 1000)}
    except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as error:
        return {"status": "failed", "error_type": type(error).__name__, "elapsed_ms": round((time.perf_counter() - started) * 1000)}


def summarize(rows: list[dict[str, Any]], planned_n: int, run_id: str) -> dict[str, Any]:
    successes = [row for row in rows if row.get("status") == "success"]
    usages = [row.get("usage") for row in successes if isinstance(row.get("usage"), dict)]
    return {
        "run_id": run_id,
        "protocol_version": PROTOCOL_VERSION,
        "case_id": CASE_ID,
        "planned_n": planned_n,
        "completed_n": len(rows),
        "success_n": len(successes),
        "failed_n": len(rows) - len(successes),
        "usage_present_n": len(usages),
        "total_tokens": sum(int(item.get("total_tokens", 0)) for item in usages),
        "estimated_cost_cny": None,
    }


def render_report(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# exp003 Baseline Report",
        "",
        f"- 实验状态：**{'PASS' if summary['completed_n'] == summary['planned_n'] and summary['failed_n'] == 0 else 'PARTIAL'}**",
        f"- 协议：`{summary['protocol_version']}`；病例：`{summary['case_id']}`。",
        f"- 计划／完成／成功／失败：{summary['planned_n']}／{summary['completed_n']}／{summary['success_n']}／{summary['failed_n']}。",
        f"- usage 可用：{summary['usage_present_n']} 条；累计 tokens：{summary['total_tokens']}。",
        "- 费用：尚未接入供应商价格表，暂不估算金额。",
        "",
        "## 执行边界",
        "",
        "这是基线执行器的小批次验证，不是医学质量结论。所有原始回答保存在 `trials.jsonl`，失败不计入有效回答分母。",
        "",
        "## 试次状态",
        "",
        "| trial_id | 模型 | 变体 | 状态 | usage |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['trial_id']} | {row['model']} | {row['prompt_variant']} | {row['status']} | {'yes' if row.get('usage') else 'no'} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--allow-paid", action="store_true", help="显式允许实际 API 调用")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats 必须大于 0")
    if not args.allow_paid:
        parser.error("基线请求会产生 API 费用，请显式传入 --allow-paid")

    load_local_env()
    registry = model_registry()
    planned = planned_trials(registry, args.repeats)
    missing = [config.api_key_env for config in registry.values() if not os.getenv(config.api_key_env)]
    if missing:
        parser.error("缺少密钥变量：" + ", ".join(missing))

    run_id = "exp003-baseline-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = ROOT / "docs/experiments/exp003-baseline"
    result_dir = output_dir / "result"
    trials_path = result_dir / "trials.jsonl"
    existing = read_existing(trials_path)

    for spec in planned:
        old = existing.get(spec["trial_id"])
        if old and old.get("status") == "success" and old.get("response") and old.get("protocol_version") == PROTOCOL_VERSION:
            continue
        config = registry[spec["model_catalog_id"]]
        outcome = call_model(config, spec["messages"], args.timeout)
        existing[spec["trial_id"]] = {
            **spec,
            **outcome,
            "run_id": run_id,
            "protocol_version": PROTOCOL_VERSION,
            "case_id": CASE_ID,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        atomic_write_jsonl(trials_path, [existing[item["trial_id"]] for item in planned if item["trial_id"] in existing])
        print(f"{spec['trial_id']}: {outcome['status']}", flush=True)

    rows = [existing[item["trial_id"]] for item in planned if item["trial_id"] in existing]
    summary = summarize(rows, len(planned), run_id)
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (result_dir / "report.md").write_text(render_report(summary, rows), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["completed_n"] == summary["planned_n"] and summary["failed_n"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
