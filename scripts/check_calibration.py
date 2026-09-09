#!/usr/bin/env python3
"""规则验证层：校验 specs/examples/negatives.jsonl 的结构与引文，核对基线分母口径。

负例集是 #11 人工定标的机器可检部分：结构、逐字引文、trial 引用、kind 覆盖与
27 条基线的截断分母。语义是否正确仍以人工定标为准——本脚本通过不等于评分正确
（specs/calibration.md §4），`expected` 逐条经主人确认后才从 pending 转 confirmed。

kind 语义是「本条负例考查什么」：状态考查（not_mentioned/negation/recommended/
conditional_support 防止状态误判）、缺陷考查（object_crosstalk/substitution_vs_
adjunct/source_misidentification/evidence_mentioned_not_verified/contradicted）、
数据状态考查（failure/truncation）。期望判定本身在 expected.paths.*.state。

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
# kind -> expected 结构要求
PATH_KINDS = {  # 必须给出非空 paths 判定
    "not_mentioned",
    "negation",
    "recommended",
    "conditional_support",
    "object_crosstalk",
    "substitution_vs_adjunct",
    "contradicted",
}
SOURCE_KINDS = {  # 必须给出 identifiable_source 或 evidence_mentioned 判定
    "source_misidentification",
    "evidence_mentioned_not_verified",
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
# 失败/截断对指标分母的结构化归属（denominator-policy.md）；机器核验，不靠散文
DENOMINATOR_EFFECT = {
    "failure": "excluded_from_valid",
    "truncation": "excluded_from_complete",
}

errors: list[str] = []
notes: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def resolve(arg: str) -> Path:
    p = Path(arg)
    return p if p.is_absolute() else ROOT / p


def parse_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    """逐行解析并保证每行是对象；坏行计错误、不中断其余检查。"""
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        err(f"{label}不存在：{path}")
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            err(f"{label}第 {line_no} 行不是合法 JSON：{e.msg}")
            continue
        if not isinstance(row, dict):
            err(f"{label}第 {line_no} 行不是 JSON 对象")
            continue
        rows.append(row)
    return rows


def load_trials(paths: list[Path]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for path in paths:
        for row in parse_jsonl(path, f"试次文件（{path.name}）"):
            tid = row.get("trial_id")
            if not isinstance(tid, str):
                continue
            if tid in index:
                err(f"trial_id 重复：{tid}（{path.name}）")
            index[tid] = row
    return index


def check_path_entry(entry: Any, key: str, neg_id: str) -> None:
    if not isinstance(entry, dict) or "mentioned" not in entry or "state" not in entry:
        err(f"{neg_id}：paths.{key} 必须是含 mentioned 与 state 的对象")
        return
    if not isinstance(entry["mentioned"], bool):
        err(f"{neg_id}：paths.{key}.mentioned 必须是布尔值，当前 {entry['mentioned']!r}")
        return
    if not isinstance(entry["state"], str) or entry["state"] not in STATES:
        err(f"{neg_id}：paths.{key}.state `{entry['state']}` 不在枚举内或不是字符串")
    if entry["mentioned"] is False:
        if entry["state"] != "not_mentioned":
            err(f"{neg_id}：paths.{key} mentioned=false 时 state 必须为 not_mentioned")
        for extra in ("attitude_target", "condition", "evidence"):
            if entry.get(extra) not in (None, ""):
                err(f"{neg_id}：paths.{key} mentioned=false 时不得有 {extra}")
    elif entry["state"] == "not_mentioned":
        err(f"{neg_id}：paths.{key} mentioned=true 时 state 不能是 not_mentioned")


def check_citations(
    expected: dict[str, Any], neg_id: str, text: str | None, trial: dict[str, Any] | None
) -> None:
    """引文字段必须是字符串，且逐字出现在负例 text 或所引 trial 正文中。"""
    corpus = text if text is not None else (trial or {}).get("response", "")
    quotes: list[tuple[str, Any]] = []
    paths = expected.get("paths", {})
    if isinstance(paths, dict):
        for key in ("western", "tcm"):
            entry = paths.get(key)
            if isinstance(entry, dict):
                quotes.append((f"paths.{key}.evidence", entry.get("evidence")))
    quotes.append(("source_evidence", expected.get("source_evidence")))
    for field, quote in quotes:
        if quote in (None, ""):
            continue
        if not isinstance(quote, str):
            err(f"{neg_id}：{field} 必须是字符串，当前 {type(quote).__name__}")
        elif not corpus:
            err(f"{neg_id}：正文为空（失败/空回答）却有 {field} 引文，无从核对")
        elif quote not in corpus:
            err(f"{neg_id}：{field} 引文未在原文中逐字定位")


def check_row(row: dict[str, Any], at: str, trials: dict[str, dict[str, Any]]) -> None:
    for field in ("id", "kind", "source", "expected", "rationale", "status"):
        if field not in row:
            err(f"{at}：缺必填字段 `{field}`")
            return

    neg_id = row["id"]
    if not isinstance(neg_id, str) or not neg_id.startswith("neg-"):
        err(f"{at}：id 须为 neg-NNN 格式，当前 {neg_id!r}")
    kind = row["kind"]
    if not isinstance(kind, str) or kind not in KINDS:
        err(f"{neg_id}：kind `{kind}` 不在枚举内或不是字符串")
        return
    if not isinstance(row["status"], str) or row["status"] not in STATUS_VALUES:
        err(f"{neg_id}：status `{row['status']}` 须为 pending_owner_confirmation 或 confirmed")

    source = row["source"]
    text = row.get("text")
    trial: dict[str, Any] | None = None
    cites_trial = isinstance(source, str) and source.startswith("trial:")
    if source == "synthetic":
        if not isinstance(text, str) or not text.strip():
            err(f"{neg_id}：source=synthetic 时 text 必须是非空字符串")
    elif cites_trial:
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

    # 失败/截断是数据状态考查，必须引用真实 trial；合成截断没有意义
    if kind in ("failure", "truncation") and not cites_trial:
        err(f"{neg_id}：kind={kind} 必须引用真实 trial（source=trial:…）")

    # 负例 kind 与所引 trial 的真实状态对得上
    if kind == "failure" and trial is not None and trial.get("status") == "success":
        err(f"{neg_id}：kind=failure 但 trial {trial['trial_id']} 的 status 是 success")
    if kind == "truncation" and trial is not None and trial.get("finish_reason") != "length":
        err(
            f"{neg_id}：kind=truncation 但 trial {trial['trial_id']} 的 finish_reason 是 "
            f"{trial.get('finish_reason')!r}"
        )

    expected = row["expected"]
    if not isinstance(expected, dict):
        err(f"{neg_id}：expected 必须是对象")
        return
    paths = expected.get("paths", {})

    # 来源判定字段：出现即必须是布尔（防「一真掩一假」绕过）
    for field in ("identifiable_source", "evidence_mentioned"):
        value = expected.get(field)
        if value is not None and not isinstance(value, bool):
            err(f"{neg_id}：expected.{field} 必须是布尔值，当前 {value!r}")

    if kind in PATH_KINDS and not (isinstance(paths, dict) and paths):
        err(f"{neg_id}：kind={kind} 必须给出非空 paths 判定")
    if kind == "failure" and paths:
        err(f"{neg_id}：kind=failure 的回答无正文，不得有 paths 判定")
    if kind in ("failure", "truncation"):
        note = expected.get("status_note")
        if not isinstance(note, str) or not note.strip():
            err(f"{neg_id}：kind={kind} 必须有 status_note")
        # truncation 的 paths 可选：仅为「截断文内观察」
    if kind in SOURCE_KINDS:
        has_source_verdict = isinstance(expected.get("identifiable_source"), bool) or isinstance(
            expected.get("evidence_mentioned"), bool
        )
        if not has_source_verdict:
            err(
                f"{neg_id}：kind={kind} 必须给出 identifiable_source 或 evidence_mentioned 布尔判定"
            )
    if kind == "source_misidentification" and expected.get("identifiable_source") is not False:
        err(f"{neg_id}：kind=source_misidentification 时 identifiable_source 必须为 false")
    if kind == "substitution_vs_adjunct":
        tcm = paths.get("tcm") if isinstance(paths, dict) else None
        if not isinstance(tcm, dict):
            err(f"{neg_id}：kind=substitution_vs_adjunct 须在 paths.tcm 给出替代/辅助判定")
        else:
            for role in ("substitution", "adjunct"):
                value = tcm.get(role)
                if not isinstance(value, str) or value not in STATES:
                    err(
                        f"{neg_id}：paths.tcm.{role} 须为 STATES 枚举字符串（替代与辅助分开编码的落点）"
                    )

    # 分母归属：失败/截断的排除规则结构化，不靠 status_note 散文
    if (
        kind in DENOMINATOR_EFFECT
        and expected.get("denominator_effect") != DENOMINATOR_EFFECT[kind]
    ):
        err(
            f"{neg_id}：kind={kind} 的 denominator_effect 必须为 "
            f"`{DENOMINATOR_EFFECT[kind]}`（当前 {expected.get('denominator_effect')!r}）"
        )

    if isinstance(paths, dict):
        for key, entry in paths.items():
            if key not in PATH_KEYS:
                err(f"{neg_id}：paths 键 `{key}` 须为 western/tcm")
                continue
            check_path_entry(entry, key, neg_id)
    elif paths != {}:
        err(f"{neg_id}：paths 必须是对象")
    check_citations(expected, neg_id, text, trial)


def check_coverage(rows: list[dict[str, Any]], require_confirmed: bool) -> None:
    present = {r["kind"] for r in rows if isinstance(r.get("kind"), str)}
    missing = REQUIRED_KINDS - present
    if missing:
        err(f"负例集缺少 issue #11 要求的 kind：{sorted(missing)}")
    n_pending = sum(1 for r in rows if r.get("status") == "pending_owner_confirmation")
    if n_pending:
        if require_confirmed:
            err(
                f"人工定标尚未完成：{n_pending} 条负例仍为 pending_owner_confirmation，"
                "主人须逐条确认后把 status 改为 confirmed（要求全部条目，不只必备 kind）"
            )
        else:
            notes.append(f"{n_pending} 条负例仍为 pending_owner_confirmation，语义判定待主人确认")


def check_denominator(baseline: Path, rows: list[dict[str, Any]], expect: dict[str, int]) -> None:
    """口径：planned = stop（完整回答）+ length（截断单列）；截断不算未提及。

    完整回答定义 = finish_reason=stop 且 status=success 且正文非空（denominator-policy.md）。
    """
    trials = parse_jsonl(baseline, "基线文件")
    if not trials:
        err(f"基线文件无有效记录：{baseline}")
        return
    finish: dict[str, int] = {}
    for t in trials:
        reason = t.get("finish_reason")
        if not isinstance(reason, str):
            err(f"{t.get('trial_id')}：finish_reason 必须是字符串，当前 {reason!r}")
            continue
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

    def has_body(t: dict[str, Any]) -> bool:
        response = t.get("response")
        return isinstance(response, str) and bool(response.strip())

    inconsistent = [
        t.get("trial_id")
        for t in trials
        if t.get("finish_reason") == "stop" and (t.get("status") != "success" or not has_body(t))
    ]
    if inconsistent:
        err(
            f"finish=stop 但 status 非 success 或正文为空/纯空白，不满足完整回答定义：{inconsistent}"
        )
    overlap = [
        t.get("trial_id")
        for t in trials
        if t.get("status") != "success" and t.get("finish_reason") == "length"
    ]
    if overlap:
        err(
            f"失败与截断分类重叠（status≠success 且 finish=length）：{overlap}——口径未定义，须人工裁定"
        )
    truncated_ids = {t["trial_id"] for t in trials if t.get("finish_reason") == "length"}
    cited = {
        r["source"][len("trial:") :]
        for r in rows
        if r.get("kind") == "truncation"
        and isinstance(r.get("source"), str)
        and r["source"].startswith("trial:")
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
        help="人工定标完成后使用：要求全部负例（不只必备 kind）已 confirmed",
    )
    args = parser.parse_args()

    rows = parse_jsonl(resolve(args.negatives), "负例集")
    ids = [r.get("id") for r in rows]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        err(f"负例 id 重复：{sorted(dupes)}")

    trials_index = load_trials([resolve(p) for p in args.trials])
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
