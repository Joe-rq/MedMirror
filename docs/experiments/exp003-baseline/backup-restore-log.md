# 备份与恢复演练记录（issue #4）

工具：`scripts/backup_data.py`（backup-v1）。备份源 docs/experiments/ + runs/；排除 .env.local 与任何含 key/credential 的文件；落点本地 `~/MedMirror-backups/<UTC 时间戳>/`（云端落点待团队确认）。恢复演练 = 恢复到独立目录 → 逐文件 sha256 校验 → 用恢复的 trials.jsonl 离线重放 #10 报告（零模型请求）→ 与 Git 跟踪的 derived-v3/analysis.md 字节比对。

| 时间（UTC） | 备份 | 校验文件 | 哈希差异 | 离线重放 | 与 derived-v3 比对 | 结论 |
|---|---|---|---|---|---|---|

| 2026-09-12T15:06:23.956478+00:00 | 20260912T150623Z | 32 文件 | 无 | 成功 | 一致 | ✅ 通过 |