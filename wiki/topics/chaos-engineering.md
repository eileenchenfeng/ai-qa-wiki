# 主题：`chaos-engineering`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
这两篇笔记共同聚焦 AI Agent 系统在生产环境下的可靠性保障问题——前者从事后视角切入，强调以 Incident-Driven Testing 将 P0/P1 事故沉淀为自动化回归用例；后者从事前视角切入，借助 ChaosMesh 主动注入故障验证 Agent 在模型退化、Prompt 漂移、工具链断裂、记忆污染、多 Agent 死锁等场景下的韧性。可复用的工程骨架包括：基于 Detect→Classify→Reproduce→Codify→Prevent 的闭环、Agent 故障 6 大类 Taxonomy（Model/Prompt/Tool/Memory/Orchestration/Infra）、ChaosMesh 网络与 Pod 级故障注入、回归用例纳入 CI Gate，以及 FAISS 召回校验、Playwright 端到端复现等手段。对 QA 落地的启发是：一方面应建立 Postmortem 到测试代码的强制转化机制，明确 48h SLA 与 Taxonomy 标签；另一方面将混沌实验常态化嵌入预发流水线，把 Agent 韧性指标作为发布准入门槛而非可选项。
<!-- LLM-DRAFT:END -->

- 共 **2** 篇笔记 · 最近更新：2026-06-21

## 时间线

- **Day 39** · 2026-05-24 · [每日 AI 学习笔记｜Day 39：AI Agent 事件驱动测试与可靠性工程](../days/day-39-day39-incident-driven-testing-reliability-engineering.md)
  > **本篇核心要点：**  1. **Incident-Driven Testing（IDT）核心理念**：每个 P0/P1 事故必须在 48h 内产出至少一条自动化回归用例，确保"同类故障不二犯"。IDT 是将 Postmortem 的 A…
- **Day 67** · 2026-06-21 · [每日 AI 学习笔记｜Day 67：AI Agent 混沌工程（ChaosMesh 与故障注入实战）](../days/day-67-day67-agent-chaos-engineering-chaosmesh-fault-injection.md)