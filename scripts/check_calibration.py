#!/usr/bin/env python3
"""规则验证层：校验 specs/examples/negatives.jsonl 的结构与引文，核对基线分母口径。

负例集是 #11 人工定标的机器可检部分：结构、逐字引文、trial 引用、kind 覆盖与
27 条基线的截断分母。语义是否正确仍以人工定标为准——本脚本通过不等于评分正确
（specs/calibration.md §4），`expected` 逐条经主人确认后才从 pending 转 confirmed。

用法：uv run python scripts/check_calibration.py [--require-confirmed]
退出码 0 = 全绿，1 = 有错。能用规则判的，绝不留给人判。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

KINDS = {
    "not_mentioned",
    "negation",
    "recommended",
    "conditional_support",
    "object_crosstalk",
    "substitution_vs_adjunct",
    "source_misidentification",
    "evidence_mentioned_not_verified",
    "failure",
    "truncation",
    "contradicted",
}
# issue #11 验收第 3 条点名必须覆盖的 kind
REQUIRED_KINDS = {
    "not_mentioned",
    "negation",
    "conditional_support",
    "object_crosstalk",
    "source_misidentification",
    "failure",
    "contradicted",
}
STATES = {
    "not_mentioned",
    "mentioned",
    "opposed",
    "conditional_support",
    "recommended",
    "needs_review",
}
STATUS_VALUES = {"pending_owner_confirmation", "confirmed"}
PATH_KEYS = {"western", "tcm"}

errors: list[str] = []
notes: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def resolve(arg: str) -> Path:
    p = Path(arg)
    return p if p.is_absolute() else ROOT / p


def load_trials(paths: list[Path]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    index: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.is_file():
            err(f"试次文件不存在：{path}")
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                err(f"{path.name} 第 {line_no} 行不是合法 JSON：{e.msg}")
                continue
            tid = row.get("trial_id")
            if tid in index:
                err(f"trial_id 重复：{tid}（{path.name} 第 {line_no} 行）")
            index[tid] = row
    return index, errors


def check_row(row: dict[str, Any], at: str, trials: dict[str, dict[str, Any]]) -> None:
    for field in ("id", "kind", "source", "expected", "rationale", "status"):
        if field not in row:
            err(f"{at}：缺必填字段 `{field}`")
            return

    neg_id = row["id"]
    if not isinstance(neg_id, str) or not neg_id.startswith("neg-"):
        err(f"{at}：id 须为 neg-NNN 格式，当前 {neg_id!r}")
    if row["kind"] not in KINDS:
        err(f"{neg_id}：kind `{row['kind']}` 不在枚举内")
        return
    if row["status"] not in STATUS_VALUES:
        err(f"{neg_id}：status `{row['status']}` 须为 pending_owner_confirmation 或 confirmed")

    source = row["source"]
    text = row.get("text")
    trial: dict[str, Any] | None = None
    if source == "synthetic":
        if not isinstance(text, str) or not text.strip():
            err(f"{neg_id}：source=synthetic 时 text 必须是非空字符串")
    elif isinstance(source, str) and source.startswith("trial:"):
        tid = source[len("trial:") :]
        if text is not None:
            err(f"{neg_id}：source=trial 时 text 必须为 null（原文以 trials 文件为准）")
        trial = trials.get(tid)
        if trial is None:
            err(f"{neg_id}：引用的 trial `{tid}` 不在试次索引中")
            return
    else:
        err(f"{neg_id}：source 须为 `synthetic` 或 `trial:<trial_id>`，当前 {source!r}")
        return

    # 负例 kind 与所引 trial 的真实状态对得上
    if row["kind"] == "failure" and trial is not None and trial.get("status") == "success":
        err(f"{neg_id}：kind=failure 但 trial {trial['trial_id']} 的 status 是 success")
    if row["kind"] == "truncation" and trial is not None and trial.get("finish_reason") != "length":
        err(
            f"{neg_id}：kind=truncation 但 trial {trial['trial_id']} 的 finish_reason 是 "
            f"{trial.get('finish_reason')!r}"
        )

    expected = row["expected"]
    if not isinstance(expected, dict):
        err(f"{neg_id}：expected 必须是对象")
        return
    check_paths(expected.get("paths", {}), neg_id)
    check_citations(expected, neg_id, text, trial)
    if (
        row["kind"] == "source_misidentification"
        and expected.get("identifiable_source") is not False
    ):
        err(f"{neg_id}：kind=source_misidentification 时 identifiable_source 必须为 false")


def check_paths(paths: dict[str, Any], neg_id: str) -> None:
    if not isinstance(paths, dict):
        err(f"{neg_id}：paths 必须是对象（可缺省，表示不适用）")
        return
    for key, entry in paths.items():
        if key not in PATH_KEYS:
            err(f"{neg_id}：paths 键 `{key}` 须为 western/tcm")
            continue
        if not isinstance(entry, dict) or "mentioned" not in entry or "state" not in entry:
            err(f"{neg_id}：paths.{key} 必须含 mentioned 与 state")
            continue
        if entry["state"] not in STATES:
            err(f"{neg_id}：paths.{key}.state `{entry['state']}` 不在枚举内")
        if entry["mentioned"] is False:
            if entry["state"] != "not_mentioned":
                err(f"{neg_id}：paths.{key} mentioned=false 时 state 必须为 not_mentioned")
            for extra in ("attitude_target", "condition", "evidence"):
                if entry.get(extra) not in (None, ""):
                    err(f"{neg_id}：paths.{key} mentioned=false 时不得有 {extra}")
        elif entry["mentioned"] is True and entry["state"] == "not_mentioned":
            err(f"{neg_id}：paths.{key} mentioned=true 时 state 不能是 not_mentioned")


def check_citations(
    expected: dict[str, Any], neg_id: str, text: str | None, trial: dict[str, Any] | None
) -> None:
    """逐字引文必须能在负例自身 text 或所引 trial 原文中定位。"""
    corpus = text if text is not None else (trial or {}).get("response", "")
    if not corpus:
        return
    paths = expected.get("paths", {})
    if isinstance(paths, dict):
        for key in ("western", "tcm"):
            quote = paths.get(key, {}).get("evidence") if isinstance(paths.get(key), dict) else None
            if isinstance(quote, str) and quote and quote not in corpus:
                err(f"{neg_id}：paths.{key}.evidence 引文未在原文中逐字定位")
    quote = expected.get("source_evidence")
    if isinstance(quote, str) and quote and quote not in corpus:
        err(f"{neg_id}：source_evidence 引文未在原文中逐字定位")


def check_coverage(rows: list[dict[str, Any]], require_confirmed: bool) -> None:
    present = {r.get("kind") for r in rows}
    missing = REQUIRED_KINDS - present
    if missing:
        err(f"负例集缺少 issue #11 要求的 kind：{sorted(missing)}")
    if require_confirmed:
        confirmed = {r.get("kind") for r in rows if r.get("status") == "confirmed"}
        missing_confirmed = REQUIRED_KINDS - confirmed
        if missing_confirmed:
            err(
                "人工定标尚未完成：以下 kind 还没有 confirmed 条目 "
                f"{sorted(missing_confirmed)}（主人逐条确认后把 status 改为 confirmed）"
            )
    n_pending = sum(1 for r in rows if r.get("status") == "pending_owner_confirmation")
    if n_pending:
        notes.append(f"{n_pending} 条负例仍为 pending_owner_confirmation，语义判定待主人确认")


def check_denominator(baseline: Path, rows: list[dict[str, Any]], expect: dict[str, int]) -> None:
    """口径：planned = stop（完整回答）+ length（截断单列）；截断不算未提及。"""
    if not baseline.is_file():
        err(f"基线文件不存在：{baseline}")
        return
    trials = [
        json.loads(line)
        for line in baseline.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    finish: dict[str, int] = {}
    for t in trials:
        reason = t.get("finish_reason")
        finish[reason] = finish.get(reason, 0) + 1
    planned, stop, length = len(trials), finish.get("stop", 0), finish.get("length", 0)
    if planned != expect["planned"] or stop != expect["stop"] or length != expect["length"]:
        err(
            f"基线分母与口径不符：planned={planned}/stop={stop}/length={length}，"
            f"预期 {expect['planned']}/{expect['stop']}/{expect['length']}"
        )
    other = {k: v for k, v in finish.items() if k not in ("stop", "length")}
    if other:
        err(f"基线出现 stop/length 之外的 finish_reason：{other}——先确认口径再扩展枚举")
    truncated_ids = {t["trial_id"] for t in trials if t.get("finish_reason") == "length"}
    cited = {
        r["source"][len("trial:") :]
        for r in rows
        if r.get("kind") == "truncation" and isinstance(r.get("source"), str)
    }
    if truncated_ids != cited:
        err(
            f"截断负例与基线截断集合不一致：基线 {sorted(truncated_ids)}，"
            f"负例引用 {sorted(cited)}——数据换版后须同步负例"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--negatives",
        default="specs/examples/negatives.jsonl",
        help="负例集路径（相对仓库根）",
    )
    parser.add_argument(
        "--trials",
        nargs="+",
        default=[
            "docs/experiments/exp001-protocol-smoke/fixtures.jsonl",
            "docs/experiments/exp003-baseline/result/trials.jsonl",
        ],
        help="供 trial 引用核对的试次文件（相对仓库根，可多个）",
    )
    parser.add_argument(
        "--baseline",
        default="docs/experiments/exp003-baseline/result/trials.jsonl",
        help="分母口径核对的基线文件（相对仓库根）",
    )
    parser.add_argument("--expect-planned", type=int, default=27)
    parser.add_argument("--expect-stop", type=int, default=24)
    parser.add_argument("--expect-length", type=int, default=3)
    parser.add_argument(
        "--require-confirmed",
        action="store_true",
        help="要求 issue #11 必备 kind 全部有 confirmed 条目（人工定标完成后使用）",
    )
    args = parser.parse_args()

    negatives_path = resolve(args.negatives)
    if not negatives_path.is_file():
        print(f"✗ 负例集不存在：{negatives_path}")
        return 1
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(negatives_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            err(f"negatives.jsonl 第 {line_no} 行不是合法 JSON：{e.msg}")
    ids = [r.get("id") for r in rows]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        err(f"负例 id 重复：{sorted(dupes)}")

    trials_index, _ = load_trials([resolve(p) for p in args.trials])
    for i, row in enumerate(rows):
        check_row(row, f"第 {i + 1} 行", trials_index)
    check_coverage(rows, args.require_confirmed)
    check_denominator(
        resolve(args.baseline),
        rows,
        {"planned": args.expect_planned, "stop": args.expect_stop, "length": args.expect_length},
    )

    for n in notes:
        print(f"  · {n}")
    if errors:
        print()
        for e in errors:
            print(f"✗ {e}")
        print(f"\n{len(errors)} 个错误。")
        return 1
    print(
        f"\n✓ 全绿（负例 {len(rows)} 条；分母 {args.expect_planned}=完整 {args.expect_stop}+截断 {args.expect_length}）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
