---
title: "每日 AI 学习笔记｜Day 50：AI Agent 长任务执行与异步工作流可靠性测试"
date: 2026-06-04
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, async-workflow, reliability, Ginkgo, Playwright, Kubernetes, API-Testing]
---

# 每日 AI 学习笔记｜Day 50：AI Agent 长任务执行与异步工作流可靠性测试

<callout icon="star" bgc="4">

**核心总结：** 当 AI Agent 从“单轮即时回答”走向“分钟级 / 小时级的长任务执行”时，测试重点会从结果正确性扩展到 **任务状态机是否清晰、断点是否可恢复、重试是否幂等、异步回调是否可信、超时与取消是否可控、跨组件链路是否最终一致**。高质量测试应把长任务拆成 **任务创建、计划冻结、异步执行、进度回传、失败重试、人工确认、断点恢复、结果归档** 八个可验证环节，并采用 **Ginkgo 做后端任务编排 E2E、Python / API 做回调契约与幂等校验、Playwright 做用户视角的进度可观测性验证、K8s 做 Worker 漂移与重启恢复演练** 的组合方案。核心原则：**不是验证 Agent 能不能把任务“跑完”，而是验证它能不能在长链路里稳定、可追踪、可恢复地跑完。**

</callout>

很多团队在做 Agent 质量时，往往先把重点放在回答质量、工具调用成功率、单次任务延迟这些指标上。但一旦业务进入真正的生产场景，用户常见需求很快就不再是“帮我答一下”，而是“帮我整理一批数据并生成报告”“持续跟踪某个环境直到条件满足再通知我”“执行多阶段检查，遇到高风险步骤先暂停确认”。

这类任务通常具备明显的异步特征：执行时间长、依赖外部系统、需要多次轮询或回调、可能跨进程跨 Pod、可能中途失败后重试，还经常伴随人工确认、计划续跑和结果归档。如果测试仍停留在同步接口返回 200 就算成功，很容易漏掉最危险的质量问题：**重复执行造成副作用、任务丢失、状态回退、用户界面显示完成但后台仍在跑、回调重复到达导致结果污染**。

{/* truncate */}

## 0. 今日核心要点

1. **长任务测试的核心不是“最终完成”，而是“执行过程始终可控”**。
2. **必须显式建模任务状态机**：queued、running、waiting_approval、retrying、partial_completed、failed、cancelled、completed。
3. **幂等与断点恢复是 P0 能力**：任何重试、重放、Worker 重启都不能放大副作用。
4. **异步回调与轮询都要测**：状态一致性、重复通知、乱序事件、延迟事件都属于高风险分支。
5. **E2E 用例要围绕完整业务链路组织**：用户发起长任务 → Agent 编排 → 子任务异步推进 → 中途失败重试 / 等待确认 → 最终完成或安全终止。
6. **用户可观测性非常关键**：看不到进度、原因和下一步动作的长任务，在线上几乎无法运维。

---

## 1. 核心理论：为什么长任务 Agent 比同步 Agent 更难测

### 1.1 从“请求-响应”到“任务-状态机”

同步型 Agent 通常是一条短链路：接收输入、做推理、调用少量工具、返回结果。只要接口超时可控、结果结构正确，很多问题就能较快暴露。

但长任务型 Agent 的本质更接近一个 **状态驱动的工作流系统**。用户发起请求后，系统不一定马上完成，而是先创建任务，再把计划拆成多个步骤，交给队列、Worker、调度器、回调处理器或人工审批节点去异步推进。此时，测试对象已经不只是模型输出，而是整个任务生命周期。

一个最常见的误区是：把异步任务当成“多等一会儿的同步接口”来测。这样会漏掉大量只会在 **超时、重试、进程重启、重复回调、用户刷新页面、审批延迟** 时出现的缺陷。

### 1.2 长任务 Agent 最常见的六类质量事故

