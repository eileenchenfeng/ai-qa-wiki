---
title: "每日 AI 学习笔记｜Day 51：AI Agent 人机协同与人工接管（Human-in-the-Loop）测试"
date: 2026-06-05
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, human-in-the-loop, approval, Ginkgo, Playwright, Kubernetes, API-Testing]
---

# 每日 AI 学习笔记｜Day 51：AI Agent 人机协同与人工接管（Human-in-the-Loop）测试

<callout icon="star" bgc="4">

**核心总结：** 当 AI Agent 从“给建议”走向“可执行动作”时，真正决定系统能否上线的，往往不是它会不会自动化，而是 **它能否在该停下来的时候停下来、把足够上下文交给人、在人做出决定后稳定续跑且不产生额外副作用**。高质量测试应把 Human-in-the-Loop 能力拆成 **风险识别、审批挂起、证据快照、审批人校验、人工接管、结果回传、任务续跑、审计留痕** 八个可验证环节，并采用 **Ginkgo 做后端审批链路 E2E、Python / API 做审批契约与过期/幂等校验、Playwright 做用户视角的人工接管体验验证、K8s 做审批服务高可用与恢复演练** 的组合方案。核心原则：**不是验证“人有没有参与”，而是验证 Agent 是否把“该由人决策的部分”真正交还给人。**

</callout>

很多团队在做 AI Agent 时，会把“自动化率高”当成成熟度标志。但在真实生产环境里，用户往往并不希望系统把所有动作都自动做完。比如：生成发布建议可以自动做，读取配置可以自动做，汇总风险也可以自动做；但一旦涉及 **回滚、发通知、写配置、删资源、修改权限**，系统就必须停下来，把关键信息交给人确认。

这时候，测试重点就不再只是“功能能不能跑通”，而是 **Agent 是否正确识别风险边界、是否把上下文交接完整、是否能防止过期审批或错误审批、是否能在人工决策后从正确位置继续执行**。如果这层能力没测透，就很容易出现最危险的一类线上事故：**系统表面上有审批，实际上审批只是摆设。**

{/* truncate */}

## 0. 今日核心要点

1. **Human-in-the-Loop 测试的核心不是“多了一个确认按钮”，而是“决策权是否真的回到了人手里”**。
2. **审批对象必须结构化**：审批人、风险摘要、证据快照、待执行动作、超时时间、幂等键，都应显式暴露。
3. **过期审批、错人审批、重复审批、上下文漂移是 P0 风险**。
4. **E2E 用例应围绕完整业务链路组织**：用户发起任务 → Agent 自动完成低风险步骤 → 遇到高风险动作挂起 → 人工审阅并决策 → 系统从正确断点继续或终止。
5. **人工接管不是纯后端逻辑**：前端是否展示足够上下文、刷新后是否能恢复、审批结论是否可追溯，都会直接影响线上可运维性。
6. **没有审计留痕的 HITL，不算真正可上线的 HITL**。

---

## 1. 核心理论：为什么 Human-in-the-Loop 比“加一个审批节点”更难测

### 1.1 Agent 的难点不是“会不会停”，而是“停得对不对”

在很多系统里，所谓的人工确认只是执行前弹一个确认框。但对 AI Agent 来说，这远远不够。因为 Agent 不是固定流程引擎，而是会理解目标、拆分步骤、调工具、根据结果动态调整路径的系统。

这意味着它在“什么时候该停、把哪些信息交给谁、停下来后哪些动作必须冻结、审批通过后从哪里继续”这些问题上，都会影响真实副作用。

一个合格的 Human-in-the-Loop 机制，至少要回答下面四个问题：

1. **为什么现在要人介入**：是高风险、证据不足、权限不足，还是策略要求？
2. **人要基于什么信息做决定**：风险摘要、环境信息、证据快照、候选动作、预估影响；
3. **人做决定后系统如何执行**：继续、终止、改计划、换审批人、要求补充证据；
4. **之后怎么追溯**：是谁在什么时候基于什么上下文批准/拒绝了什么动作。

如果这些对象都没有结构化暴露，测试就会退化成“看起来能点一下批准”，而这类验证几乎挡不住真实事故。

### 1.2 Human-in-the-Loop 最常见的六类质量事故

