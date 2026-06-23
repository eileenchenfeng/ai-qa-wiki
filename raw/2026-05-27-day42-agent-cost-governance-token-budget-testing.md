---
title: "每日 AI 学习笔记｜Day 42：AI Agent 成本治理与 Token 预算测试"
date: 2026-05-27
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, performance, Ginkgo, Playwright, Kubernetes]
---
# 每日 AI 学习笔记｜Day 42：AI Agent 成本治理与 Token 预算测试

## 0. 核心总结

<callout icon="star" bgc="4">

**核心总结：** AI Agent 的成本问题，本质上不是“模型单价太高”，而是 **上下文膨胀、无效工具调用、重试失控、长链路编排缺少预算护栏** 共同叠加的结果。测试侧不能只盯正确率，还要把 **单轮 Token 消耗、单会话累计成本、失败重试放大倍数、工具调用投入产出比、租户级预算隔离** 纳入质量门禁。工程上建议建立 **预算声明化 + 执行期熔断 + Trace 对账 + 回归基线** 四层机制；自动化上通过 **Ginkgo 后端预算断言 + Playwright 前端成本提示校验 + K8s 限流与配额治理** 构建端到端验证闭环。核心原则：**先让成本可观测，再让成本可约束，最后让成本可优化。**

</callout>

当 AI Agent 进入真实业务之后，团队很快会遇到一个经典问题：功能都能跑通，但为什么账单增长速度远快于用户增长速度？根因通常不在单点，而在整条链路：Prompt 过长、历史上下文无限追加、工具反复重试、检索召回过宽、Fallback 模型链过深、流式中断后又重新生成一次。于是，“功能成功”并不等于“系统健康”，真正要验证的是：**系统是否在满足质量目标的同时，把单位任务成本控制在预算内。**

{/* truncate */}

## 1. 核心理论：为什么成本治理已经成为 AI Agent 质量问题

### 1.1 AI Agent 的成本构成不止是模型 Token

很多团队把成本简单理解成“输入 Token + 输出 Token × 模型单价”，这只覆盖了最表层。对一个真实 Agent 请求来说，成本至少包括以下几层：

<table header-row="true" header-col="false" col-widths="180,220,270,280">
<tr>
<td>成本层</td>
<td>典型来源</td>
<td>常见失控原因</td>
<td>测试关注点</td>
</tr>
<tr>
<td>模型推理成本</td>
<td>Prompt / Completion / Embedding</td>
<td>上下文过长、温度高导致输出冗长、Fallback 多次调用</td>
<td>单轮 / 单会话 Token 是否超基线</td>
</tr>
<tr>
<td>工具调用成本</td>
<td>搜索、数据库、三方 API、代码执行</td>
<td>工具选择错误、循环调用、幂等缺失</td>
<td>工具调用次数与收益是否匹配</td>
</tr>
<tr>
<td>编排成本</td>
<td>Planner / Router / Judge / Retry</td>
<td>路由过深、重试无上限、评估链条过长</td>
<td>失败路径是否放大总体成本</td>
</tr>
<tr>
<td>基础设施成本</td>
<td>K8s 资源、缓存、队列、向量库</td>
<td>空闲副本过多、任务堆积、召回范围过大</td>
<td>峰值流量下单位请求成本是否恶化</td>
</tr>
<tr>
<td>机会成本</td>
<td>响应慢、超时、用户重复点击</td>
<td>前端无反馈、服务抖动、用户重复触发</td>
<td>体验缺陷是否诱发重复请求</td>
</tr>
</table>

### 1.2 成本治理的 5 个核心问题

1. **预算有没有被显式定义**：单请求、单会话、单租户、单天预算是否存在硬边界。
2. **超预算时有没有明确策略**：继续执行、降级回答、切换廉价模型还是直接熔断。
3. **成本是否可追踪到链路节点**：是否能定位是 Prompt、Tool、Memory 还是 Judge 放大了成本。
4. **失败是否导致成本倍增**：重试、超时、回放、双写是否带来隐性成本放大。
5. **优化是否可验证**：每次 Prompt 调整、召回裁剪、模型切换后，是否能用回归基线证明“更省且不降质”。

### 1.3 面向 QA 的关键成本指标

