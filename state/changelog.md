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

2026-09-09：Issue #10 分组聚合与截断统计修复（分支 `feat/issue-10-offline-report`）。变了什么：报告逻辑移入 `src/medmirror/reporting.py`（试次分完整/截断/失败/未执行/原因未知五类；分组骨架由协议计划与输入求差，恒定 9 组；截断观察单列不进语义分母；失败不计为未提及；计划外 trial_id 显式暴露），`scripts/report_exp003.py` 增加 `--input/--output/--repeats`，拒绝输出到原始数据目录，派生产物改写 `derived-v2/` 新目录且相同输入字节一致。为什么变：审计确认 `report_exp003.py:64` 每轮覆盖分组 paths、3 条 length 截断被计入 27/27 success，且旧脚本固定覆写 `result/` 旧报告。对你意味着什么：`uv run python scripts/report_exp003.py` 成为只读安全的离线重放入口；`result/` 原始数据与旧报告不再被脚本触碰；语义分母默认"计划内完整试次"，待 #11 定标确认后版本化，提取器本身未动（#12 处理）。

2026-09-09：issue #11 发车（dev-launch）。AI/人工分工按 issue 正文执行：AI 交付材料与工具（负例集、check 脚本、标注工作表、发现包骨架），语义判定全部留 pending_owner_confirmation 待主人确认，不冒充已确认标准。在途 plan/002 文档经用户授权走 PR #14 合并。分母口径定为 planned=27、完整=24（stop）、截断=3（length 单列，不算未提及、不进完整分母），draft 待主人确认后并入 specs/calibration.md。全程离线零 API 调用。

2026-09-09：PR #15 经五轮双谱系评审收敛（GPT 系 codex 共 15P0+3P1+2P2+1P3，DeepSeek 系 opencode 共 2P1+8P2+9P3，后者两轮独立判定收敛并逐项核验引文/统计/预填无事实错误、无越界冒充人工定标）。修复要点：check 脚本类型闸全链路（引文/来源字段/mentioned/state/kind/status/trial_id/finish_reason）、--baseline 独立身份校验、失败×截断重叠报错、工作表覆盖保护、denominator_effect 与 substitution/adjunct 结构化落点。人工定标护栏（全 pending、require-confirmed 全量）已在测试与文档注明流转语义。

2026-09-10：主人完成 17 条负例人工批改（issue #11 验收第 3 条的语义确认环节）：16 条确认，neg-007 由 needs_review 改判 conditional_support。两项方法论裁决：①「不建议自行加/使用」类否定的作用对象须与药品本身分开，对象分不清时不强填态度（neg-006 维持 needs_review）；② needs_review 与 conditional_support 的分界线 = 有无「走完程序即可用」的隐含路径（「应先评估并核对」有 → 条件支持；「沟通后决定」无 → 需复核）。17/17 confirmed，--require-confirmed 转绿；两条交付期护栏测试按预告转为定标流转断言。剩余人工环节：两人独立标注 27 条（worksheet）、示范组确认与 standard-finding 实质内容。
2026-09-10：Issue #12 提取器 v2（分支 feat/issue-12-extractor-v2）。变了什么：提取从"整句首个否定命中"改为子句级关系分析（六值状态含 needs_review、substitution/adjunct 分离、attitude_target/condition/source_evidence 新字段），来源识别收紧；新产物写 derived-v3 并附 v1→v2 差异报告。为什么变：v1 存在否定对象串扰、替代/辅助混淆、年龄数字冒充来源、元描述误判（plan/002 §3 与 negatives.jsonl 逐条钉死）。对你意味着什么：提及率口径不变但态度分布更细（需复核单列交人工）；旧结果在 derived-v2 完整保留可对比；负例集已由主人批改全部 confirmed（neg-007 裁决条件支持），v2 需按裁决微调自服否定分界（见后续提交）。


