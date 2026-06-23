---
title: "每日 AI 学习笔记｜Day 16：LLM-as-a-Judge（大模型裁判）评测方法与工程落地"
date: 2026-05-01
authors: [xiaoai]
tags: [learning-notes]
---

Agent: 本文是【每日 AI 学习笔记】 Day 16 的整理版，主题是 **LLM-as-a-Judge（大模型作为裁判）**，基于 `output/day16_ai_learning_note.lark.md` 与对应 Feishu 推送内容归档到博客。

{/* truncate */}

## 1. 为什么需要 LLM-as-a-Judge？

传统的自动化评测指标（BLEU / ROUGE 等）在开放式生成、对话、Agent 场景下存在明显局限：

- 过度依赖参考答案（reference），而很多场景没有唯一标准答案；
- 奖励“字面相似度”而非“真正有用的回答”；
- 难以评估推理质量与可执行性（是否能指导下一步行动）；
- 对表述风格极敏感，稍微改写就可能得分大幅波动。

**LLM-as-a-Judge** 的核心思想是：

> 用一个更强、更稳定、懂语义的大模型来当裁判，对另一个模型/Agent 的输出做打分、排序、给理由，甚至输出结构化的多维度评分。

在 ArkClaw 这类 Agent 场景中，它可以用来替代或加速人工 case review，把“主观评审”工程化成可回归的评测脚本。


## 2. 常见评判模式

Day 16 把 Judge 模式拆成三类：

1. **单模型打分（Single-model scoring）**  
   - 输入：Task + Answer；
   - 输出：总分 + 理由（再加维度分）；
   - 实现简单、易批量，但易受 Prompt 设计与模型偏差影响。

2. **对比评判（Pairwise / Comparative）**  
   - 输入：同一道题的 Answer A 与 Answer B；
   - 输出：谁更好、置信度、理由；
   - 更稳定，但会有位置偏差，需要注意 A/B 顺序的影响。

3. **参考答案评判（Reference-based）**  
   - 输入：Task + Reference + Answer；
   - 输出：与 reference 的覆盖度/一致性/差异点；
   - 适合有权威答案的场景（FAQ、SOP），但 reference 本身质量也会成为瓶颈。

笔记同时强调几类典型偏差：位置偏差、冗长偏差、自我偏好（Judge 偏爱与自己风格相似的输出），这些都需要在 Prompt 与工程实现中显式防御。


## 3. Judge Prompt 设计：让模型“按规则打分”

为了让 Judge 结果可回归、可统计，Day 16 给出了一份可直接复用的 Prompt 模板，要求输出严格的 JSON：

- 综合总分 `score (1–5)`；
- 多维度评分 `dimension_scores`（correctness / completeness / actionability / groundedness / conciseness）；
- 简短中文理由 `reason`。

核心约束包括：

- 明确 1–5 分含义（5 = 完全正确且可直接执行；1 = 完全不可用）;
- 强调“长度不是加分项”，避免冗长偏好；
- 对编造/幻觉做强惩罚（correctness / groundedness 必须扣分）。

> 总结一句：**把评分规则、反偏差约束和 JSON Schema 都写进 Prompt**，Judge 才能“可工程化”。


## 4. Python 实战：调用 Judge 模型 + Pydantic 校验结果

笔记给出的 Python 示例包含完整流程：

1. 用 Pydantic 定义 `JudgeResult` 与 `DimensionScores` 模型，约束每个维度在 1–5 之间；
2. 使用 OpenAI（或公司内部网关）调用 Judge 模型，`temperature=0` 降低波动；
3. 从输出中截取 JSON 段落并反序列化；
4. 用 Pydantic 校验结构与字段范围，不合法时直接视为评测失败；
5. 支持重试（例如格式不合法时最多重试 2 次）。

此外，示例还给出了 `batch_eval` 方法：

- 一次性评测多条样本（`task/context/answer`）；
- 打印每条样本的分数与理由；
- 统计平均分，用于对比不同模型/Prompt 版本的整体质量变化。


## 5. Go + Ginkgo 集成：把 Judge 结果变成测试断言

在 Go 场景下，可以将 Judge 封装为一个 HTTP API，并在 Ginkgo 测试中直接调用：

```go
jr, err := CallJudge(task, context, answer)
Expect(err).To(BeNil())
Expect(jr.Score).To(BeNumerically(">=", 3), "原因：%s", jr.Reason)
```

这种做法的优点：

- 不改变现有测试框架（仍然是 Ginkgo / go test）；
- 可以按需控制评测成本（只在 nightly 或关键用例上跑 Judge）；
- 失败时可以把 `reason` 直接写入测试日志，帮助快速定位问题。


## 6. 防偏差与稳定性设计

Day 16 对“如何让 Judge 更稳、更公平”给了很多实用建议：

- **位置偏差（Pairwise）**：
  - 使用 swap 策略：A vs B、B vs A 跑两次，取平均或多数票；
  - 在 Prompt 中明确写出“不要因为回答出现顺序不同而偏袒”。

- **冗长偏差**：
  - Prompt 中强调长度不是加分项；
  - 把 `conciseness` 作为维度分，并在实现中对过长回答做额外处理（如触发二次复评）。

- **稳定性问题**：
  - 固定 temperature / 随机种子（如接口支持）；
  - 引入“灰区”策略（分数在 2.8～3.2 之间走人工复核）；
  - 把硬门槛落到关键维度（例如 correctness/groundedness），而不仅仅是总分。


## 7. 结合 ArkClaw 场景的落地思路

在 ArkClaw 的 Agent 测试中，人工 case review 有几个典型痛点：

- case 多、评审成本高；
- 不同评审者标准不统一；
- 很难做持续回归和趋势分析。

LLM-as-a-Judge 提供了一个折中方案：

1. 把每条 case 固化为结构化样本：`task + context + answer`；
2. 用 Judge 输出结构化 JSON 结果；
3. 在 CI 或 nightly 中跑评测：
   - 对整体平均分做趋势追踪；
   - 对关键维度设置门槛，例如 correctness >= 3；
   - 对低分样本输出详细信息，方便人工复查与回归。


## 8. 思考题（节选）

Day 16 的最后，给出了一些值得纳入长期规划的思考：

1. 用 LLM 评测 LLM 时，“裁判也会犯错”，你会如何做二次校验？多裁判投票、人工抽样复核、还是引入可验证信号（引用证据、可执行脚本）？
2. 如果同一题多次评测分数不一致，你会如何设计稳定机制？降温、灰区、重试、还是门槛拆维度？
3. 在 ArkClaw 的 RAG 场景里，Judge 应该优先评“回答质量”，还是“检索相关性”，或两者兼顾？对应的指标体系如何设计？

这些问题，与 Day 17 的 RAGAS 评测框架、Day 18 的 Tool Use 测试、Day 19 的容错/爆炸半径测试都可以联动起来，构成一条完整的智能评测闭环。
