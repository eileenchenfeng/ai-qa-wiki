# 主题：`evaluation`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
该主题聚焦于 AI Agent 在真实业务链路中的可评测性问题，核心是如何构建一套可复用、可回归的评测样本集，覆盖从 Prompt 稳定性、结构化输出校验到多步推理（ToT/ReAct）与检索增强（Embedding/FAISS 相似度）等关键能力点，解决传统单测无法刻画 LLM 非确定性输出的痛点。跨笔记可沉淀的工程实践包括：以分层样本集（基础能力、边界 case、对抗样本）驱动评测，结合 LLM-as-Judge 与规则断言双轨打分，使用 Ginkgo 组织行为级用例、Playwright 驱动 Agent 端到端任务、FAISS 做语义召回基线对比，并将评测结果纳入 CI 形成回归基线。对 QA 的落地建议是：优先把样本集当作一等代码资产维护，建立版本化与失败样本回流机制；同时在 Prompt 或模型升级时强制跑通对抗集与稳定性集，避免指标在均值上看似持平、却在长尾 case 上发生静默退化。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-05-14

## 时间线

- **Day 29** · 2026-05-14 · [每日 AI 学习笔记｜Day 29：AI Agent 评测样本集工程](../days/day-29-day29-agent-evaluation-dataset-engineering.md)