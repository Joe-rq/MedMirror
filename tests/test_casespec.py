"""CaseSpec 加载与 schema 校验测试（issue #50）。

合规样本逐字节等于仓库默认配置；各拒绝路径（缺文件、坏 JSON、未知键、
版本不匹配、trial_prefix 非法、空词表）逐一覆盖——第三方配置宁报错勿默吞。
"""

import json
import tempfile
import unittest
from pathlib import Path

from medmirror.casespec import (
    DEFAULT_CASE_ID,
    default_case_path,
    load_case_spec,
    load_default_case,
)
from medmirror.protocol import EXTRACTOR_VERSION, extract_trial
from medmirror.runner import CASE_ID, CASE_TEXT, PROTOCOL_VERSION, VARIANTS


def valid_payload() -> dict:
    return {
        "case_id": "demo_case_001",
        "protocol_version": "demo-v1",
        "trial_prefix": "demo",
        "case_text": "示例病例文本",
        "synthetic": True,
        "variants": {"neutral": "示例病例文本"},
        "extraction": {
            "extractor_version": EXTRACTOR_VERSION,
            "paths": {"western": ["西医"]},
        },
        "notes": "测试样本（合成）",
    }


def write_payload(payload: dict) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", encoding="utf-8", delete=False
    ) as tmp:
        json.dump(payload, tmp, ensure_ascii=False)
    return Path(tmp.name)


class DefaultCaseSpecTest(unittest.TestCase):
    def test_default_case_matches_runner_constants(self):
        """默认配置逐字节等于改造前的代码常量（零语义漂移的配置侧证明）。"""
        spec = load_default_case(supported_extractor_version=EXTRACTOR_VERSION)
        self.assertEqual(spec.case_id, CASE_ID)
        self.assertEqual(spec.protocol_version, PROTOCOL_VERSION)
        self.assertEqual(spec.case_text, CASE_TEXT)
        self.assertEqual(spec.variants, VARIANTS)
        self.assertEqual(spec.extractor_version, EXTRACTOR_VERSION)

    def test_default_case_path_resolution(self):
        path = default_case_path()
        self.assertEqual(path.name, f"{DEFAULT_CASE_ID}.json")
        self.assertEqual(path.parent.name, "cases")
        self.assertTrue(path.exists())


