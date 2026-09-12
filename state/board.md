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

AI 侧交付物落地：`specs/examples/negatives.jsonl`（17 条负例：未提及/否定/条件支持/推荐/对象串扰/替代-辅助/来源误识别/提到未核实/失败/截断/相反回答，全部 pending_owner_confirmation，含真实 trial 引用与逐字引文）、`scripts/check_calibration.py`（结构、逐字引文子串、trial 引用、kind 覆盖、27=24+3 分母口径机械核对，`--require-confirmed` 供定标完成后启用）+ `tests/test_check_calibration.py`、`specs/calibration/`（27 条标注工作表含 offline-rules-v1 机器预填与两人空白栏、分歧裁决记录模板、分母口径 draft）、`specs/examples/standard-finding.md` 骨架（OWNER_TO_CONFIRM/MACHINE_PREFILL 占位）、`specs/examples/README.md`、`scripts/gen_annotation_worksheet.py`（默认拒绝覆盖已有工作表）。四闸与测试全绿，CNB CI 实跑绿。在途文档已走 PR #14 合并。经五轮双谱系评审（GPT 系 codex + DeepSeek 系 opencode）：R1 codex 5P0+2P1、opencode 2P1+6P2+4P3；R2 codex 4P0+1P2、opencode 1P2+2P3；R3 codex 4P0、opencode 3P3 判定收敛；R4 codex 2P0、opencode 0 新 P0 并确认同款已修；R5 codex 定向终验「两项修复确认闭环，未发现新问题」——两谱系全部发现均已处置，收敛达成。2026-09-10：主人完成 17 条负例人工批改（16 对 + neg-007 改判 conditional_support，两项裁决见 changelog），17/17 confirmed、--require-confirmed 转绿；配套审阅表 negatives-review.md 经双谱系评审修复后合并（PR #16/#18）。剩余人工环节：两人独立标注 27 条、示范组确认与 standard-finding 实质内容、留出样本误报/漏报（依赖 #12）；issue #11 保持 open。

## 开发队列已标识（2026-09-09）

用户确认后已为九条远程开放 Issue 添加标题前缀并逐条回读：阶段1 #10/#11/#5；阶段2 #12/#3/#13；阶段3 #2/#4；后置 #6。编号、正文、优先级、状态及负责人未改。统一队列写入 docs/onboarding/README.md，项目 README 增加开工入口；伙伴先 #10，主人同步 #11/#5。阶段为推进顺序，具体依赖按正文；#4 可在回放与目录就绪后提前。远程标题已生效，本地交接文档仍待提交。

## Issue #10 实现完成（2026-09-09，分支 feat/issue-10-offline-report）

离线分组报告修复落地：新增 `src/medmirror/reporting.py`（试次五类分类、分组聚合、md/json 渲染，复用 protocol 提取，不改提取器），`scripts/report_exp003.py` 重写为 `--input/--output/--repeats` CLI；派生产物写新目录 `docs/experiments/exp003-baseline/derived-v2/`（27 计划／24 完整／3 截断单列／0 失败／0 未执行／9 组，LF 换行跨平台字节一致），输出指向原始数据目录本身/子目录/祖先目录或换 input 绕过均拒绝执行；`result/` 原始数据与旧报告零改动（CLI 测试含目录哈希校验）。新增 `tests/test_report_exp003.py` 23 例（相反结果 fixture 顺序无关、截断/失败/未执行/空与空白正文/计划外/词表与路径集漂移/元数据与 vendor 不一致分类、真实 27 条回归、CLI 防覆盖与重复运行字节一致、成本数值钉死、md 表格列一致性），四闸 36/36 全绿。语义分母默认"计划内完整试次"并标注待 #11 定标确认；截断观察单列不进分母。已回填 issue #10 认领与实现规格评论；/simplify 与 pr-ready 三审计通过；双谱系评审（codex/gpt-5.6-luna + opencode/deepseek-v4-pro）三轮收敛：第一轮 3 P1 + 8 P2、第二轮 4 P2 全部闭环，DeepSeek 第二轮已给"可合并"，codex 第三轮定向核验中。附带修复：`protocol.load_jsonl` 与 `providers.load_catalog` 补 utf-8 读取（纯 I/O，非提取器语义）、`atomic_write_jsonl` 换行固定 LF（保护未来 trials.jsonl 不被 CRLF 化）、根 README 用例数更正。

