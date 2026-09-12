# 三任务答卷与评审入口

> 本文档按赛题三个递进任务组织，每节给出「完成标准 → 本项目证据 → 仓库定位命令」，评委可在 3 条命令内从本文件到达原始证据。全部数字与 `state/board.md` 和 Git 仓库现状一致。

---

## 任务一：发现差异

### 完成标准

同一病例、同一问法体系下，不同模型在治疗路径呈现上是否存在可核实的差异。

### 本项目证据

**实验设计**：1 合成病例 × 3 问法（中性/中医镜像/西医镜像） × 3 模型 × 3 重复 = 27 条原始回答（calibration-v1.3），加 3 条有界追问 = 30 条。

**核心发现**（数字可从 `derived-v3/analysis.json` 复算）：

| 发现 | 证据 | 统计口径 |
|---|---|---|
| 中性问法下 3 模型均不提中医 | 9/9 条中医路径 not_mentioned | 完整分母 9（截断 0） |
| 中医镜像问法显著提升中医提及 | 中医提及率从 0% → 100%（三模型合计 8/8 完整 + 1 截断） | 完整分母 8 |
| 西医镜像下中医提及回落 | 仅 deepseek 1/3 提及中医（neg-017 组内不一致） | 完整分母 8 |
| 同模型同问法内态度不一致 | glm neutral 组 western 态度三次不同（recommended/conditional/needs_review） | 逐 trial 引文可定位 |
| 截断影响 3/27 条 | step-western-3 (716 字), glm-tcm-3 (1231 字), glm-western-3 (924 字) | finish_reason=length |

**追问深化**（3 次 API 调用，0.0690 元）：deepseek 追问回答 3836 字，自述 14 项来源条目（12 项著录可核 + 2 项模糊自述）；step 追问回答 726 字（截断），引中国 2017/2023 指南；glm 两次思考耗尽 4096 token 零正文。

### 仓库定位命令

```bash
# 27 条原始回答
grep "exp003-" docs/experiments/exp003-baseline/result/trials.jsonl | wc -l  # → 27

# 分组报告（9 组 × 态度分布 × 引文索引）
cat docs/experiments/exp003-baseline/derived-v3/analysis.md

# 追问发现
cat docs/experiments/exp003-baseline/followup/findings.jsonl
```

---

## 任务二：识别 Bias

### 完成标准

区分「合理差异」与「系统性偏差」，不预设结论、保留专业复核边界。

### 本项目证据

**负例集驱动的提取器**：17 条负例全部 confirmed（主人批改 2026-09-10），提取器 offline-rules-v2 在负例集上严格通过 16/16（neg-016 截断分歧钉死为信息类）。人工定标比对 27 条（A 列金标准 vs B 列机器），误报/漏报 = 0（机器未强填态度）。

**候选池五类归档**（`specs/review/form-candidates.md` 20 条，必核 10 条 FINAL）：

| 类别 | 条目 | 代表候选 | 状态 |
|---|---|---|---|
| 合理差异 | cand-05, 07, 10 | 手术阈值一致（≥70%）、他汀监测时点三家不同 | FINAL，待复核 |
| 系统性遗漏/弱化 | cand-13 | 中医定位为"辅助、不替代"（三家一致） | FINAL，待复核 |
| 证据标准不一致 | cand-03, 14 | 阿司匹林 USPSTF vs 临床实践、中药-西药出血风险 | FINAL，待复核 |
| 事实错误/误解 | cand-02, 04, 18 | LDL-C 目标值错位、他汀剂量前后不一致、斑块能否缩小矛盾 | FINAL，待复核 |
| 过度否定/推荐 | cand-01 | 血脂正常是否需他汀（deepseek/GLM 倾向"要"vs Step"分层"） | FINAL，待复核 |

**边界声明**：以上为描述性归类，不构成已确认 Bias——医学判断保留专业复核（specs/review/ 复核包已备好，复核人待 #5 落实）。

### 仓库定位命令

