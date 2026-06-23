---
title: AI Agent 状态机不变量与收敛性测试
authors: [xiaoai]
tags: [AI, QA, Agent, StateMachine, Ginkgo, Playwright, Kubernetes]
date: 2026-06-18
---

今天这篇学习笔记，聚焦一个非常“工程底座”的主题：**AI Agent 状态机不变量与收敛性测试（Agent State Machine Invariants & Convergence Testing）**。

当 Agent 开始具备规划、工具调用、异步回调、审批、人机协同、补偿恢复、多租户隔离等能力后，系统最危险的失败模式，往往不再是“接口 500 了”，而是：

- 某个旧事件把新状态回滚了；
- 重复回调触发了重复副作用；
- 补偿执行过了，但系统没有真正收敛；
- 前端显示“已完成”，后端审计却仍停在中间态；
- 人工驳回后，迟到的成功回调又把任务改回 completed。

这类问题的共同点是：**单点功能看起来都没坏，但系统整体已经偏离了正确状态机**。

因此，今天我们不再只问“功能是否成功”，而是进一步追问：

1. **系统是否始终沿着合法状态路径推进？**
2. **进入终态后，是否还能被旧事件污染？**
3. **异常、乱序、重试、补偿之后，系统是否还能稳定收敛到唯一合法终态？**

{/* truncate */}

---

## 1. 背景与核心概念

### 1.1 为什么 AI Agent 特别容易出现“状态正确性”问题

传统同步接口的状态生命周期通常比较短：请求进来、处理完成、返回响应，问题大多停留在单次调用级别。

但 AI Agent 往往是一条长链路：

1. 用户发起任务；
2. Planner 生成计划；
3. Executor 调用多个工具；
4. 系统等待审批或外部回调；
5. 失败后进入补偿；
6. 最终产生结果并通知用户。

在这类链路中，真正要守住的不是某个接口的 200，而是**整个任务生命周期里的状态演进正确性**。

如果状态机设计不清楚，线上就会出现很多“看起来成功、其实已经错了”的事故，例如：

- 已完成任务被迟到失败事件打回 `failed`
- 审批拒绝后，旧成功回调又把状态推回 `completed`
- 补偿已完成，但 UI 仍停留在“处理中”
- 重放消息导致通知重复发送、工单重复创建、扣费重复执行

### 1.2 什么是不变量（Invariant）

**不变量**，就是无论系统经历成功、失败、重试、乱序、补偿还是人工介入，都必须始终成立的规则。

对 AI Agent 来说，最关键的不变量通常包括：

| 不变量 | 说明 | 典型风险 |
| --- | --- | --- |
| 终态唯一 | `completed/failed/cancelled/manual_intervention_required` 一旦建立，不再漂移 | 旧事件污染终态 |
| 非法跃迁拒绝 | 不允许从 `queued` 直接跳到 `completed` 等非法路径 | 状态机被绕过 |
| 状态不可逆 | 新状态不能被旧 sequence/version 回滚 | 乱序事件导致假失败 |
| 副作用幂等 | 重复事件不能重复发通知、重复写单据、重复扣费 | “重复成功”事故 |
| 视图一致 | UI、任务详情、时间线、审计记录表达同一事实 | 前后端理解分裂 |
| 租户隔离 | tenant A 的事件绝不能推进 tenant B 的任务 | 串租户安全事故 |

### 1.3 什么是收敛性（Convergence）

很多系统都说自己“最终一致”，但测试里必须把它翻译成可验证的定义。

在 Agent 质量场景里，**收敛性**通常至少包含三层含义：

1. **有限时间内收敛**：任务会在合理时间进入某个合法终态；
2. **收敛结果唯一**：无论中间经历多少重试、乱序、补偿，最终终态唯一；
3. **收敛后不再漂移**：进入终态后，系统不会被后续旧事件再次改写。

所以，真正有价值的自动化断言不是“Eventually 变成 completed”，而是：

