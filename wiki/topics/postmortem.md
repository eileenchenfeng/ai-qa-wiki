# 主题：`postmortem`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于事故驱动测试（Incident-Driven Testing, IDT）在 AI Agent 场景下的工程化落地，核心问题是如何将 Postmortem 中的 Action Item 转化为可执行、可回归的自动化用例，避免同类故障复发。可复用的关键实践包括 IDT 闭环五步法（Detect→Classify→Reproduce→Codify→Prevent）、Agent 故障六大 Taxonomy（Model/Prompt/Tool/Memory/Orchestration/Infra）以及 48 小时回归用例 SLA；技术栈层面可结合 Ginkgo 编写行为级回归、用 FAISS 做记忆污染与检索漂移检测、借助 Playwright 复现工具链断裂场景，并将用例纳入 CI Gate 形成准入卡口。对 QA 工作的启发是：应推动 Postmortem 模板强制关联回归用例 ID，并按故障分类维护标准化复现脚本库，使每一次 P0/P1 都沉淀为可量化的质量资产而非一次性复盘。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-24

## 时间线

- **Day 39** · 2026-05-24 · [每日 AI 学习笔记｜Day 39：AI Agent 事件驱动测试与可靠性工程](../days/day-39-day39-incident-driven-testing-reliability-engineering.md)
  > **本篇核心要点：**  1. **Incident-Driven Testing（IDT）核心理念**：每个 P0/P1 事故必须在 48h 内产出至少一条自动化回归用例，确保"同类故障不二犯"。IDT 是将 Postmortem 的 A…