---
title: "每日 AI 学习笔记｜Day 41：AI Agent 灾备演练与恢复测试"
date: 2026-05-26
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, disaster-recovery, failover, resilience, Ginkgo, Playwright, K8s, OpenTelemetry]
---
# 每日 AI 学习笔记｜Day 41：AI Agent 灾备演练与恢复测试

当 AI Agent 从实验系统走向生产之后，真正决定可用性的往往不是“功能能不能跑通”，而是“故障发生时能不能在预算时间内恢复”。灾备（Disaster Recovery, DR）测试的价值，不在于证明系统永不出错，而在于验证：主链路故障、区域不可用、依赖超时、记忆层损坏、工具服务降级时，系统是否仍能按预案完成切换、止损与恢复。

**核心总结：** AI Agent 的灾备测试不是单一故障注入，而是围绕 **故障发现、自动切换、状态恢复、数据一致性、用户体验兜底** 五个环节做端到端验证。工程上建议建立“三层灾备体系”：**控制面可切换、数据面可降级、用户面可感知但不中断**；测试上采用 **Ginkgo 后端故障编排 + K8s 流量切换 + Playwright 前端体验校验 + OpenTelemetry Trace 对账** 的组合方案；发布门禁上以 **RTO、RPO、降级成功率、故障隔离率、恢复后回归通过率** 作为核心指标。核心原则：**先保可用，再保一致；先做演练，再谈容灾。**

{/* truncate */}

## 1. 核心理论：为什么 AI Agent 更需要灾备演练

### 1.1 AI Agent 的“故障面”比传统服务更宽

传统 Web 服务做灾备，关注的多是服务实例、数据库、消息队列等基础组件；AI Agent 除此之外，还多了模型网关、工具链、上下文记忆、向量检索、评测裁判、异步编排器等依赖。只要其中一层没有设计好恢复路径，系统就会出现“表面在线、实际不可用”的灰故障。

<table header-row="true" header-col="false" col-widths="180,260,280,280">
<tr>
<td>维度</td>
<td>传统微服务</td>
<td>AI Agent 系统</td>
<td>灾备测试关注点</td>
</tr>
<tr>
<td>请求处理</td>
<td>同步接口链路</td>
<td>多轮对话 + 异步工具调用</td>
<td>会话是否中断、任务是否可恢复</td>
</tr>
<tr>
<td>状态管理</td>
<td>数据库事务</td>
<td>短期上下文 + Memory + 向量索引</td>
<td>恢复后上下文是否一致、是否串会话</td>
</tr>
<tr>
<td>依赖类型</td>
<td>RPC / DB / MQ</td>
<td>LLM、Tool、RAG、Judge、Workflow</td>
<td>依赖失效时能否降级与切流</td>
</tr>
<tr>
<td>用户体验</td>
<td>错误页 / 重试</td>
<td>流式回答、工具状态、思考中 UI</td>
<td>前端是否透明降级、是否误导用户</td>
</tr>
<tr>
<td>恢复目标</td>
<td>服务可重新访问</td>
<td>回答可继续、上下文可追溯、成本可控</td>
<td>RTO、RPO、体验恢复、语义质量恢复</td>
</tr>
</table>

### 1.2 灾备验证的 5 个核心问题

1. **故障是否被及时发现**：监控、探针、业务心跳能否在 SLA 内识别故障。
2. **切换是否自动且可控**：是否存在明确的主备、同城双活、跨区域兜底或降级路线。
3. **状态是否可恢复**：Session、Memory、任务执行状态、工具结果缓存是否可回放。
4. **影响是否被隔离**：一个租户、一个 Session、一个 Agent 的故障，是否会扩散到其他流量。
5. **恢复后是否真的可用**：不是 Pod Ready 就算恢复，而是关键 E2E 场景重新通过才算恢复完成。

### 1.3 灾备指标：RTO / RPO / FRR / DGR

```text
RTO (Recovery Time Objective)   = 从故障发生到业务恢复的最大允许时间
RPO (Recovery Point Objective)  = 系统可接受的数据丢失窗口
FRR (Failover Recovery Rate)    = 故障切换成功次数 / 故障切换总次数
DGR (Degradation Grace Rate)    = 故障时成功降级返回次数 / 故障总请求次数
```

对 AI Agent 来说，建议额外补两个测试视角：

