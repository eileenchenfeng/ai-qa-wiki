---
title: "每日 AI 学习笔记｜Day 63：AI Agent 事件溯源、审计日志与可重放测试"
date: 2026-06-17
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, event-sourcing, audit-log, replay-testing, reliability, Ginkgo, Playwright, Kubernetes, API-Testing]
---

# 每日 AI 学习笔记｜Day 63：AI Agent 事件溯源、审计日志与可重放测试

<callout icon="star" bgc="4">
**核心总结：** 当 AI Agent 进入企业级生产环境后，“结果对不对”已经不够，团队还必须回答：**这个结果是怎么来的、用了哪些输入、调用了哪些工具、谁授权了、失败后能不能复盘、线上事故能不能用同一批事件重放出来**。事件溯源与审计日志的价值，不只是为了合规留痕，而是把一次 Agent 执行拆成可追踪、可验证、可重放的事实流。对资深测试开发来说，今天的重点是用 **E2E 场景**验证完整链路：用户发起任务 → Agent 规划 → 工具调用 → 权限审批 → 事件写入 → 投影更新 → 审计查询 → 离线重放。Ginkgo 负责验证事件追加、状态投影与重放一致性；Python API Testing 负责校验审计查询、脱敏与完整性；Playwright 负责验证用户侧时间线和审计详情可理解；Kubernetes 演练日志落库延迟、consumer 重启、事件重复投递与投影重建。成熟的 Agent 质量体系，不只要能“跑成功”，还要能在出问题时**讲清楚、追得回、重放得出、修复得准**。
</callout>

昨天我们讨论了 AI Agent 异步回调、Webhook 一致性与事件驱动可靠性。进一步往生产深处走，会遇到一个更关键的问题：当用户、合规、研发或 SRE 追问“为什么 Agent 做出了这个动作”时，系统能不能给出可信证据？

今天的主题是：**AI Agent 事件溯源、审计日志与可重放测试**。它连接了质量、合规、稳定性和故障复盘，是 Agent 从 Demo 走向生产平台时必须建设的基础能力。

{/* truncate */}

## 0. 今日核心要点

1. **审计日志不是普通业务日志，而是不可随意改写的事实记录。**
2. **事件溯源的目标是用事件重建状态，而不是只保存最终状态。**
3. **可重放测试可以把线上事故变成稳定复现的回归资产。**
4. **Agent 事件必须覆盖输入、计划、工具调用、权限、输出与人工干预。**
5. **E2E 用例要验证“执行结果”和“审计证据”同时正确。**
6. **日志脱敏、租户隔离和访问控制必须纳入审计查询测试。**

---

## 1. 核心理论：为什么 Agent 需要事件溯源和审计日志

### 1.1 普通日志解决不了 Agent 生产追责问题

传统服务日志通常用于排查错误，例如请求耗时、异常堆栈、接口返回码。但 Agent 系统里的关键问题往往更复杂：

- 用户给了什么意图？
- Agent 拆成了哪些步骤？
- 每一步为什么选择这个工具？
- 工具调用前是否经过授权？
- 调用参数是否包含敏感字段？
- 最终答案是否引用了过期上下文？
- 人工审批是否改变了执行路径？

如果只依赖散落在多个服务里的普通日志，排查时很容易出现“各说各话”：模型网关有一段日志，工具服务有一段日志，审批系统有一段日志，但无法拼成一条可信的端到端证据链。

<callout icon="bulb" bgc="3">
**质量视角：** Agent 审计能力的核心，不是“多打点”，而是把每一次关键决策都变成可关联、可查询、可验证的事实。
</callout>

### 1.2 事件溯源的基本思想

事件溯源（Event Sourcing）强调：系统状态不是直接被覆盖保存，而是由一串不可变事件推导出来。例如，一个 Agent 任务的状态可以来自以下事件：

