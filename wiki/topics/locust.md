# 主题：`locust`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 在多步推理、工具调用和上下文累积场景下的性能与稳定性压测，核心问题是如何在传统 Web 压测模型之外，刻画 Agent 长链路、异步流式、Token 计费等非确定性负载特征。可复用的工程实践包括：以 Locust 编写带状态的 user behavior 模拟多轮对话与工具触发、用 k6 做高并发 HTTP/SSE 基线对比、对 LLM 网关侧统计 P95/P99 首 Token 延迟与端到端完成时延，并结合 FAISS 检索 QPS、上下文长度分桶、失败率与超时熔断阈值构建综合指标体系。对 QA 工作的启发是：应将"单请求成功"升级为"会话级 SLO"，在 CI 中固化一组带语义断言的压测剧本，并把 Token 消耗与重试率纳入回归基线，避免性能劣化被功能用例掩盖。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-19

## 时间线

- **Day 65** · 2026-06-19 · [每日 AI 学习笔记｜Day 65：AI Agent 性能压测实战（Locust + k6 + Agent 场景）](../days/day-65-day65-agent-load-testing-locust-k6.md)