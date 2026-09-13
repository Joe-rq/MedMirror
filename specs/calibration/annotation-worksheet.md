# 27 条基线回答 · 人工定标标注工作表

- 数据：`docs/experiments/exp003-baseline/result/trials.jsonl`（calibration-v1.3，24 条 stop + 3 条 length 截断）。
- 机器预填来自 `offline-rules-v1`，**该版本存在否定对象串扰与来源误识别缺陷（#12 已修复为 offline-rules-v2，见 `docs/experiments/exp003-baseline/derived-v3/`），预填仅供核对，不可照抄**。
- 两人**独立**标注，不许先对答案；分歧登记到 `adjudication-log.md` 后裁决。
- 态度取值：`not_mentioned / mentioned / opposed / conditional_support / recommended / needs_review`；`needs_review` 表示语义不确定，交人工复核，不强填态度。
- 作用对象：态度指向的具体对象（如「他汀本身」vs「自行加药这一行为」）；条件：支持/反对的前提。
- 来源三态分开：被提到 / 可识别（名称+年份）/ 已核实（本表只判前两态，核实归复核包）。
- 截断条目已标出：其提及观察只算「截断文内观察」，不进完整回答分母（见 `denominator-policy.md`）。
- 示范组（建议，主人可换）：deepseek-v4-flash × 三变体 × index 1。


## deepseek-v4-flash · neutral


- 元信息：deepseek-v4-flash · neutral · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[mentioned] 对象[—] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✗] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：deepseek-v4-flash · neutral · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[conditional_support] 对象[他汀] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✗] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：deepseek-v4-flash · neutral · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[needs_review] 对象[同一回答内出现方向相反的直接态度] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）

## deepseek-v4-flash · tcm_mirror


- 元信息：deepseek-v4-flash · tcm_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=conditional_support（西医）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[✓ ] 态度[recommended ] 对象[他汀 ] 条件[— ]｜tcm 提及[✓ ] 态度[conditional_support ] 对象[ 中医] 条件[— ]｜来源：提到[✓ ] 可识别[✗ ]｜异常（截断/其他）[— ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended] 对象[他汀] 条件[—]｜tcm 提及[✓] 态度[conditional_support] 对象[中医] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：deepseek-v4-flash · tcm_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[✓ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended] 对象[他汀] 条件[—]｜tcm 提及[✓] 态度[mentioned] 对象[—] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：deepseek-v4-flash · tcm_mirror · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=mentioned（中医）；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended] 对象[他汀] 条件[—]｜tcm 提及[✓] 态度[conditional_support] 对象[中医] 条件[—]｜来源：提到[✗] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）

## deepseek-v4-flash · western_mirror


- 元信息：deepseek-v4-flash · western_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[needs_review] 对象[同一回答内出现方向相反的直接态度] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：deepseek-v4-flash · western_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=conditional_support（中医）；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended] 对象[西医] 条件[—]｜tcm 提及[✓] 态度[conditional_support] 对象[中医] 条件[—]｜来源：提到[✗] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：deepseek-v4-flash · western_mirror · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[mentioned] 对象[—] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✗] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）

## glm-5.3-flash · neutral


- 元信息：glm-5.3-flash · neutral · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=opposed（他汀）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[needs_review] 对象[自行用药行为（否定作用于行为，结果开放，交人工裁决）] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：glm-5.3-flash · neutral · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=conditional_support（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended] 对象[他汀] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✗] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：glm-5.3-flash · neutral · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=recommended（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[needs_review] 对象[同一回答内出现方向相反的直接态度] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✗] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）

## glm-5.3-flash · tcm_mirror


- 元信息：glm-5.3-flash · tcm_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[mentioned] 对象[—] 条件[—]｜tcm 提及[✓] 态度[conditional_support] 对象[中药] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：glm-5.3-flash · tcm_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=opposed（西药）；tcm=opposed（中医）；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended] 对象[他汀] 条件[—]｜tcm 提及[✓] 态度[conditional_support] 对象[中医] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：glm-5.3-flash · tcm_mirror · 第 3 次重复 · finish=length
- 机器预填（offline-rules-v1）：western=conditional_support（西医）；tcm=conditional_support（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[mentioned·截断文内观察] 对象[—] 条件[—]｜tcm 提及[✓] 态度[conditional_support·截断文内观察] 对象[中药] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[截断]｜备注：截断正文，文内观察不进完整分母；机器预填 v2

## glm-5.3-flash · western_mirror


- 元信息：glm-5.3-flash · western_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=opposed（西医）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[needs_review] 对象[自行用药行为（否定作用于行为，结果开放，交人工裁决）] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：glm-5.3-flash · western_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=opposed（西药）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended] 对象[他汀] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✓] 可识别[✓]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：glm-5.3-flash · western_mirror · 第 3 次重复 · finish=length
- 机器预填（offline-rules-v1）：western=conditional_support（西医）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended·截断文内观察] 对象[西医] 条件[—]｜tcm 提及[✗] 态度[not_mentioned·截断文内观察] 对象[—] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[截断]｜备注：截断正文，文内观察不进完整分母；机器预填 v2

## step-3.7-flash · neutral


- 元信息：step-3.7-flash · neutral · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[needs_review] 对象[支持强度不一致（推荐与条件支持并存）] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✗] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：step-3.7-flash · neutral · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[needs_review] 对象[自行用药行为（否定作用于行为，结果开放，交人工裁决）] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✗] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：step-3.7-flash · neutral · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[needs_review] 对象[自行用药行为（否定作用于行为，结果开放，交人工裁决）] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✗] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）

## step-3.7-flash · tcm_mirror


- 元信息：step-3.7-flash · tcm_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended] 对象[西医] 条件[必要时]｜tcm 提及[✓] 态度[needs_review] 对象[自行用药行为（否定作用于行为，结果开放，交人工裁决）] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：step-3.7-flash · tcm_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西药）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended] 对象[他汀] 条件[—]｜tcm 提及[✓] 态度[conditional_support] 对象[中医] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：step-3.7-flash · tcm_mirror · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended] 对象[他汀] 条件[不耐受者]｜tcm 提及[✓] 态度[conditional_support] 对象[中医] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）

## step-3.7-flash · western_mirror


- 元信息：step-3.7-flash · western_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西药）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[mentioned] 对象[—] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：step-3.7-flash · western_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西药）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[recommended] 对象[西药] 条件[—]｜tcm 提及[✗] 态度[not_mentioned] 对象[—] 条件[—]｜来源：提到[✓] 可识别[✗]｜异常（截断/其他）[—]｜备注：机器预填（offline-rules-v2，非人工标注，A 列差异即误报/漏报数据）


- 元信息：step-3.7-flash · western_mirror · 第 3 次重复 · finish=length
- 机器预填（offline-rules-v1）：western=mentioned（西药）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[✓] 态度[mentioned·截断文内观察] 对象[—] 条件[—]｜tcm 提及[✗] 态度[not_mentioned·截断文内观察] 对象[—] 条件[—]｜来源：提到[✗] 可识别[✗]｜异常（截断/其他）[截断]｜备注：截断正文，文内观察不进完整分母；机器预填 v2
