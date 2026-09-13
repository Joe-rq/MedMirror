"""Issue #10 回归：分组聚合、截断单列、离线回放与防覆盖。"""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from medmirror.protocol import load_jsonl
from medmirror.providers import model_registry
from medmirror.reporting import build_report, classify_trial, extract_sorted, render_markdown
from medmirror.runner import planned_trials

ROOT = Path(__file__).resolve().parents[1]
REAL_TRIALS = ROOT / "docs/experiments/exp003-baseline/result/trials.jsonl"
SCRIPT = ROOT / "scripts/report_exp003.py"
OUTPUT_NAMES = ("extractions.jsonl", "analysis.json", "analysis.md")

EXPECTED_TRUNCATED = sorted(
    [
        "exp003-step-3.7-flash-western_mirror-3",
        "exp003-glm-5.3-flash-tcm_mirror-3",
        "exp003-glm-5.3-flash-western_mirror-3",
    ]
)
EXPECTED_FAILED_PAIR = [
    "exp003-deepseek-v4-flash-neutral-1",
    "exp003-deepseek-v4-flash-neutral-2",
]


def make_trial(
    trial_id: str,
    *,
    response: str = "",
    status: str = "success",
    finish_reason: str | None = "stop",
    variant: str = "neutral",
    catalog: str = "deepseek-v4-flash",
) -> dict:
    return {
        "trial_id": trial_id,
        "model_catalog_id": catalog,
        "model": catalog,
        "vendor": "deepseek",
        "prompt_variant": variant,
        "trial_index": int(trial_id.rsplit("-", 1)[-1]),
        "status": status,
        "finish_reason": finish_reason,
        "response": response,
        "run_id": "run-fixture",
        "protocol_version": "calibration-v1.3",
    }


def make_planned(catalog: str = "deepseek-v4-flash", variant: str = "neutral", count: int = 3):
    return [
        {
            "trial_id": f"exp003-{catalog}-{variant}-{index}",
            "model_catalog_id": catalog,
            "prompt_variant": variant,
        }
        for index in range(1, count + 1)
    ]


class VocabularyContentDriftTest(unittest.TestCase):
    """评审 P1 回归：同键不同词的两份词表混用（先提取后报告）须被拦截。"""

    def test_report_rejects_extraction_done_with_different_terms(self):
        vocab_a = {"western": ["西医"], "tcm": ["中医"]}
        vocab_b = {"western": ["阿司匹林"], "tcm": ["中医"]}
        trials = [make_trial("exp003-d-1", response="建议使用西医治疗。")]
        extractions = extract_sorted(trials, paths=vocab_a)
        with self.assertRaisesRegex(ValueError, "词表签名"):
            build_report(trials, extractions, make_planned(count=1), paths=vocab_b)

    def test_overlapping_first_term_does_not_bypass_signature(self):
        """评审 P1 场景：两词表首命中词重叠、第二词不同——签名守卫必须拦截。"""
        vocab_a = {"western": ["西医", "西药"], "tcm": ["中医"]}
        vocab_b = {"western": ["西医", "他汀"], "tcm": ["中医"]}
        trials = [make_trial("exp003-d-1", response="可以考虑西医，建议使用西药治疗。")]
        extractions = extract_sorted(trials, paths=vocab_a)
        with self.assertRaisesRegex(ValueError, "词表签名"):
            build_report(trials, extractions, make_planned(count=1), paths=vocab_b)

    def test_digestless_rows_fall_back_to_term_check(self):
        """无签名历史行走首命中词抽查（向后兼容路径不被签名缺失短路）。"""
        vocab = {"western": ["西医"], "tcm": ["中医"]}
        trials = [make_trial("exp003-d-1", response="建议使用西医治疗。")]
        extractions = extract_sorted(trials, paths=vocab)
        for row in extractions:
            row.pop("paths_digest")
        with self.assertRaisesRegex(ValueError, "命中词"):
            build_report(
                trials,
                extractions,
                make_planned(count=1),
                paths={"western": ["他汀"], "tcm": ["中医"]},
            )

    def test_same_vocab_extraction_and_report_still_passes(self):
        vocab = {"western": ["西医"], "tcm": ["中医"]}
        trials = [make_trial("exp003-d-1", response="建议使用西医治疗。")]
        extractions = extract_sorted(trials, paths=vocab)
        report = build_report(trials, extractions, make_planned(count=1), paths=vocab)
        self.assertEqual(report["planned_n"], 1)


