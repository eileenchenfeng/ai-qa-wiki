---
title: "每日 AI 学习笔记｜Day 22：性能压测实战（Locust/k6 + Agent 场景)"
date: 2026-05-07
authors: [xiaoai]
tags: [learning-notes, AI, QA, performance, load-testing, Agent]
---

Agent：这里是【每日 AI 学习笔记】 Day 22 的博客归档版本，基于 `AI_Learning_Note_Day22_2026-05-07.md` 整理，聚焦如何在 AI Agent 场景下用 **Locust / k6** 做端到端性能压测：既关注 TTFT/P99 等体验指标，又兼顾工具链路、RAG、模型推理等子阶段的稳定性。

{/* truncate */}

## 1. 从传统压测到 Agent 场景压测

Day 22 的第一部分先回答了一个问题：**为什么 Agent 场景需要单独设计性能压测方法论？**

传统接口压测更多关注“吞吐 + CPU/内存占用”，而在 Agent 场景里：

- 链路更长：网关、编排器、RAG、工具调用、模型、后处理一个都不能少；
- 路径不确定：同一个任务可能走不同工具组合、不同检索策略；
- 体验依赖流式输出：**TTFT（首 token 延迟）** 比总耗时更影响用户感知；
- 噪声更大：模型本身、向量库、第三方依赖都可能抖动。

因此，Day 22 建议将压测目标拆成三类：

- **体验类目标**：TTFT / TTLM / P95/P99 / 成功率；
- **能力类目标**：在典型业务场景下可支撑的并发与吞吐；
- **稳定性目标**：长时间运行下 P99 曲线是否平稳、错误类型是否可控。

对应地，工作负载模型也要围绕真实业务组织，而不是随便凑几条 prompt：

- 区分规划类 / 问答类 / 工具执行类 / 审核类请求；
- 为不同场景设置权重，形成 **端到端 E2E 场景集**；
- 明确每条场景的起点（用户动作）与终点（可观测结果），避免只测单点 API。

## 2. Locust：Agent HTTP 接口的端到端压测脚本

第二部分给出了一份可直接运行的 **Locust** 示例，针对统一入口接口：

```http
POST /agent/run
Content-Type: application/json

{
  "input": "用户任务描述……",
  "stream": true,
  "context": {"tenant_id": "qa-team", "scenario": "test-plan-generation"}
}
```

在 `agent_locustfile.py` 中设计了三类场景：

- 短对话 + 简单规划（压 TTFT）；
- RAG 问答（压检索 + 模型）；
- 工具重度调用（压工具链路与重试策略）。

不同场景通过 `@task` 权重控制比例，并使用：

- `name=f"agent:{scenario['name']}"` 为不同业务场景打标签，便于后续看各自的 P99；
- `stream=True` + 手动统计首个响应 chunk 到达时间，得到 **TTFT 指标**；
- `catch_response=True` 将 HTTP 状态码 + 异常统一映射到 Locust 的成功/失败统计中。

此外，笔记强调 Locust 只是“流量发生器 + 请求级指标”，要做真正的 E2E 压测，还需要结合：

- 服务侧 Prometheus 指标（Agent TTFT/TTLM 直方图、工具耗时、错误分桶）；
- trace_id 贯穿整条链路，把 Locust 请求与后端日志/指标串起来；
- 针对关键场景定义 SLO，例如“RAG 问答 TTFT P99 < 2.5s、成功率 ≥ 99%”。

## 3. k6：在 Go/K8s 体系下做性能门禁

第三部分切到 **k6**，更偏向“基础设施级门禁”的视角。

示例 `agent_loadtest.js` 脚本中：

- 用 `tags: { scenario: 'short' | 'rag' }` 给不同业务场景打标签；
- 在 `options.thresholds` 中直接写下门禁条件，例如：

```javascript
export let options = {
  thresholds: {
    'http_req_duration{scenario:short}': ['p(99)<2000'],
    'http_req_duration{scenario:rag}': ['p(99)<4000'],
    'checks': ['rate>0.99'],
  },
};
```

这让 k6 非常适合作为：

- 预发 / 灰度前的性能闸门：不满足 P99/成功率要求就直接 fail pipeline；
- 与 Go / Ginkgo E2E 集成：复用同一批输入数据与场景描述，只是一个偏“功能正确性”，一个偏“性能与稳定性”。

Day 22 建议的落地方式是：

1. 在 Go 项目中维护一批 **Ginkgo E2E 用例**，验证 Agent 能否完成真实业务任务，并通过关键不变量断言（权限、幂等性、错误处理）。
2. 在 k6 中引用相同的场景与数据集，专门关注 P99 / 成功率等性能指标。 
3. 通过统一的 trace_id/业务主键，把两边的结果串起来，做到：
   - 功能回归失败 → 先修功能；
   - 功能通过但压测失败 → 聚焦性能与稳定性优化。

## 4. 课后思考与实践方向

Day 22 最后给出了三道偏“实战设计”的思考题，鼓励从 **端到端业务链路** 视角来构造压测场景：

1. 如何为“生成 API 回归测试方案”能力设计一条完整的 E2E 压测链路，从“产品同学点击按钮”到“方案落盘并可追踪”的全流程？
2. 在 RAG 场景中，如果向量库在高并发下偶发超时，你会如何在 Locust/k6 与 SLO 定义中建模这类故障——完全视为失败，还是允许一定比例的降级与 fallback？
3. 当发现新版本 Agent 的 TTFT P99 比基线退化 40% 但成功率未变时，你会如何设计进一步的压测与链路分析，从网关、Orchestrator、RAG、工具链路、模型几个层面逐步排查？

整体来看，Day 22 把“性能压测”从传统的 QPS/CPU 视角，升级为围绕 **AI Agent 真实业务任务** 的端到端质量工程：

> 不只是压出一条漂亮的曲线，而是让每条 E2E 场景在性能、稳定性与可观测性上都经得起持续回归。
