# 主题：`release-gates`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 在 Kubernetes 环境下从镜像构建、灰度发布到端到端验收的发布闸门设计，核心问题是如何在模型与提示词频繁迭代的背景下，把"可上线"这一判断从主观经验沉淀为可量化、可阻断的自动化卡点。可复用的工程实践包括：以 Ginkgo/Gomega 编写带 BDD 语义的发布期验收用例、用 Playwright 串联 Agent 前端会话与工具调用链路、基于 FAISS 召回回归集进行语义相似度比对、结合 Argo Rollouts 或 Flagger 做 SLO 驱动的渐进式发布，以及通过 Prometheus 指标与 OpenTelemetry trace 共同构成回滚信号。对 QA 工作的启发是：应将质量门禁左移到 Helm Chart 与 CI 流水线中，把"语义正确率、工具调用成功率、P95 时延"三类指标固化为发布准入硬阈值；同时建立线上小流量影子评测，使每次模型或 Prompt 变更都能在真实流量下获得可追溯的验收证据。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-12

## 时间线

- **Day 27** · 2026-05-12 · [每日 AI 学习笔记｜Day 27：K8s 环境下 AI Agent 的端到端发布验收](../days/day-27-day27-k8s-agent-release-e2e-gates.md)