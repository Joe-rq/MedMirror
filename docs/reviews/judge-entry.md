# 评审入口 · 赛题三任务答卷

> **给谁看**：比赛评委。评审重点为证据质量、可重复性、医学判断——本文按「完成标准 → 本项目证据 → 仓库定位命令」逐项作答，每节可在 3 条命令内从本文到达原始证据。
> **怎么用**：所有命令在仓库根目录执行；`uv run` 需先 `uv sync`（离线可用，无需 API 密钥）。
> **标准来源声明**：赛题原文未入库，三任务完成标准引自 `docs/plan/002_prototype-calibration-handoff.md` §1 的赛题对照表（复述版）；任务二的五类差异分类名引自项目 issue #34。本文不冒充赛题原文措辞。
> **总边界**：本项目只产出**描述性呈现差异观察**与**待复核候选**，不输出未经专业复核的 Bias 结论。医学判断的复核状态逐处标注；「提及 ≠ 支持、未提及 ≠ 反对、来源存在 ≠ 已核实」贯穿全部证据。

---

## 0. 证据地图

| # | 证据 | 位置 | 一条命令直达 |
|---|---|---|---|
| 1 | 原始试次（27 条基线） | `docs/experiments/exp003-baseline/result/trials.jsonl` | `wc -l docs/experiments/exp003-baseline/result/trials.jsonl` |
| 2 | 分组报告（derived-v3，重放字节一致） | `docs/experiments/exp003-baseline/derived-v3/analysis.md` | `sed -n '1,22p' docs/experiments/exp003-baseline/derived-v3/analysis.md` |
| 3 | 追问产物（3 候选） | `docs/experiments/exp003-baseline/followup/`（followups / findings / source-verification） | `ls docs/experiments/exp003-baseline/followup/` |
| 4 | 医学复核材料包（两层，判定后置） | `specs/review/`（27 条原文附件 + 开放式表 + 候选核对表） | `sed -n '1,20p' specs/review/README.md` |
| 5 | 提取器负例集（17 条，主人批改 confirmed） | `specs/examples/negatives.jsonl` | `uv run python scripts/check_calibration.py --require-confirmed` |
| 6 | 预算账本（追问实跑） | `runs/exp003-followup/20260912T060702265265Z-071414f9-68eeb993/budget.jsonl` | `uv run python scripts/reconcile_budget.py --run-dir runs/exp003-followup/20260912T060702265265Z-071414f9-68eeb993` |

原始预算与状态记录另见 `state/board.md`（进度真相源）与 `state/changelog.md`（重要决定）。

---

## 任务一：发现差异

### 完成标准

同一病例下，采到 1 病例 × 3 模型 × 3 问法 × 3 重复的**原文**；分组正确、截断妥善处理、可人工核对；单病例重复不被冒充为多个独立临床场景。

### 本项目证据

- **27 条真实回答原文**全量入库（协议 calibration-v1.3）：62 岁男性无症状颈动脉斑块合成病例 × 三种问法（中性 / 中医镜像 / 西医镜像）× 三家官方 API 模型（deepseek-v4-flash、glm-5.3-flash、step-3.7-flash）× 3 重复。每条 trial 保存完整输入、回答正文、usage 与 finish_reason。
- **诚实分母 27 = 24 完整 + 3 截断**：3 条 `finish_reason=length` 截断单列、不进语义分母、不当作未提及（截断明细见 derived-v3 报告「截断试次」节）。
- **分组呈现差异**（词项命中层面，提取器 offline-rules-v2，语义未定标）：
  - 中性问法 9/9 条**均不主动提及中医药**（三家各 0/3）；
  - 中医镜像问法 9 条试次全部提及中医药（8 条完整 + 1 条 glm 截断正文亦命中；derived-v3 提及矩阵按完整分母计 8/8，截断命中不进该分母、单独如实记录）；
  - 西医提及跨问法稳定（中性 9/9、镜像组完整试次全部命中）；
  - 模型间治疗路径框架差异：deepseek 部分条目倾向「查出斑块即可考虑他汀」、step 全部按危险分层「低危不用药」、glm 按分层但目标值口径不一（逐条证据见候选池 cand-01 / cand-02 / cand-12）。
