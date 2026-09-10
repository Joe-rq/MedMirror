import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEGATIVES = ROOT / "specs/examples/negatives.jsonl"
# issue #11 验收第 3 条点名必须覆盖的 kind，与脚本内 REQUIRED_KINDS 对齐
REQUIRED_KINDS = {
    "not_mentioned",
    "negation",
    "conditional_support",
    "object_crosstalk",
    "source_misidentification",
    "failure",
    "contradicted",
}


class CheckCalibrationTest(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "scripts/check_calibration.py", *args],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

    def test_repo_negatives_pass(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("全绿", result.stdout)

    def test_bad_citation_fails(self):
        """引文不是原文逐字子串时必须报错，防止负例集自己漂移。"""
        bad = {
            "id": "neg-900",
            "kind": "negation",
            "source": "synthetic",
            "text": "目前暂不建议使用他汀类药物。",
            "expected": {
                "paths": {
                    "western": {
                        "mentioned": True,
                        "state": "opposed",
                        "evidence": "这句话不在原文里",
                    }
                }
            },
            "rationale": "坏引文探针",
            "status": "pending_owner_confirmation",
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "negatives.jsonl"
            path.write_text(json.dumps(bad, ensure_ascii=False) + "\n", encoding="utf-8")
            result = self.run_script("--negatives", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("引文未在原文中逐字定位", result.stdout)

    def test_required_kinds_covered(self):
        rows = [
            json.loads(line)
            for line in NEGATIVES.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        kinds = {row["kind"] for row in rows}
        self.assertEqual(kinds & REQUIRED_KINDS, REQUIRED_KINDS)

    def test_all_negatives_confirmed_after_owner_calibration(self):
        """定标流转断言（2026-09-10 主人批改后启用）：负例集全部 confirmed。

        若未来新增负例，新条目从 pending 起步——届时本用例红灯是提醒，
        待主人确认后才会再次转绿。
        """
        rows = [
            json.loads(line)
            for line in NEGATIVES.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertTrue(all(row["status"] == "confirmed" for row in rows))

    def test_non_object_line_reports_error(self):
        """合法 JSON 但非对象（如数组）必须报错，不允许 traceback 崩溃。"""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "negatives.jsonl"
            path.write_text("[1, 2, 3]\n", encoding="utf-8")
            result = self.run_script("--negatives", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("不是 JSON 对象", result.stdout)

    def test_denominator_mismatch_fails(self):
        result = self.run_script("--expect-stop", "25")
        self.assertEqual(result.returncode, 1)
        self.assertIn("基线分母与口径不符", result.stdout)

    def test_require_confirmed_green_after_owner_calibration(self):
        """定标流转断言（2026-09-10 主人批改后启用）：全部 confirmed 后收口闸转绿。"""
        result = self.run_script("--require-confirmed")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_empty_baseline_fails(self):
        """空基线文件必须报错，不允许静默跳过分母检查后仍宣称全绿。"""
        with tempfile.TemporaryDirectory() as td:
            empty = Path(td) / "empty.jsonl"
            empty.write_text("", encoding="utf-8")
            result = self.run_script("--baseline", str(empty))
            self.assertEqual(result.returncode, 1)
            self.assertIn("基线文件无有效记录", result.stdout)

    def test_unhashable_field_reports_error(self):
        """kind 写成列表必须干净报错，不允许 TypeError traceback。"""
        bad = {
            "id": "neg-902",
            "kind": ["not_mentioned"],
            "source": "synthetic",
            "text": "文本。",
            "expected": {},
            "rationale": "探针",
            "status": "pending_owner_confirmation",
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "negatives.jsonl"
            path.write_text(json.dumps(bad, ensure_ascii=False) + "\n", encoding="utf-8")
            result = self.run_script("--negatives", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("不在枚举内或不是字符串", result.stdout)

    def test_baseline_identity_checked_independently(self):
        """--baseline 独立于 --trials 指定时，trial_id 缺失/重复必须报错。"""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "baseline.jsonl"
            row = {"finish_reason": "stop", "status": "success", "response": "正文"}
            path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
            result = self.run_script(
                "--baseline", str(path), "--expect-planned", "1", "--expect-stop", "1"
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("trial_id 缺失或非字符串", result.stdout)

    def test_truncation_requires_real_trial_ref(self):
        """截断是数据状态考查：合成截断没有意义，必须引用真实 trial。"""
        bad = {
            "id": "neg-901",
            "kind": "truncation",
            "source": "synthetic",
            "text": "一段被截断的合成文本。",
            "expected": {"status_note": "合成截断探针"},
            "rationale": "探针",
            "status": "pending_owner_confirmation",
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "negatives.jsonl"
            path.write_text(json.dumps(bad, ensure_ascii=False) + "\n", encoding="utf-8")
            result = self.run_script("--negatives", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("必须引用真实 trial", result.stdout)

    def test_worksheet_generator_refuses_overwrite(self):
        """已存在的工作表默认不被覆盖，防止抹掉人工标注。"""
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "ws.md"
            target.write_text("已有人工标注\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/gen_annotation_worksheet.py",
                    "-o",
                    str(target),
                ],
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("已存在", result.stdout)
            self.assertEqual(target.read_text(encoding="utf-8"), "已有人工标注\n")


if __name__ == "__main__":
    unittest.main()
