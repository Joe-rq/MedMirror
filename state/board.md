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

## 当前审计结论（2026-09-09）

本地 HEAD 209d04c 已包含 PR #9 的 27 条结果与 plan/001，以及 PR #8 接手文档；旧的“先提交结果 PR”待办已完成。当前原始回答实际在 Git 跟踪的 `docs/experiments/exp003-baseline/result/trials.jsonl`，不是忽略的 runs/。

离线审计发现：27 条有正文，其中 24 条正常 stop、3 条 length 截断；提取器存在否定对象串扰与来源误识别；分组 paths 被最后一条覆盖；运行器尚无预算预留、配置快照和追加式 attempt 保护。四闸仍通过（13/13），不能据此判定研究验收通过。本次只更新交接文档，未修代码、未调用 API。

## 下一步

按 `docs/plan/002_prototype-calibration-handoff.md` 先做人工标准发现包与离线分组报告修复；补评分定标和运行护栏后再执行 plan/001 的有界追问。建议项目主人负责标准、证据与结论，伙伴负责实现、回放和恢复。新控制实验为待确认建议，不变更 v1.3。

## 待办与不确定性
- 远程 `origin` 已配置；忽略的 runs/ 仍需另行备份。
- .env.local 已配置；不打印任何密钥。
- 50 元暂按评测 API 预算理解，开发费用口径未确认。
- 完整 27 条保留 usage 为 68,665 tokens；早期协议修订与失败重试的历史消耗未完整回算，最终金额仍以供应商账单为准。
- 四步技能为项目草案，换谱系对抗性评审待进行；不因此阻止离线协议冒烟，不启动真实批量实验。
- 临床合理性专业复核人员尚缺。
- 27 条真实回答与提取结果的人工定标仍未开始（`specs/calibration.md` 三件套 standard/negatives/check 尚未产出）。

## 放权
已确认范围内开发、离线验证、修复连续推进；变更标准、扩大付费范围、发布交由用户决定。系统分析、27 条结果和 plan/001 已在本地合并历史中；本轮计划 002 与状态纠正尚未提交。

## 远程 Issue 复查（2026-09-09）

本轮只读核实：共 6 条，#1 已关闭，#2–#6 开放且未分配负责人。#2 的 v1.3 与次数约束已修正；#3 已登记价格但仍缺账单核对，且正文未覆盖代码预算闸门。建议保持 #1 关闭、补 #2 前置依赖和 #3 工程验收、细化 #4 恢复演练与 #5 复核安排、后置 #6；新增报告/截断、人工定标、提取修复、运行保护四项。详细建议见 plan/002 第 7 节；远程更新结果见下节。

## 远程 Issue 已更新（2026-09-09）

按用户明确指令，已更新并逐项回读验证 #2–#6；新增并回读验证 #10 报告/截断（P0）、#11 人工定标（P0）、#12 提取器修复（P0）、#13 运行记录保护（P0）。#2 依赖 #10/#11/#12/#3/#13；#3 补预算程序验收；#4 升 P1 并验恢复演练；#5 升研究侧 P0 并明确复核范围与排期；#6 保留 P2 后置。#1 保持关闭。未猜测伙伴账号，实际负责人仍待团队认领，正文已给出建议分工。

当前开工入口：伙伴优先 #10，主人同步 #11 与 #5；后续 #12、#3/#13，最后 #2。所有任务包含自足验收及实际编号依赖，不依赖尚未提交的本地 plan/002。未提交或推送本地文档，未运行评测 API。

## Issue #11 材料包开发（2026-09-09，分支 calibration/issue-11-materials）

AI 侧交付物落地：`specs/examples/negatives.jsonl`（17 条负例：未提及/否定/条件支持/推荐/对象串扰/替代-辅助/来源误识别/提到未核实/失败/截断/相反回答，全部 pending_owner_confirmation，含真实 trial 引用与逐字引文）、`scripts/check_calibration.py`（结构、逐字引文子串、trial 引用、kind 覆盖、27=24+3 分母口径机械核对，`--require-confirmed` 供定标完成后启用）+ `tests/test_check_calibration.py`、`specs/calibration/`（27 条标注工作表含 offline-rules-v1 机器预填与两人空白栏、分歧裁决记录模板、分母口径 draft）、`specs/examples/standard-finding.md` 骨架（OWNER_TO_CONFIRM/MACHINE_PREFILL 占位）、`specs/examples/README.md`、`scripts/gen_annotation_worksheet.py`（默认拒绝覆盖已有工作表）。四闸与测试全绿，CNB CI 实跑绿。在途文档已走 PR #14 合并。经五轮双谱系评审（GPT 系 codex + DeepSeek 系 opencode）：R1 codex 5P0+2P1、opencode 2P1+6P2+4P3；R2 codex 4P0+1P2、opencode 1P2+2P3；R3 codex 4P0、opencode 3P3 判定收敛；R4 codex 2P0、opencode 0 新 P0 并确认同款已修；R5 codex 定向终验「两项修复确认闭环，未发现新问题」——两谱系全部发现均已处置，收敛达成。人工环节（主人逐条确认负例、两人独立标注、裁决、示范确认）未开始；issue #11 保持 open。实现规格已评论回填 issue #11。

