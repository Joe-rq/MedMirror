#!/usr/bin/env python3
"""生成医学复核材料包的 27 条原文可读附件（issue #20）。

按 模型×变体 分组写 specs/review/attachments/<model>-<variant>.md（9 个）+ index.md。
正文内嵌模型完整回答，不经提取器转述、不裁剪；finish=length 的条目显著标注为截断
（其正文是截断前已生成的部分，不代表模型完整表述，复核人需知情）。

仅支持 exp003 基线协议（校验锚定其 VARIANTS 与数据目录），不是通用生成器。

本目录为纯派生产物：源为 Git 跟踪的 trials.jsonl，重复生成字节一致，勿手改；
人工内容一律写在 specs/review/ 其余文件。

用法：uv run python scripts/gen_review_attachments.py [--input trials.jsonl] [--output-dir 目录]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from medmirror.protocol import load_jsonl  # noqa: E402
from medmirror.runner import CASE_TEXT, VARIANTS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "docs/experiments/exp003-baseline/result/trials.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "specs/review/attachments"
# model/variant 会拼进输出文件名，白名单防路径穿越（外部 --input 的 jsonl 字段不可信）
SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9._\-]+$")
# 正文里出现「任意级标题 + trial_id 形状」的行会破坏附件的 ## 分节解析
TRIAL_HEAD_IN_BODY_RE = re.compile(r"^#{1,6} exp003-\S+", re.MULTILINE)


def validate_trials(trials: list[dict[str, Any]]) -> list[str]:
    """入口统一校验：坏输入整批拒绝，不产出半成品目录。"""
    problems: list[str] = []
    seen: set[str] = set()
    for t in trials:
        tid = t.get("trial_id") or "?"
        if tid in seen:
            problems.append(f"trial_id 重复：{tid}")
        seen.add(tid)
        for field in ("model", "prompt_variant"):
            value = str(t.get(field, ""))
            if not SAFE_NAME_RE.fullmatch(value):
                problems.append(f"{tid} 的 {field} 含文件名不安全字符：{value!r}")
        variant = t.get("prompt_variant")
        if variant not in VARIANTS:
            problems.append(f"{tid} 的 prompt_variant 不在协议 VARIANTS 中：{variant!r}")
        if not isinstance(t.get("trial_index"), int):
            problems.append(f"{tid} 的 trial_index 必须是 int：{t.get('trial_index')!r}")
        if not isinstance(t.get("response"), str):
            problems.append(f"{tid} 的 response 必须是字符串：{type(t.get('response')).__name__}")
        elif "```" in t["response"]:
            problems.append(f"{tid} 原文含 ```，会破坏附件 fence 结构")
        elif TRIAL_HEAD_IN_BODY_RE.search(t["response"]):
            problems.append(f"{tid} 原文含「# exp003-」形状的标题行，会破坏附件分节结构")
        expected_msgs = [{"role": "user", "content": VARIANTS.get(variant, "")}]
        if t.get("messages") != expected_msgs:
            problems.append(f"{tid} 的 messages 与协议 VARIANTS 提示不一致，拒绝生成（防错配提问）")
        if t.get("finish_reason") not in ("stop", "length"):
            problems.append(
                f"{tid} finish_reason={t.get('finish_reason')!r}，仅 stop/length 可入附件"
                "（其它状态须先明确分母口径）"
            )
        if t.get("status") != "success":
            problems.append(f"{tid} status={t.get('status')}，仅成功试次可入复核附件")
    return problems


def is_truncated(trial: dict[str, Any]) -> bool:
    return trial.get("finish_reason") == "length"


def variant_note(variant: str) -> str:
    """变体说明从协议常量派生，问句措辞不另存副本。"""
    if variant not in VARIANTS:
        return ""
    if variant == "neutral":
        return "基础病例文本，无补充问题。"
    suffix = VARIANTS[variant][len(CASE_TEXT) :].strip()
    return f"基础病例文本 +「{suffix}」"


def render_trial(trial: dict[str, Any]) -> str:
    truncated = is_truncated(trial)
    flag = "（**⚠ 截断条目**）" if truncated else ""
    lines = [
        f"## {trial['trial_id']}{flag}",
        "",
        f"- 元信息：{trial['model']} · {trial['prompt_variant']} · 第 {trial['trial_index']} 次重复 · finish={trial.get('finish_reason')}",
        "- 提问全文（user）：",
        "",
    ]
    for msg in trial["messages"]:
        lines.append(f"  > {msg['content']}")
    lines.append("")
    if truncated:
        lines.append(
            "> ⚠ 该条回答因输出长度上限截断（finish=length）：以下正文止于截断处，"
            "不代表该次回答的完整表述；复核意见请据此限定范围。"
        )
        lines.append("")
    lines.append("### 模型回答完整原文")
    lines.append("")
    lines.append("```text")
    # 原文逐字嵌入，不做 rstrip——尾部空白也是「原文完整不裁剪」的一部分
    lines.append(trial.get("response") or "")
    lines.append("```")
    return "\n".join(lines)


def render_group(model: str, variant: str, trials: list[dict[str, Any]]) -> str:
    header = [
        f"# {model} · {variant}",
        "",
        "> 合成病例（非真实患者）。本文件内嵌模型回答完整原文，未经裁剪或转述；"
        "由 `scripts/gen_review_attachments.py` 从 trials.jsonl 生成，勿手改。",
        f"> 提示变体 `{variant}`：{variant_note(variant)}",
        "",
    ]
    body = [render_trial(t) for t in sorted(trials, key=lambda r: r["trial_index"])]
    return "\n".join(header) + "\n\n".join(body) + "\n"


def render_index(groups: dict[tuple[str, str], list[dict[str, Any]]]) -> str:
    trials = [t for ts in groups.values() for t in ts]
    truncated = sum(1 for t in trials if is_truncated(t))
    lines = [
        f"# {len(trials)} 条基线回答原文附件 · 索引",
        "",
        "> 合成病例（非真实患者）。附件为模型完整回答原文（calibration-v1.3，"
        f"{len(trials) - truncated} 条完整 + {truncated} 条截断），未经提取器转述；"
        "生成入口 `scripts/gen_review_attachments.py`。",
        "",
        "| 模型 | 变体 | 文件 | 条目 |",
        "|---|---|---|---|",
    ]
    for (model, variant), group_trials in sorted(groups.items()):
        name = f"{model}-{variant}.md"
        entries = "、".join(
            f"`{t['trial_id']}`{'（截断）' if is_truncated(t) else ''}"
            for t in sorted(group_trials, key=lambda r: r["trial_index"])
        )
        lines.append(f"| {model} | {variant} | [`{name}`]({name}) | {entries} |")
    lines += [
        "",
        f"截断条目（finish=length）共 {truncated} 条，正文止于截断处，不进完整回答分母"
        "（口径见 `specs/calibration/denominator-policy.md`）。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="trials.jsonl 路径")
    parser.add_argument(
        "--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录（不得指向原始数据目录）"
    )
    args = parser.parse_args()

    src = Path(args.input).resolve()
    out_dir = Path(args.output_dir).resolve()
    if out_dir.exists() and not out_dir.is_dir():
        print(f"✗ 输出目录已存在且不是目录：{out_dir}")
        return 1
    # 守卫锚定仓内原始数据目录（常量锚，不随 --input 变化，防换源绕过覆写 result/）；
    # 拒绝该目录本身、其子目录与其祖先目录（祖先会把派生文件散落到 result/ 同层或仓库根）。
    # 外部 --input 的所在目录不是保护对象。
    protected = {DEFAULT_INPUT.resolve().parent}
    hit = next(
        (
            d
            for d in sorted(protected)
            if out_dir == d or d in out_dir.parents or out_dir in d.parents
        ),
        None,
    )
    if hit is not None:
        print(
            f"✗ 输出目录（{out_dir}）是原始数据目录（{hit}）本身、其子目录或其祖先目录，防止覆盖 result/。"
        )
        return 1

    trials = load_jsonl(src)
    if not trials:
        print("✗ 输入为空。")
        return 1
    bad = [t.get("trial_id") or "?" for t in trials if not (t.get("response") or "").strip()]
    if bad:
        print(f"✗ {len(bad)} 条无正文，不能进入复核附件：{bad}")
        return 1
    problems = validate_trials(trials)
    if problems:
        print(f"✗ 输入校验失败（{len(problems)} 项），拒绝生成：")
        for p in problems:
            print(f"  · {p}")
        return 1

    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for t in trials:
        groups.setdefault((t["model"], t["prompt_variant"]), []).append(t)

    # 先把全部内容渲染到内存再落盘：渲染异常不会留下半成品目录
    outputs = {f"{m}-{v}.md": render_group(m, v, ts) for (m, v), ts in sorted(groups.items())}
    outputs["index.md"] = render_index(groups)

    # 先预检全部目标再落盘：任何一个 symlink 拒绝都发生在写入之前，不留半成品
    for name in outputs:
        target = out_dir / name
        if target.is_symlink():
            print(f"✗ 输出目标 {target} 是符号链接，拒绝跟随写入。")
            return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        (out_dir / name).write_text(content, encoding="utf-8", newline="\n")

    truncated = sum(1 for t in trials if is_truncated(t))
    print(f"✓ 已生成 {len(groups)} 个分组附件 + index.md（{len(trials)} 条，截断 {truncated} 条）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