- **SCR（Session Continuity Rate）**：故障切换后还能继续完成多轮会话的比例。
- **QRR（Quality Recovery Rate）**：恢复后回答质量重新达到基线阈值的比例，例如语义评分 ≥ 0.8。

---

## 2. 工程实践：建立 AI Agent 灾备演练分层模型

### 2.1 三层灾备体系

<callout icon="bulb" bgc="5">

**推荐分层：**

1. **控制面灾备**：Agent 编排服务、路由配置、模型网关、任务调度器故障后，能否快速切换到备用实例或备用区域。
2. **数据面灾备**：Memory、向量库、缓存、任务状态存储异常时，是否支持只读、降级、重建、延迟补偿。
3. **用户面灾备**：前端页面是否显示明确的降级状态；流式响应中断后是否提示继续、重试、稍后恢复。

</callout>

### 2.2 演练场景矩阵

<table header-row="true" header-col="false" col-widths="170,230,300,300">
<tr>
<td>场景</td>
<td>典型故障</td>
<td>验证重点</td>
<td>期望结果</td>
</tr>
<tr>
<td>主区域不可用</td>
<td>agent-api / ingress 全不可达</td>
<td>流量切到备区域、Trace 连续性</td>
<td>RTO ≤ 60s，核心对话可继续</td>
</tr>
<tr>
<td>模型网关雪崩</td>
<td>大面积 5xx / timeout</td>
<td>模型切换、限流、静态兜底</td>
<td>不无限重试，不放大故障</td>
</tr>
<tr>
<td>工具服务失效</td>
<td>HTTP 503 / schema 漂移</td>
<td>工具降级、部分功能可用</td>
<td>明确告知能力受限但主会话可完成</td>
</tr>
<tr>
<td>Memory 层损坏</td>
<td>Redis / Vector DB 读写异常</td>
<td>新会话可继续、老会话不串数据</td>
<td>降级为 stateless，禁止脏数据回流</td>
</tr>
<tr>
<td>任务中断恢复</td>
<td>Worker 重启 / pod 驱逐</td>
<td>任务幂等重放、重复扣费防护</td>
<td>最多执行一次或安全补偿</td>
</tr>
<tr>
<td>前端弱网 + 后端切换</td>
<td>流式连接 reset</td>
<td>页面重连、历史消息恢复</td>
<td>用户可见但不迷惑，可继续操作</td>
</tr>
</table>

### 2.3 一条合格的灾备 E2E 用例应该长什么样

面向 QA 的灾备验证，不建议拆成零散的“切流验证”“接口 200 验证”“日志存在验证”。更推荐一条完整业务链路：

1. 用户发起一个真实任务，例如“分析近 7 天异常告警并给出处置建议”；
2. Agent 进入多步编排，调用模型、检索、工具与 Memory；
3. 在执行中注入故障，例如主模型网关超时、主区域入口断流；
4. 系统自动切到备用模型 / 备用区域 / 降级路径；
5. 用户最终收到可理解、可执行、且不泄露错误细节的结果；
6. 回放 Trace、审计状态存储、核对是否重复执行、是否丢上下文。

---

## 3. Ginkgo 实战：后端灾备编排与恢复验证

### 3.1 故障演练用例模型

```go
package dr

type DRScenario struct {
    Name              string
    TenantID          string
    SessionID         string
    UserPrompt        string
    FailureInjection  FailureInjection
    RecoveryAssertion RecoveryAssertion
}

type FailureInjection struct {
    FaultType      string        // region_down / model_timeout / memory_readonly
    TriggerAtStep  string        // route / llm_call / tool_call / memory_write
    Duration       time.Duration
    Target         string        // svc name / deployment / gateway route
}

type RecoveryAssertion struct {
    MaxRTO               time.Duration
    MaxRPO               time.Duration
    AllowStateless       bool
    ExpectFailoverRegion string
    ExpectFallbackModel  string
    MustPreserveSession  bool
    MustNotLeakMemory    bool
}
```

### 3.2 Ginkgo 灾备 E2E 示例

