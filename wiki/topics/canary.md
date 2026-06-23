# 主题：`canary`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦 AI Agent 在生产环境中如何低风险上线，核心问题是如何在不影响真实用户的前提下验证新模型或新 Prompt 链路的稳定性与效果回归。跨笔记可复用的实践包括：基于流量染色的灰度切分（按用户 ID 哈希或 Header 路由）、影子流量双跑与响应 Diff 比对、关键指标（延迟、Token 消耗、工具调用成功率、答案相似度）的实时埋点，常用技术栈涉及 Istio/Envoy 做流量镜像、FAISS 或 BERTScore 做语义相似度比对、Ginkgo 编写回归用例、Prometheus + Grafana 监控漂移。对 QA 工作的启发是：应将影子流量回放纳入发布门禁，在预发环境建立离线 Diff 报告基线，并为 Agent 输出定义可量化的语义等价阈值，避免仅依赖人工抽检导致的回归遗漏。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-18

## 时间线

- **Day 33** · 2026-05-18 · [每日 AI 学习笔记｜Day 33：AI Agent 灰度发布与影子流量测试](../days/day-33-day33-canary-shadow-traffic-testing.md)