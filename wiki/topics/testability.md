# 主题：`testability`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 这类非确定性系统的可测试性架构设计，核心问题是如何将"测不了、测不稳、测不全"的 Agent 从架构层面转化为可被自动化验证的对象，而非在测试阶段事后补救。可复用的关键实践包括六大原则（Observability、Controllability、Isolability、Deterministic Replay、Explicit Contracts、Fault Injectability），以依赖注入（DI）解耦 LLM Client、Tool Executor 与 Memory Store 以支撑 Mock/Stub/Fake，以及在 LLM 与工具调用间插入 Recording/Replay Middleware 实现线上 Trace 的本地确定性回放，将概率性输出收敛为可断言行为。对 QA 的启发是：应将可测试性作为 Design Review 的硬性准入项，与功能需求同级评审；同时尽早建设 Trace 录制与回放基础设施，把线上真实流量沉淀为回归用例库，让质量左移真正具备工程抓手。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-22

## 时间线

- **Day 37** · 2026-05-22 · [每日 AI 学习笔记｜Day 37：AI Agent 可测试性设计与质量左移](../days/day-37-day37-agent-testability-design-shift-left.md)
  > **本篇核心要点：**  1. **可测试性是架构属性**：不可测试的 Agent 不是"测试没写好"，而是"架构没设计好"。可测试性必须在 Design Review 阶段评审，与功能需求同等优先。 2. **6 大可测试性原则**：可观…