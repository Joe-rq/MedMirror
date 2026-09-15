#!/usr/bin/env python3
"""规则验证层：中英双语文档的一致性（声明锚点 / 字段表 / 互链 / 测试数）。

起因（issue #51）：英文 README 是国际评测研究者的第一入口，它与中文正本会各自漂移——
board 反复记录过同源漂移（测试数 175→186→236 手工刷 5 处、#11 状态过期刷 4 处），
中英双份文档正是下一个漂移源。而 issue 验收里最容易做假的一条是「对外声明合规」：
翻译时把「不输出未经专业复核的医学 Bias 结论」「14 条信任扩展未经独立标注」
「专业复核未回流」写弱或写没，肉眼很难发现。能用规则判的，绝不留给人判：

  1. 声明锚点成对：三条硬声明的中英锚点必须各自逐字出现在对应文档里；
  2. 字段表覆盖一致：两份 CaseSpec 文档的表格首列标识符集合必须相等
     （漏译字段会让读者按英文文档填配置直接失败）；
  3. 中英互链存在：两个文档对互为入口（入口被后续编辑吃掉即红灯）；
  4. 测试数中英一致：中文「闸3 逻辑（N 用例）」与英文「N tests」的 N 必须相等。

**机械检查的边界（如实声明）**：本脚本不判断译文是否通顺、不判断中英两句话在语义上
是否等价——那属语义判断，靠人读对照兜底。锚点是刻意钉死的字面串：改措辞会让本闸红灯，
改完请同步更新本脚本的锚点表。这是有意的摩擦，防的是「顺手改一句就把声明改弱」。

用法：python3 scripts/check_en_docs.py [--root 仓库根]
退出码 0 = 全绿，1 = 有错。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 声明锚点：(声明名, 中文文件, 中文锚点, 英文文件, 英文锚点)
DECLARATIONS = [
    (
        "不输出未经专业复核的医学 Bias 结论",
        "README.md",
        "不输出未经专业复核的医学 Bias 结论",
        "README.en.md",
        "no medical bias verdict",
    ),
    (
        "14 条信任扩展未经独立标注",
        "README.md",
        "14 条信任扩展未经独立标注",
        "README.en.md",
        "were accepted without independent annotation",
    ),
    (
        "专业复核未回流",
        "README.md",
        "专业复核未回流",
        "README.en.md",
        "professional review has not returned",
    ),
]

# 中英文档对：(中文正本, 英文版)——规则 3（互链）作用于每一对
DOC_PAIRS = [
    ("README.md", "README.en.md"),
    ("configs/cases/README.md", "configs/cases/README.en.md"),
]

# 规则 2（字段表覆盖一致）只作用于带字段表的文档对
FIELD_TABLE_PAIRS = [
    ("configs/cases/README.md", "configs/cases/README.en.md"),
]

# 测试数锚点：两侧各须命中，且数值相等（改措辞即红灯，同步改这里）
TEST_COUNT_PATTERNS = {
    "README.md": r"闸3 逻辑（(\d+) 用例）",
    "README.en.md": r"(\d+) tests",
}

# 字段表首列的标识符（如 | `case_id` | str | ... |）
FIELD_ROW_RE = re.compile(r"^\|\s*`([A-Za-z_][\w.]*)`\s*\|")


def load_texts(root: Path, errors: list[str]) -> dict[str, str]:
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
    ok = 0
    for name, zh_rel, zh_anchor, en_rel, en_anchor in DECLARATIONS:
        if zh_rel in texts and zh_anchor not in texts[zh_rel]:
            errors.append(f"{zh_rel}: 缺声明锚点「{zh_anchor}」（{name}）——中文正本先被动过")
        if en_rel in texts and en_anchor not in texts[en_rel]:
            errors.append(
                f"{en_rel}: 缺声明锚点「{en_anchor}」（{name}）"
                "——该声明在英文版里丢失或被写弱（验收：对外声明合规）"
            )
        if zh_rel in texts and en_rel in texts:
            ok += 1
    return ok


def field_idents(text: str) -> set[str]:
    return {m.group(1) for line in text.splitlines() if (m := FIELD_ROW_RE.match(line))}


def check_field_tables(texts: dict[str, str], errors: list[str]) -> int:
    ok = 0
    for zh_rel, en_rel in FIELD_TABLE_PAIRS:
        if zh_rel not in texts or en_rel not in texts:
            continue
        zh, en = field_idents(texts[zh_rel]), field_idents(texts[en_rel])
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
        if zh_link not in texts[zh_rel]:
            errors.append(f"{zh_rel}: 缺英文版入口链接（{en_rel}）")
        if en_link not in texts[en_rel]:
            errors.append(f"{en_rel}: 缺中文版入口链接（{zh_rel}）")
        if zh_link in texts[zh_rel] and en_link in texts[en_rel]:
            ok += 1
    return ok


def check_test_counts(texts: dict[str, str], errors: list[str]) -> tuple[int, int]:
    found: dict[str, set[int]] = {}
    for rel, pattern in TEST_COUNT_PATTERNS.items():
        if rel not in texts:
            continue
        values = {int(m) for m in re.findall(pattern, texts[rel])}
        if len(values) != 1:
            errors.append(
                f"{rel}: 测试数锚点（{pattern}）命中 {len(values)} 个值 {sorted(values)}"
                "——本文件内部就不自洽，或措辞已变，请同步锚点表"
            )
            continue
        found[rel] = values
    if len(found) != len(TEST_COUNT_PATTERNS):
        return 0, 0
    zh_rel, en_rel = "README.md", "README.en.md"
    zh_n, en_n = found[zh_rel].pop(), found[en_rel].pop()
    if zh_n != en_n:
        errors.append(
            f"测试数中英不一致：{zh_rel} 写 {zh_n}、{en_rel} 写 {en_n}"
            "——同源刷新漏了一处（board 记录的旧病）"
        )
        return 0, zh_n
    return 1, zh_n


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root).resolve()

    errors: list[str] = []
    texts = load_texts(root, errors)
    if not texts:
        for e in errors:
            print(f"✗ {e}")
        return 1

    decls = check_declarations(texts, errors)
    fields = check_field_tables(texts, errors)
    links = check_links(texts, errors)
    _, test_n = check_test_counts(texts, errors)

    if errors:
        for e in errors:
            print(f"✗ {e}")
        print(f"\n{len(errors)} 项不通过（检查 {len(texts)} 个文件）")
        return 1
    print(
        f"✓ 中英文档一致：{decls} 条声明锚点成对，{fields} 个字段标识符一致，"
        f"{links} 对互链，测试数 {test_n}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
