"""issue #2 有界追问测试：触发规则、限额、恢复、预算、findings。全部假网络。"""

from __future__ import annotations

import json

import pytest

from medmirror import followup
from medmirror.budget import Ledger


def make_trial(
    tid,
    model,
    variant,
    index,
    *,
    status="success",
    finish="stop",
    response="答：中医药：可以考虑；西医他汀",
):
    return {
        "trial_id": tid,
        "model_catalog_id": model,
        "vendor": model.split("-")[0],
        "prompt_variant": variant,
        "trial_index": index,
        "status": status,
        "finish_reason": finish,
        "response": response,
        "messages": [{"role": "user", "content": "原始问题"}],
    }


def make_extraction(tid, western="not_mentioned", tcm="not_mentioned", wev="", tev=""):
    return {
        "trial_id": tid,
        "status": "success",
        "extractor_version": "offline-rules-v2",
        "paths": {
            "western": {"state": western, "evidence": wev},
            "tcm": {"state": tcm, "evidence": tev},
        },
    }


def baseline_fixture(*, neutral_tcm="not_mentioned"):
    """三模型 × 3 变体 × index1；中性中医未提及可参数化，其余路径全提及。"""
    trials, extractions = {}, {}
    for model in ("deepseek-v4-flash", "glm-5.3-flash", "step-3.7-flash"):
        for variant in ("neutral", "tcm_mirror", "western_mirror"):
            for index in (1, 2, 3):
                tid = f"exp003-{model}-{variant}-{index}"
                trials[tid] = make_trial(tid, model, variant, index)
                extractions[tid] = make_extraction(
                    tid,
                    western="recommended"
                    if variant == "western_mirror" or variant == "neutral"
                    else "not_mentioned",
                    wev="西医他汀" if variant == "western_mirror" else "",
                    tcm=(
                        neutral_tcm
                        if variant == "neutral"
                        else ("conditional_support" if variant == "tcm_mirror" else "not_mentioned")
                    ),
                    tev="中医药：可以考虑" if variant == "tcm_mirror" else "",
                )
    return trials, extractions


class FakeTransport:
    def __init__(self, results=None):
        self.calls = []
        self.results = results or []

    def call(self, config, spec, params):
        self.calls.append(spec)
        return (
            self.results[len(self.calls) - 1]
            if len(self.calls) <= len(self.results)
            else {
                "status": "success",
                "response": "追问回答",
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
                "finish_reason": "stop",
            }
        )


PRICES = {
    "deepseek": {"input_cache_miss": 8.0, "output": 8.0},
    "glm": {"input_cache_miss": 4.0, "output": 4.0},
    "step": {"input_cache_miss": 1.35, "output": 8.1},
}
PARAMS = {"max_tokens": 512, "temperature": 0.7}


def registry_fixture():
    class Cfg:
        def __init__(self, model):
            self.model_id = model
            self.vendor = model.split("-")[0]
            self.endpoint = "https://example"
            self.api_key_env = "X"

    return {m: Cfg(m) for m in ("deepseek-v4-flash", "glm-5.3-flash", "step-3.7-flash")}


# ---------------------------------------------------------------- 触发规则


def test_select_candidates_basic():
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    assert len(cands) == 3
    for cand in cands:
        assert cand["path"] == "tcm"
        assert cand["prompt_variant"] == "tcm_mirror"
        assert cand["trial_index"] == 1  # 最小 trial_index
        assert cand["followup_id"] == f"{cand['parent_trial_id']}-fu1"
        # 追问消息 = 父消息 + 父回答 + 统一模板
        roles = [m["role"] for m in cand["messages"]]
        assert roles == ["user", "assistant", "user"]
        assert cand["messages"][-1]["content"] == followup.FOLLOWUP_PROMPT


def test_select_no_trigger_when_neutral_mentions():
    trials, extractions = baseline_fixture(neutral_tcm="mentioned")
    assert followup.select_candidates(trials, extractions) == []


def test_select_skips_truncated_neutral():
    trials, extractions = baseline_fixture()
    tid = "exp003-glm-5.3-flash-neutral-2"
    trials[tid]["finish_reason"] = "length"
    cands = followup.select_candidates(trials, extractions)
    assert [c["model_catalog_id"] for c in cands] == ["deepseek-v4-flash", "step-3.7-flash"]


