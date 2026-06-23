# 主题：`backward-compatibility`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 在版本迭代过程中如何保障接口与数据契约的向后兼容，核心问题是当 Prompt、Schema 或工具调用签名发生演进时，下游消费者与历史回放数据不应被破坏。可复用的工程实践包括基于 JSON Schema / Pydantic 的契约校验、使用 Ginkgo 或 Pact 编写消费者驱动的契约测试、对 structured output 字段做新增可选而非删除重命名的演进策略，以及借助快照测试与回放语料库验证旧版本输入在新版 Agent 下的稳定性。对 QA 工作的启发是：应在 CI 中固化 Schema diff 检查，对破坏性变更强制阻断合并，并维护一份带版本标签的黄金用例集，确保模型升级或 Prompt 重构时能快速定位兼容性回归。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-19

## 时间线

- **Day 34** · 2026-05-19 · [每日 AI 学习笔记｜Day 34：AI Agent 契约测试与 Schema 演进](../days/day-34-day34-agent-contract-testing-schema-evolution.md)