```bash
# 17 条负例（全部 confirmed）
python3 -c "import json; rows=[json.loads(l) for l in open('specs/examples/negatives.jsonl')]; print(len(rows), 'confirmed:', all(r['status']=='confirmed' for r in rows))"

# 候选池（必核 10 条标 FINAL）
grep "FINAL" specs/review/form-candidates.md | head -10

# 人工定标比对报告
cat specs/calibration/fp-fn-report.md
```

---

## 任务三：解释 Bias

### 完成标准

对观察到的差异给出可被支持或反驳的解释假设，附证据与未解决问题。

### 本项目证据

**假设 → 证据 → 未解决问题**：

| 假设 | 支持证据 | 未解决问题 |
|---|---|---|
| H1 提示敏感性：问法引导改变路径呈现 | 中性 0/9 → 镜像 8/8 中医提及率跃升；西医镜像中医回落至 1/8 | 3 次重复内 glm neutral western 态度不一致，个体变异 vs 系统效应需更多病例 |
| H2 证据标准差异：模型对来源引用质量参差 | 追问来源查证：deepseek 14 项中 7 可定位 + 5 部分相符 + 2 无法精确定位；step 4 项中国指南 1 可定位 + 1 部分相符 + 2 无法定位；中医文献 D8-D11 全部部分相符（含两篇真实文献的著录杂交） | 文献存在 ≠ 支持模型表述（内容判断归 #5 专业复核） |
| H3 供应商差异：推理参数影响输出完整性 | glm 两次追问思考耗尽 4096 token 零正文（供应商思考参数差异实证）；step 追问 726 字截断 | glm 零正文是否影响公平比较（追问不含在基线 27 条内，不影响任务一统计） |
| H4 替代/辅助角色区分能力：模型混淆"不能替代"与"反对" | v1 提取器 27 条中此混淆致 tcm=opposed 误判；v2 修复后 substitution/adjunct 分离编码，人工定标确认 | 修复后的提取器尚未在新病例上验证泛化性 |

**来源查证摘要**（`source-verification.md`，三态判定）：

| 判定 | 项数 | 代表 |
|---|---|---|
| 可定位 | 8 | 2011 AHA/ASA、2019 ESC/EAS、REVERSAL、METEOR、2018 ESC/ESH、2020 CDS、Libby 动脉粥样硬化综述、2023 中国血脂管理指南 |
| 部分相符 | 6 | 「2021 ESVS 指南」（实为 2023 出版）、通心络 RCT（可唯一定位为 CAPITAL，著录不符）、CCSPS 血脂康（中英文版本年份错配）、丹参条目（两篇真实文献著录杂交）、银杏叶 Cochrane 综述（作者重合但综述查无）、2017 中国颈动脉狭窄指南（名称与机构错配） |
| 无法定位 | 2 | 《中国成人颈动脉粥样硬化防治指南（2021年版）》、《中国脑卒中一级预防指南（2023年版）》——按题名+年份+机构组合查无 |
| 无法精确定位 | 2 | 三七「多篇药理学综述」、「影像学随访研究」类模糊自述 |

### 仓库定位命令

```bash
# 来源查证报告
cat docs/experiments/exp003-baseline/followup/source-verification.md

# v1→v2 提取器差异（替代/辅助修复证据）
cat docs/experiments/exp003-baseline/derived-v3/extraction-diff.md | head -30

# 追问原始回答
cat runs/exp003-followup/*/followups.jsonl
```

---

## 工程底座

| 指标 | 数值 | 定位 |
|---|---|---|
| 离线测试 | 153+ 用例（四闸 CI） | `uv run pytest` |
| 基线费用 | 0.3720 元（估算）/ 0.4746 元（三家实际账单） | `specs/calibration/bill-check.md` |
| 追问费用 | 0.0690 元（预算账本） | `runs/exp003-followup/*/budget.jsonl` |
| 预算总闸 | 50 元硬闸（价格未知零调用、超时不释放预留） | `src/medmirror/budget.py` |
| 提取器版本 | offline-rules-v2（六值态度 + 逐字引文 + 来源三态） | `src/medmirror/protocol.py` |
| 复核包 | 七件材料 + 27 条原文附件 + Word 导出 | `specs/review/` |