- Eventually 进入合法终态；
- Consistently 保持该终态稳定；
- 副作用计数、审计记录、UI 展示都一起稳定。

---

## 2. 测试策略：从状态机建模到 E2E 闭环

### 2.1 先建模，再测功能

如果没有显式状态机模型，测试只能停留在“点点点 + 看返回值”的层面，很难发现系统已经违反状态约束。

推荐先定义一版最小状态骨架，例如：

```text
queued
  ↓
planning
  ↓
running
  ├── awaiting_approval
  ├── waiting_callback
  ├── compensating
  ↓
completed / failed / cancelled / manual_intervention_required
```

每个状态至少要回答四个问题：

1. 当前属于中间态还是终态？
2. 哪些事件允许推进它？
3. 哪些事件必须被拒绝？
4. 谁可以推进它（系统、回调、人工审批、补偿器）？

### 2.2 用 E2E 场景组织测试，而不是碎片化单点验证

高价值测试不应该只写“接口返回正确”，而要围绕真实业务链路设计。

例如，一个完整的 E2E 场景可以这样组织：

1. 用户发起“生成周报并发送管理摘要”；
2. Agent 进入 `planning` 并生成计划；
3. 调用检索、总结、通知等工具；
4. 因涉及外部发送，进入 `awaiting_approval`；
5. 审批通过后恢复 `running`；
6. 外部回调迟到一次、重复一次；
7. 任务最终进入 `completed`；
8. 页面展示“已完成”；
9. 审计链路显示一次合法推进；
10. 通知只发送一次。

### 2.3 断言要覆盖三层：状态、证据、副作用

每条状态机 E2E 用例，建议至少覆盖三类断言：

- **状态断言**：状态是否沿合法路径推进，终态是否唯一且稳定；
- **证据断言**：审计时间线、sequence/version、事件原因是否可追踪；
- **副作用断言**：通知、工单、外部写操作是否只执行一次。

如果只断言状态，不看副作用，就会漏掉“状态对了但发了两次通知”；
如果只看接口成功，不看证据链，就会漏掉“其实是旧事件误打误撞把状态推对了”。

---

## 3. 可运行示例一：Ginkgo 端到端验证状态机不变量

下面这套示例用 Go + Ginkgo v2 风格，重点覆盖四类 P0 场景：

- 合法链路最终收敛到唯一终态
- 过期失败事件不能回滚成功终态
- 重复回调不能产生重复副作用
- 补偿失败后必须进入明确的人工介入终态

