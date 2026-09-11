# 27 条基线回答原文附件 · 索引

> 合成病例（非真实患者）。附件为模型完整回答原文（calibration-v1.3，24 条完整 + 3 条截断），未经提取器转述；生成入口 `scripts/gen_review_attachments.py`。

| 模型 | 变体 | 文件 | 条目 |
|---|---|---|---|
| deepseek-v4-flash | neutral | [`deepseek-v4-flash-neutral.md`](deepseek-v4-flash-neutral.md) | `exp003-deepseek-v4-flash-neutral-1`、`exp003-deepseek-v4-flash-neutral-2`、`exp003-deepseek-v4-flash-neutral-3` |
| deepseek-v4-flash | tcm_mirror | [`deepseek-v4-flash-tcm_mirror.md`](deepseek-v4-flash-tcm_mirror.md) | `exp003-deepseek-v4-flash-tcm_mirror-1`、`exp003-deepseek-v4-flash-tcm_mirror-2`、`exp003-deepseek-v4-flash-tcm_mirror-3` |
| deepseek-v4-flash | western_mirror | [`deepseek-v4-flash-western_mirror.md`](deepseek-v4-flash-western_mirror.md) | `exp003-deepseek-v4-flash-western_mirror-1`、`exp003-deepseek-v4-flash-western_mirror-2`、`exp003-deepseek-v4-flash-western_mirror-3` |
| glm-5.3-flash | neutral | [`glm-5.3-flash-neutral.md`](glm-5.3-flash-neutral.md) | `exp003-glm-5.3-flash-neutral-1`、`exp003-glm-5.3-flash-neutral-2`、`exp003-glm-5.3-flash-neutral-3` |
| glm-5.3-flash | tcm_mirror | [`glm-5.3-flash-tcm_mirror.md`](glm-5.3-flash-tcm_mirror.md) | `exp003-glm-5.3-flash-tcm_mirror-1`、`exp003-glm-5.3-flash-tcm_mirror-2`、`exp003-glm-5.3-flash-tcm_mirror-3`（截断） |
| glm-5.3-flash | western_mirror | [`glm-5.3-flash-western_mirror.md`](glm-5.3-flash-western_mirror.md) | `exp003-glm-5.3-flash-western_mirror-1`、`exp003-glm-5.3-flash-western_mirror-2`、`exp003-glm-5.3-flash-western_mirror-3`（截断） |
| step-3.7-flash | neutral | [`step-3.7-flash-neutral.md`](step-3.7-flash-neutral.md) | `exp003-step-3.7-flash-neutral-1`、`exp003-step-3.7-flash-neutral-2`、`exp003-step-3.7-flash-neutral-3` |
| step-3.7-flash | tcm_mirror | [`step-3.7-flash-tcm_mirror.md`](step-3.7-flash-tcm_mirror.md) | `exp003-step-3.7-flash-tcm_mirror-1`、`exp003-step-3.7-flash-tcm_mirror-2`、`exp003-step-3.7-flash-tcm_mirror-3` |
| step-3.7-flash | western_mirror | [`step-3.7-flash-western_mirror.md`](step-3.7-flash-western_mirror.md) | `exp003-step-3.7-flash-western_mirror-1`、`exp003-step-3.7-flash-western_mirror-2`、`exp003-step-3.7-flash-western_mirror-3`（截断） |

截断条目（finish=length）共 3 条，正文止于截断处，不进完整回答分母（口径见 `specs/calibration/denominator-policy.md`）。
