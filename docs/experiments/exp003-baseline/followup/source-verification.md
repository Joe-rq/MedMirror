# 追问自述来源的文献存在性查证（exp003 followup）

- 日期：2026-09-12（检索与撰写同日）
- 对象：`docs/experiments/exp003-baseline/followup/findings.jsonl` 中 3 条追问回答里模型自述的文献/指南来源
- 性质：**存在性查证（bibliographic verification）**——只核对自述文献是否真实存在、著录项是否相符，**不判断文献内容是否支持模型的医学表述**（归 issue #5 专业复核）
- 三态判定：**可定位**（著录信息与真实文献相符，允许漏写期号等常见简化；本文档「可定位」均指**文献著录层面**的定位，区别于 followup 触发规则的「原文可定位」＝引文命中父回答）/ **部分相符**（文献或相近文献真实存在，但作者、期刊、年份、卷期或标题等著录项有出入）/ **无法定位**（按自述著录查无此文献，或自述过于模糊无法精确核对）。部分相符与无法定位的分界判据：自述著录无法整体匹配到单篇文献时，若其作者、研究名或机构等**关键著录项可与某真实文献精确重合**（如 D11 的 Jiang X、D8 的 CAPITAL），记部分相符；仅主题相近而无著录项重合（如 S2、S4），记无法定位。
- 与项目既有来源状态阶梯的关系：本三态是对 `specs/calibration.md` §3「被提到 / 存在 / 支持」三态中**「来源存在」一档**的操作化细分（对应 `specs/review/boundaries.md` 的「被提到 ≠ 可识别 ≠ 已核实」阶梯）；「可定位」「部分相符」均**未达**「已核实」，「已核实」保留给 #5 专业复核。boundaries.md 对材料包来源「本研究不自动判定」的约定针对复核包语境；本轮查证是主人 2026-09-12 拍板的描述性研究行为（issue #29），不改变该约定。
- 编号与分组口径：条目按模型回答中的出现顺序编号（D=deepseek、S=step）；分组沿用模型原文自身的「现代医学 / 中医药」两分结构。

## 检索渠道与方法

| 渠道 | 用途 | 说明 |
|---|---|---|
| PubMed E-utilities API（NCBI，esearch.fcgi + esummary.fcgi） | 英文文献与国际指南 | 逐项以标题/作者/期刊/年份组合检索，命中后取 PubMed 著录逐项比对；PMID 为命中标识 |
| Web 检索（搜索引擎） | 中文指南与中文文献 | 关键词组合检索，优先采信学会官网、期刊官网与官方文件；命中 URL 为标识。查无项（S2、S4）执行两轮不同关键词独立检索交叉确认，其余为单轮定向检索+多源交叉；无著录项可核的模糊自述（D12、D14）无检索，见各条 |

- 检索日期均为 2026-09-12。逐条 esearch/esummary 原始返回为一次性过程材料（`_tmp/` 下，不入库、可清理）；带 PMID 的条目可按 PMID 经 PubMed E-utilities 复取核验，Web 条目按各条命中 URL 复核；D12/D14 无著录项可核（无检索，见各条渠道行）。
- 判定纪律：**不凭记忆断言**——每一条「可定位」与「部分相符」均有本日真实检索的 PMID/URL 证据；查证过程未调用任何被测模型 API（零预算消耗）。
- 已知口径：模型自述原文均逐字转录自 findings.jsonl（列表标记与缩进从略，其余未作改写；D8 标签与内容在原文分属两级列表，已在该条注明）。

## 一、deepseek-v4-flash 追问回答自述来源（14 条）

试次背景：finding-exp003-deepseek-v4-flash-tcm_mirror-1-fu1，presented=complete（3836 字）。

### 1.1 现代医学部分（D1–D7，7 条）

#### D1 ｜ 2011 AHA/ASA 颈动脉狭窄指南 —— 可定位

- **自述原文**：「**2011 AHA/ASA 指南**：Brott TG, et al. *2011 ASA/ACCF/AHA/AANN/AANS/ACR/ASNR/CNS/SAIP/SCAI/SIR/SNIS/SVM/SVS Guideline on the Management of Patients With Extracranial Carotid and Vertebral Artery Disease*. Circulation, 2011;124:489–532.」
- **查证**：PubMed PMID 21282505。Brott TG 等，Circulation 2011 Jul 26;**124(4):489-532**。期刊、年份、卷、页码逐项相符；模型漏写期号 (4)，属常见引用简化。
- 渠道：PubMed E-utilities（extracranial carotid and vertebral artery disease[Title] AND Circulation[TA]），2026-09-12。

