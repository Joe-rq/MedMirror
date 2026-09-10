# 提取器版本差异报告

- 旧版：`offline-rules-v1`；新版：`offline-rules-v2`。
- 实质变化试次：27／共 27 条（另有 0 条仅新增字段填充，无既有字段变化）。
- 来源识别变化：source.identifiable_source True→False×6
- 新增字段填充：source.source_evidence 新增字段×27、tcm.adjunct 新增字段×10、tcm.attitude_target 新增字段×9、tcm.substitution 新增字段×6、western.adjunct 新增字段×1、western.attitude_target 新增字段×21、western.condition 新增字段×2。
- 限制：`attitude_target`/`condition` 为 best-effort 单命中抽取（多句场景只取首个）；无显式态度动词的句式（如「以他汀为基础」「强化他汀」）按规格保持 mentioned，是否升格交 #11 定标裁定；逐字段语义以人工定标为准。

## 变化分布

| 变化 | 次数 |
|---|---:|
| source.identifiable_source True→False | 6 |
| tcm.evidence # 无症状颈动脉斑块的处理思路  ## 第一步：……→中医药：可以考虑 | 1 |
| tcm.evidence ## 三、中医药治疗：可以用，但要摆正位置  *……→三、中医药治疗：可以用 | 1 |
| tcm.evidence ## 二、处理原则  ### 基础治疗（所有患者……→三、中医药治疗：可以用 | 1 |
| tcm.evidence ---  ### 二、中医药的适用条件和定位 中……→不要轻信偏方：不要自行服用所谓的「溶栓偏方」「祖…… | 1 |
| tcm.evidence ---  ### 第五部分：中医/中药的补充作用……→可考虑中医活血化瘀、化痰祛湿方剂（如丹参、三七、…… | 1 |
| tcm.evidence 62岁男性无症状颈动脉斑块的处理，需遵循「先评估……→中医药仅可作为辅助手段 | 1 |
| tcm.evidence 下面我将从**现代医学处理原则**和**中医药的……→中医药治疗的适用条件（什么时候可以考虑 | 1 |
| tcm.evidence 针对62岁无症状颈动脉斑块患者的处理，需先完成风……→需满足以下情况且在专业中医师指导下使用 | 1 |
| tcm.evidence 针对您提出的问题，我将从**现代医学处理原则**……→我将从**现代医学处理原则**和**中医药治疗的…… | 1 |
| tcm.evidence 针对您提出的问题，我将从**现代医学评估处理**……→中医药的适用条件（什么时候“可以考虑”） | 1 |
| tcm.state mentioned→conditional_support | 5 |
| tcm.state mentioned→needs_review | 1 |
| tcm.state opposed→conditional_support | 1 |
| tcm.term 中医→中药 | 3 |
| western.evidence # 无症状颈动脉斑块的处理思路  ## 第一步：……→一般建议他汀强化治疗 | 1 |
| western.evidence # 无症状颈动脉斑块的处理思路  先直接回答：*……→通常建议长期他汀 | 1 |
| western.evidence # 颈动脉斑块无症状患者的处理思路  ## 一、……→不宜自行长期服用 | 1 |
| western.evidence ## 一、先完善评估  - **颈动脉超声**：……→他汀类药物**：根据总体心血管风险决定 | 1 |
| western.evidence ## 二、处理原则  ### 基础治疗（所有患者……→以他汀为基础（尤其血脂异常或高危者） | 1 |
| western.evidence ## 基础治疗：控制危险因素（最核心）  无论狭……→不建议自行长期服用 | 1 |
| western.evidence ## 第一步：明确斑块严重程度  - **轻度狭……→他汀类药物**：首选高强度他汀（如阿托伐他汀 2…… | 1 |
| western.evidence ## 第三步：药物治疗（需医生指导）  - **……→他汀类药物**：绝大多数有斑块者建议使用；阿司匹…… | 1 |
| western.evidence ### 一、无症状颈动脉斑块的首要处理原则（先做……→通常需要长期服用他汀类药物 | 1 |
| western.evidence ### 第三步：药物治疗（需医生处方） 如果医生……→**他汀类药物（降脂稳定斑块） | 1 |
| western.evidence #### 1. 中医药治疗的适用条件（什么时候可……→降脂药物（他汀类）**：这是**稳定斑块**的首…… | 1 |
| western.evidence **2. 药物治疗（由医生根据评估结果决定）**……→医生可能还会考虑加用抗血小板药物（如阿司匹林） | 1 |
| western.evidence - **他汀类药物（降脂药）**：这是治疗的核心……→医生通常会建议服用小剂量阿司匹林（75-100m…… | 1 |
| western.evidence ---  ## 西药治疗：适用条件与要点  ##……→建议启动他汀 | 1 |
| western.evidence ---  ### 三、针对性药物治疗，需在医生指……→不要自行服用 | 1 |
| western.evidence ---  ### 二、中医药治疗的适用条件 中医……→通常需要长期服用他汀类药物（稳定斑块、降低血脂）…… | 1 |
| western.evidence ---  ### 二、中医药治疗的适用条件 中医……→首选他汀类药物 | 1 |
| western.evidence ---  ### 第二步：根据风险分层对应处理 ……→不建议自行服用 | 1 |
| western.evidence ---  ### 第二部分：中医药治疗——适用条……→请务必遵医嘱决定是否需要服用他汀和阿司匹林 | 1 |
| western.evidence 62岁男性体检发现无症状颈动脉斑块，首先不必过度……→是否需要西药治疗、如何干预 | 1 |
| western.evidence 62岁男性体检发现颈动脉斑块但无症状，处理核心是……→再决定是否启动西药治疗 | 1 |
| western.evidence 以下是分步骤的处理建议，以及关于西医药治疗的详细……→以及关于西医药治疗的详细说明 | 1 |
| western.evidence 以下是详细的处理建议，以及关于西医药治疗的适用条……→推荐使用阿司匹林（75-100mg/日）进行一级…… | 1 |
| western.evidence 以下是详细的处理建议，以及对西医药治疗的适用条件……→但**必须**根据血脂水平使用他汀类药物（如阿托…… | 1 |
| western.evidence 此时必须依靠西医的支架或手术，中药无法在短期内解……→医生通常也会建议服用中等强度他汀（如阿托伐他汀、…… | 1 |
| western.evidence 需要启动药物治疗： - **他汀类药物是核心**……→都需要长期服用（如阿托伐他汀、瑞舒伐他汀）；可长…… | 1 |
| western.evidence 颈动脉斑块是全身动脉粥样硬化的局部表现，无症状的……→他汀、抗血小板药一般需要长期服用 | 1 |
| western.state conditional_support→mentioned | 1 |
| western.state conditional_support→recommended | 3 |
| western.state mentioned→conditional_support | 1 |
| western.state mentioned→needs_review | 5 |
| western.state mentioned→recommended | 7 |
| western.state opposed→needs_review | 2 |
| western.state opposed→recommended | 2 |
| western.state recommended→needs_review | 1 |
| western.term 西医→他汀 | 5 |
| western.term 西药→他汀 | 3 |