1. **状态丢失（State Lost）**：任务从 running 直接消失，或者重启后回到 queued；
2. **重复执行（Duplicate Execution）**：同一步骤因超时重试被执行两次，导致重复建资源、重复发通知；
3. **乱序落库（Out-of-Order Commit）**：较早的旧结果覆盖了较新的状态；
4. **假完成（False Completion）**：UI 已显示完成，但后台子任务仍未结束；
5. **恢复失效（Broken Resume）**：Worker 重启后无法从 checkpoint 继续，只能整单重跑；
6. **取消失效（Unsafe Cancel）**：用户点了取消，但任务仍继续执行高风险动作。

从测试角度看，这些问题比“一次回答不准确”更危险，因为它们通常带有 **真实副作用**，而且排查成本很高。

### 1.3 面向 QA 的关键指标设计

```text
TSR (Task Success Rate)         = 完整链路成功完成的长任务数 / 总长任务数
CPR (Checkpoint Recovery Rate)  = 发生中断后成功从断点恢复的次数 / 总中断次数
IER (Idempotent Execution Rate) = 重试场景中未产生重复副作用的次数 / 总重试次数
CSC (Callback State Consistency)= 回调后状态与最终持久化状态一致的次数 / 总回调次数
CCR (Cancellation Compliance)   = 收到取消后未再继续高风险执行的次数 / 总取消次数
VTR (Visibility Transparency)   = 用户可见正确进度/原因/下一步的任务数 / 总任务数
```

如果团队已经开始做生产治理，我建议再加两个发布门禁指标：

- **P95 Time-To-Checkpoint**：任务从开始执行到落下可恢复 checkpoint 的耗时；
- **Duplicate Side Effect Count**：重复建单、重复写库、重复发消息等副作用次数，必须长期接近 0。

---

## 2. 测试建模：把长任务拆成可验证对象

### 2.1 建议先定义最小任务状态模型

没有结构化状态模型，长任务测试就会退化成“不断轮询直到看起来结束”。建议至少暴露如下最小对象：

```go
package asyncagent

type TaskStatus string

const (
    StatusQueued             TaskStatus = "queued"
    StatusRunning            TaskStatus = "running"
    StatusWaitingApproval    TaskStatus = "waiting_approval"
    StatusRetrying           TaskStatus = "retrying"
    StatusPartiallyCompleted TaskStatus = "partial_completed"
    StatusFailed             TaskStatus = "failed"
    StatusCancelled          TaskStatus = "cancelled"
    StatusCompleted          TaskStatus = "completed"
)

type AgentTask struct {
    TaskID         string            `json:"task_id"`
    SessionID      string            `json:"session_id"`
    Goal           string            `json:"goal"`
    Status         TaskStatus        `json:"status"`
    CurrentStep    string            `json:"current_step"`
    Progress       int               `json:"progress"`
    NeedsApproval  bool              `json:"needs_approval"`
    CheckpointID   string            `json:"checkpoint_id"`
    SideEffects    map[string]int    `json:"side_effects"`
    LastError      string            `json:"last_error"`
    Version        int64             `json:"version"`
}

type TaskEvent struct {
    EventID        string `json:"event_id"`
    TaskID         string `json:"task_id"`
    EventType      string `json:"event_type"` // step_started, callback_received, retry_scheduled, task_resumed
    StepName       string `json:"step_name"`
    Attempt        int    `json:"attempt"`
    IdempotencyKey string `json:"idempotency_key"`
    Detail         string `json:"detail"`
}
```

这个模型的价值，在于它把很多“经验判断”变成了可断言对象：

- 当前任务是否真的进入了 waiting_approval，而不是只在前端做了假提示；
- checkpoint 是否真实存在，还是日志里写了一句“已保存”；
- 重试时是否保留相同的 idempotency key；
- 任务最终状态与事件流是否一致。

### 2.2 高价值 E2E 场景：发起长任务 → 中途失败 → 从断点恢复 → 人工确认 → 最终归档

建议用完整链路来测，而不是拆成几个零碎接口用例：

