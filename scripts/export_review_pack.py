#!/usr/bin/env python3
"""把 specs/review/ 复核材料包导出为医务人员友好的 Word 分发形态（issue #24）。

md 是真相源（check_review_pack.py 的逐字/禁词/引文校验全部跑在 md 上）；
docx 仅为派生分发物，不入库（specs/review/export/ 已 gitignore），md 改动后重导出即可。

两批发送纪律（判定后置）在导出层落地：
  --layer open        第一批（开放式复核）：background / case-card / boundaries /
                      form-open + attachments 全部（glob 派生，新增分组自动纳入）。
                      绝不包含 form-candidates——复核人先独立交回第一层意见。
  --layer candidates  第二批（候选核对）：form-candidates。其「挑选记录」区的
                      候选池状态行须为 FINAL 才可导出（DRAFT/缺失均拒绝，预览加 --allow-draft）。

Word 使用说明（填写方式、智能引号风险提示）在导出时注入 docx 头部，不写进 md 真相源。

用法：uv run python scripts/export_review_pack.py --layer open [--output-dir 目录]
前置：pandoc（缺失时报错并给安装指引，如 brew install pandoc）。
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "specs/review"
DEFAULT_OUTPUT_DIR = REVIEW / "export"
DATA_DIR = ROOT / "docs/experiments/exp003-baseline/result"
# 目录所有权标记：证明输出目录属于本脚本（整体替换前的判别依据）
MANIFEST_NAME = ".export-manifest.json"
# open 批固定文件；attachments 部分按目录 glob 派生（防静态清单漂移致静默缺文件）
OPEN_FIXED = ["background.md", "case-card.md", "boundaries.md", "form-open.md"]
# open 批明确排除的顶层材料：候选（第二批）、项目方记录、导览
OPEN_EXCLUDE = {"form-candidates.md", "record.md", "README.md"}

OPEN_HEADER = """> **给复核人（Word 版使用说明）**
>
> 1. 请先读「背景」与「病例卡」，再逐条填「第一层复核表」：在每条的**复核意见**后直接输入文字；不想评价的条目，在意见处写「**跳过**」二字即可（「[ ]」只是标记，无需打勾）。
> 2. 模型完整回答在「attachments」各文件的表格框内，请对照阅读。
> 3. **请不要复制本材料中的原文文字去充当证据引文**——Word 的自动更正会悄悄改字符（如引号变弯引号），导致引文与原文不一致；如需引用某指南或文献，写**名称+年份**即可，项目方会去核对原文。
> 4. 本包不包含研究方的任何候选清单或倾向；第二层材料将在您交回本表后另发。
> 5. 「无法判断」「不在我的专业范围」是合法且被如实记录的答案。

"""

CANDIDATES_HEADER = """> **给复核人（Word 版使用说明，第二层）**
>
> 1. 每条候选下方的**复核栏**：在对应选项后写「√」或直接删除不选的项，并在「依据与出处」写明理由；引用指南/文献写**名称+年份**即可（请勿复制材料原文充当引文，Word 自动更正会改字符）。
> 2. 「无法判断」是合法选项并如实记录。

