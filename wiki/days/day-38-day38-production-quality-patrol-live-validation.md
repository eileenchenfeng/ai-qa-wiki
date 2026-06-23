# Day 38｜每日 AI 学习笔记｜Day 38：AI Agent 线上质量巡检与生产环境验证

- 📅 日期：2026-05-23
- 🏷️ 标签：learning-notes, AI, QA, Agent, production-patrol, live-validation, synthetic-monitoring, canary-assertion, Ginkgo, Playwright, K8s, SRE
- 📄 原文：[`raw/2026-05-23-day38-production-quality-patrol-live-validation.md`](../../raw/2026-05-23-day38-production-quality-patrol-live-validation.md)

## 核心总结

**本篇核心要点：**  1. **生产环境是 AI Agent 的终极测试场**：模型漂移（Model Drift）、Prompt 注入攻击、工具 API 退化、RAG 数据腐化等问题，往往只有在真实流量下才能被暴露。离线测试无法完全覆盖生产态的长尾问题。 2. **四大线上验证手段**：合成探针（Synthetic Probes）→ 金丝雀断言（Canary Assertions）→ 流量采样回放（Traffic Sampling Replay）→ 持续评估（Continuous Eval Pipeline），构成递进式生产质量守护体系。 3. **合成探针设计原则**：探针 Query 必须覆盖 Agent 核心能力的"黄金路径"，每条探针包含确定性断言（Tool 调用序列、结构化输出字段）和模糊断言（语义相似度 > 阈值）。 4. **金丝雀断言 ≠ 金丝雀发布**：金丝雀断言是在已发布的稳定版本上持续执行的"活性检测"，一旦断言失败即触发告警，而非用于灰度切流决策。 5. **流量采样回放**：从生产 Trace 中采样真实请求，脱敏后在影子环境中回放，对比当前版本与基线版本的输出差异（Semantic Diff），检测隐性退化。 6. **持续评估 Pipeline**：将 LLM-as-a-Judge 集成到生产监控中，对每日采样的 Agent 交互自动打分（Helpfulness / Harmlessness / Hallucination），分数低于 SLO 阈值时触发 P1 告警。 7. **Ginkgo 巡检框架**：基于 Ginkgo + K8s CronJob 实现定时巡检，每个 Describe 对应一个 Agent 能力域，每个 It 对应一条合成探针，失败时自动推送飞书告警。 8. **Playwright 前端活性检测**：通过 Playwright 定时执行 E2E 交互流程（发送消息→等待 Agent 响应→断言 UI 渲染），验证前端-后端-模型全链路可用性。

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
