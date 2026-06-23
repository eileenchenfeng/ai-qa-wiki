# 主题：`SDET`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题围绕 AI Agent 在 K8s 化交付链路中的端到端质量保障展开，覆盖发布验收、安全防线、评测样本集工程、失败归因与自动化分诊、质量看板、灰度与影子流量、契约与 Schema 演进、测试数据与环境治理八个环节，核心问题是如何为具备非确定性输出的 Agent 系统建立可度量、可回归、可追责的工程化测试闭环；可复用方法包括以 Ginkgo 组织端到端用例、Playwright 驱动多模态交互验证、FAISS 做语义相似度断言与样本去重、基于 JSON Schema 的契约测试与版本兼容矩阵、影子流量比对与灰度放量门禁、Prompt Injection 与越权用例集、归因标签体系驱动自动分诊以及 Prometheus/Grafana 质量看板。建议 QA 将"评测集即代码"和"质量门禁即流水线"作为团队基建优先级，先沉淀分层断言库与失败归因字典，再以影子流量打通线上回放，逐步替代人工抽检。
<!-- LLM-DRAFT:END -->

- 共 **10** 篇笔记 · 最近更新：2026-05-22

## 时间线

- **Day 27** · 2026-05-12 · [每日 AI 学习笔记｜Day 27：K8s 环境下 AI Agent 的端到端发布验收](../days/day-27-day27-k8s-agent-release-e2e-gates.md)
- **Day 28** · 2026-05-13 · [每日 AI 学习笔记｜Day 28：AI Agent 安全测试的端到端防线设计](../days/day-28-day28-ai-agent-security-e2e-guardrails.md)
- **Day 29** · 2026-05-14 · [每日 AI 学习笔记｜Day 29：AI Agent 评测样本集工程](../days/day-29-day29-agent-evaluation-dataset-engineering.md)
- **Day 30** · 2026-05-15 · [每日 AI 学习笔记｜Day 30：AI Agent 失败归因与自动化分诊](../days/day-30-day30-agent-failure-attribution-and-auto-triage.md)
- **Day 32** · 2026-05-17 · [每日 AI 学习笔记｜Day 32：AI Agent 质量看板与持续监控](../days/day-32-day32-agent-quality-dashboard-monitoring.md)
- **Day 33** · 2026-05-18 · [每日 AI 学习笔记｜Day 33：AI Agent 灰度发布与影子流量测试](../days/day-33-day33-canary-shadow-traffic-testing.md)
- **Day 34** · 2026-05-19 · [每日 AI 学习笔记｜Day 34：AI Agent 契约测试与 Schema 演进](../days/day-34-day34-agent-contract-testing-schema-evolution.md)
- **Day 35** · 2026-05-20 · [每日 AI 学习笔记｜Day 35：AI Agent 测试数据管理与环境治理](../days/day-35-day35-test-data-management-env-governance.md)
- **Day 36** · 2026-05-21 · [每日 AI 学习笔记｜Day 36：AI Agent 回归测试策略与智能用例筛选](../days/day-36-day36-regression-testing-intelligent-selection.md)
  > **本篇核心要点：**  1. **全量回归不可持续**：AI Agent 每条用例平均消耗 0.5-2s + 数千 Token，500 条全量回归意味着 10min+ 执行时间和 \$5-20 Token 成本，必须引入智能筛选。 2. …
- **Day 37** · 2026-05-22 · [每日 AI 学习笔记｜Day 37：AI Agent 可测试性设计与质量左移](../days/day-37-day37-agent-testability-design-shift-left.md)
  > **本篇核心要点：**  1. **可测试性是架构属性**：不可测试的 Agent 不是"测试没写好"，而是"架构没设计好"。可测试性必须在 Design Review 阶段评审，与功能需求同等优先。 2. **6 大可测试性原则**：可观…