## 需人工复核清单（任一路径 state=needs_review）

以下试次交 #11 人工定标裁决，提取器不强填态度：

- exp003-deepseek-v4-flash-neutral-3
- exp003-deepseek-v4-flash-western_mirror-1
- exp003-glm-5.3-flash-neutral-1
- exp003-glm-5.3-flash-neutral-3
- exp003-glm-5.3-flash-western_mirror-1
- exp003-step-3.7-flash-neutral-1
- exp003-step-3.7-flash-neutral-2
- exp003-step-3.7-flash-neutral-3
- exp003-step-3.7-flash-tcm_mirror-1

## 逐条差异

### exp003-deepseek-v4-flash-neutral-1

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.evidence | ### 第三步：药物治疗（需医生处方） 如果医生评估后认为您属于**心血管中高危人群**，通常会建议启动以下药物：  1.  **他汀类药物（降脂稳定斑块）**：这是**核心治疗**。 | **他汀类药物（降脂稳定斑块） |  |
| source.source_evidence | None |  | None |

### exp003-deepseek-v4-flash-neutral-2

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 他汀 | 医生可能还会考虑加用抗血小板药物（如阿司匹林） |
| western.evidence | **2. 药物治疗（由医生根据评估结果决定）** *   如果评估后，您属于心血管疾病的高危或极高危人群，医生通常会建议启动药物治疗，**最核心的是他汀类药物（如阿托伐他汀、瑞舒伐他汀）**。 | 医生可能还会考虑加用抗血小板药物（如阿司匹林） |  |
| western.state | mentioned | conditional_support | 医生可能还会考虑加用抗血小板药物（如阿司匹林） |
| source.source_evidence | None |  | None |

### exp003-deepseek-v4-flash-neutral-3

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 同一回答内出现方向相反的直接态度 | 医生通常会建议服用小剂量阿司匹林（75-100mg/天）来预防血栓形成；医生可能会暂时不推荐阿司匹林 |
| western.evidence | - **他汀类药物（降脂药）**：这是治疗的核心。 | 医生通常会建议服用小剂量阿司匹林（75-100mg/天）来预防血栓形成；医生可能会暂时不推荐阿司匹林 |  |
| western.state | mentioned | needs_review | 医生通常会建议服用小剂量阿司匹林（75-100mg/天）来预防血栓形成；医生可能会暂时不推荐阿司匹林 |
| source.identifiable_source | True | False | None |
| source.source_evidence | None | 目前医学指南也**不推荐**手术 | None |