def test_select_mirror_truncated_not_used_as_parent():
    trials, extractions = baseline_fixture()
    for index in (1, 2):  # 镜像前两条完整提及被改成截断
        tid = f"exp003-glm-5.3-flash-tcm_mirror-{index}"
        trials[tid]["finish_reason"] = "length"
    cands = followup.select_candidates(trials, extractions)
    glm = next(c for c in cands if c["model_catalog_id"] == "glm-5.3-flash")
    assert glm["trial_index"] == 3


def test_select_path_order_prefers_western():
    """若 western 也触发（中性西医全未提及+镜像提及），固定顺序先选 western。"""
    trials, extractions = baseline_fixture()
    for index in (1, 2, 3):
        extractions[f"exp003-deepseek-v4-flash-neutral-{index}"]["paths"]["western"]["state"] = (
            "not_mentioned"
        )
    cands = followup.select_candidates(trials, extractions)
    deepseek = next(c for c in cands if c["model_catalog_id"] == "deepseek-v4-flash")
    assert deepseek["path"] == "western"
    assert deepseek["prompt_variant"] == "western_mirror"


def test_select_one_candidate_per_model():
    """中性两条路径都触发时，每模型仍只取固定顺序首个。"""
    trials, extractions = baseline_fixture()
    for index in (1, 2, 3):
        for model in ("deepseek-v4-flash", "glm-5.3-flash", "step-3.7-flash"):
            extractions[f"exp003-{model}-neutral-{index}"]["paths"]["western"]["state"] = (
                "not_mentioned"
            )
            extractions[f"exp003-{model}-western_mirror-{index}"]["paths"]["western"]["state"] = (
                "recommended"
            )
    cands = followup.select_candidates(trials, extractions)
    assert len(cands) == 3
    assert all(c["path"] == "western" for c in cands)


# ---------------------------------------------------------------- 执行


def test_execute_success_and_limits(tmp_path):
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    transport = FakeTransport()
    ledger = Ledger(tmp_path / "budget.jsonl", total_cny=10.0)
    stats = followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands,
        registry=registry_fixture(),
        transport=transport,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    assert stats["executed"] == 3 and stats["reused"] == 0
    assert len(transport.calls) == 3
    rows = followup.load_followup_rows(tmp_path / "followups.jsonl")
    for cand in cands:
        outcome = followup.followup_outcome(rows, cand["followup_id"])
        assert outcome["status"] == "success"
    assert ledger.state.settled_cny > 0
    assert ledger.state.reserved_cny == 0


def test_resume_does_not_recall_success(tmp_path):
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    transport = FakeTransport()
    ledger = Ledger(tmp_path / "budget.jsonl", total_cny=10.0)
    followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands,
        registry=registry_fixture(),
        transport=transport,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    stats2 = followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands,
        registry=registry_fixture(),
        transport=transport,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    assert stats2["reused"] == 3 and stats2["executed"] == 0
    assert len(transport.calls) == 3  # 未新增调用


def test_budget_refused_records_stop_reason(tmp_path):
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    transport = FakeTransport()
    ledger = Ledger(tmp_path / "budget.jsonl", total_cny=0.001)  # 不足以预留任何一次
    stats = followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands,
        registry=registry_fixture(),
        transport=transport,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    assert stats["budget_refused"] == 3 and len(transport.calls) == 0
    assert all(o["stop_reason"] == "budget_refused" for o in stats["outcomes"])


def test_failed_then_retry_on_resume_within_max_attempts(tmp_path):
    """重试语义与 #13 基线一致：单次执行内不内联重试，恢复时再试（attempt 跨恢复累计）。"""
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    transport = FakeTransport(
        results=[
            {"status": "failed", "http_status": 401, "error_type": "HTTPError", "response": ""},
            {
                "status": "success",
                "response": "重试后的回答",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                "finish_reason": "stop",
            },
        ]
    )
    ledger = Ledger(tmp_path / "budget.jsonl", total_cny=10.0)
    stats1 = followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands[:1],
        registry=registry_fixture(),
        transport=transport,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    assert stats1["executed"] == 1 and len(transport.calls) == 1
    stats2 = followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands[:1],
        registry=registry_fixture(),
        transport=transport,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    assert stats2["executed"] == 1 and len(transport.calls) == 2  # 恢复重试一次成功
    rows = followup.load_followup_rows(tmp_path / "followups.jsonl")
    outcome = followup.followup_outcome(rows, cands[0]["followup_id"])
    assert outcome["response"] == "重试后的回答"
    # 第三次：已成功，复用不再调用
    stats3 = followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands[:1],
        registry=registry_fixture(),
        transport=transport,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    assert stats3["reused"] == 1 and len(transport.calls) == 2