```go
//go:build dr_e2e

package dr_test

import (
    "context"
    "fmt"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

var _ = Describe("AI Agent DR E2E", Label("dr", "e2e"), func() {
    var (
        ctx      context.Context
        cancel   context.CancelFunc
        client   *AgentClient
        helper   *ChaosHelper
        traceSvc *TraceService
    )

    BeforeEach(func() {
        ctx, cancel = context.WithTimeout(context.Background(), 8*time.Minute)
        client = NewAgentClientFromEnv()
        helper = NewChaosHelperFromEnv()
        traceSvc = NewTraceServiceFromEnv()
    })

    AfterEach(func() {
        helper.ClearAllFaults(ctx)
        cancel()
    })

    It("should fail over to standby region without breaking a multi-turn session",
        Label("P0", "region-failover", "session-continuity"), func() {
            sessionID := fmt.Sprintf("dr-session-%d", time.Now().UnixNano())

            // Step 1: 首轮对话，建立上下文
            firstResp, err := client.Chat(ctx, ChatRequest{
                SessionID: sessionID,
                Message:   "请记住：本周重点关注订单延迟与支付失败两类告警。",
            })
            Expect(err).NotTo(HaveOccurred())
            Expect(firstResp.Content).To(ContainSubstring("订单延迟"))

            // Step 2: 在主区域注入入口故障
            err = helper.DisableRegionIngress(ctx, "primary")
            Expect(err).NotTo(HaveOccurred())
            defer helper.EnableRegionIngress(ctx, "primary")

            // Step 3: 用户继续第二轮任务
            start := time.Now()
            secondResp, err := client.Chat(ctx, ChatRequest{
                SessionID: sessionID,
                Message:   "基于刚才的重点，给我一份 3 步排查建议。",
            })
            elapsed := time.Since(start)

            // Step 4: 恢复与降级验证
            Expect(err).NotTo(HaveOccurred())
            Expect(elapsed).To(BeNumerically("<", 60*time.Second)) // RTO
            Expect(secondResp.Metadata.Region).To(Equal("standby"))
            Expect(secondResp.Content).To(ContainSubstring("订单延迟"))
            Expect(secondResp.Content).To(ContainSubstring("支付失败"))
            Expect(secondResp.Metadata.Degraded).To(BeFalse())

            // Step 5: Trace 对账，确保切换链路真实发生
            trace, err := traceSvc.QueryByRequestID(ctx, secondResp.RequestID)
            Expect(err).NotTo(HaveOccurred())
            Expect(trace.ContainsSpan("failover.route.switch")).To(BeTrue())
            Expect(trace.ContainsTag("region", "standby")).To(BeTrue())
        })

    It("should degrade to stateless mode when memory store is unavailable",
        Label("P0", "memory", "degrade"), func() {
            sessionID := fmt.Sprintf("mem-dr-%d", time.Now().UnixNano())

            _, err := client.Chat(ctx, ChatRequest{
                SessionID: sessionID,
                Message:   "记住我的值班服务是 payment-worker。",
            })
            Expect(err).NotTo(HaveOccurred())

            err = helper.MakeMemoryReadOnly(ctx, "redis-memory")
            Expect(err).NotTo(HaveOccurred())
            defer helper.RestoreMemory(ctx, "redis-memory")

            resp, err := client.Chat(ctx, ChatRequest{
                SessionID: sessionID,
                Message:   "继续帮我生成一条值班交接摘要。",
            })

            Expect(err).NotTo(HaveOccurred())
            Expect(resp.Metadata.Degraded).To(BeTrue())
            Expect(resp.Metadata.MemoryMode).To(Equal("stateless"))
            Expect(resp.Content).NotTo(BeEmpty())
            Expect(resp.Content).To(ContainSubstring("当前处于降级模式"))
        })
})
```

### 3.3 断言重点不是“返回 200”，而是“恢复闭环成立”

建议把灾备断言拆成 5 个层级：

- **链路层**：是否真的发生切流 / 降级 / 熔断。
- **状态层**：Session、任务状态、缓存与 Memory 是否一致。
- **语义层**：最终回答仍满足业务目标，不是空响应或胡乱兜底。
- **体验层**：用户可理解当前是“恢复中”还是“已切换完成”。
- **成本层**：故障期间重试次数与 token 消耗是否受控。

---

## 4. K8s 实战：通过演练脚本触发主备切换

### 4.1 使用 Kubernetes 标记主备区域

```yaml
apiVersion: v1
kind: Service
metadata:
  name: agent-gateway-primary
  namespace: agent-prod
  labels:
    app: agent-gateway
    region: primary
spec:
  selector:
    app: agent-gateway
    region: primary
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: agent-gateway-standby
  namespace: agent-prod
  labels:
    app: agent-gateway
    region: standby
spec:
  selector:
    app: agent-gateway
    region: standby
  ports:
    - port: 80
      targetPort: 8080
```

