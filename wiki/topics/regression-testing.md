# 主题：`regression-testing`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 场景下回归测试的成本与效率困境：当单条用例消耗数秒及数千 Token 时，传统全量回归在执行时长与 Token 开销上均不可持续，必须通过智能筛选压缩范围又不牺牲覆盖。可复用的工程实践包括基于代码变更—依赖图—用例映射的 Test Impact Analysis、融合历史失败率与变更频率及业务优先级的风险评分模型、按 Prompt / 工具 Schema / 模型版本差异化触发语义回归或契约测试的变更感知路由，以及 Ginkgo `Label` 选择器与 Playwright `@regression-p0` 标签等分层筛选能力。落地建议上，QA 应优先为用例补齐风险与分层元数据，使 CI 能按变更类型动态拉起最小必要集合；同时建立 Token 成本与失败率看板，将回归策略本身纳入持续度量与调优。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-21

## 时间线

- **Day 36** · 2026-05-21 · [每日 AI 学习笔记｜Day 36：AI Agent 回归测试策略与智能用例筛选](../days/day-36-day36-regression-testing-intelligent-selection.md)
  > **本篇核心要点：**  1. **全量回归不可持续**：AI Agent 每条用例平均消耗 0.5-2s + 数千 Token，500 条全量回归意味着 10min+ 执行时间和 \$5-20 Token 成本，必须引入智能筛选。 2. …