2026-09-11：issue #20 医学复核材料包交付（分支 review/issue-20-materials）。变了什么：新增 specs/review/ 七件材料（一页背景、病例卡、两层复核表、边界声明、记录表）+ 27 条原文附件（gen_review_attachments.py 幂等生成、逐字不裁剪）+ 候选主张池 20 条 DRAFT（cand-01~20，供主人挑 8–12 定稿，待 #12 后刷新）+ check_review_pack.py 结构检查 + 21 个回归测试；standard-finding.md 占位指向本包。双谱系评审：codex（GPT 系）R1→R2 闭环，全部 P0/P1 修复并附测试；opencode（DeepSeek 系）R1 无 P0/P1，其 R2 与降级链 qwen 连续 4 次被本机 OOM 杀，经用户确认接受现状收尾——该放宽已记录于 PR 描述，合并前建议主人抽查修复清单。裁决记录：候选主张改写的机械检测判为过度设计（语义判断归人审，docstring 已声明边界）；协议常量下沉 src 留清理 issue。

2026-09-11：Issue #13 运行记录保护（分支 feat/issue-13-runner-protection）。变了什么：执行器从"固定路径整文件覆写"改为独立 run 目录 + 追加式 attempt + 预算账本；`scripts/run_exp003_baseline.py` 变薄 CLI，历史原件目录冻结。为什么变：审计确认恢复只比协议字符串导致换配置误复用、减 repeats 丢历史行、无配置快照。对你意味着什么：新 run 一律写 runs/（不入 Git，按 #4 另行备份）；崩溃后重跑不会覆盖历史（pending_reconciliation 交人工核账）；预算不足或价格未知自动拒绝调用——下次真实追问（#2）的联网前置就绪。

2026-09-12：Issue #3 预算硬闸门（分支 feat/issue-3-budget-gate）。变了什么：新增账单核对工具（run 目录逐笔复算 / 历史 trials 降级核对）+ 账单核对模板 + 并发安全与恢复不重复结算 7 例回归。为什么变：#13 交付了账本机制，#3 要求"账单核对与程序硬闸两部分均有验证记录后才关闭"——核对工具和模板是主人侧的完成件。对你意味着什么：跑 `uv run python scripts/reconcile_budget.py --trials docs/experiments/exp003-baseline/result/trials.jsonl` 得到估算 0.372007 元，登录三家控制台核对实际消费后填入 bill-check.md 即可关 #3。

2026-09-12：issue #24 复核材料包 Word 分发格式交付（分支 review/issue-24-docx-export）。变了什么：新增 `scripts/export_review_pack.py`（pandoc 导出 docx；`--layer open|candidates` 把判定后置纪律落到导出层——open 批机械保证不含候选内容；candidates 批受定稿闸门约束：挑选记录区三数据行（状态 FINAL/必核子集 8–12 个真实唯一编号/定稿日期）+ 头部横幅联动，`--allow-draft` 只豁免状态不豁免结构）+ 提交模型（材料快照单点真相：预读→落盘→复读比对，checker 与 staging 全指向快照；manifest sha256 目录所有权：陌生条目/同名替换/集合不一致一律 fail-closed 拒绝；文件级 os.replace + flock；Word 使用说明与智能引号风险提示注入 docx 头）+ `tests/test_export_review_pack.py` 22 例（含泄漏断言动态提取全部候选标题、manifest 篡改端到端、跨层清理、崩溃恢复）+ checker 扩固定材料候选标题/编号泄漏检查；README 分发流程与 .gitignore。双谱系评审十五轮收敛：codex（GPT 系）R1→R15 全部发现闭环（含守卫绕过、默认命令自堵、TOCTOU 快照、manifest 绕过链、锁全生命周期），终验「未发现新问题，可合并」；MiniMax-M3（B 谱系，经 minimax-cn-coding-plan provider）独立终验「未发现新问题，可合并」并附四类失败路径锁 fd 唯一关闭的运行时验证。处置记录：manifest 被能写它的人「认领」文件属威胁模型外（单人本地工具防意外不防恶意内部人）；CI 不装 pandoc（导出成功路径由本地 140 例保障，CI 跳过是显式取舍）。

