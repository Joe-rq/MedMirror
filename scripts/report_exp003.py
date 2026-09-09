#!/usr/bin/env python3
"""对 exp003 已保存回答做离线提取与分组汇总（report-v2）。

默认读取 Git 中的原始 trials.jsonl，派生产物写入独立目录（默认 derived-v2/），
绝不写回原始数据目录；无密钥、无网络即可运行。相同版本与输入产出字节一致。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from run_exp003_baseline import atomic_write_jsonl, planned_trials

from medmirror.protocol import load_jsonl
from medmirror.providers import load_catalog, model_registry
from medmirror.reporting import build_report, extract_sorted, render_markdown

DEFAULT_INPUT = ROOT / "docs/experiments/exp003-baseline/result/trials.jsonl"
DEFAULT_OUTPUT = ROOT / "docs/experiments/exp003-baseline/derived-v2"
MAX_REPEATS = 999


def load_pricing() -> dict[str, dict[str, float]]:
    return {
        item["vendor"]: item["pricing"] for item in load_catalog()["models"] if item.get("pricing")
    }


def atomic_write_text(path: Path, text: str) -> None:
    """临时文件 + 原子替换；固定 LF 换行，保证跨平台字节一致。"""
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="原始 trials.jsonl 路径")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="派生产物输出目录")
    parser.add_argument("--repeats", type=int, default=3, help="协议计划重复次数（v1.3 为 3）")
    args = parser.parse_args(argv)
    if not 1 <= args.repeats <= MAX_REPEATS:
        parser.error(f"--repeats 必须在 1 到 {MAX_REPEATS} 之间")

    input_path = args.input.resolve()
    output_dir = args.output.resolve()
    if not input_path.is_file():
        parser.error(f"输入文件不存在：{input_path}")
    if output_dir.exists() and not output_dir.is_dir():
        parser.error(f"--output 已存在且不是目录：{output_dir}")
    # 守卫锚定两处：本次输入所在目录 + 仓内原始数据目录（防止换 --input 绕过守卫覆写 result/）；
    # 同时拒绝这些目录的子目录与祖先目录（祖先目录会把派生文件散落到 result/ 同层或仓库根）。
    protected = {input_path.parent, DEFAULT_INPUT.resolve().parent}
    hit = next(
        (
            d
            for d in sorted(protected)
            if output_dir == d or d in output_dir.parents or output_dir in d.parents
        ),
        None,
    )
    if hit is not None:
        parser.error(
            f"拒绝执行：--output（{output_dir}）是原始数据与旧版报告所在目录（{hit}）"
            "本身、其子目录或其祖先目录，派生产物必须写入独立目录，"
            "例如 docs/experiments/exp003-baseline/derived-v2/"
        )

    trials = load_jsonl(input_path)
    extractions = extract_sorted(trials)
    planned = planned_trials(model_registry(), args.repeats)
    report = build_report(trials, extractions, planned, pricing=load_pricing())

    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_jsonl(output_dir / "extractions.jsonl", extractions)
    atomic_write_text(
        output_dir / "analysis.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    atomic_write_text(output_dir / "analysis.md", render_markdown(report))

    counts = report["counts"]
    print(
        f"计划 {report['planned_n']} ／ 完整 {counts['complete']} ／ 截断 {counts['truncated']}"
        f" ／ 失败 {counts['failed']} ／ 未执行 {counts['not_executed']}"
        f" ／ 原因未知 {counts['unknown_finish']}；分组 {len(report['slices'])} 个"
    )
    print(f"派生产物已写入：{output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
