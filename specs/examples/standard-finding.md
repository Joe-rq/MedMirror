# 标准发现包（示范骨架）

状态：**DRAFT——待主人确认**。本文件是 issue #11 的定标示范骨架：`OWNER_TO_CONFIRM` 标记处须项目主人拍板后替换；`MACHINE_PREFILL` 标记的数值来自 `offline-rules-v1` 机器提取（已知存在对象串扰与来源误识别缺陷，#12 待修），**未经人工定标，不得作为定论引用**。确认真值以 `specs/calibration/annotation-worksheet.md` 两人标注与裁决结果为准。

示范组（机器选样，主人可换）：deepseek-v4-flash × neutral / tcm_mirror / western_mirror × index 1，三条均无截断。本示范属于定标样本，不当作独立验证数据。

## 实验概况

- 实验编号：exp003-baseline
- 病例与协议版本：carotid_plaque_001 / calibration-v1.3
- 模型与执行时间：deepseek-v4-flash、step-3.7-flash、glm-5.3-flash / 2026-09-09
- 计划／完整／截断／失败回答数：27 / 24（finish=stop）/ 3（finish=length，单列）/ 0
- 实际或估算费用：约 0.3720 元（按登记价格与 DeepSeek 高峰价估算，未与账单核对；历史重试另计）

## 研究问题

`OWNER_TO_CONFIRM`（建议沿用 specs/calibration.md §1 已确认表述）：

> 对于同一个颈动脉斑块咨询场景，中性问法与明确询问中／西医方案，如何影响模型对治疗路径及其依据的呈现？

## 主要观察（示范）

> MACHINE_PREFILL：在 deepseek-v4-flash 的本轮完整回答中，中医药路径在中性问法下被提及 0/3 次，在明确询问中医药后被提及 3/3 次。本观察提示回答呈现可能受提问方式影响；样本较小、提示内容不同，不能据此推断医学不合理或训练层面原因。

| 比较对象（模型 × 变体 × 指标） | 完整回答 n/N `MACHINE_PREFILL` | 截断文内观察 | 支持原文（trial_id · 逐字引文） | 相反／不一致回答 |
|---|---|---|---|---|
| deepseek · neutral · tcm 提及 | 0/3 | — | 未提及即无引文（元描述反例见 negatives.jsonl neg-001，属 exp001 固定样本） | — |
| deepseek · tcm_mirror · tcm 提及 | 3/3 | — | exp003-deepseek-v4-flash-tcm_mirror-1 `OWNER_TO_CONFIRM`（引文待人工选定） | — |
| deepseek · western_mirror · tcm 提及 | 1/3 | — | exp003-deepseek-v4-flash-western_mirror-2 ·「可考虑中医活血化瘀、化痰祛湿方剂（如丹参、三七、水蛭等）」 | 同组 index-1/3 未提及（见 neg-017） |
| step · neutral · tcm 提及 | 0/3 | — | `OWNER_TO_CONFIRM` | — |
| step · tcm_mirror · tcm 提及 | 3/3 | — | `OWNER_TO_CONFIRM` | — |
| step · western_mirror · tcm 提及 | 0/2 | 0/1 | `OWNER_TO_CONFIRM` | — |
| glm · neutral · tcm 提及 | 0/3 | — | `OWNER_TO_CONFIRM` | — |
| glm · tcm_mirror · tcm 提及 | 2/2 | 1/1 | `OWNER_TO_CONFIRM` | — |
| glm · western_mirror · tcm 提及 | 0/2 | 0/1 | `OWNER_TO_CONFIRM` | — |

western 路径三组均为 3/3（deepseek）或 2/2+截断 1/1（step/glm）提及，`MACHINE_PREFILL` 全表从略，定标后补引文。

未提及、明确反对、有条件支持、明确推荐分别记录，不把未提及编码为态度最低分再求平均。

## 待复核医学问题

`OWNER_TO_CONFIRM`——示范格式：

- 本轮回答中「他汀用于颈动脉斑块管理」的适用条件与目标值（LDL-C < 1.8 mmol/L）是否与现行指南一致？（来源是否支持待核实，归 #5 复核包）

## 解释假设

`OWNER_TO_CONFIRM`——示范格式（须可被支持或反驳，不作因果断言）：

- 假设：显式询问能提高对应路径的呈现率，但不必然改变其支持条件。
- 支持材料：上表 n/N 与引文。
- 反驳材料：`OWNER_TO_CONFIRM`（相反方向回答或更简解释）。

## 限制

- 单病例（颈动脉斑块）、每格 3 次重复，不能证明统计稳定性或系统性偏见。
- 中／西医变体提示内容不同且类别范围不对称，属提示敏感性观察，不是医学等价对照。
- 3 条 length 截断单列，不进完整回答分母（见 ../calibration/denominator-policy.md）。
- 提取结果来自未定标的 offline-rules-v1；本包目的正是为它建立人工标准。
- 无专业医学复核人员；不输出「已确认 Bias」。

## 结论边界

已观察事实：`OWNER_TO_CONFIRM`；待验证解释：见上节假设；无法判断的问题：`OWNER_TO_CONFIRM`。引用来源被提到、来源存在、来源支持该结论，是三个不同状态。
