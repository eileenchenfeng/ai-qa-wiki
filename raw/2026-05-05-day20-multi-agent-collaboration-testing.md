---
title: "每日 AI 学习笔记｜Day 20：多 Agent 协作测试"
date: 2026-05-05
authors: [xiaoai]
tags: ["AI", "QA", "MultiAgent", "Agent", "测试开发", "Ginkgo"]
---

Agent：这是【每日 AI 学习笔记】Day 20 的博客归档版，基于 `Day20_多Agent协作测试_学习笔记_2026-05-05.md` 整理，重点梳理多 Agent 系统的架构模式、通信契约、共享状态一致性，以及一套适合测试开发落地的分层测试方法。

{/* truncate */}

## 1. 为什么“多 Agent”一上来就变难测？

单 Agent 系统的测试，很多时候还聚焦在“输入对不对、工具能不能调、输出是否符合预期”；但当系统进入多 Agent 协作阶段，测试对象会从**单点行为**升级为**协同过程**。

你不仅要关注：

- 谁负责拆解任务；
- 谁负责执行；
- 谁负责审核与兜底；
- 中间消息怎么传；
- 共享上下文是否一致；
- 某个 Agent 失败后，是局部降级还是全链路雪崩。

所以，多 Agent 测试本质上是在验证一个**具备自治性、异步性和分布式特征的协作系统**，是否依然满足正确性、稳定性、可恢复性与可解释性。

## 2. 三大架构模式与各自测试关注点

Day 20 把常见的多 Agent 架构概括为三类：**Orchestrator-Worker、Peer-to-Peer、Pipeline**。它们没有绝对优劣，但测试重点完全不同。

| 架构模式 | 典型特征 | 测试重点 | 常见风险 |
| --- | --- | --- | --- |
| **Orchestrator-Worker** | 中心编排器负责拆解、派发、聚合 | 路由正确性、超时重试、失败隔离、结果聚合 | 单点调度失败、策略错误放大问题 |
| **Peer-to-Peer** | Agent 之间平等协商、互相交换消息 | 协议一致性、会话收敛、消息幂等、冲突仲裁 | 环路、死锁、责任边界模糊 |
| **Pipeline** | 多个 Agent 串联成阶段化流水线 | 阶段契约、输入输出校验、异常传播、补偿回滚 | 上游错误层层传递、下游被污染 |

### 2.1 Orchestrator-Worker

这是企业里最常见的模式。Orchestrator 负责：

- 接收用户目标；
- 拆解任务；
- 选择 Worker；
- 收敛结果；
- 在异常时触发重试、兜底、降级。

因此测试时最关键的不是“某个 Worker 能不能返回结果”，而是：

- 任务是否被拆对；
- 路由是否派给了正确 Worker；
- 某个 Worker 失败时，是否只影响局部子任务；
- 聚合结果是否可解释。

### 2.2 Peer-to-Peer

这类模式没有绝对中心，更像多个 Agent 在群聊里协商。灵活，但也更容易出现：

- 消息重复投递；
- 协商不收敛；
- 两个 Agent 给出互相冲突的结论；
- 顺序不同导致结果不同。

这类系统的测试重点更偏协议治理和收敛性治理。

### 2.3 Pipeline

Pipeline 更像一条装配线，例如：规划 Agent → 检索 Agent → 执行 Agent → 审核 Agent → 汇总 Agent。

它的优点是阶段清晰，但风险也很明显：

- 上游输出一旦偏差，下游会继续放大错误；
- 格式变化会直接让后续解析失败；
- 某个阶段的“过宽容”会让错误漏出。

所以 Pipeline 测试一定要把**阶段契约**放在核心位置。

## 3. Agent 间通信协议与消息传递

多 Agent 测试里，一个经常被低估的问题是：**Agent 之间到底在传什么？谁来保证这些消息既可追踪又可幂等？**

一条较完整的协作消息，通常至少包含：

- `trace_id`：一次任务的全局链路标识；
- `span_id`：当前执行节点标识；
- `message_id`：当前消息唯一标识；
- `sender` / `receiver`：消息发送方与接收方；
- `intent`：消息意图，例如 plan / execute / review / retry；
- `payload`：业务主体；
- `context_version`：共享状态版本；
- `retry_count`：当前重试次数；
- `deadline` 或 `timeout_ms`：超时约束。

其中最关键的三个工程属性是：

1. **可追踪**：trace 能串起整条链路；
2. **可幂等**：重复消息不能造成重复副作用；
3. **可兼容**：协议演进时不能轻易打爆旧消费方。

### 测试视角下最容易忽视的问题

多 Agent 的通信问题通常不是“消息有没有发出去”，而是：

- 消息发到了，但**顺序错了**；
- 消息重复了，导致**重复执行**；
- 字段兼容了，但语义变了，导致**隐性协议破坏**；
- 某个 Agent 消费了消息，却没有写回状态，形成**幽灵执行**。

这也是为什么 Contract Testing 在多 Agent 系统里非常关键。

## 4. 共享状态一致性：最隐蔽也最致命的问题之一

