# 主题：`MultiAgent`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于多 Agent 协作系统的可测性与质量评估，核心问题是如何在角色分工、消息传递与共享上下文的复杂拓扑下，验证协作链路的正确性、稳定性与性能边界，并将单 Agent 时代的测试经验迁移到群体智能场景。跨笔记可复用的实践包括：以 Ginkgo 组织行为驱动用例覆盖 Planner-Worker-Critic 等协作模式，结合 Playwright 驱动端到端交互回放，借助 FAISS 对共享记忆与检索结果做语义断言，并通过性能基线、负载压测与可观测性指标（trace、token、延迟）形成闭环。对 QA 工作的启发是：一方面应建立 Agent 间通信契约与消息 schema 校验，将“协作失败”从模糊的输出问题前移为可定位的链路问题；另一方面建议沉淀一套可回放的多 Agent 场景集，作为回归与性能基线的统一入口。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-05

## 时间线

- **Day 20** · 2026-05-05 · [每日 AI 学习笔记｜Day 20：多 Agent 协作测试](../days/day-20-day20-multi-agent-collaboration-testing.md)