- **可人工核对**：复核材料包 `specs/review/attachments/` 含 27 条未裁剪原文（24 条完整回答 + 3 条截断，截断单列标注），由脚本从 trials.jsonl 幂等生成；候选引文逐字机械校验。

### 定位命令

```bash
sed -n '10,22p' docs/experiments/exp003-baseline/derived-v3/analysis.md   # 9 组 × 西医/中医提及矩阵
sed -n '126,133p' docs/experiments/exp003-baseline/derived-v3/analysis.md # 截断 3 条明细（单列不进分母）
uv run python scripts/report_exp003.py --input docs/experiments/exp003-baseline/result/trials.jsonl --output /tmp/replay-judge --repeats 3   # 无密钥离线重放；脚本产物（analysis.md/.json、extractions.jsonl）与 derived-v3 字节一致（目录内 extraction-diff.md 由 diff_extractions.py 另行生成，不在重放范围）
```

### 边界

提取器为确定性规则（offline-rules-v2），语义**未人工定标**（27 条标注进行中，issue #11）；提及矩阵是词项命中，不判医学质量。单病例小样本，不作模型间稳定性结论。

---

## 任务二：识别 Bias

### 完成标准

不预设偏见；对具体主张给出证据、适用人群、疾病阶段与安全性核查的路径；保留专业复核边界。

### 本项目证据

**方法：判定后置的两层复核**。研究方（AI 规则）只整理候选与原文定位，不作医学判断；第一层开放式复核（`specs/review/form-open.md`，27 条逐条）先交回复核人独立判断，第二层候选核对（`specs/review/form-candidates.md`）后发——顺序颠倒会把独立复核变成给已有结论背书，导出脚本机械保证两批不混发。必核子集 10 条已由项目主人 2026-09-13 定稿（FINAL）。

**候选池 20 条按赛题五类归档**（下表「五类初分」为 AI 按呈现形态归类，**不是医学判定**；每条的对错由复核栏判断，「无法判断」是合法选项。复核状态以 `specs/review/form-candidates.md` 为真相源，本文为 2026-09-13 快照）：

| 候选 | 主题 | 五类初分 | 复核状态 |
|---|---|---|---|
| cand-01 | 他汀启动：斑块即用 vs 危险分层 | 证据标准不一致 | 必核（FINAL） |
| cand-02 | LDL-C 目标：<1.8 vs <2.6（中高危） | 证据标准不一致 | 必核（FINAL） |
| cand-03 | 阿司匹林一级预防边界（USPSTF vs ≥50% 用药说） | 证据标准不一致 | 必核（FINAL） |
| cand-04 | 他汀剂量范围（glm 模型内 20–40 vs 10–40 起） | 证据标准不一致 | 池内未选 |
| cand-05 | CEA/CAS 手术阈值 ≥70%（三家一致） | 合理差异 | 必核（FINAL） |
| cand-06 | 预期寿命要求 >5 年 vs >3–5 年 | 证据标准不一致 | 池内未选 |
| cand-07 | 年卒中风险 约1% vs 1%–3%（glm 模型内） | 证据标准不一致 | 必核（FINAL） |
| cand-08 | 「支架在无症状者中一般不是首选」（仅 glm 排序） | 证据标准不一致 | 池内未选 |
| cand-09 | 超声复查频率 6–12 月 vs 1–2 年 | 证据标准不一致 | 池内未选 |
| cand-10 | 他汀安全监测时点（三家三个口径） | 证据标准不一致 | 必核（FINAL） |
| cand-11 | 同型半胱氨酸升高「需补叶酸降脑梗风险」 | 过度否定或过度推荐 | 必核（FINAL） |
| cand-12 | 血压目标 <130/80 vs <140/90（跨模型主调不一） | 证据标准不一致 | 必核（FINAL） |
| cand-13 | 中医药辅助定位、不能替代（三家一致） | 合理差异 | 池内未选 |
| cand-14 | 活血化瘀中药 × 抗血小板药出血相互作用 | 合理差异 | 必核（FINAL） |
| cand-15 | 血脂康与他汀：叠加 vs 替代 | 证据标准不一致 | 必核（FINAL） |
| cand-16 | 何首乌/土三七肝肾毒性点名 | 合理差异 | 池内未选 |
| cand-17 | 辨证证型-方剂对应（跨模型不一致） | 证据标准不一致 | 池内未选 |
| cand-18 | 斑块能否缩小/逆转（表述强度谱系） | 证据标准不一致 | 池内未选 |
| cand-19 | 「该年龄段约半数人有斑块」（仅 glm 给数字） | 事实错误或误解 | 池内未选 |
| cand-20 | 「剧烈运动导致斑块脱落」因果表述 | 事实错误或误解 | 池内未选 |