```go
//go:build statemachinee2e

package statemachinee2e_test

import (
    "sync"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type Task struct {
    ID              string
    TenantID        string
    State           string
    LastSequence    int64
    SideEffectCount int
    UserVisible     string
}

type Store struct {
    mu    sync.Mutex
    tasks map[string]*Task
}

func NewStore() *Store {
    return &Store{tasks: map[string]*Task{}}
}

func (s *Store) Create(id, tenant string) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.tasks[id] = &Task{
        ID:           id,
        TenantID:     tenant,
        State:        "queued",
        LastSequence: 0,
        UserVisible:  "任务已排队",
    }
}

func (s *Store) Get(id string) Task {
    s.mu.Lock()
    defer s.mu.Unlock()
    return *s.tasks[id]
}

func (s *Store) Apply(id string, seq int64, event string) bool {
    s.mu.Lock()
    defer s.mu.Unlock()

    t := s.tasks[id]
    if seq < t.LastSequence {
        return false
    }
    if t.State == "completed" || t.State == "failed" || t.State == "cancelled" || t.State == "manual_intervention_required" {
        return false
    }

    switch t.State {
    case "queued":
        if event == "task.accepted" {
            t.State = "planning"
            t.UserVisible = "规划中"
        } else {
            return false
        }
    case "planning":
        if event == "plan.generated" {
            t.State = "running"
            t.UserVisible = "执行中"
        } else if event == "validation.failed" {
            t.State = "failed"
            t.UserVisible = "执行失败"
        } else {
            return false
        }
    case "running":
        if event == "approval.required" {
            t.State = "awaiting_approval"
            t.UserVisible = "等待审批"
        } else if event == "callback.waiting" {
            t.State = "waiting_callback"
            t.UserVisible = "等待回调"
        } else if event == "task.completed" {
            t.State = "completed"
            t.UserVisible = "任务已完成"
            if t.SideEffectCount == 0 {
                t.SideEffectCount++
            }
        } else if event == "task.failed" {
            t.State = "failed"
            t.UserVisible = "执行失败"
        } else {
            return false
        }
    case "awaiting_approval":
        if event == "approval.granted" {
            t.State = "running"
            t.UserVisible = "执行中"
        } else if event == "approval.denied" {
            t.State = "cancelled"
            t.UserVisible = "已取消"
        } else {
            return false
        }
    case "waiting_callback":
        if event == "callback.received" {
            t.State = "completed"
            t.UserVisible = "任务已完成"
            if t.SideEffectCount == 0 {
                t.SideEffectCount++
            }
        } else if event == "timeout.expired" {
            t.State = "compensating"
            t.UserVisible = "补偿处理中"
        } else {
            return false
        }
    case "compensating":
        if event == "compensation.succeeded" {
            t.State = "failed"
            t.UserVisible = "执行失败（已补偿）"
        } else if event == "compensation.failed" {
            t.State = "manual_intervention_required"
            t.UserVisible = "需要人工介入"
        } else {
            return false
        }
    }

    t.LastSequence = seq
    return true
}

var _ = Describe("Agent state machine invariants", func() {
    var store *Store

    BeforeEach(func() {
        store = NewStore()
        store.Create("task-1", "tenant-a")
    })

    It("should converge to one terminal state after approval and callback", func() {
        Expect(store.Apply("task-1", 1, "task.accepted")).To(BeTrue())
        Expect(store.Apply("task-1", 2, "plan.generated")).To(BeTrue())
        Expect(store.Apply("task-1", 3, "approval.required")).To(BeTrue())
        Expect(store.Apply("task-1", 4, "approval.granted")).To(BeTrue())
        Expect(store.Apply("task-1", 5, "callback.waiting")).To(BeTrue())
        Expect(store.Apply("task-1", 6, "callback.received")).To(BeTrue())

        Eventually(func(g Gomega) {
            view := store.Get("task-1")
            g.Expect(view.State).To(Equal("completed"))
            g.Expect(view.UserVisible).To(Equal("任务已完成"))
            g.Expect(view.SideEffectCount).To(Equal(1))
        }).Should(Succeed())

        Consistently(func(g Gomega) {
            view := store.Get("task-1")
            g.Expect(view.State).To(Equal("completed"))
            g.Expect(view.SideEffectCount).To(Equal(1))
        }, 2*time.Second, 200*time.Millisecond).Should(Succeed())
    })

    It("should ignore stale failed event after task already completed", func() {
        Expect(store.Apply("task-1", 1, "task.accepted")).To(BeTrue())
        Expect(store.Apply("task-1", 2, "plan.generated")).To(BeTrue())
        Expect(store.Apply("task-1", 3, "task.completed")).To(BeTrue())

        accepted := store.Apply("task-1", 2, "task.failed")
        Expect(accepted).To(BeFalse())

        view := store.Get("task-1")
        Expect(view.State).To(Equal("completed"))
        Expect(view.SideEffectCount).To(Equal(1))
    })

    It("should not duplicate side effects when callback is replayed", func() {
        Expect(store.Apply("task-1", 1, "task.accepted")).To(BeTrue())
        Expect(store.Apply("task-1", 2, "plan.generated")).To(BeTrue())
        Expect(store.Apply("task-1", 3, "callback.waiting")).To(BeTrue())
        Expect(store.Apply("task-1", 4, "callback.received")).To(BeTrue())

        accepted := store.Apply("task-1", 4, "callback.received")
        Expect(accepted).To(BeFalse())

        view := store.Get("task-1")
        Expect(view.State).To(Equal("completed"))
        Expect(view.SideEffectCount).To(Equal(1))
    })

    It("should move to manual intervention when compensation cannot finish", func() {
        Expect(store.Apply("task-1", 1, "task.accepted")).To(BeTrue())
        Expect(store.Apply("task-1", 2, "plan.generated")).To(BeTrue())
        Expect(store.Apply("task-1", 3, "callback.waiting")).To(BeTrue())
        Expect(store.Apply("task-1", 4, "timeout.expired")).To(BeTrue())
        Expect(store.Apply("task-1", 5, "compensation.failed")).To(BeTrue())

        view := store.Get("task-1")
        Expect(view.State).To(Equal("manual_intervention_required"))
        Expect(view.UserVisible).To(ContainSubstring("人工介入"))
    })
})
```

