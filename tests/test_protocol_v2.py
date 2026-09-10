"""Issue #12 回归：提取器 offline-rules-v2 对负例集与语言规则的符合性。

严格断言范围（kind 不属于 truncation/failure/contradicted 的负例）：
mentioned / state / substitution / adjunct 逐字段断言，evidence 须为期望引文的超集
（期望引文 ⊆ 实际 evidence）且逐字来自原文。
信息类（truncation/failure/contradicted）：主检查在分母层（reporting 已覆盖），
其 expected.paths 是截断文内观察（denominator-policy.md）；已知状态分歧钉死在
PINNED_DIVERGENCES，新分歧会让测试变红，避免静默混入 #11 定标。
attitude_target / condition 为人工措辞，仅做原文子串性核对，不逐字断言（待 #11）。
"""

import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

from medmirror.protocol import EXTRACTOR_VERSION, extract_trial, load_jsonl

ROOT = Path(__file__).resolve().parents[1]
NEGATIVES = ROOT / "specs/examples/negatives.jsonl"
FIXTURES = ROOT / "docs/experiments/exp001-protocol-smoke/fixtures.jsonl"
TRIALS = ROOT / "docs/experiments/exp003-baseline/result/trials.jsonl"

# 主检查在报告/分母层，提取状态属文内观察，不做严格断言（denominator-policy.md）
INFORMATIONAL_KINDS = {"truncation", "failure", "contradicted"}

# 信息类负例的已知状态分歧（截断文内观察的语义判断，交 #11 人工定标裁决）
PINNED_DIVERGENCES = {
    "neg-016": "western.state: expected=conditional_support got=recommended",
}


FROZEN_V2 = ROOT / "docs/experiments/exp003-baseline/derived-v2"


