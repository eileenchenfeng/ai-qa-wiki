# 主题：`failure-analysis`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 在多步推理与工具调用链路中失败原因的可观测、可归因与可自动分诊问题，核心痛点是当 Agent 出现幻觉、工具调用错误或流程中断时，如何从 trace 日志中快速定位是 prompt 设计、检索召回、模型推理还是外部工具的故障层级。可复用的工程实践包括：基于 LangSmith / OpenTelemetry 的全链路 trace 埋点、结构化错误标签体系（root_cause × failure_stage）、用 LLM-as-Judge 对失败样本做二次分类、以及结合 FAISS 对历史失败 case 做相似度聚类以发现回归模式。对 QA 工作的启发是：应将失败归因流水线纳入回归测试基建，把每次 Agent 评测产出的 bad case 自动入库并打标，形成可持续演进的失败知识图谱，而非一次性人工排查。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-15

## 时间线

- **Day 30** · 2026-05-15 · [每日 AI 学习笔记｜Day 30：AI Agent 失败归因与自动化分诊](../days/day-30-day30-agent-failure-attribution-and-auto-triage.md)