1. **审批绕过（Approval Bypass）**：高风险动作在未审批前已经执行；
2. **上下文漂移（Context Drift）**：审批时看到的是 A 版本计划，执行时跑的是 B 版本计划；
3. **错人放行（Wrong Approver）**：无权限的人也能批准高风险动作；
4. **过期决策生效（Expired Approval Reuse）**：旧审批链接或旧确认令牌仍可继续执行；
5. **重复执行（Duplicate Resume）**：同一条批准被重复消费，导致副作用翻倍；
6. **审计缺失（Audit Gap）**：无法追溯“谁批准了什么、基于什么证据、系统随后做了什么”。

这些问题中，最容易被忽略的是“上下文漂移”。例如审批人看到的风险摘要写着“将重启测试环境服务”，但实际执行时，计划已经变成“重启生产环境服务”。如果系统没有快照版本校验，这类错误是非常致命的。

### 1.3 面向 QA 的关键指标设计

```text
AHR (Approval Honor Rate)         = 需要审批的高风险动作中，真正等待批准后才执行的次数 / 总高风险动作次数
SCR (Snapshot Consistency Rate)   = 审批时快照与实际执行计划一致的次数 / 总审批执行次数
ARR (Approver Rights Rate)        = 审批请求中权限校验正确的次数 / 总审批请求次数
AER (Approval Expiry Rejection)   = 过期审批被正确拒绝的次数 / 总过期审批尝试次数
RCR (Resume Consistency Rate)     = 批准后从正确断点恢复的次数 / 总恢复次数
ATR (Audit Traceability Rate)     = 可完整追溯审批人与证据链的任务数 / 总审批任务数
```

如果团队已经进入上线治理阶段，我建议再补两个发布门禁指标：

- **P95 Approval Wait Visibility**：审批挂起后，用户能在前端看到明确原因与下一步动作的耗时；
- **Duplicate Side Effect After Approve**：批准后因重复消费或重放导致的副作用次数，必须长期接近 0。

---

## 2. 测试建模：把 Human-in-the-Loop 拆成可验证对象

### 2.1 最小可测的审批与接管模型

如果系统没有结构化审批对象，很多关键断言就只能靠日志猜。建议至少暴露如下模型：

```go
package hitl

type ApprovalStatus string

const (
    ApprovalPending  ApprovalStatus = "pending"
    ApprovalApproved ApprovalStatus = "approved"
    ApprovalRejected ApprovalStatus = "rejected"
    ApprovalExpired  ApprovalStatus = "expired"
    ApprovalRevoked  ApprovalStatus = "revoked"
)

type ApprovalRequest struct {
    ApprovalID      string         `json:"approval_id"`
    TaskID          string         `json:"task_id"`
    PlanVersion     int64          `json:"plan_version"`
    RiskLevel       string         `json:"risk_level"`
    ActionName      string         `json:"action_name"`
    Reason          string         `json:"reason"`
    SnapshotID      string         `json:"snapshot_id"`
    CandidateOps    []string       `json:"candidate_ops"`
    ApproverIDs     []string       `json:"approver_ids"`
    RequestedBy     string         `json:"requested_by"`
    Status          ApprovalStatus `json:"status"`
    IdempotencyKey  string         `json:"idempotency_key"`
    ExpiredAt       int64          `json:"expired_at"`
}

type HandoffSnapshot struct {
    SnapshotID      string            `json:"snapshot_id"`
    TaskID          string            `json:"task_id"`
    SessionID       string            `json:"session_id"`
    Goal            string            `json:"goal"`
    CurrentStep     string            `json:"current_step"`
    Evidence        []string          `json:"evidence"`
    RiskSummary     string            `json:"risk_summary"`
    PlannedEffects  map[string]int    `json:"planned_effects"`
    Metadata        map[string]string `json:"metadata"`
}
```

这个模型至少能支持以下关键断言：

- 当前动作是不是高风险动作；
- 审批针对的是哪一个计划版本；
- 审批人是不是授权范围内的人；
- 批准后到底恢复了哪一步；
- 审批时看到的证据和系统执行时用的证据是不是同一份。

### 2.2 高价值 E2E 场景：自动诊断 → 风险挂起 → 人工确认 → 断点续跑

