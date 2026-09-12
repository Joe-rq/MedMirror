"""有界追问（issue #2）：固定触发规则、可恢复、限额、预算受约束。

意向书三支柱（评测、追问、可复核发现包）中的追问环节。规则冻结自
docs/plan/001 §固定触发规则 与 issue #2 验收：

- 触发：同一模型中性变体某路径全部完整试次未提及，且明确询问该路径的
  镜像变体存在完整试次提及（对应原文可定位）——仅作提示敏感候选，
  不构成 Bias 结论。
- 选取：固定路径顺序（western → tcm），每模型最多 1 个候选；
  父回答取镜像变体中最小 trial_index 的完整提及试次，不按精彩程度挑选。
- 限额：每模型最多 2 次、全轮最多 6 次，不递归；失败重试与预算共同受限。
- 追问模板为协议固定文本；模型自述不能作为训练数据、检索或安全策略
  成因的证明（findings 中显式声明该边界）。

执行产物与 #13 同构：followups.jsonl 追加式两行制（started/finished），
恢复跳过 = 同 followup_id 已 success 且有正文；每次调用必经 budget.Ledger
reserve→settle/refund/pending_charge。本模块不做医学判断。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from medmirror.budget import BudgetError, Ledger, actual_cost_cny, estimate_cost_cny
from medmirror.runner import Transport, append_jsonl, load_jsonl_tolerant

RULE_VERSION = "followup-rules-v1"
FOLLOWUP_PROMPT = (
    "请说明你上一条回答中涉及的治疗建议或限制的依据；如能提供具体来源，"
    "请列明来源名称、年份及其支持的具体表述。无法确认的部分请明确说明。"
)
PATH_ORDER = ("western", "tcm")  # 固定路径顺序：先西医后中医
MIRROR_VARIANT = {"western": "western_mirror", "tcm": "tcm_mirror"}
MAX_PER_MODEL = 2
MAX_TOTAL = 6
DEFAULT_MAX_ATTEMPTS = 2  # 与基线一致：首次 + 一次重试，跨恢复累计

TRIAL_STOP = "stop"  # 完整试次的 finish_reason；截断（length）不参与触发判断


# ---------------------------------------------------------------- 候选选择


def load_trials_and_extractions(
    trials_path: Path, extractions_path: Path
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """按 trial_id 索引基线试次与 v2 提取结果。"""
    trials = {row["trial_id"]: row for row in load_jsonl_tolerant(trials_path)[0]}
    extractions = {row["trial_id"]: row for row in load_jsonl_tolerant(extractions_path)[0]}
    return trials, extractions


def _complete(trial: dict[str, Any]) -> bool:
    return trial.get("status") == "success" and trial.get("finish_reason") == TRIAL_STOP


def _mentioned(extraction: dict[str, Any] | None, path: str) -> bool:
    return bool(extraction) and extraction["paths"][path]["state"] != "not_mentioned"


def select_candidates(
    trials: dict[str, dict[str, Any]],
    extractions: dict[str, dict[str, Any]],
    model_order: list[str] | None = None,
) -> list[dict[str, Any]]:
    """按固定规则选择追问候选。每模型最多 1 个（固定路径顺序取首个命中）。

    父回答 = 镜像变体中最小 trial_index 的完整提及试次。
    触发要求中性 3 条全部完整且该路径 not_mentioned（截断条在场即不触发，
    保守口径）；镜像提及只认完整试次（截断条的提及不作为触发依据）。
    """
    models = model_order or sorted({t["model_catalog_id"] for t in trials.values()})
    candidates: list[dict[str, Any]] = []
    for model in models:
        for path in PATH_ORDER:
            variant = MIRROR_VARIANT[path]
            neutral = sorted(
                (
                    t
                    for t in trials.values()
                    if t.get("model_catalog_id") == model and t.get("prompt_variant") == "neutral"
                ),
                key=lambda t: t.get("trial_index") or 0,
            )
            mirrors = sorted(
                (
                    t
                    for t in trials.values()
                    if t.get("model_catalog_id") == model and t.get("prompt_variant") == variant
                ),
                key=lambda t: t.get("trial_index") or 0,
            )
            if len(neutral) != 3 or not all(_complete(t) for t in neutral):
                continue  # 中性不完整（截断/失败/缺失）：该模型该路径不触发
            if any(_mentioned(extractions.get(t["trial_id"]), path) for t in neutral):
                continue  # 中性已提及：不构成「全未提及」触发条件
            parent = next(
                (
                    t
                    for t in mirrors
                    if _complete(t) and _mentioned(extractions.get(t["trial_id"]), path)
                ),
                None,
            )
            if parent is None:
                continue
            evidence = extractions[parent["trial_id"]]["paths"][path]
            candidates.append(
                {
                    "followup_id": f"{parent['trial_id']}-fu1",
                    "parent_trial_id": parent["trial_id"],
                    "model_catalog_id": model,
                    "vendor": parent["vendor"],
                    "path": path,
                    "prompt_variant": variant,
                    "trial_index": parent.get("trial_index"),
                    "rule_version": RULE_VERSION,
                    "selection_reason": (
                        f"中性 3 条完整试次 {path} 均 not_mentioned；"
                        f"{variant} 最小 trial_index 完整提及试次 "
                        f"{parent['trial_id']}（state={evidence['state']}，"
                        f"引文「{evidence.get('evidence') or ''}」可定位）"
                    ),
                    "messages": parent.get("messages", [])
                    + [
                        {"role": "assistant", "content": parent.get("response", "")},
                        {"role": "user", "content": FOLLOWUP_PROMPT},
                    ],
                }
            )
            break  # 每模型只取固定路径顺序的首个命中
    return candidates


# ---------------------------------------------------------------- 执行


def followup_outcome(
    rows: dict[tuple[str, int], dict[str, Any]], followup_id: str
) -> dict[str, Any] | None:
    """当前结果；无 finished 或 billing_unknown → pending_reconciliation（同 #13 口径）。"""
    history = [row for (fid, _), row in rows.items() if fid == followup_id]
    if not history:
        return None
    last = max(history, key=lambda row: row["attempt"])
    if last.get("finished") is None:
        return {"status": "pending_reconciliation", "attempt": last["attempt"]}
    finished = last["finished"]
    if finished.get("billing_unknown"):
        return {**finished, "status": "pending_reconciliation"}
    return finished