1. 用户提交任务：“生成环境巡检报告，自动完成只读检查，高风险修复前必须确认”；
2. 系统创建任务，状态进入 queued → running；
3. 中途一个只读子任务超时，系统落 checkpoint 并进入 retrying；
4. Worker 重启后，任务从 checkpoint 恢复，而不是全量重跑；
5. 后续遇到高风险修复动作，任务转 waiting_approval；
6. 用户批准后继续执行，并把结果归档；
7. 最终验证：无重复副作用、进度合理推进、事件链可追溯、UI 与后台状态一致。

这种 E2E 场景能一次性把 **状态机、恢复、幂等、审批边界、最终一致性** 串起来，是最有价值的长链路用例。

---

## 3. Ginkgo 实战：验证状态机、断点恢复与取消边界

### 3.1 抽象最小客户端接口

```go
//go:build async_agent_e2e

package asyncagent_test

import (
    "context"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type AsyncAgentClient interface {
    CreateTask(ctx context.Context, sessionID, userID, goal string) (string, error)
    GetTask(ctx context.Context, taskID string) (*AgentTask, error)
    GetTaskEvents(ctx context.Context, taskID string) ([]TaskEvent, error)
    InjectStepFailure(ctx context.Context, taskID, step, failureType string) error
    RestartWorker(ctx context.Context, workerName string) error
    ApproveTaskStep(ctx context.Context, taskID, stepName string) error
    CancelTask(ctx context.Context, taskID string) error
}
```

### 3.2 E2E 用例：失败后从 checkpoint 恢复，审批前不得产生高风险副作用

```go
var _ = Describe("Async agent workflow", Label("async", "P0", "e2e"), func() {
    var client AsyncAgentClient

    BeforeEach(func() {
        client = NewAsyncAgentClientFromEnv()
    })

    It("should resume from checkpoint and block risky action before approval", func() {
        ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
        defer cancel()

        taskID, err := client.CreateTask(
            ctx,
            "async-session-001",
            "qa-user-01",
            "生成环境巡检报告，自动完成只读检查；如需执行修复动作必须先确认",
        )
        Expect(err).NotTo(HaveOccurred())

        By("在只读步骤注入超时，验证系统进入重试/恢复路径")
        Expect(client.InjectStepFailure(ctx, taskID, "fetch_cluster_snapshot", "timeout")).To(Succeed())

        Eventually(func(g Gomega) {
            task, err := client.GetTask(ctx, taskID)
            g.Expect(err).NotTo(HaveOccurred())
            g.Expect(task.Status).To(Or(Equal(StatusRetrying), Equal(StatusRunning), Equal(StatusWaitingApproval)))
            g.Expect(task.CheckpointID).NotTo(BeEmpty())
        }).WithTimeout(90 * time.Second).WithPolling(5 * time.Second).Should(Succeed())

        By("模拟 Worker 重启，验证任务可从断点恢复")
        Expect(client.RestartWorker(ctx, "async-agent-worker-0")).To(Succeed())

        Eventually(func(g Gomega) {
            events, err := client.GetTaskEvents(ctx, taskID)
            g.Expect(err).NotTo(HaveOccurred())

            var resumed bool
            for _, e := range events {
                if e.EventType == "task_resumed" && e.StepName == "fetch_cluster_snapshot" {
                    resumed = true
                }
            }
            g.Expect(resumed).To(BeTrue())
        }).WithTimeout(2 * time.Minute).WithPolling(5 * time.Second).Should(Succeed())

        By("进入高风险步骤前，任务必须等待人工确认")
        Eventually(func() TaskStatus {
            task, _ := client.GetTask(ctx, taskID)
            if task == nil {
                return ""
            }
            return task.Status
        }).WithTimeout(2 * time.Minute).WithPolling(5 * time.Second).Should(Equal(StatusWaitingApproval))

        task, err := client.GetTask(ctx, taskID)
        Expect(err).NotTo(HaveOccurred())
        Expect(task.SideEffects["apply_fix_count"]).To(Equal(0)) // ✅ 中间验证点：确认前不得修复

        By("人工确认后任务继续，并最终完成")
        Expect(client.ApproveTaskStep(ctx, taskID, "apply_fix")).To(Succeed())

        Eventually(func() TaskStatus {
            task, _ := client.GetTask(ctx, taskID)
            if task == nil {
                return ""
            }
            return task.Status
        }).WithTimeout(2 * time.Minute).WithPolling(5 * time.Second).Should(Equal(StatusCompleted))
    })
})
```

