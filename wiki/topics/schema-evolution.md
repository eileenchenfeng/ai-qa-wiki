# 主题：`schema-evolution`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦 AI Agent 在迭代过程中输入输出 Schema 的向后兼容与契约稳定性问题，核心矛盾在于模型版本升级、Prompt 调整或工具接口变更后，下游消费方仍能按既定结构解析与路由。可复用的关键实践包括：以 JSON Schema / Pydantic 模型作为契约源，借助 Pact 或自研 Contract Registry 做生产者—消费者双向校验，在 Ginkgo、Pytest 中沉淀字段级别的兼容性断言（新增可选、禁止删除必填、枚举只增不减），并结合 Schema diff 与 CI 卡点拦截破坏性变更；对于非结构化输出，可用 FAISS 做语义回归基线，Playwright 覆盖 Agent UI 链路的端到端契约。对 QA 的启发是：应将 Schema 视为一等测试对象，在 CI 中引入"契约门禁"与版本化快照，并联合 SRE 建立灰度回滚机制，让 Agent 升级具备可观测的兼容性证据而非依赖事后排障。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-19

## 时间线

- **Day 34** · 2026-05-19 · [每日 AI 学习笔记｜Day 34：AI Agent 契约测试与 Schema 演进](../days/day-34-day34-agent-contract-testing-schema-evolution.md)