```text
CPR  (Cost Per Request)        = 单请求平均成本
CPS  (Cost Per Session)        = 单会话累计成本
TPR  (Token Per Request)       = 单请求 Token 消耗
RMA  (Retry Magnification)     = 实际调用次数 / 理论最小调用次数
TCR  (Tool Cost Ratio)         = 工具调用成本 / 总成本
BVR  (Budget Violation Rate)   = 超预算请求数 / 总请求数
CER  (Cost Efficiency Ratio)   = 质量得分 / 单位成本
```

对于 AI Agent，建议再补两个指标：

- **CCR（Context Compression Ratio）**：压缩后的上下文长度 / 原始上下文长度，用来衡量记忆裁剪是否有效。
- **FRI（Fallback Recovery Inflation）**：发生回退后成本 / 正常路径成本，用来衡量容灾与降级的成本代价是否可接受。

---

## 2. 工程实践：建立可测试的成本治理体系

### 2.1 四层治理框架

<callout icon="bulb" bgc="5">

**推荐治理框架：**

1. **预算声明层**：把不同场景的预算写成配置或 DSL，而不是散落在代码里。
2. **执行控制层**：请求执行过程中实时累计 Token、工具调用数、时延与成本，超阈值立即触发降级或熔断。
3. **可观测对账层**：通过 Trace、Metrics、审计日志把每次调用的成本拆到具体步骤。
4. **回归验证层**：把成本基线纳入 CI/CD，每次变更都做“成本不回退”校验。

</callout>

### 2.2 一条合格的成本 E2E 用例应该怎么设计

按照真实用户链路，建议不要把“Prompt Token 数校验”“工具调用数校验”“前端文案校验”拆成互不相干的散点测试，而要设计成完整链路：

1. 用户发起一个真实任务，例如“汇总近 7 天支付异常并生成处置建议”；
2. Agent 进行检索、工具调用、摘要压缩与最终生成；
3. 执行期间累计预算并在某一步接近阈值；
4. 系统触发压缩、降级模型或工具裁剪；
5. 用户仍得到可用结果，同时前端明确展示“当前为节流/降级策略”；
6. 最终通过 Trace 与账单明细核对成本没有异常放大。

### 2.3 场景矩阵

<table header-row="true" header-col="false" col-widths="170,230,280,280">
<tr>
<td>场景</td>
<td>典型风险</td>
<td>验证重点</td>
<td>期望结果</td>
</tr>
<tr>
<td>长上下文会话</td>
<td>历史消息无限堆积</td>
<td>是否触发摘要压缩 / 裁剪策略</td>
<td>回答保持可用，Token 增长斜率下降</td>
</tr>
<tr>
<td>工具密集型任务</td>
<td>搜索 / API 多次循环调用</td>
<td>工具调用次数上限、去重与缓存命中</td>
<td>工具不重复空转，成本受控</td>
</tr>
<tr>
<td>失败重试场景</td>
<td>超时后全链路重放</td>
<td>幂等、部分结果复用、重试预算隔离</td>
<td>失败不导致成本成倍上涨</td>
</tr>
<tr>
<td>多租户并发</td>
<td>某租户突发流量挤占预算</td>
<td>租户级配额、限流与公平性</td>
<td>单租户异常不拖垮全局</td>
</tr>
<tr>
<td>前端重复提交</td>
<td>用户多次点击发送</td>
<td>按钮防抖、请求去重、进度提示</td>
<td>不产生重复推理与重复收费</td>
</tr>
</table>

---

## 3. Ginkgo 实战：后端成本预算断言

### 3.1 预算模型设计

```go
package budget

type BudgetPolicy struct {
    ScenarioName        string
    MaxPromptTokens     int
    MaxCompletionTokens int
    MaxTotalTokens      int
    MaxToolCalls        int
    MaxRetryCount       int
    MaxEstimatedCostUSD float64
    AllowFallbackModel  bool
    DegradeStrategy     string // compress_context / cheaper_model / skip_optional_tools / fail_fast
}

type ExecutionCost struct {
    PromptTokens     int
    CompletionTokens int
    ToolCalls        int
    RetryCount       int
    EstimatedCostUSD float64
    UsedFallback     bool
    Degraded         bool
}

func (c ExecutionCost) TotalTokens() int {
    return c.PromptTokens + c.CompletionTokens
}
```

