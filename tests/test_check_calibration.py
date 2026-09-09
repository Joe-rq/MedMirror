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

    def test_all_negatives_pending_until_owner_confirms(self):
        """定标纪律：AI 交付时不得有任何 confirmed 条目冒充已确认标准。"""
        rows = [
            json.loads(line)
            for line in NEGATIVES.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertTrue(all(row["status"] == "pending_owner_confirmation" for row in rows))


if __name__ == "__main__":
    unittest.main()
