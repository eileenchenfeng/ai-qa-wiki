# 主题：`experiment`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 在线上实验与 A/B 测试中的质量保障问题，核心矛盾在于一次 Prompt 或策略变更往往会同时牵动工具调用路径、拒绝边界、副作用、时延与 Token 成本，传统"看转化率"式的实验思路无法覆盖 Agent 系统的安全与稳定性风险。可复用的实践包括：以一致性分流保障用户体验稳定，用 Ginkgo 验证实验路由与风控隔离，借助 Python/API Testing 监控指标分布与异常，使用 Playwright 串联用户视角全链路，并依托 Kubernetes 灰度发布与 Kill Switch 实现分钟级止损。对 QA 的启发是：实验评估单元应从单条回复升级为完整业务链路，并在效果指标之外强制设立护栏指标与熔断阈值，将 A/B 测试纳入可追踪、可回滚、可审计的质量系统而非单纯的效果验证手段。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-08

## 时间线

- **Day 54** · 2026-06-08 · [每日 AI 学习笔记｜Day 54：AI Agent 线上实验与 A/B 测试质量保障](../days/day-54-day54-agent-online-experiment-ab-testing-quality-guardrails.md)
  > 对 AI Agent 来说，线上实验绝不是“换个 Prompt 看看点击率会不会涨”这么简单。因为一次实验同时改变的，往往不只是文案表现，还可能连带影响 **工具调用路径、拒绝边界、任务副作用、时延、Token 成本、用户信任和安全风险**…