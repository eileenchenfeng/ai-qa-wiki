# Day 51｜每日 AI 学习笔记｜Day 51：AI Agent 人机协同与人工接管（Human-in-the-Loop）测试

- 📅 日期：2026-06-05
- 🏷️ 标签：learning-notes, AI, QA, Agent, human-in-the-loop, approval, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-05-day51-agent-human-in-the-loop-approval-testing.md`](../../raw/2026-06-05-day51-agent-human-in-the-loop-approval-testing.md)

## 核心总结

当 AI Agent 从“给建议”走向“可执行动作”时，真正决定系统能否上线的，往往不是它会不会自动化，而是 **它能否在该停下来的时候停下来、把足够上下文交给人、在人做出决定后稳定续跑且不产生额外副作用**。高质量测试应把 Human-in-the-Loop 能力拆成 **风险识别、审批挂起、证据快照、审批人校验、人工接管、结果回传、任务续跑、审计留痕** 八个可验证环节，并采用 **Ginkgo 做后端审批链路 E2E、Python / API 做审批契约与过期/幂等校验、Playwright 做用户视角的人工接管体验验证、K8s 做审批服务高可用与恢复演练** 的组合方案。核心原则：**不是验证“人有没有参与”，而是验证 Agent 是否把“该由人决策的部分”真正交还给人。**

## 今日核心要点

1. Human-in-the-Loop 测试的核心不是“多了一个确认按钮”，而是“决策权是否真的回到了人手里”
2. 审批对象必须结构化：审批人、风险摘要、证据快照、待执行动作、超时时间、幂等键，都应显式暴露
3. 过期审批、错人审批、重复审批、上下文漂移是 P0 风险
4. E2E 用例应围绕完整业务链路组织：用户发起任务 → Agent 自动完成低风险步骤 → 遇到高风险动作挂起 → 人工审阅并决策 → 系统从正确断点继续或终止
5. 人工接管不是纯后端逻辑：前端是否展示足够上下文、刷新后是否能恢复、审批结论是否可追溯，都会直接影响线上可运维性
6. 没有审计留痕的 HITL，不算真正可上线的 HITL

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