## Issue #12 实现完成（2026-09-10，分支 feat/issue-12-extractor-v2）

提取器升级 offline-rules-v2：`protocol.py` 改子句级关系分析（元描述过滤、自服行为否定→needs_review、替代/辅助分离编码、引语回声抑制、条件子句并入引文、多子句异向→needs_review），来源识别收紧为书名号/机构名/年份紧邻（年龄+泛指南不再命中）。新增 `tests/test_protocol_v2.py` 17 例（负例 harness：严格类逐字段断言+引文子串；truncation/failure/contradicted 为信息类；自由文本字段仅验原文性）；`test_exp001.py` 的 smoke-002 期望按 neg-007 改为 needs_review；reporting 词表扩 needs_review。新增 `scripts/diff_extractions.py` 与 `derived-v3/`（v2 提取+report+逐字段差异）：27/27 条实质变化（含来源识别 6 处 True→False、六值状态与替代/辅助/对象/条件新字段）、9 条进需人工复核清单（自服否定/混合方向/强度不一致，交 #11 裁决）。derived-v2 冻结为 v1 快照，result/ 零改动。正式语义验收待 #11 人工定标（负例集全部 pending_owner_confirmation，主人批改 negatives-review.md 后回流）。


## Issue #12 双谱系评审收尾（2026-09-10）

三轮收敛：R1 codex 1P0+5P1+2P2（不可合并）、DeepSeek 1P1+3P2+2P3（需修改后合并）→ 全部闭环（derived-v2 冻结守卫、元描述片段剥离、条件邻接绑定、裸机构名剔除、告知句与"需"字推荐修复、冒号条件切分、引语回声闭合可选、冲突态双引文、diff 全字段+实质/新增分计+单元格清洗）；R2 复核 DeepSeek 判可合并（11/11 关闭）、codex 新提 4 项（冲突引文丢失 P1 等）亦已闭环（含元描述连宾语剥离与回声片段分层处理）。四闸 78/78 + check_calibration 全绿；negatives 严格 16/16、neg-016 分歧钉死为信息类。正式语义验收仍待 #11。

## Issue #12 定标回流微调（2026-09-10，主人批改后）

PR #19 落地主人裁决（17/17 confirmed，neg-007 改判 conditional_support）后，#12 分支按裁决实现自服否定分界：条件含「评估/核对」类程序表述（隐含走完程序即可用）→ conditional_support；「沟通后决定」类开放表述或无条件 → needs_review（attitude_target 标注"结果开放，交人工裁决"）。test_exp001 的 smoke-002 期望与负例 harness 随裁决更新；check_calibration --require-confirmed 全绿。derived-v3 重生成：needs_review 队列 9 条 = 5 开放性自服否定 + 3 方向相反 + 1 强度不一致，均有真实语义依据。

## Issue #20 复核材料包交付（2026-09-11，分支 review/issue-20-materials）

