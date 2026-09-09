# MedMirror

医疗模型治疗路径呈现差异评测系统，当前处于初始化阶段，尚无可运行评测程序。

- [方向](.42cog/intent.md)
- [约束与资源](.42cog/real.md)
- [报告标准和实验草案](specs/calibration.md)
- [工作状态与下一步](state/board.md)
- [Agent 开工入口](AGENTS.md)

## 结构
规约：.42cog/、specs/、CLAUDE.md。来源：vault/、notes/、resources/。方法：skills/、scripts/。作品：src/、runs/。状态：state/、docs/。过程：_tmp/、_build/、_archive/。

## 初始化验证
运行 `python3 scripts/check-manifests.py` 校验模板清单。此检查不代表 API、评测或医学判断已经验证。
密钥配置模板为 .env.example；实际密钥放 .env.local，禁止提交。未设置远程仓库，忽略文件需另行备份。

