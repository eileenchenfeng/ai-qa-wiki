---
title: "每日 AI 学习笔记｜Day 61：AI Agent 超时控制、取消传播与 Checkpoint 恢复测试"
date: 2026-06-15
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, timeout, cancellation, checkpoint-recovery, Ginkgo, Playwright, Kubernetes, API-Testing]
---

# 每日 AI 学习笔记｜Day 61：AI Agent 超时控制、取消传播与 Checkpoint 恢复测试

<callout icon="star" bgc="4">
**核心总结：** 对 AI Agent 来说，很多高风险故障并不是“执行失败”，而是**任务该停的时候没停、该取消的时候没取消、worker 重启后不知道从哪继续**。一次长任务可能同时经历模型推理、工具调用、异步轮询、文件上传、审批回调和前端状态刷新；如果没有统一的超时预算、取消传播机制和 checkpoint 恢复点，系统就容易出现：后端已超时但第三方副作用还在继续、用户点击取消但任务仍偷偷跑完、页面提示已结束但后台还在扣资源、Pod 重启后任务重复执行。对资深测试开发来说，这类质量问题不能只靠单接口超时校验，而要从 **Ginkgo** 验证超时预算拆分、取消信号透传与恢复续跑，从 **Python / API Testing** 校验任务状态机、取消幂等与 checkpoint 元数据，从 **Playwright** 验证“运行中 / 取消中 / 已取消 / 恢复中”是否对用户真实可见，从 **Kubernetes** 演练 Pod 重启、Job 中断与恢复流程。成熟的 AI Agent 长任务质量体系，不是任务永远不停，而是系统在该停、该断、该恢复时都能做出**唯一、可追踪、可解释**的正确动作。
</callout>

很多 AI Agent 已经从“单轮回答”演进到“多步骤执行”。一条真实请求里，往往同时存在长时模型调用、外部工具调用、异步状态轮询和跨系统副作用提交。此时最容易被忽略的问题，不是功能能不能跑通，而是 **超时、取消与恢复是否被设计成了可验证的系统能力**。

因此，今天这篇学习笔记聚焦一个非常贴近生产的主题：**如何为 AI Agent 设计超时控制、取消传播与 Checkpoint 恢复测试体系**，确保系统在长任务执行、人工终止、网络抖动、worker 重启和异步恢复场景下，仍能稳定收敛到可接受的结果。

{/* truncate */}

## 0. 今日核心要点

1. **超时不是一个常量，而是一套从入口到子任务逐层分配的预算系统。**
2. **取消不是前端按钮行为，而是必须一路传播到编排层、工具层和异步 worker。**
3. **没有 checkpoint 的长任务恢复，本质上只能依赖重跑，风险极高。**
4. **最危险的不是任务失败，而是用户以为任务停了，后台却仍继续执行副作用。**
5. **E2E 用例必须覆盖“启动 → 运行 → 超时/取消 → 恢复”完整链路，而不是只测单个 timeout 参数。**
6. **恢复测试的目标不是“继续跑起来”，而是验证是否从正确步骤恢复、且不重复执行已完成动作。**

---

## 1. 核心理论：为什么 AI Agent 必须重视超时、取消与恢复

### 1.1 AI Agent 天生容易产生长任务

传统接口通常在几百毫秒到几秒内完成，而 AI Agent 常见的执行链路可能包括：

- 用户输入理解与规划
- 模型推理或多轮思考
- 检索 / RAG 查询
- 工具调用与外部系统写操作
- 异步任务轮询与回调等待
- 文件生成、上传与通知发送

这意味着一个用户点击“执行”之后，系统往往会在几十秒、几分钟甚至更久的时间窗口内持续占用资源。此时如果没有明确的超时边界和取消语义，很多线上事故就会从“偶发慢”演变成 **资源泄漏、重复执行、副作用越界和用户误判**。

### 1.2 超时、取消、恢复其实是同一件事的三个阶段

从测试视角看，这三者不是孤立能力，而是一个闭环：

1. **超时控制**：定义任务最多可以跑多久；
2. **取消传播**：定义任务该停时，谁来发出终止信号、如何逐层停止；
3. **Checkpoint 恢复**：定义任务被动中断后，系统如何从已知状态继续，而不是盲目重跑。

