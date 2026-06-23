# 主题：`synthetic-monitoring`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
这两篇笔记共同聚焦 AI Agent 在生产环境下的质量守护问题：模型漂移、Prompt 注入、工具 API 退化、RAG 数据腐化、拒答策略偏移与异步链路丢失等长尾故障，往往无法被离线评测覆盖，必须在真实流量入口侧持续探测。可复用的方法论包括以合成探针覆盖黄金路径、对每条 Query 同时设置确定性断言（工具调用序列、结构化字段）与模糊断言（语义相似度阈值）、金丝雀断言做活性检测、生产 Trace 采样后在影子环境回放，并配套 Ginkgo 校验工具轨迹、Playwright 验证前端可见状态、Python/API Testing 做探针编排与指标聚合、Kubernetes CronJob 负责周期化与环境隔离。对 QA 的落地建议是：先把 Synthetic Monitoring 沉淀为发布门禁与故障归因的一等输入，而非孤立看板；同时为每条探针明确 owner、脱敏策略与告警阈值，避免演化成噪声源。
<!-- LLM-DRAFT:END -->

- 共 **2** 篇笔记 · 最近更新：2026-06-10

## 时间线

- **Day 38** · 2026-05-23 · [每日 AI 学习笔记｜Day 38：AI Agent 线上质量巡检与生产环境验证](../days/day-38-day38-production-quality-patrol-live-validation.md)
  > **本篇核心要点：**  1. **生产环境是 AI Agent 的终极测试场**：模型漂移（Model Drift）、Prompt 注入攻击、工具 API 退化、RAG 数据腐化等问题，往往只有在真实流量下才能被暴露。离线测试无法完全覆盖…
- **Day 56** · 2026-06-10 · [每日 AI 学习笔记｜Day 56：AI Agent 线上合成巡检与 Synthetic Monitoring 测试](../days/day-56-day56-agent-synthetic-monitoring-production-qa.md)
  > 对 AI Agent 来说，很多高风险问题不会先在接口 500、机器告警或离线评测里暴露，而是先出现在 **用户真实链路的体验退化** 上：回答开始变慢、工具调用偶发选错、拒答策略漂移、页面状态卡住、异步任务悄悄丢失。要尽早发现这类问题，不…