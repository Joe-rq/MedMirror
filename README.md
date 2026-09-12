# MedMirror

医疗模型治疗路径呈现差异评测系统。用自主开发方法，构建一个能在限定预算内自主开展受控评测、追问并交付可复核实验发现包的系统。

- [方向](.42cog/intent.md)
- [约束与资源](.42cog/real.md)
- [报告标准和实验草案](specs/calibration.md)
- [工作状态与下一步](state/board.md)
- [Agent 开工入口](AGENTS.md)
- [**接手开发（第二人及其 AI）**](docs/onboarding/README.md)

## 现状（2026-09-12）

意向书三支柱已全部落地，**30 条真实模型回答**（27 基线 + 3 有界追问，预算 1 元档实际花费 0.0690 元）与完整证据链入库：

- **受控评测**：协议 v1.3（1 合成病例 × 3 问法 × 3 模型 × 3 重复）；提取器 offline-rules-v2（六值态度 + 逐字引文 + 来源三态分离，语义未定标待 #11 人工标注回流）
- **有界追问**（followup-rules-v1）：固定触发规则（中性全未提及 + 镜像完整可定位提及）、每模型 ≤2 / 全轮 ≤6、按实际调用计额、预算硬闸、崩溃可恢复——真实观察：deepseek 完整作答并自述 AHA/ASA 2011 等来源、step 截断作答引中国指南、glm 两次思考耗尽零正文（供应商差异实证）
- **可复核发现包**：`specs/review/` 两层复核表（判定后置：先开放式后候选核对，引文逐字机械校验）、Word 分发闸门、候选池 20 条（分布备注已逐断言机器复算）；追问自述来源的文献存在性查证（`docs/experiments/exp003-baseline/followup/source-verification.md`，18 条目三态：8 可定位/6 部分相符/4 无法定位）
- **工程底座**：175 项离线测试 + CI 四闸 + 预算账本（reserve→settle/refund）+ 独立 run 目录恢复语义；每个 PR 经双谱系独立评审（GPT 系 + MiniMax 系）

**人工定标与专业复核尚未完成，不输出医学 Bias 结论。** 剩余人工环节：#11 27 条标注、#5 联系复核人（候选池必核子集 10 条已定稿 FINAL，#29 查证产物已过目关闭）。

## 接下来做什么

开放队列：#11 人工定标（27 条标注）、#5 复核人员与材料发送（#20 候选池已定稿、#29 查证已关闭、#4 备份已落地）。完整阶段与依赖见 [接手开发队列](docs/onboarding/README.md#开发队列按阶段与依赖不按-issue-编号)。

## 环境与四闸

```bash
uv sync                                  # 自动装 Python 3.13 与 pytest/ruff（版本由 uv.lock 锁死）
cp .env.example .env.local               # 再填三家 key，禁止提交
uv run ruff format --check .             # 闸1 格式
uv run ruff check .                      # 闸2 写法
uv run pytest                            # 闸3 逻辑（175 用例）
uv run python scripts/check-manifests.py # 闸4 包清单冒烟
```

这四条就是 CI 跑的四闸，定义见 [.cnb.yml](.cnb.yml)。本地通过是提交前检查；远程 CI 仍需实际确认，研究语义与医学判断另行验收。

## 协作流程

main 已设分支保护（禁止直推 + 需通过状态检查），每个改动都走：

**issue（自己写）→ 分支 → PR → CI 四闸绿 → 人工合并 → 关 issue**

完整接手清单、工具链与边界见 [docs/onboarding/README.md](docs/onboarding/README.md)。

## 结构
规约：.42cog/、specs/、CLAUDE.md。来源：vault/、notes/、resources/。方法：skills/、scripts/。作品：src/、runs/。状态：state/、docs/。过程：_tmp/、_build/、_archive/。

## 密钥与数据

密钥配置模板为 `.env.example`；实际密钥放 `.env.local`，禁止提交、禁止打印。`resources/` 与 `runs/` 不入库，克隆后需另行准备（见接手说明第 6 节）。