建议把 Human-in-the-Loop 放进一条完整业务链路里验证，而不是拆成“能创建审批”“能点通过”“能继续执行”三条碎片用例：

1. 用户提交目标：“帮我检查发布失败原因，并自动完成低风险只读诊断；若要回滚，请先给我确认”；
2. Agent 自动完成日志采集、配置比对、变更单查询等低风险步骤；
3. 当计划进入 `rollback_release` 这类高风险动作时，系统创建审批请求并挂起任务；
4. 审批人看到证据快照、风险摘要、影响面与可选动作；
5. 如果计划发生变化或审批超时，旧审批必须失效；
6. 审批通过后，任务从正确 checkpoint 继续，不得重放前置副作用；
7. 最终验证：审批前无副作用、审批后续跑正确、审计日志完整、前后端状态一致。

这类 E2E 场景能一次性把 **风险边界、人工接管、续跑正确性、幂等与审计** 全串起来，是最有价值的 HITL 测试链路。

---

## 3. Ginkgo 实战：验证审批挂起、快照一致性与续跑边界

### 3.1 抽象最小客户端接口

```go
//go:build hitl_e2e

package hitl_test

import (
    "context"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type HITLClient interface {
    ExecuteTask(ctx context.Context, sessionID, userID, goal string) (string, error)
    GetTask(ctx context.Context, taskID string) (*AgentTask, error)
    GetApproval(ctx context.Context, taskID string) (*ApprovalRequest, error)
    GetSnapshot(ctx context.Context, snapshotID string) (*HandoffSnapshot, error)
    Approve(ctx context.Context, approvalID, approverID, comment string) error
    Reject(ctx context.Context, approvalID, approverID, comment string) error
    MutatePlanVersion(ctx context.Context, taskID string) error
    GetSideEffects(ctx context.Context, taskID string) (map[string]int, error)
}
```

### 3.2 E2E 用例：高风险动作前必须挂起，批准后从正确断点续跑

```go
var _ = Describe("Agent human-in-the-loop workflow", Label("hitl", "P0", "e2e"), func() {
    var client HITLClient

    BeforeEach(func() {
        client = NewHITLClientFromEnv()
    })

    It("should pause before risky rollback and resume from checkpoint after approval", func() {
        ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
        defer cancel()

        taskID, err := client.ExecuteTask(
            ctx,
            "hitl-session-001",
            "qa-user-01",
            "检查发布失败原因，自动完成低风险诊断；若要回滚请先给我确认",
        )
        Expect(err).NotTo(HaveOccurred())

        By("等待任务进入待审批态，并验证审批对象被创建")
        Eventually(func(g Gomega) {
            task, err := client.GetTask(ctx, taskID)
            g.Expect(err).NotTo(HaveOccurred())
            g.Expect(task.Status).To(Equal(StatusWaitingApproval))

            approval, err := client.GetApproval(ctx, taskID)
            g.Expect(err).NotTo(HaveOccurred())
            g.Expect(approval.ActionName).To(Equal("rollback_release"))
            g.Expect(approval.Status).To(Equal(ApprovalPending))
            g.Expect(approval.SnapshotID).NotTo(BeEmpty())
        }).WithTimeout(90 * time.Second).WithPolling(5 * time.Second).Should(Succeed())

        By("审批前必须没有高风险副作用")
        effects, err := client.GetSideEffects(ctx, taskID)
        Expect(err).NotTo(HaveOccurred())
        Expect(effects["rollback_count"]).To(Equal(0))
        Expect(effects["prod_write_count"]).To(Equal(0))

        approval, err := client.GetApproval(ctx, taskID)
        Expect(err).NotTo(HaveOccurred())

        snapshot, err := client.GetSnapshot(ctx, approval.SnapshotID)
        Expect(err).NotTo(HaveOccurred())
        Expect(snapshot.CurrentStep).To(Equal("rollback_release"))
        Expect(snapshot.RiskSummary).To(ContainSubstring("回滚"))

        By("审批通过后，任务从正确断点继续，并最终完成")
        Expect(client.Approve(ctx, approval.ApprovalID, "release-owner-01", "已确认，可回滚测试环境版本")).To(Succeed())

        Eventually(func() TaskStatus {
            task, _ := client.GetTask(ctx, taskID)
            if task == nil {
                return ""
            }
            return task.Status
        }).WithTimeout(2 * time.Minute).WithPolling(5 * time.Second).Should(Equal(StatusCompleted))

        effects, err = client.GetSideEffects(ctx, taskID)
        Expect(err).NotTo(HaveOccurred())
        Expect(effects["rollback_count"]).To(Equal(1))
    })
})
```