def test_attempt_exhausted_leaves_failure_record(tmp_path):
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    failing = FakeTransport(
        results=[
            {"status": "failed", "http_status": 429, "error_type": "HTTPError", "response": ""},
            {"status": "failed", "http_status": 429, "error_type": "HTTPError", "response": ""},
        ]
    )
    ledger = Ledger(tmp_path / "budget.jsonl", total_cny=10.0)
    followup.execute_followups(  # attempt1 失败（明确 4xx，退还预留）
        run_dir=tmp_path,
        candidates=cands[:1],
        registry=registry_fixture(),
        transport=failing,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    stats2 = followup.execute_followups(  # attempt2 失败
        run_dir=tmp_path,
        candidates=cands[:1],
        registry=registry_fixture(),
        transport=failing,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    assert stats2["executed"] == 1 and len(failing.calls) == 2  # max_attempts=2 用尽
    # 再跑一次：不重试；每模型 attempt 上限（=MAX_PER_MODEL）先生效，失败记录保留
    stats3 = followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands[:1],
        registry=registry_fixture(),
        transport=failing,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    assert stats3["executed"] == 0
    assert stats3["outcomes"][0]["stop_reason"] == "max_per_model_reached"
    assert len(failing.calls) == 2


def test_attempt_exhausted_below_model_cap(tmp_path):
    """max_attempts=1（低于每模型上限）时：失败一次即耗尽该候选的 attempt 预算。"""
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    failing = FakeTransport(
        results=[
            {"status": "failed", "http_status": 429, "error_type": "HTTPError", "response": ""},
        ]
    )
    ledger = Ledger(tmp_path / "budget.jsonl", total_cny=10.0)
    followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands[:1],
        registry=registry_fixture(),
        transport=failing,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
        max_attempts=1,
    )
    stats2 = followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands[:1],
        registry=registry_fixture(),
        transport=failing,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
        max_attempts=1,
    )
    assert stats2["executed"] == 0
    assert stats2["outcomes"][0]["stop_reason"] == "attempt_exhausted"
    assert len(failing.calls) == 1