如果只有超时，没有取消传播，就会出现“请求超时返回了，但后台任务还在偷偷执行”；如果有取消，没有 checkpoint，就会出现“任务一旦中断只能从头来过”；如果有恢复但没有幂等保护，就会出现“恢复一次，副作用多做一次”。

### 1.3 长任务最常见的 5 类失控场景

<table header-row="true" col-widths="150,220,240,220">
  <tr>
    <td>场景</td>
    <td>典型现象</td>
    <td>用户风险</td>
    <td>测试关注点</td>
  </tr>
  <tr>
    <td>入口超时</td>
    <td>前端提示失败，但后台还在继续跑</td>
    <td>用户重复提交、重复副作用</td>
    <td>取消传播、任务状态回查、幂等键</td>
  </tr>
  <tr>
    <td>取消不彻底</td>
    <td>点击取消后模型/工具仍继续执行</td>
    <td>资源泄漏、越权执行</td>
    <td>context cancel、worker stop、回调中止</td>
  </tr>
  <tr>
    <td>恢复重跑</td>
    <td>worker 重启后从头执行</td>
    <td>重复创建工单、重复发消息</td>
    <td>checkpoint 粒度、已完成步骤去重</td>
  </tr>
  <tr>
    <td>状态失真</td>
    <td>页面显示已取消，后台状态仍 running</td>
    <td>用户决策被误导</td>
    <td>前后端状态一致性、事件顺序</td>
  </tr>
  <tr>
    <td>恢复失败</td>
    <td>checkpoint 存在但无法恢复</td>
    <td>任务长期卡死、人工排障成本高</td>
    <td>恢复入口、兜底终态、诊断信息</td>
  </tr>
</table>

<callout icon="bulb" bgc="3">
**工程提醒：** 对长任务系统而言，“接口返回超时”从来不是最终事实。真正需要验证的是：**系统内部是否停止了、停止是否可追踪、恢复是否不会重复副作用。**
</callout>

---

## 2. 方法框架：先定义时间预算和任务状态机，再谈自动化

### 2.1 入口预算不等于子任务预算

推荐把任务的时间预算拆成三层：

1. **用户可感知预算**：前端等待多久后要给出明确反馈；
2. **编排层总预算**：整条任务链路最多允许执行多久；
3. **步骤级预算**：每个模型调用、工具调用、轮询步骤最多跑多久。

例如，一个 90 秒总预算的任务，并不意味着每个子步骤都可以各跑 90 秒。更合理的方式是：规划 10 秒、主工具执行 30 秒、回调等待 40 秒、收尾与持久化 10 秒。

### 2.2 推荐的长任务状态机

<table header-row="true" col-widths="170,220,220,180">
  <tr>
    <td>系统状态</td>
    <td>后端含义</td>
    <td>前端展示建议</td>
    <td>优先级</td>
  </tr>
  <tr>
    <td>queued</td>
    <td>任务已入队，尚未开始执行</td>
    <td>显示排队中</td>
    <td>P1</td>
  </tr>
  <tr>
    <td>running</td>
    <td>主流程执行中</td>
    <td>显示执行中并提供取消入口</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>cancelling</td>
    <td>收到取消请求，正在停止子任务</td>
    <td>显示“正在取消，请稍候”</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>cancelled</td>
    <td>任务已安全停止，后续步骤不再推进</td>
    <td>显示已取消和已执行到的步骤</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>timed_out</td>
    <td>超过总预算，系统强制终止</td>
    <td>显示执行超时并引导查看进度</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>resuming</td>
    <td>从 checkpoint 恢复中</td>
    <td>显示正在恢复任务</td>
    <td>P1</td>
  </tr>
  <tr>
    <td>completed</td>
    <td>任务正常完成</td>
    <td>显示完成结果</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>manual_intervention_required</td>
    <td>自动恢复失败，需要人工处理</td>
    <td>显示人工接管入口和诊断编号</td>
    <td>P1</td>
  </tr>
</table>

### 2.3 测试设计时必须回答的“四个边界问题”