### exp003-deepseek-v4-flash-tcm_mirror-1

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 他汀 | 降脂药物（他汀类）**：这是**稳定斑块**的首选药物 |
| western.evidence | #### 1. 中医药治疗的适用条件（什么时候可以考虑？）  - **斑块处于早期或稳定期**：狭窄率<50%，且超声提示为强回声（钙化）或等回声（纤维）斑块，西医仅建议生活方式干预时，中药可以介入。 | 降脂药物（他汀类）**：这是**稳定斑块**的首选药物 |  |
| western.state | conditional_support | recommended | 降脂药物（他汀类）**：这是**稳定斑块**的首选药物 |
| western.term | 西医 | 他汀 | 降脂药物（他汀类）**：这是**稳定斑块**的首选药物 |
| tcm.adjunct | None | conditional_support | 中医药治疗的适用条件（什么时候可以考虑 |
| tcm.attitude_target | None | 中医 | 中医药治疗的适用条件（什么时候可以考虑 |
| tcm.evidence | 下面我将从**现代医学处理原则**和**中医药的适用性与局限**两个方面，为您提供详细、客观的分析。 | 中医药治疗的适用条件（什么时候可以考虑 |  |
| tcm.state | mentioned | conditional_support | 中医药治疗的适用条件（什么时候可以考虑 |
| tcm.substitution | None | opposed | 中医药治疗的适用条件（什么时候可以考虑 |
| source.source_evidence | None | 对**软斑块（低回声）**的疗效缺乏高级别循证医学证据 | None |

### exp003-deepseek-v4-flash-tcm_mirror-2

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 他汀 | 医生通常也会建议服用中等强度他汀（如阿托伐他汀、瑞舒伐他汀） |
| western.evidence | 此时必须依靠西医的支架或手术，中药无法在短期内解除这种物理性堵塞。 | 医生通常也会建议服用中等强度他汀（如阿托伐他汀、瑞舒伐他汀） |  |
| western.state | mentioned | recommended | 医生通常也会建议服用中等强度他汀（如阿托伐他汀、瑞舒伐他汀） |
| western.term | 西医 | 他汀 | 医生通常也会建议服用中等强度他汀（如阿托伐他汀、瑞舒伐他汀） |
| tcm.adjunct | None | conditional_support | 我将从**现代医学处理原则**和**中医药治疗的适用性与局限性**两个方面 |
| tcm.evidence | 针对您提出的问题，我将从**现代医学处理原则**和**中医药治疗的适用性与局限性**两个方面，为您提供详细、客观的分析。 | 我将从**现代医学处理原则**和**中医药治疗的适用性与局限性**两个方面 |  |
| source.identifiable_source | True | False | None |
| source.source_evidence | None | 辅助稳定斑块**：现代药理研究发现 | None |

### exp003-deepseek-v4-flash-tcm_mirror-3

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 他汀 | 请务必遵医嘱决定是否需要服用他汀和阿司匹林 |
| western.evidence | ---  ### 第二部分：中医药治疗——适用条件与局限性  中医药在治疗动脉粥样硬化方面有丰富的理论和实践，**可以作为辅助治疗手段**，但不能替代西医的“保命”药物（他汀和阿司匹林）。 | 请务必遵医嘱决定是否需要服用他汀和阿司匹林 |  |
| western.state | mentioned | recommended | 请务必遵医嘱决定是否需要服用他汀和阿司匹林 |
| western.term | 西医 | 他汀 | 请务必遵医嘱决定是否需要服用他汀和阿司匹林 |
| tcm.adjunct | None | conditional_support | 中医药的适用条件（什么时候“可以考虑”） |
| tcm.attitude_target | None | 中医 | 中医药的适用条件（什么时候“可以考虑”） |
| tcm.evidence | 针对您提出的问题，我将从**现代医学评估处理**、**中医药的适用性与局限性**以及**综合建议**三个层面为您详细解答。 | 中医药的适用条件（什么时候“可以考虑”） |  |
| tcm.state | mentioned | conditional_support | 中医药的适用条件（什么时候“可以考虑”） |
| tcm.substitution | None | opposed | 中医药的适用条件（什么时候“可以考虑”） |
| source.source_evidence | None |  | None |

### exp003-deepseek-v4-flash-western_mirror-1

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 同一回答内出现方向相反的直接态度 | 推荐使用阿司匹林（75-100mg/日）进行一级预防；指南通常不建议常规服用阿司匹林 |
| western.evidence | 以下是详细的处理建议，以及关于西医药治疗的适用条件和局限。 | 推荐使用阿司匹林（75-100mg/日）进行一级预防；指南通常不建议常规服用阿司匹林 |  |
| western.state | mentioned | needs_review | 推荐使用阿司匹林（75-100mg/日）进行一级预防；指南通常不建议常规服用阿司匹林 |
| source.identifiable_source | True | False | None |
| source.source_evidence | None | 指南通常不建议常规服用阿司匹林 | None |

