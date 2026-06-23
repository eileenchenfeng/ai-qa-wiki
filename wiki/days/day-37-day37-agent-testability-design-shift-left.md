# Day 37｜每日 AI 学习笔记｜Day 37：AI Agent 可测试性设计与质量左移

- 📅 日期：2026-05-22
- 🏷️ 标签：learning-notes, AI, QA, Agent, testability, shift-left, SDET, Ginkgo, Playwright, K8s, design-for-test, dependency-injection
- 📄 原文：[`raw/2026-05-22-day37-agent-testability-design-shift-left.md`](../../raw/2026-05-22-day37-agent-testability-design-shift-left.md)

## 核心总结

**本篇核心要点：**  1. **可测试性是架构属性**：不可测试的 Agent 不是"测试没写好"，而是"架构没设计好"。可测试性必须在 Design Review 阶段评审，与功能需求同等优先。 2. **6 大可测试性原则**：可观测性（Observability）、可控制性（Controllability）、可隔离性（Isolability）、确定性回放（Deterministic Replay）、契约显式化（Explicit Contracts）、故障可注入性（Fault Injectability）。 3. **依赖注入（DI）是基石**：Agent 的 LLM Client、Tool Executor、Memory Store、Orchestrator 必须通过接口注入，而非硬编码实例化，这是 Mock/Stub/Fake 的前提。 4. **确定性回放层**：在 LLM 调用与工具调用之间插入 Recording/Replay Middleware，支持"录制线上 Trace → 本地确定性回放"，将非确定性测试转化为确定性断言。 5. **质量左移 4 阶段**：需求评审植入可测试性检查 → 设计评审增加 Testability Scorecard → 编码阶段强制 Test Hook → PR 门禁自动化校验接口契约。 6. **Testability Scorecard（量化打分）**：从 DI 覆盖率、Mock 可替换率、Trace 可追踪率、故障注入点覆盖率、契约文件完备度 5 个维度对 Agent 模块打分（0-100），低于 60 分禁止合并。 7. **Ginkgo + httptest 确定性回放**：通过 `httptest.NewServer` + JSON Fixture 实现 LLM 响应录制回放，每次 CI 运行结果 100% 确定。 8. **Playwright Contract Snapshot**：前端 Agent UI 的工具调用面板，通过 snapshot 对比确保 Schema 变更被感知。

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
