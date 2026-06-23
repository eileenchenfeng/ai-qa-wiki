# Day 63｜每日 AI 学习笔记｜Day 63：AI Agent 事件溯源、审计链路与可重放回归测试

- 📅 日期：2026-06-18
- 🏷️ 标签：learning-notes, AI, QA, Agent, event-sourcing, audit, replay, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-18-day63-agent-event-sourcing-audit-replay-testing.md`](../../raw/2026-06-18-day63-agent-event-sourcing-audit-replay-testing.md)

## 核心总结

当 AI Agent 开始具备规划、工具调用、异步回调、补偿恢复与跨系统写操作能力后，很多最难排查的线上问题就不再是“接口报错了”，而是**系统到底经历了什么、谁在什么时候推进了状态、为什么用户看到的结果和后台事实不一致**。这时，真正能支撑质量闭环的，不只是日志多打一行，而是建立**事件溯源（Event Sourcing）+ 审计链路（Audit Trail）+ 可重放回归（Replay Testing）**能力：让每一次任务启动、状态迁移、工具执行、外部回调、补偿动作都留下可追踪事件；让测试可以从这些事件里验证顺序、幂等、租户隔离和状态一致性；让故障复盘不再靠猜，而是能把历史执行链路重新回放成 E2E 场景。对资深测试开发来说，这意味着要用 **Ginkgo** 验证完整任务生命周期的事件序列与最终状态，用 **Python / API Testing** 校验事件查询接口、审计过滤和重放接口，用 **Playwright** 验证用户侧时间线与后端事实一致，用 **Kubernetes** 演练事件消费者重启、消息回放和审计链路补齐。成熟的 AI Agent 质量体系，不只是“当下跑通”，而是**事后可解释、事中可观测、事后还能稳定重放复现**。

## 今日核心要点

1. 没有事件溯源，很多 Agent 故障只能靠日志猜，无法形成稳定回归
2. 审计链路的目标不是记录“做过”，而是记录“谁在什么上下文里做了什么”
3. 可重放测试不是简单重试接口，而是基于历史事件序列重建完整业务链路
4. E2E 用例必须覆盖“用户触发 → 事件生成 → 状态推进 → 审计可见 → 回放复现”完整闭环
5. 事件顺序、幂等键、租户标识、版本号，是审计可信度和回放正确性的关键字段
6. 用户界面中的时间线、任务状态页、通知记录，必须和后端审计事实一致

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
