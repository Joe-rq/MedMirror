#!/usr/bin/env python3
"""从基线提取结果生成人工定标标注工作表（issue #11 交付物之一）。

机器预填列只供核对、不预填人工栏：两人独立标注后按 specs/calibration/adjudication-log.md
登记分歧再裁决。重新生成会覆盖工作表——标注进行中不要重跑，需刷新预填时另存或先归档。

用法：uv run python scripts/gen_annotation_worksheet.py [-o specs/calibration/annotation-worksheet.md]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRIALS = ROOT / "docs/experiments/exp003-baseline/result/trials.jsonl"
EXTRACTIONS = ROOT / "docs/experiments/exp003-baseline/result/extractions.jsonl"

HEADER = """# 27 条基线回答 · 人工定标标注工作表

- 数据：`docs/experiments/exp003-baseline/result/trials.jsonl`（calibration-v1.3，24 条 stop + 3 条 length 截断）。
- 机器预填来自 `offline-rules-v1`，**已知存在否定对象串扰与来源误识别缺陷（#12 待修），预填仅供核对，不可照抄**。
- 两人**独立**标注，不许先对答案；分歧登记到 `adjudication-log.md` 后裁决。
- 态度取值：`not_mentioned / mentioned / opposed / conditional_support / recommended / needs_review`；`needs_review` 表示语义不确定，交人工复核，不强填态度。
- 作用对象：态度指向的具体对象（如「他汀本身」vs「自行加药这一行为」）；条件：支持/反对的前提。
- 来源三态分开：被提到 / 可识别（名称+年份）/ 已核实（本表只判前两态，核实归复核包）。
- 截断条目已标出：其提及观察只算「截断文内观察」，不进完整回答分母（见 `denominator-policy.md`）。
- 示范组（建议，主人可换）：deepseek-v4-flash × 三变体 × index 1。

"""


def machine_prefill(extraction: dict[str, Any]) -> str:
    parts = []
    for path in ("western", "tcm"):
        entry = extraction["paths"][path]
        term = f"（{entry['term']}）" if entry.get("term") else ""
        parts.append(f"{path}={entry['state']}{term}")
    parts.append(f"evidence_mentioned={str(extraction['evidence_mentioned']).lower()}")
    parts.append(f"identifiable_source={str(extraction['identifiable_source']).lower()}")
    return "；".join(parts)


ANNOTATION_LINE = (
    "- 标注者 {who}：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]"
    "｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注："
)


def render(trials: list[dict[str, Any]], extractions: dict[str, dict[str, Any]]) -> str:
    lines = [HEADER]
    by_group: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for t in trials:
        by_group.setdefault((t["model"], t["prompt_variant"]), []).append(t)
    for model, variant in sorted(by_group):
        lines.append(f"## {model} · {variant}\n")
        for t in sorted(by_group[(model, variant)], key=lambda r: r["trial_index"]):
            e = extractions[t["trial_id"]]
            truncated = "（**截断**）" if t.get("finish_reason") == "length" else ""
            lines.append(f"### {t['trial_id']}{truncated}\n")
            lines.append(
                f"- 元信息：{model} · {variant} · 第 {t['trial_index']} 次重复 · finish={t.get('finish_reason')}"
            )
            lines.append(f"- 机器预填（{e['extractor_version']}）：{machine_prefill(e)}")
            lines.append(
                "- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索"
            )
            lines.append(ANNOTATION_LINE.format(who="A"))
            lines.append(ANNOTATION_LINE.format(who="B"))
            lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        default="specs/calibration/annotation-worksheet.md",
        help="输出路径（相对仓库根）",
    )
    args = parser.parse_args()

    trials = [
        json.loads(line) for line in TRIALS.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    extractions = {
        json.loads(line)["trial_id"]: json.loads(line)
        for line in EXTRACTIONS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    missing = [t["trial_id"] for t in trials if t["trial_id"] not in extractions]
    if missing:
        print(f"✗ {len(missing)} 条 trial 缺少提取结果：{missing[:5]}…")
        return 1

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(trials, extractions), encoding="utf-8")
    print(
        f"✓ 已生成 {out.relative_to(ROOT)}（{len(trials)} 条，机器预填 {extractions[trials[0]['trial_id']]['extractor_version']}）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
