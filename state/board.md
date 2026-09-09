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

## 下一步
下一步先核对三家实际计费并共同抽查 9 条原始回答与提取结果；预算可接受后，将 `exp003-baseline` 从 9 条扩展到完整 27 条，再进入有限追问。

## 待办与不确定性
- 远程 `origin` 已配置；忽略的 runs/ 仍需另行备份。
- .env.local 已配置；不打印任何密钥。
- 50 元暂按评测 API 预算理解，开发费用口径未确认。
- 9 条小批次的保留 usage 为 21,530 tokens；此前截断和重试请求的历史消耗未完整回算，扩展前必须先按供应商账单或价格表核对。
- 四步技能为项目草案，换谱系对抗性评审待进行；不因此阻止离线协议冒烟，不启动真实批量实验。
- 临床合理性专业复核人员尚缺。

## 放权
已确认范围内开发、离线验证、修复连续推进；变更标准、扩大付费范围、发布交由用户决定。系统分析文档尚未提交 Git。