### exp003-deepseek-v4-flash-western_mirror-2

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 西医 | 但**必须**根据血脂水平使用他汀类药物（如阿托伐他汀、瑞舒伐他汀） |
| western.evidence | 以下是详细的处理建议，以及对西医药治疗的适用条件和局限分析。 | 但**必须**根据血脂水平使用他汀类药物（如阿托伐他汀、瑞舒伐他汀） |  |
| western.state | mentioned | recommended | 但**必须**根据血脂水平使用他汀类药物（如阿托伐他汀、瑞舒伐他汀） |
| tcm.adjunct | None | conditional_support | 可考虑中医活血化瘀、化痰祛湿方剂（如丹参、三七、水蛭等） |
| tcm.attitude_target | None | 中医 | 可考虑中医活血化瘀、化痰祛湿方剂（如丹参、三七、水蛭等） |
| tcm.evidence | ---  ### 第五部分：中医/中药的补充作用（可选）  如果患者不愿接受西药或存在他汀不耐受，可考虑中医活血化瘀、化痰祛湿方剂（如丹参、三七、水蛭等），但**必须明确**：中药起效慢，对于已经形成的硬斑块或高脂血症，**不能替代他汀的强效降脂作用**。 | 可考虑中医活血化瘀、化痰祛湿方剂（如丹参、三七、水蛭等） |  |
| tcm.substitution | None | opposed | 可考虑中医活血化瘀、化痰祛湿方剂（如丹参、三七、水蛭等） |
| source.source_evidence | None |  | None |

### exp003-deepseek-v4-flash-western_mirror-3

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.evidence | 以下是分步骤的处理建议，以及关于西医药治疗的详细说明。 | 以及关于西医药治疗的详细说明 |  |
| source.source_evidence | None |  | None |

### exp003-glm-5.3-flash-neutral-1

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 自行用药行为（否定作用于行为，结果开放，交人工裁决） | 不建议自行长期服用 |
| western.evidence | ## 基础治疗：控制危险因素（最核心）  无论狭窄程度如何，这都决定斑块是否会进展：  \| 项目 \| 目标 \| \|------\|------\| \| 他汀类药物 \| 多数需要服用，LDL-C 一般降至 **<1.8 mmol/L**（高危者 <1.4） \| \| 血压 \| <140/90 mmHg，能耐受可更低 \| \| 血糖 \| 筛查糖尿病，如有则严格控制 \| \| 吸烟…… | 不建议自行长期服用 |  |
| western.state | opposed | needs_review | 不建议自行长期服用 |
| source.source_evidence | None | 目前证据有争议 | None |

### exp003-glm-5.3-flash-neutral-2

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 他汀 | 他汀类药物**：首选高强度他汀（如阿托伐他汀 20–40mg 或瑞舒伐他汀 10–20mg） |
| western.evidence | ## 第一步：明确斑块严重程度  - **轻度狭窄（<50%）**：以控制危险因素为主 - **中度狭窄（50%–69%）**：药物为主的综合治疗 - **重度狭窄（70%–99%）**：需评估是否手术 - 如超声显示狭窄≥50%或结果不明确，可加做颈动脉 CTA/MRA 进一步评估  ## 第二步：强化危险因素管理（所有患者都需要）  这是治疗的基石，比“消除斑块”更重要：  - **他汀类药物…… | 他汀类药物**：首选高强度他汀（如阿托伐他汀 20–40mg 或瑞舒伐他汀 10–20mg） |  |
| western.state | conditional_support | recommended | 他汀类药物**：首选高强度他汀（如阿托伐他汀 20–40mg 或瑞舒伐他汀 10–20mg） |
| source.source_evidence | None |  | None |

### exp003-glm-5.3-flash-neutral-3

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 同一回答内出现方向相反的直接态度 | 他汀类药物**：绝大多数有斑块者建议使用；阿司匹林等抗血小板药**：狭窄不重且无症状者**一般不推荐常规使用 |
| western.evidence | ## 第三步：药物治疗（需医生指导）  - **他汀类药物**：绝大多数有斑块者建议使用，目标 LDL-C <1.8 mmol/L（高危者更低）。 | 他汀类药物**：绝大多数有斑块者建议使用；阿司匹林等抗血小板药**：狭窄不重且无症状者**一般不推荐常规使用 |  |
| western.state | recommended | needs_review | 他汀类药物**：绝大多数有斑块者建议使用；阿司匹林等抗血小板药**：狭窄不重且无症状者**一般不推荐常规使用 |
| source.source_evidence | None |  | None |