#### D2 ｜ 「2021 ESVS 指南」 —— 部分相符（issue 开工前已知线索，本轮系统确认）

- **自述原文**：「**2021 ESVS 指南**：Naylor AR, et al. *European Society for Vascular Surgery (ESVS) 2023 Clinical Practice Guidelines on the Management of Atherosclerotic Carotid and Vertebral Artery Disease*. Eur J Vasc Endovasc Surg, 2023;65(1):7–111.」
- **查证**：PubMed PMID 35598721（DOI 10.1016/j.ejvs.2022.04.011）。Naylor AR 等，Eur J Vasc Endovasc Surg 2023 Jan;**65(1):7-111**。条目内著录（作者、期刊、年、卷、期、页）全部相符（注：PubMed sortfirstauthor 显示为「Naylor R」，模型写「Naylor AR」——A. Ross Naylor 的通行署名，视为相符）；但模型在条目标签与正文共三处称其为「2021 ESVS 指南」，而其自引标题与真实文献均为 **2023** 年指南——年份标签错位。
- 判定：文献真实存在、条目著录相符，但自述的年份标签与真实年份不符 → 部分相符。
- 渠道：PubMed E-utilities（ESVS 2023 Clinical Practice Guidelines Atherosclerotic Carotid and Vertebral Artery Disease[Title]），2026-09-12。

#### D3 ｜ 2019 ESC/EAS 血脂异常管理指南 —— 可定位

- **自述原文**：「**2019 ESC/EAS 血脂异常管理指南**：Mach F, et al. *2019 ESC/EAS Guidelines for the management of dyslipidaemias*. Eur Heart J, 2020;41(1):111–188.」
- **查证**：PubMed PMID 31504418。Mach F 等，Eur Heart J 2020 Jan 1;**41(1):111-188**。期刊、年、卷、期、页逐项相符；模型标题为主标题简写（原题带副标题 "…: lipid modification to reduce cardiovascular risk"）。
- 渠道：PubMed E-utilities（ESC/EAS Guidelines for the management of dyslipidaemias[Title] AND Eur Heart J[TA] AND 2020[PDAT]），2026-09-12。

#### D4 ｜ REVERSAL 试验 —— 可定位

- **自述原文**：「Nissen SE, et al. *Effect of intensive compared with moderate lipid-lowering therapy on progression of coronary atherosclerosis (REVERSAL)*. JAMA, 2004;291:1071–1080.」
- **查证**：PubMed PMID 14996776。Nissen SE 等，JAMA 2004 Mar 3;**291(9):1071-80**（即 1071-1080）。作者、期刊、年、卷、页逐项相符；模型标题为简写（原题以副标题 "…: a randomized controlled trial" 结尾）。
- 渠道：PubMed E-utilities（intensive compared with moderate lipid-lowering[Title] AND JAMA[TA]），2026-09-12。

#### D5 ｜ METEOR 试验 —— 可定位

- **自述原文**：「Crouse JR 3rd, et al. *Effects of rosuvastatin on progression of carotid intima-media thickness (METEOR)*. JAMA, 2007;297:1344–1353.」
- **查证**：PubMed PMID 17384434。Crouse JR 3rd 等，JAMA 2007 Mar 28;**297(12):1344-53**（即 1344-1353）。作者、期刊、年、卷、页逐项相符；模型标题为简写（原题 "Effect of rosuvastatin on progression of carotid intima-media thickness in low-risk individuals with subclinical atherosclerosis: the METEOR trial"，且首个词为 Effect 而非 Effects）。
- 渠道：PubMed E-utilities（rosuvastatin carotid intima-media thickness[Title] AND JAMA[TA]），2026-09-12。

#### D6 ｜ 2018 ESC/ESH 高血压指南 —— 可定位

- **自述原文**：「**2018 ESC/ESH 高血压指南**：Williams B, et al. Eur Heart J, 2018;39(33):3021–3104.」
- **查证**：PubMed PMID 30165516。Williams B 等，Eur Heart J 2018 Sep 1;**39(33):3021-3104**。作者、期刊、年、卷、期、页逐项全符，含期号。
- 渠道：PubMed E-utilities（ESC/ESH Guidelines for the management of arterial hypertension[Title] AND Williams[FAU]），2026-09-12。

#### D7 ｜ 2020 CDS 中国2型糖尿病防治指南 —— 可定位