多 Agent 往往共享：

- 统一任务上下文；
- 当前计划版本；
- 已完成步骤列表；
- 工具执行结果缓存；
- 审核结论与风险标记。

问题在于，不同 Agent 看到的未必是同一时刻的“真相”。常见风险包括：

### 4.1 并发写冲突

两个 Agent 同时更新同一份计划：

- Agent A 把步骤 2 标记为成功；
- Agent B 基于旧版本，把整份计划回写成待执行。

结果就是 A 的更新被覆盖，系统出现**丢写**。

### 4.2 脏读与陈旧读

Reviewer 读到旧版本上下文，对已经修复的问题继续报错，造成误判。

### 4.3 版本漂移

多个 Agent 使用不同提示模板或字段解释方式，即使字段名相同，也可能出现**语义漂移**。

### 4.4 最终一致但中间不一致

系统最终看起来收敛了，但在中间窗口里：

- 编排器认为失败；
- Worker 已成功；
- 监控却还没刷新。

如果测试只看最后结果，很多中间抖动根本暴露不出来。

> 所以共享状态测试不能只断言“最后对不对”，还必须断言：版本号是否单调递增、是否存在非法状态迁移、是否出现重复完成、回滚后是否真正恢复到可继续执行状态。

## 5. 多 Agent 测试的四个核心难点

Day 20 把多 Agent 测试难点浓缩为四类，我觉得很适合直接当测试设计 checklist。

### 5.1 非确定性

随机性来源包括：

- LLM 输出本身存在随机性；
- 路由决策受上下文影响；
- 异步消息到达顺序不稳定；
- 不同 Agent 对同一输入的解释不同。

对应策略不是死盯“输出必须完全一致”，而是：

- 做**边界断言**；
- 做**不变量断言**；
- 做**关键过程断言**。

### 5.2 隐式依赖

很多问题没有写在接口文档里，但系统默认它“应该存在”，例如：

- Planner 默认 Retrieval 一定能补全背景知识；
- Reviewer 默认 Execution 输出一定包含固定字段；
- Orchestrator 默认某个 Worker 一定能在 SLA 内返回。

这类依赖如果不显式化，线上就会出现“没人觉得这里会错，但它偏偏错了”的故障。

### 5.3 级联失败

多 Agent 最大的风险不是单点失败，而是错误传播：

- 上游计划错了，中游执行偏了，下游审核继续放行；
- 单节点超时触发频繁重试，进而拖垮整条链路。

因此测试一定要关注 **Blast Radius（爆炸半径）**，看问题到底停在一个节点、一个子任务，还是扩散到整条请求。

### 5.4 可解释性不足

系统一旦出错，最痛苦的问题往往是：

- 谁先错了？
- 它基于哪个上下文做出的错误决策？
- 问题来自协议、状态还是推理本身？

这时如果没有 trace、message replay、状态快照，定位几乎只能靠猜。

## 6. 五层测试分层策略：从单测到线上回放

Day 20 最实用的部分之一，是把多 Agent 测试拆成五层：

| 层级 | 目标 | 典型内容 |
| --- | --- | --- |
| **L1：单 Agent 单测** | 验证单个 Agent 的本地行为 | Prompt 适配、工具封装、输出 schema |
| **L2：Contract Testing** | 验证 Agent 间契约 | 字段、语义、版本兼容 |
| **L3：协作链路测试** | 验证编排、路由、重试、超时 | 顺序错乱、重复消息、局部失败 |
| **L4：E2E 业务测试** | 验证用户任务最终可达成 | 真实任务闭环、部分失败兜底 |
| **L5：线上回放与观测** | 验证线上故障可定位、可复现 | trace 回放、日志关联、问题复盘 |

这个分层特别适合测开团队，因为它回答了一个关键问题：

> **线上复杂问题，最终都应该想办法沉淀回更低层、更稳定的测试层。**

## 7. Contract Testing：结构、语义、版本兼容三件事都要测

很多人说 Contract Testing，第一反应只是“校验 JSON Schema”。但在多 Agent 场景里，这远远不够。

### 7.1 结构契约

关注字段是否完整，例如消息必须包含：

- `task_id`
- `trace_id`
- `intent`
- `payload`
- `context_version`

缺任一关键字段，都不应静默放过。

### 7.2 语义契约

光有字段还不够，还要检查业务语义。例如：

- `intent=review` 时，`payload` 必须带待审核对象；
- `retry_count>0` 时，必须带 `previous_error`；
- `status=done` 时，必须带摘要或结果引用。

### 7.3 版本兼容契约

协议演进后，还要验证：

- 新字段加入后，旧消费方能否忽略；
- 新枚举值出现时，旧逻辑是否会走到危险分支；
- 新老 Agent 混跑时，是否还能平滑协作。

这三类契约加起来，才是真正意义上的多 Agent Contract Testing。

## 8. 一段完整的 Ginkgo 测试骨架

Day 20 给出了一段很适合迁移到真实工程的 Ginkgo 示例，覆盖了：

- 契约校验；
- Worker 路由；
- 失败隔离；
- 无匹配 Worker 时的降级兜底。

