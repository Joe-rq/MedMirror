#!/usr/bin/env python3
"""对 exp003 已保存回答做离线提取与描述性汇总。"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medmirror.protocol import aggregate, extract_trial, load_jsonl


def main() -> int:
    exp = ROOT / "docs/experiments/exp003-baseline"
    result = exp / "result"
    trials = load_jsonl(result / "trials.jsonl")
    extractions = [extract_trial(trial) for trial in trials]
    summary = aggregate(trials, extractions)
    summary["run_ids"] = sorted({trial.get("run_id") for trial in trials if trial.get("run_id")})
    summary["resumed"] = len(summary["run_ids"]) > 1
    summary["usage_total_tokens"] = sum(
        int(trial.get("usage", {}).get("total_tokens", 0))
        for trial in trials
        if isinstance(trial.get("usage"), dict)
    )
    catalog = json.loads((ROOT / "configs/models.json").read_text(encoding="utf-8"))
    pricing = {
        item["vendor"]: item.get("pricing") for item in catalog["models"] if item.get("pricing")
    }
    estimated_costs: dict[str, float] = {}
    for vendor, price in pricing.items():
        usage = {
            "prompt": sum(
                int(trial.get("usage", {}).get("prompt_tokens", 0))
                for trial in trials
                if trial.get("vendor") == vendor and isinstance(trial.get("usage"), dict)
            ),
            "completion": sum(
                int(trial.get("usage", {}).get("completion_tokens", 0))
                for trial in trials
                if trial.get("vendor") == vendor and isinstance(trial.get("usage"), dict)
            ),
        }
        estimated_costs[vendor] = round(
            (usage["prompt"] * price["input_cache_miss"] + usage["completion"] * price["output"])
            / 1_000_000,
            6,
        )
    summary["estimated_cost_cny_by_vendor"] = estimated_costs
    summary["estimated_cost_cny_peak_known_models"] = round(sum(estimated_costs.values()), 6)
    by_slice: dict[str, dict[str, object]] = defaultdict(
        lambda: {"planned_n": 0, "valid_n": 0, "paths": {}}
    )
    for trial, extraction in zip(trials, extractions, strict=False):
        key = f"{trial['model']}::{trial['prompt_variant']}"
        slice_data = by_slice[key]
        slice_data["planned_n"] = int(slice_data["planned_n"]) + 1
        if trial.get("status") == "success" and trial.get("response"):
            slice_data["valid_n"] = int(slice_data["valid_n"]) + 1
        slice_data["paths"] = extraction["paths"]
    summary["slices"] = by_slice
    (result / "extractions.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in extractions) + "\n",
        encoding="utf-8",
    )
    (result / "analysis.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# exp003 Baseline Analysis",
        "",
        f"- 计划／有效／失败：{summary['planned_n']}／{summary['valid_n']}／{summary['failed_n']}。",
        f"- 累计 tokens：{summary['usage_total_tokens']}；按已登记价格估算：{summary['estimated_cost_cny_by_vendor'] or '暂无'} 元（DeepSeek 按高峰价）。",
        "- 类型：已保存回答的离线规则提取；不调用模型，不做医学质量或 Bias 判断。",
        "",
        "## 总体路径呈现",
        "",
        "| 路径 | 提及次数 | 有效分母 | 提及率 |",
        "|---|---:|---:|---:|",
    ]
    for path, data in summary["path_rates"].items():
        lines.append(
            f"| {path} | {data['mentioned']} | {data['valid_n']} | {data['mention_rate']} |"
        )
    boundary = (
        "本轮已完成 3 个模型 × 3 个提示变体 × 3 次重复，共 27 条；仍属于单病例的初步观察，不能据此判断医学合理性或模型偏差。"
        if summary["planned_n"] == 27
        else "小批次每个模型和变体只有 1 次重复，只用于验证执行器与提取链路。不能据此判断稳定差异、医学合理性或模型偏差。"
    )
    lines.extend(
        [
            "",
            "## 边界",
            "",
            boundary,
        ]
    )
    (result / "analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
