# 主题：`intelligent-selection`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 测试场景下的回归效率困境：当单条用例消耗数秒与数千 Token、全量回归在 500 条规模下即逼近 10 分钟与 \$5-20 成本红线时，如何以可控代价覆盖核心风险面。可复用的工程路径包括基于代码变更—依赖图—用例映射的 Test Impact Analysis，以历史失败率、变更频率、业务优先级与执行新鲜度构建的风险评分模型，以及按 Prompt、工具 Schema、模型版本分流的变更感知路由；落地侧则依托 Ginkgo 的 `Label` 选择器与 Playwright 的 `@regression-p0` 等 Tag Filter 在 CI 中按风险层级动态裁剪。建议 QA 团队优先将用例分层打标并沉淀变更—用例映射表，再以风险评分驱动 Top-N 调度，使日常 PR 仅触发智能子集、夜间或发布前再跑全量基线。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-21

## 时间线

- **Day 36** · 2026-05-21 · [每日 AI 学习笔记｜Day 36：AI Agent 回归测试策略与智能用例筛选](../days/day-36-day36-regression-testing-intelligent-selection.md)
  > **本篇核心要点：**  1. **全量回归不可持续**：AI Agent 每条用例平均消耗 0.5-2s + 数千 Token，500 条全量回归意味着 10min+ 执行时间和 \$5-20 Token 成本，必须引入智能筛选。 2. …