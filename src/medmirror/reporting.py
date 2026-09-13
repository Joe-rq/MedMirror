"""exp003 的离线分组聚合与截断统计（report-v2）。

只做确定性派生：不改原始记录、不调用模型、不判断医学质量。
分组由协议计划与输入求差得到，截断在派生层单列，不并入完整回答，
也不当作未提及；语义分母默认取计划内完整试次，口径待定标任务（#11）确认后版本化。
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from medmirror.casespec import vocab_digest
from medmirror.protocol import EXTRACTOR_VERSION, PATH_PATTERNS, extract_trial

REPORT_VERSION = "exp003-report-v2"

# 试次分类；unknown_finish 表示结束原因缺失或非 stop/length，无法核实完整性，不并入完整。
CATEGORY_ORDER = ("complete", "truncated", "failed", "not_executed", "unknown_finish")

# 提取器可能给出的全部态度（offline-rules-v2 起含 needs_review）；未提及与其余态度分开，永不合并。
STATE_ORDER = (
    "recommended",
    "conditional_support",
    "mentioned",
    "opposed",
    "needs_review",
    "not_mentioned",
)

CALIBRATION_STATUS = "pending-issue-11"

QUOTE_DISPLAY_LIMIT = 160


def classify_trial(trial: dict[str, Any]) -> str:
    """把单条试次归入五类之一；只读，不修改原始记录。

    status=not_executed（未来运行器显式写入的计划内未执行行）→ not_executed；
    status≠success 或成功但无最终正文 → failed（与执行器"无正文不算成功"口径一致），
    正文为空的非答案不得稀释语义分母，也不计为未提及。
    """
    status = trial.get("status")
    if status == "not_executed":
        return "not_executed"
    response = trial.get("response")
    if status != "success" or not (isinstance(response, str) and response.strip()):
        return "failed"
    finish = trial.get("finish_reason")
    if finish == "stop":
        return "complete"
    if finish == "length":
        return "truncated"
    return "unknown_finish"


def _extraction_input(trial: dict[str, Any]) -> dict[str, Any]:
    """提取器无法处理非字符串正文；此处无条件最小规范化为空串。"""
    if not isinstance(trial.get("response"), str):
        return {**trial, "response": ""}
    return trial


def extract_sorted(
    trials: list[dict[str, Any]], paths: dict[str, list[str]] | None = None
) -> list[dict[str, Any]]:
    """校验输入契约、逐条提取并按 trial_id 排序；失败试次也保留 extraction 行。

    paths 缺省为默认病例词表；新病例穿自己的词表（issue #50）。
    """
    for trial in trials:
        trial_id = trial.get("trial_id")
        if not isinstance(trial_id, str) or not trial_id:
            raise ValueError(f"存在缺失或非法 trial_id 的输入行：{trial_id!r}")
    effective_paths = paths if paths is not None else PATH_PATTERNS
    rows = [
        extract_trial(_extraction_input(trial), paths=paths)
        for trial in sorted(trials, key=lambda t: t["trial_id"])
    ]
    # 词表签名随行落盘（评审 P1）：报告侧与提取侧词表必须逐字节同源，
    # 首命中词抽查不够（同键不同词、先命中项恰好重叠时会漏判）
    for row in rows:
        row["paths_digest"] = vocab_digest(effective_paths)
    return rows


def _state_counts() -> dict[str, int]:
    return {state: 0 for state in STATE_ORDER}


def _slice_key(catalog_id: Any, variant: Any) -> str:
    return f"{catalog_id or 'unknown-model'}::{variant or 'unknown-variant'}"


def _slice_fields(record: dict[str, Any]) -> tuple[Any, Any]:
    return record.get("model_catalog_id") or record.get("model"), record.get("prompt_variant")


def _spec_key(record: dict[str, Any]) -> str:
    return _slice_key(*_slice_fields(record))


def _ensure_slice(
    slices: dict[str, dict[str, Any]], record: dict[str, Any], paths: dict[str, list[str]]
) -> dict[str, Any]:
    catalog_id, variant = _slice_fields(record)
    return slices.setdefault(
        _slice_key(catalog_id, variant), _new_slice(catalog_id, variant, paths)
    )


def _bump_category(slice_data: dict[str, Any], category: str, trial_id: str) -> None:
    slice_data["counts"][category] += 1
    slice_data["trial_ids_by_category"][category].append(trial_id)


def _new_slice(catalog_id: Any, variant: Any, paths: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "model_catalog_id": catalog_id,
        "prompt_variant": variant,
        "planned_n": 0,
        "counts": {name: 0 for name in CATEGORY_ORDER},
        "trial_ids_by_category": {name: [] for name in CATEGORY_ORDER},
        "unplanned_trial_ids": [],
        "paths": {
            path: {
                "denominator": "complete",
                "complete_n": 0,
                "mentioned_n": 0,
                "mention_rate": None,
                "state_counts": _state_counts(),
                "trials_by_state": {state: [] for state in STATE_ORDER},
                "truncated_state_counts": _state_counts(),
                "truncated_trials_by_state": {state: [] for state in STATE_ORDER},
                "truncated_mentioned_n": 0,
                "evidence_index": [],
            }
            for path in paths
        },
    }


def _record_semantics(
    slice_data: dict[str, Any], trial_id: str, extraction: dict[str, Any], category: str
) -> None:
    """把一条计划内试次的提取结果记入分组；截断观察单独累计，不进语义分母。"""
    truncated = category == "truncated"
    for path, path_data in extraction["paths"].items():
        target = slice_data["paths"][path]
        state = path_data["state"]
        if truncated:
            target["truncated_state_counts"][state] += 1
            target["truncated_trials_by_state"][state].append(trial_id)
        else:
            target["complete_n"] += 1
            target["state_counts"][state] += 1
            target["trials_by_state"][state].append(trial_id)
        if path_data["mentioned"]:
            entry = {
                "trial_id": trial_id,
                "state": state,
                "term": path_data["term"],
                "evidence": path_data["evidence"],
            }
            if truncated:
                entry["truncated"] = True
            target["evidence_index"].append(entry)


def _mentioned(states: dict[str, int]) -> int:
    return sum(count for state, count in states.items() if state != "not_mentioned")


def build_report(
    trials: list[dict[str, Any]],
    extractions: list[dict[str, Any]],
    planned: list[dict[str, Any]],
    pricing: dict[str, dict[str, float]] | None = None,
    paths: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """由原始试次、提取结果与协议计划生成确定性分析报告。

    trials 为 load_jsonl 的原始行；extractions 为对应的提取结果（按 trial_id 对齐）；
    planned 为协议计划试次（含 trial_id / model_catalog_id / prompt_variant）。
    相同输入与版本产生完全一致的结果，产物不含时间戳。
    paths 缺省为默认病例词表；提取与报告须同源（同一份 CaseSpec 的词表）。
    """
    effective_paths = paths if paths is not None else PATH_PATTERNS
    ids = [trial.get("trial_id") for trial in trials]
    duplicated = sorted(tid for tid, count in Counter(ids).items() if count > 1)
    if duplicated:
        raise ValueError(f"输入存在重复 trial_id：{duplicated}")
    by_extraction = {row["trial_id"]: row for row in extractions}
    missing_extraction = sorted(set(ids) - set(by_extraction))
    if missing_extraction:
        raise ValueError(f"以下试次缺少提取结果：{missing_extraction}")
    # 提取器与报告词表一旦漂移（#11/#12 改动后未同步）立即显式报错，不产出半成品报告
    for row in extractions:
        if set(row["paths"]) != set(effective_paths):
            missing = sorted(set(effective_paths) - set(row["paths"]))
            extra = sorted(set(row["paths"]) - set(effective_paths))
            raise ValueError(
                f"{row['trial_id']}：提取结果路径集与词表不一致（缺 {missing}，多 {extra}）"
            )
        # 词表签名守卫（评审 P1）：extract_sorted 产出的行携带提取时词表摘要，
        # 与报告词表摘要逐字节比对——同键不同词的两份词表必被拦截。
        row_digest = row.get("paths_digest")
        if row_digest is not None and row_digest != vocab_digest(effective_paths):
            raise ValueError(
                f"{row['trial_id']}：提取词表签名与报告词表不一致"
                f"（提取 {row_digest[:12]}，报告 {vocab_digest(effective_paths)[:12]}）；"
                "提取与报告必须用同一份 CaseSpec 词表"
            )
        # 无签名的历史行退回首命中词抽查（部分覆盖：全零命中行无从对账）
        for path_name, path_data in row["paths"].items():
            term = path_data.get("term")
            if (
                row_digest is None
                and path_data.get("mentioned")
                and term
                and term not in effective_paths[path_name]
            ):
                raise ValueError(
                    f"{row['trial_id']}：路径 {path_name} 的命中词 {term!r} 不在报告词表中"
                    "（提取与报告须用同一份 CaseSpec 词表）"
                )
        for path_data in row["paths"].values():
            if path_data["state"] not in STATE_ORDER:
                raise ValueError(
                    f"{row['trial_id']}：提取器返回未知态度 {path_data['state']!r}（词表漂移）"
                )

    pricing = pricing or {}
    planned_ids = {spec["trial_id"] for spec in planned}
    rows_by_id = {trial["trial_id"]: trial for trial in trials}
    executed = sorted(trials, key=lambda t: t["trial_id"])

    # 分组骨架来自协议计划（模型×问法 恒定展开），与输入无关，空组也保持可见。
    slices: dict[str, dict[str, Any]] = {}
    mismatched: list[str] = []
    for spec in planned:
        slice_data = _ensure_slice(slices, spec, effective_paths)
        slice_data["planned_n"] += 1
        row = rows_by_id.get(spec["trial_id"])
        if row is not None and (
            # 身份字段：catalog_id（缺省回退 model）+ 问法 + vendor；model 本身可被环境覆盖，不作身份
            _spec_key(row) != _spec_key(spec)
            or (row.get("vendor") and spec.get("vendor") and row["vendor"] != spec["vendor"])
        ):
            # trial_id 与计划匹配但元数据不一致：按计划分组会掩盖数据损坏
            mismatched.append(spec["trial_id"])
        category = classify_trial(row) if row is not None else "not_executed"
        _bump_category(slice_data, category, spec["trial_id"])
        if row is not None and category in ("complete", "truncated"):
            _record_semantics(
                slice_data, spec["trial_id"], by_extraction[spec["trial_id"]], category
            )
    if mismatched:
        raise ValueError(
            f"输入行的模型/供应商/问法元数据与协议计划不一致：{sorted(mismatched)}；"
            "请先核对原始记录，报告不按损坏元数据静默归组。"
        )

    # 计划外试次只列名单，不进入任何计划内计数或语义分母；异常输入显式暴露，不静默丢弃。
    unplanned_ids = [t["trial_id"] for t in executed if t["trial_id"] not in planned_ids]
    for trial_id in unplanned_ids:
        _ensure_slice(slices, rows_by_id[trial_id], effective_paths)["unplanned_trial_ids"].append(
            trial_id
        )

    for slice_data in slices.values():
        for target in slice_data["paths"].values():
            target["mentioned_n"] = _mentioned(target["state_counts"])
            target["mention_rate"] = (
                round(target["mentioned_n"] / target["complete_n"], 3)
                if target["complete_n"]
                else None
            )
            target["truncated_mentioned_n"] = _mentioned(target["truncated_state_counts"])

    total_counts = {
        name: sum(item["counts"][name] for item in slices.values()) for name in CATEGORY_ORDER
    }

    # 顶层类别名单只从分组里的单一事实来源展平，不再对 trials 重新分类。
    sorted_slices = [slices[key] for key in sorted(slices)]

    def flattened(category: str) -> list[str]:
        return sorted(
            tid for item in sorted_slices for tid in item["trial_ids_by_category"][category]
        )

    truncated_ids = flattened("truncated")
    truncated_details = [
        {
            "trial_id": trial_id,
            "slice": _spec_key(rows_by_id[trial_id]),
            "finish_reason": rows_by_id[trial_id].get("finish_reason"),
            "response_chars": len(rows_by_id[trial_id].get("response") or ""),
        }
        for trial_id in truncated_ids
    ]
    complete_ids = flattened("complete")
    evidence_summary = {
        "complete_n": len(complete_ids),
        "evidence_mentioned_n": sum(
            1 for tid in complete_ids if by_extraction[tid]["evidence_mentioned"]
        ),
        "identifiable_source_n": sum(
            1 for tid in complete_ids if by_extraction[tid]["identifiable_source"]
        ),
        "note": "未定标的规则命中；来源识别规则已按 #12 收紧（裸机构名与泛指南不算），"
        "未经 #11 专业核实不作为已核实来源。",
    }

    # usage 与费用口径＝全部已执行试次（含截断），一次遍历按供应商累计。
    tokens_by_vendor: dict[str, dict[str, int]] = {}
    usage_total_tokens = 0
    for trial in executed:
        usage = trial.get("usage")
        if not isinstance(usage, dict):
            continue
        bucket = tokens_by_vendor.setdefault(
            trial.get("vendor"), {"prompt_tokens": 0, "completion_tokens": 0}
        )
        bucket["prompt_tokens"] += int(usage.get("prompt_tokens") or 0)
        bucket["completion_tokens"] += int(usage.get("completion_tokens") or 0)
        usage_total_tokens += int(usage.get("total_tokens") or 0)

    estimated_by_vendor: dict[str, float] = {}
    for vendor in sorted(pricing):
        tokens = tokens_by_vendor.get(vendor, {"prompt_tokens": 0, "completion_tokens": 0})
        price = pricing[vendor]
        estimated_by_vendor[vendor] = round(
            (
                tokens["prompt_tokens"] * price["input_cache_miss"]
                + tokens["completion_tokens"] * price["output"]
            )
            / 1_000_000,
            6,
        )

    run_ids = sorted({trial["run_id"] for trial in executed if trial.get("run_id")})

    return {
        "report_version": REPORT_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "semantic_calibration": "uncalibrated",
        "calibration_status": CALIBRATION_STATUS,
        "protocol_versions": sorted(
            {trial["protocol_version"] for trial in executed if trial.get("protocol_version")}
        ),
        "denominator_policy": {
            "semantic": "计划内完整试次（complete）",
            "truncated": "单列并保留部分观察，不并入完整、不当作未提及",
            "failed": "不进语义分母，不计为未提及；status 缺失或成功但无正文也按 failed 处理",
            "usage_and_cost": "全部已执行试次（含截断与失败中的已耗 tokens）",
            "status": "待 #11 定标确认后版本化",
        },
        "planned_n": len(planned),
        "executed_n": len(trials),
        "counts": total_counts,
        "truncated_trial_ids": truncated_ids,
        "failed_trial_ids": flattened("failed"),
        "not_executed_trial_ids": flattened("not_executed"),
        "unknown_finish_trial_ids": flattened("unknown_finish"),
        "unplanned_trial_ids": unplanned_ids,
        "truncated_trials": truncated_details,
        "run_ids": run_ids,
        "resumed": len(run_ids) > 1,
        "usage_total_tokens": usage_total_tokens,
        "estimated_cost_cny_by_vendor": estimated_by_vendor,
        "estimated_cost_cny_total": round(sum(estimated_by_vendor.values()), 6),
        "evidence": evidence_summary,
        "slices": {key: slices[key] for key in sorted(slices)},
    }


def _display_quote(text: str) -> str:
    # 展示层把连续空白（含换行）折叠为单个空格，避免模型回答里的 Markdown 破坏报告结构；
    # analysis.json 保留逐字原文。
    flat = " ".join(text.split())
    if len(flat) > QUOTE_DISPLAY_LIMIT:
        return flat[:QUOTE_DISPLAY_LIMIT] + "……（超长截断显示，全文见 analysis.json）"
    return flat


def _evidence_line(row: dict[str, Any]) -> str:
    label = f"{row['state']}·截断，不计分母" if row.get("truncated") else row["state"]
    return f"  - `{row['trial_id']}` [{label}] 命中「{row['term']}」：{_display_quote(row['evidence'])}"


def _n_of_denominator(target: dict[str, Any]) -> str:
    if target["complete_n"]:
        return f"{target['mentioned_n']}/{target['complete_n']}"
    return f"-/{target['complete_n']}"


def render_markdown(report: dict[str, Any], paths: dict[str, list[str]] | None = None) -> str:
    """渲染 Markdown 报告；paths 缺省为默认病例词表，须与生成 report 的词表同源。

    注意：本渲染器为 exp003 品牌（标题与指路文案锚定 exp003）；跨病例通用渲染待新报告版本。
    """
    effective_paths = paths if paths is not None else PATH_PATTERNS
    counts = report["counts"]
    costs = report["estimated_cost_cny_by_vendor"]
    cost_text = (
        "、".join(f"{vendor} {amount}" for vendor, amount in costs.items()) + " 元"
        if costs
        else "暂无登记价格"
    )
    path_labels = {"western": "西医", "tcm": "中医"}
    lines = [
        "# exp003 离线分组报告",
        "",
        f"- 报告版本 `{report['report_version']}`；提取器 `{report['extractor_version']}`；"
        f"语义提取**未定标**（{report['calibration_status']}）。",
        f"- 协议版本：{'、'.join(report['protocol_versions']) or '未知'}；"
        f"run：{len(report['run_ids'])} 个（{'含恢复重跑' if report['resumed'] else '单次'}）。",
        f"- 数量：计划 {report['planned_n']} ／ 已执行 {report['executed_n']} ／ "
        f"完整 {counts['complete']} ／ 截断 {counts['truncated']} ／ 失败 {counts['failed']} ／ "
        f"未执行 {counts['not_executed']} ／ 结束原因未知 {counts['unknown_finish']}。",
        "- 指标分母＝计划内完整试次；截断单列，不并入完整、不当作未提及；失败不计为未提及。"
        "分母口径待 #11 定标确认后版本化。",
        f"- usage 累计 {report['usage_total_tokens']} tokens、估算成本 {cost_text}"
        "（口径：全部已执行试次，含截断；按登记价格，DeepSeek 为高峰价）。",
        f"- 证据词命中 {report['evidence']['evidence_mentioned_n']}／来源可识别 "
        f"{report['evidence']['identifiable_source_n']}（完整试次；未定标规则命中，不等于已核实来源）。",
        "",
        "## 分组总览",
        "",
        "| 分组 | 计划 | 完整 | 截断 | 失败 | 未执行 | 原因未知 | "
        + " | ".join(f"{path_labels.get(path, path)}提及 n/N" for path in effective_paths)
        + " |",
        "|---|" + "|".join(["---:"] * (6 + len(effective_paths))) + "|",
    ]
    for key, slice_data in report["slices"].items():
        sc = slice_data["counts"]
        rates = "".join(
            f" {_n_of_denominator(slice_data['paths'][path])} |" for path in effective_paths
        )
        lines.append(
            f"| {key} | {slice_data['planned_n']} | {sc['complete']} | {sc['truncated']} | "
            f"{sc['failed']} | {sc['not_executed']} | {sc['unknown_finish']} |{rates}"
        )

    lines.extend(["", "## 各组态度计数与原文索引", ""])
    for key, slice_data in report["slices"].items():
        lines.extend([f"### {key}", ""])
        if slice_data.get("unplanned_trial_ids"):
            lines.append(
                f"- 计划外试次（不进任何计数）：{'、'.join(slice_data['unplanned_trial_ids'])}"
            )
        for path, target in slice_data["paths"].items():
            sc = target["state_counts"]
            lines.append(
                f"- **{path_labels.get(path, path)}（{path}）** 完整分母 {target['complete_n']}，"
                f"提及 {target['mentioned_n']}：推荐 {sc['recommended']}／条件支持 "
                f"{sc['conditional_support']}／仅提及 {sc['mentioned']}／反对 {sc['opposed']}／"
                f"需复核 {sc['needs_review']}／未提及 {sc['not_mentioned']}"
            )
            grouped = [
                f"{state} {'、'.join(ids)}"
                for state, ids in target["trials_by_state"].items()
                if ids
            ]
            if grouped:
                lines.append(f"  - trial 归属：{'；'.join(grouped)}")
            for row in target["evidence_index"]:
                if not row.get("truncated"):
                    lines.append(_evidence_line(row))
            for row in target["evidence_index"]:
                if row.get("truncated"):
                    lines.append(_evidence_line(row))
        lines.append("")

    lines.extend(
        [
            "## 截断试次",
            "",
            "| trial | 分组 | finish_reason | 保留正文字数 |",
            "|---|---|---|---:|",
        ]
    )
    for item in report["truncated_trials"]:
        lines.append(
            f"| {item['trial_id']} | {item['slice']} | {item['finish_reason']} | "
            f"{item['response_chars']} |"
        )
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 提及不等于支持；未提及不等于反对；截断正文的部分观察仅作记录，不进分母。",
            "- 语义提取为未定标的规则命中，不构成医学质量或 Bias 结论；医学判断保留专业复核。",
            f"- 计划外 trial_id：{'、'.join(report['unplanned_trial_ids']) or '无'}。",
            "- 本报告由 `scripts/report_exp003.py --input <trials.jsonl> --output <目录>` "
            "离线重放生成；相同版本与输入产出字节一致。",
        ]
    )
    return "\n".join(lines) + "\n"