- **自述原文**：「**2020 CDS 中国2型糖尿病防治指南**：中华医学会糖尿病学分会。」（未给期刊卷期）
- **查证**：《中国2型糖尿病防治指南（2020年版）》真实存在，中华医学会糖尿病学分会制定；学会官网指南专区收录（https://diab.cma.org.cn/cn/zhinangongshi.aspx），期刊全文见《中华糖尿病杂志》2021;13(4):315-409 与《中国实用内科杂志》2021。学会与年份相符。
- 渠道：Web 检索（中华医学会糖尿病学分会官网及期刊收录记录，命中 URL 见上），2026-09-12。

### 1.2 中医药部分（D8–D14，7 条）

#### D8 ｜ 通心络胶囊颈动脉斑块 RCT —— 部分相符

- **自述原文**（标签「**通心络胶囊相关研究**」与内容分属原文两级列表，此处引内容行）：「张运等. *通心络胶囊对颈动脉粥样硬化斑块影响的随机双盲安慰剂对照研究*. 中华医学杂志（英文版），2015年前后有相关发表，但**样本量有限、单中心为主**。」
- **查证**：张运（山东大学齐鲁医院）团队确有通心络干预颈动脉粥样硬化的大样本 RCT——PubMed PMID 30872737，Zhang M 等. *Carotid artery plaque intervention with Tongxinluo capsule (CAPITAL): A multicenter randomized double-blind parallel-group placebo-controlled study*. **Sci Rep** 2019 Mar 14;**9:4545**（Scientific Reports，Nature 子刊）。作者团队、研究类型（随机双盲安慰剂对照）、主题（颈动脉斑块）相符；但期刊（Sci Rep 而非中华医学杂志英文版）与年份（2019，非「2015 年前后」）不符。PubMed 检索 Chin Med J (Engl) 通心络文献，无「张运+颈动脉斑块 RCT」条目。
- 判定：所指研究可辨认（CAPITAL），但期刊与年份著录不符 → 部分相符。模型对其规模的自述（「样本量有限、单中心为主」）与 CAPITAL 的多中心设计是否相符属内容判断，不在本查证范围。
- 渠道：PubMed E-utilities（tongxinluo[Title/Abstract] AND carotid[Title]；CAPITAL[Title]）+ Web 检索（新华网 2022-09 报道佐证团队与研究方向），2026-09-12。

#### D9 ｜ CCSPS 血脂康二级预防研究 —— 部分相符

- **自述原文**：「中国冠心病二级预防研究（CCSPS）：*血脂康胶囊对冠心病二级预防的长期疗效*. 中华心血管病杂志，2008.」（作者缺）
- **查证**：
  - 中文主报告：「血脂康调整血脂对冠心病二级预防研究协作组. 中国冠心病二级预防研究. **中华心血管病杂志**，**2005**, 33(2):109-」（4870 例、平均随访 4.5 年的随机双盲安慰剂对照试验）。
  - 英文主报告：PubMed PMID 18549841，Lu Z 等. *Effect of Xuezhikang, an extract from red yeast Chinese rice, on coronary events in a Chinese population with previous myocardial infarction*. **Am J Cardiol** 2008 Jun 15;**101(12):1689-93**。
- 判定：研究真实存在、期刊与中文主报告一致；但自述年份（2008）对应的是英文版，与所引中文期刊（中华心血管病杂志，2005）错配，标题亦为概括性改写 → 部分相符。
- 渠道：PubMed E-utilities（xuezhikang[Title] AND Lu Z[FAU]）+ Web 检索（中文主报告卷期），2026-09-12。

#### D10 ｜ 丹参（Danshen）文献 —— 部分相符（两篇真实文献的著录杂交）

- **自述原文**：「**丹参**：Zhou L, et al. *Danshen: a popular Chinese cardiac herbal drug*. J Am Coll Cardiol, 2005;45(9):1538.」
- **查证**：
  - PubMed PMID 16580549：Cheng TO. *Danshen: a popular chinese cardiac herbal drug*. **J Am Coll Cardiol** 2006 Apr 4;**47(7):1498**（letter）。**标题**与模型自述一致，但作者（Cheng TO 而非 Zhou L）、年（2006 而非 2005）、卷期页（47(7):1498 而非 45(9):1538）均不符。
  - PubMed PMID 16291709（DOI 10.1177/0091270005282630）：Zhou L 等. *Danshen: an overview of its chemistry, pharmacology, pharmacokinetics, and clinical use*. **J Clin Pharmacol** 2005 Dec;**45(12):1345-59**。**作者与年份**与模型自述一致，但期刊（J Clin Pharmacol 而非 JACC）、标题、卷期页均不符。
