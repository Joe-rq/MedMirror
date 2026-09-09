# specs/examples · 定标示范与负例

issue #11 的三件套落位处；与 `../calibration/`（标注工作表、裁决记录、分母口径）配套。

| 文件 | 作用 | 状态流转 |
|---|---|---|
| `negatives.jsonl` | 提取判定负例集：结构化「期望正确提取」，供 #12 修复验收与回归 | 每条 `pending_owner_confirmation` → 主人确认后改 `confirmed` |
| `standard-finding.md` | 标准发现包示范骨架：研究问题、分组 n/N、引文、反例、待复核、假设、限制 | `OWNER_TO_CONFIRM` / `MACHINE_PREFILL` 占位由主人确认替换 |

## 机器检测

```bash
uv run python scripts/check_calibration.py                    # 结构、逐字引文、trial 引用、kind 覆盖、分母口径
uv run python scripts/check_calibration.py --require-confirmed  # 人工定标完成后：必备 kind 须全有 confirmed 条目
```

脚本通过只证明结构、引文与分母自洽，**不证明语义正确**（specs/calibration.md §4）；语义以人工定标为准。生成标注工作表：`uv run python scripts/gen_annotation_worksheet.py`（覆盖式输出，标注进行中勿重跑）。
