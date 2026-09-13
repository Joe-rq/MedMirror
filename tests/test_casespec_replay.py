"""exp003 字节一致重放验收（issue #50）。

对比对象是历史真实产物 `docs/experiments/exp003-baseline/result/trials.jsonl`
（27 条，冻结），不是新 plan 自比：默认 CaseSpec 经 planned_trials 生成的计划，
其请求字段须与历史逐字段一致——这是「协议事实抽为配置零语义漂移」的机器证明。

口径说明（triage D1/D8/M2）：
- 历史行无 endpoint 字段（pre-#13 执行器不存）：endpoint 改与「同一 models.json
  目录默认值派生的 registry」逐一相等（端点解析路径本次零改动，属自洽证明）；
- registry 由 load_catalog 直建（不经 env），锁定「历史按目录默认值发出」的事实
  （历史 27 行 model == catalog id 亦在测试内复核），避免本机 env 覆盖造成假红；
- variants 独立锚：直接从 CaseSpec 文件读值断言逐字节 ∈ 历史 messages，不经
  runner 派生常量，防止「拿派生值自证」。
"""

import hashlib
import json
import unittest
from pathlib import Path

from medmirror.casespec import default_case_path, load_case_spec
from medmirror.protocol import EXTRACTOR_VERSION, PATH_PATTERNS
from medmirror.providers import ModelConfig, load_catalog
from medmirror.runner import planned_trials

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_TRIALS = ROOT / "docs/experiments/exp003-baseline/result/trials.jsonl"

# 验收第 4 条：这三处不许再出现硬编码病例常量（防模板化后引用回流）
NO_CASE_CONSTANT_FILES = (
    ROOT / "src/medmirror/reporting.py",
    ROOT / "scripts/report_exp003.py",
    ROOT / "scripts/run_exp003_baseline.py",
)
CASE_CONSTANT_TOKENS = ("CASE_ID", "CASE_TEXT", "VARIANTS", "carotid_plaque_001")


def catalog_default_registry() -> dict[str, ModelConfig]:
    """按 models.json 默认值直建 registry（不加载 env，不做任何覆盖）。"""
    registry: dict[str, ModelConfig] = {}
    for item in load_catalog()["models"]:
        registry[item["id"]] = ModelConfig(
            model_id=item["id"],
            vendor=item["vendor"],
            base_url=item["base_url"],
            api_key_env=item["api_key_env"],
            api_style=item["api_style"],
            confirmed=bool(item["confirmed"]),
            price_status=item["price_status"],
        )
    return registry


def historical_rows() -> list[dict]:
    with HISTORICAL_TRIALS.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class ReplayAgainstHistoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = historical_rows()
        cls.registry = catalog_default_registry()
        cls.spec = load_case_spec(
            default_case_path(), supported_extractor_version=EXTRACTOR_VERSION
        )
        cls.planned = planned_trials(cls.registry, repeats=3)

    def test_history_shape(self):
        """历史基准自检：27 行、model==catalog id（无 env 覆盖）、单角色消息。"""
        self.assertEqual(len(self.history), 27)
        for row in self.history:
            self.assertEqual(row["model"], row["model_catalog_id"])
            self.assertEqual([m["role"] for m in row["messages"]], ["user"])

    def test_trial_id_sets_identical(self):
        self.assertEqual(
            {spec["trial_id"] for spec in self.planned},
            {row["trial_id"] for row in self.history},
        )

    def test_request_fields_identical_per_trial(self):
        """请求字段逐字段一致：messages 逐字节、元数据逐项相等。"""
        by_id = {row["trial_id"]: row for row in self.history}
        for spec in self.planned:
            row = by_id[spec["trial_id"]]
            self.assertEqual(spec["messages"], row["messages"], spec["trial_id"])
            self.assertEqual(spec["model_catalog_id"], row["model_catalog_id"])
            self.assertEqual(spec["model"], row["model"])
            self.assertEqual(spec["vendor"], row["vendor"])
            self.assertEqual(spec["prompt_variant"], row["prompt_variant"])
            self.assertEqual(spec["trial_index"], row["trial_index"])

    def test_case_spec_anchored_to_history_not_derived(self):
        """独立锚：CaseSpec 文件里的变体与版本钉子直接对历史本体断言。"""
        historical_messages = {m["content"] for row in self.history for m in row["messages"]}
        for variant, prompt in self.spec.variants.items():
            self.assertIn(prompt, historical_messages, f"variant {variant} 未逐字节命中历史")
        for row in self.history:
            self.assertEqual(row["protocol_version"], self.spec.protocol_version)
            self.assertEqual(row["case_id"], self.spec.case_id)

    def test_endpoint_set_matches_catalog_derivation(self):
        """endpoint 集合与 models.json 派生值逐一相等（历史不存该字段，口径见模块注释）。"""
        registry_endpoints = {
            catalog_id: config.endpoint for catalog_id, config in self.registry.items()
        }
        for spec in self.planned:
            self.assertEqual(
                spec["endpoint"], registry_endpoints[spec["model_catalog_id"]], spec["trial_id"]
            )

    def test_vocabulary_migration_byte_identical(self):
        """词表迁出零漂移：CaseSpec 词表 == protocol.PATH_PATTERNS 注入值。"""
        self.assertEqual(self.spec.extraction_paths, PATH_PATTERNS)

    def test_history_file_untouched_by_replay(self):
        """重放只读：历史文件在测试前后字节不变。"""
        before = hashlib.sha256(HISTORICAL_TRIALS.read_bytes()).hexdigest()
        self.assertEqual(len(historical_rows()), 27)
        after = hashlib.sha256(HISTORICAL_TRIALS.read_bytes()).hexdigest()
        self.assertEqual(before, after)


class NoCaseConstantRegressionTest(unittest.TestCase):
    def test_reporting_and_clis_free_of_case_constants(self):
        """验收第 4 条：reporting / report_exp003 / run_exp003_baseline 无病例常量引用。"""
        for path in NO_CASE_CONSTANT_FILES:
            source = path.read_text(encoding="utf-8")
            for token in CASE_CONSTANT_TOKENS:
                self.assertNotIn(
                    token, source, f"{path.name} 含病例常量引用 {token!r}（应改由 CaseSpec 驱动）"
                )


if __name__ == "__main__":
    unittest.main()
