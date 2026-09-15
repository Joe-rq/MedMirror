# 接手开发 · 一页说明

> 给第二位开发者（以及他/她的 AI agent）。目标：clone 下来半小时内跑通四闸，并清楚每个改动该走哪条路。
> 流程与仓库主人完全一致——**同一套闸门、同一条 issue → PR 路线、同一套全局技能**。

## 当前接手任务（2026-09-09 审计更新）

先读 [原型纠偏与双人交接计划](../plan/002_prototype-calibration-handoff.md)。首个单元是离线分组报告修复；人工定标与运行护栏就绪后才进入自动追问。27 条原始回答已经随 Git 提供，其中 3 条截断；不要把旧的 27/27 success 理解为完整回答。以下远程权限与工具说明是历史交接记录，实际 Issue 与权限在接手时核对。

## 开发队列：按阶段与依赖，不按 Issue 编号

> **时效声明（2026-09-13）**：下表为 2026-09-09 建队时的阶段快照（#10/#12/#3/#13/#2/#4/#11 等已在此后完成）。当前开放项以仓库 [README](../../README.md) 的「开放队列」与 `state/board.md` 为准：#5 复核人员与材料发送、#55/#52 技术报告定稿发布。

| 阶段 | 项目主人 | 伙伴 | 推进条件 |
|---|---|---|---|
| 阶段1 | [#11 人工定标](https://cnb.cool/joe-rq/MedMirror/-/issues/11)、[#5 复核人员](https://cnb.cool/joe-rq/MedMirror/-/issues/5) | [#10 报告修复](https://cnb.cool/joe-rq/MedMirror/-/issues/10) | 可立即认领，定标和报告协同完成 |
| 阶段2 | 确认评分标准，核对 #3 账单 | [#12 提取修复](https://cnb.cool/joe-rq/MedMirror/-/issues/12)、[#3 预算闸门](https://cnb.cool/joe-rq/MedMirror/-/issues/3)、[#13 运行保护](https://cnb.cool/joe-rq/MedMirror/-/issues/13) | #12 正式验收依赖 #11；#3 与 #13 共用调用/账本契约 |
| 阶段3 | 审核发现、推进实际医学复核 | [#2 有界追问](https://cnb.cool/joe-rq/MedMirror/-/issues/2)、[#4 备份恢复演练](https://cnb.cool/joe-rq/MedMirror/-/issues/4) | #2 真实调用前完成 #10/#11/#12/#3/#13；#4 在回放接口和目录就绪后可提前 |
| 后置 | 按余力与预算安排 | [#6 技能评审](https://cnb.cool/joe-rq/MedMirror/-/issues/6) | 不阻塞报告、定标和运行保护 |

阶段表示主要推进顺序，具体依赖以 Issue 正文为准，不要求同阶段所有任务都关闭才启动独立工作。每人一次认领一个开发单元；表中是建议分工，账号负责人由团队认领。#5 是人员和排期安排，其关闭不代表医学复核已经完成。

远程 Issue 标题已添加阶段前缀，编号保持稳定。#1 已完成，无需重新认领。

## 0. 权限（历史记录）

- 仓库私有，你是 **Developer**：能推分支、能开 PR。
- `main` 已设分支保护：**禁止直推 + 必须通过状态检查**。直推会被远端直接拒绝，这不是故障。

## 1. 环境（四条命令）

```bash
git clone https://cnb.cool/joe-rq/MedMirror.git
cd MedMirror
brew install uv                              # 或 curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync                                      # 自动装 Python 3.13 与 pytest/ruff
# 离线开发无需 key；仅在线调用时准备 .env.local
# 已有 .env.local 时不要覆盖
cp -n .env.example .env.local                 # key 只放本机，不提交、不打印
```

`uv.lock` 已锁死依赖版本，`uv sync` 得到的环境与 CI 一致，不需要手动建虚拟环境。

## 2. 验收环境 = 本地跑一遍 CI 的四闸

```bash
uv run ruff format --check .             # 122 files already formatted
uv run ruff check .                      # All checks passed!
uv run pytest                            # 280 passed
uv run python scripts/check-manifests.py # ✓ 全绿（校验 2 份清单）
uv run python scripts/check_docs.py      # ✓ 文档卫生（合并冲突标记 / 仓内引用）
uv run python scripts/check_en_docs.py   # ✓ 中英文档一致（声明 / 字段表 / 互链 / 测试数）
```

四条全绿说明你的环境和 CI 同源；后两条是同一 CI 另跑的两道文档卫生闸——**改文档时必跑**（2026-09-15 起英文闸进 CI）。闸门定义在 `.cnb.yml`，push `main` 与提交 PR 时都会触发。

## 3. 开工前先读（项目自己的开工协议）

按顺序读这几份，别跳：

1. `AGENTS.md` —— 跨工具开工入口（Codex / Cursor 等也读它）
2. `CLAUDE.md` —— 工作规约：授权边界、目录六组、评测护栏、调用与预算
3. `.42cog/` 四份 —— `intent`（方向，冲突时以它为准）· `real`（约束）· `cog`（认知模型）· `meta`（项目身份）
4. `specs/calibration.md` —— 报告标准与实验协议（正本）
5. `state/board.md` —— 这一轮干到哪了、下一步是什么
6. `state/memory/MEMORY.md` —— 已踩过的教训

## 4. 开发流程（与仓库主人一致）

每个改动都走这条线，没有例外：

```
issue（自己写）→ 分支 → PR → CI 全绿（四闸 + 两道文档卫生闸）→ 人工合并 → 关 issue
```

**开工第一步：读 issue。** 需求以 issue 为准，不凭记忆、不凭聊天记录：

```bash
cnb issues list-issues --repo joe-rq/MedMirror --state open    # 列出待办
cnb issues get <编号>                                          # 读完整要求与验收标准
```

认领一条再动手；同时只保留一个活跃的 issue 和分支，做完再开下一条。

- **issue 必须自己写，不假手 AI。** 意图经另一个 AI 转写，只会引入污染。四要素缺一条，AI 就会自己猜一条：
  1. 指向计划文件（不重述需求）
  2. 写明架构决策与真相源在哪（注明「不要重新调研」）
  3. 写明产物落点目录
  4. **写清「怎么算做完」**——这是你唯一一次能在动手之前定标准的机会
- **分支**：一个 issue 一条分支，例如 `feat/issue-12-followup-loop`。
- **PR**：目标 `main`，描述里把「怎么算做完」逐条勾选。
- **CI**：四闸红了先修，不红不谈合并。
- **合并**：人工点，不自动合并；合并后切回 `main`、删掉已合并分支。
- **发车**：复杂 issue 用 `/dev-launch`（九步：状态校验 → 调研定位 → 按确定性分流 → 细化 → 实现 → 验证 → 评审 → 双谱系评审 → 交付）。
- **三层验证**：规则层（脚本，机器判）→ 判据层（AI 按写下的判据判）→ 实效层（**人判，AI 不能替代**）。

## 5. 流程依赖的工具链（仓库里没有，需要自己装）

| 类别 | 需要什么 | 从哪来 |
|---|---|---|
| 运行时 | uv（含 Python 3.13） | brew 或官方脚本 |
| 四闸 | ruff、pytest | `uv sync` 自动装，已锁版本 |
| 全局技能 | `dev-launch` · `dev-req` · `pr-ready` · `aias-meta-init` / `-research` / `-proto` / `-evolve` | 训练营 / 42plugin，装在 `~/.claude/skills/` |
| 第二谱系评审 | `codex`（配 GPT 系）· `opencode`（配 GLM 系） | 见 `scripts/check-tools.sh` |

自查两条：

```bash
ls ~/.claude/skills | grep -E 'dev-launch|dev-req|pr-ready|aias-meta'   # 缺哪个装哪个
bash scripts/check-tools.sh                                             # 通用工具清单
```

**这一项最容易漏**：仓库 `skills/` 下只有四个 10 行骨架（med-init / med-research / med-proto / med-evolve），发车、需求细化、双谱系评审靠的是上面那批全局技能。没有它们，你能跑闸、能提 PR，但走不出和仓库主人一样的自主开发流程。

## 6. clone 下来会缺什么

| 缺什么 | 为什么 | 怎么办 |
|---|---|---|
| `resources/` | 只剩 `README.md`——三个浅克隆参考仓库（PhysicianBench 等）被 gitignore | 要读就自己再 clone |
| `runs/` | 运行档案目录，2026-09-13 起已入 Git（issue #4：远程仓库即备份落点，克隆即可取回；密钥类文件仍被 .env 规则排除） | 无需另行准备；本地双保险用 `scripts/backup_data.py` |
| `.env.local` | 密钥永不入库 | 从 `.env.example` 复制后自己填 |

> 已实测：干净 clone 后 `uv sync` + 四闸与两道文档卫生闸全部通过，无需额外步骤。

## 7. 边界（越线要担责）

- 密钥只放 `.env.local`：不读出、不打印、不写进报告、不进版本库。
- **付费 API 调用、修改协议或评分标准、对外发布** → 先找仓库主人拍板。
- `vault/raw/`、`notes/` 只读，不改不代提交；`resources/` 读懂后自己写，绝不 copy-paste。
- 未提及 ≠ 反对；提示敏感 ≠ Bias；小样本不得包装成稳定医学结论。

## 8. 两件待定的团队约定

- **谁的 API key、谁批预算**：总额 50 元，口径（是否含开发工具费用）尚未确认。
- **合并由谁点**：分支保护规则里 `allow_master_manual_merge: false` 这一项语义不直观。建议先让第二人开一个测试 PR 实测能否自行合并；点不了再调整规则。
