"""实验运行编排（issue #13）：独立 run 目录、追加式 attempt、可恢复、预算受约束。

旧执行器的问题（plan/002 §3 P0）：固定输出路径互相覆盖、恢复只比协议字符串导致
换配置误复用、减 repeats 丢历史行、无请求配置快照。本模块按以下语义重做：

- 每个 run 独立目录 `runs/exp003-baseline/<run_id>/`，run_id 含时间戳与配置指纹短码；
  plan.json 保存完整计划与脱敏配置快照（模型/endpoint/参数/消息/协议版本，无 key）。
- attempts.jsonl 追加式：每次 attempt 先写 started 行、拿到结果再写 finished 行；
  落盘前崩溃 → 恢复时该 attempt 显式 pending_reconciliation（已发出但结果未知，
  不声称网络 exactly-once），不自动重跑、不计数，交人工核账。
- 恢复跳过条件 = 同配置指纹 且 success 且有正文；换模型/参数/协议不误复用；
  减 repeats 只影响新计划，历史行全部保留。
- trials.jsonl 物化视图：每个 trial 一行当前状态（含 not_executed 计划行），
  与 #10 报告 CLI 的输入契约兼容。
- 每次 attempt 必须先经 budget.Ledger 预留、后结算/退还（#3 共用契约）。

本模块不做医学判断；runs/ 自 2026-09-13 起入 Git（issue #4 主人拍板：远程仓库即备份落点）。
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from medmirror.budget import BudgetError, Ledger, actual_cost_cny, estimate_cost_cny
from medmirror.casespec import CaseSpec, load_default_case
from medmirror.protocol import EXTRACTOR_VERSION
from medmirror.providers import build_chat_payload
from medmirror.reporting import classify_trial

# 病例协议事实自 CaseSpec 注入（issue #50）：默认病例 configs/cases/carotid_plaque_001.json。
# 下方常量为默认病例的派生别名，保留既有引用者（复核材料脚本、测试）零 diff；
# 换病例经 planned_trials/execute_run/config_fingerprint 的 spec 参数显式传入。
DEFAULT_CASE = load_default_case(supported_extractor_version=EXTRACTOR_VERSION)
PROTOCOL_VERSION = DEFAULT_CASE.protocol_version
CASE_ID = DEFAULT_CASE.case_id
CASE_TEXT = DEFAULT_CASE.case_text
VARIANTS = dict(DEFAULT_CASE.variants)
DEFAULT_MAX_ATTEMPTS = 2  # 每试次 attempt 上限（首次 + 一次重试），跨恢复累计


# ---------------------------------------------------------------- 计划与指纹


def _case_or_default(spec: CaseSpec | None) -> CaseSpec:
    return spec if spec is not None else DEFAULT_CASE


def planned_trials(
    registry: dict[str, Any], repeats: int, spec: CaseSpec | None = None
) -> list[dict[str, Any]]:
    case = _case_or_default(spec)
    return [
        {
            "trial_id": f"{case.trial_prefix}-{catalog_id}-{variant}-{trial_index}",
            "model_catalog_id": catalog_id,
            "model": config.model_id,
            "vendor": config.vendor,
            "endpoint": config.endpoint,
            "prompt_variant": variant,
            "trial_index": trial_index,
            "messages": [{"role": "user", "content": prompt}],
        }
        for catalog_id, config in registry.items()
        for variant, prompt in case.variants.items()
        for trial_index in range(1, repeats + 1)
    ]


def request_params() -> dict[str, Any]:
    """当前请求参数快照（脱敏，无 key）。环境未设置时显式记 null，不用现值冒充。"""
    return {
        "max_tokens": int(os.getenv("MEDMIRROR_MAX_TOKENS", "4096")),
        "thinking_mode": {
            "deepseek": os.getenv("MEDMIRROR_DEEPSEEK_THINKING_MODE"),
            "stepfun": os.getenv("MEDMIRROR_STEPFUN_THINKING_MODE"),
            "glm": os.getenv("MEDMIRROR_GLM_THINKING_MODE"),
        },
        "reasoning_effort": {
            "deepseek": os.getenv("MEDMIRROR_DEEPSEEK_REASONING_EFFORT"),
            "stepfun": os.getenv("MEDMIRROR_STEPFUN_REASONING_EFFORT"),
            "glm": os.getenv("MEDMIRROR_GLM_REASONING_EFFORT"),
        },
        "temperature": 0.7,
    }


def config_fingerprint(
    plan_specs: list[dict[str, Any]], params: dict[str, Any], spec: CaseSpec | None = None
) -> str:
    """配置指纹：协议版本 + 病例消息 + 模型/endpoint/vendor + 请求参数。

    不含 repeats（改变重复次数不使历史失效）、不含时间与 key。
    有意不含提取词表（extraction.paths）：词表不影响 API 请求，改词表走
    extractor/protocol 版本号红线（同病例改词表=新版本，不回改历史），不走指纹；
    词表审计经 plan.json 的 case_spec 快照对账。
    """
    case = _case_or_default(spec)
    payload = {
        "protocol_version": case.protocol_version,
        "case_id": case.case_id,
        "variants": case.variants,
        "params": params,
        "models": {
            spec["model_catalog_id"]: {
                "model": spec["model"],
                "endpoint": spec["endpoint"],
                "vendor": spec["vendor"],
            }
            for spec in plan_specs
        },
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_id_for(fingerprint: str) -> str:
    """时间戳含微秒 + 指纹短码 + 随机后缀，避免同秒碰撞。"""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    nonce = os.urandom(4).hex()
    return f"{stamp}-{fingerprint[:8]}-{nonce}"


# ---------------------------------------------------------------- 原子写盘


def _atomic_write(path: Path, write: Callable[[Any], None], *args: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            write(handle, *args)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """临时文件 + 原子替换；固定 LF 换行，Windows 上不会把历史文件 CRLF 化。"""
    _atomic_write(
        path,
        lambda handle, rows_: [
            handle.write(json.dumps(row, ensure_ascii=False) + "\n") for row in rows_
        ],
        rows,
    )


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write(
        path,
        lambda handle, payload_: handle.write(
            json.dumps(payload_, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ),
        payload,
    )


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl_tolerant(path: Path) -> tuple[list[dict[str, Any]], int]:
    """读取追加式 jsonl；容忍末尾被崩溃截断的半行（返回行列表与被忽略行数）。"""
    if not path.exists():
        return [], 0
    rows: list[dict[str, Any]] = []
    torn = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            torn += 1
    return rows, torn


# ---------------------------------------------------------------- 传输层


class Transport(Protocol):
    def call(
        self, config: Any, spec: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]: ...  # pragma: no cover - 协议定义


def real_transport(
    config: Any, spec: dict[str, Any], params: dict[str, Any], api_key: str, timeout: int
) -> dict[str, Any]:
    """真实 HTTP 传输（旧 call_model 迁移）；供应商返回的 model 标识一并保存。"""
    payload = build_chat_payload(
        config,
        spec["messages"],
        temperature=params["temperature"],
        max_tokens=params["max_tokens"],
        thinking_mode=params["thinking_mode"].get(spec["vendor"]),
        reasoning_effort=params["reasoning_effort"].get(spec["vendor"]),
    )
    request = urllib.request.Request(
        spec["endpoint"],
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        choice = body.get("choices", [{}])[0] if body.get("choices") else {}
        message = choice.get("message", {}) if isinstance(choice, dict) else {}
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part) for part in content
            )
        if not isinstance(content, str):
            content = ""
        reasoning_fields = [
            field
            for field in ("reasoning", "reasoning_content")
            if isinstance(message, dict) and message.get(field)
        ]
        return {
            "status": "success" if content else "no_final_content",
            "http_status": response.status,
            "response": content,
            "provider_model": body.get("model"),
            "reasoning_present": bool(reasoning_fields),
            "reasoning_chars": sum(
                len(message.get(field, ""))
                for field in reasoning_fields
                if isinstance(message.get(field), str)
            ),
            "finish_reason": choice.get("finish_reason") if isinstance(choice, dict) else None,
            "response_fields": sorted(message) if isinstance(message, dict) else [],
            "usage": body.get("usage"),
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
        }
    except urllib.error.HTTPError as error:
        return _transport_error(error.code, error.__class__.__name__, started)
    except (urllib.error.URLError, TimeoutError) as error:
        return _transport_error(None, type(error).__name__, started)
    except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as error:
        return _transport_error(None, type(error).__name__, started)


def _transport_error(http_status: int | None, error_type: str, started: float) -> dict[str, Any]:
    # 请求已发出但无法确认结果/费用：超时、连接中断、HTTP 5xx（服务端可能已处理）、
    # 响应解析失败（已返回 200 但无法读取 usage）——全部显式标 billing_unknown
    billing_unknown = error_type in (
        "TimeoutError",
        "URLError",
        "JSONDecodeError",
        "KeyError",
        "UnicodeDecodeError",
    ) or (http_status is not None and http_status >= 500)
    return {
        "status": "failed",
        "http_status": http_status,
        "error_type": error_type,
        "response": "",
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
        "billing_unknown": billing_unknown,
    }


# ---------------------------------------------------------------- 运行编排


def _request_snapshot(
    spec: dict[str, Any], params: dict[str, Any], fingerprint: str, case: CaseSpec
) -> dict:
    return {
        "config_fingerprint": fingerprint,
        "protocol_version": case.protocol_version,
        "model": spec["model"],
        "vendor": spec["vendor"],
        "endpoint": spec["endpoint"],
        "messages": spec["messages"],
        "params": params,
    }


def _attempt_key(row: dict[str, Any]) -> tuple[str, int]:
    return row["trial_id"], row["attempt"]


def load_attempts(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """按 (trial_id, attempt) 索引 attempt 事件；同一键以 started 为准合并 finished。"""
    rows, _torn = load_jsonl_tolerant(path)
    merged: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = _attempt_key(row)
        if row.get("phase") == "started":
            merged[key] = {**row, "finished": None}
        elif row.get("phase") == "finished" and key in merged:
            merged[key]["finished"] = row
    return merged


def trial_outcome(
    attempts: dict[tuple[str, int], dict[str, Any]], trial_id: str
) -> dict[str, Any] | None:
    """一个试次的当前结果。

    无 finished（落盘前崩溃）或 billing_unknown（超时/5xx/解析失败/usage 缺失——
    已发出但结果/费用未知）均为 pending_reconciliation，与崩溃路径同口径。
    """
    history = [row for (tid, _), row in attempts.items() if tid == trial_id]
    if not history:
        return None
    last = max(history, key=lambda row: row["attempt"])
    if last.get("finished") is None:
        return {"status": "pending_reconciliation", "attempt": last["attempt"]}
    finished = last["finished"]
    if finished.get("billing_unknown"):
        return {**finished, "status": "pending_reconciliation"}
    return finished


def execute_run(
    run_dir: Path,
    registry: dict[str, Any],
    repeats: int,
    transport: Transport | None,
    ledger: Ledger | None,
    prices: dict[str, dict[str, float]] | None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    budget_total_cny: float | None = None,
    resume: bool = True,
    plan_only: bool = False,
    verbose: bool = True,
    spec: CaseSpec | None = None,
) -> dict[str, Any]:
    """执行（或恢复）一次 run。返回物化视图统计。

    run_dir 必须为空目录（新 run）或含本模块 plan.json 的已有 run（恢复/扩量）。
    plan_only=True 只生成 plan.json 与 not_executed 视图，不进入 transport/ledger——
    不需要传 transport/ledger/prices。
    spec 缺省为默认病例；恢复时传入的 spec 与首跑不一致会因配置指纹不匹配被拒绝。
    """
    plan_path = run_dir / "plan.json"
    attempts_path = run_dir / "attempts.jsonl"
    trials_path = run_dir / "trials.jsonl"

    case = _case_or_default(spec)
    specs = planned_trials(registry, repeats, case)
    params = request_params()
    fingerprint = config_fingerprint(specs, params, case)
    run_id = run_dir.name

    if plan_path.exists() and resume:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if plan["config_fingerprint"] != fingerprint:
            raise RuntimeError(
                f"恢复失败：目录 {run_id} 的配置指纹 {plan['config_fingerprint'][:8]} "
                f"与当前配置 {fingerprint[:8]} 不一致；换配置请新开 run 目录，不得混写"
            )
        # 指纹有意不含词表与 trial_prefix（不影响 API 请求）；协议事实变更在此把关：
        # 词表/前缀/变体/病例文本任一不同 = 不同协议事实，不得混入同一 run 目录
        first_case = plan.get("case_spec")
        if first_case is not None:
            first_facts = {k: v for k, v in first_case.items() if k != "notes"}
            current_facts = case.protocol_facts()
            if first_facts != current_facts:
                changed = sorted(
                    key
                    for key in set(first_facts) | set(current_facts)
                    if first_facts.get(key) != current_facts.get(key)
                )
                raise RuntimeError(
                    f"恢复失败：目录 {run_id} 的 CaseSpec 协议事实与首跑不一致"
                    f"（差异字段：{changed}）；同病例改词表/前缀/变体属协议变更，"
                    "请新开 run 目录并按版本纪律走新版本"
                )
        # 预算与重试上限锁定在首次 plan；恢复时与账本一致，CLI 不许改
        if (
            budget_total_cny is not None
            and ledger is not None
            and (abs(ledger.state.total_cny - budget_total_cny) > 1e-9)
        ):
            raise RuntimeError(
                f"恢复失败：目录 {run_id} 的预算总额 {ledger.state.total_cny} 元"
                f"与当前传入 {budget_total_cny} 元不一致；预算锁定在首次 run，"
                "需要变更请新开 run 目录"
            )
        if max_attempts != plan.get("max_attempts", max_attempts):
            raise RuntimeError(
                f"恢复失败：目录 {run_id} 的 attempt 上限 {plan.get('max_attempts')} "
                f"与当前传入 {max_attempts} 不一致；上限锁定在首次 run"
            )
    else:
        plan = {
            "run_id": run_id,
            "protocol_version": case.protocol_version,
            "case_id": case.case_id,
            "trial_prefix": case.trial_prefix,
            "case_spec": case.as_dict(),
            "config_fingerprint": fingerprint,
            "created_at": datetime.now(UTC).isoformat(),
            "repeats": repeats,
            "max_attempts": max_attempts,
            "params": params,
            "models": {
                spec["model_catalog_id"]: {
                    "model": spec["model"],
                    "vendor": spec["vendor"],
                    "endpoint": spec["endpoint"],
                }
                for spec in specs
            },
            "variants": case.variants,
            "planned_trial_ids": [spec["trial_id"] for spec in specs],
        }
        atomic_write_json(plan_path, plan)

    if plan_only:
        # 只生成计划与 not_executed 视图；不进入 transport/ledger 执行路径
        attempts: dict[tuple[str, int], dict[str, Any]] = {}
        stats = {
            "reused": 0,
            "executed": 0,
            "pending_reconciliation": 0,
            "skipped": 0,
            "budget_refused": 0,
        }
        stats.update(materialize(trials_path, attempts, specs, case))
        return stats

    if transport is None or ledger is None or prices is None:
        raise ValueError("非 plan-only 模式必须提供 transport/ledger/prices")
    attempts = load_attempts(attempts_path)
    stats = {
        "reused": 0,
        "executed": 0,
        "pending_reconciliation": 0,
        "skipped": 0,
        "budget_refused": 0,
    }

    for spec in specs:
        trial_id = spec["trial_id"]
        outcome = trial_outcome(attempts, trial_id)
        if outcome is not None:
            if outcome["status"] == "pending_reconciliation":
                stats["pending_reconciliation"] += 1
                _log(
                    verbose,
                    f"{trial_id}: pending_reconciliation（结果未知，交人工核账，不自动重跑）",
                )
                continue
            if (
                outcome.get("status") == "success"
                and outcome.get("response")
                and outcome.get("config_fingerprint") == fingerprint
            ):
                stats["reused"] += 1
                _log(verbose, f"{trial_id}: 复用已有成功结果（同配置指纹）")
                continue
        used_attempts = len([1 for (tid, _), row in attempts.items() if tid == trial_id])
        if used_attempts >= max_attempts:
            stats["skipped"] += 1
            _log(verbose, f"{trial_id}: attempt 上限 {max_attempts} 已到，跳过")
            continue

        attempt_no = 1 + max(
            (row["attempt"] for (tid, _), row in attempts.items() if tid == trial_id), default=0
        )
        prompt_chars = sum(len(m["content"]) for m in spec["messages"])
        try:
            estimate = estimate_cost_cny(prices, spec["vendor"], prompt_chars, params["max_tokens"])
            ledger.reserve(trial_id, attempt_no, estimate, note=f"run={run_id}")
        except BudgetError as error:
            stats["budget_refused"] += 1
            _log(verbose, f"{trial_id}: 预算拒绝（{error}）")
            continue

        snapshot = _request_snapshot(spec, params, fingerprint, case)
        append_jsonl(
            attempts_path,
            {"phase": "started", "trial_id": trial_id, "attempt": attempt_no, **snapshot},
        )
        config = registry[spec["model_catalog_id"]]
        result = transport.call(config, spec, params)
        finished = {
            "phase": "finished",
            "trial_id": trial_id,
            "attempt": attempt_no,
            "config_fingerprint": fingerprint,
            **{k: v for k, v in result.items()},
        }
        append_jsonl(attempts_path, finished)

        if result.get("status") == "failed" and not result.get("billing_unknown"):
            # 明确失败且请求未送达（如 HTTP 4xx 立即拒绝）：退还预留
            ledger.refund(trial_id, attempt_no, estimate, note="failed_no_charge")
        elif result.get("billing_unknown") or not isinstance(result.get("usage"), dict):
            # 已发出但结果/费用未知（超时/解析失败/usage 缺失）：预留保留，
            # 不按 0 结算——反复超时不能让余额回到原位
            ledger.pending_charge(
                trial_id, attempt_no, estimate, note=result.get("error_type") or "usage_missing"
            )
        else:
            actual = actual_cost_cny(prices, spec["vendor"], result["usage"])
            ledger.settle(trial_id, attempt_no, actual, reserved_cny=estimate)
        attempts[(trial_id, attempt_no)] = {
            "phase": "started",
            "trial_id": trial_id,
            "attempt": attempt_no,
            **snapshot,
            "finished": finished,
        }
        stats["executed"] += 1
        _log(verbose, f"{trial_id}: attempt{attempt_no} {result.get('status')}")

    stats.update(materialize(trials_path, attempts, specs, case))
    return stats


def materialize(
    trials_path: Path,
    attempts: dict[tuple[str, int], dict[str, Any]],
    specs: list[dict[str, Any]],
    case_spec: CaseSpec | None = None,
) -> dict[str, int]:
    """物化 trials.jsonl：计划内每个 trial 一行当前状态（含未执行行），历史 id 全保留。"""
    case = _case_or_default(case_spec)
    counts: dict[str, int] = {}
    planned_ids = [spec["trial_id"] for spec in specs]
    history_ids = sorted({tid for tid, _ in attempts})
    rows = []
    for trial_id in sorted(set(planned_ids) | set(history_ids)):
        spec = next((s for s in specs if s["trial_id"] == trial_id), None)
        outcome = trial_outcome(attempts, trial_id)
        if outcome is None:
            row = {
                "trial_id": trial_id,
                "status": "not_executed",
                "run_id": trials_path.parent.name,
            }
        elif outcome["status"] == "pending_reconciliation":
            row = {"trial_id": trial_id, "status": "pending_reconciliation", **outcome}
        else:
            row = {
                "trial_id": trial_id,
                "status": outcome["status"],
                "http_status": outcome.get("http_status"),
                "response": outcome.get("response", ""),
                "provider_model": outcome.get("provider_model"),
                "finish_reason": outcome.get("finish_reason"),
                "usage": outcome.get("usage"),
                "elapsed_ms": outcome.get("elapsed_ms"),
                "attempt": outcome.get("attempt"),
                "config_fingerprint": outcome.get("config_fingerprint"),
                "run_id": trials_path.parent.name,
            }
        # 供 #10 报告 CLI 直接消费：试次分类需要的元数据字段
        if spec is not None:
            row.update(
                {
                    "model_catalog_id": spec["model_catalog_id"],
                    "model": spec["model"],
                    "vendor": spec["vendor"],
                    "prompt_variant": spec["prompt_variant"],
                    "trial_index": spec["trial_index"],
                    "messages": spec["messages"],
                    "protocol_version": case.protocol_version,
                    "case_id": case.case_id,
                }
            )
        else:
            row.setdefault("model_catalog_id", None)
            row.setdefault("model", None)
            row.setdefault("vendor", None)
            row.setdefault("prompt_variant", None)
            row.setdefault("trial_index", None)
        # 旧记录缺失字段标 unknown，不用现配置回填（验收第 2 条）
        for field in ("provider_model", "finish_reason"):
            if field in row and row[field] is None and row.get("status") == "success":
                row[field] = "unknown"
        outcome_label = row["status"] if row["status"] != "success" else classify_trial(row)
        counts[outcome_label] = counts.get(outcome_label, 0) + 1
        rows.append(row)
    atomic_write_jsonl(trials_path, rows)
    return {"view_total": len(rows), **{f"view_{k}": v for k, v in counts.items()}}


def _log(verbose: bool, message: str) -> None:
    if verbose:
        print(message, flush=True)
