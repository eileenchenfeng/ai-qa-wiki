# 主题：`dataset`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 评测样本集的工程化建设，核心问题是如何把零散的 Prompt 用例、工具调用轨迹与回归数据沉淀为可版本化、可复跑、可度量的 dataset，从而支撑 Agent 在多轮决策、结构化输出与稳定性维度上的持续评测。可复用的工程实践包括按场景分层（基础问答、ReAct/ToT 推理、结构化抽取、检索召回）切分样本，使用 JSONL/Parquet 固化输入与期望输出、配合 FAISS 做语义去重与相似召回、通过 Ginkgo 或 pytest 驱动断言式回归、并以 Playwright 覆盖端到端 UI Agent 链路，同时引入 LLM-as-Judge 与人工标注双轨打分。对 QA 的启发是：将评测样本集当作一等公民代码资产管理，建立 schema 校验与 CI 回归门禁；并在每次 Prompt 或模型升级时跑差分对比，量化 Pass@k 与稳定性漂移，避免凭感觉调优。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-14

## 时间线

- **Day 29** · 2026-05-14 · [每日 AI 学习笔记｜Day 29：AI Agent 评测样本集工程](../days/day-29-day29-agent-evaluation-dataset-engineering.md)