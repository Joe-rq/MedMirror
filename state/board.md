# 工作状态

## 已完成
2026-09-09：六组骨架、本地 Git 已初始化并完成首次提交（root-commit e93e81b）、Codex 入口、意向与现实约束、实验标准和四步方法草案已建立。远程 `origin` 已配置。无 API 调用、无依赖安装、无评测实现。
2026-09-09：完成系统分析初稿 `docs/research/001_med-first-run/`。决定先做离线可回放 CLI、三家最小 API 请求和有界追问；首轮只报告描述性呈现差异，不判定医学 Bias。
2026-09-09：补充 GitHub 参考登记：PhysicianBench、RxSafeBench、LiveMedBench、tracelens、harness-evals。结论是借鉴任务/trace/rubric/校准/成本字段，不 Fork 大型项目。
2026-09-09：按取材规则浅克隆 PhysicianBench、RxSafeBench、tracelens 到 `resources/`；记录 commit 与许可证，参考区已被 Git 忽略，不进入作品区。
2026-09-09：完成三仓源码级取材，结论写入 `docs/research/001_med-first-run/github-notes.md`：采用任务级运行目录、追加式轨迹、版本化 rubric、诚实分母和评分校准；不引入 EHR/FHIR、Langfuse 或大型多 Agent。
2026-09-09：执行 `exp001-protocol-smoke` 通过。6 条固定样本中 5 条有效、1 条模拟失败；4 个契约测试通过。第一次测试发现并修正了来源识别和明确推荐提取的两个问题。
2026-09-09：协议 v1.0 已冻结，新增 `configs/models.json`、统一 Provider 配置层和 `scripts/check_api_config.py`。9 个本地测试通过；三家密钥已配置，但价格与账户核对未完成，付费批量仍被阻断。
2026-09-09：用户补充 StepFun Step Plan Base URL `https://api.stepfun.com/step_plan/v1`；Provider 已派生出 `https://api.stepfun.com/step_plan/v1/chat/completions`，未发起 API 请求。
2026-09-09：已创建本地 `.env.local` 空白密钥文件，保留 `.env.example` 作为填写示例；三家密钥仍为空，配置检查未发起网络请求。
2026-09-09：用户已填写 `.env.local`；修正 Provider 配置检查，使其自动读取本地文件且不覆盖进程环境变量、不打印 Key。
2026-09-09：模型参数改为“`configs/models.json` 默认目录 + `.env.local` 可选覆盖”；三家模型名与 Base URL 已写入本地环境示例，Key 仍只保留在本机。
2026-09-09：执行 `exp002-api-connectivity`；DeepSeek、StepFun、GLM 各 1 次最小请求均返回 HTTP 200，`choices` 与 `usage` 均存在。未保存回答正文。
2026-09-09：完成 `exp003-baseline` 小批次（v1.3）；9/9 条最终答案成功落盘，累计保留 usage 计 21,530 tokens。离线提取报告已生成；该样本每个模型和变体仅 1 次重复，不作质量或 Bias 结论。
2026-09-09：用户补充 `step-3.7-flash` 价格（输入未命中 1.35 元/M、命中 0.27 元/M、输出 8.1 元/M）；已写入模型目录，StepFun 价格缺口解除。当前 v1.3 小批次 StepFun 估算成本约 0.0607 元（按输入未命中计算）。
2026-09-09：用户补充 DeepSeek 高峰/闲时价格与 GLM-5.3-Flash 当前价格；已写入模型目录。按保守高峰价估算，v1.3 保留 usage 的三家合计约 0.1106 元（不含历史重试和实际账单差异）。
2026-09-09：按确认价格将 `exp003-baseline` 扩展到完整 27 条；27/27 最终答案成功，保留 usage 68,665 tokens，按登记价格与 DeepSeek 高峰价估算约 0.3720 元。离线提取与描述性报告已刷新。
2026-09-09：流程纠偏：此前基线执行属于 Issue 入口建立前的部分实现，现将下一阶段正式登记为 `docs/plan/001_autonomous-evaluation-loop.md`，后续先按 Issue 验收再开发自主追问。
2026-09-09：只读核对 CNB `joe-rq/MedMirror` 的 6 条 Issue：拆分方向整体正确；#1（扩展 27 条）和 #3（核价闸门）已因当前进度变为过时状态，#2 需改为“每模型最多 2 次、全轮最多 6 次”并更新协议版本为 v1.3，#4/#5/#6 仍有效。
2026-09-09：规则层入口与 CI 闸门落地（分支 `ci/four-gates`，PR #7）：`pyproject.toml` + `uv.lock` + `.python-version` 锁版本，入口统一为 `uv run pytest`（13/13）；`.cnb.yml` 四闸（ruff format --check / ruff check / pytest / check-manifests）。干净 worktree 预验全绿；离线回放 exp001/exp003 产物字节级一致。CNB CI 实跑 18.2s 全绿（日志确认四闸依次通过，Python 3.13.15）。**main 已有分支保护：禁直推 + 需通过状态检查**，直推被远端拒绝，本变更走 PR，已由维护者合并（PR #7 → b722beb），本地已同步并清理已合并分支。
2026-09-09：接手材料落地（分支 `docs/onboarding`，PR #8）：新增 `docs/onboarding/README.md`（环境与四闸、开工第一步读 issue、issue→分支→PR→CI 绿→人工合并、全局技能清单、克隆后缺什么、边界、两件待定团队约定），README 修正三处过期陈述。干净 clone 实测：`uv sync` + 四闸四条命令全部通过。CI 17.6s 全绿。

## 下一步
下一步先把工作树里 exp003 的 27 条结果与 `docs/plan/001` 提成 PR（让 main 与工作树自洽，issue #2 与 plan/001 都按 27 条写）；随后共同抽查 27 条原始回答与提取结果，确认否定、条件推荐和未提及的提取边界，再实现并运行有限追问分支。

## 待办与不确定性
- 远程 `origin` 已配置；忽略的 runs/ 仍需另行备份。
- .env.local 已配置；不打印任何密钥。
- 50 元暂按评测 API 预算理解，开发费用口径未确认。
- 完整 27 条保留 usage 为 68,665 tokens；早期协议修订与失败重试的历史消耗未完整回算，最终金额仍以供应商账单为准。
- 四步技能为项目草案，换谱系对抗性评审待进行；不因此阻止离线协议冒烟，不启动真实批量实验。
- 临床合理性专业复核人员尚缺。
- 27 条真实回答与提取结果的人工定标仍未开始（`specs/calibration.md` 三件套 standard/negatives/check 尚未产出）。

## 放权
已确认范围内开发、离线验证、修复连续推进；变更标准、扩大付费范围、发布交由用户决定。系统分析文档尚未提交 Git。
