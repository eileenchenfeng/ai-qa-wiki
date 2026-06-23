# Day 39｜每日 AI 学习笔记｜Day 39：AI Agent 事件驱动测试与可靠性工程

- 📅 日期：2026-05-24
- 🏷️ 标签：learning-notes, AI, QA, Agent, incident-driven-testing, reliability-engineering, postmortem, Ginkgo, Playwright, K8s, SRE, chaos-engineering
- 📄 原文：[`raw/2026-05-24-day39-incident-driven-testing-reliability-engineering.md`](../../raw/2026-05-24-day39-incident-driven-testing-reliability-engineering.md)

## 核心总结

**本篇核心要点：**  1. **Incident-Driven Testing（IDT）核心理念**：每个 P0/P1 事故必须在 48h 内产出至少一条自动化回归用例，确保"同类故障不二犯"。IDT 是将 Postmortem 的 Action Item 落地为可执行测试代码的工程化方法。 2. **AI Agent 事故特殊性**：相比传统服务，Agent 事故根因更多元——模型退化、Prompt 漂移、工具链断裂、记忆污染、多 Agent 死锁。每类故障需要专门的检测与回归策略。 3. **IDT 闭环五步法**：Detect（发现）→ Classify（分类）→ Reproduce（复现）→ Codify（编码为测试）→ Prevent（纳入 CI/Gate）。每一步都有对应的工程化工具和自动化手段。 4. **故障分类 Taxonomy**：建立 Agent 故障 6 大类分类体系（Model/Prompt/Tool/Memory/Orchestration/Infra），每类对应标准化的测试模板和复现脚本，加速 IDT 落地。 5. **Reproduction-as-Code**：生产事故复现脚本化，使用 Trace Replay + Snapshot Restore 在隔离环境中精确重现故障现场，消除"无法复现"的借口。 6. **Ginkgo IDT Suite 设计**：基于 Label 标记故障类别和严重等级，使用 BeforeEach 注入故障条件，AfterEach 清理现场，确保 IDT 用例可在 CI 中稳定执行。 7. **可靠性度量 MTTD/MTTR/MTTF**：通过 IDT 覆盖率（已 Codify 的 Incident / 总 Incident）和故障复发率（同类故障再次发生占比）量化 IDT 体系有效性。 8. **Playwright Incident Replay**：将用户侧触发路径转化为 E2E 回放脚本，在前端层面验证修复有效性，确保用户体验层面的回归覆盖。

## 反向链接（同主题）

- `[learning-notes]` → [Day 01 day1-llm-basics](./day-01-day1-llm-basics.md)
- `[learning-notes]` → [Day 02 day2-prompt-engineering](./day-02-day2-prompt-engineering.md)
- `[learning-notes]` → [Day 03 day3-tot-react](./day-03-day3-tot-react.md)
- `[learning-notes]` → [Day 04 day4-structured-output](./day-04-day4-structured-output.md)
- `[learning-notes]` → [Day 05 day5-prompt-stability](./day-05-day5-prompt-stability.md)
- `[learning-notes]` → [Day 06 day6-embedding-similarity](./day-06-day6-embedding-similarity.md)
- `[learning-notes]` → [Day 07 day7-vector-database](./day-07-day7-vector-database.md)
- `[learning-notes]` → [Day 08 day8-rag-standard-architecture](./day-08-day8-rag-standard-architecture.md)
