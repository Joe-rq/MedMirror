# exp002-api-connectivity

三家官方 API 的最小联通测试。每个模型只发送 1 次短请求，使用 `.env.local` 中的模型参数和 Key；不保存回答正文、不打印密钥。

运行入口：`python3 scripts/test_api_connectivity.py`

本实验只验证配置、网络、鉴权、模型名和 OpenAI-compatible 请求协议，不验证医学内容质量，也不等同于正式评测。
