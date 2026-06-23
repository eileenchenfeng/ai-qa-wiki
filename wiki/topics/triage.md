# 主题：`triage`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题围绕 AI Agent 在多步推理与工具调用链路中的失败归因展开，核心问题是如何把"Agent 跑挂了"这一模糊现象拆解为可定位的失败节点，并通过自动化分诊（triage）将海量 trace 按根因聚类，降低人工复盘成本。跨笔记可复用的工程要点包括：基于 LangSmith / OpenTelemetry 的全链路 trace 采集、对 tool call 与 LLM 响应做结构化校验（JSON Schema、Pydantic）、用 embedding + FAILSS 对失败样本做相似度聚类、再以 LLM-as-Judge 输出归因标签，并接入回归集做长期监控。对 QA 工作的启发是：应将分诊流水线视为一等公民，建立"失败样本→根因标签→回归用例"的闭环，并把分诊准确率本身纳入指标体系，避免归因模型成为新的黑盒。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-15

## 时间线

- **Day 30** · 2026-05-15 · [每日 AI 学习笔记｜Day 30：AI Agent 失败归因与自动化分诊](../days/day-30-day30-agent-failure-attribution-and-auto-triage.md)