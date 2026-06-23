# 主题：`tracing`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题三篇笔记共同聚焦 AI Agent 全链路可观测性问题：在入口、编排、模型、工具、状态、前端等多层异步协作的系统里，单看接口返回往往看不出问题，必须借助统一 Trace 还原"哪里先偏了"。可复用的工程骨架是以 OpenTelemetry 贯穿 trace_id / span，将 Prompt 路由、检索召回、工具调用参数、状态机推进、前端渲染态串成同一条时间线，再用 Ginkgo 固化后端轨迹断言、用 Python 做日志拼装与根因聚合、用 Playwright 验证用户可见态与后端事实一致、用 Kubernetes 保证脏样本可隔离复现。对 QA 的落地启发是：测试用例的断言对象应从"最终输出"前移到"关键 span 属性"，把每一次线上故障的 trace 沉淀为可回放的回归样本，让链路追踪而非事后看日志成为 AI 系统质量定位的默认入口。
<!-- LLM-DRAFT:END -->

- 共 **3** 篇笔记 · 最近更新：2026-06-20

## 时间线

- **Day 23** · 2026-05-08 · [每日 AI 学习笔记｜Day 23：可观测性与链路追踪（OpenTelemetry + Trace）](../days/day-23-day23-agent-observability-and-tracing.md)
- **Day 57** · 2026-06-11 · [每日 AI 学习笔记｜Day 57：AI Agent Trace 驱动故障定位与分层调试体系](../days/day-57-day57-agent-trace-driven-debugging-and-root-cause-analysis.md)
  > AI Agent 最难排查的问题，往往不是“接口直接报错”，而是 **最终答案看起来勉强可用，但中间某一层已经悄悄偏离预期**：可能是 Prompt 路由错了、检索召回脏了、工具参数缺字段、状态机重复推进、前端把错误态伪装成加载中，或者异步…
- **Day 66** · 2026-06-20 · [每日 AI 学习笔记｜Day 66：AI Agent 可观测性与链路追踪（OpenTelemetry + Trace）](../days/day-66-day66-agent-observability-opentelemetry-tracing.md)