"""Issue #3 回归：预算硬闸门的并发安全与恢复不重复结算。

#13 已覆盖核心场景（价格未知零调用、余额不足零调用、超时 pending_charge、
失败 refund、假网络全链路）。本文件补齐 #3 专属验收：
1. 并发预留不能透支（循环模拟快速连续预留，验证数学不变式）
2. 恢复不重复结算（部分事件文件恢复后金额一致）
3. 恢复不遗失预留（崩溃时有在途预留，恢复后仍计入）
"""

import json
import tempfile
import unittest
from pathlib import Path

from medmirror.budget import BudgetError, Ledger


class ConcurrentReserveTest(unittest.TestCase):
    """循环模拟快速连续预留：总额不变式在任何时刻不被打破。"""

    def test_sequential_reserves_never_overdraft(self):
        """连续预留到余额耗尽后，下一次必须被拒绝——不能透支。"""
        ledger = Ledger(None, total_cny=1.0)
        reserve_amount = 0.1
        count = 0
        for i in range(20):  # 故意请求超过总额能容纳的次数
            try:
                ledger.reserve(f"t-{i}", 1, reserve_amount)
                count += 1
            except BudgetError:
                break
        self.assertEqual(count, 10)  # 1.0 / 0.1 = 10 次恰好填满
        self.assertEqual(ledger.state.reserved_cny, 1.0)
        self.assertEqual(ledger.state.available_cny, 0.0)
        # 第 11 次必须被拒绝
        with self.assertRaises(BudgetError):
            ledger.reserve("t-overflow", 1, 0.01)

    def test_reserve_then_partial_settle_then_more_reserves(self):
        """结算部分后释放的额度可再用于新预留。"""
        ledger = Ledger(None, total_cny=0.5)
        ledger.reserve("t-1", 1, 0.3)
        ledger.settle("t-1", 1, 0.2, reserved_cny=0.3)  # 实际 0.2，释放 0.1
        self.assertAlmostEqual(ledger.state.available_cny, 0.3)  # 0.5 - 0.2
        ledger.reserve("t-2", 1, 0.25)  # 可以用释放的额度
        self.assertAlmostEqual(ledger.state.available_cny, 0.05)


class RecoveryNoDoubleSettleTest(unittest.TestCase):
    """从部分事件文件恢复后，已结算金额与预留金额与崩溃前一致。"""

    def _write_events(self, path: Path, events: list[dict]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def test_recovery_preserves_settled_and_reserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.jsonl"
            events = [
                {"kind": "init", "amount_cny": 2.0},
                {"kind": "reserve", "trial_id": "t-1", "attempt": 1, "amount_cny": 0.5},
                {
                    "kind": "settle",
                    "trial_id": "t-1",
                    "attempt": 1,
                    "amount_cny": 0.3,
                    "reserved_cny": 0.5,
                },
                {"kind": "reserve", "trial_id": "t-2", "attempt": 1, "amount_cny": 0.4},
                {
                    "kind": "pending_charge",
                    "trial_id": "t-2",
                    "attempt": 1,
                    "amount_cny": 0.4,
                    "note": "timeout",
                },
            ]
            self._write_events(path, events)
            recovered = Ledger(path, total_cny=99.0)  # 传入不同总额也不影响——init 事件优先
            self.assertEqual(recovered.state.total_cny, 2.0)
            self.assertAlmostEqual(recovered.state.settled_cny, 0.3)
            self.assertAlmostEqual(recovered.state.reserved_cny, 0.4)  # pending_charge 的预留保留
            self.assertAlmostEqual(recovered.state.available_cny, 1.3)  # 2.0 - 0.3 - 0.4

    def test_recovery_with_truncated_tail_line(self):
        """崩溃时最后一行只写了一半：恢复时忽略，之前的完整事件不受影响。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.jsonl"
            path.write_text(
                '{"kind": "init", "amount_cny": 1.0}\n'
                '{"kind": "reserve", "trial_id": "t-1", "attempt": 1, "amount_cny": 0.3}\n'
                '{"kind": "settle", "trial_id": "t-1", "attempt": 1, "amount_cny": 0.2, "res',
                encoding="utf-8",
            )
            recovered = Ledger(path, total_cny=1.0)
            self.assertAlmostEqual(recovered.state.settled_cny, 0.0)  # settle 行被截断，不生效
            self.assertAlmostEqual(recovered.state.reserved_cny, 0.3)  # reserve 完整，保留

    def test_repeated_load_produce_same_state(self):
        """同一文件多次加载，结果一致——不因重读而重复计算。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.jsonl"
            events = [
                {"kind": "init", "amount_cny": 5.0},
                {"kind": "reserve", "trial_id": "a", "attempt": 1, "amount_cny": 1.0},
                {
                    "kind": "settle",
                    "trial_id": "a",
                    "attempt": 1,
                    "amount_cny": 0.8,
                    "reserved_cny": 1.0,
                },
                {"kind": "reserve", "trial_id": "b", "attempt": 1, "amount_cny": 0.5},
                {
                    "kind": "refund",
                    "trial_id": "b",
                    "attempt": 1,
                    "amount_cny": 0.5,
                    "note": "failed",
                },
            ]
            self._write_events(path, events)
            first = Ledger(path, total_cny=5.0)
            second = Ledger(path, total_cny=5.0)
            self.assertEqual(first.state.settled_cny, second.state.settled_cny)
            self.assertEqual(first.state.reserved_cny, second.state.reserved_cny)
            self.assertEqual(first.state.available_cny, second.state.available_cny)
            self.assertAlmostEqual(first.state.settled_cny, 0.8)
            self.assertAlmostEqual(first.state.available_cny, 4.2)


class InitEventLockTest(unittest.TestCase):
    """总额锁定在首次 init 事件中——CLI 参数不能覆盖。"""

    def test_init_overrides_constructor_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.jsonl"
            path.write_text('{"kind": "init", "amount_cny": 3.0}\n', encoding="utf-8")
            ledger = Ledger(path, total_cny=999.0)  # 传入不同值
            self.assertEqual(ledger.state.total_cny, 3.0)  # init 事件优先

    def test_first_creation_writes_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budget.jsonl"
            Ledger(path, total_cny=7.5)
            content = path.read_text(encoding="utf-8").strip()
            self.assertIn('"kind": "init"', content)
            self.assertIn("7.5", content)


if __name__ == "__main__":
    unittest.main()
