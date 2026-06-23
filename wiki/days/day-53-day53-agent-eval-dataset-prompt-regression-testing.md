# Day 53｜每日 AI 学习笔记｜Day 53：AI Agent 评测集设计与 Prompt 回归测试

- 📅 日期：2026-06-07
- 🏷️ 标签：learning-notes, AI, QA, Agent, eval, prompt-regression, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-07-day53-agent-eval-dataset-prompt-regression-testing.md`](../../raw/2026-06-07-day53-agent-eval-dataset-prompt-regression-testing.md)

## 核心总结

对 AI Agent 来说，最危险的发布风险往往不是“功能挂了”，而是 **模型版本、系统提示词、工具描述、检索策略、记忆策略中任一项轻微变更后，系统表面还能回答，但行为边界已经悄悄漂移**。高质量测试必须把评测能力做成一套可持续回归的工程系统：用 **评测集（Eval Set）** 固化关键业务场景，用 **基线答案 / 结构化断言 / 工具轨迹断言 / LLM-as-Judge 辅助判分** 共同定义通过标准，再通过 **Ginkgo 做后端回归门禁、Python 做批量评测执行与指标聚合、Playwright 做用户视角 E2E 验证、K8s / CI 做每日自动巡检**。核心原则：**不是验证“这次回答看起来不错”，而是验证“任何一次变更后，核心场景都没有退化、边界都没有漂移、代价都在预算内”。**

## 今日核心要点

1. AI Agent 回归测试的核心不是“答案像不像”，而是“关键行为是否稳定可控”
2. 评测集必须覆盖真实业务链路：用户目标、上下文、工具、知识、权限、预期结果与拒绝边界都要被显式建模
3. 单一打分方式不够可靠：结构化断言、工具轨迹断言、规则打分与 LLM-as-Judge 应组合使用
4. Prompt 变更不只是文本变更：它本质上是一次行为策略发布，必须走回归门禁
5. 高价值场景优先纳入 Golden Set：高频、高风险、高投诉、高成本场景必须先固化
6. 没有趋势视图的 Eval，不是真正可运营的 Eval：必须持续跟踪通过率、漂移率、成本、时延与失败类型分布

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
