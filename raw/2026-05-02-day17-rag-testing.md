---
title: "每日 AI 学习笔记｜Day 17：RAG（检索增强生成）测试策略与 RAGAS 实战"
date: 2026-05-02
authors: [xiaoai]
tags: [learning-notes]
---

Agent: 这是【每日 AI 学习笔记】 Day 17 的归档版，主要内容来自 `output/day17_rag_test.lark.md` 与对应 Feishu 推送，聚焦 RAG 架构测试与 RAGAS 指标体系。

{/* truncate */}

## 1. RAG 架构全景：Indexing → Retrieval → Generation

RAG（Retrieval-Augmented Generation）的核心思路是：

> 在生成之前先“查资料”，把可控的外部知识接入模型的上下文。

从测试视角，RAG 不是单个模型，而是一条链路：

1. **Indexing（建库/索引）**  
   - 切分（chunking）：按段落、语义或窗口切分原始文档；
   - 向量化（embedding）：将 chunk 编码为向量；
   - 存储（vector store）：向量 + 元数据（doc_id、agent_id、session_id、时间戳、权限标签等）。

2. **Retrieval（检索）**  
   - Query 构造：原问题、重写问题、多轮对话摘要、工具输出合成等；
   - 召回策略：向量召回 + 关键词（BM25）+ rerank（交叉编码器/LLM）；
   - 过滤与权限：基于 tenant_id / agent_id / session_id / visibility 做隔离。

3. **Generation（生成）**  
   - 提示词策略：是否强制引用、如何表达不确定、如何组织回答结构；
   - 上下文窗口管理：截断策略、去重、排序（时间优先/相关性优先）。

一条 RAG 链路的质量问题，可能来自任一环节，因此测试设计也需要“分层解耦”。


## 2. 四大质量评估维度

Day 17 将 RAG 的质量拆成四个可度量的维度：

1. **Faithfulness（忠实度）**  
   - 回答中的关键事实是否能在检索上下文中找到支撑；
   - 核心关注：幻觉注入——上下文没有、回答却“编”出了内容。

2. **Answer Relevancy（答案相关性）**  
   - 回答是否真正解决了用户问题，而不是长篇复读上下文；

3. **Context Recall（上下文召回率）**  
   - 检索出的 contexts 是否覆盖 ground_truth 所需的关键知识点；
   - 受到 chunk 策略、query 重写、过滤条件等多因素影响。

4. **Context Precision（上下文精度）**  
   - 检索结果中有多少是“真正有用”的；
   - 噪声 chunk 太多会挤占窗口，增加幻觉与截断风险。

> 一句话记忆：Indexing 测“知识可用性”；Retrieval 测“找得到且找得对”；Generation 测“用得对且说得稳”。


## 3. 常见失效模式（直接变成用例）

笔记列出了一些高价值的失效模式，非常适合直接做回归用例：

- 检索噪声：top-k 中大量无关 chunk，Context Precision 下降；
- 幻觉注入：回答出现上下文里不存在的实体/数值/流程；
- 上下文截断：有效 chunk 被截掉或被重复/噪声 chunk 挤掉；
- 语义漂移：query 重写或对话摘要篡改了用户原始意图。

在 ArkClaw 场景下，这些问题往往会直接影响多 Agent 协作和 Memory 模块的可靠性，是必须严肃对待的“质量红线”。


## 4. RAGAS 框架：把 Judge 变成可复用工具

RAGAS（RAG Assessment）可以理解为 “Day 16 的 LLM-as-a-Judge 在 RAG 场景里的具体化”：

- 数据结构约定：`(question, ground_truth, contexts, answer)`；
- 指标输出：0～1 的分数，适合做趋势分析与门禁；
- 内部实现：通常也是通过 LLM / embedding 对各维度进行判定与打分。

在工程上，可以通过 RAGAS 的 Python 脚本：

1. 从 JSONL 数据集中加载样本；
2. 调用 `evaluate()` 计算 faithfulness / answer_relevancy / context_recall 等指标；
3. 输出 JSON 报告（包括整体均值和每条样本的明细）；
4. 在 CI 或 nightly 中作为一个独立 Stage 运行，并在失败时输出“最差样本”帮助定位问题。


## 5. Go + Ginkgo 集成 RAGAS 结果

类似于 Day 16 的 Judge 集成方案，Day 17 给出的 Go 示例通过 Ginkgo 调用 Python 评测脚本：

```go
cmd := exec.Command(
    "python3",
    "tools/rag_eval.py",
    "--input", "testdata/rag_dataset.jsonl",
    "--output", outPath,
)

b, err := cmd.CombinedOutput()
Expect(err).NotTo(HaveOccurred(), "Python 评测脚本执行失败: %s", string(b))

// 解析 JSON 报告并做断言
Expect(r.Mean.Faithfulness).To(BeNumerically(">=", 0.7),
    "Faithfulness 过低，可能存在幻觉注入或上下文未被正确使用")
```

这里的关键点是：

- 不要求所有环境都装好 RAGAS，只需在特定 build tag（例如 `//go:build arkclaw`）下启用；
- 指标门槛一开始可以放在 nightly，稳定后再升级到 MR 门禁；
- 失败时不仅给出“分数过低”，还要定位哪些样本/问题最严重。


## 6. 专项测试场景示例

Day 17 针对 RAG 检索质量给出了三个很实用的专项测试场景：

1. **正常检索（Happy Path）**  
   - 例如查询“上一轮 Session 的总结是什么？”；
   - 期望：top-k 中包含该 session 的总结 chunk；`context_recall >= 0.8`。

2. **噪声干扰（Noise Injection）**  
   - 向 Memory 写入大量“相似但无关”的 chunk；
   - 期望：rerank / 过滤仍能把真正有用的 chunk 排前，前 3 个中至少 2 个有效。

3. **跨 Agent / 多租户隔离（Isolation）**  
   - Agent A 与 Agent B 在同一租户做相似任务；
   - 期望：A 的检索结果只包含 `agent_id=A`（或标记为共享的记忆）；任何越界召回都视为安全红线。

这些场景可以很好地补充纯“指标型”评测，让 RAG 质量问题更容易被定位和回归。


## 7. 结合 ArkClaw 的实践建议

对于 ArkClaw 这样带有 Memory / Session / 多 Agent 协作的系统，Day 17 的建议可以概括为：

- **链路分层测**：
  - Retrieval 层做契约测试（给定 query + filter，top-k 是否符合预期）；
  - Generation 层在固定 contexts 下做 faithful / relevancy 评估；
  - Memory 与检索层一起做隔离与安全测试。

- **数据集固化**：
  - 从真实 Session 日志中抽样构建 JSONL 数据集；
  - 保留“当时的原样 contexts”，避免知识库版本变化导致评测结果失真。

- **指标门禁与样本回放**：
  - 用 RAGAS 指标做夜间质量门禁；
  - 输出失败样本的 question + contexts + answer，方便人工查看与回放。


## 8. 思考题（节选）

笔记最后提出了几道值得持续思考的问题：

1. ground_truth 从哪里来？如何在成本可控的前提下构建高质量评测集？
2. ArkClaw 的 Memory 多租户/多 Agent 隔离在检索层具体是如何体现的？测试是否覆盖了所有关键组合？
3. RAGAS 也依赖 LLM 做判断，会不会存在“裁判与被测模型同源”的偏差？是否需要“双裁判”或规则型校验（引用链、doc_id 对齐）作为兜底？

这些问题与 Day 16 的 Judge、Day 18 的 Tool Use 测试、Day 19 的容错测试串起来，构成了一个完整的“检索 + 生成 + 工具 + 容错”的质量闭环。
