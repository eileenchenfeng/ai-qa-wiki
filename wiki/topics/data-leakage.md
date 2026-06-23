# 主题：`data-leakage`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦大模型应用中数据泄露风险的识别与防控，核心问题是如何在 Prompt 注入、越权访问与上下文回流等场景下，验证模型与检索链路是否会外泄系统提示词、用户隐私或向量库中的敏感片段。可复用的测试方法包括：构造对抗性 Prompt 用例集（含越狱、角色扮演、间接注入）跑回归，结合 Playwright 端到端模拟用户多轮诱导，使用 Ginkgo 组织分层断言，并在 RAG 链路上对 FAISS / Milvus 召回结果做敏感字段命中校验与 PII 正则扫描，同时引入 LLM-as-Judge 对响应内容做泄露评分。对 QA 工作的启发是：一方面应将数据泄露用例沉淀为独立的安全测试套件并纳入每次模型或 Prompt 变更的准入流水线，另一方面建议在测试环境预埋 Canary 敏感数据，通过日志与响应双向监控量化泄露率，形成可追踪的安全质量指标。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-22

## 时间线

- **Day 68** · 2026-06-22 · [每日 AI 学习笔记｜Day 68：AI 安全测试（Prompt Injection / 越权 / 数据泄露）](../days/day-68-day68-agent-security-testing-prompt-injection-data-leakage.md)