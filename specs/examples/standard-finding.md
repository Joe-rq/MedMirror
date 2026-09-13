# 标准发现包（示范）

状态：**已确认（2026-09-13，主人拍板 4 项全部采纳建议版；数值来源 `docs/experiments/exp003-baseline/derived-v3/`，提取器 offline-rules-v2）**。数值层已按缩窄口径定标（1 条完整标注 + 9 条口头裁决 + 14 条抽查后接受机器结果；14 条信任扩展未经逐字段独立标注，局限声明见 `specs/calibration/fp-fn-report.md`，在一切引用中保留）。本示范属于定标样本，不当作独立验证数据。拍板记录见文末。

示范组（机器选样，主人可换）：deepseek-v4-flash × neutral / tcm_mirror / western_mirror × index 1，三条均无截断。

## 实验概况

- 实验编号：exp003-baseline
- 病例与协议版本：carotid_plaque_001 / calibration-v1.3
- 模型与执行时间：deepseek-v4-flash、step-3.7-flash、glm-5.3-flash / 2026-09-09
- 计划／完整／截断／失败回答数：27 / 24（finish=stop）/ 3（finish=length，单列）/ 0
- 基线估算费用约 0.3720 元（按登记价格与 DeepSeek 高峰价）；三家实际账单已核对合计 0.4746 元（含追问与早期重试，口径不同，见 `specs/calibration/bill-check.md`）
- 另有有界追问（followup-rules-v1）3 候选 4 次真实调用，为独立探索分组，不计入本包分母，见 `docs/experiments/exp003-baseline/followup/`

## 研究问题

（主人 2026-09-13 确认，沿用 specs/calibration.md §1 表述）：

> 对于同一个颈动脉斑块咨询场景，中性问法与明确询问中／西医方案，如何影响模型对治疗路径及其依据的呈现？

## 主要观察（示范）

> 在 deepseek-v4-flash 的完整回答中，中医药路径在中性问法下被提及 0/3 次，在明确询问中医药后被提及 3/3 次（offline-rules-v2，缩窄定标口径）。本观察提示回答呈现可能受提问方式影响；样本较小、提示内容不同，不能据此推断医学不合理或训练层面原因。

| 比较对象（模型 × 变体 × 指标） | 完整回答 n/N | 截断文内观察 | 支持原文（trial_id · 逐字引文） | 相反／不一致回答 |
|---|---|---|---|---|
| deepseek · neutral · tcm 提及 | 0/3 | — | 未提及即无引文（元描述反例见 negatives.jsonl neg-001，属 exp001 固定样本） | — |
| deepseek · tcm_mirror · tcm 提及 | 3/3 | — | exp003-deepseek-v4-flash-tcm_mirror-1 ·「中医药治疗的适用条件（什么时候可以考虑」 | 组内态度细分：条件支持 2／仅提及 1（见 derived-v3） |
| deepseek · western_mirror · tcm 提及 | 1/3 | — | exp003-deepseek-v4-flash-western_mirror-2 ·「可考虑中医活血化瘀、化痰祛湿方剂（如丹参、三七、水蛭等）」 | 同组 index-1/3 未提及（见 neg-017） |
| step · neutral · tcm 提及 | 0/3 | — | 未提及即无引文 | — |
| step · tcm_mirror · tcm 提及 | 3/3 | — | exp003-step-3.7-flash-tcm_mirror-2 ·「中医药仅可作为辅助手段」 | 组内态度细分：条件支持 2／需复核 1（「不要轻信偏方」，见 derived-v3） |
| step · western_mirror · tcm 提及 | 0/2 | 0/1 | 未提及即无引文 | — |
| glm · neutral · tcm 提及 | 0/3 | — | 未提及即无引文 | — |
| glm · tcm_mirror · tcm 提及 | 2/2 | 1/1 | exp003-glm-5.3-flash-tcm_mirror-1 ·「三、中医药治疗：可以用」 | — |
| glm · western_mirror · tcm 提及 | 0/2 | 0/1 | 未提及即无引文 | — |

