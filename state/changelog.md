# 决策记录

2026-09-09：按用户指定在 02-work/MedMirror 建立独立系统；课程仓库只作为上游参考。采用 src/ 程序与 runs/ 实验产物，后者不属于可弃临时材料。采用有限证据追问作为第一版自主分支。初始化不安装模板里的可选扩展，不执行付费调用。方向来自已确认讨论，避免重复询问。

2026-09-09：系统分析收敛为“离线可回放 CLI → 三家最小官方 API 接入 → 固定基线 → 有界证据追问”。放弃第一版多病例、复杂 RAG、统一医学质量总分、无界补测和自动 Bias 裁决。StepFun 与 GLM 价格及 usage 仍是主要信息缺口。

2026-09-09：用户批准进入协议冻结与最小 API 接入准备；确认 50 元先只承诺被测模型 API，预算不足按每模型 1 次优先缩减，中西医镜像作为提示敏感性实验。冻结协议 v1.0；未配置密钥，付费批量仍被闸门阻断。

2026-09-09：用户提供 StepFun Step Plan Base URL `https://api.stepfun.com/step_plan/v1`；已更新 `configs/models.json`，实际请求路径将派生为 `/chat/completions`。StepFun 的模型权限、账户可用性与价格仍待核验，未发起网络请求。

2026-09-09：已创建 `.env.local` 本地密钥文件，初始为空；`.env.example` 保持为可提交的填写示例。密钥不会写入状态或日志。

2026-09-09：完成 `exp002-api-connectivity`；三家模型各发送 1 次最小请求，均返回 HTTP 200，确认鉴权、端点、模型名和响应结构可用。未保存回答正文，正式批量评测仍受价格与账户核验闸门约束。

2026-09-09：执行 `exp003-baseline` 小批次；经历 v1.0/v1.1 的思考输出截断后，冻结 v1.3（供应商级推理参数、4096 上限、最终正文必需）。最终 9/9 条成功，保留 usage 合计 21,530 tokens；未保存思考正文。

2026-09-09：用户补充 `step-3.7-flash` 计费：输入未命中 1.35 元/M、缓存命中 0.27 元/M、输出 8.1 元/M。已写入 `configs/models.json`；按 v1.3 保留 usage 估算 StepFun 成本约 0.0607 元，未计入历史重试请求。

2026-09-09：用户补充 DeepSeek 高峰/闲时价格和 GLM-5.3-Flash 当前/刊例价格；已写入 `configs/models.json`。按高峰价估算 v1.3 保留 usage 的三家成本约 0.1106 元，历史重试请求另计。

2026-09-09：`exp003-baseline` 扩展完成 27/27；保留 usage 68,665 tokens，按登记价格与 DeepSeek 高峰价估算约 0.3720 元。离线提取报告已刷新，未形成医学质量或 Bias 结论。

2026-09-09：流程复盘：基线原型先于 Issue 入口推进，记录为流程偏差；新增 `docs/plan/001_autonomous-evaluation-loop.md`，后续自主追问开发按 Issue 细化、验收和回归执行。

2026-09-09：只读核对 CNB Issue #1-#6；确认 #1、#3 内容已落后于 27 条基线和价格登记，#2 的次数约束需修正，#4/#5/#6 可继续保留。

2026-09-09：规则层入口与 CI 闸门定为项目基线（PR #7，分支 `ci/four-gates`）。变了什么：新增 `pyproject.toml` + `uv.lock` + `.python-version`（Python 3.13、src 布局、hatchling 可编辑安装、dev 依赖 pytest/ruff 锁版本），入口统一为 `uv run pytest`；新增 `.cnb.yml` 四闸（ruff format --check / ruff check / pytest / check-manifests），push main 与 pull_request 双向触发。为什么变：评审指出规则层只有用例没有入口、也没有自动化闸门，「违反即报错」退化成「想起来才跑」。对你意味着什么：**main 已有分支保护（禁直推 + 需通过状态检查），直推被远端拒绝，此后所有改动必须走分支 → PR → CI 绿 → 人工合并**；合并 PR #7 后本地执行 `git checkout main && git pull`（已于当日完成，main → b722beb）。

2026-09-09：用户要求对照课程与 A4 赛题复盘并交接。新增 plan/002，记录真实截断、分组覆盖、语义误识别与预算/恢复缺口；下一步回到标准发现包与离线报告修复。核实 PR #9 已在本地合并历史；更正原始数据位置。未修改原始数据、未变更研究协议、未调用付费 API、未发布 Issue 或 PR。

2026-09-09：经用户授权修改远程 Issue：更新 #2–#6、新增 #10–#13，均回读核验标题、正文和优先级成功。修正自主追问依赖顺序，保留 #1 已关闭状态；实际账号负责人未擅自分配。

2026-09-09：按用户确认保留 Issue 编号，以【阶段1】/【阶段2】/【阶段3】/【后置】标记九条开放任务的标题。回读验证只改标题；README 与接手入口增加统一开发队列。未提交或推送本地文档。

2026-09-09：issue #11 发车（dev-launch）。AI/人工分工按 issue 正文执行：AI 交付材料与工具（负例集、check 脚本、标注工作表、发现包骨架），语义判定全部留 pending_owner_confirmation 待主人确认，不冒充已确认标准。在途 plan/002 文档经用户授权走 PR #14 合并。分母口径定为 planned=27、完整=24（stop）、截断=3（length 单列，不算未提及、不进完整分母），draft 待主人确认后并入 specs/calibration.md。全程离线零 API 调用。

2026-09-09：PR #15 经五轮双谱系评审收敛（GPT 系 codex 共 15P0+3P1+2P2+1P3，DeepSeek 系 opencode 共 2P1+8P2+9P3，后者两轮独立判定收敛并逐项核验引文/统计/预填无事实错误、无越界冒充人工定标）。修复要点：check 脚本类型闸全链路（引文/来源字段/mentioned/state/kind/status/trial_id/finish_reason）、--baseline 独立身份校验、失败×截断重叠报错、工作表覆盖保护、denominator_effect 与 substitution/adjunct 结构化落点。人工定标护栏（全 pending、require-confirmed 全量）已在测试与文档注明流转语义。
