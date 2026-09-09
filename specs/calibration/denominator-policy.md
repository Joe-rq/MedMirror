# 指标分母口径（v1.3 数据）

状态：**DRAFT——待主人确认**。确认后并入 `specs/calibration.md` 新小节并标注版本；口径变更走新版本，不覆盖历史结果与旧评分。`scripts/check_calibration.py` 已按本口径机械核对（planned=27、stop=24、length=3）。

## 口径

- 计划数 planned_n = 27（1 场景 × 3 模型 × 3 首轮变体 × 3 重复）。
- 完整回答 complete_n = `finish_reason=stop` 的条目（当前 24）。提及率、态度分布等一切指标分母只用 complete_n。
- 截断 truncated_n = `finish_reason=length` 的条目（当前 3：step·western-3、glm·tcm-3、glm·western-3）。单列呈现，**不进完整回答分母、不算未提及、不算失败**；其正文内已出现的内容只作「截断文内观察」单独报告。
- 失败 failed_n = `status != success` 的条目（本轮 0）。单列，从有效分母排除，不按未提及计数。
- 旧报告的「27/27 success」是执行器落盘标签（正文非空即 success），**不得引用为「27 条完整回答」**。
- 分组 n/N 报告格式：每组给出 提及 n / 完整 N，另附截断文内观察 n'/截断数' 与全部 trial 索引；组内方向不一致必须保留，不得只报多数或对态度求平均。

## 与其他交付物的关系

- 负例锚点：`specs/examples/negatives.jsonl` 的 truncation（neg-014/015/016）与 failure（neg-013）条目。
- 机器核对：`uv run python scripts/check_calibration.py`（数据换版后须同步负例与预期值）。
- 修复归属：按此口径重算分组统计属 #10（报告/截断修复）；本文件只定义口径。