```json
[
  {"type":"task.created","task_id":"task_1001","actor":"user","sequence":1},
  {"type":"agent.plan.created","task_id":"task_1001","sequence":2},
  {"type":"tool.call.requested","tool":"search","sequence":3},
  {"type":"approval.granted","approver":"human","sequence":4},
  {"type":"tool.call.completed","tool":"search","sequence":5},
  {"type":"answer.generated","task_id":"task_1001","sequence":6}
]
```

最终状态 `completed` 并不是孤立字段，而是由这些事件按顺序投影出来的结果。这样做有三个好处：

1. **可追溯**：能看到每一步发生了什么；
2. **可重建**：投影表损坏后可以重新消费事件恢复；
3. **可重放**：线上问题可以用同一批事件在测试环境复现。

### 1.3 Agent 审计事件至少覆盖 7 类事实

<table header-row="true" col-widths="160,240,260,180">
  <tr>
    <td>事件类别</td>
    <td>典型事件</td>
    <td>审计价值</td>
    <td>测试优先级</td>
  </tr>
  <tr>
    <td>用户输入</td>
    <td>task.created / prompt.received</td>
    <td>确认触发来源与原始意图</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>规划决策</td>
    <td>agent.plan.created</td>
    <td>解释 Agent 为什么选择某条路径</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>工具调用</td>
    <td>tool.call.requested / completed</td>
    <td>追踪外部副作用和调用参数</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>权限审批</td>
    <td>approval.requested / granted / denied</td>
    <td>证明敏感动作经过授权</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>模型输出</td>
    <td>answer.generated / citation.attached</td>
    <td>追踪答案来源与引用上下文</td>
    <td>P1</td>
  </tr>
  <tr>
    <td>人工干预</td>
    <td>human.override.applied</td>
    <td>区分自动决策与人工修正</td>
    <td>P1</td>
  </tr>
  <tr>
    <td>失败补偿</td>
    <td>compensation.started / finished</td>
    <td>验证失败后是否完成收敛</td>
    <td>P0</td>
  </tr>
</table>

---

## 2. 工程实践：设计一条可审计、可重放的 Agent 事件链

### 2.1 推荐的事件模型

一个生产可用的 Agent 审计事件，建议至少包含以下字段：

```json
{
  "event_id": "evt_20260617_0001",
  "trace_id": "tr_abc_123",
  "task_id": "task_1001",
  "tenant_id": "tenant_a",
  "actor_type": "agent",
  "actor_id": "agent_runtime",
  "event_type": "tool.call.requested",
  "sequence": 3,
  "occurred_at": "2026-06-17T09:00:00Z",
  "payload_hash": "sha256:xxxx",
  "payload_redacted": {
    "tool": "search",
    "query": "redacted_summary"
  },
  "risk_level": "medium"
}
```

关键字段说明：

- `event_id`：全局唯一，用于幂等去重；
- `trace_id`：串起用户请求、Agent 执行和下游工具；
- `task_id`：业务实例主键；
- `tenant_id`：租户隔离边界；
- `sequence`：任务内单调递增序号；
- `payload_hash`：验证原始载荷是否被篡改；
- `payload_redacted`：给审计查询展示的脱敏内容。

### 2.2 事件写入与投影更新分离

建议把 Agent 执行链路拆成两个层次：

1. **事件日志（Event Log）**：只追加，不覆盖，保存事实；
2. **状态投影（Projection）**：从事件推导当前任务状态、用户可见时间线、审计视图。

```text
用户请求
  ↓
Agent Runtime
  ↓ append
Event Log（不可变事实流）
  ↓ consume
Projection Builder
  ↓
Task Status / Audit Timeline / Metrics
```

这样即使投影构建失败，也可以通过重放 Event Log 重新生成视图；即使用户侧状态展示异常，也能回到事实事件判断真实执行情况。

### 2.3 测试设计必须覆盖“两条正确”

Agent 审计类测试不能只验证业务结果，还要验证审计证据。

