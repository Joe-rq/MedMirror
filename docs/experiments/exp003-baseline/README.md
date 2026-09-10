# exp003-baseline

固定一个颈动脉斑块咨询场景，先运行 3 个模型 × 3 个提示变体 × 1 次重复的 9 条小批次，验证正式基线执行器的原始记录、usage、失败状态和恢复能力。

当前小批次采用 `calibration-v1.3`：统一使用 `max_tokens=4096`，按供应商能力设置推理参数（DeepSeek 关闭思考、StepFun 使用低推理强度、GLM 保留默认思考），保存最终 `content` 和思考字段元数据，不保存思考正文。该实验只记录模型原始回答，不在本阶段作医学质量或 Bias 结论。

小批次已按确认价格扩展到完整 27 条（3 模型 × 3 问法 × 3 重复）；其中 24 条正常结束、3 条因 `max_tokens` 截断，分组与截断统计见 `derived-v2/analysis.md`。

## 目录

- `result/`：原始回答（trials.jsonl）与 v1 时期派生报告，只读，脚本不得覆写。
- `derived-v2/`：offline-rules-v1 提取快照 + report-v2 产物（冻结保留，issue #10 交付）。
- `derived-v3/`：offline-rules-v2 提取 + report-v2 产物 + `extraction-diff.md`（v1→v2 逐条差异与需人工复核清单，issue #12 交付）。

## 运行入口

```bash
# 在线采集（付费，需显式允许并配置密钥）
python3 scripts/run_exp003_baseline.py --repeats 3 --allow-paid

# 离线重放（无密钥、无网络；相同输入字节一致；--output 指向 result/ 或其上/下级会被拒绝）
uv run python scripts/report_exp003.py --input docs/experiments/exp003-baseline/result/trials.jsonl --output docs/experiments/exp003-baseline/derived-v3

# 提取器版本差异（v1 快照 vs 当前版本）
uv run python scripts/diff_extractions.py
```

> 读取固定 UTF-8、派生产物换行固定 LF，跨平台字节一致。
