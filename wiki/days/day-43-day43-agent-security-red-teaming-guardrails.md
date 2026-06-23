# Day 43｜每日 AI 学习笔记｜Day 43：AI Agent 安全攻防测试与越权防护

- 📅 日期：2026-05-28
- 🏷️ 标签：learning-notes, AI, QA, Agent, security, red-teaming, prompt-injection, Ginkgo, Playwright, Kubernetes
- 📄 原文：[`raw/2026-05-28-day43-agent-security-red-teaming-guardrails.md`](../../raw/2026-05-28-day43-agent-security-red-teaming-guardrails.md)

## 核心总结

AI Agent 的安全问题，已经不只是传统 Web 的“鉴权 + 漏洞扫描”，而是 **Prompt Injection、工具越权、记忆污染、敏感信息外泄、跨租户数据串读、危险动作误执行** 叠加形成的新型复合风险。测试侧不能只验证“答得对不对”，还要验证 **它是否只在被允许的边界内行动**。工程上建议建立 **输入防护、决策约束、执行鉴权、结果审计、持续红队评测** 五层安全护栏；自动化上通过 **Ginkgo 后端 E2E 越权校验 + Python/API 契约校验 + Playwright 前端高风险交互验证 + K8s 隔离策略** 形成完整闭环。核心原则：**先限制能力边界，再验证攻击路径，最后把安全回归做成持续门禁。**

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
