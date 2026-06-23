# 主题：`incident-driven-testing`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于将 AI Agent 线上事故转化为可回归资产的工程化路径，核心问题是如何让 P0/P1 故障在 48 小时内沉淀为自动化用例，避免模型退化、Prompt 漂移、工具链断裂、记忆污染与多 Agent 死锁等 Agent 特有故障重复发生。可复用的关键实践包括 IDT 闭环五步法（Detect→Classify→Reproduce→Codify→Prevent）、Agent 故障 6 大类 Taxonomy（Model/Prompt/Tool/Memory/Orchestration/Infra）、Postmortem Action Item 到测试代码的映射机制，以及 Ginkgo 行为驱动断言、Playwright 端到端复现、FAISS 向量记忆校验等工具组合，配合 CI Gate 强制拦截同类回归。对 QA 工作的启发是：应在事故响应流程中固化"48h 回归用例交付"硬指标，并预先按故障 Taxonomy 维护标准化复现脚本与测试模板，使每次事故都能直接套模板产出可执行用例，将被动救火转为主动防御资产积累。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-24

## 时间线

- **Day 39** · 2026-05-24 · [每日 AI 学习笔记｜Day 39：AI Agent 事件驱动测试与可靠性工程](../days/day-39-day39-incident-driven-testing-reliability-engineering.md)
  > **本篇核心要点：**  1. **Incident-Driven Testing（IDT）核心理念**：每个 P0/P1 事故必须在 48h 内产出至少一条自动化回归用例，确保"同类故障不二犯"。IDT 是将 Postmortem 的 A…