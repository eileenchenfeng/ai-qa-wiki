# Day 48｜每日 AI 学习笔记｜Day 48：AI Agent 记忆机制与有状态测试

- 📅 日期：2026-06-02
- 🏷️ 标签：learning-notes, AI, QA, Agent, memory, stateful, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-02-day48-agent-memory-stateful-testing.md`](../../raw/2026-06-02-day48-agent-memory-stateful-testing.md)

## 核心总结

AI Agent 一旦引入记忆（memory）和会话状态（state），测试难度会从“单轮问答是否正确”升级为“跨轮交互是否持续正确、隔离正确、回收正确、降级正确”。真正高价值的问题通常不是某一轮答错，而是 **上一轮的上下文是否被错误继承、A 用户的历史是否污染到 B 用户、摘要压缩后是否丢失关键约束、状态恢复时是否发生重复执行**。测试上建议采用 **Ginkgo 做多轮会话 E2E 与幂等校验、Python/API 做记忆契约和故障注入、Playwright 做用户视角的历史连续性验证、K8s 做持久层与副本恢复演练** 的组合方案。核心原则：**把“记忆”当作正式数据资产，而不是临时缓存。**

## 今日核心要点

1. 记忆测试的核心不只是“记住了什么”，还包括“是否该忘、该隔离、该回滚”
2. Stateful Agent 至少要覆盖四类状态：会话历史、用户画像、工具执行中间态、外部持久化记忆
3. 高风险缺陷通常出现在跨轮场景：摘要压缩、上下文裁剪、重试补偿、会话恢复、并发写入
4. E2E 用例要按真实业务链路设计：用户建立偏好 → 发起任务 → 中断恢复 → 再次追问 → 验证结果与记忆一致
5. 记忆能力必须支持故障降级：写入失败时是否退化为无状态模式，读超时时是否给出显式提示而不是悄悄编造
6. 多租户隔离是 P0：任何跨用户、跨空间、跨会话的记忆串读都应视为严重事故

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
