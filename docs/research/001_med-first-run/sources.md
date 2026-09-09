# 两类来源 · 在50元预算内如何确定首轮MedMirror实验协议、官方API接入与评分方案

> 2026-09-09。按**谁积累的**分尽：自己积累的、别人积累的。
> **两类进来都问同一句：它今天还算数吗？**
>
> ⚠️ 「都没有所以自己跑」不在这里——**那不是来源，是做法**，见 `gap.md` 的「它们没做的」。
>
> ⚠️ 下面的市场与站点**会变**，用前核一眼；名字对不上就搜同类。**方法不变，名单会老。**

---

## 一、自有积累 —— 可照搬，先确认权利与时效

自家旧项目、老代码、团队规约、你自己写过的东西。

### 怎么查

**先跑一把**：`bash skills/aias-meta-research/scripts/scan-own.sh "<关键词>"`
——一次扫完本机项目、提交历史、过往对话记录，按最后改动时间排。

| 去哪 | 怎么翻 |
|---|---|
| **过去的项目目录** | 直接看。做过类似的事没有？哪一版跑通过？ |
| **自己的提交历史** | `git log --oneline --all` · `git log --author=<你>` ——**代码记做成什么样，提交记当时为什么这么定** |
| **过往对话记录** | 记忆和现实对不上时，去翻当时的讨论——**文档说 A、代码做了 B、你记得是 C，谁都别直接信** |
| **团队的仓库与规约** | 别人踩过的坑，规约里往往留着痕迹 |
| **自己写过的文档** | 笔记、总结、发过的文章 |

### 登记

| 是什么 | 在哪 | 还算数吗 | 判据 |
|---|---|---|---|
| | `resources/…` | 算 / 不算了 | 例：生产环境跑通过 ／ 规约可能过时 |
| 当前项目实验标准 | `../specs/calibration.md` | 算 | 用户已确认的研究问题、预算、报告和追问边界 |
| 课程原型实操 | `/Users/qrq/AI/code/01-learning/Auto-kaizhi/我的产出/ch03（下）-作业2-系统原型实操.md` | 算 | 亲自定标、正反例、机器规则与人工判据分工 |
| 项目意向与现实约束 | `../../.42cog/intent.md`、`../../.42cog/real.md` | 算 | 当前方向、预算、时间和资源限制 |

⚠️ **不自动可信**。同是自家的东西，判决可能相反：
「这个规约可能过时了，可以参考，但不能完全从它出发」vs「这个我反复测试过、生产跑通了，尽量复用」。

⚠️ **你三个月前写的东西，和陌生人写的东西，享受同一套审查。区别只在于——你有权照搬它。**

---

## 二、他人积累 —— 只读借鉴，先查协议

### 查四类，用同一套方法

**换对象，方法不变**——都是同一个决策点、同一套派活四件事（见 `assign.md`）。

| 查什么 | 查什么问题 | 去哪查 |
|---|---|---|
| **技能生态** | 这件事有没有人做成过技能？ | 各家插件市场与技能仓库；搜 `awesome-<你的领域>` 一类的清单仓 |
| **命令行工具** | 有哪些硬工具，用哪个？ | 三大分发市场：**Homebrew**（Mac）· **npm**（JS，四百万包）· **PyPI**（Python，八十多万项目）。Windows 看 **Scoop** / **winget** |
| **模型** | 这个活该用哪个模型？ | 公开评测榜单与各家技术报告。**要多模态、要长上下文，就得专门看那一栏** |
| **别人的项目** | 源码 · 提交历史 · 放弃过什么 | 代码托管平台（GitHub / GitLab / 国内平台）。**浅克隆到参考区再读**，别在网页上翻 |

**取材**：`bash skills/aias-meta-research/scripts/clone.sh <url>`（要挖提交历史加 `-d 200`）

### 查模型这一栏，多问三句

榜单也是他人积累，**同样要判时效、判来路**：

- **谁做的榜**？做榜的人和被测的模型有没有利害关系？
- **什么时候的**？半年前的榜单在这个行当里基本等于过期。
- **测的是不是你要的那件事**？综合分高，不代表你这一类任务上强。