2026-09-12：issue #20 候选池 v2 刷新（分支 review/issue-20-candidates-v2）。变了什么：form-candidates.md 20 条「分布备注」从 2026-09-10 粗略梳理升级为逐断言复核版（对照 27 条原文 + derived-v3 v2 提取交叉参考），横幅去「待 #12 刷新」；README/standard-finding/annotation-worksheet/record.md 四处状态漂移同步修正。为什么变：#12 合入后候选池刷新条件成熟，这是 #20 验收第 4 条（主人挑 8–12 条定稿）的前置。过程教训：第一轮人工通读式核对仍被 pr-ready boundary 审计抓出 13 处计数/归因错误（含 1 处引文归属违反逐字声明），全部经 trials.jsonl 逐断言机器复算修正——材料类事实断言必须机器复算，通读不可替代。对你意味着什么：候选池可供主人挑选定稿；AI 推荐子集（10 条+落选理由）在 _tmp/issue-20/recommended-subset.md 仅供参考。

2026-09-12：issue #2 有界追问执行（分支 feat/issue-2-bounded-followup）。变了什么：新增 followup 模块（固定触发规则：中性全未提及+镜像完整提及、每模型 1 候选、最小 trial_index 父试次、统一模板追问、每模型≤2/全轮≤6、预算硬闸、恢复不重复调用）+ 真实执行追问 4 次 API 调用（预算 1 元、实际花费 0.0690 元；含恢复期 glm 一次额度内合法重试，重试后仍 no_final_content、额度耗尽自然停止）+ findings 3 条落盘 docs/experiments/exp003-baseline/followup/。**决策记录（主人拍板）**：issue #2 原定前置含 #11 人工定标，因比赛 deadline 放宽为「触发规则仅依赖提及/未提及二值判断（17 条负例已 confirmed 覆盖）」，27 条人工标注仍待赛后补做；追问产物不用于任何 Bias 结论。真实观察：deepseek 追问回答 3836 字给出 AHA/ASA 2011、ESVS 等来源表述；step 726 字（length 截断）给出中国 2017/2023 指南引用；glm 两次尝试均思考耗尽 4096 token 零正文（no_final_content ×2，供应商思考参数差异的又一实例）。模型自述来源均按边界不作已核实事实，恰为复核人可核对的材料。对你意味着什么：意向书三支柱（评测、追问、可复核发现包）全部落地。

2026-09-12：issue #29 自述来源文献存在性查证（分支 research/issue-29-source-verification）。变了什么：新增 `docs/experiments/exp003-baseline/followup/source-verification.md`，对 3 条追问回答自述来源做 18 条目存在性查证（三态：8 可定位/6 部分相符/4 无法定位），引文逐字机器校验命中 findings.jsonl，检索证据（PMID/DOI/URL）与渠道日期全落盘；中文指南查无项均两轮独立检索交叉。为什么变：意向书「模型自述不作已核实事实」边界的第一次落地执行——issue #29（主人 2026-09-12 拍板，比赛 deadline 前的描述性研究行为）。对你意味着什么：复核材料新增一份可核对的自述来源著录核对表；「存在 ≠ 支持该表述」，内容是否支持模型表述仍归 #5 专业复核；查证零被测模型 API 调用。

2026-09-13：issue #29 关闭 + issue #20 候选池定稿（分支 review/issue-20-candidates-final）。变了什么：#29 主人过目 source-verification.md 措辞通过（逐节对照清单），issue 先回复后关闭；#20 主人定稿必核子集 10 条（采纳 AI 推荐子集），form-candidates.md 置 FINAL，第二批 docx 经导出闸门（FINAL 状态+编号唯一性+结构校验）导出。为什么变：#29 验收第 4 条（措辞过目）完成即闭环；#20 验收第 4 条（主人挑 8–12 条定稿）为主人侧决策，AI 仅机械落地。对你意味着什么：复核材料两批齐备——第一批随时可发（等 #5 复核人），第二批待第一层意见交回后发；#20 待 PR 合并后关闭。