### 3.3 P0 补充用例：取消后不得继续执行高风险动作

```go
It("should stop risky execution after user cancellation", func() {
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
    defer cancel()

    taskID, err := client.CreateTask(
        ctx,
        "async-session-cancel-001",
        "qa-user-02",
        "检查生产环境配置漂移，如需修复请先给我预案",
    )
    Expect(err).NotTo(HaveOccurred())

    Eventually(func() TaskStatus {
        task, _ := client.GetTask(ctx, taskID)
        if task == nil {
            return ""
        }
        return task.Status
    }).Should(Or(Equal(StatusRunning), Equal(StatusWaitingApproval)))

    Expect(client.CancelTask(ctx, taskID)).To(Succeed())

    Eventually(func() TaskStatus {
        task, _ := client.GetTask(ctx, taskID)
        if task == nil {
            return ""
        }
        return task.Status
    }).Should(Equal(StatusCancelled))

    task, err := client.GetTask(ctx, taskID)
    Expect(err).NotTo(HaveOccurred())
    Expect(task.SideEffects["prod_write_count"]).To(Equal(0))
})
```

这个用例非常关键，因为很多系统虽然支持“取消”按钮，但只是取消了前端展示，没有真正阻断后台执行。

---

## 4. Python / API Testing：把回调契约、幂等和乱序事件测扎实

### 4.1 任务创建契约：创建后必须返回可轮询的任务对象

```python
import requests

BASE_URL = "https://agent.example.com"


def test_create_async_task_contract():
    resp = requests.post(
        f"{BASE_URL}/api/agent/tasks",
        json={
            "session_id": "async-contract-001",
            "user_id": "qa-user-01",
            "goal": "生成 nightly 环境检查报告，并在发现异常时暂停等待确认",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    assert data["task_id"]
    assert data["status"] in {"queued", "running"}
    assert "poll_url" in data
    assert data["progress"] >= 0
```

### 4.2 回调幂等测试：重复 callback 不能重复落结果

```python
def test_duplicate_callback_should_be_idempotent():
    callback_payload = {
        "task_id": "async-callback-001",
        "step_name": "generate_report",
        "event_id": "evt-123",
        "idempotency_key": "idem-generate-report-001",
        "status": "succeeded",
        "artifact_url": "s3://report/report-001.pdf",
    }

    first = requests.post(
        f"{BASE_URL}/api/agent/callback",
        json=callback_payload,
        timeout=20,
    )
    second = requests.post(
        f"{BASE_URL}/api/agent/callback",
        json=callback_payload,
        timeout=20,
    )

    first.raise_for_status()
    second.raise_for_status()

    state = requests.get(f"{BASE_URL}/api/agent/tasks/async-callback-001", timeout=20)
    state.raise_for_status()
    body = state.json()

    assert body["side_effects"]["archive_result_count"] == 1
    assert body["last_event_id"] == "evt-123"
```

### 4.3 乱序事件测试：旧事件不能覆盖新状态

```python
def test_out_of_order_event_should_not_rollback_status():
    newer = requests.post(
        f"{BASE_URL}/api/agent/callback",
        json={
            "task_id": "async-order-001",
            "step_name": "collect_metrics",
            "event_id": "evt-new",
            "version": 3,
            "status": "succeeded",
        },
        timeout=20,
    )
    older = requests.post(
        f"{BASE_URL}/api/agent/callback",
        json={
            "task_id": "async-order-001",
            "step_name": "collect_metrics",
            "event_id": "evt-old",
            "version": 2,
            "status": "running",
        },
        timeout=20,
    )

    newer.raise_for_status()
    older.raise_for_status()

    task = requests.get(f"{BASE_URL}/api/agent/tasks/async-order-001", timeout=20).json()
    assert task["status"] != "running"
    assert task["version"] == 3
```

### 4.4 超时止损测试：长任务不能无限重试

