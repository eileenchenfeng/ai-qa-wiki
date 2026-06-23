# 主题：`test-data-management`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦 AI Agent 在持续迭代中如何稳定地管理测试数据与运行环境，核心矛盾在于 LLM 输出的非确定性使得传统断言型用例难以复用，而数据漂移、向量索引版本、外部工具 Mock 与多环境隔离又会进一步放大回归成本。可复用的工程实践包括：以 Golden Dataset 与分层 Fixture 维护可追溯的语料基线，借助 FAISS / Chroma 做向量快照与相似度阈值校验，使用 Ginkgo 组织 BDD 风格的 Agent 行为用例、Playwright 驱动端到端链路，并通过 Docker Compose 或 Testcontainers 隔离模型服务、工具依赖与数据库状态，配合 LangSmith 类追踪平台沉淀回放数据。落地建议是优先建设"数据—环境—评测"三位一体的测试底座，将测试数据视为带版本的资产而非脚本附属物，并在 CI 中固化向量与 Prompt 的指纹比对，及早暴露因数据或依赖更新引入的隐性回归。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-20

## 时间线

- **Day 35** · 2026-05-20 · [每日 AI 学习笔记｜Day 35：AI Agent 测试数据管理与环境治理](../days/day-35-day35-test-data-management-env-governance.md)