<table header-row="true" col-widths="180,300,300">
  <tr>
    <td>验证维度</td>
    <td>正确表现</td>
    <td>典型断言</td>
  </tr>
  <tr>
    <td>业务结果正确</td>
    <td>用户任务最终完成，结果符合预期</td>
    <td>任务状态为 completed，输出可访问</td>
  </tr>
  <tr>
    <td>审计链路正确</td>
    <td>每个关键动作都有事件，顺序可解释</td>
    <td>事件数量、类型、sequence、trace_id 均正确</td>
  </tr>
  <tr>
    <td>重放结果正确</td>
    <td>同一事件流重放后得到相同投影</td>
    <td>replayed_projection 与 online_projection 一致</td>
  </tr>
  <tr>
    <td>安全边界正确</td>
    <td>审计查询只返回本租户、已脱敏内容</td>
    <td>跨租户查询 403，敏感字段不可见</td>
  </tr>
</table>

---

## 3. Ginkgo 实战：验证事件追加、投影和重放一致性

### 3.1 定义 E2E 观测模型

```go
//go:build audite2e

package audite2e_test

type AuditEvent struct {
    EventID   string                 `json:"event_id"`
    TraceID   string                 `json:"trace_id"`
    TaskID    string                 `json:"task_id"`
    TenantID  string                 `json:"tenant_id"`
    Type      string                 `json:"event_type"`
    Sequence  int64                  `json:"sequence"`
    Payload   map[string]interface{} `json:"payload_redacted"`
}

type TaskProjection struct {
    TaskID             string   `json:"task_id"`
    FinalState         string   `json:"final_state"`
    TimelineEventTypes []string `json:"timeline_event_types"`
    AuditEventCount    int      `json:"audit_event_count"`
}
```

这个模型把“事件事实”和“投影结果”分开，便于在 E2E 中同时断言。

### 3.2 E2E：一次带工具调用的 Agent 任务必须生成完整审计链

```go
package audite2e_test

import (
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

var _ = Describe("Agent audit event sourcing", Label("P0", "e2e", "audit"), func() {
    It("should persist auditable events from task creation to final answer", func() {
        taskID := CreateAgentTask(CreateTaskRequest{
            TenantID: "tenant-a",
            Prompt:   "汇总本周告警并生成行动建议",
        })

        Eventually(func(g Gomega) {
            projection := GetTaskProjection(taskID)
            g.Expect(projection.FinalState).To(Equal("completed"))
        }).Should(Succeed())

        events := ListAuditEvents(taskID)
        Expect(events).To(ContainEventTypesInOrder(
            "task.created",
            "agent.plan.created",
            "tool.call.requested",
            "tool.call.completed",
            "answer.generated",
        ))

        for i, event := range events {
            Expect(event.TaskID).To(Equal(taskID))
            Expect(event.TenantID).To(Equal("tenant-a"))
            Expect(event.TraceID).NotTo(BeEmpty())
            Expect(event.Sequence).To(BeNumerically("==", i+1))
        }
    })
})
```

这里不是单独测“审计接口能返回”，而是从用户任务触发开始，完整验证执行结果与审计事实是否一致。

### 3.3 E2E：投影表清空后可通过事件重放恢复

```go
var _ = Describe("Audit replay recovery", Label("P0", "e2e", "replay"), func() {
    It("should rebuild task projection from immutable audit events", func() {
        taskID := CreateCompletedAgentTask("tenant-a")

        original := GetTaskProjection(taskID)
        Expect(original.FinalState).To(Equal("completed"))

        DeleteTaskProjectionForTest(taskID)
        TriggerReplay(ReplayRequest{TaskID: taskID})

        Eventually(func(g Gomega) {
            rebuilt := GetTaskProjection(taskID)
            g.Expect(rebuilt.FinalState).To(Equal(original.FinalState))
            g.Expect(rebuilt.TimelineEventTypes).To(Equal(original.TimelineEventTypes))
            g.Expect(rebuilt.AuditEventCount).To(Equal(original.AuditEventCount))
        }).Should(Succeed())
    })
})
```