1. **超时后是否一定要停？** 哪些步骤可以异步补完，哪些必须强停；
2. **取消后哪些副作用允许保留？** 例如已创建草稿是否保留，已发通知是否补发撤销；
3. **恢复从哪一步继续？** 是从最后成功 checkpoint，还是从最近安全边界恢复；
4. **哪些步骤绝不能重复执行？** 例如创建审批单、写审计、发送正式通知。

如果这四个问题没有被设计清楚，后续自动化往往只能测到“任务慢”这类表象，而测不到真正的工程风险。

---

## 3. Ginkgo 实战：验证超时预算、取消传播和恢复续跑

### 3.1 先定义任务运行结果与 checkpoint 元数据

```go
//go:build longtaske2e

package longtaske2e_test

type Checkpoint struct {
    StepName   string `json:"step_name"`
    Version    int    `json:"version"`
    Persisted  bool   `json:"persisted"`
    ResumeFrom bool   `json:"resume_from"`
}

type TaskRunResult struct {
    TaskID            string       `json:"task_id"`
    FinalState        string       `json:"final_state"`
    UserVisibleState  string       `json:"user_visible_state"`
    ExecutedSteps     []string     `json:"executed_steps"`
    CancelObservedBy  []string     `json:"cancel_observed_by"`
    Checkpoints       []Checkpoint `json:"checkpoints"`
    ExternalRefs      []string     `json:"external_refs"`
}
```

这个结构的价值在于：它让“任务到底停没停、从哪恢复、有没有重复执行”都能变成 **E2E 可断言事实**，而不是靠 trace 和日志人工猜测。

### 3.2 E2E：超时后必须停止下游高风险步骤

```go
package longtaske2e_test

import (
    "context"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type LongTaskRunner interface {
    Run(ctx context.Context, input string, inject map[string]string) (*TaskRunResult, error)
}

var _ = Describe("Agent timeout control", Label("P0", "e2e", "timeout"), func() {
    var runner LongTaskRunner

    BeforeEach(func() {
        runner = NewLongTaskRunnerFromEnv()
    })

    It("should stop before notification step when workflow exceeds global timeout budget", func() {
        ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
        defer cancel()

        result, err := runner.Run(ctx,
            "生成发布方案、提交审批并通知值班群",
            map[string]string{"approval-wait": "70s"},
        )
        Expect(err).NotTo(HaveOccurred())
        Expect(result.FinalState).To(Equal("timed_out"))
        Expect(result.UserVisibleState).To(Equal("执行超时，已停止后续步骤"))
        Expect(result.ExecutedSteps).To(ContainElement("create_release_plan"))
        Expect(result.ExecutedSteps).NotTo(ContainElement("send_oncall_notification"))
        Expect(result.CancelObservedBy).To(ContainElement("workflow-orchestrator"))
    })
})
```

这条用例的重点不是“返回 timeout 了”，而是验证：**超时发生后，下游高风险动作是否真的被阻断。**

### 3.3 E2E：用户点击取消后，取消信号必须传到底层工具

```go
It("should propagate cancellation to tool executor and worker", func() {
    ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
    defer cancel()

    result, err := runner.Run(ctx,
        "批量扫描知识库并生成整改建议",
        map[string]string{"cancel-after": "12s", "tool-delay": "40s"},
    )
    Expect(err).NotTo(HaveOccurred())
    Expect(result.FinalState).To(Equal("cancelled"))
    Expect(result.UserVisibleState).To(Equal("任务已取消"))
    Expect(result.CancelObservedBy).To(ContainElements(
        "workflow-orchestrator",
        "tool-executor",
        "async-worker",
    ))
    Expect(result.ExecutedSteps).NotTo(ContainElement("write_final_report"))
})
```

如果取消只停在 API 层，而底层工具仍继续执行，那么系统会出现一种非常危险的假象：**用户以为任务停了，后台其实还在消耗资源甚至继续写数据。**

### 3.4 E2E：worker 重启后必须从 checkpoint 恢复，而不是全量重跑

