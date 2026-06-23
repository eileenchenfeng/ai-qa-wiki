# 主题：`K8s`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题下的 11 篇笔记围绕 AI Agent 在 K8s 环境下从发布验收、安全防线、评测样本集、失败归因到线上巡检的全生命周期质量保障展开，核心问题是如何把非确定性的 LLM 系统纳入可工程化、可回归、可观测的测试体系。跨笔记反复出现的关键实践包括：基于 Ginkgo Label 与 Playwright Tag 的分层用例筛选、Test Impact Analysis 与风险评分驱动的智能回归、依赖注入与 Recording/Replay 中间件支撑的确定性回放、FAISS/Embedding 语义断言、合成探针与金丝雀断言构成的线上活性检测，以及围绕 Prompt、工具 Schema、模型版本的变更感知路由。对 QA 的启发是：一方面应在 Design Review 阶段把可观测性、可控制性、可隔离性作为架构验收项前置，杜绝"测不动"的 Agent 进入交付链路；另一方面要建设离线 Eval 基线与线上探针双轨制，让生产 Trace 反哺评测样本集，形成质量闭环。
<!-- LLM-DRAFT:END -->

- 共 **11** 篇笔记 · 最近更新：2026-05-26

## 时间线

- **Day 27** · 2026-05-12 · [每日 AI 学习笔记｜Day 27：K8s 环境下 AI Agent 的端到端发布验收](../days/day-27-day27-k8s-agent-release-e2e-gates.md)
- **Day 28** · 2026-05-13 · [每日 AI 学习笔记｜Day 28：AI Agent 安全测试的端到端防线设计](../days/day-28-day28-ai-agent-security-e2e-guardrails.md)
- **Day 29** · 2026-05-14 · [每日 AI 学习笔记｜Day 29：AI Agent 评测样本集工程](../days/day-29-day29-agent-evaluation-dataset-engineering.md)
- **Day 30** · 2026-05-15 · [每日 AI 学习笔记｜Day 30：AI Agent 失败归因与自动化分诊](../days/day-30-day30-agent-failure-attribution-and-auto-triage.md)
- **Day 35** · 2026-05-20 · [每日 AI 学习笔记｜Day 35：AI Agent 测试数据管理与环境治理](../days/day-35-day35-test-data-management-env-governance.md)
- **Day 36** · 2026-05-21 · [每日 AI 学习笔记｜Day 36：AI Agent 回归测试策略与智能用例筛选](../days/day-36-day36-regression-testing-intelligent-selection.md)
  > **本篇核心要点：**  1. **全量回归不可持续**：AI Agent 每条用例平均消耗 0.5-2s + 数千 Token，500 条全量回归意味着 10min+ 执行时间和 \$5-20 Token 成本，必须引入智能筛选。 2. …
- **Day 37** · 2026-05-22 · [每日 AI 学习笔记｜Day 37：AI Agent 可测试性设计与质量左移](../days/day-37-day37-agent-testability-design-shift-left.md)
  > **本篇核心要点：**  1. **可测试性是架构属性**：不可测试的 Agent 不是"测试没写好"，而是"架构没设计好"。可测试性必须在 Design Review 阶段评审，与功能需求同等优先。 2. **6 大可测试性原则**：可观…
- **Day 38** · 2026-05-23 · [每日 AI 学习笔记｜Day 38：AI Agent 线上质量巡检与生产环境验证](../days/day-38-day38-production-quality-patrol-live-validation.md)
  > **本篇核心要点：**  1. **生产环境是 AI Agent 的终极测试场**：模型漂移（Model Drift）、Prompt 注入攻击、工具 API 退化、RAG 数据腐化等问题，往往只有在真实流量下才能被暴露。离线测试无法完全覆盖…
- **Day 39** · 2026-05-24 · [每日 AI 学习笔记｜Day 39：AI Agent 事件驱动测试与可靠性工程](../days/day-39-day39-incident-driven-testing-reliability-engineering.md)
  > **本篇核心要点：**  1. **Incident-Driven Testing（IDT）核心理念**：每个 P0/P1 事故必须在 48h 内产出至少一条自动化回归用例，确保"同类故障不二犯"。IDT 是将 Postmortem 的 A…
- **Day 40** · 2026-05-25 · [每日 AI 学习笔记｜Day 40：AI Agent 端到端测试编排与流水线集成](../days/day-40-day40-e2e-test-orchestration-cicd-pipeline.md)
  > **本篇核心要点：**  1. **E2E 测试编排的核心挑战**：AI Agent E2E 测试面临三大难题——非确定性输出（同一输入不同结果）、长链路依赖（模型→编排→工具→存储）、执行时间不可控（模型推理延迟波动大）。编排策略必须针对…
- **Day 41** · 2026-05-26 · [每日 AI 学习笔记｜Day 41：AI Agent 灾备演练与恢复测试](../days/day-41-day41-agent-disaster-recovery-drills.md)
  > **推荐分层：**  1. **控制面灾备**：Agent 编排服务、路由配置、模型网关、任务调度器故障后，能否快速切换到备用实例或备用区域。 2. **数据面灾备**：Memory、向量库、缓存、任务状态存储异常时，是否支持只读、降级、重…