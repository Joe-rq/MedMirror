#!/usr/bin/env python3
"""账单核对：读 run 目录的 budget.jsonl + attempts.jsonl，按登记价格复算每笔
settle 的期望成本、与账本实际结算比对，输出差异报告（issue #3）。

用法：
  uv run python scripts/reconcile_budget.py --run-dir runs/exp003-baseline/<run_id>
  uv run python scripts/reconcile_budget.py --trials docs/experiments/exp003-baseline/result/trials.jsonl
    （无 run 目录时对历史 trials 按登记价格复算估算成本）

输出：结算差异表 + pending_charge 未核金额 + 历史估算 vs 复算差额。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medmirror.budget import actual_cost_cny
from medmirror.protocol import load_jsonl
from medmirror.runner import load_attempts


def load_prices() -> dict[str, dict[str, float]]:
    catalog = json.loads((ROOT / "configs/models.json").read_text(encoding="utf-8"))
    return {item["vendor"]: item["pricing"] for item in catalog["models"] if item.get("pricing")}


def reconcile_ledger(run_dir: Path, prices: dict) -> dict:
    """对照 budget.jsonl 的每笔 settle 事件，按 attempt 的 usage 复算期望成本。"""
    budget_path = run_dir / "budget.jsonl"
    attempts_path = run_dir / "attempts.jsonl"
    if not budget_path.is_file():
        raise SystemExit(f"✗ {budget_path} 不存在——需要 #13 架构的 run 目录")

    attempts = load_attempts(attempts_path)
    events = [
        json.loads(line)
        for line in budget_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    settled_total = 0.0
    pending_total = 0.0
    rows: list[dict] = []
    for event in events:
        kind = event["kind"]
        if kind == "settle":
            settled_total += event["amount_cny"]
            key = (event["trial_id"], event["attempt"])
            attempt = attempts.get(key)
            usage = (attempt or {}).get("finished", {}).get("usage")
            vendor = (attempt or {}).get("vendor")
            expected = actual_cost_cny(prices, vendor, usage) if vendor else None
            diff = round(event["amount_cny"] - expected, 6) if expected is not None else None
            rows.append(
                {
                    "trial_id": event["trial_id"],
                    "attempt": event["attempt"],
                    "ledger_cny": event["amount_cny"],
                    "expected_cny": expected,
                    "diff_cny": diff,
                    "usage": usage,
                }
            )
        elif kind == "pending_charge":
            pending_total += event["amount_cny"]

    init_event = next((e for e in events if e["kind"] == "init"), None)
    total_budget = init_event["amount_cny"] if init_event else None
    refund_total = sum(e["amount_cny"] for e in events if e["kind"] == "refund")

    diffs = [r["diff_cny"] for r in rows if r["diff_cny"] is not None and abs(r["diff_cny"]) > 1e-9]
    return {
        "total_budget_cny": total_budget,
        "settled_cny": round(settled_total, 6),
        "pending_charge_cny": round(pending_total, 6),
        "refunded_cny": round(refund_total, 6),
        "available_cny": round((total_budget or 0) - settled_total - pending_total, 6),
        "settle_count": len(rows),
        "mismatch_count": len(diffs),
        "rows": rows,
    }


def reconcile_trials(trials_path: Path, prices: dict) -> dict:
    """对历史 trials.jsonl 按登记价格复算估算成本（无账本时的降级核对）。"""
    trials = load_jsonl(trials_path)
    by_vendor: dict[str, dict[str, int]] = {}
    for trial in trials:
        usage = trial.get("usage")
        vendor = trial.get("vendor")
        if not isinstance(usage, dict) or not vendor:
            continue
        bucket = by_vendor.setdefault(
            vendor, {"prompt_tokens": 0, "completion_tokens": 0, "count": 0}
        )
        bucket["prompt_tokens"] += int(usage.get("prompt_tokens") or 0)
        bucket["completion_tokens"] += int(usage.get("completion_tokens") or 0)
        bucket["count"] += 1

    costs: dict[str, float] = {}
    for vendor, tokens in sorted(by_vendor.items()):
        if vendor not in prices:
            costs[vendor] = -1  # 价格未知
            continue
        price = prices[vendor]
        costs[vendor] = round(
            (
                tokens["prompt_tokens"] * price["input_cache_miss"]
                + tokens["completion_tokens"] * price["output"]
            )
            / 1_000_000,
            6,
        )
    return {
        "by_vendor": by_vendor,
        "estimated_cost_cny": costs,
        "total_cny": round(sum(v for v in costs.values() if v >= 0), 6),
    }


def render(result: dict, mode: str) -> str:
    lines = ["# 账单核对报告（issue #3）", "", f"- 模式：{mode}", ""]
    if mode == "ledger":
        lines.extend(
            [
                f"- 预算总额：{result['total_budget_cny']} 元",
                f"- 已结算：{result['settled_cny']} 元（{result['settle_count']} 笔）",
                f"- 待核账（pending_charge）：{result['pending_charge_cny']} 元",
                f"- 已退还：{result['refunded_cny']} 元",
                f"- 可用余额：{result['available_cny']} 元",
                f"- 结算差异：{result['mismatch_count']} 笔（非零差额）",
                "",
            ]
        )
        if result["rows"]:
            lines.extend(
                ["| trial | attempt | 账本结算 | 复算期望 | 差额 |", "|---|---:|---:|---:|---:|"]
            )
            for row in result["rows"]:
                diff = row["diff_cny"] if row["diff_cny"] is not None else "无法复算"
                lines.append(
                    f"| {row['trial_id']} | {row['attempt']} | {row['ledger_cny']} | "
                    f"{row['expected_cny'] if row['expected_cny'] is not None else '?'} | {diff} |"
                )
    else:
        lines.extend(
            [
                f"- 估算总成本：{result['total_cny']} 元（按登记价格、DeepSeek 高峰）",
                "",
                "| 供应商 | 试次数 | prompt tokens | completion tokens | 估算成本（元） |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for vendor, tokens in result["by_vendor"].items():
            cost = result["estimated_cost_cny"].get(vendor, -1)
            lines.append(
                f"| {vendor} | {tokens['count']} | {tokens['prompt_tokens']} | "
                f"{tokens['completion_tokens']} | {cost if cost >= 0 else '价格未知'} |"
            )
    lines.extend(
        [
            "",
            "## 待主人核对",
            "",
            "1. 登录三家控制台核对实际账单/额度变动（时间范围 + 计费口径）",
            "2. 把实际金额填入 `specs/calibration/bill-check.md`",
            "3. 差额超出估算的部分单独列出原因（历史重试/诊断/闲时价格差）",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, help="#13 架构的 run 目录（含 budget.jsonl）")
    parser.add_argument("--trials", type=Path, help="历史 trials.jsonl（无 run 目录时的降级核对）")
    parser.add_argument("--output", type=Path, help="报告输出路径（缺省打印到终端）")
    args = parser.parse_args(argv)

    prices = load_prices()
    if args.run_dir:
        result = reconcile_ledger(args.run_dir.resolve(), prices)
        report = render(result, "ledger")
    elif args.trials:
        result = reconcile_trials(args.trials.resolve(), prices)
        report = render(result, "trials")
    else:
        parser.error("需要 --run-dir 或 --trials 之一")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8", newline="\n")
        print(f"报告已写入：{args.output}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
