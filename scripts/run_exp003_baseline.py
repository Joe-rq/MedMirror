#!/usr/bin/env python3
"""执行 exp003 基线运行（issue #13 新架构）。

每次运行写独立 run 目录 `runs/exp003-baseline/<时间戳-配置指纹>/`：
plan.json（完整计划+脱敏配置快照）、attempts.jsonl（追加式逐次尝试）、
trials.jsonl（物化视图，可直接喂 #10 报告 CLI）、budget.jsonl（预算账本）。

- 同目录恢复：同配置指纹的成功试次直接复用，不重复调用；
- 换模型/参数/协议：目录指纹不匹配即拒绝，须新开 run，不混写历史；
- 未传 --allow-paid 时零网络请求（与旧版闸门一致）；--plan-only 仅生成计划。

历史原件 `docs/experiments/exp003-baseline/result/` 已冻结，本脚本不再写入。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medmirror import runner
from medmirror.budget import Ledger
from medmirror.providers import load_catalog, load_local_env, model_registry

DEFAULT_BUDGET_CNY = 50.0
PROTECTED_PARENT = ROOT / "docs/experiments/exp003-baseline"


def load_prices() -> dict[str, dict[str, float]]:
    catalog = load_catalog()
    return {item["vendor"]: item["pricing"] for item in catalog["models"] if item.get("pricing")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=1, help="每个组合的重复次数")
    parser.add_argument("--allow-paid", action="store_true", help="显式允许真实付费 API 调用")
    parser.add_argument("--plan-only", action="store_true", help="仅生成计划与未执行视图，零请求")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--max-attempts", type=int, default=runner.DEFAULT_MAX_ATTEMPTS)
    parser.add_argument(
        "--budget", type=float, default=DEFAULT_BUDGET_CNY, help="本轮预算总额（元）"
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="run 目录（缺省按时间戳+配置指纹新建；传入已有目录即恢复/扩量）",
    )
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("--repeats 必须大于 0")
    if not 1 <= args.max_attempts <= 10:
        parser.error("--max-attempts 必须在 1 到 10 之间")
    if args.plan_only and args.allow_paid:
        parser.error("--plan-only 与 --allow-paid 互斥")

    load_local_env()
    registry = model_registry()

    specs = runner.planned_trials(registry, args.repeats)
    fingerprint = runner.config_fingerprint(specs, runner.request_params())
    if args.run_dir is None:
        run_dir = ROOT / "runs/exp003-baseline" / runner.run_id_for(fingerprint)
    else:
        run_dir = args.run_dir.resolve()
        protected = PROTECTED_PARENT.resolve()
        if run_dir == protected or protected in run_dir.parents or run_dir in protected.parents:
            parser.error(
                f"拒绝执行：--run-dir（{run_dir}）位于历史原件目录（{protected}）内或其祖先，"
                "新运行必须写入独立 run 目录（runs/ 下），历史数据不覆盖"
            )

    if args.plan_only:
        stats = runner.execute_run(
            run_dir=run_dir,
            registry=registry,
            repeats=args.repeats,
            transport=None,
            ledger=None,
            prices=None,
            max_attempts=args.max_attempts,
            resume=True,
            plan_only=True,
        )
        print(f"plan-only 完成：计划 {stats['view_total']} 条（全部 not_executed，零请求）")
        print(f"run 目录：{run_dir}")
        return 0

    if not args.allow_paid:
        parser.error(
            "真实调用会产生 API 费用，请显式传入 --allow-paid（或用 --plan-only 离线生成计划）"
        )
    missing = [c.api_key_env for c in registry.values() if not os.getenv(c.api_key_env)]
    if missing:
        parser.error("缺少密钥变量：" + ", ".join(missing))
    transport = _RealTransportBridge(args.timeout)

    print(f"run 目录：{run_dir}", flush=True)  # 提前打印：中断时用户可直接 --run-dir 恢复
    ledger = Ledger(run_dir / "budget.jsonl", total_cny=args.budget)
    stats = runner.execute_run(
        run_dir=run_dir,
        registry=registry,
        repeats=args.repeats,
        transport=transport,
        ledger=ledger,
        prices=load_prices(),
        max_attempts=args.max_attempts,
        budget_total_cny=args.budget,
        resume=True,
    )
    print(
        f"run={run_dir.name} 指纹={fingerprint[:8]} 复用 {stats['reused']}／执行 {stats['executed']}"
        f"／待核账 {stats['pending_reconciliation']}／attempt 上限跳过 {stats['skipped']}"
        f"／预算拒绝 {stats['budget_refused']}；账本可用余额 {ledger.state.available_cny} 元"
    )
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