### 3.3 P0 补充用例：旧快照审批不得驱动新计划执行

```go
It("should reject stale approval when plan version has changed", func() {
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
    defer cancel()

    taskID, err := client.ExecuteTask(
        ctx,
        "hitl-session-stale-001",
        "qa-user-02",
        "检查配置漂移；若需变更必须等待确认",
    )
    Expect(err).NotTo(HaveOccurred())

    Eventually(func() ApprovalStatus {
        approval, _ := client.GetApproval(ctx, taskID)
        if approval == nil {
            return ""
        }
        return approval.Status
    }).Should(Equal(ApprovalPending))

    approval, err := client.GetApproval(ctx, taskID)
    Expect(err).NotTo(HaveOccurred())

    By("模拟计划版本变更，旧审批必须失效")
    Expect(client.MutatePlanVersion(ctx, taskID)).To(Succeed())
    err = client.Approve(ctx, approval.ApprovalID, "release-owner-01", "批准旧计划")
    Expect(err).To(HaveOccurred())

    effects, err := client.GetSideEffects(ctx, taskID)
    Expect(err).NotTo(HaveOccurred())
    Expect(effects["config_write_count"]).To(Equal(0))
})
```

这个用例很关键，因为很多审批系统虽然“有版本号”，但执行时并不会校验批准时所基于的快照是否还是最新上下文。

---

## 4. Python / API Testing：把审批契约、过期控制和幂等测扎实

### 4.1 审批契约测试：创建审批后必须返回结构化快照

```python
import requests

BASE_URL = "https://agent.example.com"


def test_create_approval_contract():
    resp = requests.post(
        f"{BASE_URL}/api/agent/tasks",
        json={
            "session_id": "hitl-contract-001",
            "user_id": "qa-user-01",
            "goal": "自动诊断发布失败；如需回滚必须等待确认",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    approval = data["approval"]
    assert approval["approval_id"]
    assert approval["status"] == "pending"
    assert approval["action_name"] == "rollback_release"
    assert approval["snapshot_id"]
    assert approval["expired_at"] > 0
    assert len(approval["approver_ids"]) >= 1
```

### 4.2 过期审批测试：过期 token 必须被拒绝

```python
def test_expired_approval_should_be_rejected():
    approval_id = "approval-expired-001"

    resp = requests.post(
        f"{BASE_URL}/api/agent/approvals/{approval_id}/approve",
        json={
            "approver_id": "release-owner-01",
            "comment": "批准执行",
            "simulate_expired": True,
        },
        timeout=20,
    )

    assert resp.status_code == 409
    body = resp.json()
    assert body["error_code"] == "APPROVAL_EXPIRED"
    assert "过期" in body["message"]
```

### 4.3 幂等测试：重复批准不能导致重复续跑

```python
def test_duplicate_approve_should_be_idempotent():
    approval_id = "approval-idem-001"
    payload = {
        "approver_id": "release-owner-01",
        "comment": "同意执行",
        "idempotency_key": "approve-001",
    }

    first = requests.post(
        f"{BASE_URL}/api/agent/approvals/{approval_id}/approve",
        json=payload,
        timeout=20,
    )
    second = requests.post(
        f"{BASE_URL}/api/agent/approvals/{approval_id}/approve",
        json=payload,
        timeout=20,
    )

    first.raise_for_status()
    second.raise_for_status()

    state = requests.get(f"{BASE_URL}/api/agent/tasks/task-hitl-001", timeout=20).json()
    assert state["side_effects"]["rollback_count"] == 1
    assert state["approval_status"] == "approved"
```

### 4.4 权限校验测试：错人审批必须被拒绝