下面保留核心骨架：

```go
package multiagent_test

import (
    "errors"
    "fmt"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type Task struct {
    TaskID         string
    TraceID        string
    Intent         string
    Payload        map[string]any
    ContextVersion int
}

type TaskResult struct {
    TaskID string
    Status string
    Output string
    Err    error
}

type Planner interface {
    Plan(userGoal string) ([]Task, error)
}

type Worker interface {
    Name() string
    CanHandle(task Task) bool
    Execute(task Task) TaskResult
}

type Orchestrator struct {
    Planner Planner
    Workers []Worker
}

func validateTaskContract(task Task) error {
    if task.TaskID == "" {
        return errors.New("missing task_id")
    }
    if task.TraceID == "" {
        return errors.New("missing trace_id")
    }
    if task.Intent == "" {
        return errors.New("missing intent")
    }
    if task.ContextVersion <= 0 {
        return errors.New("invalid context_version")
    }
    if task.Payload == nil {
        return errors.New("missing payload")
    }
    return nil
}

func (o Orchestrator) Run(userGoal string) ([]TaskResult, error) {
    tasks, err := o.Planner.Plan(userGoal)
    if err != nil {
        return nil, err
    }

    results := make([]TaskResult, 0, len(tasks))
    for _, task := range tasks {
        if err := validateTaskContract(task); err != nil {
            results = append(results, TaskResult{
                TaskID: task.TaskID,
                Status: "failed",
                Err:    err,
            })
            continue
        }

        handled := false
        for _, worker := range o.Workers {
            if worker.CanHandle(task) {
                results = append(results, worker.Execute(task))
                handled = true
                break
            }
        }

        if !handled {
            results = append(results, TaskResult{
                TaskID: task.TaskID,
                Status: "failed",
                Err:    fmt.Errorf("no worker can handle intent=%s", task.Intent),
            })
        }
    }

    return results, nil
}

var _ = Describe("Multi-Agent Collaboration", func() {
    It("should reject task when required fields are missing", func() {
        err := validateTaskContract(Task{TaskID: "task-1", Intent: "retrieve", ContextVersion: 1})
        Expect(err).To(MatchError(ContainSubstring("missing trace_id")))
    })
})
```

这段代码最有价值的点，不是语法本身，而是它把多 Agent 系统里最关键的几件事，拆成了可自动化断言的最小单元：

- **Contract 是否先拦截坏任务**；
- **Orchestrator 是否把任务路由给正确 Worker**；
- **某个 Worker 失败时，其他任务是否还能继续**；
- **没有匹配 Worker 时，系统是否优雅失败而不是崩溃**。

## 9. 更贴近实战的高价值回归用例

如果要给团队的多 Agent 系统补第一批自动化回归，我会优先选这些 case：

1. **协议缺字段**：字段缺失时必须在 L2 被拦截；
2. **消息乱序**：Reviewer 先收到结果时，系统不能误通过；
3. **单 Agent 超时重试**：验证重试次数、间隔与 trace 是否符合预期；
4. **共享状态冲突**：并发写计划时必须检测版本冲突；
5. **局部失败隔离**：一个子任务失败，其他任务仍能继续；
6. **重复消息幂等**：同一 task 重复投递时不能重复执行副作用；
7. **知识或依赖不可用时的降级**：输出应显式带风险提示，而不是伪造“成功”。

这些用例覆盖面广，而且非常贴近真实故障模式。

## 10. 今日总结

Day 20 让我对多 Agent 质量保障有了一个更清晰的判断：

> **多 Agent 测试，不只是测“答案是否正确”，更是在测“协作是否可信、状态是否一致、故障是否可控”。**

如果把单 Agent 看作一个可推理的功能模块，那么多 Agent 系统更像一个小型分布式系统。于是测试思路也必须升级：

- 从结果校验升级到**过程校验**；
- 从接口断言升级到**契约断言**；
- 从单点失败升级到**爆炸半径分析**；
- 从离线验证升级到**线上可观测性与回放能力**。

对 AI QA 来说，这篇内容最大的价值不只是“知道多 Agent 难测”，而是知道应该**先从哪几层、哪几类 case 开始补自动化**。

## 11. 课后思考题

### 思考题 1

如果某个 Reviewer Agent 偶发超时，但最终用户请求大多仍成功，你会如何判断这是否已经是一个必须治理的质量问题？

> 可以从用户影响面、重试成本、以及高并发下是否会放大为系统性风险三个角度去看。

### 思考题 2

如果多个 Agent 共享同一份任务上下文，但系统没有显式版本号机制，你预期最容易在线上出现什么问题？应该优先补哪类测试？

> 可以优先思考状态覆盖、重复执行、审核误判、回滚失效，以及如何用版本冲突测试和状态机断言快速补洞。

### 思考题 3

假设你要给当前团队的多 Agent 系统补第一批自动化回归，你会优先选哪 5 个高收益 case？为什么？

> 一个常见答案是：协议缺字段、消息乱序、单 Agent 超时重试、共享状态冲突、局部失败隔离。
