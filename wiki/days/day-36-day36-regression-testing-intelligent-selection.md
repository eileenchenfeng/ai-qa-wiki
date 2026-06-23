# Day 36｜每日 AI 学习笔记｜Day 36：AI Agent 回归测试策略与智能用例筛选

- 📅 日期：2026-05-21
- 🏷️ 标签：learning-notes, AI, QA, Agent, regression-testing, intelligent-selection, SDET, Ginkgo, Playwright, K8s, test-impact-analysis, risk-scoring
- 📄 原文：[`raw/2026-05-21-day36-regression-testing-intelligent-selection.md`](../../raw/2026-05-21-day36-regression-testing-intelligent-selection.md)

## 核心总结

**本篇核心要点：**  1. **全量回归不可持续**：AI Agent 每条用例平均消耗 0.5-2s + 数千 Token，500 条全量回归意味着 10min+ 执行时间和 \$5-20 Token 成本，必须引入智能筛选。 2. **Test Impact Analysis (TIA)**：通过代码变更 → 依赖图 → 影响用例的映射关系，将回归范围缩减 60-80%。 3. **风险评分模型**：基于历史失败率、变更频率、业务优先级、最后执行距今天数四个维度对每条用例打分，Top-N 优先执行。 4. **变更感知路由**：Prompt 变更 → 仅跑语义回归；工具 Schema 变更 → 仅跑契约 + 集成测试；模型版本变更 → 跑 Eval 基线对比。 5. **Ginkgo Label 选择器**：利用 `Label("layer", "e2e")` + `--label-filter` 实现 CI 中按风险层级动态选用例。 6. **Playwright Tag Filter**：`@regression-p0` / `@smoke` 标签配合 `--grep` 实现前端回归分层。 7. **K8s Job 弹性编排**：高风险用例并行度拉满（`parallelism: 10`），低风险用例串行节省资源。 8. **覆盖率守门员**：每次 TIA 筛选后，自动校验"被跳过的用例最近 7 天内至少执行过一次"，否则强制纳入本次回归。

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
