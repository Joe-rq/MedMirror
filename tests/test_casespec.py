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
from medmirror.protocol import EXTRACTOR_VERSION
from medmirror.runner import CASE_ID, CASE_TEXT, PROTOCOL_VERSION, VARIANTS


def valid_payload() -> dict:
    return {
        "case_id": "demo_case_001",
        "protocol_version": "demo-v1",
        "trial_prefix": "demo",
        "case_text": "示例病例文本",
        "variants": {"neutral": "示例病例文本"},
        "extraction": {
            "extractor_version": EXTRACTOR_VERSION,
            "paths": {"western": ["西医"]},
        },
        "notes": "测试样本",
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
        for bad in ("Exp003", "exp 003", "-exp", "exp/003", ""):
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


if __name__ == "__main__":
    unittest.main()
