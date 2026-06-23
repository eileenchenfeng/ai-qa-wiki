# 主题：`OpenTelemetry`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
这两篇笔记共同聚焦于 AI Agent 系统的运行时可观测性与韧性保障：Day 23 从 OpenTelemetry Trace 切入，关注 LLM 调用链、Embedding 检索、工具调用等跨服务环节的 span 串联与延迟归因；Day 41 则把视角延伸到灾备演练，按控制面（编排、路由、模型网关）、数据面（Memory、向量库、缓存）、用户面（流式降级提示）三层组织故障注入与恢复验证。可复用的工程关键词包括 OTel SDK + Collector、TraceID 透传、span 属性打点（model、tokens、retrieval_topk）、FAISS/向量库只读降级、流式响应断点续传，以及结合 Ginkgo 或 Playwright 做端到端故障回放。对 QA 的启发是：一方面把 trace 字段约定纳入接口契约测试，让链路数据成为断言依据而非排查辅助；另一方面将灾备场景沉淀为定期跑的混沌用例集，覆盖切换 RTO 与降级 UI 双重验收。
<!-- LLM-DRAFT:END -->

- 共 **2** 篇笔记 · 最近更新：2026-05-26

## 时间线

- **Day 23** · 2026-05-08 · [每日 AI 学习笔记｜Day 23：可观测性与链路追踪（OpenTelemetry + Trace）](../days/day-23-day23-agent-observability-and-tracing.md)
- **Day 41** · 2026-05-26 · [每日 AI 学习笔记｜Day 41：AI Agent 灾备演练与恢复测试](../days/day-41-day41-agent-disaster-recovery-drills.md)
  > **推荐分层：**  1. **控制面灾备**：Agent 编排服务、路由配置、模型网关、任务调度器故障后，能否快速切换到备用实例或备用区域。 2. **数据面灾备**：Memory、向量库、缓存、任务状态存储异常时，是否支持只读、降级、重…