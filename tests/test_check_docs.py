"""文档卫生闸（scripts/check_docs.py）的规则层回归。

起因：PR #38 与 main 的冲突处置取「演进版整份覆盖」，把 main 侧经查证的
内容静默删掉，而当时四闸全绿——闸门不覆盖文档。本闸只拦两类可判定的错：
未解完的冲突标记、指不到的仓库内引用（含 sed 行号越界）。
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_docs.py", "--root", str(root)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=120,
    )


class CheckDocsGateTest(unittest.TestCase):
    # 沙箱里固定用 sandbox/docs/ 存文档：排除 docs/ 是为了跳过本项目的历史
    # 研究档案，跨树复用时不应把宿主仓的档案当测试目标
    def _repo_copy(self, docs: dict[str, str], extra: dict[str, str] | None = None) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for rel, body in {**docs, **(extra or {})}.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return root

    def test_committed_repo_passes(self):
        r = run_gate(ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("文档卫生通过", r.stdout)

    def test_conflict_marker_fails(self):
        """合并没解完就提交，必须红灯——这条正是 PR #38 事故的前置条件。"""
        root = self._repo_copy(
            {
                "sandbox/a.md": (
                    "# 标题\n<<<<<<< HEAD\n取演进版\n=======\nmain 侧内容\n>>>>>>> origin/main\n"
                )
            }
        )
        r = run_gate(root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("残留合并冲突标记", r.stdout)
        # 三种标记都要被点名，别只抓开头那种
        self.assertIn("=======", r.stdout)
        self.assertIn(">>>>>>>", r.stdout)

    def test_seven_char_non_marker_line_is_clean(self):
        """正文里七连字符/等号的正常排版不得误报。"""
        root = self._repo_copy({"sandbox/a.md": "# t\n\n--------- 分隔线\n===== 另一处\n"})
        r = run_gate(root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_sibling_ref_fails(self):
        """跨目录引用写裸文件名：读者点不到，闸门判红灯并提示写全路径。"""
        root = self._repo_copy(
            {
                "sandbox/a.md": "见 `source-verification.md`\n",
                "sandbox/experiments/followup/source-verification.md": "# 真实存在但不在同目录\n",
            }
        )
        r = run_gate(root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("引用文件不存在 source-verification.md", r.stdout)
        self.assertIn("完整相对路径", r.stdout)

    def test_repo_root_ref_and_sibling_ref_pass(self):
        """仓库根起的完整路径、以及同目录裸文件名，都算命中。"""
        root = self._repo_copy(
            {
                "sandbox/a.md": "见 `sandbox/b.md` 与 `b.md`\n",
                "sandbox/b.md": "# b\n",
            }
        )
        r = run_gate(root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_absolute_missing_ref_fails(self):
        root = self._repo_copy({"sandbox/a.md": "见 `docs/nope.md`\n"})
        r = run_gate(root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("引用路径不存在 docs/nope.md", r.stdout)

    def test_sed_range_out_of_bounds_fails(self):
        """文档改写导致行号漂移，定位命令会失效——机械可查，必须拦。"""
        root = self._repo_copy(
            {
                "sandbox/a.md": "```bash\nsed -n '1,999p' sandbox/b.md\n```\n",
                "sandbox/b.md": "# b\n只有两行\n",
            }
        )
        r = run_gate(root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("sed 区间 1,999 越出 sandbox/b.md 行数 2", r.stdout)

    def test_sed_range_in_bounds_passes(self):
        root = self._repo_copy(
            {
                "sandbox/a.md": "```bash\nsed -n '1,2p' sandbox/b.md\n```\n",
                "sandbox/b.md": "# b\n只有两行\n",
            }
        )
        r = run_gate(root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_glob_and_placeholder_refs_skipped(self):
        """通配与占位名（模板示例）不参与存在性校验，只查静态前缀。"""
        root = self._repo_copy(
            {
                "sandbox/a.md": "见 `runs/x/*/budget.jsonl`、`NNN_kebab-case.md`、`positive.md`\n",
                "runs/x/2026/budget.jsonl": "{}\n",
            }
        )
        r = run_gate(root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_glob_static_prefix_missing_fails(self):
        root = self._repo_copy({"sandbox/a.md": "见 `nosuchdir/*/x.md`\n"})
        r = run_gate(root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("引用前缀不存在 nosuchdir", r.stdout)

    def test_empty_root_fails(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        r = run_gate(Path(tmp.name))
        self.assertEqual(r.returncode, 1)
        self.assertIn("没找到任何 Markdown", r.stdout)


if __name__ == "__main__":
    unittest.main()