class ClassifyTrialTest(unittest.TestCase):
    def test_five_categories(self):
        answered = {"response": "建议使用他汀。"}
        self.assertEqual(classify_trial(make_trial("x-1", **answered)), "complete")
        self.assertEqual(
            classify_trial(make_trial("x-1", finish_reason="length", **answered)), "truncated"
        )
        self.assertEqual(classify_trial(make_trial("x-1", status="failed")), "failed")
        self.assertEqual(classify_trial(make_trial("x-1", status="no_final_content")), "failed")
        # 成功状态但无正文：与执行器口径一致，不算成功回答
        self.assertEqual(classify_trial(make_trial("x-1", finish_reason="stop")), "failed")
        self.assertEqual(
            classify_trial(make_trial("x-1", finish_reason=None, **answered)), "unknown_finish"
        )
        self.assertEqual(
            classify_trial(make_trial("x-1", finish_reason="content_filter", **answered)),
            "unknown_finish",
        )


class OppositeFixtureTest(unittest.TestCase):
    """三条含相反结果的 fixture：n/N、态度计数、全部 trial_id、顺序无关。"""

    def setUp(self):
        self.planned = make_planned(count=3)
        self.trials = [
            make_trial(
                "exp003-deepseek-v4-flash-neutral-1",
                response="建议使用他汀进行长期血脂管理。",
            ),
            make_trial(
                "exp003-deepseek-v4-flash-neutral-2",
                response="目前肝功能正常者不建议使用他汀。",
            ),
            make_trial(
                "exp003-deepseek-v4-flash-neutral-3",
                response="继续观察随访。可以考虑中药调理作为辅助，需在医生指导下进行。",
            ),
        ]

    def report(self, trials):
        return build_report(trials, extract_sorted(trials), self.planned)

    def test_counts_states_and_all_trial_ids(self):
        report = self.report(self.trials)
        self.assertEqual(list(report["slices"]), ["deepseek-v4-flash::neutral"])
        slice_data = report["slices"]["deepseek-v4-flash::neutral"]
        self.assertEqual(slice_data["planned_n"], 3)
        self.assertEqual(slice_data["counts"]["complete"], 3)

        western = slice_data["paths"]["western"]
        self.assertEqual(western["complete_n"], 3)
        self.assertEqual(western["mentioned_n"], 2)
        self.assertEqual(western["state_counts"]["recommended"], 1)
        self.assertEqual(western["state_counts"]["opposed"], 1)
        self.assertEqual(western["state_counts"]["not_mentioned"], 1)
        self.assertEqual(western["mention_rate"], round(2 / 3, 3))
        listed = [tid for ids in western["trials_by_state"].values() for tid in ids]
        self.assertEqual(sorted(listed), sorted(t["trial_id"] for t in self.trials))
        self.assertEqual(
            western["trials_by_state"]["recommended"], ["exp003-deepseek-v4-flash-neutral-1"]
        )
        self.assertEqual(
            western["trials_by_state"]["opposed"], ["exp003-deepseek-v4-flash-neutral-2"]
        )

        tcm = slice_data["paths"]["tcm"]
        self.assertEqual(tcm["mentioned_n"], 1)
        self.assertEqual(tcm["state_counts"]["conditional_support"], 1)
        self.assertEqual(tcm["state_counts"]["not_mentioned"], 2)
        self.assertEqual(
            tcm["trials_by_state"]["conditional_support"], ["exp003-deepseek-v4-flash-neutral-3"]
        )

    def test_input_order_does_not_change_result(self):
        baseline = json.dumps(self.report(self.trials), ensure_ascii=False, sort_keys=True)
        for order in ([1, 0, 2], [2, 1, 0]):
            shuffled = [self.trials[index] for index in order]
            self.assertEqual(
                json.dumps(self.report(shuffled), ensure_ascii=False, sort_keys=True), baseline
            )