这个用例模拟真实生产中很常见的场景：投影表被错误刷新、索引异常、缓存污染。只要事件日志可靠，系统就应该可以重建。

### 3.4 E2E：重复事件重放不能重复产生副作用

```go
var _ = Describe("Replay idempotency", Label("P0", "e2e", "idempotency"), func() {
    It("should not send duplicate notification during replay", func() {
        taskID := CreateCompletedAgentTask("tenant-a")
        before := GetNotificationCount(taskID)

        TriggerReplay(ReplayRequest{TaskID: taskID})
        TriggerReplay(ReplayRequest{TaskID: taskID})

        Consistently(func() int {
            return GetNotificationCount(taskID)
        }).Should(Equal(before))
    })
})
```

重放应该只重建投影，不应该重复发送通知、重复调用外部工具、重复扣费或重复写入下游系统。

---

## 4. Python API Testing：审计查询、脱敏和跨租户隔离

### 4.1 审计查询必须支持按 trace / task / 时间窗口定位

```python
import requests

BASE_URL = "https://agent.example.test"


def test_audit_query_by_task_id_returns_ordered_events(auth_headers):
    task_id = create_completed_agent_task(tenant_id="tenant-a")

    resp = requests.get(
        f"{BASE_URL}/api/audit/events",
        params={"task_id": task_id},
        headers=auth_headers("tenant-a"),
        timeout=10,
    )
    assert resp.status_code == 200

    events = resp.json()["events"]
    assert len(events) >= 5
    assert [e["sequence"] for e in events] == sorted(e["sequence"] for e in events)
    assert all(e["task_id"] == task_id for e in events)
    assert all(e["trace_id"] for e in events)
```

这个测试覆盖真实排障动作：拿到一个任务 ID 后，能否按顺序查到完整事件链。

### 4.2 审计载荷必须脱敏

```python
def test_audit_payload_should_redact_sensitive_fields(auth_headers):
    task_id = create_agent_task_with_secret(
        tenant_id="tenant-a",
        prompt="使用 token sk-test-secret 调用工具并总结结果",
    )
    wait_task_completed(task_id)

    resp = requests.get(
        f"{BASE_URL}/api/audit/events",
        params={"task_id": task_id},
        headers=auth_headers("tenant-a"),
        timeout=10,
    )
    assert resp.status_code == 200

    raw_text = str(resp.json())
    assert "sk-test-secret" not in raw_text
    assert "payload_hash" in raw_text
    assert "redacted" in raw_text.lower()
```

审计不是把所有原始内容暴露给所有人。对外展示的审计视图应该能证明“发生过”，但不能泄露密钥、隐私或跨租户数据。

### 4.3 跨租户审计查询必须被拒绝

```python
def test_cross_tenant_audit_query_should_be_forbidden(auth_headers):
    task_id = create_completed_agent_task(tenant_id="tenant-a")

    resp = requests.get(
        f"{BASE_URL}/api/audit/events",
        params={"task_id": task_id},
        headers=auth_headers("tenant-b"),
        timeout=10,
    )

    assert resp.status_code in (403, 404)
```

这里不要只断言“接口返回非 200”，还要在服务端日志中检查没有把 tenant-a 的事件内容写入 tenant-b 的响应体或错误信息。

---

## 5. Playwright 实战：用户侧审计时间线 E2E

### 5.1 验证用户能看到可理解的任务时间线