**最后一句最要紧**：能自己拿三五个真实任务试一遍，胜过读十份榜单。

### 登记

| 是什么 | 在哪 | 协议 | 角色 | 读多深 | 还活着吗 |
|---|---|---|---|---|---|
| | `resources/…` | MIT / Apache / GPL… | 要比的 / 要学的 / 零件 | 逐条核查 / 只读架构 / 一两行 | 最近提交时间 |
| DeepSeek 官方 API 文档 | `https://api-docs.deepseek.com/quick_start/pricing/`、`https://api-docs.deepseek.com/guides/thinking_mode/` | 官方文档 | 接入、思考参数与价格核查 | 逐条核查 | 2026-09-09；型号、base URL、thinking 开关已核实，费率执行前重核 |
| StepFun 官方 API 文档 | `https://platform.stepfun.com/docs/zh/api-reference/chat/chat-completion-create`、`https://platform.stepfun.com/docs/zh/step-plan/integrations/reasoning-api`、`https://platform.stepfun.com/docs/zh/guides/pricing/details`、用户提供的 `https://api.stepfun.com/step_plan/v1` | 官方文档 + 用户配置 | 接入、推理参数与价格核查 | 逐条核查 | 2026-09-09；Step Plan Base URL 与接口路径已核实；官方价目表明确列出 `step-3.5-flash`，`step-3.7-flash` 具体计费仍待账户侧核对 |
| GLM/Z.ai 官方 API 文档 | `https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode`、`https://docs.bigmodel.cn/api-reference/模型-api/对话补全` | 官方文档 | 接入与思考参数核查 | 逐条核查 | 2026-09-09；endpoint 与实际请求已打通，当前模型可用但价格和关闭思考参数仍待账户侧核对 |
| MedPerturb / HealthBench / PatientAgentBench | 待补源码与官方资料 | 各自协议待核 | 只学 trial、trace、grader 和复核方法 | 只读架构 | 尚未本地取材 |
| HealthRex/PhysicianBench | `resources/PhysicianBench`；`https://github.com/HealthRex/PhysicianBench` | Apache-2.0；commit `c7efa8f` | 要学：任务、长程轨迹、resume、pass@k | 读 README 与目录，不引入 EHR | 2026-09-09；浅克隆完成 |
| CAS-SIAT-XinHai/RxSafeBench | `resources/RxSafeBench`；`https://github.com/CAS-SIAT-XinHai/RxSafeBench` | CC0-1.0；commit `a25f9a1` | 要学：药物风险、交互与禁忌的测试维度 | 读数据结构与指标，不把其医学标签当本项目真相 | 2026-09-09；浅克隆完成 |
| ZhilingYan/LiveMedBench | `https://github.com/ZhilingYan/LiveMedBench` | MIT | 要学：案例级 rubric、正负分、人工 QA | 读 rubric 与评估目录，不引入大规模数据 | 2026-09-09；尚未克隆 |
| heqiu12345/tracelens | `resources/tracelens`；`https://github.com/heqiu12345/tracelens` | MIT；commit `302d874` | 要学：trace 浏览、人工/LLM judge 对照、κ 和混淆矩阵 | 只借鉴复核数据结构，首版不引入 Langfuse | 2026-09-09；浅克隆完成 |
| harness/harness-evals | `https://github.com/harness/harness-evals` | 许可证与版本待核 | 要学：JSONL 数据、baseline、成本/重试字段与多类 grader | 只参考字段和 CLI 组织，不引入整套依赖 | 2026-09-09；README 明确有 baseline、token/cost/retry 与 trace 字段 |

⚠️ **读懂 → 自己写，绝不复制粘贴。** GPL / AGPL 只参考不链接。
⚠️ **协议不只回答「能不能用」，还决定「能读到哪一步」。**

---

## 两类都不算数时

那不是失败，那是**下一步的入口**：确认了没有，才该去跑实验。
接着填 `gap.md` 的「它们没做的」——**「压根没有」是查完之后的结果，不是时间判断。**

## 最后

**读，是复用别人的；跑，是长出你自己的。** 这一份只管前半——材料从哪来；
后半在 `gap.md` 与 `decision.md`。
