#!/usr/bin/env python3
"""规则验证层：中英双语文档的一致性（声明锚点 / 字段表 / 互链 / 测试数）。

起因（issue #51）：英文 README 是国际评测研究者的第一入口，它与中文正本会各自漂移——
board 反复记录过同源漂移（测试数 175→186→236 手工刷 5 处、#11 状态过期刷 4 处），
中英双份文档正是下一个漂移源。而 issue 验收里最容易做假的一条是「对外声明合规」：
翻译时把「不输出未经专业复核的医学 Bias 结论」「14 条信任扩展未经独立标注」
「专业复核未回流」写弱或写没，肉眼很难发现。能用规则判的，绝不留给人判：

  1. 声明锚点成对：三条硬声明的中英锚点必须各自逐字出现在对应文档的**可见正文**里；
  2. 字段表覆盖一致：两份 CaseSpec 文档的表格首列标识符集合必须相等
     （漏译字段会让读者按英文文档填配置直接失败）；
  3. 中英互链存在：两个文档对互为入口（入口被后续编辑吃掉即红灯）；
  4. 测试数处处一致：六份文档里手写的测试数必须同值
     （中文「闸3 逻辑（N 用例）」/「N 项测试」与英文「N tests」等锚点见 TEST_COUNT_PATTERNS）。

**可见性规则（评审 P2 修正）**：规则 1–3 只在**去掉围栏代码块与 HTML 注释之后**的正文里
找命中——否则把声明正文删掉、只在 ``` 块或 `<!-- -->` 里留一句，闸会假装通过。
规则 4 例外：测试数本来就写在快速上手代码块的注释里（读者可见），故用原文匹配。

**覆盖边界（如实声明）**：本闸只比对 README×2 与 CaseSpec×2 两份文档对，外加
TEST_COUNT_PATTERNS 列出的六份文档里的测试数。它**不覆盖** plan/003、judge-entry、
素材稿、onboarding 里的其它手写数字（成本 0.3720/0.0690/0.4746、27/24/3、18 条 8/6/4…），
也**不与代码 schema 对账**（CaseSpec 字段全集的正本在 `src/medmirror/casespec.py`）。
规则 4 只保证「各处写法一致」，**不保证这个数就是真实用例数**（真值以 `uv run pytest` 为准）——
六份文档一起写旧值仍然全绿。CI 全绿只说明这四类规则在覆盖范围内成立，
不等于全仓数字都没有漂移。

**机械检查的边界（如实声明）**：本脚本不判断译文是否通顺、不判断中英两句话在语义上
是否等价——那属语义判断，靠人读对照兜底。锚点是刻意钉死的字面串：改措辞会让本闸红灯，
改完请同步更新本脚本的锚点表。这是有意的摩擦，防的是「顺手改一句就把声明改弱」。
英文锚点是本 PR 的译法（canonical 正本在中文），改英文措辞同样要同步锚点表。
围栏计数为奇数（有未闭合的 ```）时，其后正文会被整段当作代码块——结果是红灯而非假绿，
先修文档格式。

用法：python3 scripts/check_en_docs.py [--root 仓库根]
退出码 0 = 全绿，1 = 有错。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 根文档对（中文正本, 英文版）——规则 1、4 的默认比对对象
README_PAIR = ("README.md", "README.en.md")

# 声明锚点：(中文锚点, 英文锚点)；两份文件取自 README_PAIR
DECLARATIONS = [
    ("不输出未经专业复核的医学 Bias 结论", "no medical bias verdict"),
    ("14 条信任扩展未经独立标注", "were accepted without independent annotation"),
    ("专业复核未回流", "professional review has not returned"),
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

# 字段表首列的标识符（如 | `case_id` | str | ... |）
FIELD_ROW_RE = re.compile(r"^\|\s*`([A-Za-z_][\w.]*)`\s*\|")
# 表格行 / 表头分隔行（|---|---|）
TABLE_ROW_RE = re.compile(r"^\|.*\|\s*$")
SEPARATOR_ROW_RE = re.compile(r"^\|(\s*:?-{2,}:?\s*\|)+\s*$")
# 围栏代码块与 HTML 注释——不算可见正文
FENCE_RE = re.compile(r"^[ \t]*```.*?^[ \t]*```", re.DOTALL | re.MULTILINE)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def visible_text(text: str) -> str:
    """去掉围栏代码块与 HTML 注释：声明、互链、字段表只认可见正文里的命中。"""
    return HTML_COMMENT_RE.sub("", FENCE_RE.sub("", text))


def unparsed_table_cells(text: str) -> list[int]:
    """列出「像表格行、但首列不是反引号字段名」的行号（跳过分隔行与表头行）。

    这类行对规则 2 隐形：中文正本加一行 `| **severity_note** | ... |`、英文版不补，
    两侧解析结果都不含它，闸会假装一致。所以宁可红灯要求改成 `| `name` | ... |`。
    """
    lines = text.splitlines()
    separators = {i for i, ln in enumerate(lines) if SEPARATOR_ROW_RE.match(ln)}
    headers = {i - 1 for i in separators if i >= 1}
    return [
        i + 1
        for i, ln in enumerate(lines)
        if i not in separators
        and i not in headers
        and TABLE_ROW_RE.match(ln)
        and not FIELD_ROW_RE.match(ln)
    ]


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
        if zh_rel in texts and zh_anchor not in visible_text(texts[zh_rel]):
            errors.append(f"{zh_rel}: 缺声明锚点「{zh_anchor}」——中文正本先被动过")
        if en_rel in texts and en_anchor not in visible_text(texts[en_rel]):
            errors.append(
                f"{en_rel}: 缺声明锚点「{en_anchor}」（对应中文「{zh_anchor}」）"
                "——该声明在英文版里丢失或被写弱（验收：对外声明合规）"
            )
    return len(DECLARATIONS)


def field_idents(text: str) -> set[str]:
    return {m.group(1) for line in text.splitlines() if (m := FIELD_ROW_RE.match(line))}


def check_field_tables(texts: dict[str, str], errors: list[str]) -> int:
    ok = 0
    for zh_rel, en_rel in FIELD_TABLE_PAIRS:
        if zh_rel not in texts or en_rel not in texts:
            continue
        for rel in (zh_rel, en_rel):
            bad = unparsed_table_cells(visible_text(texts[rel]))
            if bad:
                errors.append(
                    f"{rel}: 第 {'、'.join(map(str, bad))} 行像表格行但首列不是反引号字段名"
                    "——规则 2 看不见它，两侧不一致也能蒙混过关；改成 | `name` | … | 或移出表格"
                )
        zh = field_idents(visible_text(texts[zh_rel]))
        en = field_idents(visible_text(texts[en_rel]))
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
        zh_link, en_link = f"]({Path(en_rel).name})", f"]({Path(zh_rel).name})"
        if zh_link not in visible_text(texts[zh_rel]):
            errors.append(f"{zh_rel}: 缺英文版入口链接（{en_rel}）")
        if en_link not in visible_text(texts[en_rel]):
            errors.append(f"{en_rel}: 缺中文版入口链接（{zh_rel}）")
        if zh_link in visible_text(texts[zh_rel]) and en_link in visible_text(texts[en_rel]):
            ok += 1
    return ok


def check_test_counts(texts: dict[str, str], errors: list[str]) -> int:
    """全表命中的测试数必须彼此相等；一致则返回该数值，否则返回 0。"""
    values: set[int] = set()
    for rel, patterns in TEST_COUNT_PATTERNS.items():
        if rel not in texts:
            continue
        hits = {int(m) for pattern in patterns for m in re.findall(pattern, texts[rel])}
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
