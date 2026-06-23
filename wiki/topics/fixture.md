# 主题：`fixture`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 在持续迭代过程中如何治理测试数据与运行环境，核心问题是消除因数据漂移、外部依赖不稳定与状态污染导致的用例不可复现。可复用的工程实践包括：以 fixture 为单位管理种子数据与向量索引快照（FAISS / Chroma 的离线导出），通过 Ginkgo 的 BeforeSuite/AfterEach 或 Pytest fixture 控制作用域与清理顺序，结合 Testcontainers 拉起隔离的 LLM Mock、向量库与中间件，并用 VCR/WireMock 录制回放第三方调用，Playwright 侧则以 storageState 固化登录态。对 QA 的启发是：将 fixture 视为与代码同等的资产纳入版本管理，按 session/module/function 分层声明依赖，并为每个 Agent 用例显式声明数据契约与回滚钩子，避免"跑过一次就脏"的隐式耦合拖慢回归节奏。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-20

## 时间线

- **Day 35** · 2026-05-20 · [每日 AI 学习笔记｜Day 35：AI Agent 测试数据管理与环境治理](../days/day-35-day35-test-data-management-env-governance.md)