def execute_followups(
    run_dir: Path,
    candidates: list[dict[str, Any]],
    registry: dict[str, Any],
    transport: Transport | None,
    ledger: Ledger | None,
    prices: dict[str, dict[str, float]] | None,
    params: dict[str, Any],
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    verbose: bool = True,
) -> dict[str, Any]:
    """执行（或恢复）追问。返回统计与逐条停止原因。"""
    followups_path = run_dir / "followups.jsonl"
    rows_raw, _torn = load_jsonl_tolerant(followups_path)
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows_raw:
        key = (row["followup_id"], row["attempt"])
        if row.get("phase") == "started":
            rows[key] = {**row, "finished": None}
        elif row.get("phase") == "finished" and key in rows:
            rows[key]["finished"] = row

    stats = {
        "candidates": len(candidates),
        "reused": 0,
        "executed": 0,
        "pending_reconciliation": 0,
        "skipped": 0,
        "budget_refused": 0,
        "max_total_reached": 0,
    }
    outcomes: list[dict[str, Any]] = []
    total_success = len(
        {
            fid
            for (fid, _), row in rows.items()
            if (row.get("finished") or {}).get("status") == "success"
            and (row.get("finished") or {}).get("response")
        }
    )
    per_model_success: dict[str, int] = {}
    for (_fid, _), row in rows.items():
        finished = row.get("finished") or {}
        if finished.get("status") == "success" and finished.get("response"):
            model = finished.get("model_catalog_id", "")
            per_model_success[model] = per_model_success.get(model, 0) + 1

    for candidate in candidates:
        fid = candidate["followup_id"]
        model = candidate["model_catalog_id"]
        outcome = followup_outcome(rows, fid)
        if outcome is not None:
            if outcome["status"] == "pending_reconciliation":
                stats["pending_reconciliation"] += 1
                outcomes.append({"followup_id": fid, "stop_reason": "pending_reconciliation"})
                _log(verbose, f"{fid}: pending_reconciliation（结果未知，交人工核账）")
                continue
            if outcome.get("status") == "success" and outcome.get("response"):
                stats["reused"] += 1
                outcomes.append({"followup_id": fid, "stop_reason": "reused"})
                _log(verbose, f"{fid}: 复用已有成功结果（成功计数已含历史）")
                continue
        if total_success >= MAX_TOTAL:
            stats["max_total_reached"] += 1
            outcomes.append({"followup_id": fid, "stop_reason": "max_total_reached"})
            _log(verbose, f"{fid}: 全轮成功上限 {MAX_TOTAL} 已到，跳过")
            continue
        if per_model_success.get(model, 0) >= MAX_PER_MODEL:
            stats["skipped"] += 1
            outcomes.append({"followup_id": fid, "stop_reason": "max_per_model_reached"})
            _log(verbose, f"{fid}: 模型 {model} 成功上限 {MAX_PER_MODEL} 已到，跳过")
            continue
        used_attempts = len([1 for (f, _), row_ in rows.items() if f == fid])
        if used_attempts >= max_attempts:
            stats["skipped"] += 1
            outcomes.append({"followup_id": fid, "stop_reason": "attempt_exhausted"})
            _log(verbose, f"{fid}: attempt 上限 {max_attempts} 已到，跳过")
            continue

        if transport is None or ledger is None or prices is None:
            raise ValueError("执行模式必须提供 transport/ledger/prices（离线用 select+plan）")

        attempt_no = 1 + max((a for (f, a), row_ in rows.items() if f == fid), default=0)
        prompt_chars = sum(len(m["content"]) for m in candidate["messages"])
        try:
            estimate = estimate_cost_cny(
                prices, candidate["vendor"], prompt_chars, params["max_tokens"]
            )
            ledger.reserve(fid, attempt_no, estimate, note=f"followup={run_dir.name}")
        except BudgetError as error:
            stats["budget_refused"] += 1
            outcomes.append(
                {"followup_id": fid, "stop_reason": "budget_refused", "detail": str(error)}
            )
            _log(verbose, f"{fid}: 预算拒绝（{error}）")
            continue

        append_jsonl(
            followups_path,
            {
                "phase": "started",
                "followup_id": fid,
                "attempt": attempt_no,
                "parent_trial_id": candidate["parent_trial_id"],
                "model_catalog_id": model,
                "vendor": candidate["vendor"],
                "path": candidate["path"],
                "rule_version": RULE_VERSION,
                "selection_reason": candidate["selection_reason"],
                "messages": candidate["messages"],
                "params": params,
            },
        )
        config = registry[model]
        spec = {
            "trial_id": fid,
            "messages": candidate["messages"],
            "vendor": candidate["vendor"],
            "endpoint": config.endpoint,
            "model": config.model_id,
        }
        result = transport.call(config, spec, params)
        finished = {
            "phase": "finished",
            "followup_id": fid,
            "attempt": attempt_no,
            "parent_trial_id": candidate["parent_trial_id"],
            "model_catalog_id": model,
            **result,
        }
        append_jsonl(followups_path, finished)
        rows[(fid, attempt_no)] = {
            "phase": "started",
            "followup_id": fid,
            "attempt": attempt_no,
            "finished": finished,
        }
        if result.get("status") == "failed" and not result.get("billing_unknown"):
            ledger.refund(fid, attempt_no, estimate, note="failed_no_charge")
        elif result.get("billing_unknown") or not isinstance(result.get("usage"), dict):
            ledger.pending_charge(
                fid, attempt_no, estimate, note=result.get("error_type") or "usage_missing"
            )
        else:
            actual = actual_cost_cny(prices, candidate["vendor"], result["usage"])
            ledger.settle(fid, attempt_no, actual, reserved_cny=estimate)
            if result.get("status") == "success" and result.get("response"):
                total_success += 1
                per_model_success[model] = per_model_success.get(model, 0) + 1
        stats["executed"] += 1
        outcomes.append({"followup_id": fid, "stop_reason": result.get("status") or "unknown"})
        _log(verbose, f"{fid}: attempt{attempt_no} {result.get('status')}")

    return {**stats, "outcomes": outcomes}


