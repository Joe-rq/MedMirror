# 病例声明式配置（CaseSpec）

一份 CaseSpec 描述一个病例的全部协议事实：病例文本、提示变体、trial_id 前缀、
提取词表与版本钉子。自带病例接入 = 在本目录填一份 `<case_id>.json`，不改代码。

- 加载与校验：`src/medmirror/casespec.py`（`load_case_spec`）
- 来源：issue #50（plan/003 步骤 2.2 前半）；默认病例 `carotid_plaque_001.json`
  经 `tests/test_casespec_replay.py` 证明与 exp003 历史 27 条请求零语义漂移。

## 字段说明

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `case_id` | str | 非空 | 病例唯一标识；文件名须为 `<case_id>.json` |
| `protocol_version` | str | 非空 | 协议版本钉子（写入 plan 与物化视图，供审计） |
| `trial_prefix` | str | `^[a-z0-9][a-z0-9_-]*$` | trial_id 前缀（`<prefix>-<模型>-<变体>-<序号>`） |
| `case_text` | str | 非空 | 病例主诉文本（基线提问正文） |
| `variants` | {name: str} | 非空对象，名称与提示均非空 | 提示变体：变体名 → 完整提示文本 |
| `extraction.extractor_version` | str | 须等于当前代码支持的提取器版本 | 词表与提取器语义绑定；不匹配拒绝加载 |
| `extraction.paths` | {path: [term]} | 非空对象，词表非空列表且词项非空 | 路径词表：路径名 → 触发词列表 |
| `notes` | str | 非空，且须含「合成/非真实/synthetic」之一 | 病例声明（合成声明是硬校验——真实患者数据不入实验） |

Schema 封闭：未知顶层键与 `extraction` 内未知键一律拒绝。加字段 = schema 变更，
须显式评审，不默吞。

## 协议红线（不可绕过）

- **同病例改词表或变体 = 新 extractor/protocol 版本号**，不回改历史产物
  （`.42cog/` 与 `specs/calibration.md` 的尺子纪律）。
- CaseSpec 钉的 `extractor_version` 与 `src/medmirror/protocol.py` 支持版本不一致时
  **拒绝加载**（报错含两版本具体值）；版本字符串单源在 `protocol.EXTRACTOR_VERSION`。
- 合成病例声明必须如实：真实患者数据不入实验（intent.md 红线）。

## 新病例接入路径（当前边界）

1. 复制 `carotid_plaque_001.json` 为 `<case_id>.json`，逐字段改写；
2. 冒烟校验（加载即全量校验）：

   ```bash
   uv run python -c "
   from pathlib import Path
   from medmirror.casespec import load_case_spec
   from medmirror.protocol import EXTRACTOR_VERSION
   spec = load_case_spec(Path('configs/cases/<case_id>.json'),
                         supported_extractor_version=EXTRACTOR_VERSION)
   print(spec.case_id, spec.trial_prefix, list(spec.variants), list(spec.paths))
   "
   ```

3. 库级使用（词表与病例全链路穿参）：

   ```python
   from medmirror.casespec import load_case_spec
   from medmirror.protocol import EXTRACTOR_VERSION
   from medmirror.runner import planned_trials

   spec = load_case_spec(path, supported_extractor_version=EXTRACTOR_VERSION)
   plan = planned_trials(registry, repeats=3, spec=spec)  # 计划（messages/trial_id/endpoint）
   # 执行：runner.execute_run(..., spec=spec)（预算硬闸与恢复语义不变）
   # 提取：protocol.extract_trial(trial, paths=spec.extraction_paths)
   # 报告：reporting.extract_sorted(trials, paths=...) / build_report(..., paths=...)
   #       / render_markdown(report, paths=...)——提取与报告须同一份词表
   ```

**边界（截至 issue #50）**：尚无按 `--case` 选病例的执行 CLI——`scripts/run_exp003_baseline.py`
锚定 exp003 默认病例；新病例的基线执行属 plan/003 步骤 2.3（须病例拍板与新协议版本后），
当前接入面是配置 + 库级 API。提取词表超出 v2 词表表达形态时按步骤 2.4 分流 needs_review。
本项目按仓库 clone + `uv sync` 运行（未发布 pip 包）：默认病例在 `medmirror.protocol` /
`medmirror.runner` 导入期按仓库相对路径读取 `configs/cases/`，wheel 安装形态不含该目录
（如需分发再补 package data，当前未做）。自定义 CaseSpec 经 `load_case_spec(任意路径)`
加载则不依赖仓库内目录。
