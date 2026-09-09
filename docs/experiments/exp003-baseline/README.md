# exp003-baseline

固定一个颈动脉斑块咨询场景，先运行 3 个模型 × 3 个提示变体 × 1 次重复的 9 条小批次，验证正式基线执行器的原始记录、usage、失败状态和恢复能力。

当前小批次采用 `calibration-v1.3`：统一使用 `max_tokens=4096`，按供应商能力设置推理参数（DeepSeek 关闭思考、StepFun 使用低推理强度、GLM 保留默认思考），保存最终 `content` 和思考字段元数据，不保存思考正文。正式协议仍规定每个组合重复 3 次；小批次通过后再扩展到 27 条。该实验只记录模型原始回答，不在本阶段作医学质量或 Bias 结论。

运行入口：`python3 scripts/run_exp003_baseline.py --repeats 1 --allow-paid`
