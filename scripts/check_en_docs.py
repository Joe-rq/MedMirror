#!/usr/bin/env python3
"""规则验证层：中英双语文档的一致性（声明锚点 / 字段表 / 互链 / 测试数）。

起因（issue #51）：英文 README 是国际评测研究者的第一入口，它与中文正本会各自漂移——
board 反复记录过同源漂移（测试数 175→186→236 手工刷 5 处、#11 状态过期刷 4 处），
中英双份文档正是下一个漂移源。而 issue 验收里最容易做假的一条是「对外声明合规」：
翻译时把「不输出未经专业复核的医学 Bias 结论」「14 条信任扩展未经独立标注」
「专业复核未回流」写弱或写没，肉眼很难发现。能用规则判的，绝不留给人判：

  1. 声明锚点成对：硬声明的中英锚点必须各自逐字出现在对应文档的**可见正文**里；
  2. 字段表覆盖一致：两份 CaseSpec 文档的表格首列标识符集合必须相等
     （漏译字段会让读者按英文文档填配置直接失败）；
  3. 中英互链存在：两个文档对互为入口，且必须是**真 Markdown 链接**
     （反引号里的 `](x.md)`、图片、转义方括号都不是入口）；
  4. 测试数处处一致：六份文档里手写的测试数必须同值
     （锚点见 TEST_COUNT_PATTERNS）。

**可见性判定（块级状态机 + 行内剥离）**：规则 1–3 只在「可见正文」里找命中。
不可见的块：围栏代码块（``` 与 ~~~，未闭合视为到文末）、缩进代码块（4 空格或 Tab 起）、
HTML 注释（未闭合同样到文末）、显式隐藏的 HTML 元素（任意标签带 hidden /
display:none / visibility:hidden，含未闭合到文末；`<style>`、`<script>` 一律整块不可见）。
规则 1、3 另剥离行内代码 span（含多反引号形式）——被引号包起来的一句声明是「被引用」，
不是「在说」；规则 2 的字段名本就写在行内代码里，不剥离。规则 4 例外：测试数写在
快速上手代码块的注释里（读者可见），故保留代码块，只去注释、隐藏元素与标签。

**残余边界（如实声明）**：本闸不做完整 Markdown/HTML 解析（本仓不引入依赖）。已覆盖
上述常见遮蔽手法；外链样式表定义的隐藏类、JS 运行时才隐藏的元素，以及把声明藏进图片
alt 之类的极端手法**仍在射程外**——那些靠人读对照兜底。另两处**已知的行为边界**（不是
「处理不了」，而是按本脚本的口径算作可见）：`<template>` / `<svg>` 的标签会被剥掉、
**内容留在可见区**（浏览器未必渲染它）；锚点**跨行拆开**算不命中（渲染后读者能拼起来，
本闸不拼）。CI 全绿 = 这四类规则在覆盖范围内成立，不等于「声明一定可见、数字一定为真、
全仓无漂移」。

**覆盖边界（如实声明）**：本闸只比对 README×2 与 CaseSpec×2 两份文档对，外加
TEST_COUNT_PATTERNS 列出的六份文档里的测试数。它**不覆盖** plan/003、judge-entry、
素材稿、onboarding 里的其它手写数字（成本 0.3720/0.0690/0.4746、27/24/3、18 条 8/6/4…），
也**不与代码 schema 对账**（CaseSpec 字段全集的正本在 `src/medmirror/casespec.py`）。
规则 4 只保证「各处写法一致」，**不保证这个数就是真实用例数**（真值以 `uv run pytest` 为准）。

**机械检查的边界**：本脚本不判断译文是否通顺、不判断中英两句话在语义上是否等价——
那属语义判断，靠人读对照兜底。锚点是刻意钉死的字面串：改措辞会让本闸红灯，改完请同步
更新本脚本的锚点表。这是有意的摩擦，防的是「顺手改一句就把声明改弱」。英文锚点是本
PR 的译法（canonical 正本在中文），改英文措辞同样要同步锚点表。

用法：python3 scripts/check_en_docs.py [--root 仓库根]
退出码 0 = 全绿，1 = 有错。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 根文档对（中文正本, 英文版）
README_PAIR = ("README.md", "README.en.md")

# 声明锚点：(中文锚点, 英文锚点)；两份文件取自 README_PAIR
DECLARATIONS = [
    ("不输出未经专业复核的医学 Bias 结论", "no medical-bias verdict without professional review"),
    ("14 条信任扩展未经独立标注", "were accepted without independent annotation"),
    ("专业复核未回流", "professional review has not returned"),
    ("不是医学等价对照", "not medically equivalent controls"),
]

# 中英文档对：(中文正本, 英文版)——规则 3（互链）作用于每一对
DOC_PAIRS = [
    README_PAIR,
    ("configs/cases/README.md", "configs/cases/README.en.md"),
]

# 规则 2（字段表覆盖一致）只作用于带字段表的文档对
FIELD_TABLE_PAIRS = [
    ("configs/cases/README.md", "configs/cases/README.en.md"),
]

# 测试数锚点：逐文件列出该文件里测试数的写法（改措辞即红灯，同步改这里）。
# 全表命中的数值必须彼此相等——加一份新文档就是加一行，比较逻辑不用改。
TEST_COUNT_PATTERNS: dict[str, list[str]] = {
    "README.md": [r"闸3 逻辑（(\d+) 用例）", r"(\d+) 项(?:离线)?测试"],
    "README.en.md": [r"(\d+) tests"],
    "docs/onboarding/README.md": [r"#\s*(\d+) passed"],
    "docs/plan/003_post-hackathon-roadmap.md": [r"pytest (\d+)"],
    "docs/report/001_tech-report-materials.md": [r"(\d+) 项离线测试"],
    "docs/reviews/judge-entry.md": [r"\*\*(\d+) 项离线测试\*\*"],
}

FENCE_LINE_RE = re.compile(r"^[ \t]*([`~]{3,})")
INDENT_CODE_RE = re.compile(r"^(?: {4,}|\t)")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
UNCLOSED_COMMENT_RE = re.compile(r"<!--.*\Z", re.DOTALL)
SCRIPT_STYLE_RE = re.compile(r"<(style|script)\b.*?</\1\s*>", re.DOTALL | re.IGNORECASE)
HIDDEN_OPEN_RE = re.compile(
    r"<([a-zA-Z][\w-]*)\b[^>]*(?:hidden\b|display\s*:\s*none|visibility\s*:\s*hidden)[^>]*>",
    re.IGNORECASE,
)
HTML_TAG_RE = re.compile(r"<[^>\n]*>")
CODE_SPAN_RE = re.compile(r"(`+)(?:[^`]|(?!\1)`)*?\1")
# 链接目标：](...) —— 锚点匹配时整段去掉，只留链接文字
LINK_TARGET_RE = re.compile(r"\]\([^)\s]*\)")
MD_LINK_RE = re.compile(r"(?<![!\\])\[[^\]]*\]\(([^)\s]+)\)")
QUOTE_PREFIX_RE = re.compile(r"^[ \t]*>+[ \t]?")
# 字段名：表格首列的反引号标识符（GFM 首尾竖线可省）
FIELD_ROW_RE = re.compile(r"^[ \t]*\|?[ \t]*`([A-Za-z_][\w.]*)`[ \t]*\|")
SEPARATOR_ROW_RE = re.compile(
    r"^[ \t]*\|?(\s*:?-{2,}:?\s*\|)+\s*$|^[ \t]*:?-{2,}:?(\s*\|\s*:?-{2,}:?)+[ \t]*\|?[ \t]*$"
)


def strip_code_blocks(text: str) -> str:
    """去掉围栏代码块（```/~~~，未闭合到文末）与缩进代码块（4 空格 / Tab 起）。"""
    out: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        m = FENCE_LINE_RE.match(line)
        if fence is None:
            if m:
                fence = (m.group(1)[0], len(m.group(1)))
                continue
            if INDENT_CODE_RE.match(line):
                continue
            out.append(line)
            continue
        if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]:
            fence = None
    return "\n".join(out)


def strip_hidden_html(text: str) -> str:
    """去掉 HTML 注释、style/script 块、显式隐藏元素（未闭合者到文末），再去掉其余标签。"""
    text = HTML_COMMENT_RE.sub("", text)
    text = UNCLOSED_COMMENT_RE.sub("", text)
    text = SCRIPT_STYLE_RE.sub("", text)
    while True:
        m = HIDDEN_OPEN_RE.search(text)
        if not m:
            break
        text = text[: m.start()] + _rest_after_element(text, m)
    return HTML_TAG_RE.sub("", text)


def _rest_after_element(text: str, opening: re.Match[str]) -> str:
    """返回隐藏元素之后的部分；按同名标签计数配对，未闭合则到文末（嵌套安全）。"""
    name = re.escape(opening.group(1))
    pattern = re.compile(rf"<(/?){name}\b[^>]*>", re.IGNORECASE)
    depth, end = 1, None
    for mm in pattern.finditer(text[opening.end() :]):
        depth += -1 if mm.group(1) else 1
        if depth == 0:
            end = opening.end() + mm.end()
            break
    return text[end:] if end is not None else ""


def visible_text(text: str) -> str:
    """可见正文（块级）：去掉代码块、HTML 注释/隐藏元素/标签。"""
    return strip_hidden_html(strip_code_blocks(text))


def visible_prose(text: str) -> str:
    """可见正文再去行内代码——「被引号包起来的声明」与伪链接都不算数。"""
    return CODE_SPAN_RE.sub("", visible_text(text))


def anchor_body(text: str) -> str:
    """声明锚点的匹配域：可见正文去掉行内代码**与链接目标**。

    链接目标（`[说明](https://…/no-medical-bias-verdict…)`）读者要点开才看得到，
    不能当作「文档在声明」；只留链接文字参与锚点匹配（评审 P2）。
    """
    return LINK_TARGET_RE.sub("]", visible_prose(text))


def without_html(text: str) -> str:
    """只去注释/隐藏元素/标签，保留代码块（规则 4 用：代码块注释里的测试数读者可见）。"""
    return strip_hidden_html(text)


def markdown_links(text: str) -> list[str]:
    """可见正文里的真 Markdown 链接目标（排除图片、转义方括号、代码 span）。"""
    return MD_LINK_RE.findall(visible_prose(text))


def table_lines(text: str) -> list[str]:
    """剥掉引用块前缀后的行（引用块里的表格同样是表格）。"""
    return [QUOTE_PREFIX_RE.sub("", ln) for ln in text.splitlines()]


def is_table_row(line: str) -> bool:
    return line.count("|") >= 2 and (line.lstrip().startswith("|") or line.rstrip().endswith("|"))


def is_separator_row(line: str) -> bool:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c) for c in cells)


def table_block_flags(lines: list[str]) -> list[bool]:
    """标记表格块内的行：以「表头 + 分隔行」起，到空行为止（GFM 表格块）。

    整块都算表格上下文——块内连续多行即使都省掉首尾竖线也不会漏检
    （评审 R3：逐行邻接判定会漏掉块内第二行起的省竖线写法）。
    """
    flags = [False] * len(lines)
    i = 0
    while i < len(lines):
        if not is_separator_row(lines[i]):
            i += 1
            continue
        start = i - 1 if i > 0 else i
        j = i + 1
        while j < len(lines) and lines[j].strip():
            j += 1
        for k in range(start, j):
            flags[k] = True
        i = j
    return flags


def table_field_idents(text: str) -> set[str]:
    """只认「表格块内」的字段名——表外的 `` `x` | y `` 不算字段（防伪字段补集合）。"""
    lines = table_lines(visible_text(text))
    separators = {i for i, ln in enumerate(lines) if is_separator_row(ln)}
    in_block = table_block_flags(lines)
    idents: set[str] = set()
    for i, ln in enumerate(lines):
        if not in_block[i] or i in separators:
            continue
        m = FIELD_ROW_RE.match(ln)
        if m:
            idents.add(m.group(1))
    return idents


def unparsed_table_cells(text: str) -> list[int]:
    """列出「在表格里、但首列不是反引号字段名」的行号（跳过分隔行与表头行）。

    这类行对规则 2 隐形：中文正本加一行 `| **severity_note** | ... |` 或
    `severity_note | str | ...`（GFM 允许省首尾竖线，甚至两侧都省）、英文版不补，
    两侧解析结果都不含它，闸会假装一致。所以宁可红灯要求改成 `| `name` | ... |`。
    """
    lines = table_lines(visible_text(text))
    separators = {i for i, ln in enumerate(lines) if is_separator_row(ln)}
    headers = {i - 1 for i in separators if i >= 1}
    in_block = table_block_flags(lines)
    bad: list[int] = []
    for i, ln in enumerate(lines):
        if "|" not in ln or not in_block[i] or i in separators or i in headers:
            continue
        if not FIELD_ROW_RE.match(ln):
            bad.append(i + 1)
    return bad


def load_texts(root: Path, errors: list[str]) -> dict[str, str]:
    # 不变式：各规则表的文件都落在本加载集内（FIELD_TABLE_PAIRS 是 DOC_PAIRS 的子集）
    rels = sorted({p for pair in DOC_PAIRS for p in pair} | set(TEST_COUNT_PATTERNS))
    texts: dict[str, str] = {}
    for rel in rels:
        path = root / rel
        if not path.is_file():
            errors.append(f"{rel}: 文件不存在——中英文档对必须成对入库")
            continue
        texts[rel] = path.read_text(encoding="utf-8")
    return texts


def check_declarations(texts: dict[str, str], errors: list[str]) -> int:
    zh_rel, en_rel = README_PAIR
    for zh_anchor, en_anchor in DECLARATIONS:
        if zh_rel in texts and zh_anchor not in anchor_body(texts[zh_rel]):
            errors.append(f"{zh_rel}: 缺声明锚点「{zh_anchor}」——中文正本先被动过")
        if en_rel in texts and en_anchor not in anchor_body(texts[en_rel]):
            errors.append(
                f"{en_rel}: 缺声明锚点「{en_anchor}」（对应中文「{zh_anchor}」）"
                "——该声明在英文版里丢失或被写弱（验收：对外声明合规）"
            )
    return len(DECLARATIONS)


def check_field_tables(texts: dict[str, str], errors: list[str]) -> int:
    ok = 0
    for zh_rel, en_rel in FIELD_TABLE_PAIRS:
        if zh_rel not in texts or en_rel not in texts:
            continue
        for rel in (zh_rel, en_rel):
            bad = unparsed_table_cells(texts[rel])
            if bad:
                errors.append(
                    f"{rel}: 第 {'、'.join(map(str, bad))} 行像表格行但首列不是反引号字段名"
                    "——规则 2 看不见它，两侧不一致也能蒙混过关；改成 | `name` | … | 或移出表格"
                )
        zh = table_field_idents(texts[zh_rel])
        en = table_field_idents(texts[en_rel])
        if not zh:
            errors.append(f"{zh_rel}: 未解析到字段表首列标识符——字段表被改写？")
            continue
        only_zh, only_en = sorted(zh - en), sorted(en - zh)
        if only_zh or only_en:
            detail = []
            if only_zh:
                detail.append(f"英文版缺 {'、'.join(only_zh)}")
            if only_en:
                detail.append(f"英文版多 {'、'.join(only_en)}")
            errors.append(
                f"{en_rel}: 字段表与 {zh_rel} 不一致（{'；'.join(detail)}）"
                "——漏译字段会让读者按英文文档填配置直接失败"
            )
            continue
        ok += len(zh)
    return ok


def check_links(texts: dict[str, str], errors: list[str]) -> int:
    ok = 0
    for zh_rel, en_rel in DOC_PAIRS:
        if zh_rel not in texts or en_rel not in texts:
            continue
        zh_links, en_links = markdown_links(texts[zh_rel]), markdown_links(texts[en_rel])
        if Path(en_rel).name not in zh_links:
            errors.append(f"{zh_rel}: 缺英文版入口链接（{en_rel}）——须是真 Markdown 链接")
        if Path(zh_rel).name not in en_links:
            errors.append(f"{en_rel}: 缺中文版入口链接（{zh_rel}）——须是真 Markdown 链接")
        if Path(en_rel).name in zh_links and Path(zh_rel).name in en_links:
            ok += 1
    return ok


def check_test_counts(texts: dict[str, str], errors: list[str]) -> int:
    """全表命中的测试数必须彼此相等；一致则返回该数值，否则返回 0。"""
    values: set[int] = set()
    for rel, patterns in TEST_COUNT_PATTERNS.items():
        if rel not in texts:
            continue
        body = without_html(texts[rel])
        hits = {int(m) for pattern in patterns for m in re.findall(pattern, body)}
        if len(hits) != 1:
            errors.append(
                f"{rel}: 测试数锚点命中 {len(hits)} 个值 {sorted(hits)}"
                "——本文件内部就不自洽，或措辞已变，请同步锚点表"
            )
            continue
        values |= hits
    if len(values) != 1:
        errors.append(
            f"测试数各处不一致：{sorted(values)}"
            f"（{len(TEST_COUNT_PATTERNS)} 份文档）——同源刷新漏了一处（board 记录的旧病）"
        )
        return 0
    return next(iter(values))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root).resolve()

    errors: list[str] = []
    texts = load_texts(root, errors)

    decls = check_declarations(texts, errors)
    fields = check_field_tables(texts, errors)
    links = check_links(texts, errors)
    test_n = check_test_counts(texts, errors)

    if errors:
        for e in errors:
            print(f"✗ {e}")
        print(f"\n{len(errors)} 项不通过（检查 {len(texts)} 个文件）")
        return 1
    print(
        f"✓ 中英文档一致：{decls} 条声明锚点成对，{fields} 个字段标识符一致，"
        f"{links} 对互链，测试数 {test_n}（{len(TEST_COUNT_PATTERNS)} 份文档同值）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
