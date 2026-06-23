# 主题：`risk-scoring`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 测试体系中的回归成本失控问题——当单条用例消耗 0.5-2s 与数千 Token 时，500 条级别的全量回归在时间与费用上均不可持续，因此核心命题是如何在保障覆盖率的前提下实现"少跑、跑对"。可复用的关键实践包括：基于代码变更与依赖图的 Test Impact Analysis、由历史失败率/变更频率/业务优先级/失活天数构成的风险评分模型、按变更类型（Prompt / Schema / 模型版本）路由到语义回归、契约测试或 Eval 基线对比的差异化策略，以及借助 Ginkgo 的 Label 选择器与 Playwright 的 Tag Filter 在 CI 中按风险分层动态裁剪用例集。对 QA 的启发是：应把回归套件视为带成本的资产而非越多越好，建议先落地用例风险打分与标签分层，再以 TIA 驱动 PR 级智能选跑，将全量回归收敛到 Nightly 或发版门禁场景。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-21

## 时间线

- **Day 36** · 2026-05-21 · [每日 AI 学习笔记｜Day 36：AI Agent 回归测试策略与智能用例筛选](../days/day-36-day36-regression-testing-intelligent-selection.md)
  > **本篇核心要点：**  1. **全量回归不可持续**：AI Agent 每条用例平均消耗 0.5-2s + 数千 Token，500 条全量回归意味着 10min+ 执行时间和 \$5-20 Token 成本，必须引入智能筛选。 2. …