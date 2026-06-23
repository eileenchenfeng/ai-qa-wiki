# 主题：`API-testing`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦 AI Agent 从环境就绪到上线运营全链路的 API 层验收问题，覆盖 K8s 端到端发布验收、评测样本集构建、失败归因与自动分诊、质量看板与持续监控、灰度与影子流量、契约测试与 Schema 演进六个环节，核心矛盾是如何在模型输出非确定性下保障接口语义稳定与回归可控。可复用的工程实践包括：基于 Ginkgo/Pytest 的分层用例编排、Playwright 驱动的端到端回放、FAISS 做语义断言与相似样本聚类、JSON Schema/Pact 守护契约边界、影子流量与灰度分桶做线上对照、Prometheus + Grafana 沉淀质量看板与归因标签体系。对 QA 的落地建议有二：一是把"样本集 + 契约 + 监控"作为 Agent 项目的最小测试基线，先于功能用例建设；二是将失败归因结构化为可消费的标签流，反哺灰度门禁与发布卡点，形成闭环而非一次性验收。
<!-- LLM-DRAFT:END -->

- 共 **6** 篇笔记 · 最近更新：2026-05-19

## 时间线

- **Day 27** · 2026-05-12 · [每日 AI 学习笔记｜Day 27：K8s 环境下 AI Agent 的端到端发布验收](../days/day-27-day27-k8s-agent-release-e2e-gates.md)
- **Day 29** · 2026-05-14 · [每日 AI 学习笔记｜Day 29：AI Agent 评测样本集工程](../days/day-29-day29-agent-evaluation-dataset-engineering.md)
- **Day 30** · 2026-05-15 · [每日 AI 学习笔记｜Day 30：AI Agent 失败归因与自动化分诊](../days/day-30-day30-agent-failure-attribution-and-auto-triage.md)
- **Day 32** · 2026-05-17 · [每日 AI 学习笔记｜Day 32：AI Agent 质量看板与持续监控](../days/day-32-day32-agent-quality-dashboard-monitoring.md)
- **Day 33** · 2026-05-18 · [每日 AI 学习笔记｜Day 33：AI Agent 灰度发布与影子流量测试](../days/day-33-day33-canary-shadow-traffic-testing.md)
- **Day 34** · 2026-05-19 · [每日 AI 学习笔记｜Day 34：AI Agent 契约测试与 Schema 演进](../days/day-34-day34-agent-contract-testing-schema-evolution.md)