AI 侧交付物落地：`specs/review/`（README/background/case-card/form-open 27 条/form-candidates 候选池 20 条 DRAFT/boundaries/record）+ `attachments/`（9 组文件 + index，`scripts/gen_review_attachments.py` 从 trials.jsonl 幂等生成，正文逐字不裁剪、截断单列标注）+ `scripts/check_review_pack.py`（trial 全集/原文逐字/判定后置禁词/引文逐字定位/case-card 归属/密钥扫描等结构检查）+ `tests/test_review_pack.py`（70 例回归，含守卫绕过、路径穿越、附件删节/交换、引文篡改等破坏场景）。四闸全绿。/simplify 四角度 + pr-ready 三审计（sibling/并发/边界）全部执行并处置。双谱系评审：codex R1 3P0+6P1 → 修复 → R2 P1×2+P2×4 → 全部修复（P1 含删小节假绿、附件交换假绿，均附回归）；opencode R1 无 P0/P1（P2×5 采纳修复 4 项）；谱系 B 的 R2 因本机内存不足（opencode/qwen 连续 4 次 OOM）未完成，用户确认接受现状，风险与缓解记录于 PR。剩余人工环节：主人从候选池挑 8–12 定稿必核子集（依赖 #12 修复后刷新定位）、复核范围圈定、#5 联系复核人。issue #20 保持 open。

## Issue #13 实现完成（2026-09-11，分支 feat/issue-13-runner-protection）

运行记录保护落地：新增 `src/medmirror/runner.py`（独立 run 目录 runs/exp003-baseline/<时间戳-指纹>/、plan.json 完整计划+脱敏配置快照+配置指纹、attempts.jsonl 追加式两行制、trials.jsonl 物化视图兼容 #10 报告 CLI、恢复跳过=同指纹+success+有正文、换配置拒绝同目录、pending_reconciliation 态、max_attempts 跨恢复累计）与 `src/medmirror/budget.py`（reserve→settle/refund 三段账本、预算不足拒绝、价格未知拒绝、超支入账不拒）。`scripts/run_exp003_baseline.py` 重写为薄 CLI（--plan-only 离线生成计划、--allow-paid 付费闸门、--run-dir/--resume、--budget、--max-attempts；拒绝写入历史原件目录）。新增 `tests/test_runner.py` 17 例（假网络全场景：全新跑/同配置恢复/换配置拒绝/减 repeats 保留历史/失败重试上限/崩溃 pending/预算拒绝与超额/截断三态区分/报告 CLI 兼容）。四闸 118/118 全绿。顺手修复：check_review_pack.py 的 Windows 路径分隔符 bug（CI Linux 绿、本地 Windows 红）与三个脚本的 sibling import 漂移（run_exp003_baseline → medmirror.runner）。

## Issue #3 实现完成（2026-09-12，分支 feat/issue-3-budget-gate）

预算硬闸门补齐 + 账单核对工具：新增 `scripts/reconcile_budget.py`（读 run 目录 budget.jsonl 逐笔 settle 复算期望成本并输出差异报告；或对历史 trials 按登记价格复算——实测 0.372007 元与已登记估算精确一致）；`specs/calibration/bill-check.md`（主人核对三家实际账单的模板，含核对口径、差额归因栏、关闭勾选项）；`tests/test_budget_gate.py` 7 例（并发预留不透支、部分结算后额度复用、崩溃恢复保留已结算+在途预留、截断尾行容忍、重复加载幂等、init 事件锁定总额）。四闸 + check_calibration = 125/125 全绿。工程硬闸核心在 #13 已交付（reserve→settle/refund/pending_charge 四段、价格未知零调用、超时不释放预留、预算锁定 init），本件补齐 #3 专属三个缺口。issue #3 的关闭条件 = 主人填 bill-check.md + 本工程验收 → 人工关闭。

## Issue #24 Word 分发格式交付（2026-09-12，分支 review/issue-24-docx-export）

AI 侧交付物落地：`scripts/export_review_pack.py`（pandoc 封装，两批导出 docx；判定后置在导出层机械落地：open 批不含候选内容有测试锁定、candidates 批受定稿闸门约束且结构校验不可绕过；材料快照单点真相防 TOCTOU；manifest sha256 目录所有权防误删用户文件；文件级原子提交 + flock；导出前强制 check_review_pack 通过 + 附件重生成字节比对）+ 22 个回归测试 + checker 泄漏检查扩展 + README 分发流程。四闸 140/140 全绿。双谱系评审：codex 十五轮（每轮发现全部闭环，含多个真实 bug：默认命令被自家守卫堵死、同层重导自删、manifest 绕过链）终验可合并；MiniMax-M3 独立终验可合并。B 谱系 harness 由 DeepSeek 换 MiniMax（用户指定，deepseek 屡被 OOM）；provider 实际为 minimax-cn-coding-plan（minimax-cn key 无效）。剩余人工环节：主人在 form-candidates.md 挑选记录区勾选 8–12 条并置 FINAL → 导出第二批；第一批材料随时可导出发送（等 #5 复核人）。issue #24 保持 open 至合并。