### 3.2 Ginkgo E2E 用例：验证超预算触发降级而不是失控重试

```go
//go:build cost_guard

package budget_test

import (
    "context"
    "fmt"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

var _ = Describe("AI Agent Cost Guard", Label("cost", "e2e"), func() {
    var (
        ctx      context.Context
        cancel   context.CancelFunc
        client   *AgentClient
        traceSvc *TraceService
    )

    BeforeEach(func() {
        ctx, cancel = context.WithTimeout(context.Background(), 5*time.Minute)
        client = NewAgentClientFromEnv()
        traceSvc = NewTraceServiceFromEnv()
    })

    AfterEach(func() {
        cancel()
    })

    It("should compress context and skip optional tools when request is close to token budget",
        Label("P0", "budget", "degrade"), func() {
            sessionID := fmt.Sprintf("budget-%d", time.Now().UnixNano())

            // Step 1: 连续建立多轮上下文，模拟真实长对话
            for i := 0; i < 6; i++ {
                _, err := client.Chat(ctx, ChatRequest{
                    SessionID: sessionID,
                    Message: fmt.Sprintf("第 %d 轮：请记录今天支付、库存、物流三类异常，并保留排查上下文。", i+1),
                })
                Expect(err).NotTo(HaveOccurred())
            }

            // Step 2: 触发一个本来会调用多个工具的复杂任务
            resp, err := client.Chat(ctx, ChatRequest{
                SessionID: sessionID,
                Message:   "基于前面的上下文，输出一份值班分析摘要，并给出优先级排序。",
            })
            Expect(err).NotTo(HaveOccurred())

            // Step 3: 断言系统走了预算保护策略
            Expect(resp.Metadata.Degraded).To(BeTrue())
            Expect(resp.Metadata.BudgetStrategy).To(Equal("compress_context"))
            Expect(resp.Metadata.ToolCalls).To(BeNumerically("<=", 2))
            Expect(resp.Metadata.TotalTokens).To(BeNumerically("<=", 6000))
            Expect(resp.Content).To(ContainSubstring("优先级"))

            // Step 4: Trace 对账，确保不是靠隐藏重试“硬跑过”
            trace, err := traceSvc.QueryByRequestID(ctx, resp.RequestID)
            Expect(err).NotTo(HaveOccurred())
            Expect(trace.CountSpan("llm.call")).To(BeNumerically("<=", 2))
            Expect(trace.ContainsSpan("context.compress")).To(BeTrue())
            Expect(trace.ContainsSpan("optional_tool.skipped")).To(BeTrue())
        })

    It("should block retry amplification when upstream model keeps timing out",
        Label("P0", "retry", "cost"), func() {
            resp, err := client.Chat(ctx, ChatRequest{
                SessionID: "retry-budget-001",
                Message:   "请分析最近 24 小时订单取消率异常并输出根因假设。",
            })

            Expect(err).NotTo(HaveOccurred())
            Expect(resp.Metadata.RetryCount).To(BeNumerically("<=", 2))
            Expect(resp.Metadata.EstimatedCostUSD).To(BeNumerically("<", 0.2))
            Expect(resp.Metadata.FallbackModel).NotTo(BeEmpty())
            Expect(resp.Content).NotTo(BeEmpty())
        })
})
```

### 3.3 成本断言重点

- **不是只看结果有无返回**，还要看是否以可接受成本返回；
- **不是只看 Token 总数**，还要看其增长原因；
- **不是只看重试次数**，还要看是否复用了中间结果；
- **不是只看单请求**，还要看长会话累计成本是否失控；
- **不是只看后端**，还要确认前端没有诱发重复请求。

---

## 4. Python / API Testing：预算守卫与契约校验

### 4.1 使用 pytest 验证成本元数据结构稳定

