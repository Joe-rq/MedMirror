"""预算账本（issue #13/#3 共用契约）。

每次真实调用前必须 reserve（预留），拿到结果后 settle（按实际用量结算）；
发出前失败/被拒绝则 refund。事件追加写入 run 目录的 budget.jsonl，可跨恢复累计。

#13 交付账本与 runner 集成（假网络可测）；#3 交付真实价格核对、
账单比对与"价格未知零调用"的完整硬闸。价格未知的供应商在本账本中
reserve 直接拒绝——不把未知费用当零。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class BudgetError(RuntimeError):
    """预算不足或价格未知——调用必须被拒绝，不得重试绕过。"""


@dataclass
class LedgerState:
    total_cny: float
    reserved_cny: float = 0.0  # 已预留未结算
    settled_cny: float = 0.0  # 已结算的实际花费
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def available_cny(self) -> float:
        return round(self.total_cny - self.reserved_cny - self.settled_cny, 6)


class Ledger:
    """追加式预算账本：reserve → settle/refund，事件落盘可追溯。"""

    def __init__(self, path: Path | None, total_cny: float):
        self.path = path
        self.state = LedgerState(total_cny=total_cny)
        if path is not None and path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    self._apply(json.loads(line))
                except json.JSONDecodeError:
                    continue  # 尾部被崩溃截断的半行：忽略，不影响已入账事件
        else:
            # 首次建账：总额作为 init 事件落盘，恢复时以账本为准而非 CLI 参数
            self._append({"kind": "init", "amount_cny": round(total_cny, 6)})

    # ---------------------------------------------------------------- 恢复

    def _apply(self, event: dict[str, Any]) -> None:
        kind = event["kind"]
        amount = float(event["amount_cny"])
        if kind == "init":
            self.state.total_cny = amount
        elif kind == "reserve":
            self.state.reserved_cny = round(self.state.reserved_cny + amount, 6)
        elif kind == "settle":
            self.state.reserved_cny = round(self.state.reserved_cny - event["reserved_cny"], 6)
            self.state.settled_cny = round(self.state.settled_cny + amount, 6)
        elif kind == "refund":
            self.state.reserved_cny = round(self.state.reserved_cny - amount, 6)
        elif kind == "pending_charge":
            # 已发出但费用未知的调用：预留保留（不释放）、不计 0——待人工核账后
            # 由 settle 或 refund 关闭；available 不变（预留仍占位）
            pass
        else:
            raise ValueError(f"未知账本事件：{kind}")
        self.state.events.append(event)

    def _append(self, event: dict[str, Any]) -> None:
        self._apply(event)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    # ---------------------------------------------------------------- 操作

    def reserve(self, trial_id: str, attempt: int, amount_cny: float, note: str = "") -> None:
        if amount_cny < 0:
            raise BudgetError(f"{trial_id}#{attempt} 预留金额为负：{amount_cny}")
        if amount_cny > self.state.available_cny:
            raise BudgetError(
                f"{trial_id}#{attempt} 预留 {amount_cny} 元超出可用余额 "
                f"{self.state.available_cny} 元（总额 {self.state.total_cny}，"
                f"已结算 {self.state.settled_cny}，在途 {self.state.reserved_cny}）"
            )
        self._append(
            {
                "kind": "reserve",
                "trial_id": trial_id,
                "attempt": attempt,
                "amount_cny": round(amount_cny, 6),
                "note": note,
            }
        )

    def settle(self, trial_id: str, attempt: int, amount_cny: float, reserved_cny: float) -> None:
        """按实际用量结算：释放预留、计入实际花费。

        实际超出预留时不拒绝（钱已花掉，必须入账），可用余额转负后
        后续 reserve 自然失败——超支事实可见而非被吞掉。
        """
        self._append(
            {
                "kind": "settle",
                "trial_id": trial_id,
                "attempt": attempt,
                "amount_cny": round(amount_cny, 6),
                "reserved_cny": round(reserved_cny, 6),
            }
        )

    def refund(self, trial_id: str, attempt: int, reserved_cny: float, note: str) -> None:
        self._append(
            {
                "kind": "refund",
                "trial_id": trial_id,
                "attempt": attempt,
                "amount_cny": round(reserved_cny, 6),
                "note": note,
            }
        )

    def pending_charge(self, trial_id: str, attempt: int, reserved_cny: float, note: str) -> None:
        """已发出但结果/费用未知的调用：预留保留不释放、不按 0 结算。

        反复超时不能让账本余额回到原位——预留持续占位直到人工核账后
        settle（实际花费）或 refund（确认未计费）关闭该笔。
        """
        self._append(
            {
                "kind": "pending_charge",
                "trial_id": trial_id,
                "attempt": attempt,
                "amount_cny": round(reserved_cny, 6),
                "note": note,
            }
        )


def estimate_cost_cny(
    prices: dict[str, dict[str, float]] | None, vendor: str, prompt_chars: int, max_tokens: int
) -> float:
    """按最坏情况估算单次调用成本：输入按字符数（中文≈字≈token 上界）、输出按 max_tokens。

    价格未知的供应商抛 BudgetError——未知费用不当零（#3 硬闸原则）。
    """
    if not prices or vendor not in prices:
        raise BudgetError(f"供应商 {vendor} 价格未知，拒绝调用（未知费用不当零）")
    price = prices[vendor]
    return round(
        (prompt_chars * price["input_cache_miss"] + max_tokens * price["output"]) / 1_000_000, 6
    )


def actual_cost_cny(
    prices: dict[str, dict[str, float]] | None, vendor: str, usage: dict[str, Any] | None
) -> float:
    """按返回 usage 的实际 token 用量结算；usage 缺失按 0 计并显式标注（待核账）。"""
    if not isinstance(usage, dict):
        return 0.0
    if not prices or vendor not in prices:
        raise BudgetError(f"供应商 {vendor} 价格未知，无法结算")
    price = prices[vendor]
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    return round((prompt * price["input_cache_miss"] + completion * price["output"]) / 1_000_000, 6)