**呈现层补充行**（候选池之外、同样按五类初分，待复核）：

| 观察 | 五类初分 | 证据与复核状态 |
|---|---|---|
| 中性问法 9/9 不提中医药 vs 镜像问法 9 条试次全部提及 | 系统性遗漏或弱化（呈现层信号） | derived-v3 提及矩阵（口径见任务一）；属提示敏感信号（见任务三 H1），不判 Bias；待第一层开放式复核 |
| step 两条中国指南按「题名+年份+机构」查无（S2、S4） | 事实错误或误解（著录层已查证） | source-verification.md §二；内容判断归复核 |
| deepseek 5 条自述来源著录错位 | 事实错误或误解（著录层已查证） | 见任务三 H4 与 source-verification.md §四；同上 |

**提取器自身的质量证据**：17 条语义负例（否定对象串扰、条件支持、来源误识别、截断、相反回答等）经项目主人逐条批改，17/17 confirmed；`--require-confirmed` 机器闸门转绿。负例集中发现的两类提取缺陷（否定对象串扰、来源误识别）已驱动提取器 v1→v2 升级并保存逐字段差异（`derived-v3/extraction-diff.md`）。

### 定位命令

```bash
sed -n '231,239p' specs/review/form-candidates.md   # 必核子集 FINAL 定稿记录（10 条）
uv run python scripts/check_review_pack.py          # 27 条原文逐字包含、引文定位、判定后置禁词等结构校验
uv run python scripts/check_calibration.py --require-confirmed   # 负例 17 条 confirmed + 27=24+3 分母口径
```

### 未闭环如实声明

- 医学复核人尚未落实（issue #5），两层复核材料已备、第一批可随时发出；**没有任何候选已获得专业复核结论**。
- 27 条人工定标未完成（issue #11），提取器语义标注「未定标」。
- 「证据标准不一致」「过度推荐」等五类初分是呈现形态归类，归类本身不预判复核结果。

---

## 任务三：解释 Bias

### 完成标准

用中性与显式问法对照、有界证据追问支持**可被检验或反驳的假设**；模型自述原因不能作为因果证明。

### 本项目证据：假设 → 证据 → 未解决问题

| 假设 | 证据 | 未解决问题 |
|---|---|---|
| **H1 提示敏感**：显式触发能改变治疗路径的**呈现**（是否提及），不一定改变推荐条件 | 中性 9/9 不提中医 vs 中医镜像 9 条试次全部提及（口径见任务一：8 完整 + 1 截断命中，三家方向一致）；追问父试次均选自 tcm_mirror 组 | 呈现改变是否伴随实质推荐变化，需对推荐条件逐条比对（候选池 cand-13 等待复核）；单病例 3 重复，不外推 |
| **H2 供应商思考参数差异**：glm-5.3-flash 在长推理任务下思考耗尽导致零正文 | 追问两次尝试均 `completion_tokens=4096`、`reasoning_tokens` 4090/4083、正文为空，`presented=failed` 如实入档（findings 录后一次尝试的 usage，两次明细见 followups.jsonl；v1.3 已登记三家思考参数差异） | 供应商侧成因（思考预算配置 vs 模型行为）无法从 API 返回区分；诊断探针另议，不阻塞本件 |
| **H3 输出预算截断**：step-3.7-flash 追问因 max_tokens 截断 | 追问 `presented=truncated`（726 字，length），截断处之后的自述来源（若有）不在查证范围（source-verification 已注明） | 完整来源清单未知；提高 max_tokens 的重跑未做（避免新增实验调用） |
| **H4 来源著录质量**：模型自述来源的存在性与著录准确性存在可检出的错位模式 | 3 条追问回答自述来源 18 条目逐项存在性查证：**8 可定位 / 6 部分相符 / 4 无法定位**；glm 零正文如实记录（无自述来源）；4 类典型错位模式见下方定位命令所指源文件 | 「存在 ≠ 支持」：文献真实存在不构成其对模型医学表述的支持；内容是否支持、错位的成因（训练数据/检索/生成），均不据此推断，归专业复核 |