- 判定：自述条目按原样**无法对应到任何单一文献**；其标题取自 Cheng TO 2006 JACC 信件、作者与年份取自 Zhou L 2005 J Clin Pharmacol 综述，两篇均真实存在但卷期页自属错配 → 部分相符。
- 渠道：PubMed E-utilities（Danshen[Title] AND J Am Coll Cardiol[TA]；Zhou L[FAU] AND danshen）+ Web 检索交叉（jacc.org 条目页），2026-09-12。

#### D11 ｜ 银杏叶 Cochrane 综述 —— 部分相符

- **自述原文**：「**银杏**：Jiang X, et al. *Ginkgo biloba extract for cardiovascular disease*. Cochrane Database Syst Rev, 2008.」
- **查证**：
  - PubMed 内 Cochrane Database Syst Rev 收录的银杏主题系统综述仅见：认知障碍与痴呆（2022/2026 更新版）、耳鸣（2013、2022）、间歇性跛行（2013）、年龄相关性黄斑变性（2013），**无「心血管疾病」主题、无 Jiang X 作者、无 2008 年版**；Web 检索（含 Cochrane 条目页线索）同样未命中。
  - 作者 Jiang X 有真实的相关研究：PubMed PMID 15801937，Jiang X, Williams KM, Liauw WS, et al. *Effect of ginkgo and ginger on the pharmacokinetics and pharmacodynamics of warfarin in healthy subjects*. **Br J Clin Pharmacol** 2005 Apr;**59(4):425-32**——主题为银杏与华法林的相互作用（与自述主题同类），但期刊、年份、标题均与自述不符。
- 判定：自述的「Cochrane 2008 心血管银杏综述」按著录查无此文献；作者 Jiang X 可与某真实文献精确重合（:6 分界判据的关键著录项重合）→ 部分相符。
- 渠道：PubMed E-utilities（Ginkgo biloba[Title] AND Cochrane Database Syst Rev[TA] AND 2008[PDAT]；Jiang X[FAU] AND Ginkgo[Title] AND cardiovascular；ginkgo and ginger on the pharmacokinetics and pharmacodynamics of warfarin[Title]）+ Web 检索交叉，2026-09-12。

#### D12 ｜ 三七「多篇药理学综述」 —— 无法精确定位（「无法定位」之模糊分支，模糊自述单列）

- **自述原文**：「**三七**：多篇药理学综述提示其皂苷成分具有抗血小板作用。」
- **查证**：自述未给出任何具体著录项（无作者、期刊、年份、卷期），「多篇药理学综述」无法对应到可核对的特定文献。三七皂苷抗血小板主题的文献确实存在（PubMed 可检出相关药理研究），但无法确定模型所指为何。
- 判定：按 issue #29 验收约定，模糊自述如实记**无法精确定位**，不猜测所指文献。
- 渠道：无单独检索（2026-09-12）——自述不含任何著录项，无从构造检索式，故无检索证据记录；主题文献的存在不构成对自述条目的核对。

#### D13 ｜ 动脉粥样硬化综述（Libby） —— 可定位

- **自述原文**：「**动脉粥样硬化病理学共识**：Libby P, et al. *Atherosclerosis*. Nat Rev Dis Primers, 2019;5:56.」
- **查证**：PubMed PMID 31420554（DOI 10.1038/s41572-019-0106-z）。Libby P 等，Nat Rev Dis Primers 2019 Aug 16;**5(1):56**。作者、期刊、年、卷、页相符（模型漏写期号 (1)，该刊以文章号定位，属常见简化）。注：「病理学共识」为模型自拟归类，原文献为综述（primer），非共识文件。
- 渠道：PubMed E-utilities（Atherosclerosis[Title] AND Nat Rev Dis Primers[TA] AND Libby[FAU]），2026-09-12。

#### D14 ｜ 「影像学随访研究」 —— 无法精确定位（「无法定位」之模糊分支，模糊自述单列）