# ---------------------------------------------------------------- 发现包


def build_findings(
    candidates: list[dict[str, Any]],
    followup_rows: dict[tuple[str, int], dict[str, Any]],
    extractions: dict[str, dict[str, Any]],
    stop_reasons: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """把候选观察与追问结果合成发现记录（描述性，不做医学判断）。

    边界：追问回答中模型自述的来源/依据不能作为训练数据、检索或安全
    策略成因的证明；来源三态（被提到/可识别/已核实）中本发现只到前两态。
    """
    findings: list[dict[str, Any]] = []
    for candidate in candidates:
        outcome = followup_outcome(followup_rows, candidate["followup_id"])
        parent_extraction = extractions.get(candidate["parent_trial_id"], {})
        path_state = parent_extraction.get("paths", {}).get(candidate["path"], {})
        findings.append(
            {
                "finding_id": f"finding-{candidate['followup_id']}",
                "kind": "prompt_sensitivity_candidate",
                "rule_version": RULE_VERSION,
                "observation": {
                    "neutral_all_not_mentioned": {
                        "path": candidate["path"],
                        "note": f"中性 3 条完整试次均 not_mentioned（{RULE_VERSION}）",
                    },
                    "mirror_mentioned": {
                        "parent_trial_id": candidate["parent_trial_id"],
                        "state": path_state.get("state"),
                        "quote": path_state.get("evidence"),
                    },
                },
                "followup": {
                    "status": (outcome or {}).get("status", "not_executed"),
                    "stop_reason": (stop_reasons or {}).get(candidate["followup_id"]),
                    "usage": (outcome or {}).get("usage"),
                    "response": (outcome or {}).get("response", ""),
                },
                "boundary": (
                    "提及不等于支持，未提及不等于反对；追问回答中模型自述的来源"
                    "不作为训练数据、检索或安全策略成因的证明；来源三态仅到"
                    "「被提到/可识别」，「已核实」保留给专业复核。"
                ),
            }
        )
    return findings


def write_findings(path: Path, findings: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for finding in findings:
            handle.write(json.dumps(finding, ensure_ascii=False) + "\n")


def load_followup_rows(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    rows_raw, _torn = load_jsonl_tolerant(path)
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows_raw:
        key = (row["followup_id"], row["attempt"])
        if row.get("phase") == "started":
            rows[key] = {**row, "finished": None}
        elif row.get("phase") == "finished" and key in rows:
            rows[key]["finished"] = row
    return rows


def _log(verbose: bool, message: str) -> None:
    if verbose:
        print(message, flush=True)