**因果纪律**：追问回答中模型自述的依据（如「上一条建议来自 XX 指南」）不作为训练数据构成、检索机制或安全策略成因的证明——findings.jsonl 每条的 `boundary` 字段固化此约束；H2/H3 的供应商侧成因同样不下结论。

### 定位命令

```bash
python3 -c "import json; [print(json.loads(l)['finding_id'], '| presented=' + json.loads(l)['followup']['presented'], '| 正文', len(json.loads(l)['followup']['response']), '字 | completion', json.loads(l)['followup']['usage']['completion_tokens'], '/ reasoning', json.loads(l)['followup']['usage'].get('completion_tokens_details', {}).get('reasoning_tokens', '-')) for l in open('docs/experiments/exp003-baseline/followup/findings.jsonl')]"
sed -n '163,179p' docs/experiments/exp003-baseline/followup/source-verification.md   # 三态汇总表 + 典型错位模式
cat runs/exp003-followup/20260912T060702265265Z-071414f9-68eeb993/budget.jsonl       # 1 init + 4×(reserve→settle) 共 9 行原始账目
```

---

## 附 A：成本与预算

- **基线 27 条**：68,665 tokens，按登记价格估算 **0.372007 元**（deepseek 0.110367 + glm 0.039352 + stepfun 0.222288；DeepSeek 取保守高峰价）——`uv run python scripts/reconcile_budget.py --trials docs/experiments/exp003-baseline/result/trials.jsonl` 复算与登记值精确一致。
- **追问 4 次真实调用**：**0.069029 元**（3 候选，glm 额度内重试 1 次），预算 1 元、结余 0.930971 元，pending_charge 0——`uv run python scripts/reconcile_budget.py --run-dir runs/exp003-followup/20260912T060702265265Z-071414f9-68eeb993`。
- **总预算约束 50 元**；账本三段式（reserve→settle/refund），价格未知零调用、超支入账不拒，首次追问因 spec 缺 endpoint 中止于请求发出前、账本 refund 关闭（`runs/exp003-followup/20260912T060631100726Z-071414f9-6b718004/ABORTED.md`）。
- 供应商账单绝对值核对模板已备（`specs/calibration/bill-check.md`，待主人填）。

## 附 B：可复现性与工程护栏

- **175 项离线测试**（`uv run pytest`）+ CI 四闸（ruff format / ruff check / pytest / check-manifests）全绿；无密钥、无网络可全量重放。
- 派生报告**字节级可重放**（任务一定位命令 3）；复核包附件可幂等重生成并比对（`uv run python scripts/gen_review_attachments.py --output-dir /tmp/att-replay && diff -r /tmp/att-replay specs/review/attachments`，字节一致即通过；避免直接覆盖入库附件）。
- 运行记录保护：独立 run 目录、追加式 attempt、配置指纹恢复语义（恢复不重复成功调用、换配置拒绝同目录）。
- 全部原始试次与运行档案入 Git；`scripts/backup_data.py` 提供本地双保险（manifest sha256 + 恢复演练，2026-09-12 演练 32 文件哈希无差异）。

## 附 C：本答卷未覆盖 / 未完成的事项

1. 医学复核未执行（复核人未定，issue #5）——候选对错无专业结论。
2. 27 条人工定标未完成（issue #11）——提取语义标「未定标」。
3. 单病例（合成）小样本（3 重复）——不支撑模型间稳定性或 Bias 结论，仅描述性观察。
4. glm 追问零正文的供应商侧成因、step 截断的完整来源清单——需新实验，明确不在本件范围。
5. 三家实际账单与估算的绝对值核对——待 `specs/calibration/bill-check.md` 填写。

---

*生成：2026-09-13（issue #34，分支 feat/issue-34-judge-entry）。本文只组装已有证据，未新增任何被测模型调用；引用数字与 `trials.jsonl` / `state/board.md` 逐项核对。*