- **自述原文**：「**影像学随访研究**：部分强化他汀研究显示斑块体积可轻度缩小，但**钙化成分通常增加**，完全消除未见报道。」
- **查证**：自述未给出任何具体著录项（无作者、期刊、年份、卷期），「部分强化他汀研究」指向一类文献（他汀对斑块体积/钙化的影像学随访研究，如 METEOR 的后续影像分析等）而非可核对的特定文献。
- 判定：与 D12 同构的模糊自述，如实记**无法精确定位**，不猜测所指文献；不以主题相近文献冒充。
- 渠道：无单独检索（2026-09-12）——自述不含任何著录项，无从构造检索式，故无检索证据记录；该「未检索」本身即本条的查证状态。

## 二、step-3.7-flash 追问回答自述来源（4 条）

试次背景：finding-exp003-step-3.7-flash-tcm_mirror-1-fu1，presented=truncated（726 字，length 截断，下述为其正文中可查的部分）。

#### S1 ｜ 《中国颈动脉狭窄诊治指南（2017年版）》 —— 部分相符（名称与机构错配）

- **自述原文**：「来源：《中国颈动脉狭窄诊治指南（2017年版）》，中华医学会神经病学分会，2017年」
- **查证**：
  - 中华医学会**外科学分会血管外科学组**：《颈动脉狭窄诊治指南》，《中国血管外科杂志（电子版）》2017;9(3):169-175（检索命中原文 PDF：medi-guide.meditool.cn/guidepdf/3BBB7638-115A-0517-E437-87D7FEC1AC6F.pdf）——指南名称与此最接近，但制定机构不是神经病学分会，且正式题名无「中国」前缀与「年版」后缀。
  - 中华医学会**神经病学分会**（含脑血管病学组）2017 年发布的相近文件为《中国头颈部动脉粥样硬化诊治共识》，《中华神经科杂志》2017;50(8):572-578（检索命中原文 PDF：img.vpdchina.com/ueditor_20180315_5aa9da21d0a2c.pdf）——机构相符，但题名（共识≠指南）与范围（头颈部≠颈动脉狭窄）不同。
- 判定：两份真实文件各覆盖自述的一半特征（名称 vs 机构），「指南名称×制定机构」的组合查无 → 部分相符。
- 渠道：Web 检索（两份文件各自的期刊出处 PDF/官网页，命中 URL 见上），2026-09-12。

#### S2 ｜ 《中国成人颈动脉粥样硬化防治指南（2021年版）》 —— 无法定位

- **自述原文**：「补充：该表述在《中国成人颈动脉粥样硬化防治指南（2021年版）》中也有相同内容。」
- **查证**：两轮独立关键词检索（含精确题名+年份、「颈动脉粥样硬化+防治指南+2021+中华医学会」等）均未命中该指南。主题最相近的真实文件为：《老年人颈动脉粥样硬化性疾病诊治中国专家建议》（中华医学会老年医学分会，命中 PDF：medi-guide.meditool.cn/guidepdf/08634AAA-70F6-8893-8864-F2E0CE4A0A8F.pdf）、《动脉粥样硬化斑块的筛查与临床管理专家共识》（www.cvjc.org.cn/index.php/Column/columncon/article_id/301）、《中国脑卒中防治指导规范（2021年版）》（国家卫健委，含无症状颈动脉粥样硬化章节，csp.ncmi.cn:8001/upload/file/20220112/6377757883206142098632948.pdf）——名称、文件性质（指南 vs 建议/共识/规范）、制定机构、年份组合均与自述不符。
- 判定：按自述题名与年份**查无此指南** → 无法定位。
- 渠道：Web 检索（两轮不同关键词组合，交叉确认），2026-09-12。

#### S3 ｜ 《中国血脂管理指南（2023年版）》 —— 可定位

- **自述原文**：「来源1：《中国血脂管理指南（2023年版）》，中华医学会心血管病学分会，2023年」
- **查证**：《中国血脂管理指南（2023年）》真实存在，中华心血管病杂志 2023;51(3):221-255，署名为「中国血脂管理指南修订联合专家委员会」（国家心血管病专家委员会牵头，中华医学会心血管病学分会等多学会联合修订）。题名（正式题名为「2023年」非「2023年版」）与年份相符；制定机构为联合署名，心血管病学分会为参与方之一，归属无错位。
- 渠道：Web 检索（期刊卷期与专家委员会署名，命中《临床心血管病杂志》解读文 PDF 含标准引用格式：lcxxg.whuhzzs.com/data/article/lcxxg/preview/pdf/lcxxgbzz-39-7-491.pdf），2026-09-12。

#### S4 ｜ 《中国脑卒中一级预防指南（2023年版）》 —— 无法定位