## 开发队列已标识（2026-09-09）

用户确认后已为九条远程开放 Issue 添加标题前缀并逐条回读：阶段1 #10/#11/#5；阶段2 #12/#3/#13；阶段3 #2/#4；后置 #6。编号、正文、优先级、状态及负责人未改。统一队列写入 docs/onboarding/README.md，项目 README 增加开工入口；伙伴先 #10，主人同步 #11/#5。阶段为推进顺序，具体依赖按正文；#4 可在回放与目录就绪后提前。远程标题已生效，本地交接文档仍待提交。

## Issue #10 实现完成（2026-09-09，分支 feat/issue-10-offline-report）

离线分组报告修复落地：新增 `src/medmirror/reporting.py`（试次五类分类、分组聚合、md/json 渲染，复用 protocol 提取，不改提取器），`scripts/report_exp003.py` 重写为 `--input/--output/--repeats` CLI；派生产物写新目录 `docs/experiments/exp003-baseline/derived-v2/`（27 计划／24 完整／3 截断单列／0 失败／0 未执行／9 组，LF 换行跨平台字节一致），输出指向原始数据目录本身/子目录/祖先目录或换 input 绕过均拒绝执行；`result/` 原始数据与旧报告零改动（CLI 测试含目录哈希校验）。新增 `tests/test_report_exp003.py` 23 例（相反结果 fixture 顺序无关、截断/失败/未执行/空与空白正文/计划外/词表与路径集漂移/元数据与 vendor 不一致分类、真实 27 条回归、CLI 防覆盖与重复运行字节一致、成本数值钉死、md 表格列一致性），四闸 36/36 全绿。语义分母默认"计划内完整试次"并标注待 #11 定标确认；截断观察单列不进分母。已回填 issue #10 认领与实现规格评论；/simplify 与 pr-ready 三审计通过；双谱系评审（codex/gpt-5.6-luna + opencode/deepseek-v4-pro）三轮收敛：第一轮 3 P1 + 8 P2、第二轮 4 P2 全部闭环，DeepSeek 第二轮已给"可合并"，codex 第三轮定向核验中。附带修复：`protocol.load_jsonl` 与 `providers.load_catalog` 补 utf-8 读取（纯 I/O，非提取器语义）、`atomic_write_jsonl` 换行固定 LF（保护未来 trials.jsonl 不被 CRLF 化）、根 README 用例数更正。

## Issue #12 实现完成（2026-09-10，分支 feat/issue-12-extractor-v2）

提取器升级 offline-rules-v2：`protocol.py` 改子句级关系分析（元描述过滤、自服行为否定→needs_review、替代/辅助分离编码、引语回声抑制、条件子句并入引文、多子句异向→needs_review），来源识别收紧为书名号/机构名/年份紧邻（年龄+泛指南不再命中）。新增 `tests/test_protocol_v2.py` 17 例（负例 harness：严格类逐字段断言+引文子串；truncation/failure/contradicted 为信息类；自由文本字段仅验原文性）；`test_exp001.py` 的 smoke-002 期望按 neg-007 改为 needs_review；reporting 词表扩 needs_review。新增 `scripts/diff_extractions.py` 与 `derived-v3/`（v2 提取+report+逐字段差异）：27/27 条实质变化（含来源识别 6 处 True→False、六值状态与替代/辅助/对象/条件新字段）、9 条进需人工复核清单（自服否定/混合方向/强度不一致，交 #11 裁决）。derived-v2 冻结为 v1 快照，result/ 零改动。正式语义验收待 #11 人工定标（负例集全部 pending_owner_confirmation，主人批改 negatives-review.md 后回流）。


## Issue #12 双谱系评审收尾（2026-09-10）

三轮收敛：R1 codex 1P0+5P1+2P2（不可合并）、DeepSeek 1P1+3P2+2P3（需修改后合并）→ 全部闭环（derived-v2 冻结守卫、元描述片段剥离、条件邻接绑定、裸机构名剔除、告知句与"需"字推荐修复、冒号条件切分、引语回声闭合可选、冲突态双引文、diff 全字段+实质/新增分计+单元格清洗）；R2 复核 DeepSeek 判可合并（11/11 关闭）、codex 新提 4 项（冲突引文丢失 P1 等）亦已闭环（含元描述连宾语剥离与回声片段分层处理）。四闸 78/78 + check_calibration 全绿；negatives 严格 16/16、neg-016 分歧钉死为信息类。正式语义验收仍待 #11。
