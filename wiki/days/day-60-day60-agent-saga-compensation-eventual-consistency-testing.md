# Day 60｜每日 AI 学习笔记｜Day 60：AI Agent 补偿事务与最终一致性测试

- 📅 日期：2026-06-14
- 🏷️ 标签：learning-notes, AI, QA, Agent, saga, compensation, eventual-consistency, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-14-day60-agent-saga-compensation-eventual-consistency-testing.md`](../../raw/2026-06-14-day60-agent-saga-compensation-eventual-consistency-testing.md)

## 核心总结

当 AI Agent 从“只会回答”升级为“会代表用户执行业务动作”后，真正高风险的质量问题就不再是某一步报错，而是**跨系统动作做了一半**：工单创建成功但通知失败、审批单已提交但会话状态仍显示处理中、知识库写入成功但审计日志缺失、回调重放导致任务重复落库。对资深测试开发来说，补偿事务与最终一致性测试的核心，不是验证“失败后能不能 retry 一下”，而是验证 **系统是否定义了可恢复边界、是否记录了可追踪状态、是否在补偿期间对用户诚实展示、是否在最终一致后收敛到唯一正确结果**。工程上要同时从 **Ginkgo** 验证 Saga 编排与补偿顺序、从 **Python / API Testing** 校验状态机和幂等键、从 **Playwright** 验证前端对“处理中 / 补偿中 / 已恢复”的展示、从 **Kubernetes** 演练异步 worker 崩溃与恢复。成熟的 AI Agent 质量体系，不是每一步都永远成功，而是失败发生后仍能保证：**状态可见、补偿可控、结果唯一、用户不被误导。**

## 今日核心要点

1. AI Agent 的事务问题，本质是跨系统动作无法依赖单库 ACID 事务兜底
2. 补偿不是“回滚一切”，而是按业务语义撤销已执行副作用
3. 最终一致性测试最重要的不是“最后成功了”，而是中间状态是否可见、可追踪、可恢复
4. 每个异步步骤都必须有幂等键、状态机和重试边界，否则补偿会制造二次事故
5. E2E 用例必须覆盖“部分成功 + 延迟恢复 + 前端观察”完整链路，而不是只测单接口
6. 最危险的不是系统失败，而是系统已经偏离一致性却仍向用户展示“已完成”

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