class LoadCaseSpecTest(unittest.TestCase):
    def load(self, payload: dict):
        path = write_payload(payload)
        self.addCleanup(path.unlink)
        return load_case_spec(path, supported_extractor_version=EXTRACTOR_VERSION)

    def test_valid_payload_round_trip(self):
        spec = self.load(valid_payload())
        self.assertEqual(spec.case_id, "demo_case_001")
        self.assertEqual(spec.trial_prefix, "demo")
        self.assertEqual(spec.extraction_paths, {"western": ["西医"]})
        snapshot = spec.as_dict()
        self.assertEqual(snapshot, valid_payload())

    def test_missing_file_names_path_and_fix(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            load_case_spec(
                Path("/nonexistent/case.json"), supported_extractor_version=EXTRACTOR_VERSION
            )
        self.assertIn("/nonexistent/case.json", str(ctx.exception))
        self.assertIn("configs/cases/", str(ctx.exception))

    def test_invalid_json_rejected(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as tmp:
            tmp.write("{not json")
        path = Path(tmp.name)
        self.addCleanup(path.unlink)
        with self.assertRaises(ValueError):
            load_case_spec(path, supported_extractor_version=EXTRACTOR_VERSION)

    def test_unknown_top_level_key_rejected(self):
        payload = {**valid_payload(), "surprise": 1}
        with self.assertRaisesRegex(ValueError, "未知顶层键.*surprise"):
            self.load(payload)

    def test_unknown_extraction_key_rejected(self):
        payload = valid_payload()
        payload["extraction"] = {**payload["extraction"], "extra": True}
        with self.assertRaisesRegex(ValueError, "extraction 含未知键.*extra"):
            self.load(payload)

    def test_extractor_version_mismatch_rejected(self):
        payload = valid_payload()
        payload["extraction"]["extractor_version"] = "offline-rules-v1"
        with self.assertRaisesRegex(ValueError, "offline-rules-v1.*offline-rules-v2"):
            self.load(payload)

    def test_synthetic_field_required_and_must_be_true(self):
        """intent.md 红线机械把关：synthetic 缺失或为假即拒绝（显式布尔，不可被否定表述绕过）。"""
        for bad in (None, False, "true", 1):
            payload = {**valid_payload(), "synthetic": bad}
            with self.assertRaisesRegex(ValueError, "synthetic"):
                self.load(payload)
        payload = valid_payload()
        payload.pop("synthetic")
        with self.assertRaisesRegex(ValueError, "synthetic"):
            self.load(payload)

    def test_duplicate_json_keys_rejected(self):
        """重复键会被 json 静默取后值（评审 P2），必须显式拒绝。"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as tmp:
            tmp.write('{"case_id": "a", "case_id": "b"}')
        path = Path(tmp.name)
        self.addCleanup(path.unlink)
        with self.assertRaisesRegex(ValueError, "重复键.*case_id"):
            load_case_spec(path, supported_extractor_version=EXTRACTOR_VERSION)

    def test_unsafe_variant_name_rejected(self):
        """变体名进 trial_id 与报告（评审 P2）：控制字符与 | 破坏结构，拒绝。"""
        for bad in ("neu\ntral", "a|b"):
            payload = {**valid_payload(), "variants": {bad: "示例病例文本"}}
            with self.assertRaisesRegex(ValueError, "variants"):
                self.load(payload)

    def test_unsafe_path_name_rejected(self):
        payload = valid_payload()
        payload["extraction"]["paths"] = {"west\nern": ["西医"]}
        with self.assertRaisesRegex(ValueError, "paths 键"):
            self.load(payload)

    def test_missing_required_field_rejected(self):
        for key in ("case_id", "protocol_version", "trial_prefix", "case_text", "notes"):
            payload = valid_payload()
            payload.pop(key)
            with self.assertRaisesRegex(ValueError, key):
                self.load(payload)

    def test_blank_required_field_rejected(self):
        payload = {**valid_payload(), "case_id": "   "}
        with self.assertRaisesRegex(ValueError, "case_id"):
            self.load(payload)

    def test_bad_trial_prefix_rejected(self):
        for bad in ("Exp003", "exp 003", "-exp", "exp/003", "", "exp003\n"):
            payload = {**valid_payload(), "trial_prefix": bad}
            with self.assertRaisesRegex(ValueError, "trial_prefix"):
                self.load(payload)

    def test_empty_variants_rejected(self):
        payload = {**valid_payload(), "variants": {}}
        with self.assertRaisesRegex(ValueError, "variants"):
            self.load(payload)

    def test_blank_variant_prompt_rejected(self):
        payload = {**valid_payload(), "variants": {"neutral": "  "}}
        with self.assertRaisesRegex(ValueError, "neutral"):
            self.load(payload)

    def test_empty_paths_rejected(self):
        payload = valid_payload()
        payload["extraction"]["paths"] = {}
        with self.assertRaisesRegex(ValueError, "paths"):
            self.load(payload)

    def test_empty_term_list_rejected(self):
        payload = valid_payload()
        payload["extraction"]["paths"] = {"western": []}
        with self.assertRaisesRegex(ValueError, "western"):
            self.load(payload)

    def test_blank_term_rejected(self):
        payload = valid_payload()
        payload["extraction"]["paths"] = {"western": ["西医", ""]}
        with self.assertRaisesRegex(ValueError, "western"):
            self.load(payload)

    def test_whitespace_term_rejected(self):
        """空白词项会命中任意含空格文本（评审 P2），必须拒绝。"""
        payload = valid_payload()
        payload["extraction"]["paths"] = {"western": [" "]}
        with self.assertRaisesRegex(ValueError, "空白或空词项"):
            self.load(payload)


class VocabularyThreadingTest(unittest.TestCase):
    """自定义词表全链路穿参（评审 P1：关系归属不能仍读默认词表）。

    用全新路径族（不含默认词表任何词项）验证替代/辅助/自服否定三类关系分析
    对自定义词表生效——否则新病例词表形同虚设（「只抽病例不抽词表」红线）。
    """

    CUSTOM_PATHS = {"therapy_x": ["X 药", "X药"], "standard_y": ["Y 疗法"]}

    def extract(self, response: str) -> dict:
        return extract_trial(
            {"trial_id": "t-custom-1", "status": "success", "response": response},
            paths=self.CUSTOM_PATHS,
        )

    def test_custom_vocab_mention_and_direct_attitude(self):
        result = self.extract("可以考虑 X 药治疗。")
        self.assertTrue(result["paths"]["therapy_x"]["mentioned"])
        self.assertEqual(result["paths"]["therapy_x"]["state"], "conditional_support")

    def test_custom_vocab_substitution_relation(self):
        result = self.extract("不建议用 X 药替代 Y 疗法。")
        self.assertEqual(result["paths"]["therapy_x"]["substitution"], "opposed")
        self.assertEqual(result["paths"]["standard_y"]["substitution"], None)

    def test_custom_vocab_adjunct_relation(self):
        result = self.extract("在 Y 疗法基础上可以联合使用 X 药。")
        self.assertEqual(result["paths"]["therapy_x"]["adjunct"], "conditional_support")
        self.assertEqual(result["paths"]["standard_y"]["adjunct"], None)

    def test_custom_vocab_self_admin_needs_review(self):
        result = self.extract("不建议自行加用 X 药，请与医生沟通后决定。")
        self.assertEqual(result["paths"]["therapy_x"]["state"], "needs_review")

    def test_default_vocab_not_leaked_into_custom_extraction(self):
        """自定义词表提取时，默认词表的路径不得出现（防全局词表混入）。"""
        result = self.extract("可以考虑 X 药治疗，也谈谈中医。")
        self.assertEqual(set(result["paths"]), set(self.CUSTOM_PATHS))


class VocabRegistryTest(unittest.TestCase):
    """同版本词表不可变闸（评审 P1）：cases 目录内配置受 vocab-registry 约束。"""

    def _write_in_cases_dir(self, payload: dict) -> Path:
        target = default_case_path().parent / f"zzz_test_{abs(id(payload)) % 10000}.json"
        target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self.addCleanup(target.unlink)
        return target

    def test_unregistered_version_triple_rejected(self):
        payload = {**valid_payload(), "case_id": "unregistered_case"}
        path = self._write_in_cases_dir(payload)
        with self.assertRaisesRegex(ValueError, "未在.*登记"):
            load_case_spec(path, supported_extractor_version=EXTRACTOR_VERSION)

    def test_registered_triple_with_changed_vocab_rejected(self):
        """同版本改词表（登记摘要不一致）拒绝——「改词表=新版本号」红线的机械闸。"""
        payload = json.loads(default_case_path().read_text(encoding="utf-8"))
        payload["extraction"]["paths"]["western"] = ["西医", "新词"]
        path = self._write_in_cases_dir(payload)
        with self.assertRaisesRegex(ValueError, "词表与登记摘要不一致"):
            load_case_spec(path, supported_extractor_version=EXTRACTOR_VERSION)

    def test_registered_default_case_loads(self):
        spec = load_default_case(supported_extractor_version=EXTRACTOR_VERSION)
        self.assertTrue(spec.synthetic)

    def test_outside_cases_dir_skips_registry(self):
        """目录外第三方路径不受登记约束（自理纪律），合法样本可直接加载。"""
        path = write_payload(valid_payload())
        self.addCleanup(path.unlink)
        spec = load_case_spec(path, supported_extractor_version=EXTRACTOR_VERSION)
        self.assertEqual(spec.case_id, "demo_case_001")


if __name__ == "__main__":
    unittest.main()
