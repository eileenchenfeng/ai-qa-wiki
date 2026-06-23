# 主题：`chaosmesh`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 系统在生产环境下的稳定性验证问题，核心是如何通过混沌工程手段主动暴露 LLM 调用链路、向量检索与外部工具依赖中的脆弱点，而非依赖事后故障复盘。可复用的工程实践包括：使用 ChaosMesh 在 Kubernetes 层注入 Pod Kill、网络延迟、DNS 故障与带宽限制，针对 LLM Gateway、FAISS/向量库、Redis 会话存储等关键依赖编排稳态假设与爆炸半径控制，并结合 Ginkgo 或 pytest 编写故障场景下的回归用例，配合 Prometheus 指标作为自动化判稳信号。对 QA 工作的落地建议有两点：一是将故障注入纳入 Agent 上线前的准入流水线，把超时降级、重试幂等与上下文回滚作为强制验收项；二是为每条 Agent 链路预先定义 SLO 与稳态指标，避免混沌实验沦为无判据的"演练秀"。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-21

## 时间线

- **Day 67** · 2026-06-21 · [每日 AI 学习笔记｜Day 67：AI Agent 混沌工程（ChaosMesh 与故障注入实战）](../days/day-67-day67-agent-chaos-engineering-chaosmesh-fault-injection.md)