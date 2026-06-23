# 主题：`reliability`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
这组笔记共同聚焦 AI Agent 走向生产环境后的可靠性命题：当系统从单轮问答演进为长任务、异步回调、多模型路由与事件驱动架构时，故障形态从"答错"转向"状态不收敛、回调重复、降级不透明、链路无法复盘"，测试关注点也随之从结果正确性扩展到状态机完整性、幂等性、可重放性与 SLO 可度量性。可复用的方法栈相对收敛：Ginkgo 承担后端 E2E 与状态机/事件链路编排，Python API Testing 负责 webhook 契约、签名、去重与审计查询校验，Playwright 验证降级提示与进度时间线的用户可感知性，Chaos Mesh 与 Kubernetes 用于 consumer 重启、队列堆积、Worker 漂移等故障注入，并以发布评分卡沉淀 SLO 基线。落地建议有二：一是把"任务状态机 + 事件溯源"作为 Agent 类系统的测试基建前置项，没有清晰状态枚举与重放能力就不进入 E2E；二是 QA 应主动牵头降级透明度与审计可追溯性的验收标准，避免可靠性问题只在事故复盘时才被发现。
<!-- LLM-DRAFT:END -->

- 共 **6** 篇笔记 · 最近更新：2026-06-17

## 时间线

- **Day 24** · 2026-05-09 · [每日 AI 学习笔记｜Day 24：AI Agent 混沌工程与故障注入（Chaos Mesh + Ginkgo E2E）](../days/day-24-day24-agent-chaos-engineering.md)
- **Day 31** · 2026-05-16 · [每日 AI 学习笔记｜Day 31：AI Agent 质量 SLO 与发布评分卡](../days/day-31-day31-agent-quality-slo-scorecard.md)
- **Day 46** · 2026-05-31 · [每日 AI 学习笔记｜Day 46：AI Agent 模型路由与降级回退测试](../days/day-46-day46-agent-model-routing-fallback-testing.md)
  > AI Agent 进入生产后，最常见的线上事故往往不是“模型完全不可用”，而是 **模型路由选错、回退不及时、降级不透明**：本该走高质量模型的高风险请求被打到轻量模型，导致答案失真；主模型超时后没有及时 fallback，造成整条链路雪崩…
- **Day 50** · 2026-06-04 · [每日 AI 学习笔记｜Day 50：AI Agent 长任务执行与异步工作流可靠性测试](../days/day-50-day50-agent-long-running-async-workflow-reliability-testing.md)
  > 当 AI Agent 从“单轮即时回答”走向“分钟级 / 小时级的长任务执行”时，测试重点会从结果正确性扩展到 **任务状态机是否清晰、断点是否可恢复、重试是否幂等、异步回调是否可信、超时与取消是否可控、跨组件链路是否最终一致**。高质量测…
- **Day 62** · 2026-06-16 · [每日 AI 学习笔记｜Day 62：AI Agent 异步回调、Webhook 一致性与事件驱动可靠性测试](../days/day-62-day62-agent-async-callback-webhook-event-driven-reliability-testing.md)
  > 当 AI Agent 从“同步问答”走向“异步执行”后，很多 P0 故障就不再出在模型答错，而是出在**事件到了但状态没收敛、回调重放后副作用重复、前端展示与后端真实进度脱节、消息乱序导致状态回退**。一个真实场景里，Agent 可能先提交…
- **Day 63** · 2026-06-17 · [每日 AI 学习笔记｜Day 63：AI Agent 事件溯源、审计日志与可重放测试](../days/day-63-day63-agent-event-sourcing-audit-log-replay-testing.md)
  > 当 AI Agent 进入企业级生产环境后，“结果对不对”已经不够，团队还必须回答：**这个结果是怎么来的、用了哪些输入、调用了哪些工具、谁授权了、失败后能不能复盘、线上事故能不能用同一批事件重放出来**。事件溯源与审计日志的价值，不只是为…