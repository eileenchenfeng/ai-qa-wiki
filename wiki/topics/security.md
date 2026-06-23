# 主题：`security`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦 AI Agent 区别于传统 Web 的新型复合安全风险，核心覆盖 Prompt Injection、工具越权、记忆污染、跨租户数据串读、敏感信息外泄与危险动作误执行等攻击面，强调测试目标需从"答得对不对"转向"是否仅在授权边界内行动"。跨笔记可复用的工程实践包括五层安全护栏（输入防护、决策约束、执行鉴权、结果审计、持续红队评测），以及 Ginkgo 驱动的后端 E2E 越权校验、Python/API 契约校验、Playwright 前端高风险交互验证、K8s 命名空间隔离策略，构成攻防闭环。落地建议有二：一是把红队用例（注入语料、越权路径、数据泄露探针）沉淀为可回归的安全测试集并接入 CI 门禁，避免一次性演练；二是优先以最小权限收敛工具与数据访问边界，再围绕该边界设计攻击用例，让 QA 从被动验证转为主动的风险建模者。
<!-- LLM-DRAFT:END -->

- 共 **3** 篇笔记 · 最近更新：2026-06-22

## 时间线

- **Day 28** · 2026-05-13 · [每日 AI 学习笔记｜Day 28：AI Agent 安全测试的端到端防线设计](../days/day-28-day28-ai-agent-security-e2e-guardrails.md)
- **Day 43** · 2026-05-28 · [每日 AI 学习笔记｜Day 43：AI Agent 安全攻防测试与越权防护](../days/day-43-day43-agent-security-red-teaming-guardrails.md)
  > AI Agent 的安全问题，已经不只是传统 Web 的“鉴权 + 漏洞扫描”，而是 **Prompt Injection、工具越权、记忆污染、敏感信息外泄、跨租户数据串读、危险动作误执行** 叠加形成的新型复合风险。测试侧不能只验证“答得…
- **Day 68** · 2026-06-22 · [每日 AI 学习笔记｜Day 68：AI 安全测试（Prompt Injection / 越权 / 数据泄露）](../days/day-68-day68-agent-security-testing-prompt-injection-data-leakage.md)