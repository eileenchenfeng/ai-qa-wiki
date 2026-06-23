---
title: "每日 AI 学习笔记｜Day 60：AI Agent 补偿事务与最终一致性测试"
date: 2026-06-14
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, saga, compensation, eventual-consistency, Ginkgo, Playwright, Kubernetes, API-Testing]
---

# 每日 AI 学习笔记｜Day 60：AI Agent 补偿事务与最终一致性测试

<callout icon="star" bgc="4">
**核心总结：** 当 AI Agent 从“只会回答”升级为“会代表用户执行业务动作”后，真正高风险的质量问题就不再是某一步报错，而是**跨系统动作做了一半**：工单创建成功但通知失败、审批单已提交但会话状态仍显示处理中、知识库写入成功但审计日志缺失、回调重放导致任务重复落库。对资深测试开发来说，补偿事务与最终一致性测试的核心，不是验证“失败后能不能 retry 一下”，而是验证 **系统是否定义了可恢复边界、是否记录了可追踪状态、是否在补偿期间对用户诚实展示、是否在最终一致后收敛到唯一正确结果**。工程上要同时从 **Ginkgo** 验证 Saga 编排与补偿顺序、从 **Python / API Testing** 校验状态机和幂等键、从 **Playwright** 验证前端对“处理中 / 补偿中 / 已恢复”的展示、从 **Kubernetes** 演练异步 worker 崩溃与恢复。成熟的 AI Agent 质量体系，不是每一步都永远成功，而是失败发生后仍能保证：**状态可见、补偿可控、结果唯一、用户不被误导。**
</callout>

很多 AI Agent 已经不只是“给出建议”，而是会直接创建工单、提交审批、写入知识库、触发 Webhook、发送 IM 通知，甚至发起自动化运维动作。只要这些动作跨越多个系统，就一定会遇到一个经典难题：**局部成功、全局未完成**。

因此，今天这篇学习笔记聚焦一个极其关键但常被低估的话题：**如何为 AI Agent 设计补偿事务（Compensation / Saga）与最终一致性（Eventual Consistency）测试体系**，确保系统在部分失败、回调延迟、重复投递、异步恢复场景下，依然能把任务收敛到用户可理解、业务可接受的正确状态。

{/* truncate */}

## 0. 今日核心要点

1. **AI Agent 的事务问题，本质是跨系统动作无法依赖单库 ACID 事务兜底。**
2. **补偿不是“回滚一切”，而是按业务语义撤销已执行副作用。**
3. **最终一致性测试最重要的不是“最后成功了”，而是中间状态是否可见、可追踪、可恢复。**
4. **每个异步步骤都必须有幂等键、状态机和重试边界，否则补偿会制造二次事故。**
5. **E2E 用例必须覆盖“部分成功 + 延迟恢复 + 前端观察”完整链路，而不是只测单接口。**
6. **最危险的不是系统失败，而是系统已经偏离一致性却仍向用户展示“已完成”。**

---

## 1. 核心理论：为什么 AI Agent 特别需要补偿事务与最终一致性测试

### 1.1 AI Agent 正在从“建议型系统”走向“执行型系统”

当 Agent 只负责输出文本时，失败通常体现在回答错误、超时或体验抖动；但当它开始替用户执行动作后，请求链路往往变成：

- 规划任务
- 调用工具创建业务对象
- 写入状态中心或数据库
- 发送通知 / 回调外部系统
- 更新前端任务状态
- 记录审计日志与追踪信息

这意味着一个用户点击“执行”后，系统内部很可能已经发生了多个不可逆副作用。此时真正的问题不是“报错没有”，而是 **已经成功的那部分动作怎么处理，没成功的那部分又如何收敛**。

### 1.2 什么叫补偿事务，不等于传统数据库回滚

传统数据库事务强调原子性：要么都成功，要么都回滚。但跨系统场景里，很多动作已经提交到第三方，无法真的 `rollback`。因此，工程上通常采用 **Saga / 补偿事务** 思路：

1. 主流程按步骤推进；
2. 某一步失败后，不强行回滚数据库事务；
3. 对已经执行成功的动作，执行对应的补偿动作；
4. 最终把全局状态收敛到“已完成”或“已补偿终止”等稳定态。

### 1.3 AI Agent 中最常见的 5 类不一致场景

