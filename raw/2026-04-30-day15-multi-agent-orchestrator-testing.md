---
title: "每日 AI 学习笔记｜Day 15：Multi-Agent 与 Orchestrator 测试难点"
date: 2026-04-30
authors: [xiaoai]
tags: [learning-notes]
---

Agent: 本文是【每日 AI 学习笔记】 Day 15 在博客中的归档版，源内容来自 `output/day15_ai_notes.lark.md`，主题聚焦多智能体（Multi-Agent）系统与 Orchestrator 的质量保障。

{/* truncate */}

## 1. Multi-Agent 系统到底在复杂哪里？

Multi-Agent 的本质是：把一个大问题拆成多个可并行、可回滚的小问题，交给不同能力的 Agent 协同完成。常见架构模式包括：

1. **Orchestrator–Worker（编排-工人）**  
   - 中心 Orchestrator 负责“拆任务 → 派发 → 监督 → 聚合”；
   - Worker 只关注单个子任务执行；
   - 工程上最容易做 SLA、审计、状态回放。

2. **Peer-to-Peer（点对点自治）**  
   - 没有中心，Agent 之间通过协议协商；
   - 灵活但难以保证一致性、终止条件与责任边界。

3. **Hierarchical（层级/树状）**  
   - 顶层 Agent 负责任务分解；
   - 中间层编排子目标；
   - 底层 Agent 执行具体动作。

> 笔记的核心观点：要测试 Multi-Agent，**不要只把它当“对话系统”，要把它当“分布式状态机/调度系统”**。


## 2. Orchestrator 的四大职责

Day 15 把 Orchestrator 从“聊天主持人”的形象，重构为一个真正的“分布式任务调度器”，并拆出四个可测职责：

1. **任务分解（Decompose）**  
   - 把目标拆成 Subtask，定义清晰的输入/输出契约；
   - 明确依赖关系（DAG）与终止条件（Done Definition）。

2. **任务分发（Dispatch）**  
   - 选择合适的子 Agent（能力、权限、负载、成本）；
   - 为子任务设置超时、重试、幂等键和优先级。

3. **状态跟踪（Track）**  
   - 维护任务状态机：`Created → Dispatched → Running → Succeeded / Failed / Timeout → Aggregated`；
   - 处理并发极端场景：重复回包、乱序回包、部分回包。

4. **结果聚合（Aggregate）**  
   - 对子结果做格式校验、冲突消解、质量打分；
   - 输出可追溯证据（日志、引用、工具调用轨迹）。

这四点都可以成为测试设计的直接抓手。


## 3. 常见失效模式：Multi-Agent 为什么“难测”？

笔记列举了一批非常典型、也非常“工程味”的失效模式：

- **任务丢失（Task Lost）**：
  - Dispatch 成功但 Worker 未收到；
  - Worker 收到但回包丢失，Orchestrator 误判未完成。

- **结果不一致（Inconsistent Result）**：
  - Orchestrator 认为完成，Worker 认为失败或仍在运行；
  - 多个 Worker 对同一任务产生冲突结果。

- **死锁/循环依赖（Deadlock / Cyclic Dependency）**：
  - A 等 B 的结果，B 又等 A 的补充信息；
  - 重试策略叠加导致“忙等风暴”。

- **幻觉传播（Hallucination Propagation）**：
  - 某个子 Agent 生成了“自信但错误”的结论；
  - 其他 Agent 把它当事实继续推理，错误在链路上被放大。

> 这些问题几乎都不是单元测试能覆盖的，需要 **系统测试 + 故障注入 + 回放** 才能逼出来。


## 4. 关键指标一：任务闭环率（Task Completion Rate）

笔记建议给 Multi-Agent 系统定义一个核心指标：**闭环率**。

- 分母：在时间窗口内 Orchestrator 成功分发的子任务数 `N_dispatched`；
- 分子：最终被 Orchestrator 判定为 `Succeeded` 且结果通过契约校验的子任务数 `N_closed`；
- 指标：`TCR = N_closed / N_dispatched`。

同时拆解两个辅助指标：

- **接收率（Receive Rate）**：Worker 实际收到 / Orchestrator 分发；
- **聚合率（Aggregate Rate）**：Orchestrator 成功聚合 / Worker 成功完成。

在 Ginkgo 测试中，可以通过 Fake Worker + Fault Injection 的方式批量跑 N 个子任务，再对 `TCR` 做统计断言，并输出未闭环样本用于诊断。


## 5. 关键指标二：状态一致性（State Consistency）

Multi-Agent 的另一个难点在于 **双账本一致性**：Orchestrator 与各子 Agent 对同一任务的状态是否一致。

可以从三类断言来设计用例：

1. **强一致性（必须立即一致）**  
   - Orchestrator 记录“已分发”的任务，消息/存储中一定要有对应记录；

2. **最终一致性（允许延迟）**  
   - Worker 完成后，Orchestrator 允许在一定时间窗口内才将状态收敛为 `Succeeded`；

3. **单调性（不可回退）**  
   - 状态不应从 `Succeeded` 回退到 `Running`；
   - 同一 `subtask_id` 最终只允许一个终态（Succeeded/Failed/Timeout）。

配合故障注入（超时、报错、错误格式、乱序/重复回包），可以在测试中系统性验证这些断言。


## 6. trace_id 与可观测性：把链路变成“可回放故事”

Day 15 强调 Multi-Agent 可观测性的关键：**统一的 trace_id 与结构化日志**。

推荐实践：

- Orchestrator 为每次任务生成 `trace_id`，子任务继承或附加 `span_id`；
- 所有跨进程消息、工具调用、状态变更都携带 `trace_id`；
- 日志采用 JSON Lines，并附带 `trace_id / subtask_id / component / state / ts` 等字段。

随后可以通过 Python 脚本按 `trace_id` 聚合日志，统计闭环率、列出未闭环样本，并为故障排查提供“可回放的状态链”。


## 7. 结合 ArkClaw 的落地建议

笔记中以 ArkClaw 团队协作场景为例，把 Multi-Agent 映射到真实业务：

- 主 Agent 负责接收任务、拆分子任务、分发到不同子 Agent 或同学；
- 子 Agent 负责各自专业领域的处理；
- Orchestrator 需要对跨 Agent 链路做 trace、SLA 和质量兜底。

落地建议包括：

- 在现有 ArkClaw 流水线中引入“闭环率”与“一致性”作为核心质量指标；
- 为关键链路设计 K8s 级别的故障注入（Pod 重启、网络抖动、依赖服务 5xx 等）；
- 在日志解析与报表中突出“未闭环任务样本”，方便快速定位与回归。


## 8. 思考题（节选）

Day 15 结尾抛出了几个值得持续思考的问题：

1. 当子 Agent 提出要调用高风险/高成本工具时，Orchestrator 应该如何处理？白名单 + 审批，还是自动执行但加强审计？
2. 如何定义 Multi-Agent 系统的“测试完成标准”？仅有功能正确是否足够？
3. 当多个子 Agent 给出互相冲突的结论时，Orchestrator 的“裁决机制”是什么？多数票、置信度、还是引入“裁判 Agent”？

这些问题都可以自然延伸到 ArkClaw / 其他 Agent 平台的自动化测试设计中，为后续的工程实践提供方向。
