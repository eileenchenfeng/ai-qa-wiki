# 主题：`opentelemetry`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 在多步推理与工具调用链路中的可观测性缺口，核心问题是如何在 LLM 输出非确定性的前提下，定位 prompt、检索、tool call 各环节的耗时瓶颈与失败归因。跨笔记可复用的工程要点包括：以 OpenTelemetry 为统一埋点标准，将 Agent 的 plan-act-observe 循环建模为父子 Span，结合 trace_id 串联 RAG 检索（如 FAISS 召回耗时）、工具调用与模型推理，再通过 Jaeger 或 Langfuse 做可视化下钻，并在 Span 属性中固化 token 数、模型版本、prompt 哈希等关键标签。对 QA 工作的启发是：回归测试不应只断言最终输出，而应在 E2E 用例中校验 Span 拓扑与关键属性是否齐全，把"链路完整性"作为质量门禁；同时可基于历史 trace 沉淀延迟与失败率基线，用于发布前的性能比对与异常检测。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-20

## 时间线

- **Day 66** · 2026-06-20 · [每日 AI 学习笔记｜Day 66：AI Agent 可观测性与链路追踪（OpenTelemetry + Trace）](../days/day-66-day66-agent-observability-opentelemetry-tracing.md)