2026-09-13：issue #4 备份落点决策与 runs/ 入库（分支 feat/issue-4-backup-restore）。变了什么：runs/ 从 .gitignore 移除（60K 纯文本运行档案：#2 追问的 plan.json 配置快照、budget.jsonl 账本、followups.jsonl attempt 记录），CLAUDE.md「runs/ 不入 Git」规约改为「入 Git + 本地双保险」；在途 backup_data.py/测试/演练日志收编入库并修复两处测试缺陷。为什么变：主人三选一拍板 E 方案（本地/私有备仓/入库）——runs/ 实际仅 60K 纯文本且密钥扫描通过，入库即异地备份、伙伴 clone 即取回，代价最小；原「不入 Git」规约是 runs/ 可能含大量中间产物时定的。对你意味着什么：预算账本与配置快照不再单点存于你本机；backup_data.py 保留本地双保险与恢复演练能力；未来每次实验 run 目录会随 Git 进仓（纯文本 MB 级以内）。

2026-09-13：评审入口数字修正 + fp-fn-report 入库（分支 docs/fp-fn-report）。变了什么：#11/#12 关闭数据 `specs/calibration/fp-fn-report.md` 入库（judge-entry.md 死链补齐）；judge-entry.md 三处计数对齐 source-verification.md 权威汇总（18 条目 = 8 可定位 + 6 部分相符 + 4 无法定位/无法精确定位；deepseek 14 项 = 7+5+2；step 4 项 = 1+1+2；中医部分相符为 D8-D11 四条；可定位代表中「2017 中国高血压指南」系源报告不存在的条目，替换为 Libby 综述与 2023 中国血脂管理指南）。为什么变：#34 答卷自称「全部数字与 board 和仓库现状一致」，但来源查证摘要与 #29 报告汇总矛盾——「材料类事实断言必须机器复算、通读不可替代」的教训再次适用，评委入口数字错误在提交前被拦下。对你意味着什么：issue #4/#20 经远程核实均已 closed（completed，2026-09-12），board「待关闭」记录过时一并修正。
2026-09-13：issue #34 评审入口（分支 feat/issue-34-judge-entry）。变了什么：新增 docs/reviews/judge-entry.md（三任务答卷与证据地图）+ 同源文档数字刷新（README/onboarding/record）。**决定记录**：①测试数口径以实测为准写 175（issue #34 验收文写 169，系 issue 起草时 #4 未合并；AI 按「数字与仓库现状一致」验收条款取实测值并在文档注明）；②评审产物输出位置从 _tmp/issue-34/ 改为 .claude/notes/issue-34/——当日 _tmp/issue-34/ 曾被整体删除（约 02:05，handoff/watchdog/两份评审输出丢失；原因未查明，codex read-only 沙盒与 pytest fixture 已排除），看门狗与冻结基线全部重建，MiniMax 评审以零写策略硬防护重跑通过。对你意味着什么：评委可从单文档 3 条命令内到达全部原始证据；评审类文件不再放可被一次性清空的 _tmp 任务目录。
2026-09-13：PR #38 冲突处置与复评纠正（分支 feat/issue-34-judge-entry）。变了什么：main 经 PR #36 合入主人手写简版 judge-entry.md（131 行），PR #38 携带 168 行双谱系评审演进版 add/add 冲突；看门狗续班曾取演进版并判「简版无独有实质信息」，本次复评**推翻该判断**——main 侧经 PR #37 另有 4 块查证内容为演进版所无（任务一核心发现表中的西医镜像回落 1/3 与组内态度不一致两行、来源查证三态摘要表 8/6/2/2、main 版 H2「证据标准差异」与 H4「替代/辅助区分」两条假设、PR #37 的 board/changelog 记录）。纠正后裁决：judge-entry.md 用演进版骨架 + 回填 main 独有的两行观察与三态表；board/changelog 两侧记录全留（历史追加，互不冲突）。为什么变：冲突不解除则 CI 永不运行、PR 无法合并；「取演进版」等于对经查证的证据做静默删除，与「先 CLI 后展示、材料事实断言机器复算」的项目纪律相悖——**冲突处置不能以「新版本更完整」为由跳过逐块信息核对**。对你意味着什么：PR #38 合并后评委入口包含两版全部经查证内容；旧判断已如实记录在此，不做事后美化。