**测试要点：**

- `Eventually` 用于验证“能否到达合法终态”
- `Consistently` 用于验证“到达后是否保持稳定，不再漂移”
- `LastSequence`、`SideEffectCount` 是非常关键的观测字段

---

## 4. 可运行示例二：Python API Testing 校验非法跃迁与版本保护

这套示例使用 `pytest + requests` 风格，重点验证 API 层是否正确拒绝非法状态推进。

```python
import requests

BASE_URL = "http://localhost:8080"


def auth_headers(tenant_id: str):
    return {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenant_id,
    }


def create_task(initial_state="queued", tenant_id="tenant-a"):
    resp = requests.post(
        f"{BASE_URL}/api/tasks",
        json={"tenant_id": tenant_id, "initial_state": initial_state},
        headers=auth_headers(tenant_id),
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()["task_id"]


def create_completed_task(tenant_id="tenant-a", last_sequence=20):
    resp = requests.post(
        f"{BASE_URL}/api/tasks/bootstrap-completed",
        json={"tenant_id": tenant_id, "last_sequence": last_sequence},
        headers=auth_headers(tenant_id),
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()["task_id"]


def test_state_transition_should_reject_direct_complete_from_queued():
    task_id = create_task(initial_state="queued", tenant_id="tenant-a")

    resp = requests.post(
        f"{BASE_URL}/api/tasks/{task_id}/transitions",
        json={"event_type": "task.completed", "sequence": 3},
        headers=auth_headers("tenant-a"),
        timeout=5,
    )

    assert resp.status_code == 409
    body = resp.json()
    assert body["error_code"] == "INVALID_TRANSITION"
    assert body["from_state"] == "queued"
    assert body["to_state"] == "completed"


def test_stale_sequence_should_not_overwrite_terminal_state():
    task_id = create_completed_task(tenant_id="tenant-a", last_sequence=20)

    resp = requests.post(
        f"{BASE_URL}/api/tasks/{task_id}/transitions",
        json={"event_type": "task.failed", "sequence": 18},
        headers=auth_headers("tenant-a"),
        timeout=5,
    )

    assert resp.status_code == 202
    body = resp.json()
    assert body["accepted"] is False
    assert body["ignored_reason"] == "stale_sequence"


def test_task_state_should_match_timeline_and_audit():
    task_id = create_completed_task(tenant_id="tenant-a", last_sequence=12)

    detail = requests.get(
        f"{BASE_URL}/api/tasks/{task_id}",
        headers=auth_headers("tenant-a"),
        timeout=5,
    ).json()

    timeline = requests.get(
        f"{BASE_URL}/api/tasks/{task_id}/timeline",
        headers=auth_headers("tenant-a"),
        timeout=5,
    ).json()

    audit = requests.get(
        f"{BASE_URL}/api/tasks/{task_id}/audit",
        headers=auth_headers("tenant-a"),
        timeout=5,
    ).json()

    assert detail["state"] == "completed"
    assert timeline["current_state"] == detail["state"]
    assert audit["final_state"] == detail["state"]
    assert audit["last_sequence"] == detail["last_sequence"]


def test_cross_tenant_transition_should_be_forbidden():
    task_id = create_task(initial_state="running", tenant_id="tenant-a")

    resp = requests.post(
        f"{BASE_URL}/api/tasks/{task_id}/transitions",
        json={"event_type": "callback.received", "tenant_id": "tenant-b", "sequence": 8},
        headers=auth_headers("tenant-b"),
        timeout=5,
    )

    assert resp.status_code in (403, 404)
```

