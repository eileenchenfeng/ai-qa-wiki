# 主题：`fault-injection`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 在复杂依赖与不确定性环境下的鲁棒性验证，核心问题是如何在受控条件下主动暴露 LLM 调用链、向量检索与工具编排中的脆弱点，而非被动等待线上故障。可复用的工程实践包括基于 ChaosMesh 的 Pod / 网络 / IO 故障注入，针对 LLM 接口的延迟与超时模拟、限流与 5xx 错误回放，结合 Ginkgo 编写稳态假设（Steady-State Hypothesis）驱动的混沌实验用例，并通过对 FAISS 等向量库的节点抖动验证降级与重试策略的有效性。对 QA 工作的启发是：将故障注入纳入 Agent 回归流水线，为每条关键链路预先定义可观测的稳态指标与自动回滚阈值；同时建立故障场景库，覆盖模型超时、工具调用失败与检索为空三类高发模式，让韧性测试常态化而非一次性演练。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-21

## 时间线

- **Day 67** · 2026-06-21 · [每日 AI 学习笔记｜Day 67：AI Agent 混沌工程（ChaosMesh 与故障注入实战）](../days/day-67-day67-agent-chaos-engineering-chaosmesh-fault-injection.md)