def test_failed_attempts_consume_model_quota(tmp_path):
    """失败调用同样消耗每模型额度——两次失败后该模型任何追问（含重试）均被 ≤2/模型 拦截。"""
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    twin = {**cands[0], "followup_id": cands[0]["followup_id"] + "x"}  # 人为第二条同模型候选
    failing = FakeTransport(
        results=[
            {"status": "failed", "http_status": 429, "error_type": "HTTPError", "response": ""},
            {"status": "failed", "http_status": 429, "error_type": "HTTPError", "response": ""},
        ]
    )
    ledger = Ledger(tmp_path / "budget.jsonl", total_cny=10.0)
    # 第一次：两候选各失败一次 → 该模型 attempt 额度已耗尽（按 attempt 计，不论成败）
    followup.execute_followups(
        run_dir=tmp_path,
        candidates=[cands[0], twin],
        registry=registry_fixture(),
        transport=failing,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    assert len(failing.calls) == 2
    # 第二次恢复：两条候选的重试与任何新调用都被每模型上限拦截
    stats2 = followup.execute_followups(
        run_dir=tmp_path,
        candidates=[cands[0], twin],
        registry=registry_fixture(),
        transport=failing,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    assert stats2["executed"] == 0
    assert all(o["stop_reason"] == "max_per_model_reached" for o in stats2["outcomes"])
    assert len(failing.calls) == 2  # 失败额度不豁免——不再发起新调用


def test_billing_unknown_pending_reconciliation(tmp_path):
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    transport = FakeTransport(
        results=[
            {
                "status": "failed",
                "http_status": None,
                "error_type": "TimeoutError",
                "response": "",
                "billing_unknown": True,
            },
        ]
    )
    ledger = Ledger(tmp_path / "budget.jsonl", total_cny=10.0)
    followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands[:1],
        registry=registry_fixture(),
        transport=transport,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    rows = followup.load_followup_rows(tmp_path / "followups.jsonl")
    outcome = followup.followup_outcome(rows, cands[0]["followup_id"])
    assert outcome["status"] == "pending_reconciliation"
    assert ledger.state.reserved_cny > 0  # 预留保留，不按 0 结算


# ---------------------------------------------------------------- findings


def test_build_findings_content_and_boundary(tmp_path):
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    transport = FakeTransport()
    ledger = Ledger(tmp_path / "budget.jsonl", total_cny=10.0)
    stats = followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands,
        registry=registry_fixture(),
        transport=transport,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    stop_reasons = {o["followup_id"]: o["stop_reason"] for o in stats["outcomes"]}
    rows = followup.load_followup_rows(tmp_path / "followups.jsonl")
    findings = followup.build_findings(cands, rows, extractions, stop_reasons)
    assert len(findings) == 3
    for finding in findings:
        assert finding["observation"]["mirror_mentioned"]["quote"] == "中医药：可以考虑"
        assert finding["followup"]["response"] == "追问回答"
        assert "不作为训练数据" in finding["boundary"]
    followup.write_findings(tmp_path / "findings.jsonl", findings)
    loaded = [json.loads(line) for line in (tmp_path / "findings.jsonl").read_text().splitlines()]
    assert [f["finding_id"] for f in loaded] == [f"finding-{c['followup_id']}" for c in cands]


def test_findings_not_executed_when_plan_only(tmp_path):
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    findings = followup.build_findings(cands, {}, extractions, {})
    assert all(f["followup"]["status"] == "not_executed" for f in findings)


def test_unlocatable_evidence_fail_closed():
    """「原文可定位」fail-closed：evidence 为空 / 不是父回答子串 / 提取失败 → 不触发。"""
    trials, extractions = baseline_fixture()
    # 情形一：glm 全部镜像 evidence 为空字符串（state 仍为提及）
    for index in (1, 2, 3):
        extractions[f"exp003-glm-5.3-flash-tcm_mirror-{index}"]["paths"]["tcm"]["evidence"] = ""
    # 情形二：deepseek 全部镜像 evidence 不是父回答子串
    for index in (1, 2, 3):
        key = f"exp003-deepseek-v4-flash-tcm_mirror-{index}"
        extractions[key]["paths"]["tcm"]["evidence"] = "原文里没有这句"
    # 情形三：step 全部镜像提取 status 失败
    for index in (1, 2, 3):
        extractions[f"exp003-step-3.7-flash-tcm_mirror-{index}"]["status"] = "extraction_failed"
    cands = followup.select_candidates(trials, extractions)
    assert cands == []


def test_neutral_not_mentioned_state_only_uses_extraction_state():
    """中性侧「已提及」只看提取 state（与镜像父的 locatable 判定不同——中性不选父）。"""
    trials, extractions = baseline_fixture(neutral_tcm="mentioned")
    assert followup.select_candidates(trials, extractions) == []


def test_prepare_plan_locks_config(tmp_path):
    """plan 指纹锁定：换配置（max_attempts/消息）恢复同目录被拒绝。"""
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    plan = followup.prepare_plan(
        run_dir=tmp_path,
        candidates=cands,
        params=PARAMS,
        max_attempts=2,
        registry=registry_fixture(),
    )
    assert plan["candidate_count"] == 3
    # 同配置恢复：返回已有 plan
    again = followup.prepare_plan(
        run_dir=tmp_path,
        candidates=cands,
        params=PARAMS,
        max_attempts=2,
        registry=registry_fixture(),
    )
    assert again["config_fingerprint"] == plan["config_fingerprint"]
    # 换 max_attempts → 拒绝
    with pytest.raises(RuntimeError, match="配置指纹不一致"):
        followup.prepare_plan(
            run_dir=tmp_path,
            candidates=cands,
            params=PARAMS,
            max_attempts=1,
            registry=registry_fixture(),
        )
    # 换候选内容 → 拒绝
    mutated = [{**cands[0], "messages": cands[0]["messages"][:-1]}, *cands[1:]]
    with pytest.raises(RuntimeError, match="配置指纹不一致"):
        followup.prepare_plan(
            run_dir=tmp_path,
            candidates=mutated,
            params=PARAMS,
            max_attempts=2,
            registry=registry_fixture(),
        )


def test_reconcile_ledger_closes_orphan_reserve(tmp_path):
    """恢复对账：reserve 后崩溃的两种窗口 + finished 后未结算，最终全部闭合。"""
    ledger_path = tmp_path / "budget.jsonl"
    ledger = Ledger(ledger_path, total_cny=10.0)
    # 窗口一：reserve 后 started 落盘前崩溃（请求未发出）→ refund
    ledger.reserve("fid-a", 1, 0.01, note="crash_before_started")
    # 窗口二：started 落盘后 call 中崩溃 → pending_charge 保留预留
    ledger.reserve("fid-b", 1, 0.02, note="crash_mid_call")
    followup.append_jsonl(
        tmp_path / "followups.jsonl",
        {
            "phase": "started",
            "followup_id": "fid-b",
            "attempt": 1,
            "model_catalog_id": "deepseek-v4-flash",
            "vendor": "deepseek",
        },
    )
    # 窗口三：finished 已落盘（success+usage）但 settle 前崩溃 → 补 settle
    ledger.reserve("fid-c", 1, 0.5, note="crash_before_settle")
    followup.append_jsonl(
        tmp_path / "followups.jsonl",
        {
            "phase": "started",
            "followup_id": "fid-c",
            "attempt": 1,
            "model_catalog_id": "deepseek-v4-flash",
            "vendor": "deepseek",
        },
    )
    followup.append_jsonl(
        tmp_path / "followups.jsonl",
        {
            "phase": "finished",
            "followup_id": "fid-c",
            "attempt": 1,
            "status": "success",
            "response": "答",
            "vendor": "deepseek",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        },
    )
    rows = followup.load_followup_rows(tmp_path / "followups.jsonl")
    reconciled = followup.reconcile_ledger(ledger, rows, PRICES, verbose=False)
    assert reconciled == 3
    assert ledger.state.reserved_cny == 0.02  # 仅 fid-b 的 pending 占位保留
    # fid-c 按实际用量结算（deepseek 8/8 元/M：150 token = 0.0012 元）
    assert abs(ledger.state.settled_cny - 0.0012) < 1e-9
    # 再跑一次：无新未闭合预留
    assert followup.reconcile_ledger(ledger, rows, PRICES, verbose=False) == 0


def test_transport_exception_becomes_pending(tmp_path):
    """传输层抛未捕获异常 → 按「已发出、结果未知」记录并挂账，不中断整轮。"""
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)

    class Exploding:
        calls = 0

        def call(self, config, spec, params):
            Exploding.calls += 1
            if Exploding.calls == 1:
                raise RuntimeError("boom")
            return {
                "status": "success",
                "response": "第二条成功",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                "finish_reason": "stop",
            }

    ledger = Ledger(tmp_path / "budget.jsonl", total_cny=10.0)
    stats = followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands,
        registry=registry_fixture(),
        transport=Exploding(),
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    assert stats["executed"] == 3  # 异常被转为记录，其余候选照常执行
    rows = followup.load_followup_rows(tmp_path / "followups.jsonl")
    outcome = followup.followup_outcome(rows, cands[0]["followup_id"])
    assert outcome["status"] == "pending_reconciliation"
    assert outcome["error_type"] == "RuntimeError"


def test_findings_presented_truncated_and_neutral_ids(tmp_path):
    """截断追问的 presented=truncated（不写成 success）；findings 含中性试次 IDs。"""
    trials, extractions = baseline_fixture()
    cands = followup.select_candidates(trials, extractions)
    transport = FakeTransport(
        results=[
            {  # deepseek：length 截断但有正文
                "status": "success",
                "response": "截断的回答",
                "usage": {"prompt_tokens": 10, "completion_tokens": 4096},
                "finish_reason": "length",
            },
        ]
    )
    ledger = Ledger(tmp_path / "budget.jsonl", total_cny=10.0)
    stats = followup.execute_followups(
        run_dir=tmp_path,
        candidates=cands,
        registry=registry_fixture(),
        transport=transport,
        ledger=ledger,
        prices=PRICES,
        params=PARAMS,
    )
    stop_reasons = {o["followup_id"]: o["stop_reason"] for o in stats["outcomes"]}
    rows = followup.load_followup_rows(tmp_path / "followups.jsonl")
    findings = followup.build_findings(cands, rows, extractions, stop_reasons)
    first = findings[0]
    assert first["followup"]["presented"] == "truncated"
    assert first["followup"]["status"] == "success"  # 原始状态保留
    assert len(first["observation"]["neutral_all_not_mentioned"]["trial_ids"]) == 3
    assert first["extractor_version"] == "offline-rules-v2"