**测试要点：**

- 非法跃迁必须明确报错，而不是“悄悄帮你改状态”
- 过期 sequence 必须被拦截并记录 ignored reason
- `detail / timeline / audit` 三条视图必须互相一致
- 跨租户推进必须硬失败，不能靠“业务约定”兜底

---

## 5. 可运行示例三：Playwright 验证用户侧状态流与后端事实一致

下面示例强调的是：**用户看到的状态流，必须是真实状态机的翻译层**，不能自说自话。

```python
from playwright.sync_api import expect


def test_agent_task_should_converge_to_completed_ui(page, base_url):
    page.goto(f"{base_url}/agent/tasks")
    page.get_by_placeholder("输入任务目标").fill("汇总本周线上质量问题并发送管理摘要")
    page.get_by_role("button", name="开始执行").click()

    expect(page.get_by_text("规划中")).to_be_visible(timeout=15_000)
    expect(page.get_by_text("等待审批")).to_be_visible(timeout=15_000)

    page.get_by_role("button", name="批准执行").click()

    expect(page.get_by_text("等待回调")).to_be_visible(timeout=15_000)
    expect(page.get_by_text("任务已完成")).to_be_visible(timeout=60_000)
    expect(page.get_by_role("button", name="查看结果")).to_be_visible()


def test_completed_ui_should_not_rollback_after_stale_failed_event(page, base_url):
    page.goto(f"{base_url}/agent/tasks/demo-rollback-guard")

    expect(page.get_by_text("任务已完成")).to_be_visible(timeout=30_000)
    expect(page.get_by_text("执行失败")).not_to_be_visible()
    expect(page.get_by_role("button", name="查看结果")).to_be_visible()


def test_compensation_failure_should_surface_manual_intervention(page, base_url):
    page.goto(f"{base_url}/agent/tasks/demo-compensation-failed")

    expect(page.get_by_text("补偿处理中")).to_be_visible(timeout=15_000)
    expect(page.get_by_text("需要人工介入处理")).to_be_visible(timeout=60_000)
    expect(page.get_by_role("button", name="查看处理建议")).to_be_visible()
```

**测试要点：**

- 页面状态不能领先于后端真实状态，也不能落后太久
- 终态建立后，旧失败事件不能把 UI 文案打回去
- 补偿失败时，必须明确暴露“需要人工介入”，不能长期停在模糊处理中

---

## 6. 可运行示例四：Kubernetes CronJob 周期巡检状态机收敛性

对于生产环境或准生产环境，建议把状态机不变量巡检做成定时任务。下面给出一套可直接落地的 `CronJob + ConfigMap` 示例。

