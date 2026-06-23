# 主题：`Locust`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 场景下的性能压测工程化与回归门禁建设，核心问题是如何将一次性的压测脚本沉淀为可复用、可纳入 CI 的质量资产，覆盖 LLM 推理、流式输出与 WebSocket 长连接等非传统 HTTP 形态的负载特征。跨笔记可复用的实践包括：以 Locust 承载有状态的会话级用户行为建模、以 k6 处理 WebSocket 与高并发短连接、以 Ginkgo 编写 BDD 风格的回归断言，并围绕 P95/P99、Token 吞吐、首字节延迟等指标设定基线阈值，通过资产化的场景库与门禁脚本实现版本间的横向对比。对 QA 工作的启发是：应将压测脚本与基线指标纳入版本仓库与流水线，像功能用例一样治理；同时为 Agent 场景单独建立流式与长连接的指标口径，避免沿用传统接口压测的均值思维而漏掉尾部劣化。
<!-- LLM-DRAFT:END -->

- 共 **2** 篇笔记 · 最近更新：2026-05-11

## 时间线

- **Day 25** · 2026-05-10 · [每日 AI 学习笔记｜Day 25：AI Agent 性能压测资产化与回归门禁（k6 WebSocket + Locust + Ginkgo）](../days/day-25-day25-agent-performance-regression-gates.md)
- **Day 26** · 2026-05-11 · [每日 AI 学习笔记｜Day 26：面向 Agent 场景的 Locust/k6 性能压测工程化](../days/day-26-day26-locust-k6-agent-scenarios.md)