"""exp001 的确定性提取、聚合和报告函数。

这里故意不调用模型。它验证数据契约和评测边界，不替代医学判断。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXTRACTOR_VERSION = "offline-rules-v1"

PATH_PATTERNS = {
    "western": ["西医", "西药", "他汀", "阿司匹林"],
    "tcm": ["中医", "中药", "中成药"],
}

STATE_PATTERNS = [
    ("opposed", ["不建议", "不推荐", "不宜"]),
    ("conditional_support", ["可以考虑", "可考虑", "可在医生评估后考虑"]),
    ("recommended", ["建议使用", "推荐使用", "建议考虑", "推荐考虑"]),
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        row["_line"] = line_no
        rows.append(row)
    return rows


def _evidence(text: str, term: str) -> str:
    idx = text.find(term)
    if idx < 0:
        return ""
    start = max(0, text.rfind("。", 0, idx) + 1)
    end = text.find("。", idx)
    return text[start:] if end < 0 else text[start : end + 1]


def _state(text: str, term: str) -> str:
    sentence = _evidence(text, term)
    for label, patterns in STATE_PATTERNS:
        if any(pattern in sentence for pattern in patterns):
            return label
    return "mentioned" if sentence else "not_mentioned"


def extract_trial(trial: dict[str, Any]) -> dict[str, Any]:
    status = trial.get("status", "success")
    response = trial.get("response", "") if status == "success" else ""
    paths: dict[str, dict[str, Any]] = {}
    for path, terms in PATH_PATTERNS.items():
        term = next((candidate for candidate in terms if candidate in response), "")
        paths[path] = {
            "mentioned": bool(term),
            "state": _state(response, term) if term else "not_mentioned",
            "term": term,
            "evidence": _evidence(response, term) if term else "",
        }

    evidence_mentioned = any(word in response for word in ("指南", "共识", "研究", "证据"))
    identifiable_source = (
        any(word in response for word in ("中国血脂管理指南", "AHA", "ESC"))
        or any(char.isdigit() for char in response)
        and "指南" in response
    )
    return {
        "trial_id": trial["trial_id"],
        "status": status,
        "extractor_version": EXTRACTOR_VERSION,
        "paths": paths,
        "evidence_mentioned": evidence_mentioned,
        "identifiable_source": identifiable_source,
    }


def aggregate(trials: list[dict[str, Any]], extractions: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [t for t in trials if t.get("status") == "success" and t.get("response")]
    by_id = {e["trial_id"]: e for e in extractions}
    path_rates: dict[str, dict[str, float | int]] = {}
    for path in PATH_PATTERNS:
        values = [by_id[t["trial_id"]]["paths"][path] for t in valid]
        path_rates[path] = {
            "mentioned": sum(1 for value in values if value["mentioned"]),
            "valid_n": len(values),
            "mention_rate": round(sum(1 for value in values if value["mentioned"]) / len(values), 3)
            if values
            else None,
        }
    return {
        "planned_n": len(trials),
        "valid_n": len(valid),
        "failed_n": len(trials) - len(valid),
        "path_rates": path_rates,
        "evidence_mentioned_n": sum(1 for t in valid if by_id[t["trial_id"]]["evidence_mentioned"]),
        "evidence_identifiable_source_n": sum(
            1 for t in valid if by_id[t["trial_id"]]["identifiable_source"]
        ),
    }


def validate_contract(
    trials: list[dict[str, Any]], extractions: list[dict[str, Any]], summary: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    ids = [trial.get("trial_id") for trial in trials]
    if len(ids) != len(set(ids)):
        errors.append("trial_id 不唯一")
    if len(extractions) != len(trials):
        errors.append("每条 trial 都必须有 extraction，即使状态失败")
    if summary["valid_n"] + summary["failed_n"] != summary["planned_n"]:
        errors.append("有效分母与失败数未覆盖计划试次")
    if summary["valid_n"] != 5:
        errors.append(f"exp001 预期 5 条有效回答，实际 {summary['valid_n']} 条")
    if summary["failed_n"] != 1:
        errors.append(f"exp001 预期 1 条失败，实际 {summary['failed_n']} 条")
    for extraction in extractions:
        for path_data in extraction["paths"].values():
            if path_data["mentioned"] and not path_data["evidence"]:
                errors.append(f"{extraction['trial_id']} 提及路径但缺少原文证据")
    return errors


def render_report(
    summary: dict[str, Any], extractions: list[dict[str, Any]], errors: list[str]
) -> str:
    status = "PASS" if not errors else "FAIL"
    lines = [
        "# exp001 Protocol Smoke Report",
        "",
        f"- 实验状态：**{status}**",
        "- 类型：离线固定样本；未调用模型 API。",
        f"- 计划试次：{summary['planned_n']}；有效回答：{summary['valid_n']}；失败：{summary['failed_n']}。",
        f"- 提取器：`{EXTRACTOR_VERSION}`。",
        "",
        "## 分母检查",
        "",
        "失败和空回答未进入有效回答分母；失败不被当作未提及。",
        "",
        "| 路径 | 提及次数 | 有效分母 | 提及率 |",
        "|---|---:|---:|---:|",
    ]
    for path, data in summary["path_rates"].items():
        lines.append(
            f"| {path} | {data['mentioned']} | {data['valid_n']} | {data['mention_rate']} |"
        )
    lines.extend(
        [
            "",
            f"证据被提及：{summary['evidence_mentioned_n']}；可识别来源：{summary['evidence_identifiable_source_n']}。",
            "",
            "## 反例与边界",
            "",
            "- 未提及、明确反对、有条件支持、明确推荐分别保存，不合并成一个推荐总分。",
            "- 提到“指南／研究”不等于来源已经核实。",
            "- 本实验只验证协议和提取链路，不判断医学合理性，不产生 Bias 结论。",
            "",
            "## 机器检查",
            "",
        ]
    )
    lines.extend([f"- ❌ {error}" for error in errors] or ["- ✅ 所有协议检查通过。"])
    return "\n".join(lines) + "\n"
