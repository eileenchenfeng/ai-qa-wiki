# 主题：`protobuf`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 在工具调用与多服务协作中如何通过 Protobuf 约束接口契约，并在 Schema 持续演进的过程中保证向前/向后兼容。笔记从契约测试视角切入，强调以 .proto 文件作为单一事实源，配合 buf breaking、buf lint 做变更门禁，结合 Ginkgo/Go test 编写消费者驱动契约用例，并借助 Pact 或自建 golden message 仓库回放历史报文，验证字段新增、reserved 占位、oneof 扩展等典型演进场景下 Agent 调用链的稳定性。对 QA 工作的启发有两点：一是把 proto 变更纳入 CI 强制流水线，破坏性变更需显式审批并同步更新 fixture，避免 LLM 侧解析静默失败；二是为结构化输出建立 schema 快照库，定期跑兼容性回归，及早暴露模型升级与契约漂移带来的隐性故障。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-19

## 时间线

- **Day 34** · 2026-05-19 · [每日 AI 学习笔记｜Day 34：AI Agent 契约测试与 Schema 演进](../days/day-34-day34-agent-contract-testing-schema-evolution.md)