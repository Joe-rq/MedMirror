#!/usr/bin/env python3
"""执行 exp003 有界追问（issue #2）。

输入基线 trials 与 v2 提取结果，按固定触发规则选择候选（每模型最多 1 个），
统一模板追问，限额每模型 2 次/全轮 6 次，预算经 Ledger 硬闸。产物：
run 目录下 followups.jsonl（追加式）+ budget.jsonl；findings.jsonl 物化到
docs/experiments/exp003-baseline/followup/（Git 跟踪，保存追问证据）。

- 未传 --allow-paid 时零网络请求；--plan-only 仅打印候选与选择理由；
- 同目录恢复：已成功的追问不重复调用（预算与基线一致按账本锁定）。

用法：
  uv run python scripts/run_exp003_followup.py --plan-only
  uv run python scripts/run_exp003_followup.py --allow-paid --budget 1.0
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medmirror import followup, runner
from medmirror.budget import Ledger
from medmirror.providers import load_catalog, load_local_env, model_registry

DEFAULT_TRIALS = ROOT / "docs/experiments/exp003-baseline/result/trials.jsonl"
DEFAULT_EXTRACTIONS = ROOT / "docs/experiments/exp003-baseline/derived-v3/extractions.jsonl"
FINDINGS_DIR = ROOT / "docs/experiments/exp003-baseline/followup"
NO_CANDIDATES_DIR = ROOT / "runs/exp003-followup/no-candidates"
DEFAULT_BUDGET_CNY = 1.0
PROTECTED_PARENT = ROOT / "docs/experiments/exp003-baseline/result"


def record_no_candidates() -> None:
    """无候选也是一次可追溯的运行：落盘空结果（防「本轮无候选」与「上轮有候选」混淆）。"""
    NO_CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    (NO_CANDIDATES_DIR / "result.json").write_text(
        json.dumps(
            {
                "rule_version": followup.RULE_VERSION,
                "candidate_count": 0,
                "stop_reason": "no_candidates",
                "at": datetime.now(UTC).isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_prices() -> dict[str, dict[str, float]]:
    catalog = load_catalog()
    return {item["vendor"]: item["pricing"] for item in catalog["models"] if item.get("pricing")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=Path, default=DEFAULT_TRIALS, help="基线 trials.jsonl")
    parser.add_argument("--extractions", type=Path, default=DEFAULT_EXTRACTIONS)
    parser.add_argument("--allow-paid", action="store_true", help="显式允许真实付费调用")
    parser.add_argument("--plan-only", action="store_true", help="仅列出候选与选择理由，零请求")
    parser.add_argument(
        "--budget", type=float, default=DEFAULT_BUDGET_CNY, help="本轮追问预算（元）"
    )
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--max-attempts", type=int, default=followup.DEFAULT_MAX_ATTEMPTS)
    parser.add_argument(
        "--run-dir", type=Path, default=None, help="追问 run 目录（缺省新建；传入即恢复）"
    )
    args = parser.parse_args(argv)
    if args.plan_only and args.allow_paid:
        parser.error("--plan-only 与 --allow-paid 互斥")
    if not 1 <= args.max_attempts <= followup.MAX_PER_MODEL:
        parser.error(
            f"--max-attempts 必须在 1 到 {followup.MAX_PER_MODEL} 之间"
            "（追问失败重试不得突破每模型固定上限）"
        )

    trials, extractions = followup.load_trials_and_extractions(args.trials, args.extractions)
    missing = sorted(set(trials) - set(extractions))
    if missing:
        parser.error(f"提取结果缺少 {len(missing)} 条基线试次（如 {missing[0]}），先跑 #12 提取")

    candidates = followup.select_candidates(trials, extractions)
    if not candidates:
        record_no_candidates()
        followup.write_findings(FINDINGS_DIR / "findings.jsonl", [])
        print("无候选：三家均不满足「中性全未提及且镜像完整提及」触发规则，正常结束（已记录）")
        return 0
    print(f"候选 {len(candidates)} 个（每模型最多 1，路径顺序 {'→'.join(followup.PATH_ORDER)}）：")
    for candidate in candidates:
        print(f"  {candidate['followup_id']} [{candidate['path']}]")
        print(f"    理由：{candidate['selection_reason']}")

    if args.plan_only:
        return 0

    if not args.allow_paid:
        parser.error(
            "真实调用会产生 API 费用，请显式传入 --allow-paid（或用 --plan-only 查看候选）"
        )

    load_local_env()
    registry = model_registry()
    missing_keys = [c.api_key_env for c in registry.values() if not os.getenv(c.api_key_env)]
    if missing_keys:
        parser.error("缺少密钥变量：" + ", ".join(missing_keys))

    params = runner.request_params()
    fingerprint = runner.config_fingerprint(runner.planned_trials(registry, 1), params)
    if args.run_dir is None:
        run_dir = ROOT / "runs/exp003-followup" / runner.run_id_for(fingerprint)
    else:
        run_dir = args.run_dir.resolve()
        protected = PROTECTED_PARENT.resolve()
        if run_dir == protected or protected in run_dir.parents or run_dir in protected.parents:
            parser.error(
                f"拒绝执行：--run-dir（{run_dir}）位于历史原件目录内或其祖先，"
                "追问运行必须写入独立 run 目录（runs/ 下），历史数据不覆盖"
            )
    run_dir.mkdir(parents=True, exist_ok=True)

    # plan 锁定配置指纹与 max_attempts：恢复换配置/换上限拒绝同目录混写（同 #13 契约）
    followup.prepare_plan(
        run_dir=run_dir,
        candidates=candidates,
        params=params,
        max_attempts=args.max_attempts,
        registry=registry,
    )
    ledger = Ledger(run_dir / "budget.jsonl", total_cny=args.budget)
    if abs(ledger.state.total_cny - args.budget) > 1e-9:
        parser.error(
            f"恢复失败：目录 {run_dir.name} 的预算总额 {ledger.state.total_cny} 元"
            f"与当前传入 {args.budget} 元不一致；预算锁定在首次 run（与基线 #13 契约一致）"
        )
    transport = _RealTransportBridge(args.timeout)
    stats = followup.execute_followups(
        run_dir=run_dir,
        candidates=candidates,
        registry=registry,
        transport=transport,
        ledger=ledger,
        prices=load_prices(),
        params=params,
        max_attempts=args.max_attempts,
    )
    stop_reasons = {o["followup_id"]: o["stop_reason"] for o in stats["outcomes"]}
    rows = followup.load_followup_rows(run_dir / "followups.jsonl")
    findings = followup.build_findings(candidates, rows, extractions, stop_reasons)
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    followup.write_findings(FINDINGS_DIR / "findings.jsonl", findings)
    # 追问原始记录物化到 docs（证据保存，Git 跟踪）；runs/ 过程件另行备份（#4）
    rows_flat = []
    for (_fid, _attempt), row in sorted(rows.items()):
        rows_flat.append({k: v for k, v in row.items() if k != "finished"})
        if row.get("finished"):
            rows_flat.append(row["finished"])
    (FINDINGS_DIR / "followups.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows_flat), encoding="utf-8"
    )
    print(
        f"追问完成：候选 {stats['candidates']}／执行 {stats['executed']}／复用 {stats['reused']}"
        f"／预算拒绝 {stats['budget_refused']}／待核账 {stats['pending_reconciliation']}；"
        f"账本可用余额 {ledger.state.available_cny} 元"
    )
    print(f"findings：{FINDINGS_DIR / 'findings.jsonl'}")
    return 0


class _RealTransportBridge:
    def __init__(self, timeout: int):
        self.timeout = timeout

    def call(self, config, spec, params):
        return runner.real_transport(
            config, spec, params, os.environ[config.api_key_env], self.timeout
        )


if __name__ == "__main__":
    raise SystemExit(main())
