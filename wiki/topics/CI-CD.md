# 主题：`CI-CD`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 在 CI/CD 流水线中的端到端测试编排难题，核心矛盾在于如何用确定性的工程框架去约束非确定性的模型行为、长链路依赖与不稳定的推理延迟。可复用的工程范式包括：Setup-Execute-Verify 三阶段编排模型、基于 YAML/Go Struct 的 ScenarioSpec 场景 DSL、语义+结构+副作用的三维断言体系，以及 Smoke/Core/Full/Chaos 四层流水线分级（分别绑定 PR Gate、Merge Gate、Nightly、Weekly），配合 K8s Namespace 实现并行隔离与 Label 选择器驱动用例子集。对 QA 落地的启发是：一方面应将测试场景声明化、数据驱动化，沉淀为可参数复用的资产而非一次性脚本；另一方面要按执行时长与稳定性给用例分层挂载到不同 Gate，避免长尾用例阻塞主干合入节奏。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-25

## 时间线

- **Day 40** · 2026-05-25 · [每日 AI 学习笔记｜Day 40：AI Agent 端到端测试编排与流水线集成](../days/day-40-day40-e2e-test-orchestration-cicd-pipeline.md)
  > **本篇核心要点：**  1. **E2E 测试编排的核心挑战**：AI Agent E2E 测试面临三大难题——非确定性输出（同一输入不同结果）、长链路依赖（模型→编排→工具→存储）、执行时间不可控（模型推理延迟波动大）。编排策略必须针对…