"""issue #24 Word 导出的规则层回归。

覆盖：open 批次不含候选内容（判定后置在导出层落地）、candidates 批次 DRAFT
拒绝与 --allow-draft 放行、pandoc 缺失指引、输出目录防呆、幂等重建、
陌生 docx 不误删。pandoc 未安装的环境自动跳过导出用例（CI 无 pandoc 时四闸仍绿）；
守卫类用例（数据目录防呆、DRAFT 拒绝）不依赖 pandoc，始终执行。
"""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs/experiments/exp003-baseline/result"
HAS_PANDOC = shutil.which("pandoc") is not None

sys.path.insert(0, str(ROOT / "scripts"))
from export_review_pack import (  # noqa: E402
    MANIFEST_NAME,
    candidates_finalized,
    load_manifest,
    pick_section_problems,
)

# 独立 manifest：不 import 实现的 open_layer_files（防测试与实现共用错误）；
# 实现侧漂移由 open_layer_files 的目录对账兜底，此处独立清单负责抓实现漂移。
EXPECTED_OPEN_DOCX = sorted(
    [
        "background.docx",
        "case-card.docx",
        "boundaries.docx",
        "form-open.docx",
        "attachments__index.docx",
    ]
    + [
        f"attachments__{m}-{v}.docx"
        for m in ("deepseek-v4-flash", "glm-5.3-flash", "step-3.7-flash")
        for v in ("neutral", "tcm_mirror", "western_mirror")
    ]
)

# 泄漏标记：候选编号正则全覆盖 + 从真相源动态提取全部候选标题（20 条全覆盖，
# 不抽样）。泛词「候选主张」不列入——流程预告不含具体主张内容，不构成泄漏。
CAND_ID_RE = re.compile(r"cand-\d{2}")


def cand_titles() -> list[str]:
    text = (ROOT / "specs/review/form-candidates.md").read_text(encoding="utf-8")
    return [
        m.group(1).strip()
        for m in re.finditer(r"^#{2,3} cand-\d+ 【[^】]*】(.+)$", text, re.MULTILINE)
    ]


def run_export(*args: str, env=None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/export_review_pack.py", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=300,
        env=env,
    )


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    return re.sub(r"<[^>]+>", "", xml)


class ExportGuardTest(unittest.TestCase):
    """不依赖 pandoc 的规则层守卫（触发分支都在 ensure_pandoc 之前）。"""

    def test_refuse_output_into_data_dir(self):
        r = run_export("--layer", "open", "--output-dir", str(DATA_DIR / "export"))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("受保护目录", r.stdout)

    def test_refuse_output_into_review_dir(self):
        """派生 docx 不得混入 md 真相源目录 specs/review/ 本体。"""
        r = run_export("--layer", "open", "--output-dir", str(ROOT / "specs" / "review"))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("受保护目录", r.stdout)

    def test_placeholder_section_refused_even_with_allow_draft(self):
        """挑选区为占位（未勾选）→ 结构拒绝，--allow-draft 也不豁免。

        场景自建（真实材料 2026-09-13 已定稿 FINAL，不再天然提供占位状态）：
        拷贝材料包后把必核子集/日期行改回占位，校验结构守卫。
        """
        with tempfile.TemporaryDirectory() as td:
            pack = Path(td) / "review"
            shutil.copytree(ROOT / "specs/review", pack)
            cand = pack / "form-candidates.md"
            text = cand.read_text(encoding="utf-8")
            text = re.sub(r"^- 必核子集：.*$", "- 必核子集：待定", text, flags=re.MULTILINE)
            cand.write_text(text, encoding="utf-8", newline="\n")
            out = Path(td) / "export"
            r = run_export(
                "--layer", "candidates", "--review-dir", str(pack),
                "--output-dir", str(out), "--allow-draft",
            )
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("结构不合法", r.stdout)
            self.assertFalse(list(out.glob("*.docx")) if out.exists() else [])

    def test_pandoc_missing_hint(self):
        """PATH 清空时报错并给安装指引（不依赖 pandoc 存在与否都可测）。"""
        with tempfile.TemporaryDirectory() as td:
            r = run_export("--layer", "open", "--output-dir", str(Path(td) / "e"), env={"PATH": ""})
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("brew install pandoc", r.stdout + r.stderr)

    def test_unknown_layer_rejected(self):
        r = run_export("--layer", "nope")
        self.assertNotEqual(r.returncode, 0)


