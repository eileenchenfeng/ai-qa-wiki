# 主题：`SRE`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
SRE 主题下两篇笔记共同聚焦 AI Agent 在生产环境的质量守护问题：模型漂移、Prompt 注入、工具 API 退化、RAG 数据腐化、记忆污染、多 Agent 死锁等长尾故障无法被离线测试覆盖，必须依赖线上手段持续验证并通过事故反向沉淀回归资产。可复用的方法论包括合成探针（确定性断言＋语义相似度模糊断言）、金丝雀断言式活性检测、生产 Trace 采样脱敏后在影子环境回放、持续评估流水线，以及 Incident-Driven Testing 的 Detect-Classify-Reproduce-Codify-Prevent 闭环，配合 Model/Prompt/Tool/Memory/Orchestration/Infra 六类故障 Taxonomy 标准化复现模板。对 QA 的落地启发：一是将探针与金丝雀断言接入告警体系，把"测试用例"前移为线上守护资产；二是建立 48h 内事故转回归用例的硬性 SLA，并纳入 CI Gate，确保同类故障不二犯。
<!-- LLM-DRAFT:END -->

- 共 **2** 篇笔记 · 最近更新：2026-05-24

## 时间线

- **Day 38** · 2026-05-23 · [每日 AI 学习笔记｜Day 38：AI Agent 线上质量巡检与生产环境验证](../days/day-38-day38-production-quality-patrol-live-validation.md)
  > **本篇核心要点：**  1. **生产环境是 AI Agent 的终极测试场**：模型漂移（Model Drift）、Prompt 注入攻击、工具 API 退化、RAG 数据腐化等问题，往往只有在真实流量下才能被暴露。离线测试无法完全覆盖…
- **Day 39** · 2026-05-24 · [每日 AI 学习笔记｜Day 39：AI Agent 事件驱动测试与可靠性工程](../days/day-39-day39-incident-driven-testing-reliability-engineering.md)
  > **本篇核心要点：**  1. **Incident-Driven Testing（IDT）核心理念**：每个 P0/P1 事故必须在 48h 内产出至少一条自动化回归用例，确保"同类故障不二犯"。IDT 是将 Postmortem 的 A…