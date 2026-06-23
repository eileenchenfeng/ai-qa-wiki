# Day 46｜每日 AI 学习笔记｜Day 46：AI Agent 模型路由与降级回退测试

- 📅 日期：2026-05-31
- 🏷️ 标签：learning-notes, AI, QA, Agent, routing, fallback, reliability, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-05-31-day46-agent-model-routing-fallback-testing.md`](../../raw/2026-05-31-day46-agent-model-routing-fallback-testing.md)

## 核心总结

AI Agent 进入生产后，最常见的线上事故往往不是“模型完全不可用”，而是 **模型路由选错、回退不及时、降级不透明**：本该走高质量模型的高风险请求被打到轻量模型，导致答案失真；主模型超时后没有及时 fallback，造成整条链路雪崩；系统虽然触发了降级，但前端和日志都没有把真实决策暴露出来，结果排障困难、用户体验也失控。测试侧要把 **路由规则正确性、fallback 成功率、降级透明度、熔断隔离能力、成本与时延平衡** 一起纳入 E2E 质量基线。落地上建议采用 **Ginkgo 后端编排链路验证 + Python/API 路由契约测试 + Playwright 前端降级告知验证 + K8s 配置灰度与熔断演练** 的组合方案。核心原则：**不仅要验证“有没有答案”，更要验证“系统为什么选这个模型、失败后如何退、退完后用户是否可感知且可追溯”。**

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
