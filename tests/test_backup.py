"""issue #4 备份与恢复演练测试：排除规则、哈希清单、防覆盖、损坏检测。不触网。"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import backup_data as bd


def test_excluded_patterns_cover_credentials():
    assert bd._excluded(Path("/x/.env.local"))
    assert bd._excluded(Path("/x/api_keys.txt"))
    assert bd._excluded(Path("/x/credentials.json"))
    assert not bd._excluded(Path("/x/trials.jsonl"))
    assert not bd._excluded(Path("/x/walnut.txt"))  # 子串误伤检查：普通词不含 key
    assert bd._excluded(Path("/x/monkey.txt"))  # monkey 含 key 子串 → 保守排除（fail-safe 方向）


def test_create_backup_manifest_and_exclude(tmp_path, monkeypatch):
    (bd.ROOT / "runs" / "unit-test-run").mkdir(parents=True, exist_ok=True)
    (bd.ROOT / "runs" / "unit-test-run" / "budget.jsonl").write_text("{}\n", encoding="utf-8")
    (bd.ROOT / "runs" / "unit-test-run" / ".env.local").write_text("SECRET=1\n", encoding="utf-8")
    try:
        result = bd.create_backup(tmp_path, verbose=False)
        manifest = json.loads(
            (Path(result["backup_dir"]) / "manifest.json").read_text(encoding="utf-8")
        )
        paths = [f["path"] for f in manifest["files"]]
        assert any("unit-test-run/budget.jsonl" in p for p in paths)
        assert not any(".env.local" in p for p in paths)  # 凭据不进备份
        assert ".env.local" in str(manifest["excluded_seen"])  # 但被排除事实入清单
        assert manifest["file_count"] == len(manifest["files"])
        # docs/experiments 的 Git 跟踪数据在清单里（原始回答+追问证据）
        assert any("result/trials.jsonl" in p for p in paths)
        assert any("followup/findings.jsonl" in p for p in paths)
        # 每个条目有 sha256 且非空
        assert all(len(f["sha256"]) == 64 for f in manifest["files"])
    finally:
        import shutil

        shutil.rmtree(bd.ROOT / "runs" / "unit-test-run")


def test_backup_timestamp_dirs_not_overwritten(tmp_path, monkeypatch):
    """同秒重复备份 → 拒绝且原目录不被触碰；时间戳推进 → 新目录、历史保留。"""

    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 9, 13, 0, 0, 0, tzinfo=UTC)

    class FakeDatetimeNextSecond(FakeDatetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 9, 13, 0, 0, 1, tzinfo=UTC)

    monkeypatch.setattr(bd, "datetime", FakeDatetime)
    r1 = bd.create_backup(tmp_path, verbose=False)
    with pytest.raises(SystemExit):
        bd.create_backup(tmp_path, verbose=False)  # 同秒碰撞拒绝，不覆盖已有备份
    assert Path(r1["backup_dir"]).exists()

    monkeypatch.setattr(bd, "datetime", FakeDatetimeNextSecond)
    r2 = bd.create_backup(tmp_path, verbose=False)
    assert Path(r1["backup_dir"]) != Path(r2["backup_dir"])  # 历史版本保留
    assert Path(r1["backup_dir"]).exists()


def test_verify_detects_tampering(tmp_path):
    result = bd.create_backup(tmp_path, verbose=False)
    backup_dir = Path(result["backup_dir"])
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    victim = next(f["path"] for f in manifest["files"] if f["path"].endswith("trials.jsonl"))
    (backup_dir / victim).write_text("篡改\n", encoding="utf-8")
    report = bd.verify_backup(backup_dir)
    assert any(
        m["path"] == victim and m["problem"] == "sha256_mismatch" for m in report["mismatches"]
    )


def test_verify_detects_missing(tmp_path):
    result = bd.create_backup(tmp_path, verbose=False)
    backup_dir = Path(result["backup_dir"])
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    victim = backup_dir / next(
        f["path"] for f in manifest["files"] if f["path"].endswith("trials.jsonl")
    )
    victim.unlink()
    report = bd.verify_backup(backup_dir)
    assert any(m["problem"] == "missing" for m in report["mismatches"])


def test_verify_clean_backup(tmp_path):
    result = bd.create_backup(tmp_path, verbose=False)
    report = bd.verify_backup(Path(result["backup_dir"]))
    assert report["mismatches"] == []
    assert report["checked"] == report["file_count"]