```go
It("should resume from latest persisted checkpoint after worker restart", func() {
    ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
    defer cancel()

    result, err := runner.Run(ctx,
        "创建发布单、上传附件并同步审批流",
        map[string]string{"crash-after-step": "upload_attachments"},
    )
    Expect(err).NotTo(HaveOccurred())
    Expect(result.FinalState).To(Equal("completed"))
    Expect(result.UserVisibleState).To(Equal("任务恢复完成"))
    Expect(result.Checkpoints).To(ContainElement(MatchFields(IgnoreExtras, Fields{
        "StepName": Equal("upload_attachments"),
        "Persisted": BeTrue(),
        "ResumeFrom": BeTrue(),
    })))
    Expect(result.ExecutedSteps).NotTo(ContainElement("create_release_ticket_again"))
    Expect(result.ExternalRefs).To(HaveLen(1))
})
```

这里验证的是：**系统恢复时是否识别“前面哪些动作已经成功”，而不是为了省事直接从头再来。**

### 3.5 E2E：取消和恢复同时发生时，必须遵循唯一终态

```go
It("should keep cancelled as terminal state when resume request arrives after cancel", func() {
    ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
    defer cancel()

    result, err := runner.Run(ctx,
        "执行长任务并在恢复前人工取消",
        map[string]string{"cancel-after": "8s", "resume-request-after": "10s"},
    )
    Expect(err).NotTo(HaveOccurred())
    Expect(result.FinalState).To(Equal("cancelled"))
    Expect(result.UserVisibleState).To(Equal("任务已取消"))
    Expect(result.ExecutedSteps).NotTo(ContainElement("resume_after_cancel"))
})
```

这类边界场景特别关键，因为线上最容易出现的是 **多信号竞争**：超时、人工取消、自动恢复同时发生，最后状态机被撞乱。

---

## 4. Python / API Testing：校验任务状态、取消幂等与 checkpoint 一致性

### 4.1 查询任务详情，验证终态是否唯一

```python
from __future__ import annotations

from dataclasses import dataclass
import requests


TERMINAL_STATES = {"completed", "cancelled", "timed_out", "manual_intervention_required"}


@dataclass
class TaskDetail:
    task_id: str
    state: str
    checkpoint_step: str | None
    cancel_requested: bool


def fetch_task_detail(base_url: str, task_id: str) -> TaskDetail:
    resp = requests.get(f"{base_url}/api/tasks/{task_id}", timeout=10)
    resp.raise_for_status()
    body = resp.json()
    return TaskDetail(
        task_id=body["task_id"],
        state=body["state"],
        checkpoint_step=body.get("checkpoint_step"),
        cancel_requested=body.get("cancel_requested", False),
    )


def assert_terminal_state(detail: TaskDetail) -> None:
    assert detail.state in TERMINAL_STATES, f"unexpected final state: {detail.state}"
```

### 4.2 Contract：取消接口必须是幂等的

```python
import requests


def test_cancel_api_should_be_idempotent():
    task_id = "task-long-running-001"

    first = requests.post(f"https://agent.example.com/api/tasks/{task_id}/cancel", timeout=10)
    second = requests.post(f"https://agent.example.com/api/tasks/{task_id}/cancel", timeout=10)

    first.raise_for_status()
    second.raise_for_status()

    body1 = first.json()
    body2 = second.json()

    assert body1["accepted"] is True
    assert body2["accepted"] is True
    assert body2["message"] in {"already_cancelling", "already_cancelled", "cancel_accepted"}
```

取消接口如果不具备幂等性，就很容易在前端重复点击、自动重试或脚本误触发时制造新的状态混乱。

### 4.3 校验 checkpoint 是否单调推进

```python
from dataclasses import dataclass
import requests


@dataclass
class CheckpointEvent:
    step: str
    version: int
    persisted: bool


def fetch_checkpoints(base_url: str, task_id: str) -> list[CheckpointEvent]:
    resp = requests.get(f"{base_url}/api/tasks/{task_id}/checkpoints", timeout=10)
    resp.raise_for_status()
    body = resp.json()
    return [
        CheckpointEvent(
            step=item["step"],
            version=item["version"],
            persisted=item["persisted"],
        )
        for item in body["items"]
    ]


def assert_checkpoint_monotonic(events: list[CheckpointEvent]) -> None:
    versions = [item.version for item in events]
    assert versions == sorted(versions), f"checkpoint version disorder: {versions}"
    assert all(item.persisted for item in events), "found non-persisted checkpoint in recovery path"
```

### 4.4 Polling：取消请求发出后，应在超时窗口内收敛

