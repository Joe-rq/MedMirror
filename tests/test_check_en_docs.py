"""中英文档一致性闸（scripts/check_en_docs.py）的规则层回归。

起因：issue #51——英文 README 是国际读者的第一入口，验收②「对外声明合规」
最容易做假（翻译时把 Bias/定标局限/复核状态写弱或写没，肉眼难发现），
且中英双份文档是下一个同源漂移源（board 记录过测试数手工刷 5 处）。
本闸拦四类可判定的错：锚点缺失、字段漏译、入口断链、测试数不一致。
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 沙箱最小正例：覆盖闸门读的全部八份文档，声明锚点、字段表、互链、测试数齐全
FIXTURE = {
    "README.md": (
        "# MedMirror\n\n"
        "**[English](README.en.md)**\n\n"
        "不输出未经专业复核的医学 Bias 结论\n\n"
        "14 条信任扩展未经独立标注\n\n"
        "专业复核未回流\n\n"
        "236 项测试（无需 API 密钥）\n\n"
        "236 项离线测试\n\n"
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
    "docs/onboarding/README.md": "uv run pytest  # 236 passed\n",
    "docs/plan/003_post-hackathon-roadmap.md": "- 四闸 CI 全绿（pytest 236）\n",
    "docs/report/001_tech-report-materials.md": "uv sync && uv run pytest  # 236 项离线测试\n",
    "docs/reviews/judge-entry.md": "- **236 项离线测试** + CI 四闸全绿\n",
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
    def _repo_copy(self, override: dict[str, str] | None = None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for rel, body in {**FIXTURE, **(override or {})}.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return root

    def assert_gate_fails(self, rel: str, old: str, new: str, *fragments: str) -> None:
        """把沙箱里 rel 的 old 换成 new，断言闸门红灯且报出 fragments。"""
        self.assertIn(old, FIXTURE[rel], "沙箱 fixture 里找不到待替换串——本轮测试自身失效")
        body = FIXTURE[rel].replace(old, new)
        r = run_gate(self._repo_copy({rel: body}))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        for frag in fragments:
            self.assertIn(frag, r.stdout)

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
        self.assertIn("2 对互链", r.stdout)
        self.assertIn("测试数 236（6 份文档同值）", r.stdout)

    def test_weakened_declaration_fails(self):
        """声明在翻译中被写弱/写没——本闸存在的主要理由。"""
        self.assert_gate_fails(
            "README.en.md",
            "no medical bias verdict",
            "descriptive results",
            "缺声明锚点「no medical bias verdict」",
            "对外声明合规",
        )

    def test_zh_side_anchor_removed_fails(self):
        """中文正本先坏也要拦：声明是锚在两侧的，不是只查英文。"""
        self.assert_gate_fails(
            "README.md",
            "专业复核未回流\n",
            "",
            "缺声明锚点「专业复核未回流」",
            "中文正本先被动过",
        )

    def test_missing_translated_field_fails(self):
        """字段漏译：读者按英文文档填配置会直接失败。"""
        self.assert_gate_fails(
            "configs/cases/README.en.md",
            "| `notes` | str | case description |\n",
            "",
            "字段表与 configs/cases/README.md 不一致",
            "英文版缺 notes",
        )

    def test_extra_translated_field_fails(self):
        """英文版多一个字段同样是漂移（正本才是字段全集）。"""
        self.assert_gate_fails(
            "configs/cases/README.en.md",
            "| `notes` | str | case description |",
            "| `notes` | str | case description |\n| `extra_key` | str | invented |",
            "英文版多 extra_key",
        )

    def test_missing_cross_link_fails(self):
        """中文版没了英文入口，国际读者找不到门。"""
        self.assert_gate_fails(
            "README.md",
            "**[English](README.en.md)**\n",
            "",
            "缺英文版入口链接（README.en.md）",
        )

    def test_missing_reverse_cross_link_fails(self):
        """反向也要拦：英文版没了中文入口，中文读者回不去正本。"""
        self.assert_gate_fails(
            "README.en.md",
            "**[中文版（Chinese）](README.md)**\n",
            "",
            "缺中文版入口链接（README.md）",
        )

    def test_test_count_drift_across_files_fails(self):
        """跨文件漂移：只刷了一处、漏了另外五份——board 记录的旧病。"""
        self.assert_gate_fails(
            "docs/onboarding/README.md",
            "# 236 passed",
            "# 236 passed\nuv run pytest  # 999 passed",
            "测试数锚点命中 2 个值",
        )

    def test_test_count_single_file_stale_fails(self):
        """六份文档同值约束：一份整体写旧值，其余五份新值，也要红灯。"""
        self.assert_gate_fails(
            "docs/reviews/judge-entry.md",
            "**236 项离线测试**",
            "**999 项离线测试**",
            "测试数各处不一致",
        )

    def test_self_inconsistent_count_fails(self):
        """同一文件里两个测试数——锚点自己就矛盾，先修文档再谈一致性。"""
        self.assert_gate_fails(
            "README.md",
            "uv run pytest  # 闸3 逻辑（236 用例）",
            "uv run pytest  # 闸3 逻辑（236 用例）\nuv run pytest  # 闸3 逻辑（300 用例）",
            "命中 2 个值",
        )

    def test_missing_english_file_fails(self):
        """英文文档没入库即红灯（成对入库是硬要求）。"""
        root = self._repo_copy()
        (root / "README.en.md").unlink()
        r = run_gate(root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("README.en.md: 文件不存在", r.stdout)

    def test_field_table_rewritten_fails(self):
        """字段表被整段改写（首列不再是反引号标识符）——解析不到即红灯。"""
        self.assert_gate_fails(
            "configs/cases/README.md",
            "| 字段 | 类型 | 说明 |\n|---|---|---|\n"
            "| `case_id` | str | 唯一标识 |\n"
            "| `synthetic` | bool | 合成声明 |\n"
            "| `notes` | str | 病例说明 |\n",
            "字段表已删除\n",
            "未解析到字段表首列标识符",
        )

    def test_empty_root_fails(self):
        """--root 指错地方不能静默通过。"""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        r = run_gate(Path(tmp.name))
        self.assertEqual(r.returncode, 1)
        self.assertIn("文件不存在", r.stdout)


if __name__ == "__main__":
    unittest.main()