### 4.2 演练脚本：切断主区域并验证恢复

```bash
#!/usr/bin/env bash
set -euo pipefail

NAMESPACE=agent-prod
PRIMARY_DEPLOY=agent-gateway-primary
STANDBY_DEPLOY=agent-gateway-standby

start_ts=$(date +%s)
echo "[DR] scale down primary gateway"
kubectl -n ${NAMESPACE} scale deploy/${PRIMARY_DEPLOY} --replicas=0

echo "[DR] wait standby ready"
kubectl -n ${NAMESPACE} rollout status deploy/${STANDBY_DEPLOY} --timeout=60s

echo "[DR] run synthetic probe"
curl -sS https://agent.example.com/healthz | jq .

end_ts=$(date +%s)
echo "[DR] estimated RTO=$((end_ts - start_ts))s"
```

### 4.3 建议引入演练护栏

<callout icon="first_place_medal" bgc="3">

**演练护栏建议：**

- 演练窗口必须可配置，默认仅在低峰时段执行。
- 演练前自动校验备用链路是否 Ready，避免“拿坏备机演练”。
- 演练期间全程采集 TraceID、切流事件、错误码分布、会话丢失率。
- 演练结束必须自动回切或进入受控人工确认阶段。

</callout>

---

## 5. Playwright 实战：前端侧验证灾备体验

### 5.1 为什么前端也必须参与灾备测试

后端完成切换，不代表用户真正恢复。对 Agent 产品来说，用户更在意：

- 页面是否长时间卡在“思考中”；
- 流式回复断掉后是否有重试或继续提示；
- 历史消息是否还在；
- 用户是否被错误地告知“成功”。

### 5.2 Playwright E2E 示例：流式中断后恢复

```python
from playwright.sync_api import Page, expect

def test_streaming_resume_after_failover(page: Page):
    page.goto("https://agent.example.com/chat")

    page.get_by_placeholder("请输入你的问题").fill("请帮我分析今天的支付异常并给出处置建议")
    page.get_by_role("button", name="发送").click()

    # 首先确认进入流式态
    expect(page.get_by_text("思考中")).to_be_visible(timeout=5_000)

    # 模拟网关切换：后端在演练环境里注入一次连接中断
    page.wait_for_timeout(4_000)

    # 验证前端给出可理解提示，而不是一直转圈
    expect(page.get_by_text("服务已切换，正在恢复回答")).to_be_visible(timeout=15_000)

    # 最终仍需收到完整结果
    expect(page.get_by_test_id("assistant-message").last).to_contain_text("处置建议", timeout=30_000)

    # 历史消息必须保留
    expect(page.get_by_test_id("user-message").last).to_contain_text("支付异常")
```

### 5.3 用户体验层的关键断言

1. 有明确提示：**恢复中 / 已切换 / 当前为降级模式**。
2. 不误导：不能显示“成功”但实际上回答为空。
3. 可继续：用户可以继续下一轮对话，而不是整页刷新丢状态。
4. 有边界：若确实不可恢复，必须快速失败并给出可执行建议。

---

## 6. OpenTelemetry 与 API Testing：恢复是否真的发生过

仅通过接口返回判断灾备是否成功，很容易误判。更稳妥的方法是把测试断言和 Trace / Metrics / Audit Log 对齐。

### 6.1 用 Trace 验证切流路径

```go
package traceassert

func AssertFailoverTrace(trace TraceTree) error {
    if !trace.ContainsSpan("gateway.request") {
        return fmt.Errorf("missing gateway.request span")
    }
    if !trace.ContainsSpan("failover.route.switch") {
        return fmt.Errorf("missing failover route switch span")
    }
    if !trace.ContainsTag("region", "standby") {
        return fmt.Errorf("standby region tag not found")
    }
    if trace.ContainsSpan("memory.cross_session_leak") {
        return fmt.Errorf("memory isolation violation detected")
    }
    return nil
}
```

### 6.2 API Contract 校验：降级响应结构必须稳定

```json
{
  "request_id": "req_123",
  "session_id": "sess_456",
  "content": "当前主链路异常，已切换到降级模式，以下是基础排查建议……",
  "metadata": {
    "degraded": true,
    "degrade_reason": "memory_unavailable",
    "region": "standby",
    "memory_mode": "stateless"
  }
}
```

