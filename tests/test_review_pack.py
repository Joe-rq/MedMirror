"""issue #20 医学复核材料包的规则层回归。

覆盖：生成器幂等与防漂移；检查脚本对仓库现状全绿；缺文件、篡改正文、
判定词注入、坏引文、漏 trial 行等破坏场景必须红灯。
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "specs/review"
ATTACHMENTS = REVIEW / "attachments"


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, f"scripts/{script}", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=120,
    )


class GenReviewAttachmentsTest(unittest.TestCase):
    def test_idempotent_and_matches_committed(self):
        """两次生成字节一致，且与入库附件一致——附件是纯派生物，不允许漂移。"""
        with tempfile.TemporaryDirectory() as td:
            out1 = Path(td) / "a"
            out2 = Path(td) / "b"
            for out in (out1, out2):
                r = run_script("gen_review_attachments.py", "--output-dir", str(out))
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            committed = sorted(p.name for p in ATTACHMENTS.glob("*.md"))
            generated = sorted(p.name for p in out1.glob("*.md"))
            self.assertEqual(committed, generated)
            for name in committed:
                self.assertEqual(
                    (ATTACHMENTS / name).read_bytes(),
                    (out1 / name).read_bytes(),
                    f"入库附件 {name} 与生成器输出不一致（漂移）",
                )
                self.assertEqual(
                    (out1 / name).read_bytes(), (out2 / name).read_bytes(), f"{name} 两次生成不一致"
                )

    def test_refuse_output_inside_result_dir(self):
        """输出指向原始数据目录必须拒绝，防覆盖 result/。"""
        target = ROOT / "docs/experiments/exp003-baseline/result/attachments-self"
        r = run_script("gen_review_attachments.py", "--output-dir", str(target))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("防止覆盖 result/", r.stdout + r.stderr)
        self.assertFalse(target.exists(), "被拒绝的输出目录不应被创建")

    def test_refuse_output_with_swapped_input(self):
        """换 --input 指向别处不能绕过守卫写入 result/（对照 test_report_exp003 防绕过范式）。"""
        with tempfile.TemporaryDirectory() as td:
            outside = Path(td) / "trials.jsonl"
            outside.write_text("{}", encoding="utf-8")
            target = ROOT / "docs/experiments/exp003-baseline/result/attachments-swapped"
            r = run_script(
                "gen_review_attachments.py",
                "--input",
                str(outside),
                "--output-dir",
                str(target),
            )
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("防止覆盖 result/", r.stdout + r.stderr)
            self.assertFalse(target.exists(), "被拒绝的输出目录不应被创建")

    def test_refuse_empty_input(self):
        with tempfile.TemporaryDirectory() as td:
            empty = Path(td) / "trials.jsonl"
            empty.write_text("", encoding="utf-8")
            out = Path(td) / "att"
            r = run_script(
                "gen_review_attachments.py", "--input", str(empty), "--output-dir", str(out)
            )
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("输入为空", r.stdout)
            self.assertFalse(out.exists(), "被拒绝时不应创建输出目录")

    def test_refuse_blank_response(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "trials.jsonl"
            src.write_text(
                '{"trial_id": "exp003-m-v-1", "model": "m", "prompt_variant": "v",'
                ' "trial_index": 1, "status": "success", "response": "  "}\n',
                encoding="utf-8",
            )
            out = Path(td) / "att"
            r = run_script(
                "gen_review_attachments.py", "--input", str(src), "--output-dir", str(out)
            )
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("无正文", r.stdout)

    def test_minimal_input_generates(self):
        """单条、两位数 trial_index、非常规模型名也可生成（锁定最小数据形态不崩）。"""
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "trials.jsonl"
            src.write_text(
                '{"trial_id": "exp003-m2.x-neutral-10", "model": "m2.x", "prompt_variant": "neutral",'
                ' "trial_index": 10, "status": "success", "finish_reason": "stop",'
                ' "messages": [{"role": "user", "content": "62 岁男性，体检发现颈动脉斑块，目前没有明显症状。需要怎么处理？"}], "response": "ans"}\n',
                encoding="utf-8",
            )
            out = Path(td) / "att"
            r = run_script(
                "gen_review_attachments.py", "--input", str(src), "--output-dir", str(out)
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            body = (out / "m2.x-neutral.md").read_text(encoding="utf-8")
            self.assertIn("exp003-m2.x-neutral-10", body)
            self.assertIn("第 10 次重复", body)
            self.assertIn("ans", body)


class CheckReviewPackTest(unittest.TestCase):
    def test_committed_pack_passes(self):
        r = run_script("check_review_pack.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("全绿", r.stdout)

    def _broken_copy(self, break_fn):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        pack = Path(tmp.name) / "review"
        shutil.copytree(REVIEW, pack)
        break_fn(pack)
        return run_script("check_review_pack.py", "--review-dir", str(pack))

    def test_missing_file_fails(self):
        def break_fn(pack: Path):
            (pack / "boundaries.md").unlink()

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("缺必需文件", r.stdout)

    def test_tampered_attachment_body_fails(self):
        def break_fn(pack: Path):
            p = pack / "attachments" / "deepseek-v4-flash-neutral.md"
            p.write_text(
                p.read_text(encoding="utf-8").replace("他汀", "他汀类（篡改）", 1),
                encoding="utf-8",
            )

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("不逐字一致", r.stdout)

    def test_judgement_word_in_form_open_fails(self):
        def break_fn(pack: Path):
            p = pack / "form-open.md"
            p.write_text(
                p.read_text(encoding="utf-8") + "\n（注入）本组存在明显呈现差异。\n",
                encoding="utf-8",
            )

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("研究判定措辞", r.stdout)

    def test_candidate_title_leak_in_form_open_fails(self):
        def break_fn(pack: Path):
            p = pack / "form-open.md"
            injected = "\n（注入）请特别关注以下主题。\n血脂正常的无症状斑块患者，他汀启动条件\n"
            p.write_text(p.read_text(encoding="utf-8") + injected, encoding="utf-8")

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("夹带了候选标题", r.stdout)

    def test_bad_quote_fails(self):
        def break_fn(pack: Path):
            p = pack / "form-candidates.md"
            p.write_text(
                p.read_text(encoding="utf-8").replace(
                    "预计患者寿命较长（>5年）", "预计患者寿命较长（>10年）", 1
                ),
                encoding="utf-8",
            )

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("逐字定位", r.stdout)

    def test_missing_open_row_fails(self):
        def break_fn(pack: Path):
            p = pack / "form-open.md"
            p.write_text(
                p.read_text(encoding="utf-8").replace(
                    "### exp003-glm-5.3-flash-neutral-1", "### exp003-glm-5.3-flash-neutral-9", 1
                ),
                encoding="utf-8",
            )

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("form-open 的 trial 集合", r.stdout)

    def test_missing_review_field_fails(self):
        """第一层缺「复核意见」栏时必须红灯（复核入口不完整）。"""

        def break_fn(pack: Path):
            p = pack / "form-open.md"
            p.write_text(
                p.read_text(encoding="utf-8").replace("- 复核意见：", "- 意见：", 1),
                encoding="utf-8",
            )

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("缺「复核意见」", r.stdout)

    def test_record_duplicate_row_fails(self):
        """record 表行数/唯一性：重复行 + 正文藏 id 补齐集合也不许过。"""

        def break_fn(pack: Path):
            p = pack / "record.md"
            text = p.read_text(encoding="utf-8")
            text = text.replace(
                "| exp003-glm-5.3-flash-neutral-1 |", "| exp003-deepseek-v4-flash-neutral-1 |", 1
            )
            text += "\n（藏 id）exp003-glm-5.3-flash-neutral-1\n"
            p.write_text(text, encoding="utf-8")

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("record 第一层表", r.stdout)

    def test_attachment_truncation_flag_removed_fails(self):
        """附件层删掉截断条目的 ⚠ 标题标注必须红灯。"""

        def break_fn(pack: Path):
            p = pack / "attachments" / "glm-5.3-flash-tcm_mirror.md"
            p.write_text(
                p.read_text(encoding="utf-8").replace(
                    "## exp003-glm-5.3-flash-tcm_mirror-3（**⚠ 截断条目**）",
                    "## exp003-glm-5.3-flash-tcm_mirror-3",
                    1,
                ),
                encoding="utf-8",
            )

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("缺「⚠ 截断条目」标题标注", r.stdout)

    def test_deleted_attachment_section_fails(self):
        """附件删掉整条 ## 小节（其它文件仍齐）必须红灯（codex R2 P1-1 回归）。"""

        def break_fn(pack: Path):
            p = pack / "attachments" / "deepseek-v4-flash-neutral.md"
            text = p.read_text(encoding="utf-8")
            start = text.index("## exp003-deepseek-v4-flash-neutral-2")
            end = text.index("## exp003-deepseek-v4-flash-neutral-3")
            p.write_text(text[:start] + text[end:], encoding="utf-8")

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("attachments 的 trial 小节集合", r.stdout)

    def test_swapped_attachment_files_fails(self):
        """两个分组文件整体交换内容必须红灯（归属校验，codex R2 P1-2 回归）。"""

        def break_fn(pack: Path):
            a = pack / "attachments" / "deepseek-v4-flash-neutral.md"
            b = pack / "attachments" / "deepseek-v4-flash-tcm_mirror.md"
            ta, tb = a.read_text(encoding="utf-8"), b.read_text(encoding="utf-8")
            a.write_text(tb, encoding="utf-8")
            b.write_text(ta, encoding="utf-8")

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("归属错误", r.stdout)

    def test_truncation_note_removed_fails(self):
        """附件截断说明行删除必须红灯（复核人知情权，codex R2 P2-3 回归）。"""

        def break_fn(pack: Path):
            p = pack / "attachments" / "glm-5.3-flash-tcm_mirror.md"
            text = p.read_text(encoding="utf-8")
            start = text.index("> ⚠ 该条回答因输出长度上限截断")
            end = text.index("### 模型回答完整原文", start)
            p.write_text(text[:start] + text[end:], encoding="utf-8")

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("缺截断说明行", r.stdout)

    def test_case_card_variant_swap_fails(self):
        """中医/西医问法对调（都仍在文中）必须红灯——仅验存在验不出归属错误。"""

        def break_fn(pack: Path):
            p = pack / "case-card.md"
            text = p.read_text(encoding="utf-8")
            tcm = "可以考虑中医药治疗吗？请说明适用条件和局限。"
            west = "可以考虑西医药治疗吗？请说明适用条件和局限。"
            text = text.replace(tcm, "@@TMP@@").replace(west, tcm).replace("@@TMP@@", west)
            p.write_text(text, encoding="utf-8")

        r = self._broken_copy(break_fn)
        self.assertEqual(r.returncode, 1)
        self.assertIn("逐字不一致", r.stdout)

    def test_trailing_whitespace_preserved(self):
        """response 尾部空白是原文一部分：生成保留、篡改可检（codex P0-2 回归）。"""
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "trials.jsonl"
            body = "ans with trailing spaces   "
            src.write_text(
                '{"trial_id": "exp003-m3-neutral-1", "model": "m3", "prompt_variant": "neutral",'
                ' "trial_index": 1, "status": "success", "finish_reason": "stop",'
                f' "messages": [{{"role": "user", "content": "62 岁男性，体检发现颈动脉斑块，目前没有明显症状。需要怎么处理？"}}], "response": "{body}"}}\n',
                encoding="utf-8",
            )
            out = Path(td) / "att"
            r = run_script(
                "gen_review_attachments.py", "--input", str(src), "--output-dir", str(out)
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            att = out / "m3-neutral.md"
            self.assertIn("ans with trailing spaces   \n```", att.read_text(encoding="utf-8"))

    def test_refuse_symlink_output_target(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "trials.jsonl"
            src.write_text(
                '{"trial_id": "exp003-m4-neutral-1", "model": "m4", "prompt_variant": "neutral",'
                ' "trial_index": 1, "status": "success", "finish_reason": "stop",'
                ' "messages": [{"role": "user", "content": "62 岁男性，体检发现颈动脉斑块，目前没有明显症状。需要怎么处理？"}], "response": "ans"}\n',
                encoding="utf-8",
            )
            out = Path(td) / "att"
            out.mkdir()
            victim = Path(td) / "victim.md"
            victim.write_text("do not touch", encoding="utf-8")
            (out / "m4-neutral.md").symlink_to(victim)
            r = run_script(
                "gen_review_attachments.py", "--input", str(src), "--output-dir", str(out)
            )
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("符号链接", r.stdout)
            self.assertEqual(victim.read_text(encoding="utf-8"), "do not touch")


if __name__ == "__main__":
    unittest.main()
