# 主题：`agent`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题下的四篇笔记围绕 AI Agent 上线前后的质量保障展开，核心问题集中在如何对一个非确定性、多跳调用、依赖外部工具与模型的系统进行性能、可观测性、韧性与安全四个维度的工程化验证。可复用的方法栈较为清晰：性能侧用 Locust 与 k6 构造多轮对话与工具调用混合场景，关注 TTFT、tokens/s 与并发下的尾延迟；可观测性侧以 OpenTelemetry 串联 LLM 调用、Tool 调用与向量检索（如 FAISS）的 Trace，沉淀 span 级指标；韧性侧用 ChaosMesh 注入网络延迟、依赖中断与模型超时，验证降级与重试策略；安全侧覆盖 Prompt Injection、越权访问与数据泄露的用例集。对 QA 的启发是，应尽早把 Agent 当作分布式系统而非单接口看待，建立"压测—追踪—混沌—红队"一体化流水线，并将 Trace ID 贯穿用例与缺陷单，使非确定性失败可复现、可归因。
<!-- LLM-DRAFT:END -->

- 共 **4** 篇笔记 · 最近更新：2026-06-22

## 时间线

- **Day 65** · 2026-06-19 · [每日 AI 学习笔记｜Day 65：AI Agent 性能压测实战（Locust + k6 + Agent 场景）](../days/day-65-day65-agent-load-testing-locust-k6.md)
- **Day 66** · 2026-06-20 · [每日 AI 学习笔记｜Day 66：AI Agent 可观测性与链路追踪（OpenTelemetry + Trace）](../days/day-66-day66-agent-observability-opentelemetry-tracing.md)
- **Day 67** · 2026-06-21 · [每日 AI 学习笔记｜Day 67：AI Agent 混沌工程（ChaosMesh 与故障注入实战）](../days/day-67-day67-agent-chaos-engineering-chaosmesh-fault-injection.md)
- **Day 68** · 2026-06-22 · [每日 AI 学习笔记｜Day 68：AI 安全测试（Prompt Injection / 越权 / 数据泄露）](../days/day-68-day68-agent-security-testing-prompt-injection-data-leakage.md)