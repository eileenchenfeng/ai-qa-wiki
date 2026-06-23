# 主题：`environment-governance`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 在多环境、多版本迭代下的测试数据治理与环境一致性问题，核心矛盾在于 Agent 行为的非确定性与传统测试环境静态假设之间的冲突，需要解决数据漂移、依赖隔离、Mock 与真实服务切换、向量库快照回滚等工程难题。可复用的实践包括以数据契约（JSON Schema / Pydantic）约束输入输出、通过 Testcontainers 编排依赖、用 FAISS 或 Milvus 快照固化检索基线、借助 LangSmith / Langfuse 追踪链路，以及结合 Ginkgo、Pytest、Playwright 在不同层级构建分层用例，并通过种子数据与影子流量实现回归对齐。对 QA 落地的启发：一是将测试数据视为版本化制品，与模型权重、Prompt 模板共同纳入 CI 流水线；二是建立环境画像基线，对每次 Agent 上线执行差异巡检，避免静默退化。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-20

## 时间线

- **Day 35** · 2026-05-20 · [每日 AI 学习笔记｜Day 35：AI Agent 测试数据管理与环境治理](../days/day-35-day35-test-data-management-env-governance.md)