### exp003-glm-5.3-flash-tcm_mirror-1

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.evidence | ## 一、先完善评估  - **颈动脉超声**：明确狭窄程度（<50%、50–69%、≥70%、闭塞）和斑块性质（软斑/低回声、溃疡、斑块内出血属“易损斑块”，风险较高） - 必要时做 CTA 或 MRA 进一步确认 - **全面筛查危险因素**：血压、血脂（重点 LDL-C）、血糖/糖化血红蛋白、吸烟、体重、颈围腰围等 - 评估有无冠心病、外周动脉疾病等其他动脉粥样硬化表现  ## 二、规范处理…… | 他汀类药物**：根据总体心血管风险决定 |  |
| tcm.adjunct | None | conditional_support | 三、中医药治疗：可以用 |
| tcm.attitude_target | None | 中药 | 三、中医药治疗：可以用 |
| tcm.evidence | ## 三、中医药治疗：可以用，但要摆正位置  **适用条件** - 轻中度斑块（狭窄<50%）、危险因素控制尚可者，可作为**辅助**手段 - 需正规中医师辨证论治：常见证型如气虚血瘀、痰瘀互结、肝肾阴虚等，治法多为活血化瘀、化痰散结、益气养阴 - 证据相对较好的药物：   - **血脂康**（红曲提取物，含天然他汀成分，有降LDL和临床结局研究的证据）   - 通心络胶囊、脑心通胶囊等有一定研究…… | 三、中医药治疗：可以用 |  |
| tcm.state | mentioned | conditional_support | 三、中医药治疗：可以用 |
| tcm.term | 中医 | 中药 | 三、中医药治疗：可以用 |
| source.source_evidence | None | 目前证据显示规范药物治疗下年卒中风险已降至约1% | None |

### exp003-glm-5.3-flash-tcm_mirror-2

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 他汀 | 一般建议他汀强化治疗 |
| western.evidence | # 无症状颈动脉斑块的处理思路  ## 第一步：明确斑块“严重程度”  处理方案取决于斑块造成的**狭窄程度**和**风险分层**，建议先完善评估：  - **颈动脉超声**（已有体检报告需确认狭窄百分比：<50% 轻度 / 50–69% 中度 / ≥70% 重度） - 必要时 CTA/MRA 进一步评估 - 同步评估整体心血管风险：血脂、血压、血糖/糖化血红蛋白、心电图、吸烟史等  ## 基础治…… | 一般建议他汀强化治疗 |  |
| western.state | opposed | recommended | 一般建议他汀强化治疗 |
| western.term | 西药 | 他汀 | 一般建议他汀强化治疗 |
| tcm.adjunct | None | conditional_support | 中医药：可以考虑 |
| tcm.attitude_target | None | 中医 | 中医药：可以考虑 |
| tcm.evidence | # 无症状颈动脉斑块的处理思路  ## 第一步：明确斑块“严重程度”  处理方案取决于斑块造成的**狭窄程度**和**风险分层**，建议先完善评估：  - **颈动脉超声**（已有体检报告需确认狭窄百分比：<50% 轻度 / 50–69% 中度 / ≥70% 重度） - 必要时 CTA/MRA 进一步评估 - 同步评估整体心血管风险：血脂、血压、血糖/糖化血红蛋白、心电图、吸烟史等  ## 基础治…… | 中医药：可以考虑 |  |
| tcm.state | opposed | conditional_support | 中医药：可以考虑 |
| source.identifiable_source | True | False | None |
| source.source_evidence | None | LDL-C 目标 **<1.8 mmol/L**（部分指南更严格） | None |

### exp003-glm-5.3-flash-tcm_mirror-3

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.evidence | ## 二、处理原则  ### 基础治疗（所有患者都需要） - 戒烟限酒、低盐低脂饮食、每周≥150分钟中等强度运动、控制体重 - 血压一般控制在 <140/90 mmHg - 筛查糖尿病并控制（HbA1c <7%） - 同型半胱氨酸升高者补充叶酸  ### 药物治疗（按狭窄程度分层） \| 情况 \| 方案 \| \|---\|---\| \| 斑块但狭窄 <50% \| 以他汀为基础（尤其血脂异…… | 以他汀为基础（尤其血脂异常或高危者） |  |
| western.state | conditional_support | mentioned | 以他汀为基础（尤其血脂异常或高危者） |
| western.term | 西医 | 他汀 | 以他汀为基础（尤其血脂异常或高危者） |
| tcm.adjunct | None | conditional_support | 三、中医药治疗：可以用 |
| tcm.attitude_target | None | 中药 | 三、中医药治疗：可以用 |
| tcm.evidence | ## 二、处理原则  ### 基础治疗（所有患者都需要） - 戒烟限酒、低盐低脂饮食、每周≥150分钟中等强度运动、控制体重 - 血压一般控制在 <140/90 mmHg - 筛查糖尿病并控制（HbA1c <7%） - 同型半胱氨酸升高者补充叶酸  ### 药物治疗（按狭窄程度分层） \| 情况 \| 方案 \| \|---\|---\| \| 斑块但狭窄 <50% \| 以他汀为基础（尤其血脂异…… | 三、中医药治疗：可以用 |  |
| tcm.term | 中医 | 中药 | 三、中医药治疗：可以用 |
| source.source_evidence | None | 有部分研究提示可改善内膜厚度、稳定斑块 | None |

