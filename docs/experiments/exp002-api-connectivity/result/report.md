# exp002 API Connectivity Report

- 实验状态：**PASS**
- 测试方式：每个模型 1 次最小请求，`max_tokens=8`，不保存回答正文。
- 结果：3/3 返回 HTTP 200，且响应包含 `choices` 和 `usage` 字段。

| 模型 | 端点结果 | 耗时 | 结构检查 |
|---|---:|---:|---|
| deepseek-v4-flash | 200 | 842 ms | `choices`、`usage` 均存在 |
| step-3.7-flash | 200 | 665 ms | `choices`、`usage` 均存在 |
| glm-5.3-flash | 200 | 1187 ms | `choices`、`usage` 均存在 |

## 结论

三家 Key、Base URL、模型名和请求格式均已实际打通。StepFun 的 Step Plan 路径可用。

本实验不判断回答质量、医学安全性或模型差异；正式评测仍须先完成价格与账户用量核验，并按 `specs/calibration.md` 执行固定协议。
