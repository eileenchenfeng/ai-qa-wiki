# 主题：`load-testing`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题四篇笔记聚焦于 AI Agent 场景下的性能压测如何从一次性脚本演进为可回归、可门禁的工程资产，核心问题在于传统 HTTP 压测工具难以覆盖 LLM 流式响应、长会话 WebSocket、多轮工具调用等不确定性负载，且缺乏对 token 吞吐、首包延迟（TTFT）、尾延迟与失败语义的统一度量。跨笔记可复用的方法论包括：以 Locust 承载多步骤业务化用户行为、以 k6（含 WebSocket 扩展）承载高并发与协议级压测、用 Ginkgo 将压测断言与基线对比纳入 BDD 风格回归、并通过 SLO 阈值（P95/P99、错误率、token/s）形成 CI 门禁。对 QA 的启发是：应尽早将 Agent 压测脚本与 Mock LLM、数据集快照一同纳入版本库，按场景分层维护基线指标，并在流水线中以红绿门禁阻断性能回退，避免性能问题滞留到线上才被发现。
<!-- LLM-DRAFT:END -->

- 共 **4** 篇笔记 · 最近更新：2026-06-19

## 时间线

- **Day 22** · 2026-05-07 · [每日 AI 学习笔记｜Day 22：性能压测实战（Locust/k6 + Agent 场景)](../days/day-22-day22-load-testing-practice.md)
- **Day 25** · 2026-05-10 · [每日 AI 学习笔记｜Day 25：AI Agent 性能压测资产化与回归门禁（k6 WebSocket + Locust + Ginkgo）](../days/day-25-day25-agent-performance-regression-gates.md)
- **Day 26** · 2026-05-11 · [每日 AI 学习笔记｜Day 26：面向 Agent 场景的 Locust/k6 性能压测工程化](../days/day-26-day26-locust-k6-agent-scenarios.md)
- **Day 65** · 2026-06-19 · [每日 AI 学习笔记｜Day 65：AI Agent 性能压测实战（Locust + k6 + Agent 场景）](../days/day-65-day65-agent-load-testing-locust-k6.md)