建议把降级响应也纳入契约测试：即使服务在故障时返回“降级结果”，其字段结构也必须稳定，方便前端和监控系统正确消费。

---

## 7. 发布门禁：把灾备演练纳入 CI/CD

### 7.1 建议的流水线分层

```yaml
name: dr-gate

on:
  pull_request:
  schedule:
    - cron: '0 3 * * 2'

jobs:
  dr-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run DR smoke
        run: |
          go test ./tests/dr/... \
            -ginkgo.label-filter="dr && smoke" \
            -ginkgo.junit-report=dr-smoke.xml

  dr-nightly:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run region failover drill
        run: |
          go test ./tests/dr/... \
            -ginkgo.label-filter="dr && (region-failover || memory || tool)" \
            -ginkgo.procs=3 \
            -ginkgo.timeout=30m
```

### 7.2 推荐门禁阈值

<table header-row="true" header-col="false" col-widths="220,260,260">
<tr>
<td>指标</td>
<td>建议阈值</td>
<td>失败处理</td>
</tr>
<tr>
<td>RTO</td>
<td>核心链路 ≤ 60s</td>
<td>阻塞发布</td>
</tr>
<tr>
<td>RPO</td>
<td>会话状态丢失 ≤ 1 条消息</td>
<td>阻塞发布</td>
</tr>
<tr>
<td>Failover 成功率</td>
<td>≥ 95%</td>
<td>进入灰度观察，不全量</td>
</tr>
<tr>
<td>Degrade Grace Rate</td>
<td>≥ 99%</td>
<td>要求补齐兜底策略</td>
</tr>
<tr>
<td>恢复后回归通过率</td>
<td>核心 E2E 100%</td>
<td>阻塞发布</td>
</tr>
</table>

---

## 8. 实战建议：常见误区与改进方向

### 8.1 常见误区

- **误区 1：把“实例重启成功”当成“业务恢复成功”**
  - 正解：必须以真实用户场景重新跑通为准。
- **误区 2：只测主备切换，不测恢复后的数据一致性**
  - 正解：Session、Memory、工具结果、任务状态都要对账。
- **误区 3：只做后端演练，不测前端体验**
  - 正解：用户看到的恢复提示、历史消息和可继续交互同样关键。
- **误区 4：只做季度演练，不纳入持续门禁**
  - 正解：至少保留 smoke 级别 DR 演练进入常规 CI。
- **误区 5：演练只看成功率，不看成本和重试风暴**
  - 正解：要同时观察 token 消耗、请求倍增、队列堆积与告警噪音。

### 8.2 推荐落地顺序

1. 先定义关键业务链路与可接受 RTO/RPO。
2. 再补齐切换事件、降级事件、恢复事件的可观测性埋点。
3. 用 Ginkgo 固化核心灾备用例，优先覆盖 P0 业务。
4. 用 Playwright 把“用户看得见的恢复体验”纳入验证。
5. 最后把 DR smoke 纳入 PR / Nightly gate，形成常态化演练。

---

## 9. 课后思考题

1. 如果主模型不可用，但备用模型回答质量明显下降，你会把这类场景定义为“恢复成功”还是“降级成功”？门禁阈值该怎么定？
2. 如果 Memory 层发生故障，你更倾向于“短时间不可用”还是“降级为 stateless 模式继续回答”？为什么？
3. 对一个多租户 Agent 平台来说，灾备测试里最需要优先验证的“隔离性”指标有哪些？
4. 如果演练导致系统触发大量自动告警，如何区分“演练噪音”和“真实恢复失败”？
5. 你所在团队目前最接近单点风险的模块是什么？如果明天就要做一次 DR Drill，第一条 E2E 场景会怎么设计？

---

## 10. 今日小结

今天这篇笔记的重点，不是讲“如何把系统做成永不故障”，而是建立一个更务实的质量观：**故障是常态，恢复能力才是生产质量的核心竞争力。**

对 AI Agent 而言，灾备测试必须覆盖从模型、工具、Memory 到前端交互的完整链路。真正高质量的灾备方案，不只是主备切换成功，而是：

- 用户任务能继续；
- 会话状态不串、不丢、不乱；
- 降级路径可理解、可追踪、可回放；
- 恢复过程被量化、被门禁、被持续演练。

一句话总结：**DR 不是一次演习，而是一种把“恢复能力”产品化、工程化、测试化的长期机制。**
