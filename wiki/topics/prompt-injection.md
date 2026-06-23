# 主题：`prompt-injection`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
这两篇笔记共同聚焦于 AI Agent 时代的安全测试范式迁移，核心议题是如何在 Prompt Injection、工具越权调用、记忆污染、敏感信息外泄与跨租户数据串读等复合风险下，验证模型与 Agent 是否始终在被授权的能力边界内行动，而非仅评估输出正确性。可复用的工程实践包括：以输入防护、决策约束、执行鉴权、结果审计、红队评测构成五层护栏，并通过 Ginkgo 编排后端越权与 API 契约用例、Playwright 覆盖前端高风险交互、K8s 命名空间与 RBAC 做租户隔离、注入语料库做回归扫描，形成攻防闭环。对 QA 的启发是：应把红队 Prompt 与越权用例沉淀为持续运行的安全门禁，纳入 CI 强制卡点；同时在测试设计阶段前置威胁建模，按"能力边界—攻击路径—审计证据"三段式补齐用例，避免安全验证滞后于 Agent 能力扩张。
<!-- LLM-DRAFT:END -->

- 共 **2** 篇笔记 · 最近更新：2026-06-22

## 时间线

- **Day 43** · 2026-05-28 · [每日 AI 学习笔记｜Day 43：AI Agent 安全攻防测试与越权防护](../days/day-43-day43-agent-security-red-teaming-guardrails.md)
  > AI Agent 的安全问题，已经不只是传统 Web 的“鉴权 + 漏洞扫描”，而是 **Prompt Injection、工具越权、记忆污染、敏感信息外泄、跨租户数据串读、危险动作误执行** 叠加形成的新型复合风险。测试侧不能只验证“答得…
- **Day 68** · 2026-06-22 · [每日 AI 学习笔记｜Day 68：AI 安全测试（Prompt Injection / 越权 / 数据泄露）](../days/day-68-day68-agent-security-testing-prompt-injection-data-leakage.md)