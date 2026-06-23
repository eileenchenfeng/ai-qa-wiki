# 主题：`observability`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
这组笔记围绕 AI Agent 全链路可观测性展开，核心问题是如何让一个由 LLM 推理、工具调用、异步任务和前端交互拼接而成的非确定性系统变得"可被看见、可被解释、可被归因"，覆盖从 OpenTelemetry Trace 埋点、失败分诊与质量看板，到决策审计、合成巡检的完整闭环。跨笔记可复用的方法论已较为收敛：以 OpenTelemetry 统一 Trace/Span 语义并贯穿工具调用链，用 Ginkgo 守护推理轨迹与工具调用顺序的 E2E 正确性，用 Python/API 测试承担指标聚合、契约校验与告警阈值，用 Playwright 验证前端可见状态与可解释性 UI，用 K8s CronJob 承载周期化合成探针与审计日志可靠性校验。对 QA 的启发是：测试断言应从"输出文本对不对"前移到"推理链路、工具轨迹、审计记录是否完整可复盘"，并把合成巡检结果直接接入发布门禁，让线上质量信号在真实用户受损前触发拦截。
<!-- LLM-DRAFT:END -->

- 共 **6** 篇笔记 · 最近更新：2026-06-20

## 时间线

- **Day 23** · 2026-05-08 · [每日 AI 学习笔记｜Day 23：可观测性与链路追踪（OpenTelemetry + Trace）](../days/day-23-day23-agent-observability-and-tracing.md)
- **Day 30** · 2026-05-15 · [每日 AI 学习笔记｜Day 30：AI Agent 失败归因与自动化分诊](../days/day-30-day30-agent-failure-attribution-and-auto-triage.md)
- **Day 32** · 2026-05-17 · [每日 AI 学习笔记｜Day 32：AI Agent 质量看板与持续监控](../days/day-32-day32-agent-quality-dashboard-monitoring.md)
- **Day 47** · 2026-06-01 · [每日 AI 学习笔记｜Day 47：AI Agent 可解释性与决策审计测试](../days/day-47-day47-agent-explainability-audit-testing.md)
  > 当 AI Agent 进入企业关键业务后，"模型为什么这么回答" 比 "答得对不对" 更重要。没有可解释性与决策审计，就很难回答三件事：**这个决策是谁做的（人/Agent/工具/外部系统）？是基于什么输入做的？如果出事故，能否完整复盘并给…
- **Day 56** · 2026-06-10 · [每日 AI 学习笔记｜Day 56：AI Agent 线上合成巡检与 Synthetic Monitoring 测试](../days/day-56-day56-agent-synthetic-monitoring-production-qa.md)
  > 对 AI Agent 来说，很多高风险问题不会先在接口 500、机器告警或离线评测里暴露，而是先出现在 **用户真实链路的体验退化** 上：回答开始变慢、工具调用偶发选错、拒答策略漂移、页面状态卡住、异步任务悄悄丢失。要尽早发现这类问题，不…
- **Day 66** · 2026-06-20 · [每日 AI 学习笔记｜Day 66：AI Agent 可观测性与链路追踪（OpenTelemetry + Trace）](../days/day-66-day66-agent-observability-opentelemetry-tracing.md)