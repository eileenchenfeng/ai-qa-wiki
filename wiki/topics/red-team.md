# 主题：`red-team`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于大模型应用的红队视角安全测试，核心问题是如何系统性识别 Prompt Injection、越权访问与敏感数据泄露三类典型风险，并将其纳入可回归的工程化流程。可复用的方法包括：构建对抗 Prompt 用例库（直接注入、间接注入、越狱模板、角色劫持）并通过 Ginkgo 组织分级断言、对 RAG 链路的检索结果做来源白名单与权限标签校验、利用 Playwright 模拟多租户会话验证越权边界、在向量库（FAISS / pgvector）侧对召回内容做 PII 与机密关键词扫描、以 LLM-as-Judge 加正则双通道判定输出是否泄露 system prompt 或上下文。落地建议是将红队用例固化为 CI 中的安全回归集，每次 Prompt 或检索策略变更均触发对抗测试；同时建立越权与泄露事件的语义化指标，纳入质量门禁而非仅做一次性渗透。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-22

## 时间线

- **Day 68** · 2026-06-22 · [每日 AI 学习笔记｜Day 68：AI 安全测试（Prompt Injection / 越权 / 数据泄露）](../days/day-68-day68-agent-security-testing-prompt-injection-data-leakage.md)