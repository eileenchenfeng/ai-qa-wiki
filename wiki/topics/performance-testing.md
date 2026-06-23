# 主题：`performance-testing`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 在多轮对话、工具调用与 RAG 链路下的性能压测难题：传统接口压测无法覆盖 Token 流式返回、上下文累积与外部依赖（向量库、LLM API）带来的长尾延迟与成本波动。可复用的方法包括以 Locust 编写有状态的 Agent 会话脚本、用 k6 进行高并发流式 SSE 压测，并将 TTFT、tokens/s、P95 端到端延迟、工具调用失败率与单请求成本纳入统一指标口径；配合 FAISS / pgvector 检索耗时分桶、Prometheus + Grafana 看板与混沌注入（限流、超时、降级）形成闭环。对 QA 的启发是：应尽早建立 Agent 专属的性能基线与回归门禁，将 Token 成本视为与延迟同权重的 SLO 指标，避免上线后被长上下文与工具链放大效应反噬。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-19

## 时间线

- **Day 65** · 2026-06-19 · [每日 AI 学习笔记｜Day 65：AI Agent 性能压测实战（Locust + k6 + Agent 场景）](../days/day-65-day65-agent-load-testing-locust-k6.md)