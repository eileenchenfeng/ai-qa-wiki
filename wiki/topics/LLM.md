# 主题：`LLM`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题下的两篇笔记聚焦于大模型从底层机理到工程可控性的链路问题：Day 01 梳理 LLM 的演进脉络与 Transformer、预训练-微调范式等基础概念，Day 04 则切入结构化输出约束，讨论 JSON Mode、Regex Constraint 与 Function Calling 等手段对输出可解析性的保障。跨笔记可复用的关键词包括 Token 级概率分布、温度与 top-p 采样、JSON Schema 校验、约束解码（Outlines、Guidance）以及与 Ginkgo/Pytest 结合的输出断言流水线。对 QA 工作的启发在于：一是将"输出可被机器解析"作为 LLM 接口的一等验收指标，使用 Schema 校验加正则双层断言替代字符串模糊匹配；二是为非确定性响应建立基于多次采样的稳定性回归用例，量化字段缺失率与格式漂移率，使大模型测试具备可观测、可回归的工程基线。
<!-- LLM-DRAFT:END -->

- 共 **2** 篇笔记 · 最近更新：2026-04-13

## 时间线

- **Day 01** · 2026-04-10 · [每日 AI 学习笔记 Day 1：LLM 的前世今生](../days/day-01-day1-llm-basics.md)
- **Day 04** · 2026-04-13 · [每日 AI 学习笔记 Day 4：结构化输出约束（JSON Mode 与 Regex Constraint）](../days/day-04-day4-structured-output.md)