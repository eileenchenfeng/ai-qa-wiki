# 主题：`test-impact-analysis`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 场景下回归测试的成本与效率困境：当单条用例需消耗秒级时延与数千 Token 时，全量回归在时间与费用上均不可持续，必须以「精准筛选」替代「无差别覆盖」。可复用的工程实践包括基于代码变更与依赖图的 Test Impact Analysis、融合历史失败率/变更频率/业务优先级/执行新鲜度的风险评分模型，以及按变更类型路由测试范围（Prompt 变更跑语义回归、Schema 变更跑契约测试、模型版本变更跑 Eval 基线），落地层面则可借助 Ginkgo 的 Label 选择器与 Playwright 的 Tag Filter 在 CI 中按风险层级动态裁剪用例集。对 QA 的启发是：应将"用例选择"视为一等公民纳入流水线，建立变更类型到测试套件的显式映射表，并以 Token 成本与缺陷逃逸率双指标持续校准筛选策略，避免为追求速度而牺牲回归可信度。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-21

## 时间线

- **Day 36** · 2026-05-21 · [每日 AI 学习笔记｜Day 36：AI Agent 回归测试策略与智能用例筛选](../days/day-36-day36-regression-testing-intelligent-selection.md)
  > **本篇核心要点：**  1. **全量回归不可持续**：AI Agent 每条用例平均消耗 0.5-2s + 数千 Token，500 条全量回归意味着 10min+ 执行时间和 \$5-20 Token 成本，必须引入智能筛选。 2. …