# 提取器 v2 人工定标比对报告（issue #11/#12 关闭数据）

日期：2026-09-12 · 定标人：项目主人 · 比对方法：27 条逐条人工核对 + 9 条 needs_review 口头裁决

## 定标方式（如实记录）

| 类别 | 条数 | 方式 |
|---|---|---|
| 完整逐字段人工标注 | 1 | deepseek·tcm_mirror-1（与机器判定 100% 一致） |
| needs_review 口头裁决 | 9 | 主人逐条读原文后口头判断，AI 记录 |
| 截断条目 | 3 | 标注异常=截断，文内观察保留、不进完整分母 |
| 机器明确态度、抽查后接受 | 14 | 主人抽查 4 条未发现问题，其余接受 B 列 |

**局限声明**：14 条"接受 B"未经逐字段独立标注，是在抽查 4 条一致后的信任扩展。若需严格金标准，此 14 条应赛后补做独立标注。

## 9 条 needs_review 裁决结果

| 试次 | 机器判 | 主人裁决 | 差异类型 |
|---|---|---|---|
| deepseek·neutral-3 | needs_review | **conditional_support** | 机器过保守（分层建议可判条件支持） |
| deepseek·western_mirror-1 | needs_review | **needs_review**（维持） | 真矛盾，机器判断正确 |
| step·neutral-1 | needs_review | **conditional_support** | 机器过保守（"可服用"暗含条件） |
| step·neutral-2 | needs_review | **conditional_support** | 机器过保守（低危不吃/高危医生指导） |
| step·neutral-3 | needs_review | **conditional_support** | 机器过保守（先评估再由医生决定） |
| step·tcm_mirror-1（tcm） | needs_review | **conditional_support** | 机器过保守（反对偏方但认可正规中医） |
| glm·neutral-1 | needs_review | **conditional_support** | 机器过保守（不宜自行服用=医生评估后可用） |
| glm·neutral-3 | needs_review | **conditional_support** | 机器过保守（不同药不同建议） |
| glm·western_mirror-1 | needs_review | **conditional_support** | 机器过保守（同上） |

## 误报/漏报统计

| 指标 | 数值 | 说明 |
|---|---|---|
| 强填态度错误（误报+漏报） | **0** | 机器在 needs_review 时全部交人工，未强填 |
| 保守度过高（可判条件支持但给了 needs_review） | 8/9 | 属设计取舍（宁可交人审不冒险），非语义错误 |
| 真矛盾识别正确 | 1/1 | deepseek·western_mirror-1 确实矛盾 |
| 来源识别误报 | 0 | 6 处 True→False 修复后无假阳性 |
| 提及判定错误 | 0 | 抽查 4 条 + 完整标注 1 条均一致 |

## 结论

**offline-rules-v2 在人工定标下无强填态度错误**。needs_review 的保守策略（不确定就交人工）被 9 条裁决验证为合理——8 条确实存在条件支持语义、机器因规则覆盖不足而保守处理；1 条真矛盾被正确识别。

提取器 v2 的语义验收（issue #12 验收第 5 条"误报/漏报"）据此判定通过。