```python
from playwright.sync_api import expect


def test_user_can_view_agent_audit_timeline(page, base_url):
    page.goto(f"{base_url}/agent/tasks")
    page.get_by_role("button", name="新建任务").click()
    page.get_by_label("任务目标").fill("分析本周质量风险并生成建议")
    page.get_by_role("button", name="开始执行").click()

    expect(page.get_by_text("执行中")).to_be_visible()
    expect(page.get_by_text("已完成")).to_be_visible(timeout=120_000)

    page.get_by_role("button", name="查看审计时间线").click()

    expect(page.get_by_text("任务已创建")).to_be_visible()
    expect(page.get_by_text("Agent 已生成执行计划")).to_be_visible()
    expect(page.get_by_text("工具调用已完成")).to_be_visible()
    expect(page.get_by_text("最终答案已生成")).to_be_visible()
```

用户侧不一定要展示底层事件名，但必须展示可理解的业务时间线。否则审计能力只对研发有用，对真实用户和运营同学并没有帮助。

### 5.2 验证敏感字段不会出现在页面

```python
def test_audit_timeline_should_not_render_secret(page, base_url):
    task_id = create_task_with_sensitive_prompt("请使用 api_key=secret-123 完成查询")

    page.goto(f"{base_url}/agent/tasks/{task_id}/audit")
    expect(page.get_by_text("secret-123")).not_to_be_visible()
    expect(page.get_by_text("已脱敏")).to_be_visible()
```

这类用例非常适合放进回归套件，因为一次前端字段透传或后端 DTO 变更，就可能让敏感信息从审计页面泄露出去。

---

## 6. Kubernetes 演练：consumer 重启与投影重建

### 6.1 场景：投影 consumer 重启后不能丢事件

```bash
kubectl -n agent-platform rollout restart deployment/agent-projection-consumer
kubectl -n agent-platform rollout status deployment/agent-projection-consumer --timeout=120s
```

重启前后用 E2E 任务持续写入事件，验证：

1. 事件日志没有丢失；
2. consumer 恢复后能继续消费；
3. 投影最终与事件重放结果一致；
4. 没有重复通知、重复工具调用等副作用。

### 6.2 场景：审计存储短暂不可用后可补偿

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: audit-store-delay
  namespace: chaos-testing
spec:
  action: delay
  mode: one
  selector:
    namespaces:
      - agent-platform
    labelSelectors:
      app: agent-audit-store
  delay:
    latency: "1500ms"
    correlation: "80"
    jitter: "300ms"
  duration: "5m"
