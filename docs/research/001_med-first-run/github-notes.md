# GitHub 参考取材笔记

日期：2026-09-09。三份仓库均为 `depth=1` 浅克隆，仅作只读参考。

## PhysicianBench

来源：`resources/PhysicianBench`，Apache-2.0，commit `c7efa8f`。

重点文件：

- `scripts/run_task.py`：单任务端到端编排，建立 job 目录、执行 Agent、执行 verifier、写入元数据。
- `scripts/job_manager.py`：批次名包含时间、模型、推理配置和温度；任务结果落在 `jobs/<batch>/<task>/`。
- `agent/trajectory.py`：追加式 JSONL 轨迹；事件有 `type`、`content`、`metadata`，metadata 可放工具名和 token。
- `scripts/score_jobs.py`：从轨迹和 verifier 日志派生调用次数、检查点结果、成功率和多次运行聚合。

MedMirror 采用：

1. `runs/<run_id>/<model>/<case>/` 的任务级目录。
2. 追加式 `trials.jsonl` 与独立 `evaluations.jsonl`。
3. `run_config.json` 记录协议、模型、参数、版本和费用口径。
4. 中断恢复按唯一 `trial_id` 跳过已成功试次。

不采用：FHIR 容器、长程工具调用和 EHR 工作区；它们属于 PhysicianBench 的任务环境。

## RxSafeBench

来源：`resources/RxSafeBench`，CC0-1.0，commit `a25f9a1`。

数据文件：`data/RxSafeBench_Contradiction.json` 有 538 条，`data/RxSafeBench_Interaction.json` 有 696 条。样例将疾病适应症、候选药物、风险提醒、模拟对话和结构分数放在同一条记录中。

MedMirror 采用：

- 把病例上下文、预定义观察维度和原文证据放在一个可定位的 Case/Trial 关系中。
- 将安全维度拆开记录，而不是混成一个医学总分。
- 把“是否提到风险”与“风险判断是否正确”区分开。

不采用：它的药物风险标签和专家筛选数据不能直接成为本项目中西医比较的 ground truth；也不把其分数迁移到本项目。

## tracelens

来源：`resources/tracelens`，MIT，commit `302d874`。

重点文件：

- `packages/core/src/rubric.ts`：Rubric 有 `id`、`version`、维度、量表和适用条件；评分标准随 trace 版本路由。
- `packages/adapter-langfuse/src/pairing.ts`：按 `(trace_id, dimension)` 配对人类与 judge，只保留双方都有评分的样本，明确诚实分母。
- `packages/adapter-langfuse/src/calibration.ts`：分类指标给出 exact agreement、Cohen’s κ、混淆矩阵；数值指标给出容差内一致率、Pearson、均值和 bias delta；样本不足时做低置信标记。

MedMirror 采用：

1. `rubric_version` 与 `extractor_version` 随结果保存，旧结果不覆盖。
2. 人工评分与自动评分按 `trial_id + dimension` 配对。
3. 样本不足显示低置信度，不输出看似精确的总分。
4. 把分歧样本列成复核队列，保留双方数值和理由。

首版不采用：Langfuse、Node UI 和完整校准仪表盘；先用本地 JSONL 与 Markdown 报告验证数据契约。

## 对 MedMirror 的直接改变

参考项目共同支持四项实现决定：

- 原始回答、结构化提取、评分和报告分层保存。
- 评分标准必须版本化，不能在同一实验中悄悄换尺子。
- 预算、重试、token、费用和完成状态属于运行元数据。
- 自动评分只产生可解释的观察和待复核项，医学裁决仍需人工。

## 当前不做

不引入 EHR/FHIR、Langfuse、Docker、复杂前端、外部 benchmark 数据集或大型多 Agent 编排。它们不会改变首轮“一个病例是否能产出可追溯发现包”的判断。