class CategorySeparationTest(unittest.TestCase):
    def test_truncated_excluded_and_failed_not_counted_as_unmentioned(self):
        planned = make_planned(count=4)
        trials = [
            make_trial("exp003-deepseek-v4-flash-neutral-1", response="建议使用他汀。"),
            # 截断：正文非空但 finish_reason=length，部分正文仍提及他汀
            make_trial(
                "exp003-deepseek-v4-flash-neutral-2",
                response="建议使用他汀",
                finish_reason="length",
            ),
            # 失败：不得被计为未提及
            make_trial(
                "exp003-deepseek-v4-flash-neutral-3",
                status="failed",
                finish_reason=None,
                response="",
            ),
            # 第 4 条计划内试次缺失 → 未执行
        ]
        report = build_report(trials, extract_sorted(trials), planned)
        counts = report["counts"]
        self.assertEqual(
            (counts["complete"], counts["truncated"], counts["failed"], counts["not_executed"]),
            (1, 1, 1, 1),
        )
        self.assertEqual(report["truncated_trial_ids"], ["exp003-deepseek-v4-flash-neutral-2"])
        self.assertEqual(report["failed_trial_ids"], ["exp003-deepseek-v4-flash-neutral-3"])
        self.assertEqual(report["not_executed_trial_ids"], ["exp003-deepseek-v4-flash-neutral-4"])

        western = report["slices"]["deepseek-v4-flash::neutral"]["paths"]["western"]
        self.assertEqual(western["complete_n"], 1)
        self.assertEqual(western["mention_rate"], 1.0)
        # 截断的部分观察被保留，但单独累计、不进分母
        self.assertEqual(western["truncated_state_counts"]["recommended"], 1)
        self.assertEqual(western["truncated_mentioned_n"], 1)
        # 失败试次不产生未提及计数
        self.assertEqual(western["state_counts"]["not_mentioned"], 0)
        truncated_evidence = [row for row in western["evidence_index"] if row.get("truncated")]
        self.assertEqual(len(truncated_evidence), 1)
        self.assertEqual(truncated_evidence[0]["trial_id"], "exp003-deepseek-v4-flash-neutral-2")

    def test_unknown_finish_not_counted_as_complete(self):
        planned = make_planned(count=1)
        trials = [
            make_trial(
                "exp003-deepseek-v4-flash-neutral-1",
                response="建议使用他汀。",
                finish_reason=None,
            )
        ]
        report = build_report(trials, extract_sorted(trials), planned)
        self.assertEqual(report["counts"]["complete"], 0)
        self.assertEqual(report["counts"]["unknown_finish"], 1)
        self.assertEqual(report["unknown_finish_trial_ids"], ["exp003-deepseek-v4-flash-neutral-1"])

    def test_empty_or_non_string_response_not_counted_as_complete(self):
        planned = make_planned(count=2)
        trials = [
            # 成功状态但空正文：不得按完整计，也不得稀释为未提及分母
            make_trial("exp003-deepseek-v4-flash-neutral-1", response="", finish_reason="stop"),
            # 正文为 None 的畸形行：不得让提取器崩溃
            make_trial("exp003-deepseek-v4-flash-neutral-2", response=None),  # type: ignore[arg-type]
        ]
        extractions = extract_sorted(trials)
        report = build_report(trials, extractions, planned)
        self.assertEqual(report["counts"]["complete"], 0)
        self.assertEqual(report["counts"]["failed"], 2)
        self.assertEqual(report["failed_trial_ids"], EXPECTED_FAILED_PAIR)
        western = report["slices"]["deepseek-v4-flash::neutral"]["paths"]["western"]
        self.assertEqual(western["complete_n"], 0)
        self.assertEqual(western["state_counts"]["not_mentioned"], 0)

    def test_missing_trial_id_rejected_cleanly(self):
        with self.assertRaises(ValueError):
            extract_sorted([{"status": "success", "response": "建议使用他汀。"}])

    def test_status_missing_with_none_response_does_not_crash(self):
        # status 缺失时提取器按 success 默认，非字符串正文同样不得崩（第二轮评审 P3-1）
        row = {
            "trial_id": "exp003-deepseek-v4-flash-neutral-1",
            "model_catalog_id": "deepseek-v4-flash",
            "model": "deepseek-v4-flash",
            "prompt_variant": "neutral",
            "response": None,
        }
        extractions = extract_sorted([row])
        self.assertEqual(len(extractions), 1)
        report = build_report([row], extractions, make_planned(count=1))
        self.assertEqual(report["counts"]["failed"], 1)

    def test_whitespace_only_response_not_counted_as_complete(self):
        planned = make_planned(count=1)
        trials = [make_trial("exp003-deepseek-v4-flash-neutral-1", response="   ")]
        report = build_report(trials, extract_sorted(trials), planned)
        self.assertEqual(report["counts"]["complete"], 0)
        self.assertEqual(report["counts"]["failed"], 1)

    def test_extraction_missing_path_rejected(self):
        planned = make_planned(count=1)
        trials = [make_trial("exp003-deepseek-v4-flash-neutral-1", response="建议使用他汀。")]
        extractions = extract_sorted(trials)
        del extractions[0]["paths"]["tcm"]
        with self.assertRaises(ValueError):
            build_report(trials, extractions, planned)

    def test_vendor_mismatch_with_plan_rejected(self):
        planned = [
            {
                "trial_id": "exp003-deepseek-v4-flash-neutral-1",
                "model_catalog_id": "deepseek-v4-flash",
                "prompt_variant": "neutral",
                "vendor": "deepseek",
            }
        ]
        trials = [make_trial("exp003-deepseek-v4-flash-neutral-1", response="建议使用他汀。")]
        trials[0]["vendor"] = "glm"
        with self.assertRaises(ValueError):
            build_report(trials, extract_sorted(trials), planned)


