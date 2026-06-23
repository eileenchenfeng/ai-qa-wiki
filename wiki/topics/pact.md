# 主题：`pact`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 在多版本协作场景下如何通过契约测试稳定接口语义，核心问题是当上游模型输出 Schema 或工具调用协议发生演进时，下游消费方如何在不回归整体链路的前提下快速定位破坏性变更。可复用的工程实践包括：基于 Pact / OpenAPI 的 consumer-driven contract 校验、使用 JSON Schema + Ajv 对 LLM 结构化输出做字段级断言、借助 Ginkgo 组织契约用例并产出 pact 文件、在 CI 中接入 Pact Broker 实现 provider 端的 can-i-deploy 闸口，以及对 Embedding 与检索结果用 FAISS 做兼容性回放。对 QA 落地建议有二：一是将 Agent 的工具调用参数、函数返回体纳入契约资产管理，按版本归档并与 prompt 模板共同灰度；二是在流水线中前置 Schema diff 检测，把"字段新增/删除/类型变更"映射为不同等级的阻断策略，降低模型升级带来的回归成本。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-19

## 时间线

- **Day 34** · 2026-05-19 · [每日 AI 学习笔记｜Day 34：AI Agent 契约测试与 Schema 演进](../days/day-34-day34-agent-contract-testing-schema-evolution.md)