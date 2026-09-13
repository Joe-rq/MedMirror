#!/usr/bin/env python3
"""规则验证层：入库 Markdown 的合并卫生与仓库内引用完整性。

起因（真实事故）：PR #38 与 main 的冲突处置曾取「演进版整份覆盖」，
把 main 侧经 PR #37 查证过的四块内容静默删掉，而四闸全绿——当时的
闸门只验代码与结构，不验文档内容有没有被吃掉。能用规则判的，绝不留给人判：

  1. 冲突标记清零：`<<<<<<<` / `=======` / `>>>>>>>` 不得入库任何 Markdown
     （合并没做完就 push，CI 必须先红灯）；
  2. 仓库相对路径引用存在：文中反引号里的 `xxx/yyy.md|py|jsonl|json` 等
     必须真实存在（写错路径的定位命令等于把评委指向空处）；
  3. 行号区间引用在界内：`sed -n 'A,Bp' <path>` 的 A/B 不得超过该文件行数
     （文档改写后行号漂移会让「一条命令直达证据」失效）。

**机械检查的边界（如实声明）**：本脚本不判断内容是否完整、数字是否正确、
两版合并有没有丢信息——那属语义判断，靠逐块 diff 与人工复核兜底；
本脚本只拦「没解完的冲突」和「指不到的引用」这两类可判定的错。

用法：python3 scripts/check_docs.py [--root 仓库根]
退出码 0 = 全绿，1 = 有错。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git",
    ".venv",
    ".claude",
    "_tmp",
    "_build",
    "_archive",
    "node_modules",
    "resources",
    "export",
    "docs",
}
CONFLICT_RE = re.compile(r"^(<{7}|={7}|>{7})( |$)")
# 反引号内的仓库相对路径（带扩展名才算，避免把 `uv run pytest` 之类当路径）
PATH_RE = re.compile(r"`([A-Za-z0-9_][\w./*$-]*\.(?:md|py|jsonl|json|yml|yaml|toml|sh|txt|docx))`")
SED_RE = re.compile(r"sed -n '(\d+),(\d+)p' ([^\s`]+)")
# 允许「按模式定位」的路径片段（*、$、<...>）不做存在性校验，只需真实前缀
# 抽象名/占位名（模板与目录说明里的示例引用，本仓另有跳过目录中的 doc 模式文件）
ALLOW_NAMES = {
    "NNN_kebab-case.md",
    "001_kebab-case.md",
    "readme.md",
    "index.md",
    # 本目录的「待产出清单」：表格里列的是计划落位的文件名，不是已存在文件
    "positive.md",
    "negative.md",
    "lexicon.md",
    # 命名法示例（形如日期的档案示例名，本仓无此文件）
    "2026-07-16_界面审计.md",
    "20260728-禁用词.md",
}
ALLOW_GLOBS = ("*", "$", "<", "?", "[")


def iter_markdown(root: Path):
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def check_conflict_markers(path: Path, root: Path, errors: list[str]) -> None:
    rel = path.relative_to(root)
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if CONFLICT_RE.match(line):
            errors.append(f"{rel}:{lineno} 残留合并冲突标记（{line[:12]!r}）——先解冲突再提交")


def resolve(root: Path, path: Path, ref: str) -> Path | None:
    """把文档里的相对引用解析到真实文件；不存在返回 None。

    依次尝试：仓库根、文档所在目录、文档所在目录的父级。
    """
    if ref.startswith("/") or "://" in ref:
        return None
    for base in (root, path.parent, path.parent.parent):
        if (base / ref).exists():
            return base / ref
    return None


def check_refs(root: Path, path: Path, errors: list[str], plain: set[str]) -> None:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(root)
    for ref in sorted(set(PATH_RE.findall(text))):
        if ref.startswith("/") or "://" in ref:
            continue
        if any(ch in ref for ch in ALLOW_GLOBS):
            # 通配/占位引用：只校验最左的静态目录段真实存在
            head = ref.split("/", 1)[0]
            if any(ch in head for ch in ALLOW_GLOBS):
                continue
            if resolve(root, path, head) is None:
                errors.append(f"{rel}: 引用前缀不存在 {head}（源 {ref}）")
            continue
        if ref in ALLOW_NAMES:
            continue
        if resolve(root, path, ref) is None:
            if ref in plain:
                errors.append(
                    f"{rel}: 引用文件不存在 {ref}"
                    "（跨目录引用请写仓库根起的完整相对路径，避免读者定位不到）"
                )
                continue
            errors.append(f"{rel}: 引用路径不存在 {ref}")
    for start, end, target in SED_RE.findall(text):
        if any(ch in target for ch in ALLOW_GLOBS):
            continue  # 通配目标的行数无从校验，静态前缀已在上面查过
        resolved = resolve(root, path, target)
        if resolved is None or not resolved.is_file():
            continue  # 不存在已在上面报过
        total = sum(1 for _ in resolved.open(encoding="utf-8"))
        if int(start) < 1 or int(end) > total or int(start) > int(end):
            errors.append(
                f"{rel}: sed 区间 {start},{end} 越出 {target} 行数 {total}——行号漂移会让定位失效"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root).resolve()

    errors: list[str] = []
    files = list(iter_markdown(root))
    if not files:
        print(f"✗ {root} 下没找到任何 Markdown——路径写错？")
        return 1
    # 全仓文件名集合（仅用于把「路径没写全」和「文件不存在」分开报）
    plain = {
        p.name
        for p in root.rglob("*")
        if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(root).parts)
    }
    for path in files:
        check_conflict_markers(path, root, errors)
        check_refs(root, path, errors, plain)

    if errors:
        for e in errors:
            print(f"✗ {e}")
        print(f"\n{len(errors)} 项不通过（检查 {len(files)} 个 Markdown 文件）")
        return 1
    print(f"✓ 文档卫生通过：{len(files)} 个 Markdown 文件无冲突标记，仓库内引用与 sed 区间均在界内")
    return 0


if __name__ == "__main__":
    sys.exit(main())
