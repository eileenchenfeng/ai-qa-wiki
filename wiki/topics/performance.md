# 主题：`performance`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦 AI Agent 在真实负载下的性能、稳定性与成本治理，关注的并非单次推理延迟，而是长上下文、多工具调用、流式 WebSocket 通信、重试放大与租户级预算在持续压测中的退化行为，以及如何把这些指标沉淀为可回归的质量门禁。跨笔记可复用的工程实践包括：以 Locust 与 k6（含 WebSocket 场景）构建 Agent 化压测脚本，以 Ginkgo 做后端断言与预算校验，以 Playwright 验证前端成本与降级提示，结合 Trace 对账、基线快照与 K8s 限流配额，形成"基线—压测—资产化—门禁"的闭环，核心指标覆盖 P95 延迟、单会话 Token、失败重试倍数与工具调用 ROI。建议 QA 侧把性能与成本基线纳入每次发版的强制门禁，并将压测脚本与阈值同业务用例一同版本化，避免性能回归在上线后才被账单和告警发现。
<!-- LLM-DRAFT:END -->

- 共 **5** 篇笔记 · 最近更新：2026-05-27

## 时间线

- **Day 21** · 2026-05-06 · [每日 AI 学习笔记｜Day 21：AI Agent 性能与稳定性基线测试](../days/day-21-day21-agent-performance-baseline.md)
- **Day 22** · 2026-05-07 · [每日 AI 学习笔记｜Day 22：性能压测实战（Locust/k6 + Agent 场景)](../days/day-22-day22-load-testing-practice.md)
- **Day 25** · 2026-05-10 · [每日 AI 学习笔记｜Day 25：AI Agent 性能压测资产化与回归门禁（k6 WebSocket + Locust + Ginkgo）](../days/day-25-day25-agent-performance-regression-gates.md)
- **Day 26** · 2026-05-11 · [每日 AI 学习笔记｜Day 26：面向 Agent 场景的 Locust/k6 性能压测工程化](../days/day-26-day26-locust-k6-agent-scenarios.md)
- **Day 42** · 2026-05-27 · [每日 AI 学习笔记｜Day 42：AI Agent 成本治理与 Token 预算测试](../days/day-42-day42-agent-cost-governance-token-budget-testing.md)
  > AI Agent 的成本问题，本质上不是“模型单价太高”，而是 **上下文膨胀、无效工具调用、重试失控、长链路编排缺少预算护栏** 共同叠加的结果。测试侧不能只盯正确率，还要把 **单轮 Token 消耗、单会话累计成本、失败重试放大倍数、…