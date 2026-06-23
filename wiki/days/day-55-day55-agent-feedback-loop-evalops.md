# Day 55｜每日 AI 学习笔记｜Day 55：AI Agent 线上反馈闭环与 EvalOps 测试体系

- 📅 日期：2026-06-09
- 🏷️ 标签：learning-notes, AI, QA, Agent, EvalOps, feedback-loop, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-09-day55-agent-feedback-loop-evalops.md`](../../raw/2026-06-09-day55-agent-feedback-loop-evalops.md)

## 核心总结

AI Agent 的质量建设，真正难的不是“离线评测做一套”，而是如何把 **线上真实失败、人工纠正、用户反馈、轨迹日志和事故复盘** 持续回灌成可执行的评测集、回归集与发布门禁。一个成熟的 EvalOps 体系，本质上是把 **线上问题 → 标准样本 → 自动评测 → 回归门禁 → 发布决策 → 再次观测** 串成闭环。对测试开发来说，重点不是单次评测分数，而是构建一条 **可沉淀、可复跑、可归因、可分级、可阻断上线** 的工程链路：用 **Ginkgo** 守住 P0 回归与工具调用正确性，用 **Python / API Testing** 负责样本治理与指标聚合，用 **Playwright** 补齐用户视角体验闭环，用 **Kubernetes CronJob / Job** 跑周期化回归与线上回灌。核心判断标准只有一个：**今天线上踩过的坑，明天不能再以同样方式重来一次。**

## 今日核心要点

1. 线上反馈不是复盘材料，而是下一轮评测集的输入
2. EvalOps 的最小闭环是：发现问题、标准化样本、自动评测、阻断回归、持续观测
3. 样本治理比模型打分更重要：没有标签、分层、优先级和归因字段，评测集很快会失真
4. 评测必须分层：离线语义评测、接口契约评测、工具轨迹评测、E2E 用户体验评测缺一不可
5. P0 样本必须强门禁：一旦线上事故进入 P0 回归集，新版本发布前必须 100% 通过
6. 闭环的目标不是提高平均分，而是持续压缩“重复犯错率”

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
