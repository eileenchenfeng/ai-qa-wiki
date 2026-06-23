# 主题：`performance`

- 共 **5** 篇笔记 · 最近更新：2026-05-27

## 时间线

- **Day 21** · 2026-05-06 · [每日 AI 学习笔记｜Day 21：AI Agent 性能与稳定性基线测试](../days/day-21-day21-agent-performance-baseline.md)
- **Day 22** · 2026-05-07 · [每日 AI 学习笔记｜Day 22：性能压测实战（Locust/k6 + Agent 场景)](../days/day-22-day22-load-testing-practice.md)
- **Day 25** · 2026-05-10 · [每日 AI 学习笔记｜Day 25：AI Agent 性能压测资产化与回归门禁（k6 WebSocket + Locust + Ginkgo）](../days/day-25-day25-agent-performance-regression-gates.md)
- **Day 26** · 2026-05-11 · [每日 AI 学习笔记｜Day 26：面向 Agent 场景的 Locust/k6 性能压测工程化](../days/day-26-day26-locust-k6-agent-scenarios.md)
- **Day 42** · 2026-05-27 · [每日 AI 学习笔记｜Day 42：AI Agent 成本治理与 Token 预算测试](../days/day-42-day42-agent-cost-governance-token-budget-testing.md)
  > AI Agent 的成本问题，本质上不是“模型单价太高”，而是 **上下文膨胀、无效工具调用、重试失控、长链路编排缺少预算护栏** 共同叠加的结果。测试侧不能只盯正确率，还要把 **单轮 Token 消耗、单会话累计成本、失败重试放大倍数、…