# specs/review · 医学复核材料包

issue #20 交付物：为 #5 的医学复核人准备的可独立判断材料包。复核人看模型**完整回答原文**，不经提取器或报告转述；研究方判定后置。**本材料包不代替专业复核，也不预设任何 Bias 结论。**

## 文件构成

| 文件 | 内容 | 何时用 |
|---|---|---|
| `background.md` | 一页背景：研究问题、协议、复核目的、合成病例声明 | 复核开始前必读 |
| `case-card.md` | 病例卡：场景原文（合成）与三种问法 | 复核开始前必读 |
| `attachments/` | 27 条模型回答完整原文（9 个分组文件 + `index.md` 索引） | 全程对照 |
| `form-open.md` | **第一层**：逐条开放式复核表（27 条，每条意见栏 + 可跳过） | 先做，交回后再发第二层 |
| `form-candidates.md` | **第二层**：候选核对表（候选主张 + 原文定位 + 支持/反证栏）与候选池 DRAFT | 第一层意见收回后 |
| `boundaries.md` | 边界声明：来源三态、指南引用不作已验证事实 | 复核前后均须知 |
| `record.md` | 复核记录表：复核人、日期、逐条状态、分歧处理 | 全程登记 |

## 两层复核流程（判定后置）

流程的完整说明以 `background.md`（复核人侧权威入口）为准：第一层开放式逐条意见先交回，第二层候选核对后发——顺序颠倒会把独立复核变成给已有结论背书。

## 复核范围

- 本包默认列出全部条目（截断处理口径见 `boundaries.md`；最新计数以 `attachments/index.md` 为准）。**不要求全量复核**：实际复核范围（哪些条目、哪些候选）由项目主人在发出材料时圈定并记录于 `record.md`。
- 必核子集（8–12 个具体问题）从 `form-candidates.md` 候选池中由主人挑选定稿；候选池当前为 DRAFT，分布备注已于 2026-09-12 对照 27 条原文逐条复核刷新（交叉参考 offline-rules-v2 提取结果，语义未定标），待主人挑选定稿。

## 边界与安全

- 病例为**合成**，非真实患者；复核意见用于**研究边界判定**，不用于任何患者的诊疗。
- 模型回答是被测对象，不是医学真相；见 `boundaries.md`。
- 本目录不含任何密钥、真实患者信息；`attachments/` 由 `scripts/gen_review_attachments.py` 从 Git 跟踪的 trials.jsonl 生成，勿手改。

## 分发给复核人（Word 形态）

md 是真相源与机器校验载体；发给复核人的 docx 由 `scripts/export_review_pack.py`（pandoc）派生，**不入库**（`export/` 已 gitignore），md 改动后重导出。前置依赖：`brew install pandoc`。

| 批次 | 命令 | 内容 | 发送时点 |
|---|---|---|---|
| 第一批（开放式） | `uv run python scripts/export_review_pack.py --layer open` | background、case-card、boundaries、form-open + attachments 全部（文件集随材料目录派生） | 立即；**绝不与候选内容同发**（脚本机械保证） |
| 第二批（候选核对） | `uv run python scripts/export_review_pack.py --layer candidates` | form-candidates | 第一层意见交回**且**必核子集定稿后（DRAFT 状态脚本拒绝导出，预览加 `--allow-draft`） |

复核人交回填好的 docx 后，意见**原话粘贴**进 `record.md`（不改写、不做医学加工）。导出的 docx 头部已自动附 Word 使用说明（填写方式、智能引号风险提示）。

## 机器检测

```bash
uv run python scripts/check_review_pack.py   # 结构、trial 全集、原文逐字包含、第一层无判定词、引文子串
uv run python scripts/gen_review_attachments.py  # 重新生成 attachments/（幂等，字节一致）
```

脚本通过只证明结构与原文自洽，**不证明候选问题措辞恰当**——那属于主人的研究判断（issue #20 约定）。