```python
import requests


def test_cost_metadata_contract():
    payload = {
        "session_id": "cost-contract-001",
        "message": "请总结本周支付异常并给出三条建议"
    }
    resp = requests.post("https://agent.example.com/api/chat", json=payload, timeout=60)
    resp.raise_for_status()
    body = resp.json()

    assert "content" in body
    assert "metadata" in body

    metadata = body["metadata"]
    assert isinstance(metadata["total_tokens"], int)
    assert isinstance(metadata["prompt_tokens"], int)
    assert isinstance(metadata["completion_tokens"], int)
    assert isinstance(metadata["estimated_cost_usd"], (int, float))
    assert isinstance(metadata["retry_count"], int)
    assert isinstance(metadata["tool_calls"], int)
    assert "budget_strategy" in metadata
```

### 4.2 典型降级响应示例

```json
{
  "request_id": "req_cost_123",
  "session_id": "sess_cost_456",
  "content": "当前任务已启用预算保护策略，以下提供压缩后的排查建议……",
  "metadata": {
    "prompt_tokens": 3200,
    "completion_tokens": 680,
    "total_tokens": 3880,
    "estimated_cost_usd": 0.084,
    "tool_calls": 2,
    "retry_count": 1,
    "degraded": true,
    "budget_strategy": "compress_context",
    "fallback_model": "gpt-4o-mini"
  }
}
```

建议把这类成本字段纳入 API Contract 测试，否则前端和监控在降级场景中就无法稳定消费预算状态。

---

## 5. Playwright 实战：前端如何避免“用户手滑造成双倍成本”

### 5.1 为什么前端体验直接影响成本

很多成本浪费并不是模型“笨”，而是交互设计“坏”：

- 发送按钮无防抖，用户连点三次；
- 流式回答期间无状态提示，用户以为没发出去又重试；
- 网络慢时没有请求关联 ID，刷新后再次发起同任务；
- 页面不展示降级中，用户误判系统卡死而重复输入。

### 5.2 Playwright E2E 示例：重复点击不应触发重复推理

```python
from playwright.sync_api import Page, expect


def test_duplicate_submit_should_not_duplicate_cost(page: Page):
    page.goto("https://agent.example.com/chat")

    input_box = page.get_by_placeholder("请输入你的问题")
    send_button = page.get_by_role("button", name="发送")

    input_box.fill("请分析今日支付失败激增的可能原因，并给出排查顺序")

    # 用户连续点击两次
    send_button.click()
    send_button.click()

    # 前端应立刻禁用发送按钮，避免第二次提交
    expect(send_button).to_be_disabled(timeout=2_000)

    # 页面应展示处理中状态
    expect(page.get_by_text("正在生成回答")).to_be_visible(timeout=5_000)

    # 最终只有一条 assistant 响应
    expect(page.get_by_test_id("assistant-message")).to_have_count(1, timeout=30_000)

    # 页面展示预算提示或节流提示（可选）
    expect(page.get_by_text("本次任务已启用预算保护策略")).to_be_visible(timeout=30_000)
```

### 5.3 前端成本防护检查清单

1. 发送按钮是否在请求进行中禁用；
2. 是否有幂等 request_id 防止重复提交；
3. 流式中断后是否提示“恢复中”而不是让用户重新发；
4. 是否在高成本场景提示“将进行摘要压缩/分步回答”；
5. 历史消息恢复后是否继续同一会话，而不是新开会话重复消耗。

---

## 6. K8s 与平台治理：从单请求预算走向租户级成本隔离

### 6.1 配额与隔离思路

对于多租户 AI 平台，仅做应用层预算还不够，还需要平台层做隔离：

<table header-row="true" header-col="false" col-widths="190,260,260,250">
<tr>
<td>治理层</td>
<td>典型手段</td>
<td>适用问题</td>
<td>测试关注点</td>
</tr>
<tr>
<td>应用层</td>
<td>请求预算、上下文压缩、工具裁剪</td>
<td>单请求过贵</td>
<td>降级策略是否生效</td>
</tr>
<tr>
<td>租户层</td>
<td>QPS 配额、日预算、模型白名单</td>
<td>单租户抢占全局资源</td>
<td>预算隔离是否严格</td>
</tr>
<tr>
<td>集群层</td>
<td>Namespace ResourceQuota、HPA、队列长度保护</td>
<td>峰值流量导致资源挤兑</td>
<td>扩缩容是否稳定</td>
</tr>
<tr>
<td>平台层</td>
<td>账单对账、成本告警、异常任务熔断</td>
<td>长周期成本漂移</td>
<td>告警是否及时、是否可追踪</td>
</tr>
</table>