```python
import time
import requests


def wait_until_stopped(base_url: str, task_id: str, timeout_s: int = 60) -> str:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = requests.get(f"{base_url}/api/tasks/{task_id}", timeout=5)
        resp.raise_for_status()
        state = resp.json()["state"]
        if state in {"cancelled", "timed_out", "manual_intervention_required"}:
            return state
        time.sleep(2)
    raise AssertionError(f"task {task_id} was not stopped within {timeout_s}s")
```

如果取消请求发出后任务长时间仍停留在 `running`，那说明系统要么没有真正传播取消，要么缺乏对卡死子步骤的兜底停止机制。

---

## 5. Playwright 实战：验证用户看到的停止与恢复是否真实

### 5.1 为什么这类问题必须做前端验证

超时、取消和恢复在后端日志里可能都“看起来正确”，但用户真正感知的是：

- 页面是否还在持续 loading；
- 点击取消后按钮有没有变化；
- 系统有没有明确说明当前是取消中还是已取消；
- 恢复后是否展示“从第几步继续执行”；
- 是否出现重复结果或重复可点击入口。

因此，这类质量问题如果只做 API 测试，很容易漏掉 **状态可见性和交互一致性**。

### 5.2 Playwright：取消中必须禁用二次触发按钮

```python
from playwright.sync_api import Page, expect


def test_cancelling_state_should_disable_retry_and_submit(page: Page):
    page.goto("https://agent.example.com/workspace/ws-release-center?scenario=long_run")
    page.get_by_placeholder("输入任务目标").fill("生成发布方案并同步审批")
    page.get_by_role("button", name="发送").click()

    page.get_by_role("button", name="取消任务").click()

    expect(page.get_by_text("正在取消，请稍候")).to_be_visible(timeout=20_000)
    expect(page.get_by_role("button", name="发送")).to_be_disabled()
    expect(page.get_by_role("button", name="重新执行")).to_be_disabled()
```

### 5.3 Playwright：超时后必须展示已执行进度，而不是一句泛化失败

```python
from playwright.sync_api import Page, expect


def test_timeout_should_show_last_safe_progress(page: Page):
    page.goto("https://agent.example.com/workspace/ws-release-center?inject_fault=approval_wait_timeout")
    page.get_by_placeholder("输入任务目标").fill("创建发布单并等待审批回调")
    page.get_by_role("button", name="发送").click()

    expect(page.get_by_text("执行超时，已停止后续步骤")).to_be_visible(timeout=30_000)
    expect(page.get_by_text("已完成：发布单创建")).to_be_visible()
    expect(page.get_by_text("未执行：群通知发送")).to_be_visible()
    expect(page.get_by_role("button", name="查看停止详情")).to_be_visible()
```

### 5.4 Playwright：恢复成功后必须明确说明恢复起点

```python
from playwright.sync_api import Page, expect


def test_resume_should_show_checkpoint_source(page: Page):
    page.goto("https://agent.example.com/workspace/ws-release-center?inject_fault=worker_restart_after_upload")
    page.get_by_placeholder("输入任务目标").fill("创建发布单、上传附件并同步审批流")
    page.get_by_role("button", name="发送").click()

    expect(page.get_by_text("任务已恢复执行")).to_be_visible(timeout=30_000)
    expect(page.get_by_text("从“附件上传完成”继续执行")).to_be_visible()
    expect(page.get_by_text("未重复创建发布单")).to_be_visible()
```

### 5.5 Playwright：人工接管场景必须暴露诊断编号

```python
from playwright.sync_api import Page, expect


def test_manual_intervention_should_show_recovery_ticket(page: Page):
    page.goto("https://agent.example.com/workspace/ws-release-center?inject_fault=checkpoint_corrupted")
    page.get_by_placeholder("输入任务目标").fill("执行长任务并在中断后自动恢复")
    page.get_by_role("button", name="发送").click()

    expect(page.get_by_text("自动恢复失败，需要人工介入")).to_be_visible(timeout=30_000)
    expect(page.get_by_text("恢复工单编号")).to_be_visible()
    expect(page.get_by_role("button", name="复制诊断信息")).to_be_visible()
```

如果前端把 `cancelling`、`cancelled`、`timed_out`、`resuming` 都混成一句“任务异常”，用户就很难知道自己该重试、该等待还是该找人处理。