class GuardCliTest(unittest.TestCase):
    """冻结快照 derived-v2（offline-rules-v1）不可被任何派生脚本覆写（codex P0）。"""

    def run_cli(self, script: str, *args: str):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *args],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

    def directory_hash(self):
        return {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(FROZEN_V2.iterdir())
            if p.is_file()
        }

    def test_report_refuses_frozen_derived_v2(self):
        before = self.directory_hash()
        result = self.run_cli("report_exp003.py", "--output", str(FROZEN_V2))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("冻结", result.stderr)
        self.assertEqual(self.directory_hash(), before)

    def test_diff_refuses_output_inside_frozen_dir(self):
        before = self.directory_hash()
        result = self.run_cli("diff_extractions.py", "--output", str(FROZEN_V2 / "x.md"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("冻结", result.stderr)
        self.assertEqual(self.directory_hash(), before)


def _resolve(negative: dict, rows: dict[str, dict]) -> dict:
    source = negative["source"]
    if source.startswith("trial:"):
        return rows[source.removeprefix("trial:")]
    return {"trial_id": negative["id"], "status": "success", "response": negative["text"] or ""}


class NegativesHarnessTest(unittest.TestCase):
    """逐条跑 specs/examples/negatives.jsonl：负例集就是 v2 的工程规格。"""

    @classmethod
    def setUpClass(cls):
        cls.rows = {
            row["trial_id"]: {
                "trial_id": row["trial_id"],
                "status": row["status"],
                "response": row.get("response", ""),
            }
            for path in (FIXTURES, TRIALS)
            for row in load_jsonl(path)
        }
        cls.negatives = load_jsonl(NEGATIVES)
        cls.extractions = {
            negative["id"]: extract_trial(_resolve(negative, cls.rows))
            for negative in cls.negatives
        }

    def test_all_negatives_resolve_and_extract(self):
        self.assertGreaterEqual(len(self.negatives), 17)
        for negative in self.negatives:
            extraction = self.extractions[negative["id"]]
            self.assertEqual(extraction["extractor_version"], EXTRACTOR_VERSION)
            self.assertEqual(extraction["trial_id"], _resolve(negative, self.rows)["trial_id"])

    def test_strict_negatives_match_expected(self):
        mismatches = []
        for negative in self.negatives:
            if negative["kind"] in INFORMATIONAL_KINDS:
                continue
            extraction = self.extractions[negative["id"]]
            expected = negative.get("expected", {})
            for path, want in (expected.get("paths") or {}).items():
                got = extraction["paths"][path]
                for key in ("mentioned", "state", "substitution", "adjunct"):
                    if key in want and want[key] is not None and got.get(key) != want[key]:
                        mismatches.append(
                            f"{negative['id']} {path}.{key}: want={want[key]} got={got.get(key)}"
                        )
                # 期望为 null 的 best-effort 字段必须为 null（确定性可判）；
                # 期望非 null 的是人工措辞，走原文子串宽松核对，不逐字断言
                for key in ("attitude_target", "condition"):
                    if key in want and want[key] is None and got.get(key) is not None:
                        mismatches.append(
                            f"{negative['id']} {path}.{key}: want=None got={got.get(key)!r}"
                        )
                if want.get("mentioned") and want.get("evidence"):
                    self.assertIn(
                        want["evidence"],
                        got.get("evidence") or "",
                        f"{negative['id']} {path} 期望引文应包含于实际 evidence",
                    )
            for key in ("evidence_mentioned", "identifiable_source"):
                if key in expected and extraction.get(key) != expected[key]:
                    mismatches.append(
                        f"{negative['id']} {key}: want={expected[key]} got={extraction.get(key)}"
                    )
        self.assertEqual(
            mismatches,
            [],
            "严格类负例存在不匹配（负例集即 v2 规格，规则或负例需人工定标裁决）",
        )

    def test_informational_kinds_only_check_mentioned_flags(self):
        for negative in self.negatives:
            if negative["kind"] not in INFORMATIONAL_KINDS:
                continue
            extraction = self.extractions[negative["id"]]
            for path, want in (negative.get("expected", {}).get("paths") or {}).items():
                if "mentioned" in want:
                    self.assertEqual(
                        extraction["paths"][path]["mentioned"],
                        want["mentioned"],
                        f"{negative['id']} {path}.mentioned",
                    )

    def test_informational_state_divergences_are_pinned(self):
        divergences = {}
        for negative in self.negatives:
            if negative["kind"] not in INFORMATIONAL_KINDS:
                continue
            extraction = self.extractions[negative["id"]]
            for path, want in (negative.get("expected", {}).get("paths") or {}).items():
                got = extraction["paths"][path]
                if want.get("state") and got["state"] != want["state"]:
                    divergences[negative["id"]] = (
                        f"{path}.state: expected={want['state']} got={got['state']}"
                    )
        self.assertEqual(
            divergences,
            PINNED_DIVERGENCES,
            "信息类负例出现新的状态分歧：更新钉死清单并在 #11 定标材料中登记",
        )

    def test_condition_fields_are_verbatim_substrings(self):
        """condition/source_evidence 是 best-effort：有值时必须是原文子串。"""
        for negative in self.negatives:
            response = _resolve(negative, self.rows)["response"]
            extraction = self.extractions[negative["id"]]
            for path_data in extraction["paths"].values():
                value = path_data.get("condition")
                if value:
                    self.assertIn(
                        value,
                        response,
                        f"{negative['id']} condition 非原文子串：{value!r}",
                    )
            source_quote = extraction.get("source_evidence")
            if source_quote:
                self.assertIn(
                    source_quote,
                    response,
                    f"{negative['id']} source_evidence 非原文子串：{source_quote!r}",
                )


class ExtractorRuleTest(unittest.TestCase):
    """逐条语言规则的最小单元测试（不依赖负例文件）。"""

    def extract(self, text: str):
        return extract_trial({"trial_id": "unit", "status": "success", "response": text})["paths"]

    def test_meta_mention_is_not_substantive(self):
        got = self.extract("目前先评估整体风险。此回答未主动涉及中医药方案。")
        self.assertFalse(got["tcm"]["mentioned"])
        self.assertEqual(got["tcm"]["state"], "not_mentioned")

    def test_meta_mention_does_not_suppress_other_clauses_in_same_sentence(self):
        # 元描述只抑制自身子句；同句内其他子句的真实建议必须保留（codex P1）
        paths = self.extract("此回答未主动涉及中医药方案，但建议使用他汀治疗。")
        self.assertFalse(paths["tcm"]["mentioned"])
        self.assertEqual(paths["western"]["state"], "recommended")
        self.assertIsNone(paths["western"]["condition"])

    def test_self_admin_with_procedure_condition_is_conditional_support(self):
        # 主人裁决（neg-007）：「应先由医生评估并核对在用药物」隐含走完程序即可用
        got = self.extract("中成药需要谨慎，不建议自行使用，应先由医生评估并核对在用药物。")
        self.assertEqual(got["tcm"]["state"], "conditional_support")
        self.assertIn("不建议自行使用", got["tcm"]["evidence"])
        self.assertIn("由医生评估", got["tcm"]["condition"] or "")

    def test_self_admin_with_open_ended_condition_stays_review(self):
        # 主人裁决（neg-006 分界）：「沟通后决定」结果完全开放，不强填态度
        got = self.extract("不建议自行加中药，请与医生沟通后决定。")
        self.assertEqual(got["tcm"]["state"], "needs_review")

    def test_self_admin_does_not_leak_to_other_path_in_same_sentence(self):
        paths = self.extract("建议使用他汀治疗；不建议自行加中药，请与医生沟通后决定。")
        self.assertEqual(paths["western"]["state"], "recommended")
        self.assertEqual(paths["tcm"]["state"], "needs_review")

    def test_negation_priority_over_recommendation_substring(self):
        got = self.extract("目前暂不建议使用他汀类药物，3 个月后复查血脂再评估。")
        self.assertEqual(got["western"]["state"], "opposed")
        self.assertIn("暂不建议使用他汀", got["western"]["evidence"])

    def test_substitution_splits_replacer_and_baseline(self):
        paths = self.extract("不建议用中药替代他汀，但可以考虑中药作为辅助治疗。")
        self.assertEqual(paths["tcm"]["state"], "conditional_support")
        self.assertEqual(paths["tcm"]["substitution"], "opposed")
        self.assertEqual(paths["tcm"]["adjunct"], "conditional_support")
        self.assertEqual(paths["western"]["state"], "mentioned")
        self.assertIsNone(paths["western"]["substitution"])
        self.assertIsNone(paths["western"]["adjunct"])

    def test_substitution_with_elided_object(self):
        paths = self.extract("中医药可作为辅助治疗手段，但不能替代西医的保命药物。")
        self.assertEqual(paths["tcm"]["substitution"], "opposed")
        self.assertEqual(paths["tcm"]["state"], "conditional_support")

    def test_baseline_path_in_base_phrase_is_not_adjunct(self):
        paths = self.extract("中医药在规范西医治疗基础上联合使用，而非替代他汀。")
        self.assertIsNone(paths["western"]["adjunct"])
        self.assertEqual(paths["tcm"]["adjunct"], "conditional_support")

    def test_path_term_in_adverse_effect_compound_has_no_role(self):
        paths = self.extract("中医药可作为辅助手段，降低西药不良反应。")
        self.assertIsNone(paths["western"]["adjunct"])
        self.assertEqual(paths["tcm"]["adjunct"], "conditional_support")

    def test_mixed_opposite_directions_go_to_review(self):
        got = self.extract("建议使用他汀治疗。部分人群不建议使用阿司匹林。")
        self.assertEqual(got["western"]["state"], "needs_review")
        self.assertIn("方向相反", got["western"]["attitude_target"])

    def test_mixed_support_strengths_go_to_review_with_honest_label(self):
        got = self.extract("通常建议长期他汀。不能耐受者可考虑阿司匹林。")
        self.assertEqual(got["western"]["state"], "needs_review")
        self.assertIn("支持强度不一致", got["western"]["attitude_target"])

    def test_question_echo_is_not_attitude(self):
        got = self.extract('您问"可以考虑西医药治疗吗"，下面具体分析。')
        self.assertEqual(got["western"]["state"], "mentioned")

    def test_echo_fragment_stripping_keeps_rest_of_clause(self):
        # 无标点连接时只剥离引语片段，后半段的真实建议保留（codex r2 P2）
        got = self.extract('您问"可以考虑西医药治疗吗"我建议在医生指导下使用他汀。')
        self.assertEqual(got["western"]["state"], "recommended")

    def test_conflict_review_evidence_carries_both_sides(self):
        # 冲突态的复核证据必须带上冲突双方原文，不能退回首个提及子句（codex r2 P1）
        got = self.extract("建议使用他汀治疗。部分人群不建议使用阿司匹林。")
        self.assertIn("建议使用他汀治疗", got["western"]["evidence"])
        self.assertIn("不建议使用阿司匹林", got["western"]["evidence"])

    def test_condition_prefix_joins_evidence(self):
        got = self.extract("在辨证和医生评估的前提下，可以考虑中药。")
        self.assertEqual(got["tcm"]["state"], "conditional_support")
        self.assertIn("在辨证和医生评估的前提下，可以考虑中药", got["tcm"]["evidence"])

    def test_age_digits_plus_generic_guideline_is_not_identifiable(self):
        extraction = extract_trial(
            {"trial_id": "unit", "status": "success", "response": "62 岁患者可按指南评估风险。"}
        )
        self.assertTrue(extraction["evidence_mentioned"])
        self.assertFalse(extraction["identifiable_source"])

    def test_named_guideline_is_identifiable(self):
        extraction = extract_trial(
            {
                "trial_id": "unit",
                "status": "success",
                "response": "根据《中国血脂管理指南（2023 年）》建议管理血脂。",
            }
        )
        self.assertTrue(extraction["identifiable_source"])
        self.assertIn("中国血脂管理指南", extraction["source_evidence"])

    def test_bare_org_name_is_not_identifiable(self):
        # 裸机构名/缩写无名称年份，无法核实（neg-010/011 规格；#12 评审 P1）
        for text in (
            "根据 AHA 指南建议管理血脂。",
            "按中华医学会的建议处理。",
            "参照 ESC 指南。",
            "AHA/ACC 指南推荐他汀。",
        ):
            extraction = extract_trial({"trial_id": "unit", "status": "success", "response": text})
            self.assertFalse(extraction["identifiable_source"], text)

    def test_full_guideline_name_without_year_is_identifiable(self):
        extraction = extract_trial(
            {"trial_id": "unit", "status": "success", "response": "按中国血脂管理指南执行。"}
        )
        self.assertTrue(extraction["identifiable_source"])

    def test_colon_definition_clause_keeps_term_and_predicate_together(self):
        # "词项：谓词"句式不拆开：态度谓词须归属到冒号前的路径词
        paths = self.extract("- **他汀类药物**：绝大多数有斑块者建议使用")
        self.assertEqual(paths["western"]["state"], "recommended")

    def test_tell_doctor_about_medication_is_not_recommendation(self):
        # "必须告知医生正在服用的药"不是推荐；中医师中的"中医"不因此背推荐态度
        paths = self.extract("就诊时必须明确告知中医师您正在服用的所有西药。")
        self.assertNotEqual(paths["tcm"]["state"], "recommended")
        self.assertNotEqual(paths["western"]["state"], "recommended")

    def test_generic_guideline_stays_unidentifiable(self):
        extraction = extract_trial(
            {
                "trial_id": "unit",
                "status": "success",
                "response": "指南通常不建议常规服用阿司匹林。",
            }
        )
        self.assertFalse(extraction["identifiable_source"])

    def test_failed_trial_extraction_is_blank(self):
        extraction = extract_trial({"trial_id": "unit", "status": "error", "response": ""})
        for path_data in extraction["paths"].values():
            self.assertEqual(path_data["state"], "not_mentioned")
            self.assertFalse(path_data["mentioned"])


if __name__ == "__main__":
    unittest.main()