```python
def test_wrong_approver_should_be_forbidden():
    resp = requests.post(
        f"{BASE_URL}/api/agent/approvals/approval-auth-001/approve",
        json={
            "approver_id": "qa-intern-01",
            "comment": "我来替大家点一下",
        },
        timeout=20,
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == "APPROVER_NOT_ALLOWED"
```

### 4.5 上下文漂移测试：快照变更后旧审批必须失效

```python
def test_stale_snapshot_should_not_resume_new_plan():
    approval = requests.get(
        f"{BASE_URL}/api/agent/approvals/approval-stale-001",
        timeout=20,
    ).json()

    requests.post(
        f"{BASE_URL}/api/agent/tasks/{approval['task_id']}/replan",
        json={"reason": "environment_changed"},
        timeout=20,
    ).raise_for_status()

    resp = requests.post(
        f"{BASE_URL}/api/agent/approvals/{approval['approval_id']}/approve",
        json={"approver_id": "release-owner-01"},
        timeout=20,
    )

    assert resp.status_code == 409
    assert resp.json()["error_code"] == "SNAPSHOT_STALE"
```

对于 Human-in-the-Loop 系统来说，**批准动作本身就是高风险接口**。如果这个接口的契约没有测透，后面的所有“人审机制”都可能只是幻觉。

---

## 5. Playwright 实战：从用户视角验证人工接管体验与可恢复性

### 5.1 前端验证关注点

前端不只是展示一个“等待审批”标签，而是要验证用户与审批人能否看清：

- 当前任务为什么被挂起；
- 待审批动作是什么、影响范围是什么；
- 哪些证据已经收集完成；
- 谁可以审批、审批是否快过期；
- 页面刷新后，审批态和任务态是否还能恢复；
- 审批通过或拒绝后，系统是否给出明确下一步结果。

### 5.2 Playwright E2E：挂起可见、证据可审、刷新可恢复、过期可提示

```python
from playwright.sync_api import Page, expect


def test_ui_should_show_hitl_context_and_resume_after_approval(page: Page):
    page.goto("https://agent.example.com/workspace")

    page.get_by_placeholder("输入任务目标").fill(
        "自动诊断发布失败；如需回滚必须先给我确认"
    )
    page.get_by_role("button", name="开始执行").click()

    # Step 1: 任务应进入待审批态
    expect(page.get_by_text("等待人工确认")).to_be_visible(timeout=30_000)
    expect(page.get_by_text("rollback_release")).to_be_visible(timeout=10_000)

    # Step 2: 审批面板应展示证据摘要与风险说明
    expect(page.get_by_text("风险摘要")).to_be_visible()
    expect(page.get_by_text("证据快照")).to_be_visible()
    expect(page.get_by_text("影响范围")).to_be_visible()

    # Step 3: 刷新页面后，仍应恢复到原审批态
    page.reload()
    expect(page.get_by_text("等待人工确认")).to_be_visible(timeout=10_000)
    expect(page.get_by_role("button", name="批准执行")).to_be_visible()

    # Step 4: 审批通过后，任务应继续执行并最终完成
    page.get_by_role("button", name="批准执行").click()
    expect(page.get_by_text("继续执行中")).to_be_visible(timeout=20_000)
    expect(page.get_by_text("任务已完成")).to_be_visible(timeout=60_000)

    # ✅ 最终验证点：批准后应出现执行结果，而不是永远停留在审批态
    expect(page.get_by_text("回滚已执行")).to_be_visible()
```

### 5.3 UI 负向检查清单

- 页面显示“等待确认”，但后台其实还在继续跑；
- 风险摘要太弱，审批人根本不知道自己在批准什么；
- 刷新页面后任务重新开始，而不是恢复审批态；
- 审批已经过期，但按钮仍可点击；
- 用户拒绝后，前端仍显示“处理中”而不是“已终止 / 已回退到人工处理”。

---

## 6. K8s / 工程化视角：把人工接管纳入持续回归与发布门禁

### 6.1 HITL 系统在基础设施层面的常见风险

当 Human-in-the-Loop 能力落到真实工程里，很多风险来自运行时，而不仅是业务逻辑：

