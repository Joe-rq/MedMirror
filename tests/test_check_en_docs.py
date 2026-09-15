"""中英文档一致性闸（scripts/check_en_docs.py）的规则层回归。

起因：issue #51——英文 README 是国际读者的第一入口，验收②「对外声明合规」
最容易做假（翻译时把 Bias/定标局限/复核状态写弱或写没，肉眼难发现），
且中英双份文档是下一个同源漂移源（board 记录过测试数手工刷 5 处）。
本闸只拦四类可判定的错：锚点缺失、字段漏译、入口断链、测试数不一致。
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 沙箱最小正例：四份文档，声明锚点、字段表、互链、测试数齐全
FIXTURE = {
    "README.md": (
        "# MedMirror\n\n"
        "**[English](README.en.md)**\n\n"
        "不输出未经专业复核的医学 Bias 结论\n\n"
        "14 条信任扩展未经独立标注\n\n"
        "专业复核未回流\n\n"
        "uv run pytest  # 闸3 逻辑（236 用例）\n"
    ),
    "README.en.md": (
        "# MedMirror\n\n"
        "**[中文版（Chinese）](README.md)**\n\n"
        "no medical bias verdict\n\n"
        "were accepted without independent annotation\n\n"
        "professional review has not returned\n\n"
        "uv run pytest  # 236 tests\n"
    ),
    "configs/cases/README.md": (
        "# 病例声明式配置（CaseSpec）\n\n"
        "**[English](README.en.md)**\n\n"
        "| 字段 | 类型 | 说明 |\n|---|---|---|\n"
        "| `case_id` | str | 唯一标识 |\n"
        "| `synthetic` | bool | 合成声明 |\n"
        "| `notes` | str | 病例说明 |\n"
    ),
    "configs/cases/README.en.md": (
        "# Case configuration (CaseSpec)\n\n"
        "**[中文版（Chinese）](README.md)**\n\n"
        "| Field | Type | Notes |\n|---|---|---|\n"
        "| `case_id` | str | unique id |\n"
        "| `synthetic` | bool | synthetic declaration |\n"
        "| `notes` | str | case description |\n"
    ),
}


def run_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_en_docs.py", "--root", str(root)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=120,
    )


class CheckEnDocsGateTest(unittest.TestCase):
    def _repo_copy(self, override: dict[str, str] | None = None, drop: set[str] | None = None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        files = {rel: body for rel, body in FIXTURE.items() if rel not in (drop or set())}
        for rel, body in {**files, **(override or {})}.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return root

    def test_committed_repo_passes(self):
        r = run_gate(ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("中英文档一致", r.stdout)

    def test_sandbox_fixture_passes(self):
        """沙箱正例先自证——不然反例红灯可能来自 fixture 本身不合规。"""
        r = run_gate(self._repo_copy())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("3 条声明锚点成对", r.stdout)
        self.assertIn("3 个字段标识符一致", r.stdout)

    def test_weakened_declaration_fails(self):
        """声明在翻译中被写弱/写没——本闸存在的主要理由。"""
        body = FIXTURE["README.en.md"].replace("no medical bias verdict", "descriptive results")
        r = run_gate(self._repo_copy({"README.en.md": body}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("缺声明锚点「no medical bias verdict」", r.stdout)
        self.assertIn("对外声明合规", r.stdout)

    def test_zh_side_anchor_removed_fails(self):
        """中文正本先坏也要拦：声明是锚在两侧的，不是只查英文。"""
        body = FIXTURE["README.md"].replace("专业复核未回流\n", "")
        r = run_gate(self._repo_copy({"README.md": body}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("缺声明锚点「专业复核未回流」", r.stdout)
        self.assertIn("中文正本先被动过", r.stdout)

    def test_missing_translated_field_fails(self):
        """字段漏译：读者按英文文档填配置会直接失败。"""
        body = FIXTURE["configs/cases/README.en.md"].replace(
            "| `notes` | str | case description |\n", ""
        )
        r = run_gate(self._repo_copy({"configs/cases/README.en.md": body}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("字段表与 configs/cases/README.md 不一致", r.stdout)
        self.assertIn("英文版缺 notes", r.stdout)

    def test_extra_translated_field_fails(self):
        """英文版多一个字段同样是漂移（正本才是字段全集）。"""
        body = FIXTURE["configs/cases/README.en.md"].replace(
            "| `notes` | str | case description |",
            "| `notes` | str | case description |\n| `extra_key` | str | invented |",
        )
        r = run_gate(self._repo_copy({"configs/cases/README.en.md": body}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("英文版多 extra_key", r.stdout)

    def test_missing_cross_link_fails(self):
        """入口断链：中文版没了英文入口（或反之），国际读者找不到门。"""
        body = FIXTURE["README.md"].replace("**[English](README.en.md)**\n", "")
        r = run_gate(self._repo_copy({"README.md": body}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("缺英文版入口链接（README.en.md）", r.stdout)

    def test_test_count_drift_fails(self):
        """中英测试数不一致——board 记录的旧病（手工刷多处必漏一处）。"""
        body = FIXTURE["README.en.md"].replace("236 tests", "999 tests")
        r = run_gate(self._repo_copy({"README.en.md": body}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("测试数中英不一致", r.stdout)
        self.assertIn("README.md 写 236、README.en.md 写 999", r.stdout)

    def test_self_inconsistent_count_fails(self):
        """同一文件里两个测试数——锚点自己就矛盾，先修文档再谈一致性。"""
        body = FIXTURE["README.md"].replace(
            "uv run pytest  # 闸3 逻辑（236 用例）",
            "uv run pytest  # 闸3 逻辑（236 用例）\nuv run pytest  # 闸3 逻辑（300 用例）",
        )
        r = run_gate(self._repo_copy({"README.md": body}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("命中 2 个值", r.stdout)

    def test_missing_english_file_fails(self):
        """英文文档没入库即红灯（成对入库是硬要求）。"""
        r = run_gate(self._repo_copy(drop={"README.en.md"}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("README.en.md: 文件不存在", r.stdout)

    def test_field_table_rewritten_fails(self):
        """字段表被整段改写（首列不再是反引号标识符）——解析不到即红灯。"""
        body = "# 病例声明式配置（CaseSpec）\n\n**[English](README.en.md)**\n\n字段表已删除\n"
        r = run_gate(self._repo_copy({"configs/cases/README.md": body}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("未解析到字段表首列标识符", r.stdout)

    def test_empty_root_fails(self):
        """--root 指错地方不能静默通过。"""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        r = run_gate(Path(tmp.name))
        self.assertEqual(r.returncode, 1)
        self.assertIn("文件不存在", r.stdout)


if __name__ == "__main__":
    unittest.main()
