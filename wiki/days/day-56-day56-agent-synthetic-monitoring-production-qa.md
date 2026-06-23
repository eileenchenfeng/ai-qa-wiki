# Day 56｜每日 AI 学习笔记｜Day 56：AI Agent 线上合成巡检与 Synthetic Monitoring 测试

- 📅 日期：2026-06-10
- 🏷️ 标签：learning-notes, AI, QA, Agent, synthetic-monitoring, observability, Ginkgo, Playwright, Kubernetes, API-Testing
- 📄 原文：[`raw/2026-06-10-day56-agent-synthetic-monitoring-production-qa.md`](../../raw/2026-06-10-day56-agent-synthetic-monitoring-production-qa.md)

## 核心总结

对 AI Agent 来说，很多高风险问题不会先在接口 500、机器告警或离线评测里暴露，而是先出现在 **用户真实链路的体验退化** 上：回答开始变慢、工具调用偶发选错、拒答策略漂移、页面状态卡住、异步任务悄悄丢失。要尽早发现这类问题，不能只靠被动日志和事故单，而要建立一套 **线上合成巡检（Synthetic Monitoring）** 机制：用一批低风险、可重复、可审计、具备明确断言的探针请求，持续从 **用户入口** 发起 E2E 检查，并把结果沉淀到质量看板、发布门禁和故障归因里。对资深测试开发而言，最关键的不是“把探针跑起来”，而是把它设计成一条真正有工程价值的链路：**Ginkgo** 守住核心路径和工具轨迹正确性，**Python / API Testing** 负责探针编排、指标聚合与告警阈值，**Playwright** 验证前端可见状态与交互反馈，**Kubernetes CronJob** 负责周期化执行与环境隔离。合成巡检的目标不是替代真实用户，而是让团队在真实用户受影响之前，先一步看到系统已经开始偏离健康状态。

## 今日核心要点

1. 合成巡检的本质是“主动发起的线上 E2E 体检”，不是简单的存活探测
2. 探针必须业务化：既要覆盖真实用户高频链路，又要足够安全、可重复、无副作用
3. 断言必须分层：可用性、时延、工具轨迹、策略边界、前端反馈都要分别校验
4. 探针失败不是简单告警，而是质量归因入口：要能回答失败在模型、编排、工具、前端还是依赖侧
5. 合成巡检要和发布流程联动：灰度阶段、版本切换、依赖升级后都应提升巡检频率
6. 巡检资产必须长期沉淀：一次线上故障，最终应留下至少一条永不删除的探针或回放样本

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
