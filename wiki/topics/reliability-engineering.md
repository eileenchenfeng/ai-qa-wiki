# 主题：`reliability-engineering`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 系统在生产环境中的可靠性工程，核心问题是如何将事故经验沉淀为可执行的回归资产，避免同类故障在模型退化、Prompt 漂移、工具链断裂、记忆污染与多 Agent 死锁等多元根因下反复出现。可复用的关键实践是 Incident-Driven Testing 闭环五步法（Detect→Classify→Reproduce→Codify→Prevent），辅以 6 大类故障 Taxonomy（Model/Prompt/Tool/Memory/Orchestration/Infra）形成标准化复现模板，并通过 Ginkgo 等 BDD 框架编码回归用例、接入 CI Gate 强制拦截，配合 FAISS 等向量检索做记忆污染比对。对 QA 工作的启发是：将 48h 内产出至少一条自动化回归用例写入 Postmortem SOP，并按故障分类维护可插拔的测试模板库，让事故复盘真正闭环到流水线而非停留在文档。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-24

## 时间线

- **Day 39** · 2026-05-24 · [每日 AI 学习笔记｜Day 39：AI Agent 事件驱动测试与可靠性工程](../days/day-39-day39-incident-driven-testing-reliability-engineering.md)
  > **本篇核心要点：**  1. **Incident-Driven Testing（IDT）核心理念**：每个 P0/P1 事故必须在 48h 内产出至少一条自动化回归用例，确保"同类故障不二犯"。IDT 是将 Postmortem 的 A…