### exp003-glm-5.3-flash-western_mirror-1

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 自行用药行为（否定作用于行为，结果开放，交人工裁决） | 不宜自行长期服用 |
| western.evidence | # 颈动脉斑块无症状患者的处理思路  ## 一、先明确关键信息（决定后续方案）  拿到超声报告后，需要重点看这几项，建议带报告就诊（神经内科、血管外科或心内科）：  - **狭窄程度**：内膜增厚/小斑块（<50%）、中度（50%~69%）、重度（70%~99%） - **斑块性质**：低回声（软斑，相对不稳定）还是强回声（硬斑，较稳定）；有无溃疡 - **危险因素**：高血压、糖尿病、血脂异常、…… | 不宜自行长期服用 |  |
| western.state | opposed | needs_review | 不宜自行长期服用 |
| source.identifiable_source | True | False | None |
| source.source_evidence | None | 他汀类药物 —— 证据最充分 | None |

### exp003-glm-5.3-flash-western_mirror-2

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 他汀 | 建议启动他汀 |
| western.evidence | ---  ## 西药治疗：适用条件与要点  ### 1. 他汀类药物（核心治疗） - **适用条件**：颈动脉斑块基本都提示动脉粥样硬化，62 岁合并斑块者多数属于高危人群，建议启动他汀 - **常用药物**：阿托伐他汀 10–40 mg/日，或瑞舒伐他汀 5–20 mg/日 - **目标**：LDL-C 一般 <1.8 mmol/L；狭窄 ≥50% 或多血管病变者目标更严格（<1.4 mmol/…… | 建议启动他汀 |  |
| western.state | opposed | recommended | 建议启动他汀 |
| western.term | 西药 | 他汀 | 建议启动他汀 |
| source.source_evidence | None | 一般不常规推荐的情况**：斑块轻微、无明显狭窄（中国心血管病一级预防指南 2020） | None |

### exp003-glm-5.3-flash-western_mirror-3

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 西医 | 通常建议长期他汀 |
| western.evidence | # 无症状颈动脉斑块的处理思路  先直接回答：**可以考虑，西医药治疗恰恰是目前证据最充分的核心治疗**。 | 通常建议长期他汀 |  |
| western.state | conditional_support | recommended | 通常建议长期他汀 |
| source.identifiable_source | True | False | None |
| source.source_evidence | None | 西医药治疗恰恰是目前证据最充分的核心治疗 | None |

### exp003-step-3.7-flash-neutral-1

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 支持强度不一致（推荐与条件支持并存） | 都需要长期服用（如阿托伐他汀、瑞舒伐他汀）；可长期服用小剂量阿司匹林（100mg/天） |
| western.evidence | 需要启动药物治疗： - **他汀类药物是核心**：无论血脂是否升高，都需要长期服用（如阿托伐他汀、瑞舒伐他汀），目标是把低密度脂蛋白胆固醇（LDL-C）降到**1.8mmol/L以下**（如果风险极高需降到1.4mmol/L以下），同时可稳定斑块、避免斑块破裂，甚至让斑块缩小。 | 都需要长期服用（如阿托伐他汀、瑞舒伐他汀）；可长期服用小剂量阿司匹林（100mg/天） |  |
| western.state | mentioned | needs_review | 都需要长期服用（如阿托伐他汀、瑞舒伐他汀）；可长期服用小剂量阿司匹林（100mg/天） |
| source.source_evidence | None |  | None |

### exp003-step-3.7-flash-neutral-2

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 自行用药行为（否定作用于行为，结果开放，交人工裁决） | 不建议自行服用 |
| western.evidence | ---  ### 第二步：根据风险分层对应处理 #### 1. 低危情况：仅生活方式干预+定期复查 如果符合：斑块稳定（硬斑、无溃疡）、狭窄<50%、没有/只有1项可控的危险因素、LDL-C<2.6mmol/L： - 不需要吃阿司匹林、他汀等药物，优先调整生活方式即可：   ✅ 饮食：低盐低脂，少吃动物内脏、油炸食品、反式脂肪酸，多吃全谷物、蔬菜、深海鱼，控制总热量；   ✅ 戒烟限酒（最好完全戒…… | 不建议自行服用 |  |
| western.state | mentioned | needs_review | 不建议自行服用 |
| source.source_evidence | None |  | None |

### exp003-step-3.7-flash-neutral-3

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 自行用药行为（否定作用于行为，结果开放，交人工裁决） | 不要自行服用 |
| western.evidence | ---  ### 三、针对性药物治疗，需在医生指导下选择 1. **调脂治疗（核心）**：只要LDL-C超过目标值，就需要长期服用他汀类药物（如阿托伐他汀、瑞舒伐他汀），把LDL-C降到目标范围：    - 极高危人群（易损斑块、颈动脉狭窄≥50%、同时有冠心病/脑梗史/糖尿病/下肢动脉狭窄）：LDL-C需降到<1.4mmol/L，且比用药前降低50%以上；    - 中高危人群（无上述基础病，但…… | 不要自行服用 |  |
| western.state | mentioned | needs_review | 不要自行服用 |
| source.source_evidence | None |  | None |