### 6.2 K8s 配额示例

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: agent-tenant-a-quota
  namespace: agent-tenant-a
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    limits.cpu: "16"
    limits.memory: 32Gi
    pods: "30"
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: tenant-a-egress-guard
  namespace: agent-tenant-a
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: shared-llm-gateway
```

### 6.3 平台级压测建议

<callout icon="first_place_medal" bgc="3">

**建议补充三类成本压测：**

- **吞吐-成本曲线压测**：并发从低到高递增，观察单位请求成本是否在拐点后急剧恶化。
- **重试放大压测**：主动制造上游 5xx / timeout，观察重试是否让成本成倍增长。
- **租户争抢压测**：模拟大租户突发流量，验证小租户是否还能维持预算内服务。

</callout>

---

## 7. 可观测性：让每一分钱都能在 Trace 上对账

成本治理如果没有可观测性，最终会沦为“拍脑袋调 Prompt”。建议把以下字段打进 Trace / Metrics：

```json
{
  "trace_id": "trace_cost_001",
  "session_id": "sess_cost_001",
  "tenant_id": "tenant-a",
  "prompt_tokens": 2800,
  "completion_tokens": 540,
  "tool_calls": 2,
  "retry_count": 1,
  "estimated_cost_usd": 0.072,
  "budget_strategy": "skip_optional_tools",
  "fallback_model": "gpt-4o-mini"
}
```

建议至少做到三件事：

1. **按 Span 拆成本**：prompt build、memory recall、tool call、llm infer、judge evaluate 分别记录；
2. **按租户聚合**：支持看租户、场景、模型维度的成本分布；
3. **按版本对比**：新旧版本上线后比较成本中位数、P95 与质量得分，做回归判断。

---

## 8. 发布门禁：把“成本不回退”正式纳入 CI/CD

### 8.1 建议的门禁分层

```yaml
name: agent-cost-guard

on:
  pull_request:
  schedule:
    - cron: '0 2 * * 3'

jobs:
  cost-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run cost smoke suite
        run: |
          go test ./tests/cost/... \
            -ginkgo.label-filter="cost && smoke" \
            -ginkgo.junit-report=cost-smoke.xml

  cost-regression:
    runs-on: ubuntu-latest
    needs: cost-smoke
    steps:
      - uses: actions/checkout@v4
      - name: Compare token baseline
        run: |
          python3 scripts/compare_cost_baseline.py \
            --current reports/current_cost.json \
            --baseline reports/baseline_cost.json \
            --fail-on-token-regression 0.15 \
            --fail-on-cost-regression 0.10
```

### 8.2 推荐阈值

- PR Smoke：核心场景 `TPR` 不得回退超过 **15%**；
- Nightly Regression：`CPR / CPS / BVR` 同比基线回退超过 **10%** 即报警；
- Weekly Review：对 Fallback 场景单独统计 `FRI`，避免“容灾可用但代价过高”。

---

## 9. 课后思考题

1. 你的 Agent 系统里，哪一层最容易造成“看不见的成本放大”：Prompt、Tool、Judge 还是 Retry？为什么？
2. 如果只能先做一个成本质量门禁，你会优先选 `Token 基线`、`重试放大倍数` 还是 `租户预算隔离`？
3. 当降级策略能明显省钱，但答案质量略有下降时，测试团队应该如何定义“可接受”的阈值？
4. 你所在团队是否已经把成本字段透出给前端与监控？如果没有，最小可落地版本应该包含哪些字段？

---

## 10. 今日小结

今天这篇的核心，不是教你“怎么省几分钱”，而是建立一个更工程化的认知：**成本是 AI Agent 的一等质量属性。**

对 QA / 测试开发来说，真正有价值的不是手工看账单，而是把成本问题像性能、稳定性、隔离性一样，纳入自动化验证和发布门禁。只要你能把 **预算定义、执行期保护、链路对账、回归比较** 这四件事串起来，团队就能逐步从“月底看账单焦虑”走向“上线前就发现成本回退”。

下一步很适合继续深入的方向包括：**基于真实流量回放的成本画像**、**RAG 召回成本优化**、**多模型路由的性价比评估**，以及 **质量-成本联合评分卡** 的落地。