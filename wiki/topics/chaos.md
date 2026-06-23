# 主题：`chaos`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦 AI Agent 在真实生产环境中的韧性问题，核心矛盾是 LLM 调用链路长、依赖外部模型与向量检索服务，一旦出现网络抖动、节点宕机或下游限流，Agent 容易陷入幻觉重试或静默失败，传统功能测试难以覆盖。可复用的工程实践包括：以 Chaos Mesh 注入 Pod Kill、网络延迟与 DNS 故障，结合 Ginkgo 编写 E2E 场景化用例，对 LLM Gateway、FAISS 向量库与 Agent 调度器进行分层故障演练，并通过 SLO（成功率、P99 时延、降级路径命中率）作为稳态假设的判定指标。对 QA 工作的启发是：应把混沌实验左移至 CI 流水线，针对每个新增 Tool 调用补充对应的故障矩阵；同时建立降级回归基线，确保模型超时或检索失败时 Agent 能稳定走兜底回答而非随机生成。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-09

## 时间线

- **Day 24** · 2026-05-09 · [每日 AI 学习笔记｜Day 24：AI Agent 混沌工程与故障注入（Chaos Mesh + Ginkgo E2E）](../days/day-24-day24-agent-chaos-engineering.md)