#!/usr/bin/env python3
"""规则验证层：校验 specs/review/ 医学复核材料包（issue #20）。

能用规则判的绝不留给人判：
  1. 必需文件齐全（七件材料 + 附件目录按源派生的分组文件 + index.md）；
  2. trial 全集一致：form-open、record、attachments、index 与 trials.jsonl 相等（行级计数 + 唯一），
     源本身 status=success 且 finish∈{stop,length}；
  3. 原文完整：附件 fence 内正文与 response 逐字一致（仅容忍文件级换行结构，不剥行尾空白），
     附件提问行、元信息行、截断标注均与源一致；
  4. 判定后置：form-open.md 不含研究判定词，也不得夹带候选标题（候选措辞属第二层）；
  5. 引文可定位：form-candidates.md 的「引文」（trial_id）逐字子串于该 trial 原文，
     形状可疑（半/全角括号手偏）显式报错，每候选小节至少一条引文；
  6. case-card 三种问法按变体归属逐字等于协议 VARIANTS；
  7. 无密钥模式；合成病例声明在场；复核表意见/跳过栏在场。

**机械检查的边界（如实声明）**：候选主张正文的改写泄漏（非标题逐字）无法机械比对，
属语义判断，由人工评审兜底；FORBIDDEN_IN_OPEN 词表是该判断的可机械化投影，非全集。

脚本通过只证明结构与原文自洽，不证明候选问题措辞恰当（研究判断归主人，issue #20）。

用法：uv run python scripts/check_review_pack.py [--root 仓库根] [--trials trials.jsonl]
退出码 0 = 全绿，1 = 有错。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from medmirror.protocol import load_jsonl  # noqa: E402
from medmirror.runner import VARIANTS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR_NAME = "specs/review"

REQUIRED_FILES = [
    "README.md",
    "background.md",
    "case-card.md",
    "form-open.md",
    "form-candidates.md",
    "boundaries.md",
    "record.md",
]
# form-open（第一层）禁用的研究判定措辞：出现即视为把判定带进了开放式层
FORBIDDEN_IN_OPEN = [
    "呈现差异",
    "提示敏感",
    "Bias",
    "偏见",
    "符合预期",
    "研究观察一致",
    "支持率",
    "提及率",
    "偏向",
    "差异显著",
]
# trial_id 片段与截断标记：单一来源，全部正则由此组装
TRIAL_ID = r"exp003-[a-z0-9][a-z0-9._\-]*\d"
TRIAL_ID_PREFIX = "exp003-"
TRIAL_ID_RE = re.compile(rf"({TRIAL_ID})")
# 与 gen_review_attachments.py 的附件/form-open 标题标记保持同一拼法
TRUNC_FLAG = r"（\*\*⚠ 截断条目\*\*）"
TRIAL_HEAD_RE = re.compile(rf"^#+ ({TRIAL_ID})({TRUNC_FLAG})?\s*$", re.MULTILINE)
META_RE = re.compile(r"^- 元信息：(\S+) · (\S+) · 第 (\d+) 次重复 · finish=(\S+)$", re.MULTILINE)
# record 表数据行（行级解析后另校验列数与状态列非空，防删列假绿）
RECORD_ROW_RE = re.compile(rf"^\| ({TRIAL_ID}) \|", re.MULTILINE)
# index 表格数据行中的反引号 id（行级计数用，正文藏 id 会计数偏多而红灯）
INDEX_ID_RE = re.compile(rf"`({TRIAL_ID})`")
CAND_TITLE_RE = re.compile(r"^#{2,3} (cand-\d+ .+)$", re.MULTILINE)
# 引文捕获组不含 」（引文本身不应嵌套右引号），防止同行多引文/嵌套时错捕错归因
QUOTE_LINE_RE = re.compile(rf"^\s*-\s*「([^」]+)」\s*（({TRIAL_ID})）\s*$", re.MULTILINE)
KEY_SECRET_RE = re.compile(r"sk-[A-Za-z0-9]{16,}|Bearer\s+[A-Za-z0-9._\-]{16,}")
# case-card 问法表数据行：| `variant` | 提示全文 |
CASE_ROW_RE = re.compile(r"^\|\s*`(\w+)`\s*\|\s*(\S.*?)\s*\|\s*$", re.MULTILINE)

errors: list[str] = []
notes: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def load_trials(path: Path) -> dict[str, dict]:
    trials: dict[str, dict] = {}
    for row in load_jsonl(path):
        tid = row.get("trial_id")
        if tid is None:
            err(f"trials 源存在缺 trial_id 的行：{str(row)[:60]}…")
            continue
        if tid in trials:
            err(f"trials 源中 trial_id 重复：{tid}")
        trials[tid] = row
    return trials


def read_texts(review: Path) -> dict[str, str]:
    """一次读齐全部 md，后续检查复用同一份文本。

    相对路径统一用正斜杠：Windows 的 Path.relative_to 产生反斜杠，
    会让 startswith("attachments/") 类判断在 CI（Linux）与本地（Windows）分叉。
    """
    return {
        str(p.relative_to(review)).replace("\\", "/"): p.read_text(encoding="utf-8")
        for p in sorted(review.rglob("*.md"))
    }


def check_required_files(review: Path, texts: dict[str, str]) -> None:
    for name in REQUIRED_FILES:
        if name not in texts:
            err(f"缺必需文件 specs/review/{name}")
    if not any(n.startswith("attachments/") for n in texts):
        err("缺 specs/review/attachments/ 目录或其中没有 md 文件")
    elif "attachments/index.md" not in texts:
        err("缺 attachments/index.md")


def parse_open_sections(text: str) -> dict[str, dict]:
    """解析 form-open 的 ### 小节：{trial_id: {truncated, meta, fields_ok}}。"""
    sections: dict[str, dict] = {}
    heads = list(TRIAL_HEAD_RE.finditer(text))
    for i, m in enumerate(heads):
        tid = m.group(1)
        if tid in sections:
            err(f"form-open 中 {tid} 的小节重复出现")
        body = text[m.end() : heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        meta = META_RE.search(body)
        sections[tid] = {
            "truncated": bool(m.group(2)),
            "meta": meta.groups() if meta else None,
            # 复核入口必须存在：意见栏 + 跳过框；截断条目还须有截断说明行
            "fields_ok": (
                "- 复核意见：" in body
                and "- 跳过：[ ]" in body
                and (not m.group(2) or "该条回答因输出长度上限截断" in body)
            ),
        }
    return sections


def parse_attachments(texts: dict[str, str]) -> dict[str, dict]:
    """从附件文本提取 {trial_id: {truncated, meta, prompt, body}}。"""
    parsed: dict[str, dict] = {}
    for name, text in texts.items():
        if not name.startswith("attachments/") or name == "attachments/index.md":
            continue
        current: str | None = None
        current_flag = False
        collecting = False
        buf: list[str] = []
        prompts: list[str] = []
        body_head = ""
        for line in text.splitlines():
            if not collecting:
                m = re.match(rf"^## ({TRIAL_ID})({TRUNC_FLAG})?\s*$", line)
                if m:
                    current = m.group(1)
                    current_flag = bool(m.group(2))
                    prompts = []
                    body_head = ""
                elif line.strip() == "```text" and current:
                    collecting = True
                    buf = []
                elif current and line.startswith("  > "):
                    prompts.append(line[4:])
                else:
                    body_head += line + "\n"
            elif line.strip() == "```":
                if current in parsed:
                    err(f"{name} 中 {current} 的小节重复出现")
                parsed[current] = {
                    "truncated": current_flag,
                    "trunc_note": "该条回答因输出长度上限截断" in body_head,
                    "meta": None,
                    "file": name.split("/", 1)[1],
                    "prompt": "\n".join(prompts),
                    "body": "\n".join(buf),
                }
                collecting = False
            else:
                buf.append(line)
        if "合成" not in text:
            err(f"{name} 缺合成病例声明")
    return parsed


def attach_meta(texts: dict[str, str], parsed: dict[str, dict]) -> None:
    """把各附件的元信息行按小节归属填进 parsed（供与源比对）。"""
    for name, text in texts.items():
        if not name.startswith("attachments/") or name == "attachments/index.md":
            continue
        heads = list(TRIAL_HEAD_RE.finditer(text))
        for i, m in enumerate(heads):
            body = text[m.end() : heads[i + 1].start() if i + 1 < len(heads) else len(text)]
            meta = META_RE.search(body)
            if m.group(1) in parsed:
                parsed[m.group(1)]["meta"] = meta.groups() if meta else None


def check_open_layer(text: str, trials: dict[str, dict]) -> None:
    """第一层：trial 全集 + 截断标注 + 元信息/复核栏与源一致 + 禁判定词。"""
    sections = parse_open_sections(text)
    ids = set(trials)
    truncated = {t for t, r in trials.items() if r.get("finish_reason") == "length"}

    if set(sections) != ids:
        err(
            f"form-open 的 trial 集合与 trials.jsonl 不一致：缺 {sorted(ids - set(sections))}，"
            f"多 {sorted(set(sections) - ids)}"
        )

    for tid, sec in sections.items():
        src = trials.get(tid)
        if src is None:
            continue
        should = tid in truncated
        if sec["truncated"] and not should:
            err(f"form-open 中 {tid} 为 finish=stop 却标注了截断")
        if should and not sec["truncated"]:
            err(f"form-open 中 {tid} 为 finish=length 却未标注截断")
        if not sec["fields_ok"]:
            err(f"form-open 中 {tid} 缺「复核意见」或「跳过」栏（复核入口不完整）")
        if sec["meta"] is None:
            err(f"form-open 中 {tid} 缺「元信息」行")
            continue
        model, variant, index, finish = sec["meta"]
        expected = (
            src.get("model", ""),
            src.get("prompt_variant", ""),
            str(src.get("trial_index", "")),
            src.get("finish_reason") or "unknown",
        )
        if (model, variant, index, finish) != expected:
            err(f"form-open 中 {tid} 元信息行 {sec['meta']} 与源 {expected} 不一致")

    for word in FORBIDDEN_IN_OPEN:
        if word in text:
            err(f"form-open.md 出现研究判定措辞「{word}」——第一层必须保持开放式，判定词不得出现")


def check_candidate_leak(open_text: str, cand_text: str) -> None:
    for title in CAND_TITLE_RE.findall(cand_text):
        core = title.split("】", 1)[-1].strip()
        if core and core in open_text:
            err(f"form-open.md 夹带了候选标题「{title}」——候选措辞属第二层")


def check_candidates(text: str, trials: dict[str, dict]) -> None:
    quotes = QUOTE_LINE_RE.findall(text)
    if not quotes:
        err("form-candidates.md 未解析到任何「引文」（trial_id）行")
    for quote, tid in quotes:
        if tid not in trials:
            err(f"form-candidates.md 引用了未知 trial：{tid}")
        elif quote not in (trials[tid].get("response") or ""):
            err(f"form-candidates.md 引文未在 {tid} 原文中逐字定位：{quote[:40]}…")

    # 形状可疑的引文行显式报错：含「且含（/(exp003- 却不匹配 QUOTE_LINE_RE 的行，
    # 说明格式手偏后静默脱离了逐字校验（半角括号、同行多引文、嵌套引号等）
    for line in text.splitlines():
        s = line.strip()
        if (
            s.startswith("-")
            and "「" in s
            and (f"（{TRIAL_ID_PREFIX}" in s or f"({TRIAL_ID_PREFIX}" in s)
            and not QUOTE_LINE_RE.match(line)
        ):
            err(f"form-candidates.md 存在形状无法解析的引文行：{s[:60]}…")

    heads = list(CAND_TITLE_RE.finditer(text))
    cand_ids = [m.group(1).split(" ")[0] for m in heads]
    if len(set(cand_ids)) != len(cand_ids):
        err(f"form-candidates.md 候选编号重复：{cand_ids}")
    # 对账：每个候选小节至少一条引文行——防引文行格式手偏后被 QUOTE_LINE_RE 静默跳过
    for i, m in enumerate(heads):
        section = text[m.end() : heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        if not QUOTE_LINE_RE.search(section):
            err(f"form-candidates.md 的 {m.group(1).split(' ')[0]} 小节没有任何可解析的引文行")


def check_case_card(text: str) -> None:
    """问法表按变体归属逐字比对协议 VARIANTS——防 tcm/western 对调（仅验存在验不出）。"""
    rows = {variant: prompt for variant, prompt in CASE_ROW_RE.findall(text)}
    if set(rows) != set(VARIANTS):
        err(f"case-card.md 问法表变体集合 {sorted(rows)} 与协议不一致 {sorted(VARIANTS)}")
    for variant, prompt in VARIANTS.items():
        if variant in rows and rows[variant] != prompt:
            err(f"case-card.md 的 {variant} 行与协议 VARIANTS 逐字不一致（可能对调或改动）")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="仓库根目录（须为与协议常量同版本的仓库：VARIANTS 从脚本所在仓导入）",
    )
    parser.add_argument(
        "--trials",
        default=None,
        help="trials.jsonl 路径（默认 <root>/docs/experiments/exp003-baseline/result/trials.jsonl）",
    )
    parser.add_argument("--review-dir", default=None, help="材料包目录（默认 <root>/specs/review）")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    # 默认 trials 跟随 --root 解析（而非 import 期绑死本仓），跨树校验不张冠李戴
    trials_path = (
        Path(args.trials).resolve()
        if args.trials
        else root / "docs/experiments/exp003-baseline/result/trials.jsonl"
    )
    review = Path(args.review_dir).resolve() if args.review_dir else root / REVIEW_DIR_NAME

    if not trials_path.is_file():
        print(f"✗ 找不到 trials 源：{trials_path}")
        return 1
    trials = load_trials(trials_path)

    ids = set(trials)
    truncated = {t for t, r in trials.items() if r.get("finish_reason") == "length"}

    # 源侧合法性：纳入复核的条目必须是成功试次且 finish 口径明确（分母不失真）
    for tid, row in trials.items():
        if row.get("status") != "success":
            err(f"{tid} status={row.get('status')}，失败/未完成试次不得进入复核材料包")
        if row.get("finish_reason") not in ("stop", "length"):
            err(f"{tid} finish_reason={row.get('finish_reason')!r} 不在 stop/length 口径内")

    if not review.is_dir():
        print(f"✗ 找不到材料包目录：{review}")
        return 1
    texts = read_texts(review)
    check_required_files(review, texts)

    parsed = parse_attachments(texts)
    attach_meta(texts, parsed)

    # 附件文件集 = 源派生的分组文件 + index（合并/缺组/多文件都会在这里现形）
    expected_files = {f"{r['model']}-{r['prompt_variant']}.md" for r in trials.values()}
    actual_files = {
        n.split("/", 1)[1]
        for n in texts
        if n.startswith("attachments/") and n != "attachments/index.md"
    }
    if actual_files != expected_files:
        err(
            f"attachments 文件集合与源派生不一致：缺 {sorted(expected_files - actual_files)}，"
            f"多 {sorted(actual_files - expected_files)}"
        )

    if "attachments/index.md" in texts:
        index_ids = INDEX_ID_RE.findall(texts["attachments/index.md"])
        if (
            len(index_ids) != len(ids)
            or len(set(index_ids)) != len(index_ids)
            or set(index_ids) != ids
        ):
            err(
                f"attachments/index 的 trial 计数/唯一性/集合与源不一致"
                f"（行数 {len(index_ids)}、唯一 {len(set(index_ids))}、应为 {len(ids)}）"
                "——正文藏 id 或表格缺行都会在此现形"
            )
    # 附件小节集合双向对账：删整条小节（其它文件仍齐）不得假绿
    if set(parsed) != ids:
        err(
            f"attachments 的 trial 小节集合与源不一致：缺 {sorted(ids - set(parsed))}，"
            f"多 {sorted(set(parsed) - ids)}"
        )
    if "record.md" in texts:
        rows: list[str] = []
        for line in texts["record.md"].splitlines():
            m = re.match(rf"^\| ({TRIAL_ID}) \|", line)
            if not m:
                continue
            cells = line.split("|")
            if len(cells) < 6 or not cells[2].strip():
                err(f"record 表 {m.group(1)} 行列数不完整或状态列为空：{line[:60]}…")
                continue
            rows.append(m.group(1))
        if len(rows) != len(ids) or len(set(rows)) != len(rows) or set(rows) != ids:
            err(
                f"record 第一层表的 trial 计数/唯一性/集合与源不一致"
                f"（行数 {len(rows)}、唯一 {len(set(rows))}、应为 {len(ids)}）"
            )

    for tid, sec in parsed.items():
        row = trials.get(tid)
        if row is None:
            continue  # 集合检查已报「多」，此处不重复崩
        # 原文完整：仅容忍文件级换行结构，行尾空白不剥（尾部空白也是原文）
        src_response = (row.get("response") or "").rstrip("\n")
        if sec["body"].rstrip("\n") != src_response:
            err(f"attachments 中 {tid} 正文与 trials.jsonl 不逐字一致（原文完整不裁剪被破坏）")
        should_trunc = tid in truncated
        if sec["truncated"] and not should_trunc:
            err(f"attachments 中 {tid} 为 finish=stop 却带截断标注")
        if should_trunc and not sec["truncated"]:
            err(f"attachments 中 {tid} 为 finish=length 却缺「⚠ 截断条目」标题标注")
        if should_trunc and not sec["trunc_note"]:
            err(f"attachments 中 {tid} 缺截断说明行（复核人需知情其正文止于截断处）")
        expected_file = f"{row.get('model', '')}-{row.get('prompt_variant', '')}.md"
        if sec["file"] != expected_file:
            err(f"attachments 中 {tid} 归属错误：位于 {sec['file']}，按源应位于 {expected_file}")
        expected_prompt = "\n".join(m.get("content", "") for m in row.get("messages", []))
        if sec["prompt"] != expected_prompt:
            err(f"attachments 中 {tid} 的提问行与源 messages 不一致")
        if sec["meta"] is None:
            err(f"attachments 中 {tid} 缺「元信息」行")
        else:
            model, variant, index, finish = sec["meta"]
            expected_meta = (
                row.get("model", ""),
                row.get("prompt_variant", ""),
                str(row.get("trial_index", "")),
                row.get("finish_reason") or "unknown",
            )
            if (model, variant, index, finish) != expected_meta:
                err(f"attachments 中 {tid} 元信息行 {sec['meta']} 与源 {expected_meta} 不一致")

    if "form-open.md" in texts:
        check_open_layer(texts["form-open.md"], trials)
    if "form-open.md" in texts and "form-candidates.md" in texts:
        check_candidate_leak(texts["form-open.md"], texts["form-candidates.md"])
    if "form-candidates.md" in texts:
        check_candidates(texts["form-candidates.md"], trials)
    if "case-card.md" in texts:
        check_case_card(texts["case-card.md"])

    for name, text in texts.items():
        if KEY_SECRET_RE.search(text):
            err(f"{name} 疑似含密钥模式（sk-/Bearer）")
        if name in ("background.md", "case-card.md") and "合成" not in text:
            err(f"{name} 缺合成病例声明")

    notes.append(f"trial 全集 {len(ids)} 条（截断 {len(truncated)}）")

    for n in notes:
        print(f"  · {n}")
    if errors:
        print()
        for e in errors:
            print(f"✗ {e}")
        print(f"\n{len(errors)} 个错误。")
        return 1
    print(f"\n✓ 全绿（{len(trials)} 条 trial、材料包结构与原文自洽）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
