# 认知模型

协议定义病例、提示变体、模型配置与指标。一次 Run 包含多个 Trial；Trial 保存全部输入、回答、用量、错误与唯一编号。Extraction 将原文映射为指标并附逐字引文。Finding 引用 Trial 与 Extraction，表达观察而非医学裁决。Followup 关联 parent_trial_id，属于独立探索分组。Review 保存待复核问题、来源与人工意见。BudgetLedger 保存预留和结算；State 支持中断恢复。

方向与验证闭环见 intent.md；具体标准见 ../specs/calibration.md。