```python
def test_timeout_should_end_with_safe_failure_instead_of_infinite_retry():
    resp = requests.post(
        f"{BASE_URL}/api/agent/execute-async",
        json={
            "session_id": "async-timeout-001",
            "goal": "持续轮询环境直到服务恢复",
            "fault_injection": {"health_checker": "always_timeout"},
        },
        timeout=30,
    )
    resp.raise_for_status()
    task_id = resp.json()["task_id"]

    final = requests.get(f"{BASE_URL}/api/agent/tasks/{task_id}?wait=true", timeout=180)
    final.raise_for_status()
    body = final.json()

    assert body["status"] == "failed"
    assert body["retry_count"] <= 3
    assert "超时" in body["last_error"]
```

长任务系统最怕的不是一次失败，而是 **失败后无上限重试**，因为这会同时放大成本、队列压力和副作用风险。

---

## 5. Playwright 实战：从用户视角验证进度透明、可恢复与可取消

### 5.1 前端验证重点

前端不只是“任务创建成功”弹个 Toast，而是要验证用户能否看清：

- 当前任务处于哪个状态；
- 哪一步已经完成，哪一步在重试，哪一步等待确认；
- 页面刷新后，任务进度是否还能恢复；
- 用户点击取消后，状态是否及时变化；
- 任务失败时，是否展示最小可解释原因与下一步建议。

### 5.2 Playwright E2E：进度可见 + 刷新可恢复 + 取消生效

```python
from playwright.sync_api import Page, expect


def test_ui_should_show_async_progress_and_resume_after_refresh(page: Page):
    page.goto("https://agent.example.com/workspace")

    page.get_by_placeholder("输入任务目标").fill(
        "生成环境巡检报告，自动完成只读检查；如需修复动作必须先确认"
    )
    page.get_by_role("button", name="开始执行").click()

    # Step 1: 任务创建后可见进度区域
    expect(page.get_by_text("任务进度")).to_be_visible(timeout=10_000)
    expect(page.get_by_text("执行中")).to_be_visible(timeout=20_000)

    # Step 2: 页面展示当前步骤和重试状态
    expect(page.get_by_text("fetch_cluster_snapshot")).to_be_visible(timeout=20_000)

    # Step 3: 刷新页面后，任务状态应可恢复，而不是丢成初始态
    page.reload()
    expect(page.get_by_text("任务进度")).to_be_visible(timeout=10_000)
    expect(page.get_by_text("执行中")).to_be_visible(timeout=20_000)

    # Step 4: 进入高风险步骤时，显示等待确认
    expect(page.get_by_text("等待确认")).to_be_visible(timeout=60_000)
    expect(page.get_by_role("button", name="确认执行")).to_be_visible()

    # Step 5: 用户取消后，页面应反映真实取消状态
    page.get_by_role("button", name="取消任务").click()
    expect(page.get_by_text("已取消")).to_be_visible(timeout=20_000)

    # ✅ 最终验证点：取消后不应再出现“修复已执行”的提示
    expect(page.get_by_text("已完成修复")).not_to_be_visible()
```

### 5.3 UI 负向检查清单

- 后台已经 retrying，但页面仍显示 running；
- 页面刷新后重新创建了一个新任务，而不是恢复旧任务；
- 用户点击取消后按钮变灰，但后台状态并未改变；
- 任务失败只显示“系统繁忙”，没有展示哪一步失败；
- 进度条到 100%，但最终结果区域为空或仍在加载。

---

## 6. K8s / 工程化视角：把长任务可靠性纳入持续回归与发布门禁

### 6.1 长任务 Agent 的基础设施风险

当长任务真正运行在 K8s 中，很多风险来自编排层和运行时：

1. **Worker 漂移**：不同 Pod 使用不同版本的工具定义或状态机逻辑；
2. **队列重复投递**：消息至少一次投递导致任务被重复消费；
3. **Checkpoint 落盘不完整**：Pod 被驱逐时只写入了一半状态；
4. **水平扩缩容竞争**：两个 Worker 同时抢到同一任务；
5. **审批态与执行态分离**：审批服务状态已更新，但执行 Worker 未感知。

