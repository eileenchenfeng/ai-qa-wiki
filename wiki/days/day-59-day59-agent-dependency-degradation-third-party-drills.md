# Day 59｜每日 AI 学习笔记｜Day 59：AI Agent 外部依赖降级与第三方故障演练

- 📅 日期：2026-06-13
- 🏷️ 标签：learning-notes, AI, QA, Agent, resilience, dependency-failure, degradation, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-13-day59-agent-dependency-degradation-third-party-drills.md`](../../raw/2026-06-13-day59-agent-dependency-degradation-third-party-drills.md)

## 核心总结

AI Agent 真正难测的地方，往往不在主流程本身，而在它高度依赖外部世界：模型网关、向量检索、工作流引擎、审批系统、对象存储、Webhook、搜索服务，任何一个依赖抖动、限流、慢响应、半失败，都会沿着编排链路被放大成“回答慢”“工具失效”“页面一直转圈”“重复执行副作用”等用户可感知事故。对资深测试开发来说，质量目标不能停留在“依赖挂了系统也报错”，而要验证 **系统是否识别了故障、是否按预期降级、是否避免副作用扩散、是否向用户诚实暴露当前能力边界**：用 **Ginkgo** 断言后端编排在第三方超时/429/5xx 下的降级路径与幂等行为，用 **Python / API Testing** 做依赖契约探测和熔断状态校验，用 **Playwright** 验证页面在降级模式下的提示、按钮可见性和结果一致性，用 **Kubernetes** 注入故障并定时演练恢复。稳定的 AI 质量体系，不是依赖永远不出错，而是依赖出错时系统仍能回答：**现在降到了哪一层、哪些能力已关闭、用户还能安全完成什么。**

## 今日核心要点

1. AI Agent 的大多数严重事故，本质都是依赖故障被编排层放大
2. 降级不是简单兜底文案，而是要明确能力边界、状态迁移和副作用控制
3. 429、超时、半成功、脏数据、回调丢失 都必须分别建模，不能统称“第三方失败”
4. 最有价值的 E2E 用例，是验证“依赖失败后系统仍然安全且可解释”
5. 前端必须同步感知后端降级状态，否则就会出现“后台已降级，页面还在假装正常”的体验事故
6. 故障演练的目标不是证明系统会失败，而是证明失败被收敛在可接受爆炸半径内

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
