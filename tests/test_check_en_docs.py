"""中英文档一致性闸（scripts/check_en_docs.py）的规则层回归。

起因：issue #51——英文 README 是国际读者的第一入口，验收②「对外声明合规」
最容易做假（翻译时把 Bias/定标局限/复核状态写弱或写没，肉眼难发现），
且中英双份文档是下一个同源漂移源（board 记录过测试数手工刷 5 处）。
本闸拦四类可判定的错：锚点缺失、字段漏译、入口断链、测试数不一致。

「可见性」是本闸的主要攻防面：声明必须出现在读者看得见的正文里，
代码块（含未闭合的、波浪线的）、HTML 注释、HTML 属性、行内代码里的命中都不算。
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
        "中／西医变体是提示敏感性条件，不是医学等价对照\n\n"
        "236 项测试（无需 API 密钥）\n\n"
        "236 项离线测试\n\n"
        "uv run pytest  # 闸3 逻辑（236 用例）\n"
    ),
    "README.en.md": (
        "# MedMirror\n\n"
        "**[中文版（Chinese）](README.md)**\n\n"
        "no medical-bias verdict without professional review\n\n"
        "were accepted without independent annotation\n\n"
        "professional review has not returned\n\n"
        "prompt-sensitivity conditions, not medically equivalent controls\n\n"
        "uv run pytest  # 236 tests\n"
    ),
    "configs/cases/README.md": (
        "# 病例声明式配置（CaseSpec）\n\n"
        "**[English](README.en.md)**\n\n"
        "| 字段 | 类型 | 说明 |\n|---|---|---|\n"
        "| `case_id` | str | 唯一标识 |\n"
        "| `synthetic` | bool | 合成声明 |\n"
        "| `extraction.paths` | {path: [term]} | 路径词表 |\n"
        "| `notes` | str | 病例说明 |\n"
    ),
    "configs/cases/README.en.md": (
        "# Case configuration (CaseSpec)\n\n"
        "**[中文版（Chinese）](README.md)**\n\n"
        "| Field | Type | Notes |\n|---|---|---|\n"
        "| `case_id` | str | unique id |\n"
        "| `synthetic` | bool | synthetic declaration |\n"
        "| `extraction.paths` | {path: [term]} | path vocabulary |\n"
        "| `notes` | str | case description |\n"
    ),
    "docs/onboarding/README.md": "uv run pytest  # 236 passed\n",
    "docs/plan/003_post-hackathon-roadmap.md": "- 四闸 CI 全绿（pytest 236）\n",
    "docs/report/001_tech-report-materials.md": "uv sync && uv run pytest  # 236 项离线测试\n",
    "docs/reviews/judge-entry.md": "- **236 项离线测试** + CI 四闸全绿\n",
}

BOLD_BIAS = "**no medical-bias verdict without professional review**"


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

    def assert_gate_fails_body(self, rel: str, body: str, *fragments: str) -> None:
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
        self.assertIn("4 条声明锚点成对", r.stdout)
        self.assertIn("4 个字段标识符一致", r.stdout)
        self.assertIn("2 对互链", r.stdout)
        self.assertIn("测试数 236（6 份文档同值）", r.stdout)

    def test_weakened_declaration_fails(self):
        """声明在翻译中被写弱/写没——本闸存在的主要理由。"""
        self.assert_gate_fails(
            "README.en.md",
            "no medical-bias verdict without professional review",
            "descriptive results",
            "缺声明锚点「no medical-bias verdict without professional review」",
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

    def test_variant_boundary_missing_fails(self):
        """「中／西医变体不是医学等价对照」两侧成对——英文入口漏了它同样红灯。"""
        self.assert_gate_fails(
            "README.en.md",
            "prompt-sensitivity conditions, not medically equivalent controls\n",
            "",
            "缺声明锚点「not medically equivalent controls」",
        )

    def test_anchor_in_code_fence_does_not_count(self):
        """把声明从正文挪进围栏代码块：读者看不见，闸必须仍红灯。"""
        self.assert_gate_fails(
            "README.en.md",
            "no medical-bias verdict without professional review",
            "```text\nno medical-bias verdict without professional review\n```",
            "缺声明锚点「no medical-bias verdict without professional review」",
        )

    def test_unclosed_fence_hides_anchor(self):
        """未闭合的围栏按 CommonMark 延续到文末——其后正文不算可见（docstring 已声明）。"""
        self.assert_gate_fails(
            "README.en.md",
            "no medical-bias verdict without professional review",
            "```text\nno medical-bias verdict without professional review",
            "缺声明锚点「no medical-bias verdict without professional review」",
        )

    def test_tilde_fence_hides_anchor(self):
        """~~~ 围栏与 ``` 同等对待。"""
        self.assert_gate_fails(
            "README.en.md",
            "no medical-bias verdict without professional review",
            "~~~\nno medical-bias verdict without professional review\n~~~",
            "缺声明锚点「no medical-bias verdict without professional review」",
        )

    def test_unclosed_html_comment_hides_anchor(self):
        """未闭合的 HTML 注释同样延续到文末（与未闭合围栏同款处理）。"""
        self.assert_gate_fails(
            "README.en.md",
            "no medical-bias verdict without professional review",
            "<!-- no medical-bias verdict without professional review",
            "缺声明锚点「no medical-bias verdict without professional review」",
        )

    def test_hidden_element_hides_anchor(self):
        """display:none 之类显式隐藏元素里的声明，读者看不见。"""
        self.assert_gate_fails(
            "README.en.md",
            "no medical-bias verdict without professional review",
            '<div style="display:none">no medical-bias verdict without professional review</div>',
            "缺声明锚点「no medical-bias verdict without professional review」",
        )

    def test_hidden_element_variants_hide_anchor(self):
        """style/script 块与任意标签上的 hidden 都算不可见（R2 补）。"""
        for wrap in ("<style>{}</style>", "<script>{}</script>", "<article hidden>{}</article>"):
            with self.subTest(wrap=wrap):
                body = FIXTURE["README.en.md"].replace(
                    "no medical-bias verdict without professional review",
                    wrap.format("no medical-bias verdict without professional review"),
                )
                r = run_gate(self._repo_copy({"README.en.md": body}))
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("缺声明锚点「no medical-bias verdict", r.stdout)

    def test_inline_code_hides_anchor(self):
        """声明被塞进行内代码：是被引用，不是「在说」——不算数（R2 补）。"""
        self.assert_gate_fails(
            "README.en.md",
            "no medical-bias verdict without professional review",
            "`no medical-bias verdict without professional review`",
            "缺声明锚点「no medical-bias verdict without professional review」",
        )

    def test_indented_code_hides_anchor(self):
        """4 空格缩进在 Markdown 里是代码块（R2 补）。"""
        self.assert_gate_fails(
            "README.en.md",
            "no medical-bias verdict without professional review",
            "    no medical-bias verdict without professional review",
            "缺声明锚点「no medical-bias verdict without professional review」",
        )

    def test_image_and_escaped_links_do_not_count(self):
        """图片、转义方括号、双反引号代码 span 都不是入口链接（R2 补）。"""
        for wrap in (
            "![English](README.en.md)",
            "\\[English](README.en.md)",
            "``[English](README.en.md)``",
        ):
            with self.subTest(wrap=wrap):
                body = FIXTURE["README.md"].replace("**[English](README.en.md)**", wrap)
                r = run_gate(self._repo_copy({"README.md": body}))
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("缺英文版入口链接（README.en.md）", r.stdout)

    def test_html_attribute_hides_anchor(self):
        """HTML 标签属性里的声明读者看不见。"""
        self.assert_gate_fails(
            "README.en.md",
            "no medical-bias verdict without professional review",
            '<span aria-label="no medical-bias verdict without professional review"></span>',
            "缺声明锚点「no medical-bias verdict without professional review」",
        )

    def test_anchor_in_html_comment_does_not_count(self):
        """HTML 注释里留一句声明，也不该算数。"""
        self.assert_gate_fails(
            "README.en.md",
            "no medical-bias verdict without professional review",
            "we report descriptive observations only\n\n"
            "<!-- no medical-bias verdict without professional review -->",
            "缺声明锚点「no medical-bias verdict without professional review」",
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

    def test_cross_link_in_code_fence_does_not_count(self):
        """入口链接藏在代码块里，读者点不到——同样红灯。"""
        self.assert_gate_fails(
            "README.md",
            "**[English](README.en.md)**",
            "```\n[English](README.en.md)\n```",
            "缺英文版入口链接（README.en.md）",
        )

    def test_inline_code_link_is_not_a_link(self):
        """行内代码里的 `](README.en.md)` 不是链接，点不动——不算入口。"""
        self.assert_gate_fails(
            "README.md",
            "**[English](README.en.md)**",
            "`](README.en.md)`",
            "缺英文版入口链接（README.en.md）",
        )

    def test_unparsed_table_row_fails(self):
        """正本加一行非反引号格式的字段行、英文版不补：两侧都解析不到，必须红灯而非静默放过。"""
        self.assert_gate_fails(
            "configs/cases/README.md",
            "| `notes` | str | 病例说明 |",
            "| `notes` | str | 病例说明 |\n| **severity_note** | str | 新增字段 |",
            "像表格行但首列不是反引号字段名",
        )

    def test_table_row_without_leading_pipe_is_visible(self):
        """GFM 允许省首尾竖线——这类行必须仍被规则 2 看见（英文版不补即红灯）。"""
        self.assert_gate_fails(
            "configs/cases/README.md",
            "| `notes` | str | 病例说明 |",
            "| `notes` | str | 病例说明 |\n`case_text` | str | 隐藏字段 |",
            "字段表与 configs/cases/README.md 不一致",
            "英文版缺 case_text",
        )

    def test_table_row_without_any_edge_pipe_fails(self):
        """两侧都省竖线的合法 GFM 表格行同样不能隐形（R2 补）。"""
        self.assert_gate_fails(
            "configs/cases/README.md",
            "| 字段 | 类型 | 说明 |\n|---|---|---|",
            "字段 | 类型 | 说明\n--- | --- | ---\n**severity_note** | str | 新增字段",
            "像表格行但首列不是反引号字段名",
        )

    def test_blockquote_table_row_fails(self):
        """引用块里的表格同样是表格（R2 补）。"""
        self.assert_gate_fails(
            "configs/cases/README.md",
            "| `notes` | str | 病例说明 |",
            "| `notes` | str | 病例说明 |\n> | **severity_note** | str | 新增字段 |",
            "像表格行但首列不是反引号字段名",
        )

    def test_pseudo_field_outside_table_is_not_a_field(self):
        """表外的 `` `x` | y `` 不算字段——否则可用伪字段补齐集合蒙混过关（R2 补）。"""
        self.assert_gate_fails(
            "configs/cases/README.md",
            "| `notes` | str | 病例说明 |\n",
            "",
            "字段表与 configs/cases/README.md 不一致",
        )

    def test_prose_with_pipe_is_not_a_table(self):
        """带竖线的普通句子不该被误判成表格行（沙箱自证：正例仍绿）。"""
        body = FIXTURE["configs/cases/README.md"] + "\n说明：字段与类型用 `|` 分隔。\n"
        r = run_gate(self._repo_copy({"configs/cases/README.md": body}))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

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

    def test_test_count_in_html_comment_does_not_count(self):
        """把测试数挪进 HTML 注释，读者看不见——规则 4 也去注释。"""
        self.assert_gate_fails(
            "README.en.md",
            "uv run pytest  # 236 tests",
            "<!-- 236 tests -->",
            "测试数锚点命中 0 个值",
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
            "| `extraction.paths` | {path: [term]} | 路径词表 |\n"
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
