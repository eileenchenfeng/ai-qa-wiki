# 主题：`canary-assertion`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 在生产环境下的持续质量守护问题，核心矛盾在于离线测试无法覆盖模型漂移、Prompt 注入、工具 API 退化与 RAG 数据腐化等长尾故障，必须依赖线上态的主动探测机制来兜底。可复用的工程实践包括：以合成探针覆盖黄金路径并组合确定性断言（Tool 调用序列、结构化字段校验）与模糊断言（基于 FAISS 或 sentence-transformers 的语义相似度阈值）、在稳定版本上以 Cron 触发金丝雀断言做活性检测、通过 OpenTelemetry 采样生产 Trace 后在影子环境回放、以及搭建持续评估 Pipeline 形成递进防线。对 QA 落地的启发是：应明确区分金丝雀断言与金丝雀发布，将前者建设为独立于灰度流程的线上回归资产；同时把探针用例与离线评测集双向同步，让生产暴露的 Bad Case 反哺回归库，形成闭环。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-23

## 时间线

- **Day 38** · 2026-05-23 · [每日 AI 学习笔记｜Day 38：AI Agent 线上质量巡检与生产环境验证](../days/day-38-day38-production-quality-patrol-live-validation.md)
  > **本篇核心要点：**  1. **生产环境是 AI Agent 的终极测试场**：模型漂移（Model Drift）、Prompt 注入攻击、工具 API 退化、RAG 数据腐化等问题，往往只有在真实流量下才能被暴露。离线测试无法完全覆盖…