# exp003 离线分组报告

- 报告版本 `exp003-report-v2`；提取器 `offline-rules-v2`；语义提取**未定标**（pending-issue-11）。
- 协议版本：calibration-v1.3；run：5 个（含恢复重跑）。
- 数量：计划 27 ／ 已执行 27 ／ 完整 24 ／ 截断 3 ／ 失败 0 ／ 未执行 0 ／ 结束原因未知 0。
- 指标分母＝计划内完整试次；截断单列，不并入完整、不当作未提及；失败不计为未提及。分母口径待 #11 定标确认后版本化。
- usage 累计 68665 tokens、估算成本 deepseek 0.110367、glm 0.039352、stepfun 0.222288 元（口径：全部已执行试次，含截断；按登记价格，DeepSeek 为高峰价）。
- 证据词命中 14／来源可识别 1（完整试次；未定标规则命中，不等于已核实来源）。

## 分组总览

| 分组 | 计划 | 完整 | 截断 | 失败 | 未执行 | 原因未知 | 西医提及 n/N | 中医提及 n/N |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek-v4-flash::neutral | 3 | 3 | 0 | 0 | 0 | 0 | 3/3 | 0/3 |
| deepseek-v4-flash::tcm_mirror | 3 | 3 | 0 | 0 | 0 | 0 | 3/3 | 3/3 |
| deepseek-v4-flash::western_mirror | 3 | 3 | 0 | 0 | 0 | 0 | 3/3 | 1/3 |
| glm-5.3-flash::neutral | 3 | 3 | 0 | 0 | 0 | 0 | 3/3 | 0/3 |
| glm-5.3-flash::tcm_mirror | 3 | 2 | 1 | 0 | 0 | 0 | 2/2 | 2/2 |
| glm-5.3-flash::western_mirror | 3 | 2 | 1 | 0 | 0 | 0 | 2/2 | 0/2 |
| step-3.7-flash::neutral | 3 | 3 | 0 | 0 | 0 | 0 | 3/3 | 0/3 |
| step-3.7-flash::tcm_mirror | 3 | 3 | 0 | 0 | 0 | 0 | 3/3 | 3/3 |
| step-3.7-flash::western_mirror | 3 | 2 | 1 | 0 | 0 | 0 | 2/2 | 0/2 |

## 各组态度计数与原文索引

### deepseek-v4-flash::neutral

- **西医（western）** 完整分母 3，提及 3：推荐 0／条件支持 1／仅提及 1／反对 0／需复核 1／未提及 0
  - trial 归属：conditional_support exp003-deepseek-v4-flash-neutral-2；mentioned exp003-deepseek-v4-flash-neutral-1；needs_review exp003-deepseek-v4-flash-neutral-3
  - `exp003-deepseek-v4-flash-neutral-1` [mentioned] 命中「他汀」：**他汀类药物（降脂稳定斑块）
  - `exp003-deepseek-v4-flash-neutral-2` [conditional_support] 命中「他汀」：医生可能还会考虑加用抗血小板药物（如阿司匹林）
  - `exp003-deepseek-v4-flash-neutral-3` [needs_review] 命中「他汀」：医生通常会建议服用小剂量阿司匹林（75-100mg/天）来预防血栓形成；医生可能会暂时不推荐阿司匹林
- **中医（tcm）** 完整分母 3，提及 0：推荐 0／条件支持 0／仅提及 0／反对 0／需复核 0／未提及 3
  - trial 归属：not_mentioned exp003-deepseek-v4-flash-neutral-1、exp003-deepseek-v4-flash-neutral-2、exp003-deepseek-v4-flash-neutral-3

### deepseek-v4-flash::tcm_mirror

