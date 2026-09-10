# specs/examples · 定标示范与负例

issue #11 的三件套落位处；与 `../calibration/`（标注工作表、裁决记录、分母口径）配套。

| 文件 | 作用 | 状态流转 |
|---|---|---|
| `negatives.jsonl` | 提取判定负例集：结构化「期望正确提取」，供 #12 修复验收与回归 | 每条 `pending_owner_confirmation` → 主人确认后改 `confirmed` |
| `negatives-review.md` | 上表的人读版审阅表（考题/AI 答案/批改栏，按档位校准顺序编排）——主人批改的入口，结论回流 `negatives.jsonl` | 批改完成后随 status 同步归档 |
| `standard-finding.md` | 标准发现包示范骨架：研究问题、分组 n/N、引文、反例、待复核、假设、限制 | `OWNER_TO_CONFIRM` / `MACHINE_PREFILL` 占位由主人确认替换 |

## kind 语义与关键字段

- `kind` 是**考查点**，分三组：状态考查（`not_mentioned`/`negation`/`recommended`/`conditional_support`——防止状态误判，neg-004 的「推荐」与 neg-005 的「条件支持」是防止升格/降格的锚点条目）、缺陷考查（`object_crosstalk`/`substitution_vs_adjunct`/`source_misidentification`/`evidence_mentioned_not_verified`/`contradicted`）、数据状态考查（`failure`/`truncation`，必须引用真实 trial）。期望判定本身在 `expected.paths.*.state`，与 kind 不冗余。
- `denominator_effect`：失败/截断条目的分母归属结构化字段（`excluded_from_valid` / `excluded_from_complete`），机器核验，不靠散文。
- `substitution`/`adjunct`：`substitution_vs_adjunct` 类负例的替代/辅助态度落点（STATES 枚举），供 #12 断言。
- `REQUIRED_KINDS` = issue #11 点名必须覆盖的 7 类考查点；覆盖不足即检查失败。`recommended` 同为状态锚点但未入 REQUIRED_KINDS：issue 未点名，且推荐态已由 `negation`/`conditional_support` 的对照锚定，非必备。

## 机器检测

```bash
uv run python scripts/check_calibration.py                    # 结构、逐字引文、trial 引用、kind 覆盖、分母口径
uv run python scripts/check_calibration.py --require-confirmed  # 人工定标完成后：要求全部负例已 confirmed
```

脚本通过只证明结构、引文与分母自洽，**不证明语义正确**（specs/calibration.md §4）；语义以人工定标为准。生成标注工作表：`uv run python scripts/gen_annotation_worksheet.py`（输出已存在时拒绝覆盖，防抹掉人工标注；确认覆盖加 `--force`）。
