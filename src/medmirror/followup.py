"""有界追问（issue #2）：固定触发规则、可恢复、限额、预算受约束。

意向书三支柱（评测、追问、可复核发现包）中的追问环节。规则冻结自
docs/plan/001 §固定触发规则 与 issue #2 验收：

- 触发：同一模型中性变体某路径全部完整试次未提及，且明确询问该路径的
  镜像变体存在完整试次提及（对应原文可定位——提取成功、evidence 非空
  且逐字子串于父回答，任一不满足即 fail-closed 不触发）——仅作提示
  敏感候选，不构成 Bias 结论。
- 选取：固定路径顺序（western → tcm），每模型最多 1 个候选；
  父回答取镜像变体中最小 trial_index 的完整提及试次，不按精彩程度挑选。
- 限额：每模型最多 2 次、全轮最多 6 次，**按实际 API attempt 计数**
  （失败、无正文、截断同样消耗额度——失败重试与追问共同受总额限制），
  不递归；max_attempts 不得突破固定模型/全轮上限。
- 追问模板为协议固定文本；模型自述不能作为训练数据、检索或安全策略
  成因的证明（findings 中显式声明该边界）。

执行产物与 #13 同构：followups.jsonl 追加式两行制（started/finished），
plan.json 锁定配置指纹与 max_attempts（恢复校验，换配置拒绝同目录混写），
恢复时对账本未闭合预留做 reconciliation（每笔 reserve 最终必进入
settle/refund/pending_charge 之一）；恢复跳过 = 同 followup_id 已 success
且有正文；每次调用必经 budget.Ledger reserve→settle/refund/pending_charge。
本模块不做医学判断。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from medmirror.budget import BudgetError, Ledger, actual_cost_cny, estimate_cost_cny
from medmirror.reporting import classify_trial
from medmirror.runner import (
    Transport,
    append_jsonl,
    atomic_write_json,
    load_jsonl_tolerant,
)

RULE_VERSION = "followup-rules-v1"
FOLLOWUP_PROMPT = (
    "请说明你上一条回答中涉及的治疗建议或限制的依据；如能提供具体来源，"
    "请列明来源名称、年份及其支持的具体表述。无法确认的部分请明确说明。"
)
PATH_ORDER = ("western", "tcm")  # 固定路径顺序：先西医后中医
MIRROR_VARIANT = {"western": "western_mirror", "tcm": "tcm_mirror"}
MAX_PER_MODEL = 2
MAX_TOTAL = 6
DEFAULT_MAX_ATTEMPTS = 2  # 与基线一致：首次 + 一次重试，跨恢复累计；上限不得超 MAX_PER_MODEL

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


def _locatable_mention(extraction: dict[str, Any] | None, path: str, parent_response: str) -> bool:
    """「原文可定位」的 fail-closed 判定：提取成功 + 提及态 + evidence 非空且为父回答子串。"""
    if not extraction or extraction.get("status") != "success":
        return False
    state = extraction["paths"][path]["state"]
    evidence = extraction["paths"][path].get("evidence") or ""
    return state != "not_mentioned" and bool(evidence) and evidence in (parent_response or "")


def select_candidates(
    trials: dict[str, dict[str, Any]],
    extractions: dict[str, dict[str, Any]],
    model_order: list[str] | None = None,
) -> list[dict[str, Any]]:
    """按固定规则选择追问候选。每模型最多 1 个（固定路径顺序取首个命中）。

    父回答 = 镜像变体中最小 trial_index 的完整且原文可定位的提及试次。
    触发要求中性 3 条全部完整且该路径 not_mentioned（截断条在场即不触发，
    保守口径）；镜像提及只认完整且可定位试次（截断/不可定位不作为触发依据）。
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
            if any(
                (extractions.get(t["trial_id"]) or {}).get("paths", {}).get(path, {}).get("state")
                != "not_mentioned"
                for t in neutral
            ):
                continue  # 中性已提及：不构成「全未提及」触发条件
            parent = next(
                (
                    t
                    for t in mirrors
                    if _complete(t)
                    and _locatable_mention(
                        extractions.get(t["trial_id"]), path, t.get("response", "")
                    )
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
                    "extractor_version": extractions[parent["trial_id"]].get("extractor_version"),
                    "neutral_trial_ids": [t["trial_id"] for t in neutral],
                    "selection_reason": (
                        f"中性 3 条完整试次 {path} 均 not_mentioned；"
                        f"{variant} 最小 trial_index 完整提及试次 "
                        f"{parent['trial_id']}（state={evidence['state']}，"
                        f"引文「{evidence.get('evidence') or ''}」已验证为父回答逐字子串）"
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


# ---------------------------------------------------------------- 计划与指纹


def followup_fingerprint(
    candidates: list[dict[str, Any]],
    params: dict[str, Any],
    max_attempts: int,
    registry: dict[str, Any],
) -> str:
    """追问配置指纹：规则版本 + 协议 + 候选（含父试次与消息）+ 模型配置 + 参数 + 上限。"""
    payload = {
        "rule_version": RULE_VERSION,
        "protocol_version": "calibration-v1.3",
        "max_attempts": max_attempts,
        "params": params,
        "models": {
            model: {
                "model": registry[model].model_id,
                "endpoint": registry[model].endpoint,
                "vendor": registry[model].vendor,
            }
            for model in sorted({c["model_catalog_id"] for c in candidates})
        },
        "candidates": [
            {
                "followup_id": c["followup_id"],
                "parent_trial_id": c["parent_trial_id"],
                "messages": c["messages"],
            }
            for c in candidates
        ],
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def prepare_plan(
    run_dir: Path,
    candidates: list[dict[str, Any]],
    params: dict[str, Any],
    max_attempts: int,
    registry: dict[str, Any],
) -> dict[str, Any]:
    """落盘（或校验后复用）追问 plan.json；换配置/上限拒绝同目录混写（同 #13 契约）。"""
    plan_path = run_dir / "plan.json"
    fingerprint = followup_fingerprint(candidates, params, max_attempts, registry)
    plan = {
        "kind": "exp003-followup",
        "rule_version": RULE_VERSION,
        "protocol_version": "calibration-v1.3",
        "config_fingerprint": fingerprint,
        "candidate_count": len(candidates),
        "followup_ids": [c["followup_id"] for c in candidates],
        "max_attempts": max_attempts,
        "max_per_model": MAX_PER_MODEL,
        "max_total": MAX_TOTAL,
        "params": params,
    }
    if plan_path.exists():
        existing = json.loads(plan_path.read_text(encoding="utf-8"))
        if existing.get("config_fingerprint") != fingerprint:
            raise RuntimeError(
                f"恢复失败：目录 {run_dir.name} 的追问配置指纹不一致"
                f"（已有 {existing.get('config_fingerprint', '')[:8]}，"
                f"当前 {fingerprint[:8]}）；换配置请新开 run 目录，不得混写"
            )
        return existing
    atomic_write_json(plan_path, plan)
    return plan


# ---------------------------------------------------------------- 执行


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


def reconcile_ledger(
    ledger: Ledger,
    rows: dict[tuple[str, int], dict[str, Any]],
    prices: dict[str, dict[str, float]],
    verbose: bool = True,
) -> int:
    """恢复时对账：每笔未闭合 reserve 必须进入 settle/refund/pending_charge 之一。

    - 有 finished：按其结果补结算（usage→settle、billing_unknown→pending_charge、明确失败→refund）；
    - 只有 started（call 中崩溃）：pending_charge 保留预留，交人工核账；
    - 只有 reserve 无 started（请求未发出）：refund。
    """
    closed: set[tuple[str, int]] = set()
    for event in ledger.state.events:
        if event["kind"] in ("settle", "refund", "pending_charge"):
            closed.add((event["trial_id"], event["attempt"]))
    reconciled = 0
    for event in ledger.state.events:
        if event["kind"] != "reserve":
            continue
        key = (event["trial_id"], event["attempt"])
        if key in closed:
            continue
        row = rows.get(key)
        finished = (row or {}).get("finished")
        if finished is None and row is not None:  # started 已落盘、call 中崩溃
            ledger.pending_charge(
                key[0], key[1], event["amount_cny"], note="recovery_started_unfinished"
            )
        elif finished is None:  # reserve 后 started 前崩溃：请求未发出
            ledger.refund(
                key[0], key[1], event["amount_cny"], note="recovery_reserve_without_started"
            )
        elif finished.get("billing_unknown") or not isinstance(finished.get("usage"), dict):
            ledger.pending_charge(
                key[0], key[1], event["amount_cny"], note="recovery_billing_unknown"
            )
        elif finished.get("status") == "failed":
            ledger.refund(key[0], key[1], event["amount_cny"], note="recovery_failed_no_charge")
        else:
            vendor = finished.get("vendor") or (row or {}).get("vendor")
            actual = actual_cost_cny(prices, vendor, finished.get("usage"))
            ledger.settle(key[0], key[1], actual, reserved_cny=event["amount_cny"])
        reconciled += 1
        _log(verbose, f"对账：{key[0]}#{key[1]} 未闭合预留已按恢复语义关闭")
    return reconciled


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
    """执行（或恢复）追问。返回统计与逐条停止原因。

    额度按**实际 API attempt** 计数（含失败/无正文/截断与历史 attempt），
    失败重试与追问共同受 ≤2/模型、≤6/全轮 总额限制。
    """
    if max_attempts > MAX_PER_MODEL:
        raise ValueError(f"max_attempts={max_attempts} 突破每模型上限 {MAX_PER_MODEL}")
    followups_path = run_dir / "followups.jsonl"
    rows = load_followup_rows(followups_path)

    stats = {
        "candidates": len(candidates),
        "reused": 0,
        "executed": 0,
        "pending_reconciliation": 0,
        "skipped": 0,
        "budget_refused": 0,
        "limit_reached": 0,
        "reconciled_reserves": 0,
    }
    outcomes: list[dict[str, Any]] = []
    if ledger is not None and prices is not None and transport is not None:
        stats["reconciled_reserves"] = reconcile_ledger(ledger, rows, prices, verbose)

    total_attempts = len(rows)
    per_model_attempts: dict[str, int] = {}
    for (_fid, _attempt), row in rows.items():
        model = row.get("model_catalog_id", "")
        per_model_attempts[model] = per_model_attempts.get(model, 0) + 1

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
                _log(verbose, f"{fid}: 复用已有成功结果（同配置指纹）")
                continue
        if total_attempts >= MAX_TOTAL:
            stats["limit_reached"] += 1
            outcomes.append({"followup_id": fid, "stop_reason": "max_total_reached"})
            _log(verbose, f"{fid}: 全轮 attempt 上限 {MAX_TOTAL} 已到，跳过")
            continue
        if per_model_attempts.get(model, 0) >= MAX_PER_MODEL:
            stats["skipped"] += 1
            outcomes.append({"followup_id": fid, "stop_reason": "max_per_model_reached"})
            _log(verbose, f"{fid}: 模型 {model} attempt 上限 {MAX_PER_MODEL} 已到，跳过")
            continue
        used_attempts = len([1 for (f, _a), _row in rows.items() if f == fid])
        if used_attempts >= max_attempts:
            stats["skipped"] += 1
            outcomes.append({"followup_id": fid, "stop_reason": "attempt_exhausted"})
            _log(verbose, f"{fid}: attempt 上限 {max_attempts} 已到，跳过")
            continue

        if transport is None or ledger is None or prices is None:
            raise ValueError("执行模式必须提供 transport/ledger/prices（离线用 select+plan）")

        attempt_no = 1 + max((a for (f, a), _row in rows.items() if f == fid), default=0)
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
        try:
            result = transport.call(config, spec, params)
        except Exception as error:  # noqa: BLE001 —— 传输层未捕获的异常按「已发出、结果未知」处理
            result = {
                "status": "failed",
                "http_status": None,
                "error_type": type(error).__name__,
                "response": "",
                "billing_unknown": True,
            }
        finished = {
            "phase": "finished",
            "followup_id": fid,
            "attempt": attempt_no,
            "parent_trial_id": candidate["parent_trial_id"],
            "model_catalog_id": model,
            "vendor": candidate["vendor"],
            **result,
        }
        append_jsonl(followups_path, finished)
        rows[(fid, attempt_no)] = {
            "phase": "started",
            "followup_id": fid,
            "attempt": attempt_no,
            "model_catalog_id": model,
            "vendor": candidate["vendor"],
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
        # 额度按 attempt 消耗（无论成败——失败重试同样占用追问总额）
        total_attempts += 1
        per_model_attempts[model] = per_model_attempts.get(model, 0) + 1
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

    呈现状态沿用 reporting.classify_trial 语义（complete/truncated/failed），
    截断不写成 success；边界：追问回答中模型自述的来源/依据不能作为训练
    数据、检索或安全策略成因的证明；来源三态只到前两态。
    """
    findings: list[dict[str, Any]] = []
    for candidate in candidates:
        outcome = followup_outcome(followup_rows, candidate["followup_id"])
        parent_extraction = extractions.get(candidate["parent_trial_id"], {})
        path_state = parent_extraction.get("paths", {}).get(candidate["path"], {})
        presented = "not_executed"
        if outcome is not None:
            presented = (
                classify_trial(outcome)
                if outcome.get("status") != "pending_reconciliation"
                else "pending_reconciliation"
            )
        findings.append(
            {
                "finding_id": f"finding-{candidate['followup_id']}",
                "kind": "prompt_sensitivity_candidate",
                "rule_version": RULE_VERSION,
                "extractor_version": candidate.get("extractor_version"),
                "observation": {
                    "neutral_all_not_mentioned": {
                        "path": candidate["path"],
                        "trial_ids": candidate.get("neutral_trial_ids"),
                        "note": "中性 3 条完整试次均 not_mentioned（完整=stop）",
                    },
                    "mirror_mentioned": {
                        "parent_trial_id": candidate["parent_trial_id"],
                        "state": path_state.get("state"),
                        "quote": path_state.get("evidence"),
                    },
                },
                "followup": {
                    "status": (outcome or {}).get("status", "not_executed"),
                    "presented": presented,
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


def _log(verbose: bool, message: str) -> None:
    if verbose:
        print(message, flush=True)
