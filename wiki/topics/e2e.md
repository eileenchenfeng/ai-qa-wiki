# 主题：`e2e`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题三篇笔记聚焦于 AI Agent 端到端质量保障的闭环建设，核心问题是如何在非确定性输出场景下，将安全防线、评测样本与失败归因串成可持续运行的 E2E 测试体系：Day 28 从输入注入、工具调用越权到输出泄露分层设计防御用例，Day 29 讨论评测样本集的分层抽样、版本化与脏数据治理，Day 30 则覆盖失败模式分类与自动分诊回流。可复用的工程实践包括用 Playwright 驱动多轮对话回放、Ginkgo 组织分层 BDD 用例、FAISS 做语义去重与相似 case 聚类，以及通过 LLM-as-Judge 配合规则断言形成双轨校验。对 QA 的启发是：应把样本集、断言器与归因标签视为与被测系统同等重要的资产纳入 CI 流水线，并建立失败用例自动回灌评测集的机制，让 E2E 体系随 Agent 迭代共同演进。
<!-- LLM-DRAFT:END -->

- 共 **3** 篇笔记 · 最近更新：2026-05-15

## 时间线

- **Day 28** · 2026-05-13 · [每日 AI 学习笔记｜Day 28：AI Agent 安全测试的端到端防线设计](../days/day-28-day28-ai-agent-security-e2e-guardrails.md)
- **Day 29** · 2026-05-14 · [每日 AI 学习笔记｜Day 29：AI Agent 评测样本集工程](../days/day-29-day29-agent-evaluation-dataset-engineering.md)
- **Day 30** · 2026-05-15 · [每日 AI 学习笔记｜Day 30：AI Agent 失败归因与自动化分诊](../days/day-30-day30-agent-failure-attribution-and-auto-triage.md)