### 6.2 示例：用 CronJob 触发夜间长任务回归

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: async-agent-nightly-regression
  namespace: ai-agent
spec:
  schedule: "0 3 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: regression-runner
              image: your-registry/async-agent-regression:latest
              env:
                - name: TARGET_BASE_URL
                  value: "https://agent.example.com"
                - name: SUITE_LABELS
                  value: "async,P0,recovery,idempotency"
          restartPolicy: Never
```

建议夜间回归至少覆盖三类长链路场景：

- **标准成功链路**：创建任务 → 多步执行 → 结果归档；
- **恢复链路**：中途失败 → checkpoint → Worker 重启 → 续跑成功；
- **止损链路**：超时 / 权限不足 / 审批未通过 → 安全失败或取消。

### 6.3 发布前建议增加的自动门禁

如果团队已经在做 Agent 发布治理，建议把这些信号接进门禁：

- P0 长任务场景通过率；
- 重试场景下重复副作用次数必须为 0；
- checkpoint 恢复成功率不低于基线；
- 取消合规率必须达标；
- 回调乱序保护必须通过；
- 页面刷新后的任务恢复可用率必须稳定。

长任务系统一旦上线，很多事故都不是“马上挂掉”，而是“慢慢偏”。所以回归门禁必须盯住恢复与一致性，而不是只看平均成功率。

---

## 7. 测试设计建议：如何把异步工作流纳入日常测试体系

### 7.1 按风险分层

- **P0**：重复执行导致副作用、取消后仍执行、断点恢复失败、回调乱序覆盖新状态；
- **P1**：刷新页面状态丢失、进度显示与后台不一致、审批后恢复延迟过高；
- **P2**：进度文案不稳定、低风险步骤排序轻微波动、历史记录展示细节问题。

### 7.2 推荐回归套件结构

1. **Contract 层**：Task / Event / Callback / Approval / Cancel schema；
2. **Service 层**：状态迁移、重试上限、checkpoint 写入、幂等校验；
3. **E2E 层**：真实业务目标驱动的长链路异步执行；
4. **Chaos 层**：Worker 重启、队列重复投递、回调延迟、数据库瞬断；
5. **Online Patrol 层**：抽样巡检长任务，关注超时、取消、重复副作用、卡死率。

### 7.3 对研发的左移建议

如果希望这类测试长期稳定落地，建议研发阶段先补齐这些可测试性能力：

- 每个任务都产出稳定的 `task_id / version / checkpoint_id`；
- 每个步骤都明确 `step_name / attempt / idempotency_key`；
- 状态迁移要落结构化事件，而不是只写文本日志；
- 回调处理器要显式做去重和版本保护；
- 前端刷新后能根据 `task_id` 恢复任务上下文；
- 对高风险步骤暴露单独的 approval / cancel 控制面。

---

## 8. 课后思考题

1. 你当前负责的 Agent 或自动化系统里，哪些任务已经具备明显的“长任务 / 异步工作流”特征？它们目前有清晰状态机吗？
2. 如果你要为现有系统补一个 checkpoint 恢复能力，最小落地方案会怎么设计？
3. 当外部 callback 发生重复、延迟、乱序时，你会如何定义系统应该接受哪些、拒绝哪些？
4. 你所在团队的“取消任务”是真取消、软取消，还是只取消前端展示？你会如何验证？

---

## 9. 今日小结

今天这篇内容的重点，是把 **AI Agent 的长任务执行与异步工作流** 当成一个完整的工程系统来测试，而不是把它当成“接口等久一点”的同步能力。对测试开发来说，真正要验证的是：**状态迁移是否清晰、checkpoint 是否可恢复、重试是否幂等、回调是否最终一致、取消是否真正生效、用户是否看得见任务现在发生了什么。**

只要把这几件事建模清楚，很多线上难排查的问题就能提前转成自动化断言：重复副作用、恢复成功率、乱序保护、取消合规率、进度透明度。长任务 Agent 要想真正可上线、可运维、可回归，靠的不是“最终跑完一次”，而是 **每一次中断、重试、恢复和终止都仍然在边界内**。
