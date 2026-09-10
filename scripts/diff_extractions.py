#!/usr/bin/env python3
"""对比两版提取结果，输出逐条差异报告（issue #12：新旧结果分别保留并给出差异）。

默认对比 derived-v2（offline-rules-v1 快照）与 derived-v3（offline-rules-v2），
差异写入新目录；绝不写进原始数据目录 result/。确定性输出，无时间戳。

用法：
  uv run python scripts/diff_extractions.py \
      --old docs/experiments/exp003-baseline/derived-v2/extractions.jsonl \
      --new docs/experiments/exp003-baseline/derived-v3/extractions.jsonl \
      --output docs/experiments/exp003-baseline/derived-v3/extraction-diff.md
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from report_exp003 import atomic_write_text

from medmirror.protocol import PATH_PATTERNS, load_jsonl

RAW_DIR = ROOT / "docs/experiments/exp003-baseline/result"
# derived-v2 是 offline-rules-v1 冻结快照（作为 --old 读取），其内部禁止写入
FROZEN_DIR = ROOT / "docs/experiments/exp003-baseline/derived-v2"
DEFAULT_OLD = FROZEN_DIR / "extractions.jsonl"
DEFAULT_NEW = ROOT / "docs/experiments/exp003-baseline/derived-v3/extractions.jsonl"
DEFAULT_OUTPUT = ROOT / "docs/experiments/exp003-baseline/derived-v3/extraction-diff.md"

PATHS = tuple(PATH_PATTERNS)
TOP_LEVEL_FIELDS = ("evidence_mentioned", "identifiable_source", "source_evidence")


def cell(value: object, limit: int = 80) -> str:
    """表格单元格清洗：原文中的竖线/换行/首尾空白不得破坏 Markdown 表格。"""
    text = str(value).replace("|", "\\|").replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit] + "……"


def compare_group(po: dict, pn: dict, label: str) -> tuple[list[str], list[str], list[str]]:
    """对比一组字段：返回（表格行, 实质变化键, 新增字段键）。

    旧版不存在的字段首次出现算「新增字段填充」，与既有字段的实质变化分开，
    避免 v2 新字段把"有变化试次"计数灌满。
    """
    rows: list[str] = []
    changed: list[str] = []
    added: list[str] = []
    for field in sorted(set(po) | set(pn)):
        vo, vn = po.get(field), pn.get(field)
        if vo == vn:
            continue
        if field not in po:
            added.append(f"{label}.{field} 新增字段")
        else:
            changed.append(f"{label}.{field} {cell(vo, 24)}→{cell(vn, 24)}")
        quote = "" if field == "evidence" else cell(pn.get("evidence"))
        rows.append(f"| {label}.{field} | {cell(vo, 200)} | {cell(vn, 200)} | {quote} |")
    return rows, changed, added


def render(old_rows: dict, new_rows: dict) -> str:
    transitions: Counter[str] = Counter()
    source_transitions: Counter[str] = Counter()
    substantive_changed = 0
    field_add_only = 0
    review_queue: list[str] = []
    body: list[str] = []

    for trial_id in sorted(set(old_rows) | set(new_rows)):
        old, new = old_rows.get(trial_id), new_rows.get(trial_id)
        row_changes: list[str] = []
        changed_keys: list[str] = []
        added_keys: list[str] = []
        if old is None or new is None:
            row_changes.append(
                f"| 仅存在于一侧（old={old is not None}, new={new is not None}） | | | |"
            )
            changed_keys.append(trial_id)
        else:
            # 全字段对比：路径内取两版键并集，顶层含来源三态；
            # 只带两版各自真实存在的键——旧版缺失的 source_evidence 等归入"新增字段"，
            # 不得构造成 None 值冒充既有字段变化
            for path in PATHS:
                rows, changed, added = compare_group(old["paths"][path], new["paths"][path], path)
                row_changes.extend(rows)
                changed_keys.extend(changed)
                added_keys.extend(added)
            rows, changed, added = compare_group(
                {f: old[f] for f in TOP_LEVEL_FIELDS if f in old},
                {f: new[f] for f in TOP_LEVEL_FIELDS if f in new},
                "source",
            )
            row_changes.extend(rows)
            changed_keys.extend(changed)
            added_keys.extend(added)
        if new and any(new["paths"][p]["state"] == "needs_review" for p in PATHS):
            review_queue.append(trial_id)
        if row_changes:
            if changed_keys:
                substantive_changed += 1
            else:
                field_add_only += 1
            transitions.update(changed_keys)
            source_transitions.update(added_keys)
            body.append(f"### {trial_id}\n")
            body.append("| 变化 | 旧值 | 新值 | 新版引文（截断显示） |")
            body.append("|---|---|---|---|")
            body.extend(row_changes)
            body.append("")

    old_version = next(iter(old_rows.values()), {}).get("extractor_version", "?")
    new_version = next(iter(new_rows.values()), {}).get("extractor_version", "?")
    source_shifts = sorted(
        (key, count)
        for key, count in transitions.items()
        if key.startswith(("source.identifiable_source", "source.evidence_mentioned"))
    )
    added_note = (
        "、".join(f"{key}×{count}" for key, count in sorted(source_transitions.items())) or "无"
    )
    head = [
        "# 提取器版本差异报告",
        "",
        f"- 旧版：`{old_version}`；新版：`{new_version}`。",
        f"- 实质变化试次：{substantive_changed}／共 {len(set(old_rows) | set(new_rows))} 条"
        f"（另有 {field_add_only} 条仅新增字段填充，无既有字段变化）。",
        "- 来源识别变化："
        + ("、".join(f"{key}×{count}" for key, count in source_shifts) if source_shifts else "无"),
        f"- 新增字段填充：{added_note}。",
        "- 限制：`attitude_target`/`condition` 为 best-effort 单命中抽取（多句场景只取首个）；"
        "无显式态度动词的句式（如「以他汀为基础」「强化他汀」）按规格保持 mentioned，"
        "是否升格交 #11 定标裁定；逐字段语义以人工定标为准。",
        "",
        "## 变化分布",
        "",
        "| 变化 | 次数 |",
        "|---|---:|",
    ]
    for key in sorted(transitions):
        head.append(f"| {key} | {transitions[key]} |")
    head.extend(
        [
            "",
            "## 需人工复核清单（任一路径 state=needs_review）",
            "",
            "以下试次交 #11 人工定标裁决，提取器不强填态度：",
            "",
        ]
    )
    if review_queue:
        head.extend(f"- {trial_id}" for trial_id in review_queue)
    else:
        head.append("- 无")
    head.extend(["", "## 逐条差异", ""])
    return "\n".join(head + body).rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, default=DEFAULT_OLD, help="旧版 extractions.jsonl")
    parser.add_argument("--new", type=Path, default=DEFAULT_NEW, help="新版 extractions.jsonl")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="差异报告输出路径")
    args = parser.parse_args(argv)

    old_path, new_path, output = args.old.resolve(), args.new.resolve(), args.output.resolve()
    for label, path in (("--old", old_path), ("--new", new_path)):
        if not path.is_file():
            parser.error(f"{label} 输入文件不存在：{path}")
    # 守卫与 report_exp003 的双锚点守卫刻意不同：差异报告按设计与 --new 同目录
    # （derived-v3 内），需保护原始数据目录、冻结快照目录与输入文件本身
    raw = RAW_DIR.resolve()
    frozen = FROZEN_DIR.resolve()
    if output == raw or raw in output.parents or output in raw.parents:
        parser.error(
            f"拒绝执行：--output（{output}）位于原始数据目录（{raw}）内或其祖先，"
            "差异报告必须写入独立目录"
        )
    if output == frozen or frozen in output.parents:
        parser.error(
            f"拒绝执行：--output（{output}）落在冻结快照（{frozen}）内，旧版本产物不可覆写"
        )
    if output in (old_path, new_path):
        parser.error("拒绝执行：--output 不得覆盖输入文件")

    old_rows = {row["trial_id"]: row for row in load_jsonl(old_path)}
    new_rows = {row["trial_id"]: row for row in load_jsonl(new_path)}
    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(output, render(old_rows, new_rows))
    print(f"差异报告已写入：{output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