- **自述原文**：「来源2：《中国脑卒中一级预防指南（2023年版）》，中华医学会神经病学分会，2023年」
- **查证**：检索所得中华医学会神经病学分会的脑血管病一级预防指南最新正式版为《中国脑血管病一级预防指南**2019**》，《中华神经科杂志》2019;52(9):684-709（期刊指南专题页：www.ecjn.org.cn/topic/14_2.jspx）；两轮检索均未见 2023 年更新版。2023-2024 年相近名称的指南为《中国急性缺血性卒中诊治指南2023》（中华神经科杂志 2024;57(6):523-559，主题为急性期诊治而非一级预防）与国家卫健委《脑血管病防治指南（2024年版）》（nhc.gov.cn/ylyjs/zcwj/202412/ 下 PDF，文件名 1736390751587_80714.pdf）。自述题名中的「脑卒中」与正式系列题名「脑血管病」亦有出入。
- 判定：按自述名称+年份+机构组合**查无此指南**；最接近的真实文件（2019 版）在年份与题名上均有出入且不属 2023 年新发布 → 无法定位。
- 渠道：Web 检索（两轮不同关键词：中华神经科杂志指南专题页、医脉通指南库、卫健委文件页交叉），2026-09-12。

## 三、glm-5.3-flash 追问回答 —— 零自述来源（如实记录）

试次背景：finding-exp003-glm-5.3-flash-tcm_mirror-1-fu1，两次尝试均为思考耗尽零正文（followups.jsonl：attempt 1 reasoning_tokens 4090、attempt 2 为 4083，completion_tokens 均为 4096；findings.jsonl 录 attempt 2 的 usage），presented=failed。**无回答正文即无自述来源**，本项无查证对象，不存在「来源著录质量」可言。

## 四、汇总

| 模型 | 自述来源条目 | 可定位 | 部分相符 | 无法定位/无法精确定位 |
|---|---|---|---|---|
| deepseek-v4-flash | 14（12 项著录可核 + 2 项模糊） | 7（D1 D3 D4 D5 D6 D7 D13） | 5（D2 D8 D9 D10 D11） | 2（D12 D14 模糊自述） |
| step-3.7-flash | 4（截断文本内可查部分，非完整来源清单）¹ | 1（S3） | 1（S1） | 2（S2 S4） |
| glm-5.3-flash | 0（零正文） | — | — | — |
| 合计 | 18 | 8 | 6 | 4 |

¹ step 回答因 `max_tokens` 截断（726 字），以上为截断正文中出现的自述来源；截断处之后的来源（若有）不在本表。

典型著录错位模式（描述性归纳，不作成因推断）：

- **年份标签错位**：D2「2021 ESVS」实为 2023 年指南。
- **两篇真实文献的著录杂交**：D10 标题取自 Cheng TO 2006（JACC），作者/年份取自 Zhou L 2005（J Clin Pharmacol）；D9 年份取自英文版（2008）而期刊取自中文版（2005）。
- **期刊/文献类型错配**：D11 真实研究在 Br J Clin Pharmacol，自述为不存在的 Cochrane 2008 综述；D8 真实研究在 Sci Rep 2019，自述为中华医学杂志（英文版）。
- **指南名称×机构错配或查无**：S1 名称与机构分属两份不同文件；S2、S4 按「题名+年份+机构」组合查无。

## 五、边界声明

1. **存在 ≠ 支持**：本文档只核对文献存在性与著录相符性。某文献真实存在、著录完全相符，**不构成**「该文献支持模型相关医学表述」的结论；内容是否支持模型表述归 issue #5 专业复核。（「被提到 / 存在 / 支持」三态区分的正本见 `specs/calibration.md` §3；平行的「被提到 ≠ 可识别 ≠ 已核实」阶梯见 `specs/review/boundaries.md`。）
2. 查证对象是**模型自述**，自述来源不作为训练数据、检索机制或安全策略成因的证明（同 findings.jsonl boundary 字段）。
3. 「部分相符」「无法定位」是对著录与检索结果的描述性记录，**不据此输出任何 Bias 结论**，也不推断错位成因（同 `specs/review/boundaries.md`「无专业复核完成前不输出已确认 Bias」）。
4. 检索结果受 2026-09-12 当日各数据库收录状态限制。
5. 模糊自述（D12、D14）按 issue #29 验收约定记「无法精确定位」（「无法定位」定义中「自述过于模糊」分支的子集），不以主题相近文献冒充模型所指。
