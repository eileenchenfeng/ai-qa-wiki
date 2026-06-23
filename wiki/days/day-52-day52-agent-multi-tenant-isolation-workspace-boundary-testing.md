# Day 52｜每日 AI 学习笔记｜Day 52：AI Agent 多租户隔离与工作空间边界测试

- 📅 日期：2026-06-06
- 🏷️ 标签：learning-notes, AI, QA, Agent, tenant-isolation, workspace-security, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-06-day52-agent-multi-tenant-isolation-workspace-boundary-testing.md`](../../raw/2026-06-06-day52-agent-multi-tenant-isolation-workspace-boundary-testing.md)

## 核心总结

当 AI Agent 从“单用户助手”升级为“团队协作平台能力”后，最容易被低估、但一旦出事就最严重的质量问题，不是回答不准，而是 **跨租户串数、跨会话串上下文、跨工作空间误执行工具、越权访问文件或记忆**。高质量测试必须把多租户安全拆成 **身份归属、资源作用域、会话隔离、工具权限、缓存边界、异步任务归属、审计留痕** 七类可验证对象，并采用 **Ginkgo 做后端隔离链路 E2E、Python / API 做鉴权契约与越权回归、Playwright 做用户视角的工作空间切换验证、K8s 做缓存漂移与多副本一致性演练** 的组合方案。核心原则：**不是验证“用户能不能访问自己的数据”，而是验证“任何时候都绝不能访问到别人的数据”。**

## 今日核心要点

1. 多租户测试的核心不是“账号 A 无法看到账号 B 页面”，而是“任意系统层都不能混淆资源归属”
2. 隔离边界必须结构化建模：tenant_id、workspace_id、session_id、resource_owner、tool_scope、memory_namespace、task_owner 缺一不可
3. 缓存、异步任务、重试恢复、搜索召回是最容易漏测的串租户高风险点
4. E2E 用例必须围绕完整链路组织：用户在租户 A 发起任务 → Agent 调工具 / 读记忆 / 读文件 / 写结果 → 切换到租户 B 验证不可见且不可操作
5. 前端展示正确不等于真正隔离：后端检索、对象存储路径、队列消费者、审计日志都必须验证归属一致性
6. 没有审计与告警的隔离能力，不算可上线的隔离能力

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
