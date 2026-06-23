# 主题：`contract-testing`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 在多版本迭代与多服务协作场景下的接口稳定性问题，核心矛盾在于 LLM 输出的非确定性与上下游对结构化数据的强约束之间如何达成可验证的契约。可复用的工程实践包括：以 JSON Schema / Pydantic 模型固化 Agent 的输入输出契约，借助 Pact 或自研 schema diff 工具进行消费者驱动的契约校验，结合 Ginkgo、pytest 编写版本兼容性回归用例，并在 CI 中引入 schema 演进检查（新增字段向后兼容、删除字段需走 deprecation 流程）以及基于快照的语义回归。对 QA 工作的启发是：应将 Agent 视为一个具备版本号的 API 而非黑盒模型，把 schema 变更纳入发布门禁，并为 prompt、模型、工具链分别维护独立的契约测试套件，避免一次升级引发跨链路静默失败。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-19

## 时间线

- **Day 34** · 2026-05-19 · [每日 AI 学习笔记｜Day 34：AI Agent 契约测试与 Schema 演进](../days/day-34-day34-agent-contract-testing-schema-evolution.md)