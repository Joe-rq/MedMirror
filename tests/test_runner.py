"""Issue #13 回归：独立 run 目录、追加式 attempt、恢复语义、预算账本（全部假网络）。

本文件零真实请求：传输层由 FakeTransport 注入，验证的是运行记录保护本身——
历史不覆盖、同配置不重复调用、换配置不误复用、崩溃可恢复、预算受约束。
"""

import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from medmirror.budget import BudgetError, Ledger, actual_cost_cny, estimate_cost_cny
from medmirror.runner import (
    DEFAULT_MAX_ATTEMPTS,
    append_jsonl,
    config_fingerprint,
    execute_run,
    load_attempts,
    load_jsonl_tolerant,
    planned_trials,
    request_params,
    trial_outcome,
)

PRICES = {
    "deepseek": {"input_cache_miss": 1.0, "output": 2.0},
    "glm": {"input_cache_miss": 0.5, "output": 1.0},
}


def make_registry(model_id="m-1", vendor="deepseek"):
    return {
        "cat-1": SimpleNamespace(
            model_id=model_id, vendor=vendor, endpoint="http://fake/ep", api_key_env="FAKE_KEY"
        )
    }


def success_outcome(response="建议使用他汀。", finish_reason="stop"):
    return {
        "status": "success",
        "http_status": 200,
        "response": response,
        "provider_model": "provider-returned-model",
        "finish_reason": finish_reason,
        "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        "elapsed_ms": 5,
        "reasoning_present": False,
        "reasoning_chars": 0,
        "response_fields": ["content"],
    }


class FakeTransport:
    """可编程假网络：按 trial_id 返回预设结果，记录全部调用。"""

    def __init__(self, resolver):
        self.resolver = resolver
        self.calls: list[str] = []

    def call(self, config, spec, params):
        self.calls.append(spec["trial_id"])
        return self.resolver(spec)


def always_success(spec):
    return success_outcome(f"回答-{spec['trial_id']}")


def run_once(
    run_dir,
    registry=None,
    repeats=1,
    resolver=always_success,
    budget=100.0,
    prices=None,
    max_attempts=DEFAULT_MAX_ATTEMPTS,
):
    registry = registry or make_registry()
    transport = FakeTransport(resolver)
    ledger = Ledger(run_dir / "budget.jsonl", total_cny=budget)
    stats = execute_run(
        run_dir=run_dir,
        registry=registry,
        repeats=repeats,
        transport=transport,
        ledger=ledger,
        prices=prices if prices is not None else PRICES,
        max_attempts=max_attempts,
        verbose=False,
    )
    return stats, transport, ledger


class PlanAndFingerprintTest(unittest.TestCase):
    def test_fingerprint_excludes_repeats_and_includes_model(self):
        registry = make_registry()
        specs = planned_trials(registry, 1)
        params = request_params()
        base = config_fingerprint(specs, params)
        self.assertEqual(config_fingerprint(planned_trials(registry, 3), params), base)
        changed = config_fingerprint(planned_trials(make_registry(model_id="m-2"), 1), params)
        self.assertNotEqual(base, changed)

    def test_request_params_snapshot_has_no_secrets(self):
        params = request_params()
        self.assertNotIn("api_key", json.dumps(params))
        self.assertIn("max_tokens", params)