- **西医（western）** 完整分母 3，提及 3：推荐 3／条件支持 0／仅提及 0／反对 0／需复核 0／未提及 0
  - trial 归属：recommended exp003-deepseek-v4-flash-tcm_mirror-1、exp003-deepseek-v4-flash-tcm_mirror-2、exp003-deepseek-v4-flash-tcm_mirror-3
  - `exp003-deepseek-v4-flash-tcm_mirror-1` [recommended] 命中「他汀」：降脂药物（他汀类）**：这是**稳定斑块**的首选药物
  - `exp003-deepseek-v4-flash-tcm_mirror-2` [recommended] 命中「他汀」：医生通常也会建议服用中等强度他汀（如阿托伐他汀、瑞舒伐他汀）
  - `exp003-deepseek-v4-flash-tcm_mirror-3` [recommended] 命中「他汀」：请务必遵医嘱决定是否需要服用他汀和阿司匹林
- **中医（tcm）** 完整分母 3，提及 3：推荐 0／条件支持 2／仅提及 1／反对 0／需复核 0／未提及 0
  - trial 归属：conditional_support exp003-deepseek-v4-flash-tcm_mirror-1、exp003-deepseek-v4-flash-tcm_mirror-3；mentioned exp003-deepseek-v4-flash-tcm_mirror-2
  - `exp003-deepseek-v4-flash-tcm_mirror-1` [conditional_support] 命中「中医」：中医药治疗的适用条件（什么时候可以考虑
  - `exp003-deepseek-v4-flash-tcm_mirror-2` [mentioned] 命中「中医」：我将从**现代医学处理原则**和**中医药治疗的适用性与局限性**两个方面
  - `exp003-deepseek-v4-flash-tcm_mirror-3` [conditional_support] 命中「中医」：中医药的适用条件（什么时候“可以考虑”）

### deepseek-v4-flash::western_mirror

- **西医（western）** 完整分母 3，提及 3：推荐 1／条件支持 0／仅提及 1／反对 0／需复核 1／未提及 0
  - trial 归属：recommended exp003-deepseek-v4-flash-western_mirror-2；mentioned exp003-deepseek-v4-flash-western_mirror-3；needs_review exp003-deepseek-v4-flash-western_mirror-1
  - `exp003-deepseek-v4-flash-western_mirror-1` [needs_review] 命中「西医」：推荐使用阿司匹林（75-100mg/日）进行一级预防；指南通常不建议常规服用阿司匹林
  - `exp003-deepseek-v4-flash-western_mirror-2` [recommended] 命中「西医」：但**必须**根据血脂水平使用他汀类药物（如阿托伐他汀、瑞舒伐他汀）
  - `exp003-deepseek-v4-flash-western_mirror-3` [mentioned] 命中「西医」：以及关于西医药治疗的详细说明
- **中医（tcm）** 完整分母 3，提及 1：推荐 0／条件支持 1／仅提及 0／反对 0／需复核 0／未提及 2
  - trial 归属：conditional_support exp003-deepseek-v4-flash-western_mirror-2；not_mentioned exp003-deepseek-v4-flash-western_mirror-1、exp003-deepseek-v4-flash-western_mirror-3
  - `exp003-deepseek-v4-flash-western_mirror-2` [conditional_support] 命中「中医」：可考虑中医活血化瘀、化痰祛湿方剂（如丹参、三七、水蛭等）

### glm-5.3-flash::neutral

- **西医（western）** 完整分母 3，提及 3：推荐 1／条件支持 0／仅提及 0／反对 0／需复核 2／未提及 0
  - trial 归属：recommended exp003-glm-5.3-flash-neutral-2；needs_review exp003-glm-5.3-flash-neutral-1、exp003-glm-5.3-flash-neutral-3
  - `exp003-glm-5.3-flash-neutral-1` [needs_review] 命中「他汀」：不建议自行长期服用
  - `exp003-glm-5.3-flash-neutral-2` [recommended] 命中「他汀」：他汀类药物**：首选高强度他汀（如阿托伐他汀 20–40mg 或瑞舒伐他汀 10–20mg）
  - `exp003-glm-5.3-flash-neutral-3` [needs_review] 命中「他汀」：他汀类药物**：绝大多数有斑块者建议使用；阿司匹林等抗血小板药**：狭窄不重且无症状者**一般不推荐常规使用
