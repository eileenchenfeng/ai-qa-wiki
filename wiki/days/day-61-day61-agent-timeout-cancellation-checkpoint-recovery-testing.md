# Day 61｜每日 AI 学习笔记｜Day 61：AI Agent 超时控制、取消传播与 Checkpoint 恢复测试

- 📅 日期：2026-06-15
- 🏷️ 标签：learning-notes, AI, QA, Agent, timeout, cancellation, checkpoint-recovery, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-15-day61-agent-timeout-cancellation-checkpoint-recovery-testing.md`](../../raw/2026-06-15-day61-agent-timeout-cancellation-checkpoint-recovery-testing.md)

## 核心总结

对 AI Agent 来说，很多高风险故障并不是“执行失败”，而是**任务该停的时候没停、该取消的时候没取消、worker 重启后不知道从哪继续**。一次长任务可能同时经历模型推理、工具调用、异步轮询、文件上传、审批回调和前端状态刷新；如果没有统一的超时预算、取消传播机制和 checkpoint 恢复点，系统就容易出现：后端已超时但第三方副作用还在继续、用户点击取消但任务仍偷偷跑完、页面提示已结束但后台还在扣资源、Pod 重启后任务重复执行。对资深测试开发来说，这类质量问题不能只靠单接口超时校验，而要从 **Ginkgo** 验证超时预算拆分、取消信号透传与恢复续跑，从 **Python / API Testing** 校验任务状态机、取消幂等与 checkpoint 元数据，从 **Playwright** 验证“运行中 / 取消中 / 已取消 / 恢复中”是否对用户真实可见，从 **Kubernetes** 演练 Pod 重启、Job 中断与恢复流程。成熟的 AI Agent 长任务质量体系，不是任务永远不停，而是系统在该停、该断、该恢复时都能做出**唯一、可追踪、可解释**的正确动作。

## 今日核心要点

1. 超时不是一个常量，而是一套从入口到子任务逐层分配的预算系统
2. 取消不是前端按钮行为，而是必须一路传播到编排层、工具层和异步 worker
3. 没有 checkpoint 的长任务恢复，本质上只能依赖重跑，风险极高
4. 最危险的不是任务失败，而是用户以为任务停了，后台却仍继续执行副作用
5. E2E 用例必须覆盖“启动 → 运行 → 超时/取消 → 恢复”完整链路，而不是只测单个 timeout 参数
6. 恢复测试的目标不是“继续跑起来”，而是验证是否从正确步骤恢复、且不重复执行已完成动作

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
