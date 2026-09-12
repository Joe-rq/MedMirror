#!/usr/bin/env python3
"""数据备份与恢复演练（issue #4）：本地双保险备份 + 哈希清单 + 恢复演练。

- 备份源：docs/experiments/（原始回答/提取/报告/追问证据）+ runs/（run 目录、账本）。
  2026-09-13 起 runs/ 已入 Git（主人拍板，落点=远程仓库）；本脚本提供本地双保险
  与独立的恢复演练能力，不是唯一备份。
- 排除规则：.env.local、任何 *key*/*credential* 文件——凭据永不进备份（验收第 1 条）。
- 输出：<dest>/<UTC 时间戳>/：数据副本 + manifest.json（逐文件 sha256 与大小、来源、
  排除规则、脚本版本）。时间戳目录不覆盖——历史版本保留（验收第 3 条）。
- 恢复演练 `--drill`：从最近（或指定）备份恢复到独立目录 → 逐文件哈希校验 →
  用恢复的 trials.jsonl 离线重放 #10 报告（零模型请求）→ 与 Git 跟踪的
  derived-v3 报告比对——成功则演练记录追加 backup-restore-log.md（验收第 4 条）。
- 备份落点默认本地 `~/MedMirror-backups`（不涉及云端上传；云端落点需团队确认后另行配置）。

用法：
  uv run python scripts/backup_data.py                      # 备份到默认本地目录
  uv run python scripts/backup_data.py --dest /path/to/dir  # 指定落点
  uv run python scripts/backup_data.py --drill              # 恢复演练（只读源备份）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_VERSION = "backup-v1"
SOURCES = ["docs/experiments", "runs"]
EXCLUDE_PATTERNS = (".env.local", ".env", "key", "credential")  # 凭据永不进备份
LOG_PATH = ROOT / "docs/experiments/exp003-baseline/backup-restore-log.md"


def _excluded(path: Path) -> bool:
    name = path.name.lower()
    return any(pat in name for pat in EXCLUDE_PATTERNS)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(base: Path) -> list[Path]:
    if base.is_file():
        return [base]
    return sorted(p for p in base.rglob("*") if p.is_file() and not _excluded(p))


def create_backup(dest_root: Path, verbose: bool = True) -> dict:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = dest_root / stamp
    if backup_dir.exists():
        raise SystemExit(f"备份目录已存在（同秒碰撞）：{backup_dir}")
    backup_dir.mkdir(parents=True)

    manifest = {
        "script_version": SCRIPT_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "sources": SOURCES,
        "exclude_patterns": EXCLUDE_PATTERNS,
        "file_count": 0,
        "total_bytes": 0,
        "files": [],
    }
    excluded_seen: list[str] = []
    for source in SOURCES:
        src = ROOT / source
        if not src.exists():
            continue
        for path in iter_files(src):
            rel = path.relative_to(ROOT)
            target = backup_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            size = path.stat().st_size
            manifest["files"].append({"path": str(rel), "sha256": _sha256(target), "bytes": size})
            manifest["file_count"] += 1
            manifest["total_bytes"] += size
    for source in SOURCES:  # 记录被排除项供核对（只记相对路径，不复制内容）
        src = ROOT / source
        if src.exists():
            excluded_seen += [str(p.relative_to(ROOT)) for p in src.rglob("*") if _excluded(p)]
    manifest["excluded_seen"] = excluded_seen
    (backup_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if verbose:
        print(f"备份完成：{manifest['file_count']} 个文件、{manifest['total_bytes']} 字节")
        print(f"落点：{backup_dir}")
        if excluded_seen:
            print(f"已排除（凭据规则）：{len(excluded_seen)} 项 {excluded_seen[:3]}…")
    return {"backup_dir": str(backup_dir), "file_count": manifest["file_count"]}


def verify_backup(backup_dir: Path) -> dict:
    """逐文件哈希校验；返回 mismatches 列表（空 = 全部一致）。"""
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"缺少 manifest.json：{backup_dir}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches = []
    for entry in manifest["files"]:
        target = backup_dir / entry["path"]
        if not target.exists():
            mismatches.append({"path": entry["path"], "problem": "missing"})
        elif _sha256(target) != entry["sha256"]:
            mismatches.append({"path": entry["path"], "problem": "sha256_mismatch"})
    return {
        "file_count": manifest["file_count"],
        "checked": len(manifest["files"]),
        "mismatches": mismatches,
    }


def latest_backup(dest_root: Path) -> Path:
    stamps = sorted(p for p in dest_root.iterdir() if p.is_dir() and (p / "manifest.json").exists())
    if not stamps:
        raise SystemExit(f"落点 {dest_root} 下没有含 manifest 的备份")
    return stamps[-1]


def drill(backup_dir: Path) -> dict:
    """恢复演练：恢复到独立目录 → 哈希校验 → 离线重放 #10 报告（零模型请求）→ 比对。"""
    restore_dir = backup_dir / "_drill_restore"
    if restore_dir.exists():
        shutil.rmtree(restore_dir)
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        src = backup_dir / entry["path"]
        target = restore_dir / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    verification = verify_backup(
        restore_dir.parent / restore_dir.name.replace("_drill_restore", "")
    )
    # 离线重放：用恢复的 trials.jsonl 生成报告，与 Git 跟踪的 derived-v3 比对
    trials_restored = restore_dir / "docs/experiments/exp003-baseline/result/trials.jsonl"
    out_dir = restore_dir / "_drill_report"
    replay_ok = False
    replay_detail = ""
    if trials_restored.exists():
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/report_exp003.py"),
                "--input",
                str(trials_restored),
                "--output",
                str(out_dir),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        replay_ok = proc.returncode == 0
        replay_detail = proc.stderr.strip()[-200:] or proc.stdout.strip()[-200:]
    ref = ROOT / "docs/experiments/exp003-baseline/derived-v3/analysis.md"
    ref_match = False
    if replay_ok and ref.exists() and (out_dir / "analysis.md").exists():
        ref_match = ref.read_bytes() == (out_dir / "analysis.md").read_bytes()
    result = {
        "at": datetime.now(UTC).isoformat(),
        "backup_dir": str(backup_dir),
        "verified_files": verification["checked"],
        "mismatches": verification["mismatches"],
        "replay_ok": replay_ok,
        "replay_detail": replay_detail,
        "replay_matches_derived_v3": ref_match,
    }
    ok = (not verification["mismatches"]) and replay_ok and ref_match
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n| {result['at']} | {Path(backup_dir).name} | {verification['checked']} 文件 | "
            f"{'无' if not verification['mismatches'] else verification['mismatches']} | "
            f"{'成功' if replay_ok else '失败'} | {'一致' if ref_match else '不一致'} | "
            f"{'✅ 通过' if ok else '❌ 未通过'} |"
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"演练{'通过' if ok else '未通过'}（记录已追加 {LOG_PATH}）")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path.home() / "MedMirror-backups",
        help="备份落点（默认本地 ~/MedMirror-backups；云端落点需团队确认后另行配置）",
    )
    parser.add_argument("--drill", action="store_true", help="恢复演练（默认取落点下最新备份）")
    parser.add_argument("--drill-from", type=Path, default=None, help="指定演练的备份目录")
    args = parser.parse_args(argv)
    if args.drill:
        source = args.drill_from or latest_backup(args.dest)
        result = drill(source)
        return (
            0
            if (
                not result["mismatches"]
                and result["replay_ok"]
                and result["replay_matches_derived_v3"]
            )
            else 1
        )
    create_backup(args.dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