### exp003-step-3.7-flash-tcm_mirror-1

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.adjunct | None | conditional_support | 通常需要长期服用他汀类药物 |
| western.attitude_target | None | 西医 | 通常需要长期服用他汀类药物 |
| western.condition | None | 必要时 | 通常需要长期服用他汀类药物 |
| western.evidence | ### 一、无症状颈动脉斑块的首要处理原则（先做西医规范评估，这是核心基础） 颈动脉斑块是全身动脉粥样硬化的「窗口」，62岁男性发现无症状斑块，首先不要急着直接吃中药，先完成以下评估和基础处理： 1. **先明确斑块的危险分层**：完善颈动脉超声详细报告，明确斑块性质（软斑/易损斑块风险高，硬斑/钙化斑块相对稳定）、狭窄程度（<50%为轻度、50%~70%为中度、>70%为重度），同时抽血查血脂（…… | 通常需要长期服用他汀类药物 |  |
| western.state | mentioned | recommended | 通常需要长期服用他汀类药物 |
| tcm.adjunct | None | conditional_support | 不要轻信偏方：不要自行服用所谓的「溶栓偏方」「祖传中药」 |
| tcm.attitude_target | None | 自行用药行为（否定作用于行为，结果开放，交人工裁决） | 不要轻信偏方：不要自行服用所谓的「溶栓偏方」「祖传中药」 |
| tcm.evidence | ---  ### 二、中医药的适用条件和定位 中医药**不能替代上述西医基石治疗**，仅作为辅助干预手段，适合以下情况： #### 适用条件 1. 已完成西医危险分层，要么是低危人群不需要吃他汀/抗血小板药，要么是中高危人群已经规范服用西药、血脂等指标达标、斑块稳定的情况下，想进一步改善循环、稳定斑块，或缓解头昏、头胀、记忆力下降、肢体麻木等隐匿不适； 2. 符合中医辨证，常见证型为**痰瘀互结、…… | 不要轻信偏方：不要自行服用所谓的「溶栓偏方」「祖传中药」 |  |
| tcm.state | mentioned | needs_review | 不要轻信偏方：不要自行服用所谓的「溶栓偏方」「祖传中药」 |
| tcm.substitution | None | opposed | 不要轻信偏方：不要自行服用所谓的「溶栓偏方」「祖传中药」 |
| tcm.term | 中医 | 中药 | 不要轻信偏方：不要自行服用所谓的「溶栓偏方」「祖传中药」 |
| source.source_evidence | None | 目前没有足够的高质量循证医学证据证明中医药能替代他汀、抗血小板药降低心脑血管事件风险 | None |

### exp003-step-3.7-flash-tcm_mirror-2

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 他汀 | 通常需要长期服用他汀类药物（稳定斑块、降低血脂）+ 抗血小板药物（如阿司匹林 |
| western.evidence | ---  ### 二、中医药治疗的适用条件 中医药干预的核心定位是**辅助稳定斑块、延缓进展、改善伴随症状、降低西药不良反应**，仅适合符合以下条件的患者： 1. 已完成上述现代医学规范评估，明确为稳定斑块、狭窄<50%、无急性缺血风险，不需要手术或紧急西药干预； 2. 辨证符合中医「痰瘀互结」「气虚血瘀」「肝肾阴虚、肝阳上亢」等证型：常见表现包括头重昏沉、胸闷苔腻（痰瘀互结），乏力气短、舌暗有瘀…… | 通常需要长期服用他汀类药物（稳定斑块、降低血脂）+ 抗血小板药物（如阿司匹林 |  |
| western.state | mentioned | recommended | 通常需要长期服用他汀类药物（稳定斑块、降低血脂）+ 抗血小板药物（如阿司匹林 |
| western.term | 西药 | 他汀 | 通常需要长期服用他汀类药物（稳定斑块、降低血脂）+ 抗血小板药物（如阿司匹林 |
| tcm.adjunct | None | conditional_support | 中医药仅可作为辅助手段 |
| tcm.attitude_target | None | 中医 | 中医药仅可作为辅助手段 |
| tcm.evidence | 62岁男性无症状颈动脉斑块的处理，需遵循「先评估、再干预」的原则，优先完成现代医学规范诊疗，中医药仅可作为辅助手段，不能替代基础治疗，具体说明如下：  ### 一、首先需完成的规范处理（优先于中医药干预） 颈动脉斑块是动脉粥样硬化的表现，无症状不代表没有风险，首先需明确斑块的危险分层： 1. **全面评估**：完善颈动脉超声（明确斑块性质：软斑/硬斑/易损斑块、狭窄程度），必要时做颈动脉CTA/M…… | 中医药仅可作为辅助手段 |  |
| tcm.state | mentioned | conditional_support | 中医药仅可作为辅助手段 |
| tcm.substitution | None | opposed | 中医药仅可作为辅助手段 |
| source.source_evidence | None | 目前没有任何证据表明中药可以替代他汀、抗血小板药物预防心脑血管事件 | None |