class FreshRunTest(unittest.TestCase):
    def test_new_run_writes_plan_attempts_view_and_ledger(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "20260911T000000Z-abcd1234"
            stats, transport, _ = run_once(run_dir)
            self.assertEqual(stats["executed"], 3)
            self.assertEqual(len(transport.calls), 3)

            plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
            self.assertEqual(len(plan["planned_trial_ids"]), 3)
            self.assertIn("config_fingerprint", plan)
            self.assertNotIn("FAKE_KEY", json.dumps(plan))
            self.assertEqual(plan["models"]["cat-1"]["endpoint"], "http://fake/ep")

            attempt_lines = (run_dir / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(attempt_lines), 6)  # started+finished ×3
            started = json.loads(attempt_lines[0])
            self.assertEqual(started["phase"], "started")
            self.assertIn("messages", started)
            self.assertNotIn("FAKE_KEY", json.dumps(started))
            finished = json.loads(attempt_lines[1])
            self.assertEqual(finished["provider_model"], "provider-returned-model")

            view = [
                json.loads(x)
                for x in (run_dir / "trials.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(len(view), 3)
            self.assertTrue(all(row["status"] == "success" for row in view))
            self.assertEqual(stats["view_complete"], 3)

            events = [
                json.loads(x)
                for x in (run_dir / "budget.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            kinds = [e["kind"] for e in events]
            self.assertEqual(kinds.count("reserve"), 3)
            self.assertEqual(kinds.count("settle"), 3)


class ResumeSemanticsTest(unittest.TestCase):
    def test_same_config_resume_reuses_successes_without_calls(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            first, transport1, _ = run_once(run_dir)
            self.assertEqual(first["executed"], 3)
            before = (run_dir / "attempts.jsonl").read_text(encoding="utf-8")

            second, transport2, _ = run_once(run_dir)
            self.assertEqual(second["reused"], 3)
            self.assertEqual(second["executed"], 0)
            self.assertEqual(transport2.calls, [])
            self.assertEqual(before, (run_dir / "attempts.jsonl").read_text(encoding="utf-8"))

    def test_smaller_repeats_keeps_history(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_once(run_dir, repeats=2)  # 6 条
            stats, _, _ = run_once(run_dir, repeats=1)  # 计划缩到 3
            self.assertEqual(stats["reused"], 3)
            view = (run_dir / "trials.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(view), 6)  # 历史 trial 行全部保留

    def test_changed_config_cannot_reuse_same_dir(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_once(run_dir, registry=make_registry(model_id="m-1"))
            with self.assertRaises(RuntimeError):
                run_once(run_dir, registry=make_registry(model_id="m-2"))

    def test_failed_result_is_not_reused_and_retry_caps_across_resume(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            flaky = {"exp003-cat-1-neutral-1": "failed"}

            def resolver(spec):
                if flaky.get(spec["trial_id"]) == "failed":
                    return {
                        "status": "failed",
                        "http_status": 500,
                        "error_type": "HTTPError",
                        "response": "",
                        "elapsed_ms": 1,
                        "billing_unknown": False,
                    }
                return success_outcome(f"回答-{spec['trial_id']}")

            first, t1, _ = run_once(run_dir, resolver=resolver)
            self.assertEqual(first["executed"], 3)
            view = [
                json.loads(x)
                for x in (run_dir / "trials.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                next(r for r in view if r["trial_id"] == "exp003-cat-1-neutral-1")["status"],
                "failed",
            )

            second, t2, _ = run_once(run_dir, resolver=resolver)  # 重试一次
            self.assertEqual(second["reused"], 2)
            self.assertEqual(t2.calls, ["exp003-cat-1-neutral-1"])
            third, t3, _ = run_once(run_dir, resolver=resolver)  # attempt 上限，跳过
            self.assertEqual(third["skipped"], 1)
            self.assertEqual(t3.calls, [])
            attempts = load_attempts(run_dir / "attempts.jsonl")
            self.assertEqual(
                len([1 for (tid, _), row in attempts.items() if tid == "exp003-cat-1-neutral-1"]), 2
            )

    def test_truncated_and_failure_and_not_executed_are_distinguished(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"

            def resolver(spec):
                if spec["trial_id"] == "exp003-cat-1-neutral-1":
                    return success_outcome("截断的回答", finish_reason="length")
                return success_outcome(f"回答-{spec['trial_id']}")

            # 预算恰好够第一条（neutral 在计划首位）：后两条预算拒绝
            from medmirror.runner import CASE_TEXT

            just_enough = estimate_cost_cny(PRICES, "deepseek", len(CASE_TEXT), 4096)
            stats, _, _ = run_once(run_dir, resolver=resolver, budget=just_enough)
            # 预算只够第一条：后两条预算拒绝，物化视图记 not_executed
            self.assertEqual(stats["view_truncated"], 1)
            self.assertEqual(stats["budget_refused"], 2)
            view = [
                json.loads(x)
                for x in (run_dir / "trials.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            by_status = {row["status"]: row["trial_id"] for row in view}
            self.assertIn("not_executed", by_status)


class CrashRecoveryTest(unittest.TestCase):
    def test_started_without_finished_is_pending_reconciliation(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_once(run_dir)
            # 模拟崩溃：手工追加一条只有 started 没有 finished 的 attempt
            append_jsonl(
                run_dir / "attempts.jsonl",
                {
                    "phase": "started",
                    "trial_id": "exp003-cat-1-neutral-1",
                    "attempt": 2,
                    "config_fingerprint": "x" * 64,
                },
            )
            stats, transport, _ = run_once(run_dir)
            self.assertEqual(stats["pending_reconciliation"], 1)
            self.assertNotIn("exp003-cat-1-neutral-1", transport.calls)  # 不自动重跑
            view = [
                json.loads(x)
                for x in (run_dir / "trials.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            pending = next(r for r in view if r["trial_id"] == "exp003-cat-1-neutral-1")
            self.assertEqual(pending["status"], "pending_reconciliation")

    def test_trial_outcome_pending_detection(self):
        attempts = {
            ("t-1", 1): {"phase": "started", "trial_id": "t-1", "attempt": 1, "finished": None}
        }
        self.assertEqual(trial_outcome(attempts, "t-1")["status"], "pending_reconciliation")
        self.assertIsNone(trial_outcome(attempts, "t-2"))

    def test_torn_trailing_line_is_tolerated(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.jsonl"
            path.write_text(
                '{"trial_id": "t-1"}\n{"trial_id": "t-2"}\n{"trial_id": "t-3', encoding="utf-8"
            )
            rows, torn = load_jsonl_tolerant(path)
            self.assertEqual(len(rows), 2)
            self.assertEqual(torn, 1)


class BudgetLedgerTest(unittest.TestCase):
    def test_reserve_settle_refund_math_and_recovery(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.jsonl"
            ledger = Ledger(path, total_cny=1.0)
            ledger.reserve("t-1", 1, 0.4)
            self.assertEqual(ledger.state.available_cny, 0.6)
            ledger.settle("t-1", 1, 0.3, reserved_cny=0.4)
            self.assertEqual(ledger.state.reserved_cny, 0.0)
            self.assertEqual(ledger.state.settled_cny, 0.3)
            self.assertEqual(ledger.state.available_cny, 0.7)
            ledger.reserve("t-2", 1, 0.2)
            ledger.refund("t-2", 1, 0.2, note="failed_before_send")
            self.assertEqual(ledger.state.available_cny, 0.7)

            recovered = Ledger(path, total_cny=1.0)  # 跨恢复累计
            self.assertEqual(recovered.state.settled_cny, 0.3)
            self.assertEqual(recovered.state.available_cny, 0.7)

    def test_reserve_refuses_when_exhausted(self):
        ledger = Ledger(None, total_cny=0.1)
        with self.assertRaises(BudgetError):
            ledger.reserve("t-1", 1, 0.2)

    def test_overshoot_settle_drives_negative_and_blocks_next_reserve(self):
        ledger = Ledger(None, total_cny=0.1)
        ledger.reserve("t-1", 1, 0.1)
        ledger.settle("t-1", 1, 0.5, reserved_cny=0.1)  # 实际超预留：入账不拒绝
        self.assertAlmostEqual(ledger.state.available_cny, -0.4)
        with self.assertRaises(BudgetError):
            ledger.reserve("t-2", 1, 0.01)

    def test_unknown_price_refuses_estimate_and_settle(self):
        with self.assertRaises(BudgetError):
            estimate_cost_cny({}, "deepseek", 100, 100)
        with self.assertRaises(BudgetError):
            actual_cost_cny(None, "deepseek", {"prompt_tokens": 1})
        self.assertEqual(actual_cost_cny(PRICES, "deepseek", None), 0.0)

    def test_unknown_price_zero_calls_via_runner(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            stats, transport, _ = run_once(run_dir, prices={})  # 价格表为空
            self.assertEqual(transport.calls, [])
            self.assertEqual(stats["budget_refused"], 3)
            view = [
                json.loads(x)
                for x in (run_dir / "trials.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertTrue(all(row["status"] == "not_executed" for row in view))


class ReportCompatTest(unittest.TestCase):
    def test_materialized_view_feeds_report_cli(self):
        import subprocess
        import sys
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "20260911T000000Z-abcd1234"
            # catalog id 与真实模型目录一致，报告 CLI 的计划才能对上这些试次
            matching = {
                "deepseek-v4-flash": SimpleNamespace(
                    model_id="deepseek-v4-flash",
                    vendor="deepseek",
                    endpoint="http://fake/ep",
                    api_key_env="FAKE_KEY",
                )
            }
            run_once(run_dir, registry=matching)
            out = Path(tmp) / "derived"
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts/report_exp003.py"),
                    "--input",
                    str(run_dir / "trials.jsonl"),
                    "--output",
                    str(out),
                    "--repeats",
                    "1",
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[1],
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            analysis = json.loads((out / "analysis.json").read_text(encoding="utf-8"))
            # 真实 registry 是 3 模型 × 3 变体 × 1 次 = 计划 9；假 run 只有 1 模型 3 条成功
            self.assertEqual(analysis["planned_n"], 9)
            self.assertEqual(analysis["counts"]["complete"], 3)
            self.assertEqual(analysis["counts"]["not_executed"], 6)


if __name__ == "__main__":
    unittest.main()
