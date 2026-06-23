# 主题：`shift-left`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦一个核心问题：AI Agent 的非确定性与多层依赖（LLM、Tool、Memory、Orchestrator）使传统测试范式失效，必须将"可测试性"作为架构属性在 Design Review 阶段前置评审，而非事后补救。可复用的关键实践包括六大原则（可观测性、可控制性、可隔离性、确定性回放、契约显式化、故障可注入性），以依赖注入（DI）为基石将 LLM Client、Tool Executor 等通过接口解耦，并在 LLM 与 Tool 调用之间植入 Recording/Replay Middleware，将线上 Trace 录制为本地夹具以实现确定性断言，配合 Mock/Stub/Fake 与故障注入完成契约校验。对 QA 的落地建议：一是将可测试性 Checklist 纳入 Agent 类需求的准入门禁，对硬编码 LLM/Tool 实例化的 PR 直接打回；二是搭建统一的 Trace 录制回放平台，让回归用例从"调用真实模型"迁移到"重放历史 Trace"，显著降低 CI 成本与 Flaky 率。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-22

## 时间线

- **Day 37** · 2026-05-22 · [每日 AI 学习笔记｜Day 37：AI Agent 可测试性设计与质量左移](../days/day-37-day37-agent-testability-design-shift-left.md)
  > **本篇核心要点：**  1. **可测试性是架构属性**：不可测试的 Agent 不是"测试没写好"，而是"架构没设计好"。可测试性必须在 Design Review 阶段评审，与功能需求同等优先。 2. **6 大可测试性原则**：可观…