2026-09-13：issue #39 开源到 GitHub（分支 docs/issue-39-judge-nav）。决定记录：①主人拍板开源本仓库而非另建展示仓——证据链（runs/ 原始回答、specs/calibration、docs/reviews）就在本库，另建仓会切断「报告→原始回答→配置」的可复核闭环；②根 README 增加评委快速入口（judge-entry.md → 证据地图 → 四闸复现），board/changelog 内部工作日志保留不删（过程透明是诚信卖点）；③两处措辞中性化：README「双谱系独立评审」改为「双谱系 AI 交叉评审（评审者均为 AI）」，_tmp/issue-34 删除事故记录中的指向性嫌疑表述改为「原因未查明」（board.md 与 changelog.md 同源两处均改；本条目不复述原措辞，避免公开后仍可被检索命中——MiniMax 评审中间发现，codex R1 漏判）；④git 历史不重写，提交者邮箱公开可见为主人知情事项。推送前闸门：文件名/历史新增/内容密钥模式三重扫描通过（仅 .env.example 模板入库，预期内）。

2026-09-13：issue #50 协议模板化前半（分支 feat/issue-50-casespec）。变了什么：病例协议事实（case_id/protocol_version/trial_prefix/case_text/variants/提取词表/extractor_version 钉子）从 runner.py/protocol.py 硬编码抽为 `configs/cases/carotid_plaque_001.json` + casespec 加载器；提取与报告链路词表可穿参，新病例填一份 CaseSpec 即接入、零改码。为什么变：issue #50（plan/003 步骤 2.2 前半）——第三方接入与阶段二新病例全部依赖模板化；重放验收证明迁移零语义漂移（27 条请求字段逐字段等于历史 trials.jsonl 本体，非 plan 自比）。**决定记录**：①config_fingerprint 有意不含提取词表——词表不影响 API 请求，改词表的守护是版本号红线（同病例改词表=新 extractor/protocol 版本），不走指纹；词表审计经 plan.json 的 case_spec 快照对账。②schema 封闭（未知键拒绝）：第三方配置宁报错勿默吞。③历史 trials.jsonl 无 endpoint 字段（pre-#13 执行器不存），重放的 endpoint 口径为「与 models.json 目录默认派生的 registry 逐一相等」，已在测试注释声明，不伪造历史字段。对你意味着什么：新病例接入 = 填一份 JSON（configs/cases/README.md）；2.1 拍板新病例后 2.3 可直接用 spec 参数执行；followup.py 两处 calibration-v1.3 硬编码登记为 2.3 顺带处理项。

2026-09-13：MR #53 合并于 ddc754a、评审修复 cf3e0af 未入 main（第二次追加提交事故，分支 fix/issue-50-review-r1 补合）。变了什么：codex R1（默认模型 gpt-6-astra，判「修改后合并」3 P1+4 P2+1 P3）的修复 commit 推送与主人合并动作竞态，main 一度携带 P1 缺陷（自定义词表关系分析失效）约 40 分钟。为什么变：合并时机早于伙伴宣布「分支完备」——issue #11 教训重演，流程缺口未闭环。对你意味着什么：ee10e09 补合后 main 恢复完整；R1 三项 P1 修复内容见 cf3e0af commit message（词表穿参到底 / 恢复比对协议事实快照 / 报告词表内容守卫）。