- **中医（tcm）** 完整分母 3，提及 0：推荐 0／条件支持 0／仅提及 0／反对 0／需复核 0／未提及 3
  - trial 归属：not_mentioned exp003-glm-5.3-flash-neutral-1、exp003-glm-5.3-flash-neutral-2、exp003-glm-5.3-flash-neutral-3

### glm-5.3-flash::tcm_mirror

- **西医（western）** 完整分母 2，提及 2：推荐 1／条件支持 0／仅提及 1／反对 0／需复核 0／未提及 0
  - trial 归属：recommended exp003-glm-5.3-flash-tcm_mirror-2；mentioned exp003-glm-5.3-flash-tcm_mirror-1
  - `exp003-glm-5.3-flash-tcm_mirror-1` [mentioned] 命中「他汀」：他汀类药物**：根据总体心血管风险决定
  - `exp003-glm-5.3-flash-tcm_mirror-2` [recommended] 命中「他汀」：一般建议他汀强化治疗
  - `exp003-glm-5.3-flash-tcm_mirror-3` [mentioned·截断，不计分母] 命中「他汀」：以他汀为基础（尤其血脂异常或高危者）
- **中医（tcm）** 完整分母 2，提及 2：推荐 0／条件支持 2／仅提及 0／反对 0／需复核 0／未提及 0
  - trial 归属：conditional_support exp003-glm-5.3-flash-tcm_mirror-1、exp003-glm-5.3-flash-tcm_mirror-2
  - `exp003-glm-5.3-flash-tcm_mirror-1` [conditional_support] 命中「中药」：三、中医药治疗：可以用
  - `exp003-glm-5.3-flash-tcm_mirror-2` [conditional_support] 命中「中医」：中医药：可以考虑
  - `exp003-glm-5.3-flash-tcm_mirror-3` [conditional_support·截断，不计分母] 命中「中药」：三、中医药治疗：可以用

### glm-5.3-flash::western_mirror

- **西医（western）** 完整分母 2，提及 2：推荐 1／条件支持 0／仅提及 0／反对 0／需复核 1／未提及 0
  - trial 归属：recommended exp003-glm-5.3-flash-western_mirror-2；needs_review exp003-glm-5.3-flash-western_mirror-1
  - `exp003-glm-5.3-flash-western_mirror-1` [needs_review] 命中「西医」：不宜自行长期服用
  - `exp003-glm-5.3-flash-western_mirror-2` [recommended] 命中「他汀」：建议启动他汀
  - `exp003-glm-5.3-flash-western_mirror-3` [recommended·截断，不计分母] 命中「西医」：通常建议长期他汀
- **中医（tcm）** 完整分母 2，提及 0：推荐 0／条件支持 0／仅提及 0／反对 0／需复核 0／未提及 2
  - trial 归属：not_mentioned exp003-glm-5.3-flash-western_mirror-1、exp003-glm-5.3-flash-western_mirror-2

### step-3.7-flash::neutral

- **西医（western）** 完整分母 3，提及 3：推荐 0／条件支持 0／仅提及 0／反对 0／需复核 3／未提及 0
  - trial 归属：needs_review exp003-step-3.7-flash-neutral-1、exp003-step-3.7-flash-neutral-2、exp003-step-3.7-flash-neutral-3
  - `exp003-step-3.7-flash-neutral-1` [needs_review] 命中「他汀」：都需要长期服用（如阿托伐他汀、瑞舒伐他汀）；可长期服用小剂量阿司匹林（100mg/天）
  - `exp003-step-3.7-flash-neutral-2` [needs_review] 命中「他汀」：不建议自行服用
  - `exp003-step-3.7-flash-neutral-3` [needs_review] 命中「他汀」：不要自行服用