"""


PANDOC: str | None = None


def ensure_pandoc() -> str:
    """返回 pandoc 可执行路径；缺失时报错退出。后续 subprocess 直接用它，避免 which 后又被移除的窗口。"""
    global PANDOC
    if PANDOC is None:
        PANDOC = shutil.which("pandoc")
        if PANDOC is None:
            print("✗ 未找到 pandoc。请先安装，例如：brew install pandoc")
            sys.exit(1)
    return PANDOC


def open_layer_files(review: Path = REVIEW) -> list[str]:
    """open 批文件集：固定材料 + attachments 全量 glob；并与目录双向对账。

    对账防两类事故：静态清单漂移后静默缺文件（新增分组未纳入）；目录里混入
    不属于 open 批也不在排除集的新材料（未归类即分发，语义不明）。
    """
    files = sorted(
        OPEN_FIXED + [f"attachments/{p.name}" for p in (review / "attachments").glob("*.md")]
    )
    actual = sorted(
        p.name
        for p in review.glob("*.md")
        if p.name not in OPEN_EXCLUDE and p.name not in OPEN_FIXED
    )
    if actual:
        print(
            f"✗ specs/review/ 顶层存在未归类材料 {actual}——"
            "不属于 open 批固定文件也不在排除集，先归类（加入 OPEN_FIXED 或 OPEN_EXCLUDE）再导出。"
        )
        sys.exit(1)
    return files


def pick_section_problems(text: str) -> list[str]:
    """解析「挑选记录」区块（到下一个二级标题为止）的结构问题（fail-closed）：
    三个数据行各恰好一条、必核子集为 8–12 个唯一且真实存在的候选编号、日期含年份。
    说明文字与本区块之外的任何内容都不参与解析。"""
    problems: list[str] = []
    heads = list(re.finditer(r"^## 挑选记录.*$", text, re.MULTILINE))
    if len(heads) != 1:
        return [f"「## 挑选记录」区块应恰好一个，实际 {len(heads)} 个"]
    m = heads[0]
    tail = text[m.end() :]
    nxt = re.search(r"^## ", tail, re.MULTILINE)
    section = tail[: nxt.start()] if nxt else tail

    def unique_line(prefix: str) -> str | None:
        hits = re.findall(rf"^- {prefix}：(.+?)\s*$", section, re.MULTILINE)
        if len(hits) != 1:
            problems.append(f"「{prefix}」行应恰好一条，实际 {len(hits)} 条")
            return None
        return hits[0]

    status = unique_line("候选池状态")
    subset = unique_line("必核子集")
    date = unique_line("定稿依据与日期")
    if subset is not None:
        if "待定" in subset:
            problems.append("必核子集行仍是占位")
        picks = re.findall(r"(?<![a-zA-Z0-9_-])cand-\d{2}(?![a-zA-Z0-9_-])", subset)
        residue = re.sub(r"(?<![a-zA-Z0-9_-])cand-\d{2}(?![a-zA-Z0-9_-])|[、，,\s]", "", subset)
        if residue:
            problems.append(f"必核子集行含无法解析的残留文本：{residue[:40]!r}")
        if len(picks) != len(set(picks)):
            problems.append("必核子集编号重复")
        if not 8 <= len(picks) <= 12:
            problems.append(f"必核子集应勾选 8–12 个编号，实际 {len(picks)} 个")
        legal = set(re.findall(r"^#{2,3} (cand-\d{2}) ", text, re.MULTILINE))
        ghosts = sorted(set(picks) - legal)
        if ghosts:
            problems.append(f"勾选了不存在的候选编号：{ghosts}")
    if date is not None and ("待定" in date or not re.search(r"20\d{2}", date)):
        problems.append("定稿依据与日期行仍是占位或不含年份")
    if status is not None and status not in ("DRAFT", "FINAL"):
        problems.append(f"候选池状态取值异常：{status}")
    return problems


def load_manifest(path: Path) -> dict[str, str] | None:
    """严格 schema（fail-closed）：files 为非空 {安全 basename: sha256 hex}。

    空 files、字段类型错、含路径分隔/..、hash 非 64 位十六进制 → None（视为无所有权凭证）。
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(files, dict) or not files:
        return None
    recorded: dict[str, str] = {}
    for key, value in files.items():
        if not isinstance(key, str) or not re.fullmatch(r"[\w.\-]+", key) or ".." in key:
            return None
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            return None
        recorded[key] = value
    return recorded


def pick_section_status(text: str) -> str | None:
    """受限区块（「## 挑选记录」到下一个二级标题）内的状态行取值；区块缺失或不唯一返回 None。"""
    heads = list(re.finditer(r"^## 挑选记录.*$", text, re.MULTILINE))
    if len(heads) != 1:
        return None
    m = heads[0]
    tail = text[m.end() :]
    nxt = re.search(r"^## ", tail, re.MULTILINE)
    section = tail[: nxt.start()] if nxt else tail
    hits = re.findall(r"^- 候选池状态：(\S+)\s*$", section, re.MULTILINE)
    return hits[0] if len(hits) == 1 else None