<table header-row="true" col-widths="150,220,240,220">
  <tr>
    <td>场景</td>
    <td>典型现象</td>
    <td>用户风险</td>
    <td>测试关注点</td>
  </tr>
  <tr>
    <td>部分成功</td>
    <td>工单已创建，但通知发送失败</td>
    <td>用户误以为全流程未执行</td>
    <td>状态拆分、补偿触发、结果可追踪</td>
  </tr>
  <tr>
    <td>回调延迟</td>
    <td>后端已完成，前端长时间显示处理中</td>
    <td>重复点击、重复执行</td>
    <td>轮询超时、最终一致收敛、按钮禁用</td>
  </tr>
  <tr>
    <td>重复投递</td>
    <td>消息队列至少一次投递导致重复消费</td>
    <td>重复扣费、重复创建对象</td>
    <td>幂等键、去重存储、重放测试</td>
  </tr>
  <tr>
    <td>补偿失败</td>
    <td>创建成功后删除失败，状态卡在中间态</td>
    <td>系统长期脏状态</td>
    <td>死信队列、人工接管、告警可观测</td>
  </tr>
  <tr>
    <td>状态乱序</td>
    <td>先收到完成回调，后收到处理中回调</td>
    <td>最终界面回退到旧状态</td>
    <td>状态机单向推进、版本号校验</td>
  </tr>
</table>

<callout icon="bulb" bgc="3">
**工程提醒：** 对 AI Agent 而言，“最后成功了”并不代表质量合格。如果过程中曾经向用户暴露错误状态、触发重复副作用、或者让系统进入难以恢复的中间态，这依然是高风险缺陷。
</callout>

---

## 2. 方法框架：先定义状态机，再设计补偿与一致性断言

### 2.1 先把任务状态拆成可验证的阶段

建议把一个可执行 Agent 任务至少拆成以下状态：

1. `planned`：规划完成，尚未执行副作用；
2. `running`：已开始执行，主流程推进中；
3. `waiting_callback`：等待异步确认或第三方回调；
4. `compensating`：检测到局部失败，正在执行补偿；
5. `completed`：全部动作完成且结果一致；
6. `compensated`：主流程未完成，但系统已通过补偿收敛到稳定失败态；
7. `manual_intervention_required`：自动补偿失败，需要人工接管。

### 2.2 每个状态都要绑定清晰的用户语义

<table header-row="true" col-widths="170,220,220,180">
  <tr>
    <td>系统状态</td>
    <td>后端含义</td>
    <td>前端展示建议</td>
    <td>优先级</td>
  </tr>
  <tr>
    <td>running</td>
    <td>主流程执行中，尚未确认副作用闭环</td>
    <td>显示处理中，禁止重复提交</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>waiting_callback</td>
    <td>外部系统已接单，等待异步回执</td>
    <td>显示“等待外部系统确认”</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>compensating</td>
    <td>检测到部分失败，正在撤销已执行动作</td>
    <td>显示“正在恢复一致状态，请勿重试”</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>compensated</td>
    <td>自动补偿完成，系统回到稳定失败态</td>
    <td>显示已终止并说明已撤销哪些动作</td>
    <td>P0/P1</td>
  </tr>
  <tr>
    <td>manual_intervention_required</td>
    <td>自动恢复失败，需要人工处理</td>
    <td>显示人工介入入口与上下文编号</td>
    <td>P1</td>
  </tr>
</table>

### 2.3 测试设计时必须回答“三个唯一性问题”

1. **唯一结果**：最终用户只能看到一个稳定结论，不能一会成功一会失败；
2. **唯一副作用**：外部对象最多只被创建 / 提交 / 扣费一次；
3. **唯一状态推进**：状态机只能向前收敛，不能被旧事件回退。

如果这三个“唯一性”无法被自动化断言，最终一致性大概率只是口头承诺。

---

## 3. Ginkgo 实战：把 Saga 编排与补偿顺序做成 E2E 断言

### 3.1 先定义运行结果与补偿轨迹结构

```go
//go:build sagae2e

package sagae2e_test

type TaskRunResult struct {
    TaskID             string   `json:"task_id"`
    FinalState         string   `json:"final_state"`
    UserVisibleState   string   `json:"user_visible_state"`
    ExecutedActions    []string `json:"executed_actions"`
    CompensationTrail  []string `json:"compensation_trail"`
    ExternalObjectRefs []string `json:"external_object_refs"`
}
```