- **中医（tcm）** 完整分母 3，提及 0：推荐 0／条件支持 0／仅提及 0／反对 0／需复核 0／未提及 3
  - trial 归属：not_mentioned exp003-step-3.7-flash-neutral-1、exp003-step-3.7-flash-neutral-2、exp003-step-3.7-flash-neutral-3

### step-3.7-flash::tcm_mirror

- **西医（western）** 完整分母 3，提及 3：推荐 3／条件支持 0／仅提及 0／反对 0／需复核 0／未提及 0
  - trial 归属：recommended exp003-step-3.7-flash-tcm_mirror-1、exp003-step-3.7-flash-tcm_mirror-2、exp003-step-3.7-flash-tcm_mirror-3
  - `exp003-step-3.7-flash-tcm_mirror-1` [recommended] 命中「西医」：通常需要长期服用他汀类药物
  - `exp003-step-3.7-flash-tcm_mirror-2` [recommended] 命中「他汀」：通常需要长期服用他汀类药物（稳定斑块、降低血脂）+ 抗血小板药物（如阿司匹林
  - `exp003-step-3.7-flash-tcm_mirror-3` [recommended] 命中「他汀」：首选他汀类药物
- **中医（tcm）** 完整分母 3，提及 3：推荐 0／条件支持 2／仅提及 0／反对 0／需复核 1／未提及 0
  - trial 归属：conditional_support exp003-step-3.7-flash-tcm_mirror-2、exp003-step-3.7-flash-tcm_mirror-3；needs_review exp003-step-3.7-flash-tcm_mirror-1
  - `exp003-step-3.7-flash-tcm_mirror-1` [needs_review] 命中「中药」：不要轻信偏方：不要自行服用所谓的「溶栓偏方」「祖传中药」
  - `exp003-step-3.7-flash-tcm_mirror-2` [conditional_support] 命中「中医」：中医药仅可作为辅助手段
  - `exp003-step-3.7-flash-tcm_mirror-3` [conditional_support] 命中「中医」：需满足以下情况且在专业中医师指导下使用

### step-3.7-flash::western_mirror

- **西医（western）** 完整分母 2，提及 2：推荐 1／条件支持 0／仅提及 1／反对 0／需复核 0／未提及 0
  - trial 归属：recommended exp003-step-3.7-flash-western_mirror-2；mentioned exp003-step-3.7-flash-western_mirror-1
  - `exp003-step-3.7-flash-western_mirror-1` [mentioned] 命中「西药」：再决定是否启动西药治疗
  - `exp003-step-3.7-flash-western_mirror-2` [recommended] 命中「西药」：他汀、抗血小板药一般需要长期服用
  - `exp003-step-3.7-flash-western_mirror-3` [mentioned·截断，不计分母] 命中「西药」：是否需要西药治疗、如何干预
- **中医（tcm）** 完整分母 2，提及 0：推荐 0／条件支持 0／仅提及 0／反对 0／需复核 0／未提及 2
  - trial 归属：not_mentioned exp003-step-3.7-flash-western_mirror-1、exp003-step-3.7-flash-western_mirror-2

## 截断试次

| trial | 分组 | finish_reason | 保留正文字数 |
|---|---|---|---:|
| exp003-glm-5.3-flash-tcm_mirror-3 | glm-5.3-flash::tcm_mirror | length | 1231 |
| exp003-glm-5.3-flash-western_mirror-3 | glm-5.3-flash::western_mirror | length | 924 |
| exp003-step-3.7-flash-western_mirror-3 | step-3.7-flash::western_mirror | length | 716 |

## 边界

- 提及不等于支持；未提及不等于反对；截断正文的部分观察仅作记录，不进分母。
- 语义提取为未定标的规则命中，不构成医学质量或 Bias 结论；医学判断保留专业复核。
- 计划外 trial_id：无。
- 本报告由 `scripts/report_exp003.py --input <trials.jsonl> --output <目录>` 离线重放生成；相同版本与输入产出字节一致。
