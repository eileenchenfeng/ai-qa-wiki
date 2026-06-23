# Day 45｜每日 AI 学习笔记｜Day 45：AI Agent 委托授权与最小权限测试

- 📅 日期：2026-05-30
- 🏷️ 标签：learning-notes, AI, QA, Agent, authorization, least-privilege, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-05-30-day45-agent-delegated-authorization-least-privilege-testing.md`](../../raw/2026-05-30-day45-agent-delegated-authorization-least-privilege-testing.md)

## 核心总结

AI Agent 一旦具备“代替用户调用工具、查询数据、执行动作”的能力，最危险的质量缺陷就不再只是回答不准，而是 **权限代理失真**：用户只有读权限，Agent 却借系统身份拿到了写能力；用户只能看摘要，Agent 却通过检索链路拿到了原始明细；高风险动作本该审批，Agent 却直接绕过门禁执行。测试侧必须把 **用户身份透传、作用域约束、最小权限裁剪、审批门禁、执行审计** 做成可自动化验证的 E2E 质量基线。落地上建议采用 **Ginkgo 后端授权链路校验 + Python/API 策略契约测试 + Playwright 前端审批与告知验证 + K8s 工作负载身份隔离** 的组合方式。核心原则：**永远验证 Agent 是否真正以“用户被允许的最小权限”在行动，而不是以“系统能做到的最大权限”在行动。**

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