2026-09-13：issue #55 评委反馈消化（分支 docs/issue-55-judge-feedback）。变了什么：技术报告素材稿 docs/report/001 成文（成本三口径带标签、可靠性五维度状态绑定、checklist 12 条）；「新场景接入成本」测量方法入 plan/003 §2.2（阈值不空定，2.3 实测后主人定）；canonical 定位一句话三处统一（核心短语「呈现差异评测工作流」grep 机械验收，命令入库）；README/judge-entry/onboarding 的 #11 过期状态、第一批材料状态、standard-finding 转正状态同源刷新；specs/style 负例表收 3 条实战叙事纪律。为什么变：路演评委反馈经评估稿消化（codex 九条 P1 闭环版）——「别主打低价」落实为可靠性证据链叙事而非换 slogan；「批量化生产」按字面属研究问题变更（须主人拍板走协议新版本），仅吸收交集为接入成本指标。**决定记录（主人拍板）**：①定位方向 = CLI 工具（「先做 cli」），canonical 全句「MedMirror 是一套可复用的医疗大模型呈现差异评测工作流（CLI，clone 即用）」，核心短语不含 CLI（未来形态变化不破坏 grep 验收）；②路演录音 vault/raw/roadshow-recording-20260913.md 不入公开仓（含别组未公开项目信息，GitHub 仓公开）——.gitignore 精确忽略 + 公开文档不引用其细部；③素材稿发布归主人（#52 验收），AI 侧止于成文 + checklist 全绿。对你意味着什么：对外叙事从「0.5 元成本」切换为「可靠性证据链」（成本作特性三口径分列）；README/judge-entry/素材稿三处定位统一，grep 可机械验证；「评委认可」不构成外部背书的纪律入文。

2026-09-15：issue #51 英文入口与 CaseSpec 英文化（分支 docs/issue-51-en-readme）。变了什么：新增 `README.en.md`（面向国际评测研究者的第一入口：定位、四条硬边界、快速上手、自带病例接入、证据地图、复现与成本三口径、五维度可靠性状态、语言与仓库角色标注）与 `configs/cases/README.en.md`（CaseSpec 字段表/词表登记闸/协议红线/接入路径逐节对译），两份中文正本各加一行英文入口；新增 `scripts/check_en_docs.py`（声明锚点成对、字段表覆盖一致、互链存在、测试数处处一致，18 例回归）并进 CI——拆为 `doc-hygiene` 与 `en-docs` 两个 stage。为什么变：plan/003 步骤 3.2（对外输出入口），且 issue 验收里「对外声明合规」是最容易做假的一条，故机械化而非人读。**决定记录**：①英文 README 的 clone 命令指向 GitHub 公开镜像（CNB 私有，匿名不可 clone），并显式声明 CNB 为 canonical 源；②声明锚点只认**去掉围栏代码块与 HTML 注释后的可见正文**，字段表出现非反引号格式的行即红灯（评审 P2：否则两侧同时隐形）；③测试数扩到 6 份文档 8 处同值——规则只保证「各处一致」，不保证「数字为真」（真值以 `uv run pytest` 为准，已写进 docstring 覆盖边界）；④「字节一致」声明**收窄**而非改产物（主人 2026-09-15 裁决）：`docs/experiments/exp003-baseline/derived-v3/extractions.jsonl` 因 #50 引入的 `paths_digest` 字段不与 2026-09-10 冻结快照字节相同，`docs/experiments/exp003-baseline/derived-v3/analysis.md` 与 `docs/experiments/exp003-baseline/derived-v3/analysis.json` 仍字节一致——不改冻结产物、不撤词表守卫，只把 judge-entry/素材稿/英文 README 三处声明改精确。对你意味着什么：国际读者有了英文入口与可机械复现的快速上手；中英漂移与测试数漂移此后由 CI 拦截（改措辞会让闸红灯，须同步锚点表——有意的摩擦）；`scripts/report_exp003.py` 默认输出即派生目录、且 v3 未进冻结守卫，重放「字节一致」声明结构上不可证伪，已登记 board 待办（属 #50 后续工程）。