1. **审批服务与任务服务分离**：任务已挂起，但审批事件丢失；
2. **多副本重复消费**：同一个批准事件被两个 Worker 同时消费；
3. **审批 TTL 漏清理**：过期审批仍残留在缓存或消息队列里；
4. **滚动发布导致快照不兼容**：旧版本快照被新版本执行器误读；
5. **通知成功但状态落库失败**：审批人收到通知，但后台并未真正创建审批对象。

### 6.2 示例：用 CronJob 做夜间 HITL 回归

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: agent-hitl-nightly-regression
  namespace: ai-agent
spec:
  schedule: "30 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: hitl-regression
              image: your-registry/agent-hitl-regression:latest
              env:
                - name: TARGET_BASE_URL
                  value: "https://agent.example.com"
                - name: SUITE_LABELS
                  value: "hitl,P0,approval,resume,audit"
          restartPolicy: Never
```

这类夜间回归建议至少覆盖三种链路：

- **标准批准链路**：创建审批 → 人工批准 → 断点续跑 → 完成；
- **拒绝链路**：创建审批 → 人工拒绝 → 任务安全终止 / 转人工；
- **失效链路**：创建审批 → 上下文变更或审批过期 → 旧批准被拒绝。

### 6.3 发布前建议增加的自动门禁

如果团队已经把 Agent 用到真实环境，我建议把这些信号纳入上线门禁：

- P0 审批链路通过率；
- 审批前副作用次数必须为 0；
- 过期审批拒绝率必须达标；
- 审批快照一致率不低于基线；
- 审计链完整率必须达标；
- 批准事件重复消费次数必须为 0。

---

## 7. 测试设计建议：如何把 Human-in-the-Loop 纳入日常测试体系

### 7.1 按风险分层

- **P0**：审批绕过、错人审批、过期审批生效、快照漂移后仍继续执行；
- **P1**：审批态前后端不一致、刷新丢状态、拒绝后未正确终止；
- **P2**：审批文案不清晰、风险标签展示不统一、通知渠道略有延迟。

### 7.2 推荐回归套件结构

1. **Contract 层**：Approval / Snapshot / Resume / Audit schema；
2. **Service 层**：风险识别、审批创建、权限校验、TTL 失效、幂等消费；
3. **E2E 层**：真实业务目标驱动的完整人机协同链路；
4. **Chaos 层**：审批事件重复投递、快照版本漂移、通知与状态不一致；
5. **Online Patrol 层**：抽样巡检高风险任务，检查审批绕过与审计缺口。

### 7.3 对研发的左移建议

如果希望后续测试稳定落地，建议研发阶段先补齐这些可测试性能力：

- 每一个待审批动作都暴露 `approval_id / plan_version / snapshot_id`；
- 风险摘要和候选动作结构化输出，而不是只给一段自然语言；
- 批准 / 拒绝接口支持幂等键；
- 任务续跑时显式记录 `resume_from_step`；
- 审计日志保留审批人、审批时间、审批意见与执行结果映射。

---

## 8. 课后思考题

1. 你当前负责的 Agent 系统里，哪些动作属于“可自动执行”，哪些动作必须经过人工确认？这个边界是否被系统显式建模？
2. 如果审批人看到的证据快照与系统实际执行时的计划版本不一致，你会如何在系统和测试层双重防护？
3. 对于“拒绝执行”这一分支，你们当前系统是简单结束，还是会自动生成替代建议？这条链路是否被自动化覆盖？
4. 如果同一个批准事件被消息队列重复投递两次，你准备如何验证系统只消费一次？

---

## 9. 今日小结

今天这篇内容的重点，是把 **AI Agent 的 Human-in-the-Loop 能力** 从一个“看起来很合理的审批流程”拆成真正可落地的测试对象。对测试开发来说，真正要验证的不是“系统里有没有人工确认”，而是 **高风险动作是否真的被挂起、审批所基于的快照是否稳定、批准后是否从正确断点恢复、拒绝或过期后是否安全终止、整条链路是否可审计可追溯**。

如果把这套能力建模好，后续很多原本依赖经验判断的问题都能转成客观指标：审批遵守率、快照一致率、过期拒绝率、续跑一致率、审计链完整率。也只有把这些能力纳入回归和发布门禁，Agent 才能真正从“会自动做事”进化成“知道何时该交还决策权”的生产系统。