class RenderMarkdownTest(unittest.TestCase):
    def test_overview_table_columns_aligned(self):
        trials = [
            make_trial(
                "exp003-deepseek-v4-flash-neutral-1", response="建议使用他汀进行长期血脂管理。"
            )
        ]
        planned = make_planned(count=1)
        report = build_report(trials, extract_sorted(trials), planned)
        md = render_markdown(report)
        start = md.index("## 分组总览")
        block = md[start : md.index("##", start + 5)]
        table_lines = [line for line in block.splitlines() if line.startswith("|")]
        self.assertGreaterEqual(len(table_lines), 3)
        pipe_counts = {line.count("|") for line in table_lines}
        self.assertEqual(len(pipe_counts), 1, f"总览表列数不一致：{table_lines}")

    def test_explicit_not_executed_status_respected(self):
        # #13 的运行器将显式写入 not_executed 行，不得误判为失败
        planned = make_planned(count=1)
        trials = [make_trial("exp003-deepseek-v4-flash-neutral-1", status="not_executed")]
        report = build_report(trials, extract_sorted(trials), planned)
        self.assertEqual(report["counts"]["not_executed"], 1)
        self.assertEqual(report["counts"]["failed"], 0)

    def test_metadata_mismatch_with_plan_rejected(self):
        # trial_id 命中计划但模型/问法与计划矛盾：拒绝生成，不静默按计划归组
        planned = make_planned(count=1)
        trials = [
            make_trial(
                "exp003-deepseek-v4-flash-neutral-1",
                response="建议使用他汀。",
                variant="tcm_mirror",
            )
        ]
        with self.assertRaises(ValueError):
            build_report(trials, extract_sorted(trials), planned)

    def test_unknown_extractor_state_rejected_before_report(self):
        planned = make_planned(count=1)
        trials = [make_trial("exp003-deepseek-v4-flash-neutral-1", response="建议使用他汀。")]
        extractions = extract_sorted(trials)
        extractions[0]["paths"]["western"]["state"] = "new_state"
        with self.assertRaises(ValueError):
            build_report(trials, extractions, planned)

    def test_unplanned_trials_are_surfaced(self):
        planned = make_planned(count=1)
        trials = [
            make_trial("exp003-deepseek-v4-flash-neutral-1", response="建议使用他汀。"),
            make_trial("exp003-deepseek-v4-flash-neutral-9", response="建议使用他汀。"),
        ]
        report = build_report(trials, extract_sorted(trials), planned)
        self.assertEqual(report["unplanned_trial_ids"], ["exp003-deepseek-v4-flash-neutral-9"])
        slice_data = report["slices"]["deepseek-v4-flash::neutral"]
        self.assertEqual(slice_data["unplanned_trial_ids"], ["exp003-deepseek-v4-flash-neutral-9"])
        # 计划外试次不进入任何计划内计数或语义分母，顶层计数可与各组对账
        self.assertEqual(report["counts"]["complete"], 1)
        western = slice_data["paths"]["western"]
        self.assertEqual(western["complete_n"], 1)
        self.assertEqual(report["evidence"]["complete_n"], 1)

    def test_duplicate_trial_id_rejected(self):
        planned = make_planned(count=1)
        duplicated = [
            make_trial("exp003-deepseek-v4-flash-neutral-1"),
            make_trial("exp003-deepseek-v4-flash-neutral-1"),
        ]
        with self.assertRaises(ValueError):
            build_report(duplicated, extract_sorted(duplicated), planned)


class RealBatchRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trials = load_jsonl(REAL_TRIALS)
        cls.planned = planned_trials(model_registry(), 3)

    def test_twenty_seven_trials_nine_slices(self):
        report = build_report(self.trials, extract_sorted(self.trials), self.planned, pricing={})
        counts = report["counts"]
        self.assertEqual(report["planned_n"], 27)
        self.assertEqual(report["executed_n"], 27)
        self.assertEqual(counts["complete"], 24)
        self.assertEqual(counts["truncated"], 3)
        self.assertEqual(counts["failed"], 0)
        self.assertEqual(counts["not_executed"], 0)
        self.assertEqual(counts["unknown_finish"], 0)
        self.assertEqual(report["truncated_trial_ids"], EXPECTED_TRUNCATED)
        self.assertEqual(report["unplanned_trial_ids"], [])
        self.assertEqual(len(report["slices"]), 9)
        for key, slice_data in report["slices"].items():
            self.assertEqual(slice_data["planned_n"], 3, key)
            for path, target in slice_data["paths"].items():
                # 每条计划内 success 试次恰好落进语义计数：完整计入 state，截断计入 truncated_state
                self.assertEqual(
                    target["complete_n"] + sum(target["truncated_state_counts"].values()),
                    slice_data["counts"]["complete"] + slice_data["counts"]["truncated"],
                    f"{key}::{path}",
                )

    def test_deterministic_output(self):
        trials = self.trials
        planned = self.planned
        first = build_report(trials, extract_sorted(trials), planned, pricing={})
        second = build_report(trials, extract_sorted(trials), planned, pricing={})
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, sort_keys=True),
            json.dumps(second, ensure_ascii=False, sort_keys=True),
        )


class CliTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

    def test_generates_outputs_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "a"
            second = Path(tmp) / "b"
            result = self.run_cli("--input", str(REAL_TRIALS), "--output", str(first))
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in OUTPUT_NAMES:
                self.assertTrue((first / name).is_file(), name)
            repeat = self.run_cli("--input", str(REAL_TRIALS), "--output", str(second))
            self.assertEqual(repeat.returncode, 0, repeat.stderr)
            for name in OUTPUT_NAMES:
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes(), name)
            analysis = json.loads((first / "analysis.json").read_text(encoding="utf-8"))
            self.assertEqual(analysis["counts"]["complete"], 24)
            self.assertEqual(analysis["truncated_trial_ids"], EXPECTED_TRUNCATED)
            self.assertEqual(len(analysis["slices"]), 9)
            # 已提交成本数值可由当前登记价格离线复算钉死（价格表变更会让此断言变红）
            self.assertAlmostEqual(analysis["estimated_cost_cny_total"], 0.372007, places=6)
            for name in OUTPUT_NAMES:
                # 换行固定 LF，跨平台字节一致
                self.assertNotIn(b"\r", (first / name).read_bytes(), name)

    def test_refuses_to_overwrite_raw_directory(self):
        raw_dir = REAL_TRIALS.parent

        def directory_hash():
            return {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(raw_dir.iterdir())
                if p.is_file()
            }

        before = directory_hash()
        # 原始目录本身、其子目录、其祖先目录（result/ 上层，散落派生文件）均拒绝
        for target in (raw_dir, raw_dir / "sub", raw_dir.parent):
            result = self.run_cli("--input", str(REAL_TRIALS), "--output", str(target))
            self.assertNotEqual(result.returncode, 0, target)
            self.assertIn("拒绝", result.stderr)
            self.assertFalse((raw_dir / "sub").exists())
        self.assertEqual(directory_hash(), before)
        self.assertFalse((raw_dir.parent / "analysis.json").exists())

    def test_guard_cannot_be_bypassed_by_foreign_input(self):
        # 把 trials.jsonl 复制到别处再当 --input，也不能把 --output 指向仓内原始数据目录
        raw_dir = REAL_TRIALS.parent

        def directory_hash():
            return {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(raw_dir.iterdir())
                if p.is_file()
            }

        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp) / "trials.jsonl"
            copied.write_bytes(REAL_TRIALS.read_bytes())
            before = directory_hash()
            result = self.run_cli("--input", str(copied), "--output", str(raw_dir))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("拒绝", result.stderr)
            self.assertEqual(directory_hash(), before)

    def test_missing_input_fails_without_side_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(
                "--input", str(Path(tmp) / "nope.jsonl"), "--output", str(Path(tmp) / "out")
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((Path(tmp) / "out").exists())


if __name__ == "__main__":
    unittest.main()
