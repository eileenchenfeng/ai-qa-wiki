# Day 63｜每日 AI 学习笔记｜Day 63：AI Agent 事件溯源、审计日志与可重放测试

- 📅 日期：2026-06-17
- 🏷️ 标签：learning-notes, AI, QA, Agent, event-sourcing, audit-log, replay-testing, reliability, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-17-day63-agent-event-sourcing-audit-log-replay-testing.md`](../../raw/2026-06-17-day63-agent-event-sourcing-audit-log-replay-testing.md)

## 核心总结

当 AI Agent 进入企业级生产环境后，“结果对不对”已经不够，团队还必须回答：**这个结果是怎么来的、用了哪些输入、调用了哪些工具、谁授权了、失败后能不能复盘、线上事故能不能用同一批事件重放出来**。事件溯源与审计日志的价值，不只是为了合规留痕，而是把一次 Agent 执行拆成可追踪、可验证、可重放的事实流。对资深测试开发来说，今天的重点是用 **E2E 场景**验证完整链路：用户发起任务 → Agent 规划 → 工具调用 → 权限审批 → 事件写入 → 投影更新 → 审计查询 → 离线重放。Ginkgo 负责验证事件追加、状态投影与重放一致性；Python API Testing 负责校验审计查询、脱敏与完整性；Playwright 负责验证用户侧时间线和审计详情可理解；Kubernetes 演练日志落库延迟、consumer 重启、事件重复投递与投影重建。成熟的 Agent 质量体系，不只要能“跑成功”，还要能在出问题时**讲清楚、追得回、重放得出、修复得准**。

## 今日核心要点

1. 审计日志不是普通业务日志，而是不可随意改写的事实记录
2. 事件溯源的目标是用事件重建状态，而不是只保存最终状态
3. 可重放测试可以把线上事故变成稳定复现的回归资产
4. Agent 事件必须覆盖输入、计划、工具调用、权限、输出与人工干预
5. E2E 用例要验证“执行结果”和“审计证据”同时正确
6. 日志脱敏、租户隔离和访问控制必须纳入审计查询测试

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
