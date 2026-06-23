# 主题：`dependency-injection`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于一个被长期低估的工程命题：AI Agent 的可测试性本质上是架构属性，而依赖注入则是支撑 Mock、Stub、Fake 等隔离手段得以成立的前置条件，没有 DI 就没有真正可控的单元测试与集成测试。可复用的关键实践包括：通过接口抽象 LLM Client、Tool Executor、Memory Store 与 Orchestrator 等核心依赖，在调用链中插入 Recording/Replay Middleware 实现 Trace 录制与确定性回放，将 LLM 的非确定性输出转化为可断言的固定向量，并围绕可观测性、可控制性、可隔离性、故障可注入性建立 Design Review 检查项。对 QA 工作的落地建议有二：一是将"是否通过构造函数或容器注入外部依赖"作为 Agent 代码合入的硬性门禁；二是搭建线上 Trace 采样回放流水线，让回归测试直接消费真实流量样本，替代脆弱的 Prompt 字符串断言。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-22

## 时间线

- **Day 37** · 2026-05-22 · [每日 AI 学习笔记｜Day 37：AI Agent 可测试性设计与质量左移](../days/day-37-day37-agent-testability-design-shift-left.md)
  > **本篇核心要点：**  1. **可测试性是架构属性**：不可测试的 Agent 不是"测试没写好"，而是"架构没设计好"。可测试性必须在 Design Review 阶段评审，与功能需求同等优先。 2. **6 大可测试性原则**：可观…