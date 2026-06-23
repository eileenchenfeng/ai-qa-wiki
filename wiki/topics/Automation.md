# 主题：`Automation`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题围绕 AI Agent 上线后的可度量质量治理展开，核心问题是如何把模糊的"模型表现好不好"翻译成可追踪、可回归、可阻断发布的工程指标，即 SLO 设计、发布评分卡与自动化门禁的闭环。可复用的关键实践包括：以任务成功率、工具调用准确率、首响延迟 P95、单次会话成本等组成多维 SLO，结合金标集（golden set）回放与 LLM-as-Judge 双轨评估，落到 CI 中的发布评分卡，并通过 Ginkgo 编排行为级用例、Playwright 驱动端到端 Agent 操作、FAISS 维护检索基线、Prometheus + Grafana 跟踪线上 SLI 漂移。对 QA 的启示是：应尽早把评分卡纳入发布流水线，设定红线指标自动拦截劣化版本；同时建立golden set 与线上 badcase 的双向回流机制，让评测集随真实流量演进，避免离线分数虚高而线上回归。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-16

## 时间线

- **Day 31** · 2026-05-16 · [每日 AI 学习笔记｜Day 31：AI Agent 质量 SLO 与发布评分卡](../days/day-31-day31-agent-quality-slo-scorecard.md)