这个结构的价值在于：它把“任务最终有没有一致收敛”从日志猜测，变成 **可以被 E2E 明确断言的事实模型**。

### 3.2 E2E：通知失败时，主业务成功但要记录补偿边界

```go
package sagae2e_test

import (
    "context"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type SagaRunner interface {
    Run(ctx context.Context, input string, inject map[string]string) (*TaskRunResult, error)
}

var _ = Describe("Saga compensation", Label("P0", "e2e", "consistency"), func() {
    var runner SagaRunner

    BeforeEach(func() {
        runner = NewSagaRunnerFromEnv()
    })

    It("should keep business object and mark notification as compensatable when notification fails", func() {
        ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
        defer cancel()

        result, err := runner.Run(ctx,
            "创建发布单并通知值班群",
            map[string]string{"notify-service": "500"},
        )
        Expect(err).NotTo(HaveOccurred())
        Expect(result.FinalState).To(Equal("completed_with_partial_compensation"))
        Expect(result.UserVisibleState).To(Equal("通知补发中"))
        Expect(result.ExecutedActions).To(ContainElement("create_release_ticket"))
        Expect(result.ExecutedActions).NotTo(ContainElement("create_release_ticket_again"))
        Expect(result.CompensationTrail).To(ContainElement("schedule_notification_retry"))
        Expect(result.ExternalObjectRefs).To(HaveLen(1))
    })
})
```

这里的重点不是把所有失败都算成全局失败，而是验证：**业务主对象是否只创建一次，且系统是否清楚告诉用户还有哪一段在补偿。**

### 3.3 E2E：审批已提交但审计写入失败时，必须进入补偿态而不是假装完成

```go
It("should enter compensating state when audit log persistence fails after approval submit", func() {
    ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
    defer cancel()

    result, err := runner.Run(ctx,
        "提交今晚发布审批并登记审计记录",
        map[string]string{"audit-log-service": "timeout"},
    )
    Expect(err).NotTo(HaveOccurred())
    Expect(result.FinalState).To(Equal("compensating"))
    Expect(result.UserVisibleState).To(Equal("正在恢复一致状态"))
    Expect(result.ExecutedActions).To(ContainElement("submit_release_approval"))
    Expect(result.CompensationTrail).To(ContainElement("query_approval_status"))
    Expect(result.CompensationTrail).To(ContainElement("rebuild_audit_log"))
})
```

这条用例要验证的是：**系统是否承认自己还没完全收敛，而不是为了“看起来成功”直接展示完成态。**

### 3.4 E2E：重复回调到达时，不能让状态机倒退

```go
It("should ignore duplicated or out-of-order callbacks", func() {
    ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
    defer cancel()

    result, err := runner.Run(ctx,
        "创建变更任务并等待异步回调",
        map[string]string{"callback-mode": "completed_then_running"},
    )
    Expect(err).NotTo(HaveOccurred())
    Expect(result.FinalState).To(Equal("completed"))
    Expect(result.UserVisibleState).To(Equal("已完成"))
    Expect(result.CompensationTrail).NotTo(ContainElement("rollback_to_running"))
})
```

这类问题在线上很常见，根因往往不是主逻辑错，而是 **旧事件覆盖新状态**。

---

## 4. Python / API Testing：校验状态机、幂等键与最终一致性收敛

### 4.1 查询任务状态轨迹，验证是否单向推进

```python
from __future__ import annotations

from dataclasses import dataclass
import requests


@dataclass
class TaskStateEvent:
    state: str
    version: int
    ts: str


def fetch_task_timeline(base_url: str, task_id: str) -> list[TaskStateEvent]:
    resp = requests.get(f"{base_url}/api/tasks/{task_id}/timeline", timeout=10)
    resp.raise_for_status()
    body = resp.json()
    return [
        TaskStateEvent(
            state=item["state"],
            version=item["version"],
            ts=item["ts"],
        )
        for item in body["events"]
    ]


def assert_monotonic_version(events: list[TaskStateEvent]) -> None:
    versions = [item.version for item in events]
    assert versions == sorted(versions), f"non-monotonic versions: {versions}"
```

### 4.2 校验补偿后是否收敛到允许终态