---

## 6. Kubernetes 实战：把长任务中断与恢复演练做成持续能力

### 6.1 用 CronJob 周期性演练 worker 重启恢复

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: agent-checkpoint-recovery-drill
spec:
  schedule: "0 10 * * 2,6"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: recovery-drill
              image: python:3.11-slim
              command:
                - /bin/sh
                - -c
                - |
                  python run_recovery_drill.py \
                    --scenario=worker_restart_after_checkpoint \
                    --target-env=staging \
                    --assert-final-state=completed
              env:
                - name: BASE_URL
                  value: "https://agent.example.com"
                - name: ALERT_WEBHOOK
                  valueFrom:
                    secretKeyRef:
                      name: qa-drill-secret
                      key: webhook
```

### 6.2 推荐优先覆盖的 5 类恢复演练场景

1. **worker 在 checkpoint 前崩溃**：验证是否正确回退到最近安全点；
2. **worker 在 checkpoint 后崩溃**：验证是否从已持久化步骤恢复；
3. **取消请求与 worker 重启同时发生**：验证取消优先级和终态唯一性；
4. **checkpoint 元数据损坏**：验证是否进入人工接管而不是盲目重跑；
5. **第三方回调在恢复期间到达**：验证状态机是否忽略过期事件。

### 6.3 每次演练至少应沉淀的 4 类产物

<table header-row="true" col-widths="180,250,260,180">
  <tr>
    <td>产物</td>
    <td>说明</td>
    <td>用途</td>
    <td>优先级</td>
  </tr>
  <tr>
    <td>场景编号</td>
    <td>明确是哪一步中断、何种恢复模式</td>
    <td>便于回归和缺陷归档</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>checkpoint 轨迹</td>
    <td>记录各步骤版本、持久化状态、恢复起点</td>
    <td>验证恢复逻辑是否正确</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>用户可见结果</td>
    <td>取消、超时、恢复提示文案与按钮状态</td>
    <td>验证前端是否诚实展示</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>副作用核对单</td>
    <td>创建对象、通知、审计、文件等是否重复</td>
    <td>防止恢复制造二次事故</td>
    <td>P0/P1</td>
  </tr>
</table>

<callout icon="bulb" bgc="3">
**质量建议：** 恢复演练如果只验证“任务最后成功了”，价值很有限。更高价值的做法是沉淀一张统一核对单：**恢复从哪步开始、哪些副作用被跳过、哪些状态被重放、用户最终看到了什么。**
</callout>

---

## 7. 课后思考题

1. 如果任务总预算为 90 秒，但某个高风险步骤单独就可能跑 80 秒，你会优先优化预算拆分、增加 checkpoint、还是改变产品交互？为什么？
2. 用户点击取消后，如果第三方系统已经开始执行但尚未返回结果，你会把系统终态定义为 `cancelled`、`cancelling` 还是 `manual_intervention_required`？依据是什么？
3. 在你的业务里，哪些步骤最适合作为 checkpoint 边界？哪些步骤绝不应该作为恢复起点？
4. 如果恢复成功了，但前端没有明确告诉用户“从哪一步恢复”，你会把它归类为体验问题、可观测性问题还是可靠性问题？为什么？
5. 你的团队目前更缺哪一类能力：统一超时预算、取消传播链路、checkpoint 持久化，还是恢复演练机制？如果只能先补一个，你会选哪个？

---

## 8. 今日小结

今天我们把视角从“任务能不能跑完”进一步推进到了 **任务该什么时候停、停下后如何保证系统不失控、以及中断后如何安全恢复**。这其实是生产级 AI Agent 从 demo 走向可托管执行系统时绕不开的一步。

对资深测试开发来说，超时控制、取消传播与 checkpoint 恢复测试的核心，不是再多写几条 timeout case，而是建立一套完整的长任务质量闭环：**先定义预算，再定义状态机；先定义停止语义，再定义恢复边界；最后用 Ginkgo、Python、Playwright 和 Kubernetes 把这些规则固化成可持续执行的自动化资产。** 当系统能够在超时、取消、重启和恢复之间始终维持唯一终态、不重复副作用、且对用户诚实可见时，这套 AI Agent 质量体系才算真正具备生产韧性。
