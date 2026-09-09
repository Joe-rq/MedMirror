# MedMirror

医疗模型治疗路径呈现差异评测系统。用自主开发方法，构建一个能在限定预算内自主开展受控评测、追问并交付可复核实验发现包的系统。

- [方向](.42cog/intent.md)
- [约束与资源](.42cog/real.md)
- [报告标准和实验草案](specs/calibration.md)
- [工作状态与下一步](state/board.md)
- [Agent 开工入口](AGENTS.md)
- [**接手开发（第二人及其 AI）**](docs/onboarding/README.md)

## 现状

协议 v1.3 已冻结；三家官方 API 已接通；`exp003-baseline` 27/27 条真实回答已落盘（含 usage），离线提取与描述性报告可复现。**人工定标尚未完成，不输出医学 Bias 结论。**

## 环境与四闸

```bash
uv sync                                  # 自动装 Python 3.13 与 pytest/ruff（版本由 uv.lock 锁死）
cp .env.example .env.local               # 再填三家 key，禁止提交
uv run ruff format --check .             # 闸1 格式
uv run ruff check .                      # 闸2 写法
uv run pytest                            # 闸3 逻辑（13 用例）
uv run python scripts/check-manifests.py # 闸4 包清单冒烟
```

这四条就是 CI 跑的四闸，定义见 [.cnb.yml](.cnb.yml)。本地全绿 = 推送后不会红。

## 协作流程

main 已设分支保护（禁止直推 + 需通过状态检查），每个改动都走：

**issue（自己写）→ 分支 → PR → CI 四闸绿 → 人工合并 → 关 issue**

完整接手清单、工具链与边界见 [docs/onboarding/README.md](docs/onboarding/README.md)。

## 结构
规约：.42cog/、specs/、CLAUDE.md。来源：vault/、notes/、resources/。方法：skills/、scripts/。作品：src/、runs/。状态：state/、docs/。过程：_tmp/、_build/、_archive/。

## 密钥与数据

密钥配置模板为 `.env.example`；实际密钥放 `.env.local`，禁止提交、禁止打印。`resources/` 与 `runs/` 不入库，克隆后需另行准备（见接手说明第 6 节）。