```python
ALLOWED_TERMINAL_STATES = {"completed", "compensated", "manual_intervention_required"}


def assert_terminal_state(events: list[TaskStateEvent]) -> str:
    final_state = events[-1].state
    assert final_state in ALLOWED_TERMINAL_STATES, f"unexpected final state: {final_state}"
    return final_state
```

### 4.3 Contract：同一幂等键重复执行，不允许重复创建外部对象

```python
import requests


def test_same_idempotency_key_should_not_create_duplicate_ticket():
    payload = {
        "input": "创建今晚发布单并同步通知",
        "idempotency_key": "release-2026-06-14-001",
    }

    first = requests.post("https://agent.example.com/api/agent/run", json=payload, timeout=20)
    second = requests.post("https://agent.example.com/api/agent/run", json=payload, timeout=20)

    first.raise_for_status()
    second.raise_for_status()

    body1 = first.json()
    body2 = second.json()

    assert body1["ticket_id"] == body2["ticket_id"]
    assert body2["deduplicated"] is True
    assert body2["status"] in {"running", "waiting_callback", "completed"}
```

对最终一致性系统来说，**幂等键不是优化项，而是生死线**。没有幂等，补偿和重试本身就会成为事故来源。

### 4.4 Polling：验证系统能在超时窗口内收敛

```python
import time
import requests


def wait_until_terminal(base_url: str, task_id: str, timeout_s: int = 120) -> str:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = requests.get(f"{base_url}/api/tasks/{task_id}", timeout=5)
        resp.raise_for_status()
        state = resp.json()["state"]
        if state in {"completed", "compensated", "manual_intervention_required"}:
            return state
        time.sleep(3)
    raise AssertionError(f"task {task_id} did not converge within {timeout_s}s")
```

如果系统长时间停在 `running` 或 `compensating`，即便最后某天会恢复，也不能算一个合格的生产级实现。

---

## 5. Playwright 实战：验证前端对“一致性恢复过程”真实可见

### 5.1 为什么最终一致性一定要做前端验证

用户并不会盯着 trace、状态机版本号和消息队列 offset；用户只会看到：

- 页面是不是一直转圈；
- 有没有出现“处理中 / 补偿中 / 已恢复”的明确提示；
- 按钮是不是被正确禁用；
- 最后展示的结果是不是唯一且稳定。

所以，前端测试要验证的不是样式，而是 **系统是否把恢复过程诚实展示给用户**。

### 5.2 Playwright：进入补偿态时必须禁止重复提交

```python
from playwright.sync_api import Page, expect


def test_compensating_state_should_disable_resubmit(page: Page):
    page.goto("https://agent.example.com/workspace/ws-release?inject_fault=audit_timeout")
    page.get_by_placeholder("输入任务目标").fill("提交今晚发布审批并登记审计记录")
    page.get_by_role("button", name="发送").click()

    expect(page.get_by_text("正在恢复一致状态，请勿重复提交")).to_be_visible(timeout=20_000)
    expect(page.get_by_role("button", name="重新执行")).to_be_disabled()
    expect(page.get_by_role("button", name="查看恢复详情")).to_be_visible()
```

### 5.3 Playwright：补偿完成后必须展示唯一终态与补偿说明

```python
from playwright.sync_api import Page, expect


def test_compensated_state_should_show_single_terminal_result(page: Page):
    page.goto("https://agent.example.com/workspace/ws-release?inject_fault=notify_fail_then_compensate")
    page.get_by_placeholder("输入任务目标").fill("创建发布单并通知值班群")
    page.get_by_role("button", name="发送").click()

    expect(page.get_by_text("主任务已完成，通知正在补发")).to_be_visible(timeout=20_000)
    expect(page.get_by_text("发布单已创建")).to_be_visible()
    expect(page.get_by_text("未发现重复创建")).to_be_visible()
    expect(page.get_by_role("button", name="再次创建发布单")).not_to_be_visible()
```

### 5.4 Playwright：人工介入场景必须暴露诊断编号

```python
from playwright.sync_api import Page, expect


def test_manual_intervention_should_expose_recovery_ticket(page: Page):
    page.goto("https://agent.example.com/workspace/ws-release?inject_fault=compensation_fail")
    page.get_by_placeholder("输入任务目标").fill("创建发布单并回写审计记录")
    page.get_by_role("button", name="发送").click()

    expect(page.get_by_text("自动恢复失败，需要人工介入")).to_be_visible(timeout=20_000)
    expect(page.get_by_text("恢复单号")).to_be_visible()
    expect(page.get_by_role("button", name="复制上下文信息")).to_be_visible()
```