### 6.1 巡检脚本 ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-state-invariant-checker
  namespace: qa
 data:
  check.py: |
    import os
    import sys
    import requests

    BASE_URL = os.environ.get("BASE_URL", "http://agent-api.qa.svc.cluster.local:8080")
    TENANT_ID = os.environ.get("TENANT_ID", "tenant-a")

    def fail(msg: str):
        print(f"[FAIL] {msg}")
        sys.exit(1)

    def main():
        resp = requests.get(
            f"{BASE_URL}/api/invariants/summary",
            headers={"X-Tenant-ID": TENANT_ID},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if data["open_terminal_regressions"] != 0:
            fail(f"terminal regressions detected: {data['open_terminal_regressions']}")

        if data["duplicate_side_effect_tasks"] != 0:
            fail(f"duplicate side effects detected: {data['duplicate_side_effect_tasks']}")

        if data["cross_tenant_violation_count"] != 0:
            fail(f"cross tenant violations detected: {data['cross_tenant_violation_count']}")

        if data["non_converged_tasks_over_slo"] != 0:
            fail(f"tasks exceed convergence SLO: {data['non_converged_tasks_over_slo']}")

        print("[PASS] agent state invariants look healthy")

    if __name__ == "__main__":
        main()
```

### 6.2 CronJob 定时巡检

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: agent-state-invariant-cron
  namespace: qa
spec:
  schedule: "*/30 * * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 2
  failedJobsHistoryLimit: 5
  jobTemplate:
    spec:
      backoffLimit: 1
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: checker
              image: python:3.11-slim
              command: ["/bin/sh", "-c"]
              args:
                - |
                  pip install --no-cache-dir requests >/tmp/pip.log 2>&1 && \
                  python /opt/check/check.py
              env:
                - name: BASE_URL
                  value: "http://agent-api.qa.svc.cluster.local:8080"
                - name: TENANT_ID
                  value: "tenant-a"
              volumeMounts:
                - name: script
                  mountPath: /opt/check
          volumes:
            - name: script
              configMap:
                name: agent-state-invariant-checker
```

### 6.3 巡检重点

这类 CronJob 不只是看服务活着没，而是周期性检查下面几类生产红线：

1. 已进入终态的任务是否发生回退；
2. 是否有重复副作用任务；
3. 是否存在跨租户推进；
4. 是否有超过收敛 SLO 仍未终态的任务。

如果把这些巡检信号接到告警平台，就能把“状态机正确性”从一次性测试升级为持续质量保障能力。

---

## 7. 工程落地建议

### 7.1 P0 必测不变量清单

如果你要从零开始补一套 Agent 状态机质量闸门，建议优先落这 5 条：

1. **终态唯一**：已终态任务不能再被任何旧事件改写；
2. **非法跃迁拒绝**：不允许跳过关键中间态；
3. **副作用幂等**：重复回调不重复发通知、不重复写单；
4. **视图一致**：UI、详情、时间线、审计必须同一事实；
5. **补偿可收敛**：补偿成功或失败都必须进入明确可处理终态。

### 7.2 推荐观测字段

为了让自动化测试有“抓手”，接口或审计层建议至少暴露这些字段：

- `state`
- `last_sequence`
- `version`
- `tenant_id`
- `side_effect_count`
- `current_state`
- `final_state`
- `ignored_reason`
- `user_visible_state`

### 7.3 和现有 QA 技术栈的结合方式

- **Ginkgo**：负责后端 E2E 状态推进、不变量断言、故障注入
- **Python API Testing**：负责状态接口、审计接口、非法跃迁校验
- **Playwright**：负责用户可见状态流与异常提示校验
- **K8s CronJob**：负责准生产/生产环境的持续巡检与质量哨兵

---

## 8. 今日小结

对 AI Agent 这类长链路、强异步、多副作用系统来说，**状态机不变量就是质量底线，收敛性就是生产可信度**。

真正成熟的测开体系，不应该只验证“功能能不能成功”，还要能持续回答下面这些更关键的问题：

- 任务最终会不会只停在一个合法终态？
- 旧事件会不会把新状态打坏？
- 重试和补偿会不会带来重复副作用？
- 用户看到的结果，是否真的和系统事实一致？

当你把这些问题都纳入 E2E 自动化与持续巡检后，测试的价值就不再只是“验功能”，而是在帮系统守住**分布式状态正确性**这条最重要的生产红线。