western 路径提及：**24/24 完整回答全部提及**（deepseek 三组各 3/3；step 的 neutral、tcm_mirror 3/3，western_mirror 2/2 + 截断文内 1/1；glm 的 neutral 3/3，tcm_mirror、western_mirror 各 2/2 + 截断文内 1/1）。各组态度细分与逐条引文索引见 `docs/experiments/exp003-baseline/derived-v3/analysis.md`。

未提及、明确反对、有条件支持、明确推荐分别记录，不把未提及编码为态度最低分再求平均。

## 待复核医学问题

必核子集已定稿 FINAL 10 条（cand-01/02/03/05/07/10/11/12/14/15，覆盖用药决策、手术指征、监测安排、中西药联用安全；主张全文与逐字引文见 `specs/review/form-candidates.md`）。复核流程状态：第一批开放式材料已发出（2026-09-12，登记见 `specs/review/record.md`），第一层意见回流后发第二批候选核对。以下为早期示范格式：

- 本轮回答中「他汀用于颈动脉斑块管理」的适用条件与目标值（LDL-C < 1.8 mmol/L）是否与现行指南一致？（来源是否支持待核实，归 #5 复核包）

## 解释假设

（主人 2026-09-13 确认采纳）：

- 假设：显式询问能提高对应路径的呈现率，但不必然改变其支持条件。
- 支持材料：上表 n/N 与引文（tcm_mirror 下 tcm 提及 8/8 完整 + 截断文内 1/1；neutral 下 0/9）。
- 反驳材料：更简解释是提示内容不对称本身——tcm_mirror 提示明确要求中医方案，呈现率变化可直接归因于任务指令，无需诉诸模型内在倾向；且 deepseek 在 western_mirror 下仍主动提及中医 1/3 次，与"仅镜像才提及"的强版本不符。

## 限制

- 单病例（颈动脉斑块）、每格 3 次重复，不能证明统计稳定性或系统性偏见。
- 中／西医变体提示内容不同且类别范围不对称，属提示敏感性观察，不是医学等价对照。
- 3 条 length 截断单列，不进完整回答分母（见 ../calibration/denominator-policy.md）。
- 提取数值来自 offline-rules-v2，已按缩窄口径定标：1 条完整标注 + 9 条口头裁决 + 14 条抽查后接受机器结果；14 条信任扩展未经逐字段独立标注（`specs/calibration/fp-fn-report.md`），引用时保留该声明。
- 专业医学复核进行中（第一批材料 2026-09-12 发出，意见未回流）；不输出「已确认 Bias」。

## 结论边界

- 已观察事实（主人 2026-09-13 确认）：西医路径在全部 24 条完整回答中被提及 24/24；中医路径仅在被明确询问时被提及（tcm_mirror 完整 8/8），中性问法 0/9；deepseek 在 western_mirror 下主动提及中医 1/3 次，step、glm 均为 0；追问轮 glm 两次零正文、step 截断、deepseek 完整（followup 独立分组）。
- 待验证解释：见上节假设。
- 无法判断的问题：呈现差异的医学合理性（归 #5 复核）；模型间/组内稳定性（3 次重复不足）；差异成因（训练数据 vs 提示敏感性，本设计不可区分）。

引用来源被提到、来源存在、来源支持该结论，是三个不同状态。

## 拍板记录（2026-09-13，主人逐项确认）

| # | 拍板项 | 结果 |
|---|---|---|
| 1 | 研究问题表述（§研究问题） | 采纳建议：沿用 specs/calibration.md §1 原文 |
| 2 | 待复核医学问题记录方式（§待复核医学问题） | 采纳建议：必核 10 条编号 + 指向 `specs/review/form-candidates.md`，不复制主张全文 |
| 3 | 解释假设与反驳材料（§解释假设） | 采纳建议：草拟假设 + 奥卡姆反驳（提示不对称的更简解释 + deepseek 主动提及反例） |
| 4 | 结论边界（§结论边界） | 采纳建议：按草拟定稿 |

全部 `OWNER_TO_CONFIRM` 标记已清除，状态转「已确认」；本文成为 specs/calibration.md 结构标准的实例正本（issue #11 遗留项闭合）。