## Issue #20 候选池 v2 刷新（2026-09-12，分支 review/issue-20-candidates-v2）

候选池分布备注升级为逐断言复核版：20 条备注对照 27 条原文 + derived-v3（offline-rules-v2，语义未定标仅参考）刷新，含精确三家计数、needs_review 交叉标注（横幅声明选择性标注规则，全量 9 条三类）、离群口径补充；候选主张/逐字引文/复核栏/机器闸门格式零改动。process：/simplify 4 角度（修 README 状态词指针化）+ pr-ready 三审计——boundary 抓出第一轮 13 处计数/归因错误（含 cand-08 引文归属违反逐字声明），全部经 trials.jsonl 逐断言机器复算修正（6-12 口径实测 21/24）；sibling 修四处状态漂移（README:13、standard-finding、annotation-worksheet「#12 待修」假陈述、record.md 版本表）。四闸 147 + check_review_pack + check_calibration 全绿。AI 推荐必核子集 10 条在 _tmp/issue-20/recommended-subset.md（仅供参考）。剩余人工环节不变：主人挑 8–12 条置 FINAL → 导出第二批；圈定复核范围；#5 联系复核人。issue #20 保持 open 至定稿。

## Issue #2 有界追问执行完成（2026-09-12，分支 feat/issue-2-bounded-followup）

AI 侧交付：`src/medmirror/followup.py`（触发规则 followup-rules-v1 + 限额 + 预算 + 恢复语义同 #13）+ CLI + 评审后增至 22 例假网络测试（四闸 169/169）。真实执行：3 候选（三家各 1、tcm 路径、父试次 tcm_mirror-1）→ 4 次真实调用（预算 1 元、花费 0.0690 元；glm 额度内重试一次后耗尽，无预算拒绝）。观察：deepseek 完整答（presented=complete，3836 字、AHA/ASA 2011 等来源）、step 截断答（presented=truncated，726 字、中国指南引用）、glm 两次均思考耗尽零正文（presented=failed）。产物：docs/experiments/exp003-baseline/followup/{followups.jsonl, findings.jsonl}。决策（主人拍板）：#11 27 条人工标注未完成，放宽前置的理由=触发规则仅用二值提及判断（负例已 confirmed 覆盖），标注赛后补。首次实跑因 spec 缺 endpoint 中止于请求发出前（零费用），账本已 refund 关闭。issue #2 关闭条件：本 PR 合并 + 主人过目追问产物。

## Issue #29 自述来源文献存在性查证（2026-09-12，分支 research/issue-29-source-verification）

AI 侧交付：`docs/experiments/exp003-baseline/followup/source-verification.md`——3 条追问回答自述来源 18 条目逐项存在性查证（deepseek 14、step 4、glm 零正文如实记录），三态判定 8 可定位/6 部分相符/4 无法定位；每条附模型自述原文（机器校验逐字命中 findings.jsonl）、查证证据（PMID/DOI/URL）、检索渠道与日期。渠道：PubMed E-utilities（英文 11 项）+ Web 检索（中文指南与文献；查无项两轮独立检索交叉）；零被测模型 API 调用。典型发现：deepseek「2021 ESVS」实为 2023 指南（issue 已知线索系统确认）、丹参条目为两篇真实文献著录杂交、step 两条中国指南按「题名+年份+机构」查无。四闸在干净 worktree 全绿（169 passed；本地 ruff format 红仅 issue-4 在途未跟踪文件，与本件无关）。边界：存在 ≠ 支持，不输出 Bias 结论，内容判断归 #5。PR #31 已合并；主人 2026-09-13 过目措辞通过，issue #29 已关闭（先回复后关闭）。

