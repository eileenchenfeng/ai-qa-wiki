# 主题：`production-patrol`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦 AI Agent 在生产环境下的持续质量保障问题，核心矛盾在于模型漂移、Prompt 注入、工具 API 退化与 RAG 索引腐化等长尾故障无法通过离线评测充分暴露，必须依赖线上手段补齐观测盲区。可复用的工程实践包括：以合成探针（Synthetic Probes）覆盖黄金路径并组合确定性断言（工具调用序列、JSON Schema 字段校验）与模糊断言（基于 embedding 的语义相似度阈值），通过金丝雀断言对已发布版本做活性巡检，利用 Trace 采样在影子环境回放脱敏流量做 diff 比对，并接入持续评估流水线；技术栈上可结合 OpenTelemetry、Langfuse、FAISS 与 Ginkgo/Pytest 组织断言集。对 QA 的启发是：将"线上巡检"纳入发布后质量基线，把探针用例与离线评测集同源管理，并为每条断言失败定义清晰的告警分级与回滚 Runbook，避免巡检沦为噪声看板。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-23

## 时间线

- **Day 38** · 2026-05-23 · [每日 AI 学习笔记｜Day 38：AI Agent 线上质量巡检与生产环境验证](../days/day-38-day38-production-quality-patrol-live-validation.md)
  > **本篇核心要点：**  1. **生产环境是 AI Agent 的终极测试场**：模型漂移（Model Drift）、Prompt 注入攻击、工具 API 退化、RAG 数据腐化等问题，往往只有在真实流量下才能被暴露。离线测试无法完全覆盖…