@unittest.skipUnless(HAS_PANDOC, "本机未安装 pandoc，跳过导出用例")
class ExportOpenLayerTest(unittest.TestCase):
    def test_open_layer_excludes_candidates(self):
        """open 批次导出物绝不包含候选主张内容（判定后置的导出层落地）。"""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "export"
            r = run_export("--layer", "open", "--output-dir", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            docx_files = sorted(p.name for p in out.glob("*.docx"))
            self.assertEqual(docx_files, EXPECTED_OPEN_DOCX, "导出文件集应与独立 manifest 一致")
            self.assertNotIn("form-candidates.docx", docx_files)
            texts = {p.name: docx_text(p) for p in sorted(out.glob("*.docx"))}
            titles = cand_titles()
            self.assertGreaterEqual(len(titles), 15, "候选标题提取应覆盖候选池（防提取器静默失效）")
            for name, text in texts.items():
                self.assertIsNone(CAND_ID_RE.search(text), f"{name} 泄漏了候选编号")
                for marker in titles:
                    self.assertNotIn(marker, text, f"{name} 泄漏了候选标题：{marker}")
            # 使用说明与复核入口在场
            self.assertIn("Word 版使用说明", texts["form-open.docx"])
            self.assertIn("自动更正", texts["form-open.docx"])
            self.assertIn("exp003-glm-5.3-flash-tcm_mirror-3", texts["form-open.docx"])

    def test_default_output_dir_works(self):
        """默认命令必须可用（P1-1 回归：specs/review/export/ 是 REVIEW 锚的唯一豁免）。"""
        r = run_export("--layer", "open")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((ROOT / "specs/review/export/form-open.docx").is_file())

    def test_idempotent_rebuild(self):
        """重导出可重建且核心内容一致（docx zip 含时间戳，比对正文而非字节）。"""
        with tempfile.TemporaryDirectory() as td:
            out1, out2 = Path(td) / "a", Path(td) / "b"
            for out in (out1, out2):
                r = run_export("--layer", "open", "--output-dir", str(out))
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(docx_text(out1 / "form-open.docx"), docx_text(out2 / "form-open.docx"))

    def test_foreign_and_replaced_files_refused(self):
        """陌生文件拒绝执行；与 manifest 记录不一致的同名文件（被人工替换）同样拒绝。"""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "export"
            r = run_export("--layer", "open", "--output-dir", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            # 陌生异名文件：拒绝执行且不删
            foreign = out / "复核人回执-旧版.docx"
            foreign.write_bytes(b"user file")
            r = run_export("--layer", "open", "--output-dir", str(out))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("拒绝执行", r.stdout)
            self.assertTrue(foreign.exists(), "用户文件不得被误删")
            # 同名人工替换：hash 与 manifest 不一致 → 拒绝覆盖
            foreign.unlink()
            victim = out / "form-open.docx"
            backup = victim.read_bytes()
            victim.write_bytes(b"user replaced file with product name")
            r = run_export("--layer", "open", "--output-dir", str(out))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("不一致", r.stdout)
            self.assertEqual(victim.read_bytes(), b"user replaced file with product name")
            # 恢复产物后重导成功（正常重建路径）
            victim.write_bytes(backup)
            r = run_export("--layer", "open", "--output-dir", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("复核意见", docx_text(out / "form-open.docx"))

    def test_layer_switch_cleans_recorded_files(self):
        """跨层导出：旧层产物（manifest 记录且 hash 吻合）被清理，新层就位。"""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "export"
            r = run_export("--layer", "open", "--output-dir", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            pack = Path(td) / "pack"
            shutil.copytree(ROOT / "specs/review", pack)
            cand = pack / "form-candidates.md"
            text = cand.read_text(encoding="utf-8")
            text = text.replace(
                "- 必核子集：待定",
                "- 必核子集：" + "、".join(f"cand-{i:02d}" for i in range(1, 9)),
            ).replace("- 定稿依据与日期：待定", "- 定稿依据与日期：预览 2026")
            cand.write_text(text, encoding="utf-8", newline="\n")
            r = run_export(
                "--layer",
                "candidates",
                "--review-dir",
                str(pack),
                "--output-dir",
                str(out),
                "--allow-draft",
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse((out / "form-open.docx").exists(), "旧层产物应被清理")
            self.assertTrue((out / "form-candidates.docx").is_file())


class ManifestSchemaTest(unittest.TestCase):
    """manifest 严格 schema 单测（fail-closed，不依赖 pandoc）。"""

    def _manifest(self, payload: str, td) -> Path:
        p = Path(td) / MANIFEST_NAME
        p.write_text(payload, encoding="utf-8")
        return p

    def test_valid_manifest_loads(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._manifest('{"files": {"form-open.docx": "' + "a" * 64 + '"}}', td)
            self.assertEqual(load_manifest(p), {"form-open.docx": "a" * 64})

    def test_empty_or_malformed_refused(self):
        """空 files / 类型错 / 路径穿越 key / 坏 hash 都视为无所有权凭证。"""
        with tempfile.TemporaryDirectory() as td:
            for payload in (
                '{"files": {}}',
                '{"files": []}',
                "[]",
                "not json",
                '{"files": {"../escape.docx": "' + "a" * 64 + '"}}',
                '{"files": {"a/b.docx": "' + "a" * 64 + '"}}',
                '{"files": {"ok.docx": "nothex"}}',
            ):
                p = self._manifest(payload, td)
                self.assertIsNone(load_manifest(p), payload)


class FinalizedGateTest(unittest.TestCase):
    """定稿闸门契约单测（纯函数，不依赖 pandoc）。"""

    TITLES = "\n".join(f"## cand-{i:02d} 【类】候选 {i}" for i in range(1, 13))

    def _section(self, status: str, subset: str, header_draft: bool = True) -> str:
        banner = "**状态：DRAFT——说明**" if header_draft else "**状态：FINAL——说明**"
        return (
            f"# 头部\n> {banner}\n\n{self.TITLES}\n\n## 挑选记录（主人定稿区）\n\n"
            f"- 候选池状态：{status}\n- 必核子集：{subset}\n- 定稿依据与日期：2026-09-11\n\n"
            "> 机器闸门说明（含「cand-01」示例与占位说明文字，不参与解析）\n"
        )

    def test_final_with_8_to_12_picks_passes(self):
        picks = "、".join(f"cand-{i:02d}" for i in range(1, 9))
        self.assertTrue(candidates_finalized(self._section("FINAL", picks, header_draft=False)))
        picks12 = "、".join(f"cand-{i:02d}" for i in range(1, 13))
        self.assertTrue(candidates_finalized(self._section("FINAL", picks12, header_draft=False)))

    def test_header_still_draft_fails(self):
        """挑选区已定稿但头部横幅仍 DRAFT 时拒绝（防导出物自相矛盾）。"""
        picks = "、".join(f"cand-{i:02d}" for i in range(1, 9))
        self.assertFalse(candidates_finalized(self._section("FINAL", picks, header_draft=True)))

    def test_picks_must_be_real_candidates(self):
        """勾选不存在的候选编号必须拒绝（P1-2 回归）。"""
        ghosts = "、".join(f"cand-{i:02d}" for i in range(81, 89))
        self.assertFalse(candidates_finalized(self._section("FINAL", ghosts, header_draft=False)))

    def test_duplicate_pick_section_refused(self):
        """插入重复「挑选记录」区块（伪造 FINAL 区在前）必须拒绝（R8-P1 回归）。"""
        picks = "、".join(f"cand-{i:02d}" for i in range(1, 9))
        fake = (
            "## 挑选记录（伪造）\n\n- 候选池状态：FINAL\n"
            f"- 必核子集：{picks}\n- 定稿依据与日期：2026\n\n"
        )
        real = self._section("DRAFT", "待定", header_draft=False)
        self.assertFalse(candidates_finalized(fake + real))
        self.assertNotEqual(pick_section_problems(fake + real), [])

    def test_real_template_final_passes(self):
        """真实 form-candidates.md 模板按定稿契约填好后必须可导出（P1-1 回归：
        说明文字/池规模/示例编号不参与判定）。"""
        real = (ROOT / "specs/review/form-candidates.md").read_text(encoding="utf-8")
        finalized = (
            real.replace(
                "**状态：DRAFT（候选池草案，必核子集未定稿）**", "**状态：FINAL（必核子集已定稿）**"
            )
            .replace("- 候选池状态：DRAFT", "- 候选池状态：FINAL")
            .replace(
                "- 必核子集：待定", "- 必核子集：" + "、".join(f"cand-{i:02d}" for i in range(1, 9))
            )
            .replace("- 定稿依据与日期：待定", "- 定稿依据与日期：2026-09-11 主人挑选")
        )
        self.assertTrue(
            candidates_finalized(finalized), finalized[finalized.find("## 挑选记录") :][:400]
        )

    def test_draft_or_missing_or_pending_fails(self):
        self.assertFalse(candidates_finalized(self._section("DRAFT", "cand-01、cand-02")))
        self.assertFalse(candidates_finalized(self._section("FINAL", "待定")))
        self.assertFalse(candidates_finalized("# 无挑选记录区\n候选池状态：FINAL\n"))

    def test_pick_count_out_of_range_fails(self):
        picks7 = "、".join(f"cand-{i:02d}" for i in range(1, 8))
        self.assertFalse(candidates_finalized(self._section("FINAL", picks7)))
        picks13 = "、".join(f"cand-{i:02d}" for i in range(1, 14))
        self.assertFalse(candidates_finalized(self._section("FINAL", picks13)))
        self.assertFalse(candidates_finalized(self._section("FINAL", "、".join(["cand-01"] * 9))))

    @unittest.skipUnless(HAS_PANDOC, "端到端导出路径需要 pandoc")
    def test_empty_files_manifest_blocks_export(self):
        """被篡改为空 files 的 manifest 必须让导出拒绝（R6-P1 回归）。"""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "export"
            r = run_export("--layer", "open", "--output-dir", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            (out / MANIFEST_NAME).write_text('{"files": {}}', encoding="utf-8")
            victim = out / "form-open.docx"
            victim.write_bytes(b"user replaced")
            r = run_export("--layer", "open", "--output-dir", str(out))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("非法", r.stdout)
            self.assertEqual(victim.read_bytes(), b"user replaced")

    @unittest.skipUnless(HAS_PANDOC, "端到端导出路径需要 pandoc")
    def test_partial_manifest_refused(self):
        """合法 schema 但 files 集合与目录不一致（R7-P1 回归）→ 拒绝。"""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "export"
            r = run_export("--layer", "open", "--output-dir", str(out))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            # 篡改 manifest：只记录一个别的文件名（schema 合法）
            (out / MANIFEST_NAME).write_text(
                '{"files": {"other.docx": "' + "a" * 64 + '"}}', encoding="utf-8"
            )
            r = run_export("--layer", "open", "--output-dir", str(out))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("不一致", r.stdout)


@unittest.skipUnless(HAS_PANDOC, "本机未安装 pandoc，跳过导出用例")
class ExportCandidatesLayerTest(unittest.TestCase):
    def _picked_but_draft_pack(self, td: Path) -> Path:
        """已勾选 8–12 条但状态行仍 DRAFT 的材料副本（--allow-draft 的合法预览场景）。

        按行正则整体改写三个数据行与头部横幅，不依赖真实材料当前处于何种状态
        （真实材料 2026-09-13 已定稿 FINAL，占位串 replace 会静默落空）。
        """
        pack = Path(td) / "review"
        shutil.copytree(ROOT / "specs/review", pack)
        cand = pack / "form-candidates.md"
        text = cand.read_text(encoding="utf-8")
        picks = "、".join(f"cand-{i:02d}" for i in range(1, 9))
        text = re.sub(r"^- 候选池状态：.*$", "- 候选池状态：DRAFT", text, flags=re.MULTILINE)
        text = re.sub(r"^- 必核子集：.*$", f"- 必核子集：{picks}", text, flags=re.MULTILINE)
        text = re.sub(
            r"^- 定稿依据与日期：.*$", "- 定稿依据与日期：预览（主人未定稿）2026", text, flags=re.MULTILINE
        )
        text = re.sub(r"^> \*\*状态：.*$", "> **状态：DRAFT（fixture 预览场景）**", text, flags=re.MULTILINE, count=1)
        cand.write_text(text, encoding="utf-8", newline="\n")
        return pack

    def test_allow_draft_exports_picked_but_draft(self):
        """结构合法（已勾选）+ 状态 DRAFT：--allow-draft 放行、不带则拒绝。"""
        with tempfile.TemporaryDirectory() as td:
            pack = self._picked_but_draft_pack(Path(td))
            out = Path(td) / "export"
            r = run_export(
                "--layer", "candidates", "--review-dir", str(pack), "--output-dir", str(out)
            )
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("DRAFT", r.stdout)
            r = run_export(
                "--layer",
                "candidates",
                "--review-dir",
                str(pack),
                "--output-dir",
                str(out),
                "--allow-draft",
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            text = docx_text(out / "form-candidates.docx")
            self.assertIn("cand-01", text)
            self.assertIn("第二层", text)


if __name__ == "__main__":
    unittest.main()
