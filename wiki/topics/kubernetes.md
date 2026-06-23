# 主题：`kubernetes`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题笔记聚焦于 Kubernetes 环境下 AI Agent 系统的稳定性验证，核心问题是如何在分布式推理与多组件协作场景中量化故障容忍度，尤其针对 Pod 异常、网络分区、依赖中断等典型扰动下 Agent 链路的退化行为与恢复能力。可复用的工程实践包括基于 ChaosMesh 的声明式故障注入（NetworkChaos、PodChaos、StressChaos）、结合 Ginkgo 编写场景化 E2E 用例、以 Prometheus 与 OpenTelemetry 采集 SLO 指标，并通过 Argo Workflows 或 Tekton 串联混沌实验流水线，形成"扰动-观测-回归"闭环。对 QA 工作的启发是：应将混沌实验左移至 CI 阶段，针对 LLM 调用超时、向量库（如 FAISS、Milvus）抖动等 AI 特有故障建立专用故障库，并将 Agent 任务成功率、token 重试率纳入发布门禁，避免仅以单元测试覆盖率作为质量基线。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-21

## 时间线

- **Day 67** · 2026-06-21 · [每日 AI 学习笔记｜Day 67：AI Agent 混沌工程（ChaosMesh 与故障注入实战）](../days/day-67-day67-agent-chaos-engineering-chaosmesh-fault-injection.md)