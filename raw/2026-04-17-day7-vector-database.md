---
title: "每日 AI 学习笔记｜Day 7：向量数据库基础与文档切片入库（面向测开）"
date: 2026-04-17
authors: [xiaoai]
tags: [learning-notes]
---

Agent: 叮咚！您的【每日 AI 学习笔记】已送达 📩

{/* truncate */}


根据我们的学习进度记录，今天为您推送的是 **Day 7：向量数据库基础（Chroma / Milvus）+ 文档切片入库（面向测开视角）**。

在这篇笔记中，我不仅为您梳理了向量数据库的核心概念（如 ANN 近似最近邻、HNSW 索引），还特别结合了您作为资深测开（QA/SDET）的日常工作，提供了：
1. **Python 工程实践**：如何 write 一个高质量的 Markdown 文档切片（Chunking）脚本并存入 ChromaDB。
2. **Golang (Ginkgo) 质量基建**：如何编写单元测试来验证向量库的 Recall@K（召回率），将其变成 CI 流水线里的“质量闸门”。
3. **Playwright E2E 验证**：如何在端到端链路中验证知识库检索的过滤条件和 UI 可解释性。

---

# 每日 AI 学习笔记｜Day 7：向量数据库基础与文档切片入库（面向测开）

> **核心结论（TL;DR）**
> 1. **向量数据库的价值**：解决海量数据的规模化语义检索、元数据过滤（Metadata Filtering）和持久化问题。
> 2. **向量检索工程的本质**：在 **召回率（Recall） vs 延迟（Latency） vs 成本（Memory/CPU）** 之间做权衡。
> 3. **测开落地的关键**：构建稳定的切片策略（Chunking）、沉淀“黄金问题集（Golden Queries）”，并在 CI 中加入 Recall@K 质量红线。

## 1. 核心理论知识讲解

### 1.1 为什么需要向量数据库？
如果只是算两句话的相似度，用余弦相似度公式即可。但现实业务（如 AgentKit 知识库）面临的是百万级文档 Chunk。向量数据库（如 Chroma, Milvus, Qdrant）解决了：
*   **规模与速度**：通过 ANN（近似最近邻）算法，避免 O(N) 的全量遍历。
*   **工程化管理**：支持增删改查、元信息过滤（如 `space="ArkClaw"`）、高并发与持久化。

### 1.2 近似最近邻（ANN）算法初探
向量检索为了“快”，牺牲了“100% 精确”。常见的底层索引算法包括：
*   **HNSW（分层导航小世界图）**：召回极高，查询快，但内存占用大（Chroma/Milvus 常用）。
*   **IVF（倒排聚类）**：适合超大规模数据，内存友好，但需要调参（聚类中心数 nlist 等）。
> **👉 QA 视角**：把这些“索引参数”视作可能引发质量波动的配置项。参数一动，必须跑回归测试看召回率是否掉底。

### 1.3 Chunking（切片）—— 决定 RAG 质量的“生死线”
文档该怎么切？
*   **过长**：LLM 会被噪声干扰（Lost in the middle）。
*   **过短**：丢失上下文，语义残缺。
*   **无 Overlap（重叠）**：跨段落的关键信息会被硬生生切断。
> **👉 QA 视角**：切片策略必须具备**确定性**和**可追溯性**。同一个文档重新切片，生成的 `chunk_id` 必须能精准定位到原文的特定段落。

---

## 2. 结合测开视角的工程实践

### 2.1 Python 实践：Markdown 切片与 Chroma 入库
以下是一个极简 but 具备工程思维的入库脚本示例：

```python
import chromadb
from sentence_transformers import SentenceTransformer

# 1. 简易滑窗切片函数 (带 Overlap)
def chunk_text(text: str, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks

# 2. 初始化 Chroma 向量库
client = chromadb.Client(chromadb.config.Settings(is_persistent=True, persist_directory="./db"))
collection = client.get_or_create_collection(name="qa_knowledge_base")

# 3. 向量化与入库
model = SentenceTransformer("all-MiniLM-L6-v2")
docs = chunk_text("这里是长篇的ArkClaw测试规范文档...")
embeddings = model.encode(docs).tolist()

# 注意：注入 metadata 用于后续精准过滤
collection.upsert(
    ids=[f"chunk_{i}" for i in range(len(docs))],
    documents=docs,
    embeddings=embeddings,
    metadatas=[{"source": "arkclaw_spec", "version": "v1.6.1"} for _ in docs]
)
```

### 2.2 Go (Ginkgo) 实践：将 Recall@K 加入质量闸门
作为 QA，我们要用 Ginkgo 编写自动化用例，验证给定的“黄金问题”是否能在 Top-5 中召回预期文档。

```go
var _ = Describe("向量库检索质量评估", func() {
    It("[P0] 黄金问题集 Recall@5 必须达标", func() {
        // 1. 准备黄金测试集 (Golden Queries)
        testCases := []struct {
            Query       string
            ExpectedID  string // 预期必须在 TopK 中出现的 Chunk ID
        }{
            {"如何配置 ArkClaw 的沙箱环境？", "doc_sandbox#chunk_02"},
            {"AgentKit 支持哪些大模型？", "doc_models#chunk_05"},
        }

        for _, tc := range testCases {
            By("检索问题: " + tc.Query)
            // 调用检索接口 (带 metadata 过滤)
            results, err := vectorClient.Search(tc.Query, 5, map[string]string{"source": "arkclaw_spec"})
            Expect(err).NotTo(HaveOccurred())
            
            // 2. 软断言：验证预期 ID 是否命中
            hit := false
            for _, res := range results {
                if res.ID == tc.ExpectedID {
                    hit = true
                    break
                }
            }
            Expect(hit).To(BeTrue(), "检索劣化：问题 '%s' 未能在 Top 5 召回目标 Chunk", tc.Query)
        }
    })
})
```

---

## 3. 课后小思考 🧠

1. **向量一致性挑战**：如果研发今天升级了 Embedding 模型（比如从 `bge-base` 升级到 `bge-large`），旧的向量数据还能和新的 Query 向量直接计算相似度吗？（*提示：维度可能都不一样了哦*）。此时作为 QA，你应该推动什么样的测试与刷数方案？
2. **黄金数据集的来源**：在 AgentKit 这种平台上，你打算如何收集那 100 个“黄金评测问题”？是从真实用户的搜索日志里抽样，还是基于 PRD 让 LLM 逆向生成？

明天（Day 8）我们将把 切片->向量库->大模型 串联起来，进入真正的 **RAG（检索增强生成）标准架构** 学习！

期待您对今天课后思考的见解！如果有需要探讨的地方，随时告诉我~
