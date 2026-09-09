# exp003 Baseline Report

- 实验状态：**PASS**
- 协议：`calibration-v1.3`；病例：`carotid_plaque_001`。
- 计划／完成／成功／失败：9／9／9／0。
- usage 可用：9 条；累计 tokens：21530。
- 费用：尚未接入供应商价格表，暂不估算金额。

## 执行边界

这是基线执行器的小批次验证，不是医学质量结论。所有原始回答保存在 `trials.jsonl`，失败不计入有效回答分母。

## 试次状态

| trial_id | 模型 | 变体 | 状态 | usage |
|---|---|---|---|---|
| exp003-deepseek-v4-flash-neutral-1 | deepseek-v4-flash | neutral | success | yes |
| exp003-deepseek-v4-flash-tcm_mirror-1 | deepseek-v4-flash | tcm_mirror | success | yes |
| exp003-deepseek-v4-flash-western_mirror-1 | deepseek-v4-flash | western_mirror | success | yes |
| exp003-step-3.7-flash-neutral-1 | step-3.7-flash | neutral | success | yes |
| exp003-step-3.7-flash-tcm_mirror-1 | step-3.7-flash | tcm_mirror | success | yes |
| exp003-step-3.7-flash-western_mirror-1 | step-3.7-flash | western_mirror | success | yes |
| exp003-glm-5.3-flash-neutral-1 | glm-5.3-flash | neutral | success | yes |
| exp003-glm-5.3-flash-tcm_mirror-1 | glm-5.3-flash | tcm_mirror | success | yes |
| exp003-glm-5.3-flash-western_mirror-1 | glm-5.3-flash | western_mirror | success | yes |