def candidates_finalized(text: str) -> bool:
    """结构合法（pick_section_problems 为空）且受限区块内状态行=FINAL 且头部横幅已去 DRAFT。

    --allow-draft 只豁免本函数的「状态」两项（FINAL 与头部横幅），结构校验不可绕过。
    """
    if pick_section_problems(text):
        return False
    if pick_section_status(text) != "FINAL":
        return False
    return "状态：DRAFT" not in text[: text.find("## 挑选记录")]


def render_docx(pandoc: str, md_path: Path, docx_path: Path) -> None:
    try:
        result = subprocess.run(
            [pandoc, str(md_path), "-o", str(docx_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        print(f"✗ pandoc 转换超时（{md_path.name}），已中止。")
        sys.exit(1)
    except OSError as e:
        print(f"✗ 无法执行 pandoc（{md_path.name}）：{e}")
        sys.exit(1)
    if result.returncode != 0:
        print(f"✗ pandoc 转换失败（{md_path.name}）：{result.stderr[:300]}")
        sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", required=True, choices=["open", "candidates"], help="导出批次")
    parser.add_argument(
        "--review-dir", default=str(REVIEW), help="材料包目录（默认 specs/review；测试注入口）"
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="候选池未定稿（状态行仍为 DRAFT）时也允许导出 candidates 层（仅供测试/预览）",
    )
    args = parser.parse_args()

    review = Path(args.review_dir).resolve()
    if not review.is_dir():
        print(f"✗ 找不到材料包目录：{review}")
        return 1
    out_dir = Path(args.output_dir).resolve()
    if out_dir.exists() and not out_dir.is_dir():
        print(f"✗ 输出路径已存在且不是目录：{out_dir}")
        return 1
    # 防呆锚两处：原始数据目录 + md 真相源目录（派生 docx 不得混入 result/ 或 specs/review/ 本体）。
    # 唯一豁免：默认导出目录 specs/review/export/（gitignored 派生区）。
    # 同款守卫另见 report_exp003.py 与 gen_review_attachments.py（收敛为共享模块待第 4 处出现）。
    protected = {DATA_DIR, review}
    hit = next(
        (
            d
            for d in sorted(protected)
            if (out_dir == d or d in out_dir.parents or out_dir in d.parents)
            and out_dir != DEFAULT_OUTPUT_DIR
        ),
        None,
    )
    if hit is not None:
        print(f"✗ 输出目录（{out_dir}）不得指向受保护目录（{hit}）本身、其子目录或其祖先目录。")
        return 1

    layer_files = open_layer_files(review) if args.layer == "open" else ["form-candidates.md"]
    missing = [f for f in layer_files if not (review / f).is_file()]
    if missing:
        print(f"✗ 材料包缺文件（先确认 issue #20 的材料已在 main）：{missing}")
        return 1
    if args.layer == "candidates":
        cand_pre = (review / "form-candidates.md").read_text(encoding="utf-8")
        pre_problems = pick_section_problems(cand_pre)
        if pre_problems:
            print("✗ 挑选记录区结构不合法，拒绝导出（--allow-draft 也不豁免结构）：")
            for problem in pre_problems:
                print(f"  · {problem}")
            return 1
    ensure_pandoc()  # 快速失败：无 pandoc 时先于快照/checker 报安装指引

    # ── 材料快照（单点真相）：全部预读 → 落盘 _tmp/ 快照目录 → 复读比对，
    # 定稿判定、checker、附件重生成比对与 staging 全部只面向快照——
    # 校验对象 = 导出对象，关闭「校验后、导出前」live 材料被改写的 TOCTOU。
    out_tag = hashlib.sha256(str(out_dir).encode()).hexdigest()[:12]
    parent = out_dir.parent
    snap_root = ROOT / "_tmp"
    try:
        parent.mkdir(parents=True, exist_ok=True)
        snap_root.mkdir(exist_ok=True)  # 干净环境 _tmp 可能不存在
        lock = parent / f".export-{out_tag}.lock"
        lock_fd = os.open(lock, os.O_CREAT | os.O_RDWR)
    except OSError as e:
        print(f"✗ 无法准备导出工作区（_tmp/锁）：{e}")
        return 1
    # 锁先于快照：并发导出不会用旧快照覆盖新提交；锁释放：成功路径提交段 finally close，
    # 失败路径由进程退出自动释放。锁获取与全部快照 I/O 在下方统一异常保护内。
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        # 快照须是材料目录的完整镜像（checker rglob 全部 md；本层清单只是导出子集）
        snapshot_names = {
            str(q.relative_to(review))
            for q in review.rglob("*.md")
            if q.relative_to(review).parts[0] != "export"
        }
        materials = {name: (review / name).read_text(encoding="utf-8") for name in snapshot_names}
        with tempfile.TemporaryDirectory(
            prefix=f".export-snap-{out_tag}-", dir=snap_root
        ) as snap_td:
            snapshot = Path(snap_td)
            # 快照生命周期随 with 块：任何失败路径自动清理（不留 _tmp 残留）
            for name in sorted(snapshot_names):
                target = snapshot / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(materials[name], encoding="utf-8", newline="\n")
            # 复读校验：预读期间材料被并发修改（内容或目录成员增删）→ 拒绝（fail-closed，重跑即可）
            changed = [
                n
                for n, body in materials.items()
                if (review / n).read_text(encoding="utf-8") != body
            ]
            reread_names = {
                str(q.relative_to(review))
                for q in review.rglob("*.md")
                if q.relative_to(review).parts[0] != "export"
            }
            if changed or reread_names != set(materials):
                print(
                    f"✗ 材料在快照期间被修改（内容变化 {changed}；成员差集 "
                    f"{sorted(reread_names ^ set(materials))}），拒绝导出——请重试。"
                )
                return 1
            if args.layer == "candidates":
                cand_text = materials["form-candidates.md"]
                structural = pick_section_problems(cand_text)
                if structural:
                    print("✗ 挑选记录区结构不合法，拒绝导出（--allow-draft 也不豁免结构）：")
                    for problem in structural:
                        print(f"  · {problem}")
                    return 1
                if not candidates_finalized(cand_text) and not args.allow_draft:
                    print(
                        "✗ 候选池未定稿（挑选记录区状态行仍为 DRAFT 或头部横幅未更新），拒绝导出第二批——"
                        "定稿流程见 form-candidates.md 的挑选记录区；确认预览用 --allow-draft。"
                    )
                    return 1

            # 防线一：导出前材料包必须通过结构检查（trial 全集/原文逐字/禁词等），
            # 防止把被篡改或不完整的真相源转成分发物；附件 symlink 一并拒绝（checker 不查）。
            try:
                check = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "check_review_pack.py"),
                        "--review-dir",
                        str(snapshot),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
            except (subprocess.TimeoutExpired, OSError) as e:
                print(f"✗ 无法运行 check_review_pack.py：{e}")
                return 1
            if check.returncode != 0:
                print("✗ 材料包未通过 check_review_pack.py，拒绝导出（先修复材料再分发）：")
                print(check.stdout.strip()[:800])
                return 1
            for f in layer_files:
                if (review / f).is_symlink():
                    print(f"✗ 材料文件是符号链接：{f}，拒绝导出（防包外内容混入）。")
                    return 1
            # 防线二：附件必须与源严格一致——用生成器重生成到临时目录逐文件字节比对
            # （幂等性有测试锁定；此处拦截往附件/index 夹带非生成内容的篡改）。
            if args.layer == "open":
                with tempfile.TemporaryDirectory() as td:
                    try:
                        regen = subprocess.run(
                            [
                                sys.executable,
                                str(ROOT / "scripts" / "gen_review_attachments.py"),
                                "--output-dir",
                                str(Path(td) / "regen"),
                            ],
                            capture_output=True,
                            text=True,
                            timeout=300,
                        )
                    except (subprocess.TimeoutExpired, OSError) as e:
                        print(f"✗ 无法运行 gen_review_attachments.py：{e}")
                        return 1
                    if regen.returncode != 0:
                        print(f"✗ 附件重生成失败，拒绝导出：{regen.stdout.strip()[:300]}")
                        return 1
                    for name in layer_files:
                        if not name.startswith("attachments/"):
                            continue
                        regen_path = Path(td) / "regen" / name.removeprefix("attachments/")
                        if (snapshot / name).read_bytes() != regen_path.read_bytes():
                            print(
                                f"✗ 附件 {name} 与源重生成结果不一致（被手改或夹带内容），拒绝导出。"
                            )
                            return 1

            header = OPEN_HEADER if args.layer == "open" else CANDIDATES_HEADER
            expected_docx = {
                f.removesuffix(".md").replace("/", "__") + ".docx" for f in layer_files
            }

            # 提交模型（文件级原子，无目录空窗）：
            #  - manifest 记录每个产物的 sha256，是目录所有权的唯一凭证；
            #  - 重导出前校验现有文件 hash 与 manifest 一致（防同名用户文件被误删），
            #    跨层切换时只删 manifest 记录且 hash 吻合的旧产物；
            #  - 新产物全部在 tmp 生成并校验后逐个 os.replace 就位（逐文件提交非事务，
            #    崩溃半就位态由下次运行的状态校验拦截并提示人工）；
            #  - 锁防并发互踩；tmp 残留按本目录指纹清理（不碰其它输出目录的残留）。
            parent = out_dir.parent
            lock = parent / f".export-{out_tag}.lock"
            # out_dir 就位（锁与 parent.mkdir 已在快照前完成）
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
            except (FileExistsError, NotADirectoryError) as e:
                print(f"✗ 输出路径的祖先存在非目录项：{e}")
                return 1
            tmpdir: Path | None = None
            try:
                manifest_path = out_dir / MANIFEST_NAME
                recorded: dict[str, str] = {}
                if manifest_path.is_file():
                    recorded_or_none = load_manifest(manifest_path)
                    if recorded_or_none is None:
                        print(
                            f"✗ {MANIFEST_NAME} 非法（空/残缺/字段类型错/含不安全路径），"
                            "拒绝执行——请手动核对该目录。"
                        )
                        return 1
                    recorded = recorded_or_none
                elif any(out_dir.iterdir()):
                    print(
                        f"✗ 输出目录非空且无 {MANIFEST_NAME}（非本脚本所属目录），拒绝写入——"
                        "请换目录或手动清空。"
                    )
                    return 1

                def sha256(path: Path) -> str:
                    return hashlib.sha256(path.read_bytes()).hexdigest()

                # 状态校验（全部 fail-closed）：
                #  - manifest 与任何条目是符号链接 → 拒绝（hash 会跟随链接读目录外内容，悬挂链接直接崩）
                #  - manifest.files 键集必须与目录条目集（除 manifest）严格相等——防「合法但不完整」
                #    的 manifest 放行未登记的同名文件
                #  - 陌生条目拒绝；manifest 记录的文件被改写（hash 不符）拒绝覆盖
                if manifest_path.is_symlink():
                    print(f"✗ {MANIFEST_NAME} 是符号链接，拒绝执行。")
                    return 1
                entries = sorted(out_dir.iterdir())
                if any(e.is_symlink() for e in entries):
                    print("✗ 输出目录含符号链接条目，拒绝执行。")
                    return 1
                entry_names = {e.name for e in entries if e.name != MANIFEST_NAME}
                if manifest_path.is_file() and entry_names != set(recorded):
                    print(
                        f"✗ {MANIFEST_NAME} 记录与目录实际文件集不一致"
                        f"（目录有 {sorted(entry_names - set(recorded))}、记录多 {sorted(set(recorded) - entry_names)}），"
                        "拒绝执行——请手动核对该目录。"
                    )
                    return 1
                for entry in entries:
                    if entry.name == MANIFEST_NAME:
                        continue
                    if not entry.is_file():  # 子目录、FIFO、socket 等非普通文件一律拒绝
                        print(
                            f"✗ 输出目录含非普通文件条目：{entry.name}，拒绝执行，请换目录或手动移走。"
                        )
                        return 1
                    if entry.name in recorded:
                        if sha256(entry) != recorded[entry.name]:
                            print(
                                f"✗ {entry.name} 与 manifest 记录不一致（可能被人工替换），"
                                "拒绝覆盖——请先核对该文件。"
                            )
                            return 1
                    elif entry.name not in expected_docx:
                        print(
                            f"✗ 输出目录含非本脚本产物：{entry.name}，拒绝执行，请换目录或手动移走。"
                        )
                        return 1

                # tmp 用 mkdtemp（随机目录名、本进程持有所有权；崩溃残留可手动删 .export-tmp-*），
                # 与输出目录同卷保证 os.replace 原子；不做跨运行自动清理（可预测名清理会误删用户文件）
                tmpdir = Path(tempfile.mkdtemp(prefix=f".export-tmp-{out_tag}-", dir=parent))
                staged: dict[str, Path] = {}
                for name in layer_files:  # 只导本层清单；materials 是全量镜像（checker 用）
                    body = materials[name]
                    flat = name.removesuffix(".md").replace("/", "__")
                    tmp_md = tmpdir / f"{flat}.md"
                    tmp_md.write_text(header + body, encoding="utf-8", newline="\n")
                    staged[f"{flat}.docx"] = tmp_md
                # pandoc 阶段（md → 同目录 tmp docx），全部成功才提交
                for docx_name, tmp_md in sorted(staged.items()):
                    render_docx(ensure_pandoc(), tmp_md, tmpdir / docx_name)
                # 产物校验：期望集合齐全且均为合法 docx（防「返回 0 但无产物」的伪 pandoc）
                got = {n.name for n in tmpdir.glob("*.docx")}
                if got != expected_docx or not all(zipfile.is_zipfile(tmpdir / n) for n in got):
                    print(
                        f"✗ 导出产物不完整或非有效 docx：期望 {sorted(expected_docx)}，实际 {sorted(got)}"
                    )
                    return 1
                # 提交顺序：新产物逐文件 os.replace 就位 → 删除旧 manifest 记录且 hash 吻合的旧层文件
                # → manifest 最后替换。注意：逐文件提交不是事务，中途崩溃会留下新旧混合的半就位状态，
                # 下次运行会被状态校验（manifest/目录不一致）拦下并提示人工核对——这是设计取舍，
                # 不是「失败自动保留旧版本」。
                for n in sorted(expected_docx):
                    os.replace(tmpdir / n, out_dir / n)
                for old_name, old_hash in recorded.items():
                    if old_name in expected_docx:  # 同层重导：刚就位的新产物即使 hash 未变也不许删
                        continue
                    old_path = out_dir / old_name
                    if old_path.is_file() and sha256(old_path) == old_hash:
                        old_path.unlink()
                new_manifest = {
                    "layer": args.layer,
                    "files": {n: sha256(out_dir / n) for n in sorted(expected_docx)},
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }
                tmp_manifest = tmpdir / MANIFEST_NAME
                tmp_manifest.write_text(
                    json.dumps(new_manifest, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                os.replace(tmp_manifest, manifest_path)
            finally:
                if tmpdir is not None:
                    shutil.rmtree(tmpdir, ignore_errors=True)

        print(f"✓ 已导出 {args.layer} 批次 {len(layer_files)} 个 docx → {out_dir}")
        return 0
    except (OSError, UnicodeDecodeError) as e:
        print(f"✗ 快照/导出工作区 I/O 失败：{e}")
        return 1
    finally:
        # 锁 fd 生命周期 = 本进程导出全程（含一切失败路径）；fd 关闭即解锁
        os.close(lock_fd)


if __name__ == "__main__":
    sys.exit(main())
