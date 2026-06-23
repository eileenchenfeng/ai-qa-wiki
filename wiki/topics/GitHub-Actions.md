# 主题：`GitHub-Actions`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦 AI Agent 端到端测试在 GitHub Actions 流水线中的工程化落地，核心问题在于如何应对 LLM 输出非确定性、模型→编排→工具→存储的长链路依赖以及推理延迟波动，使 E2E 测试在 CI 中保持稳定可控。可复用的关键实践包括：Setup-Execute-Verify 三阶段编排模型并配套超时熔断与失败隔离、基于 YAML/Go Struct 的 ScenarioSpec DSL 实现声明式场景与数据驱动、语义+结构+副作用的三维断言、按 Smoke/Core/Full/Chaos 分层并通过 Label 选择器绑定 PR Gate 与 Nightly，以及借助 K8s Namespace 做并行化资源隔离。对 QA 工作的启发是：应优先将测试场景 DSL 化以沉淀为资产而非一次性脚本，并在 GitHub Actions 中按时长预算严格分层，避免 PR 卡点被长尾用例拖垮。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-25

## 时间线

- **Day 40** · 2026-05-25 · [每日 AI 学习笔记｜Day 40：AI Agent 端到端测试编排与流水线集成](../days/day-40-day40-e2e-test-orchestration-cicd-pipeline.md)
  > **本篇核心要点：**  1. **E2E 测试编排的核心挑战**：AI Agent E2E 测试面临三大难题——非确定性输出（同一输入不同结果）、长链路依赖（模型→编排→工具→存储）、执行时间不可控（模型推理延迟波动大）。编排策略必须针对…