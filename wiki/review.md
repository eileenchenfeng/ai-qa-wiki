# 主题综述 LLM 草稿 · Review

- 共 **5** 个主题已起草（候选总数 125）
- 用途：人工审阅 LLM 自动生成的 topic 顶部综述，确认满意后再跑 `--all`。
- 修改方式：直接编辑 `wiki/topics/<topic>.md` 中 `<!-- LLM-DRAFT:BEGIN/END -->` 之间的内容；
  审阅通过后，建议把该 markers 替换为 `<!-- HUMAN-REVIEWED:BEGIN/END -->` 以避免被重跑覆盖。

---

## `learning-notes`  · 66 篇笔记  · 461 字

> 本主题围绕大模型应用从基础认知到工程化落地的完整链路展开，核心问题是如何让 LLM 在测开场景下输出可控、可评测、可复现：从 Day 1 的 LLM 原理铺垫，到 Prompt 工程进阶（CoT/ToT/ReAct）、结构化输出约束（JSON Mode、Regex Constraint）、Prompt 稳定性评测，再延伸至 Embedding 相似度、向量数据库与 RAG 标准架构。跨笔记可复用的关键实践包括：以 cosine similarity + 多次采样统计输出方差衡量 Prompt 稳定性、用 JSON Schema 与正则约束兜底解析失败、基于 FAISS/Chroma 做切片入库与召回评估、以 ReAct 框架拆解 Agent 行为便于断言。对 QA 工作的启发是：应把 LLM 输出当作非确定性接口对待，在 Ginkgo 或 pytest 中引入语义断言（embedding 距离阈值）替代字符串完全匹配，并将 RAG 链路按"切片→召回→生成"三段分别建立指标看板，避免端到端黑盒导致的回归盲区。

- 源文件：[`wiki/topics/learning-notes.md`](topics/learning-notes.md)

---

## `QA`  · 54 篇笔记  · 434 字

> 该主题下的 54 篇笔记围绕 LLM 与 AI Agent 的质量保障展开，核心问题集中在如何将传统 QA 范式迁移到非确定性系统：包括 Prompt 稳定性度量、结构化输出（JSON Mode、Regex Constraint）的契约校验、Embedding 相似度评估、多 Agent 协作链路验证，以及性能基线与可观测性建设。跨笔记可复用的方法论包括基于 FAISS 的语义回归断言、ToT/ReAct 推理路径的可重放测试、Locust/k6 对 Agent 场景的并发压测、OpenTelemetry Trace 串联多跳调用，以及 Skill 编排的契约化用例设计。对 QA 工作的启发是：一方面应尽快沉淀「语义断言 + 结构断言」双层校验框架，替代仅依赖字符串匹配的脆弱用例；另一方面应将 Trace 与性能基线纳入 CI 流水线，对 Agent 的延迟、Token 消耗与工具调用成功率做持续守护，使非确定性输出在工程层面获得可度量、可回归的质量底座。

- 源文件：[`wiki/topics/QA.md`](topics/QA.md)

---

## `AI`  · 53 篇笔记  · 421 字

> 本主题 53 篇笔记围绕 LLM 与 AI Agent 的全链路质量保障展开，核心问题集中在如何把不确定性强、行为难复现的大模型系统纳入可度量、可回归的工程体系：从 LLM 基础、Prompt 工程与稳定性、ToT/ReAct 推理范式、JSON Mode 与正则约束等结构化输出，延伸到 Embedding 相似度、向量库（FAISS）、Skill 编排，再到多 Agent 协作测试、性能与稳定性基线、Locust/k6 压测、OpenTelemetry 链路追踪以及 Chaos Mesh + Ginkgo E2E 的混沌注入。可复用的方法论是"语义断言 + 结构校验 + Trace 观测 + 基线回归"四件套，将不确定输出转为可比对指标。建议 QA 团队尽早把 Prompt/Schema 纳入版本化管理，并以 Trace ID 串联压测、混沌与功能用例，建立 Agent 的 P95 延迟与成功率基线，避免回归阶段才发现行为漂移。

- 源文件：[`wiki/topics/AI.md`](topics/AI.md)

---

## `Agent`  · 48 篇笔记  · 429 字

> 该主题下的笔记围绕 AI Agent 的构建、评测与质量保障展开，核心问题集中在如何让基于 LLM 的 Agent 在复杂推理（ToT/ReAct）、技能编排、多 Agent 协作场景下保持输出稳定性、性能基线与故障韧性，并实现可观测、可回归的工程化交付。跨笔记可复用的方法论包括：用结构化输出与 Embedding 相似度（FAISS）做语义断言、用 Ginkgo 编排 E2E 与混沌实验、用 Locust 与 k6（含 WebSocket）压测 Agent 的长链路对话、用 OpenTelemetry Trace 还原工具调用链路，以及把 Prompt 稳定性、性能基线、故障注入沉淀为 CI 回归门禁。对 QA 落地的启发是：一方面应尽早把"语义等价 + Trace 断言"作为 Agent 测试的第一公民，替代脆弱的字面匹配；另一方面建议将性能与混沌用例资产化入库，与 Prompt 版本一同纳入门禁，避免模型或 Skill 升级带来的隐性回归。

- 源文件：[`wiki/topics/Agent.md`](topics/Agent.md)

---

## `Ginkgo`  · 41 篇笔记  · 418 字

> 该主题下的笔记围绕 AI Agent 全生命周期质量保障展开，核心问题是如何把单 Agent 与多 Agent 协作系统的不确定性输出，转化为可度量、可回归、可发布门禁的工程化资产，覆盖性能压测、安全防线、评测样本集、失败归因、SLO 评分卡与持续监控等环节。跨笔记可复用的方法论包括以 Ginkgo 组织 BDD 风格用例与回归门禁，结合 k6 WebSocket、Locust 做并发与流式压测，借助 FAISS/Embedding 做语义断言与样本去重，依托 K8s 端到端发布验收串起灰度与回滚，并通过自动化分诊将失败按 Prompt、工具、模型、环境四类归因。对 QA 的启发是：一方面把"评测样本集 + SLO 评分卡"作为 AI 测试的一等公民纳入 CI，让每次模型或 Prompt 变更都触发可对比的基线回归；另一方面用 Ginkgo 统一传统接口测试与 Agent 行为测试的描述语言，降低用例维护成本并沉淀质量看板。

- 源文件：[`wiki/topics/Ginkgo.md`](topics/Ginkgo.md)

---