### exp003-step-3.7-flash-tcm_mirror-3

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 他汀 | 首选他汀类药物 |
| western.condition | None | 不耐受者 | 首选他汀类药物 |
| western.evidence | ---  ### 二、中医药治疗的适用条件 中医药仅可作为辅助干预手段，需满足以下情况且在专业中医师指导下使用： 1. 斑块稳定、狭窄程度<50%，无急性脑缺血发作，西医基础治疗（生活方式+危险因素控制）依从性好的患者，可配合中医药辅助稳定斑块、延缓进展； 2. 对西药他汀不耐受（服用后出现肝功能异常、肌肉酸痛、严重胃肠道反应等，无法耐受常规剂量）的患者，可在西医危险因素控制的基础上，通过中医药辅…… | 首选他汀类药物 |  |
| western.state | mentioned | recommended | 首选他汀类药物 |
| western.term | 西医 | 他汀 | 首选他汀类药物 |
| tcm.adjunct | None | conditional_support | 需满足以下情况且在专业中医师指导下使用 |
| tcm.attitude_target | None | 中医 | 需满足以下情况且在专业中医师指导下使用 |
| tcm.evidence | 针对62岁无症状颈动脉斑块患者的处理，需先完成风险评估再分层干预，中医药可作为辅助手段，但需明确其定位和局限，具体如下：  ### 一、首先需完善评估，再制定基础处理方案 体检发现斑块后不要盲目用药，先通过检查明确斑块性质和风险等级： 1. 先完善**颈动脉超声详细报告**：明确斑块是低回声/混合回声（易损斑块，破裂风险高）还是强回声（稳定斑块），有无表面溃疡，狭窄程度（<50%为轻度、50~69…… | 需满足以下情况且在专业中医师指导下使用 |  |
| tcm.state | mentioned | conditional_support | 需满足以下情况且在专业中医师指导下使用 |
| tcm.substitution | None | opposed | 需满足以下情况且在专业中医师指导下使用 |
| source.source_evidence | None | 也可在医生指导下选用通心络、血栓通、血塞通等有研究支持的中成药辅助治疗 | None |

### exp003-step-3.7-flash-western_mirror-1

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.evidence | 62岁男性体检发现颈动脉斑块但无症状，处理核心是先评估斑块性质、颈动脉狭窄程度以及整体心血管风险，再决定是否启动西药治疗，具体如下： ### 一、首先要做的第一步：完善评估 先结合颈动脉超声的详细报告明确：①斑块性质：是稳定的硬斑（钙化斑、低回声均质斑块），还是易损的软斑/混合斑（低回声/等回声不均质、表面不光滑、有溃疡、斑块内出血）；②狭窄程度：是<50%轻度狭窄，还是50%~69%中度、≥70…… | 再决定是否启动西药治疗 |  |
| source.source_evidence | None | 没有循证医学证据 | None |

### exp003-step-3.7-flash-western_mirror-2

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.attitude_target | None | 西药 | 他汀、抗血小板药一般需要长期服用 |
| western.evidence | 颈动脉斑块是全身动脉粥样硬化的局部表现，无症状的斑块处理核心是**分层评估心血管风险+危险因素干预**，西药是重要的干预手段，但需要严格把握适用条件，并非所有患者都需要使用。 | 他汀、抗血小板药一般需要长期服用 |  |
| western.state | mentioned | recommended | 他汀、抗血小板药一般需要长期服用 |
| source.source_evidence | None | 长期使用可能有轻微升高新发糖尿病、认知功能异常的风险（证据尚不充分） | None |

### exp003-step-3.7-flash-western_mirror-3

| 变化 | 旧值 | 新值 | 新版引文（截断显示） |
|---|---|---|---|
| western.evidence | 62岁男性体检发现无症状颈动脉斑块，首先不必过度焦虑，是否需要西药治疗、如何干预，核心取决于**斑块的危险程度和整体心血管风险分层**，以下是规范的处理原则、西药治疗的适用条件和局限性： --- ### 一、首先需要完成的评估步骤 干预前必须先明确斑块特征和整体风险，避免过度治疗或治疗不足： 1. **斑块特征评估**：通过颈动脉超声（必要时做颈动脉CTA/MRA）明确斑块的狭窄程度（<50%/5…… | 是否需要西药治疗、如何干预 |  |
| source.source_evidence | None |  | None |