```

演练重点不是简单看服务是否报错，而是看延迟结束后：

- 积压事件是否被补齐；
- 审计查询是否最终完整；
- 用户侧时间线是否从“同步中”变为完整状态；
- 告警是否能指出具体滞后窗口。

---

## 7. E2E 测试用例设计：从真实客户场景组织

### 用例 1：客户发起高风险 Agent 任务后，审计链路完整可追踪

**业务场景：** 客户让 Agent 分析生产告警并调用工具生成处置建议，系统需要记录每一步决策和工具调用。

**执行步骤：**

1. 用户在前端创建 Agent 任务，输入告警分析目标。
   - 预期中间状态：任务进入 `running`，生成 `task.created` 事件。
2. Agent 生成执行计划并选择查询工具。
   - 预期中间状态：出现 `agent.plan.created` 和 `tool.call.requested`。
3. 工具调用完成，Agent 生成最终建议。
   - 预期中间状态：出现 `tool.call.completed` 和 `answer.generated`。
4. 用户打开审计时间线。
   - ✅ 最终验证点：页面展示完整业务时间线，后端事件按 sequence 有序，trace_id 一致。

### 用例 2：投影异常清空后，通过事件重放恢复用户可见状态

**业务场景：** 线上投影索引异常，需要从不可变事件日志重建任务状态和审计视图。

**执行步骤：**

1. 创建并完成一个 Agent 任务。
   - 预期中间状态：任务状态为 `completed`，审计事件完整。
2. 在测试环境清空该任务投影。
   - 预期中间状态：用户侧临时看不到完整时间线，但 Event Log 仍存在。
3. 触发 replay job。
   - 预期中间状态：投影 consumer 开始重建。
4. 查询任务状态和审计时间线。
   - ✅ 最终验证点：重建后的 projection 与原始 projection 一致，且没有重复通知或重复工具调用。

### 用例 3：审计查询必须保护租户边界和敏感字段

**业务场景：** 多租户客户查询自己的 Agent 审计记录，系统不能泄露其他租户或敏感参数。

**执行步骤：**

1. tenant-a 创建包含敏感参数的 Agent 任务。
   - 预期中间状态：原始事件写入时保留 hash，展示 payload 已脱敏。
2. tenant-a 查询审计时间线。
   - 预期中间状态：可以看到事件类型、时间、工具名和脱敏摘要。
3. tenant-b 使用同一 task_id 查询。
   - 预期中间状态：接口返回 403 或 404。
4. 检查响应体和前端页面。
   - ✅ 最终验证点：tenant-b 看不到任何 tenant-a 内容；tenant-a 页面不展示密钥明文。

### 用例 4：consumer 重启期间事件积压，恢复后最终一致

**业务场景：** 审计 projection consumer 发布升级，期间 Agent 任务仍在运行。

**执行步骤：**

1. 持续创建 Agent 任务并写入审计事件。
   - 预期中间状态：Event Log 写入成功。
2. 重启 projection consumer。
   - 预期中间状态：部分任务时间线显示“同步中”。
3. consumer 恢复后等待积压消费完成。
   - 预期中间状态：lag 指标回落。
4. 对比在线 projection 与 replay projection。
   - ✅ 最终验证点：两者一致，任务最终状态正确，未产生重复副作用。

---

## 8. 质量度量：Agent 审计能力的关键指标

<table header-row="true" col-widths="220,300,220">
  <tr>
    <td>指标</td>
    <td>含义</td>
    <td>建议目标</td>
  </tr>
  <tr>
    <td>audit_event_completeness</td>
    <td>关键业务动作是否都有审计事件</td>
    <td>核心链路 100%</td>
  </tr>
  <tr>
    <td>projection_replay_consistency</td>
    <td>重放投影与在线投影一致比例</td>
    <td>> 99.9%</td>
  </tr>
  <tr>
    <td>audit_query_latency_p95</td>
    <td>审计查询 P95 延迟</td>
    <td>< 2s</td>
  </tr>
  <tr>
    <td>redaction_escape_count</td>
    <td>脱敏逃逸次数</td>
    <td>0</td>
  </tr>
  <tr>
    <td>cross_tenant_audit_violation</td>
    <td>跨租户审计越权次数</td>
    <td>0</td>
  </tr>
</table>

---

## 9. 课后思考题

1. 如果 Agent 的最终答案正确，但审计事件缺失了工具调用参数摘要，这个任务应该算成功还是部分失败？为什么？
2. 事件日志不可变与用户“删除数据”诉求冲突时，系统应如何设计脱敏、逻辑删除和合规保留？
3. 事件重放时，哪些动作只能重建投影，绝不能再次执行真实副作用？请列出你的系统清单。
4. 如果 replay projection 与 online projection 不一致，你会优先检查事件顺序、消费幂等、还是投影代码版本？
5. 审计查询页面应该展示底层事件名，还是业务化描述？如何兼顾研发排障和客户可理解性？

---

## 10. 今日小结

今天我们把 AI Agent 的质量关注点从“异步事件是否可靠收敛”继续推进到“执行过程是否可追踪、可审计、可重放”。事件溯源与审计日志不是附加功能，而是生产级 Agent 的基础设施。

对测试开发而言，最重要的转变是：不要只验证任务最后是否完成，还要验证完成路径是否留下可信证据；不要只检查日志里有没有一行记录，而要检查这批事件能否重建同一个状态；不要只看研发能不能排查，还要看客户、运营、合规是否能理解这条时间线。

明天可以继续深入：**AI Agent 数据版本、知识库快照与可复现实验测试**，把“同一输入在同一上下文下是否能稳定复现”纳入质量体系。
