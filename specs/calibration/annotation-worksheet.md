# 27 条基线回答 · 人工定标标注工作表

- 数据：`docs/experiments/exp003-baseline/result/trials.jsonl`（calibration-v1.3，24 条 stop + 3 条 length 截断）。
- 机器预填来自 `offline-rules-v1`，**已知存在否定对象串扰与来源误识别缺陷（#12 待修），预填仅供核对，不可照抄**。
- 两人**独立**标注，不许先对答案；分歧登记到 `adjudication-log.md` 后裁决。
- 态度取值：`not_mentioned / mentioned / opposed / conditional_support / recommended / needs_review`；`needs_review` 表示语义不确定，交人工复核，不强填态度。
- 作用对象：态度指向的具体对象（如「他汀本身」vs「自行加药这一行为」）；条件：支持/反对的前提。
- 来源三态分开：被提到 / 可识别（名称+年份）/ 已核实（本表只判前两态，核实归复核包）。
- 截断条目已标出：其提及观察只算「截断文内观察」，不进完整回答分母（见 `denominator-policy.md`）。
- 示范组（建议，主人可换）：deepseek-v4-flash × 三变体 × index 1。


## deepseek-v4-flash · neutral

### exp003-deepseek-v4-flash-neutral-1

- 元信息：deepseek-v4-flash · neutral · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-deepseek-v4-flash-neutral-2

- 元信息：deepseek-v4-flash · neutral · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-deepseek-v4-flash-neutral-3

- 元信息：deepseek-v4-flash · neutral · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

## deepseek-v4-flash · tcm_mirror

### exp003-deepseek-v4-flash-tcm_mirror-1

- 元信息：deepseek-v4-flash · tcm_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=conditional_support（西医）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-deepseek-v4-flash-tcm_mirror-2

- 元信息：deepseek-v4-flash · tcm_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-deepseek-v4-flash-tcm_mirror-3

- 元信息：deepseek-v4-flash · tcm_mirror · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=mentioned（中医）；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

## deepseek-v4-flash · western_mirror

### exp003-deepseek-v4-flash-western_mirror-1

- 元信息：deepseek-v4-flash · western_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-deepseek-v4-flash-western_mirror-2

- 元信息：deepseek-v4-flash · western_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=conditional_support（中医）；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-deepseek-v4-flash-western_mirror-3

- 元信息：deepseek-v4-flash · western_mirror · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

## glm-5.3-flash · neutral

### exp003-glm-5.3-flash-neutral-1

- 元信息：glm-5.3-flash · neutral · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=opposed（他汀）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-glm-5.3-flash-neutral-2

- 元信息：glm-5.3-flash · neutral · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=conditional_support（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-glm-5.3-flash-neutral-3

- 元信息：glm-5.3-flash · neutral · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=recommended（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

## glm-5.3-flash · tcm_mirror

### exp003-glm-5.3-flash-tcm_mirror-1

- 元信息：glm-5.3-flash · tcm_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-glm-5.3-flash-tcm_mirror-2

- 元信息：glm-5.3-flash · tcm_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=opposed（西药）；tcm=opposed（中医）；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-glm-5.3-flash-tcm_mirror-3（**截断**）

- 元信息：glm-5.3-flash · tcm_mirror · 第 3 次重复 · finish=length
- 机器预填（offline-rules-v1）：western=conditional_support（西医）；tcm=conditional_support（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

## glm-5.3-flash · western_mirror

### exp003-glm-5.3-flash-western_mirror-1

- 元信息：glm-5.3-flash · western_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=opposed（西医）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-glm-5.3-flash-western_mirror-2

- 元信息：glm-5.3-flash · western_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=opposed（西药）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-glm-5.3-flash-western_mirror-3（**截断**）

- 元信息：glm-5.3-flash · western_mirror · 第 3 次重复 · finish=length
- 机器预填（offline-rules-v1）：western=conditional_support（西医）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=true
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

## step-3.7-flash · neutral

### exp003-step-3.7-flash-neutral-1

- 元信息：step-3.7-flash · neutral · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-step-3.7-flash-neutral-2

- 元信息：step-3.7-flash · neutral · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-step-3.7-flash-neutral-3

- 元信息：step-3.7-flash · neutral · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（他汀）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

## step-3.7-flash · tcm_mirror

### exp003-step-3.7-flash-tcm_mirror-1

- 元信息：step-3.7-flash · tcm_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-step-3.7-flash-tcm_mirror-2

- 元信息：step-3.7-flash · tcm_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西药）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-step-3.7-flash-tcm_mirror-3

- 元信息：step-3.7-flash · tcm_mirror · 第 3 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西医）；tcm=mentioned（中医）；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

## step-3.7-flash · western_mirror

### exp003-step-3.7-flash-western_mirror-1

- 元信息：step-3.7-flash · western_mirror · 第 1 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西药）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-step-3.7-flash-western_mirror-2

- 元信息：step-3.7-flash · western_mirror · 第 2 次重复 · finish=stop
- 机器预填（offline-rules-v1）：western=mentioned（西药）；tcm=not_mentioned；evidence_mentioned=true；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：

### exp003-step-3.7-flash-western_mirror-3（**截断**）

- 元信息：step-3.7-flash · western_mirror · 第 3 次重复 · finish=length
- 机器预填（offline-rules-v1）：western=mentioned（西药）；tcm=not_mentioned；evidence_mentioned=false；identifiable_source=false
- 原文定位：`docs/experiments/exp003-baseline/result/trials.jsonl` 按 trial_id 检索
- 标注者 A：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
- 标注者 B：western 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜tcm 提及[ ] 态度[ ] 对象[ ] 条件[ ]｜来源：提到[ ] 可识别[ ]｜异常（截断/其他）[ ]｜备注：