如果前端把 `compensating`、`compensated`、`manual_intervention_required` 全都简化成一句“任务失败”，用户就无法判断自己是否需要重试、等待还是找人处理。

---

## 6. Kubernetes 实战：把异步补偿与最终一致性演练做成持续能力

### 6.1 用 CronJob 周期性演练 Worker 崩溃后的恢复能力

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: agent-saga-recovery-drill
spec:
  schedule: "0 11 * * 2,6"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: drill-runner
              image: python:3.11-slim
              command:
                - /bin/sh
                - -c
                - |
                  python run_saga_recovery_drill.py \
                    --scenario=worker-crash-after-ticket-created \
                    --target-env=staging \
                    --assert-terminal-state=compensated
              env:
                - name: BASE_URL
                  value: "https://agent.example.com"
                - name: ALERT_WEBHOOK
                  valueFrom:
                    secretKeyRef:
                      name: qa-drill-secret
                      key: webhook
```

### 6.2 建议优先覆盖的 5 类一致性演练场景

1. **主动作成功、通知失败**：验证业务对象保留与补发补偿；
2. **主动作成功、审计失败**：验证恢复日志与状态补写；
3. **回调重复 / 乱序**：验证状态机单向推进；
4. **worker 崩溃后重启恢复**：验证 checkpoint 与任务续跑；
5. **补偿动作自身失败**：验证人工接管与告警链路。

### 6.3 每次演练至少要沉淀的 4 类产物

<table header-row="true" col-widths="180,250,260,180">
  <tr>
    <td>产物</td>
    <td>说明</td>
    <td>用途</td>
    <td>优先级</td>
  </tr>
  <tr>
    <td>场景编号</td>
    <td>明确哪一段 Saga、哪种失败模式</td>
    <td>方便回归与复盘对齐</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>状态轨迹</td>
    <td>记录状态迁移、版本号、终态</td>
    <td>验证是否一致收敛</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>副作用清单</td>
    <td>记录创建了哪些外部对象、是否重复</td>
    <td>验证幂等与补偿边界</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>恢复建议</td>
    <td>自动补偿、人工接管、后续修复项</td>
    <td>支持发布门禁和问题治理</td>
    <td>P1</td>
  </tr>
</table>

<callout icon="bulb" bgc="3">
**质量建议：** 对补偿事务的测试，最怕只验证“补偿逻辑被调用过”。更高价值的做法，是追问补偿后系统到底收敛到了什么终态、用户看到了什么、有没有残留副作用、还能不能安全重试。
</callout>

---

## 7. 课后思考题

1. 如果主业务对象已创建成功，但通知失败且补发还在进行中，你会把这个场景定义为成功、部分成功还是失败？为什么？
2. 如果补偿动作本身也失败了，你更倾向于继续自动重试，还是尽快切换到人工接管？判断边界是什么？
3. 你的业务里最危险的重复副作用是什么：重复扣费、重复审批、重复发消息，还是重复执行运维动作？为什么？
4. 如果最终一致性需要 2 分钟才能收敛，你会如何设计前端提示和按钮状态，避免用户误操作？
5. 你的团队目前对 Saga / 补偿事务最薄弱的一环是什么：状态机定义、幂等键、补偿脚本、回调治理，还是人工介入流程？如果只能先补一个，你会先补哪个？

---

## 8. 今日小结

今天我们把关注点从“依赖出问题时怎么降级”进一步推进到“跨系统动作已经做了一半时，怎么恢复一致性”。对 AI Agent 来说，这一步非常关键，因为它决定了系统是否真的具备从建议走向执行的质量基础。

补偿事务与最终一致性测试的本质，不是给系统多写几个 retry，而是建立一整套可验证的恢复闭环：**先定义状态机，再设计补偿边界，再用 Ginkgo、Python、Playwright 和 Kubernetes 把状态收敛、副作用唯一、用户可见、人工可接管这些要求全部落成自动化资产。** 当系统在部分失败后仍能做到“结果唯一、状态透明、恢复可追踪、用户不被误导”，这套 AI Agent 才算真正具备生产级执行能力。
