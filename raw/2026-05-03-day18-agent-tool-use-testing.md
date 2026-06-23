---
title: "每日 AI 学习笔记｜Day 18：Agent 工具调用（Tool Use / Function Calling）测试策略"
date: 2026-05-03
authors: [xiaoai]
tags: [learning-notes]
---

Agent: 这是【每日 AI 学习笔记】 Day 18 的博客归档版，主要内容来自 `AI_Learning_Note_Day18_2026-05-03.md`，聚焦当 LLM/Agent 开始“动手做事”时，如何对 Tool Use 进行系统化测试。

{/* truncate */}

## 1. 为什么要专门测 Tool Use？

与纯文本问答相比，**工具调用把系统带到了“可执行”层面**，质量风险显著增加：

- 安全性：越权调用、敏感信息泄露、危险操作（删库、发通知、改配置）；
- 可靠性：参数错误、调用序列错误、超时后重复执行导致幂等问题；
- 正确性：工具返回 A，模型总结为 B，忽略或歪曲工具结果；
- 可观测性与可回归：需要能够记录 Agent 的“动作轨迹”，支撑回放与回归测试。

Day 18 将 Tool Use 的测试拆成多个维度，并把前几天的内容（RAG、LLM-as-a-Judge）串联起来，形成一个统一视角：

> **检索其实也是一种 Tool**，RAG 的 Faithfulness/Answer Relevancy 等指标完全可以迁移到 “工具结果 → 最终回答” 的链路上。


## 2. 工具调用质量的核心维度

笔记给出了一张非常实用的维度表，可以直接转成测试用例与质量看板：

- **选择正确工具**：是否选择了允许且最合适的工具；
- **参数正确**：字段、类型、取值范围、必填项、枚举；
- **调用序列正确**：先后依赖、次数控制、循环终止条件；
- **幂等与重试安全**：超时/5xx/网络抖动后的重试策略，是否会导致重复副作用；
- **结果忠实使用**：最终回答是否忠实反映工具结果，而不是无视/篡改/编造；
- **权限与安全**：RBAC、租户隔离、敏感字段脱敏；
- **可观测与可回归**：是否有 trace / tool log / 输入输出快照，支持回放。

这些维度既可以驱动手工测试设计，也可以直接映射到自动化指标与门禁上。


## 3. 三层测试视角：Schema → Trajectory → Semantic

Day 18 建议把 Tool Use 测试拆成三层：

1. **Contract / Schema 层（确定性）**  
   - 工具名白名单、JSON Schema、参数范围与枚举校验；
   - 最适合作为硬门禁（速度快、结果稳定）。

2. **Trajectory / Workflow 层（半确定性）**  
   - 某类任务必须调用哪些工具，顺序如何；
   - 超时/失败时的 fallback 与重试策略；
   - 对应多步状态机与工具调用序列的断言。

3. **Semantic / Judge 层（智能评估）**  
   - 最终回答是否忠实于工具观测（类似 RAG 的 Faithfulness）；
   - 工具调用是否“必要且合适”，有没有无意义或高风险调用。

> CI 中推荐：**1、2 层作为主门禁，3 层只在 nightly 或关键回归场景中跑**，以平衡成本与稳定性。


## 4. Python：Tool Contract Testing（Schema + Trace）

笔记提供了一组 Python 示例，用 JSON Schema + pytest 对工具调用轨迹做硬门禁：

- 为每个工具定义 JSON Schema（字段、类型、取值范围、额外属性禁止等）；
- 从 Agent 执行 trace（JSON）中逐条读取 `tool_name` 和 `arguments`；
- 对每一次 tool call 执行 schema 校验；
- 对未知工具名或 schema 失败给出带位置信息的断言（方便定位 Prompt 或代码问题）。

这种做法可以在完全脱离模型推理的前提下，保证：

- 工具调用契约没有被悄悄破坏；
- 下游服务不会因为参数乱飞而崩溃；
- 轨迹记录格式稳定，可被后续分析工具消费。


## 5. Go + Ginkgo：工具桩 + 轨迹断言

在 Go 场景中，Day 18 给出了用 `httptest` 搭建工具桩的示例：

- 使用 `httptest.NewServer` 模拟 Tool 服务（如 `search_docs`）；
- 在测试中运行 Agent 逻辑，让它调用该伪造的工具；
- 对工具调用次数、参数范围、状态机终止条件做断言；
- 对 FinalAnswer 中是否体现“基于检索结果”做最基本的语义检查。

这类测试更偏向“半集成测试”：

- 不依赖真实下游服务，便于注入各种错误（超时、5xx、无效响应）；
- 可以验证重试策略、超时控制、危险工具的保护策略；
- 可以作为 HTL / 集成流水线中的可靠门禁。


## 6. 结合 Judge：专测“忠实使用工具结果”

Day 18 建议把 Day 16 的 LLM-as-a-Judge 复用到 Tool Use 场景中：

1. 把某次工具调用的 Observation 与最终 Answer 一起喂给 Judge；
2. 要求 Judge 判断：
   - Answer 是否严格依据 Observation；
   - 是否存在把失败说成成功、忽略关键错误、无证据编造等行为；
3. 输出 `faithful: true/false, reasons, risk level` 等结构化结果。

这种方式尤其适合：

- 高价值但文本多样性大的场景（无法用简单字符串匹配评估）；
- 夜间回归或预发门禁，用来捕捉“语义层面”的回归问题。


## 7. CI/CD 集成建议

在 CI 中，可以按“三段式”集成 Tool Use 测试：

1. 单测阶段：
   - Go：`ginkgo -r -p` / `go test ./...`；
   - Python：`pytest -q`；
   - 重点在 schema、纯函数、解析组件。

2. 工具桩集成测试：
   - 使用 httptest / wiremock 等模拟工具服务；
   - 注入 timeout/5xx/无效响应；
   - 验证序列、重试与降级逻辑。

3. 语义评估：
   - LLM-as-a-Judge 对关键用例做抽样评测；
   - 产出趋势：faithful rate、tool misuse rate 等。

同时，trace/日志建议：

- 输出每个用例的 tool call 序列与关键参数；
- 在失败时附上原始 tool call、工具返回、最终回答，便于快速定位问题。


## 8. 思考与行动项

Day 18 的结尾给出了一些值得立即落地的行动项：

- 为 ArkClaw 的若干高风险工具补齐 timeout / retry / idempotency contract；
- 增加 Memory 故障注入用例（写入失败降级、读取隔离拒绝）；
- 在 HTL 流水线上引入可靠性门禁（失败重试次数、熔断状态、副作用计数等）。

这些内容与前几天关于 RAG、Judge、Multi-Agent 的学习一起，构成了“让 Agent 从能回答问题 → 能稳定做事”的完整质量链路。
