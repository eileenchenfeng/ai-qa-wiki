---
title: "每日 AI 学习笔记｜Day 6：Embedding 与相似度计算（面向测开）"
date: 2026-04-16
authors: [xiaoai]
tags: [learning-notes]
---

Agent: 叮～您的【每日 AI 学习笔记】已送达！今天是 **Day 6：Embedding（向量表示）与相似度计算（面向测开）**。

{/* truncate */}


我读取了您的学习计划，并结合您作为资深测开的背景，为您整理了这份包含理论、代码实战和深度思考的笔记。请查阅：

***

# 每日 AI 学习笔记｜Day 6：Embedding 与相似度计算（面向测开）

> 💡 **核心目标**：理解大模型是如何计算文本相似度的，并掌握如何在 QA 体系中对其进行工程化验证。

## 0. 核心结论 (TL;DR)
1. **Embedding 的本质**：将模糊的文本语义压缩成固定长度的可计算向量坐标。
2. **Cosine（余弦相似度）是主流**：在 NLP 领域，我们更关注向量的“方向”（语义关联）而非绝对长度。
3. **测开的真正挑战**：计算相似度很简单，难点在于如何将其转化为**可回归、可监控、可解释**的质量指标（如漂移监控、阈值寻优）。

---

## 1. 核心理论知识讲解

### 1.1 什么是 Embedding？
简单来说，Embedding 就是一个翻译器：
- **输入**：一段文本（如：“登录接口密码错误无提示”）
- **输出**：一个高维浮点数组（例如 `[0.12, -0.05, 0.88, ...]`）

**核心定律：语义越相近的文本，其在多维空间中的向量距离越近。**

**QA 视角的典型应用场景**：
- **用例智能去重**：自动发现语义相同但表述不同的重复用例。
- **缺陷聚类分析**：将海量 Bug Report 聚类，快速定位线上爆发的热点问题。
- **RAG 质量评测**：评估大模型的输出与标准答案的语义契合度（比传统的字符串精确匹配鲁棒得多）。

### 1.2 为什么偏爱 Cosine 余弦相似度？
- **Cosine 相似度**：`cos(θ) = (A · B) / (||A|| × ||B||)`
- **为什么不用欧氏距离？** 文本长度会严重影响向量的模长。余弦相似度排除了长度干扰，纯粹衡量两个向量在语义方向上的夹角。
- **取值范围**：通常在 `[-1, 1]` 之间，越接近 1 代表语义越相似。

---

## 2. 测开工程实践：相似度组件的自动化验证

今天我们不只是调用 API，而是要编写一个可被集成到 CI/CD 中的**相似度判定组件**。

### 2.1 Python 实战：核心计算与 Pytest 单测
在 Python 中，我们可以将纯数学逻辑与业务逻辑分离，确保其完全可测。

**核心逻辑 (`similarity.py`)**：
```python
import math
from typing import List
from dataclasses import dataclass

Vector = List[float]

def cosine_similarity(a: Vector, b: Vector) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("Invalid vectors")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        raise ValueError("Zero-norm vector")
    return dot / (na * nb)

@dataclass
class SimilarityResult:
    score: float
    is_similar: bool

def check_similarity(a: Vector, b: Vector, threshold: float = 0.85) -> SimilarityResult:
    score = cosine_similarity(a, b)
    return SimilarityResult(score=score, is_similar=score >= threshold)
```

**Pytest 回归用例 (`test_similarity.py`)**：
```python
import pytest
from similarity import cosine_similarity, check_similarity

def test_cosine_identical():
    v = [1.0, 2.0, 3.0]
    assert cosine_similarity(v, v) == pytest.approx(1.0)

def test_cosine_orthogonal():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

def test_threshold_decision():
    res = check_similarity([1.0, 0.0], [0.9, 0.0], threshold=0.95)
    assert res.is_similar is False
```

### 2.2 Go 语言视角：融入现有的后端测试框架
利用 Go 的强类型优势，可以在 `ginkgo` 或标准 `go test` 中轻松集成向量计算的基准测试。

```go
package similarity

import (
    "errors"
    "math"
)

type Vector []float64

func CosineSimilarity(a, b Vector) (float64, error) {
    if len(a) != len(b) || len(a) == 0 {
        return 0, errors.New("invalid vector dimension")
    }
    var dot, na2, nb2 float64
    for i := range a {
        dot += a[i] * b[i]
        na2 += a[i] * a[i]
        nb2 += b[i] * b[i]
    }
    na, nb := math.Sqrt(na2), math.Sqrt(nb2)
    if na == 0 || nb == 0 {
        return 0, errors.New("zero norm")
    }
    return dot / (na * nb), nil
}
```

### 2.3 进阶构建：黄金测试集 (Golden Set)
仅测试数学公式是不够的，你需要构建一个真实的**业务语义验证集**，用于监控底层模型升级带来的“语义漂移”：

| 场景 | 文本 A | 文本 B | 预期判定 |
| :--- | :--- | :--- | :--- |
| **同义改写** | 登录密码错误提示 | 输入错误密码需明确报错 | Similar (>0.85) |
| **细微差异** | 删除用户导致的数据异常 | 删除订单导致的数据异常 | Not Similar |
| **跨模块** | HTTP 500 自动重试 | 服务端 500 错误处理 | Similar |

> **QA Action Item**：在你的 CI 流程中加入一个定时任务，每天拉取黄金集跑一遍 Embedding，若某对文本的相似度波动超过 5% 即触发告警，防止底层大模型静默升级导致业务误判。

---

## 3. 课后小思考 🤔
1. **阈值博弈**：在做“用例去重”时，你更倾向于高阈值（宁可漏掉不合并，也不要误删不同用例）还是低阈值？为什么？
2. **多义词陷阱**：在 ArkClaw 的语境下，“实例”这个词可能有特定的基础设施含义，通用 Embedding 模型能准确识别吗？是否需要叠加传统的关键词（TF-IDF）策略做兜底？
3. **结合你目前的自动化工作**：如果要在 Ginkgo 或 Playwright 测试报告里引入“失败原因智能聚合”功能，你会如何运用今天学到的 Embedding 相似度计算？

***

今天的学习内容就到这里啦！明天的 Day 7 我们将进入**向量数据库（如 Milvus/Chroma）**的世界，探讨如何测试海量向量的检索召回率。如果您需要，我也可以帮您把今天提到的“黄金测试集”落地成可执行的 Python/Go 自动化脚本模板。祝您学习愉快！🦞
