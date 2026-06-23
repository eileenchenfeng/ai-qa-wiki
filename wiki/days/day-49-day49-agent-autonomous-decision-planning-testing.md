# Day 49｜每日 AI 学习笔记｜Day 49：AI Agent 自主决策与规划测试

- 📅 日期：2026-06-03
- 🏷️ 标签：learning-notes, AI, QA, Agent, decision-making, planning, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-03-day49-agent-autonomous-decision-planning-testing.md`](../../raw/2026-06-03-day49-agent-autonomous-decision-planning-testing.md)

## 核心总结

当 AI Agent 开始自己做“下一步该做什么”的判断时，测试目标就不再只是答案对不对，而是 **决策路径是否可解释、规划步骤是否收敛、失败后是否会重规划、越权动作是否被拦住、最终副作用是否可控**。高质量测试应把“自主决策”拆成 **目标理解、约束继承、工具选择、计划生成、执行反馈、动态重规划、最终止损** 七个可验证环节，并采用 **Ginkgo 做后端决策链路 E2E、Python / API 做计划契约与故障注入、Playwright 做用户视角的计划透明性验证、K8s 做多副本与发布门禁演练** 的组合方案。核心原则：**不是验证 Agent 会不会“想”，而是验证它会不会在边界内稳定地“做决定”。**

## 今日核心要点

1. 自主决策测试的核心是“过程正确”而不只是“结果看似正确”
2. 决策链至少要覆盖七层对象：目标、约束、计划、工具选择、执行反馈、重规划、止损策略
3. 高风险缺陷通常出现在动态分支：工具失败、信息不足、权限不足、部分成功、长链路超时
4. E2E 用例应围绕真实业务链路设计：用户下达复杂目标 → Agent 生成计划 → 中途遇阻 → 自动调整策略 → 最终在边界内完成或显式终止
5. 可解释性是测试抓手：如果系统无法暴露 plan、action、observation、decision reason，很多问题就只能靠猜
6. 越权与误执行是 P0：任何未经确认的高风险动作、越过审批的执行、错误环境写入，都应按严重事故处理

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