## Issue #20 候选池定稿（2026-09-13，分支 review/issue-20-candidates-final）

主人定稿必核子集 10 条（cand-01/02/03/05/07/10/11/12/14/15，采纳 AI 推荐子集；筛选框架：安全性直接相关、高分歧、具体可答；覆盖用药决策、手术指征、监测安排、中西药联用安全）。form-candidates.md 挑选记录区置 FINAL、头部横幅去 DRAFT；export_review_pack.py --layer candidates 闸门校验通过并导出第二批 docx（export/，不入库）。两批判分材料齐备：第一批（开放式）随时可发，第二批（候选核对）待第一层意见交回后发。剩余人工环节：#5 联系复核人并发送第一批。issue #20 待本 PR 合并后关闭。

## Issue #4 备份与恢复落地（2026-09-13，分支 feat/issue-4-backup-restore）

主人拍板（E 方案）：runs/ 运行档案入 Git——从 .gitignore 移除，远程仓库即备份落点，伙伴 clone 取回（验收②⑤）；CLAUDE.md 规约句同步改写。在途工作收编：scripts/backup_data.py（备份+manifest sha256+凭据排除+--drill 恢复演练，转为本地双保险角色）+ tests/test_backup.py（修复两处测试缺陷：monkey 含 key 子串改教学断言、同秒碰撞 mock 时钟断言拒绝覆盖）+ backup-restore-log.md（含 2026-09-12 一次通过的真实演练记录：32 文件、哈希无差异、离线重放一致）+ runs/ 两个 run 目录（#2 追问的 plan/账本/attempt 档案，入库前密钥扫描通过——命中均为 usage 字段名）。验收①③④已在 #4 前置工作与演练记录中达成。剩余：PR 合并后回复并关闭 issue #4。

## Issue #34 评审入口与三任务答卷（2026-09-13，分支 feat/issue-34-judge-entry）

AI 侧交付：`docs/reviews/judge-entry.md`——评委导航入口（证据地图 6 处 + 任务一/二/三「完成标准→证据→定位命令」+ 候选池 20 条五类归档（证据标准不一致 13/合理差异 4/过度推荐 1/事实错误候选 2/系统性遗漏由呈现层观察承担）+ 假设→证据→未解决问题表 H1–H4 + 附 A 成本/附 B 可复现/附 C 未完成清单）。全部定位命令实跑验证（13+ 条，含离线重放字节一致）。drafts.md 数字校对（161→175 ×2、0.063→0.0690、追问 3 条回答/4 次调用口径）。测试数以实测 175 为准（issue 写 169 是 #4 合并前口径）。同源漂移修复：根 README 测试数与开放队列、onboarding 时效声明与 runs/ 入库状态、record.md 必核 10 行落位。/simplify 修 12 跳 4；pr-ready 三审计（sibling P1×3+P2×2、boundary 9/9 口径 ×3 显式化）。双谱系评审：codex R1「修改后合并」P1×5 修 4 跳 1 + P2×2/P3×1 修；MiniMax R1「可合并」P2×2 修——两谱系数字独立实测全部一致。冻结产物 sha256 前后校验零改动。**事故记录**：~02:05 _tmp/issue-34/ 目录被整体删除（handoff/watchdog/评审输出丢失，凶手未定、嫌疑最大为 MiniMax 评审会话，codex 只读沙盒与 pytest fixture 已排除），已全部重建（评审输出改存 .claude/notes/issue-34/、看门狗 v2 重启），MiniMax 硬防护重跑通过。剩余人工环节：主人过目答卷措辞与边界声明；PR 合并后回复并关闭 issue #34。
