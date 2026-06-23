---
title: "每日 AI 学习笔记｜Day 47：AI Agent 可解释性与决策审计测试"
date: 2026-06-01
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, explainability, audit, observability, Ginkgo, Playwright, Kubernetes, API-Testing]
---

# 每日 AI 学习笔记｜Day 47：AI Agent 可解释性与决策审计测试

<callout icon="star" bgc="4">

**核心总结：** 当 AI Agent 进入企业关键业务后，"模型为什么这么回答" 比 "答得对不对" 更重要。没有可解释性与决策审计，就很难回答三件事：**这个决策是谁做的（人/Agent/工具/外部系统）？是基于什么输入做的？如果出事故，能否完整复盘并给出责任边界？** 测试侧不能只盯输出文本的好坏，而要把 **推理链路、工具调用、策略分支、敏感操作审批记录、审计日志** 一起纳入可验证范围。工程上建议用 **Ginkgo 做决策轨迹 E2E 校验 + Python/API 做审计契约测试 + Playwright 做前端可解释性 UI 验证 + K8s/日志系统做审计数据可靠性验证** 的组合方案。核心原则：**每一次关键决策都要能被“看见、解释、复盘、归因”。**

</callout>

在传统系统里，审计通常是权限变更、配置发布、资金操作等少数关键节点的记账；但在 AI Agent 系统中，**几乎每一次对话都在产生决策**：是否调用某个危险工具、是否执行写操作、是否越权访问某个租户数据、是否走高成本模型、是否触发自动修复流程……如果这些决策只体现在黑盒大模型的一段回答里，而没有被结构化记录和约束，任何一次“幻觉”都有可能演变成真实事故。

从 QA 角度看，可解释性与决策审计测试的目标可以总结为三层：

1. **决策可见**：关键步骤必须产生结构化 metadata（who/what/when/why/how），而不是埋在自由文本里；
2. **因果可追**：从终端结果能回溯到上游输入、策略版本、模型/工具调用序列；
3. **责任可界**：在多 Agent、多系统协作场景下，能明确区分人、Agent、外部系统各自的责任边界。

{/* truncate */}

## 1. 核心理论：从 "好不好用" 到 "说得清楚" 的质量跃迁

### 1.1 可解释性不等于“把 Prompt 打出来”

不少系统在谈可解释性时，会简单地在 UI 上加一个“查看提示词”的按钮，或者在日志里记录当前使用的系统 Prompt。**这只能算是最外层的透明度**，离真正的决策可解释还差很远。真正有价值的可解释性至少包括：

- **决策结构**：本次决策是一阶段的单步推理，还是多轮工具调用 + 再推理的组合？
- **候选方案**：是否评估过多个候选动作或答案？被淘汰的方案是否有记录？
- **约束边界**：本次决策受到哪些 business constraint、权限策略、合规规则的约束？
- **风险提示**：系统是否意识到当前回答有不确定性，是否给出置信度或风险标签？

从测试角度，**仅仅验证“能看到 Prompt”远远不够**，我们要验证：

- 日志/Trace/前端是否能看到结构化的 **DecisionTrace**（而不是只有纯文本）；
- 是否可以通过 ID（trace_id / decision_id）把一次决策在多个系统之间串起来；
- 当系统使用了某些危险权限（比如批量删除、资金划转）时，是否存在多方可验证的审批与确认链路。

### 1.2 决策审计的五个关键问题

一个合格的决策审计体系，至少要能回答下面五个问题：

1. **Who（谁发起/谁决策）**：是哪个用户、哪个租户、哪个 Agent、哪个子模块做出的决策；
2. **What（具体做了什么）**：调用了哪一类工具、对哪个资源做了什么操作（读/写/删/转移）；
3. **When（何时发生）**：时间戳、会话 ID、请求 ID、trace_id 是否统一；
4. **Why（为什么这么做）**：哪些输入、规则、模型输出驱动了这次决策；
5. **Result（结果如何）**：操作是否成功、是否被回滚、有没有后续补偿动作。

测试目标就是确保：**在任何一条高风险链路上，上面五个问题都能被结构化地回答**，而不是靠人肉翻聊天记录或截图来猜。

### 1.3 面向 QA 的可解释性/审计指标

```text
XCR (Explainability Coverage Rate) = 含结构化 DecisionTrace 的关键请求数 / 关键请求总数
ALR (Audit Log Reliability)       = 审计日志与实际执行动作一致的次数 / 抽检次数
DLT (Decision Lookup Time)        = 从请求 ID 定位到完整决策轨迹的时间 P95
RAR (Responsibility Attribution Rate) = 能准确归因的已处理事故数 / 总事故数
``` 

可以再加两个更贴近工程实践的指标：

- **MDR（Metadata Density Ratio）**：每条关键链路中结构化字段 vs 自由文本的比例，帮助避免“全都写在自然语言备注里”；
- **GCR（Guardrail Coverage Ratio）**：被审计追踪到并成功阻断的违规尝试占比，例如越权读写、越界工具调用。

---

## 2. 工程实践：把决策过程变成可测试的“数据结构”

### 2.1 设计一个最小可测的 DecisionTrace 结构

下面是一个简化版的决策轨迹数据结构，用于在编排服务里串起每一次模型调用与工具调用：

```go
package audit

type DecisionStep struct {
    StepID       string   `json:"step_id"`
    Type         string   `json:"type"`          // model_call / tool_call / rule_eval / user_confirm
    Actor        string   `json:"actor"`         // agent_name / tool_name / user
    InputSummary string   `json:"input_summary"` // 截断后的摘要，避免泄露敏感全文
    OutputSummary string  `json:"output_summary"`
    RiskLevel    string   `json:"risk_level"`    // low / medium / high
    Guardrails   []string `json:"guardrails"`    // 命中的规则或安全策略
}

type DecisionTrace struct {
    TraceID      string          `json:"trace_id"`
    SessionID    string          `json:"session_id"`
    TenantID     string          `json:"tenant_id"`
    UserID       string          `json:"user_id"`
    StartedAt    int64           `json:"started_at"`
    FinishedAt   int64           `json:"finished_at"`
    FinalStatus  string          `json:"final_status"` // success / blocked / rolled_back
    Steps        []DecisionStep  `json:"steps"`
    Approvals    []ApprovalEvent `json:"approvals"`
}

type ApprovalEvent struct {
    ApprovalID  string `json:"approval_id"`
    ApproverID  string `json:"approver_id"`
    Action      string `json:"action"`      // approved / rejected
    Reason      string `json:"reason"`
    ApprovedAt  int64  `json:"approved_at"`
}
```

这一层设计如果做得不好，后面的测试都会变成“爬日志 + 正则匹配”，既脆弱又难维护。建议在设计阶段就让 QA 参与进来，共同定义：

- 哪些字段是 **P0 必须存在** 的（如 trace_id、tenant_id、step.type）；
- 哪些字段可以按业务扩展，但必须保证 **前向兼容**（新增字段不影响旧版本解析）；
- 对于涉及敏感数据的字段（如 InputSummary），如何做脱敏与长度控制。

### 2.2 一条高价值 E2E 场景：高风险批量删除 + 多人审批

根据“端到端场景优先”的原则，我们不拆开“Agent 生成删除计划”“提交审批”“执行删除”“写审计日志”这几个动作，而是用一条 E2E 链路覆盖：

1. 用户在控制台发起指令：“请帮我删除过去 30 天内所有无主的测试环境集群”；
2. Agent 先通过只读工具扫描资源，生成删除候选列表（Step1: tool_call）；
3. Agent 识别到这是高风险操作，自动生成删除计划说明，并提交给审批流（Step2: model_call + rule_eval）；
4. 人工审批通过后，Agent 执行批量删除（Step3: tool_call）、记录结果；
5. 系统生成一条完整 DecisionTrace，并写入审计存储；
6. 前端在详情页展示“谁在什么时间批准了什么操作，删除了哪些资源”。

这条链路至少产出三类可测产物：

- HTTP/API 层面的审计查询接口（便于自动化回放与验证）；
- Trace/Log 系统里的结构化事件；
- 前端的“可解释性详情页”。

---

## 3. Ginkgo 实战：验证 DecisionTrace 与实际动作完全对齐

### 3.1 定义一个对外暴露的审计查询接口

```go
// GET /api/audit/trace/{trace_id}

type AuditTraceResponse struct {
    Trace   DecisionTrace `json:"trace"`
    Exists  bool          `json:"exists"`
}
```

### 3.2 Ginkgo E2E：执行一次高风险操作，并回查审计轨迹

```go
//go:build audit_e2e

package audit_test

import (
    "context"
    "net/http"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type DeletePlanClient interface {
    // 触发一次“删除无主测试集群”的高风险流程
    TriggerDeleteOrphanClusters(ctx context.Context, tenantID, userID string) (traceID string, err error)

    // 根据 traceID 查询审计数据
    GetAuditTrace(ctx context.Context, traceID string) (*AuditTraceResponse, int, error)
}

var _ = Describe("High-risk deletion audit trail", Label("audit", "P0", "e2e"), func() {
    var client DeletePlanClient

    BeforeEach(func() {
        client = NewDeletePlanClientFromEnv()
    })

    It("should persist a complete DecisionTrace for high-risk deletion", func() {
        ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
        defer cancel()

        traceID, err := client.TriggerDeleteOrphanClusters(ctx, "tenant-a", "qa-owner-01")
        Expect(err).NotTo(HaveOccurred())
        Expect(traceID).NotTo(BeEmpty())

        // 等待异步审计入库
        var (
            resp *AuditTraceResponse
            code int
        )

        Eventually(func(g Gomega) {
            var innerErr error
            resp, code, innerErr = client.GetAuditTrace(ctx, traceID)
            g.Expect(innerErr).NotTo(HaveOccurred())
            g.Expect(code).To(Equal(http.StatusOK))
            g.Expect(resp.Exists).To(BeTrue())
        }).WithTimeout(30 * time.Second).WithPolling(2 * time.Second).Should(Succeed())

        trace := resp.Trace

        // Step 1: 基本字段齐全
        Expect(trace.TraceID).To(Equal(traceID))
        Expect(trace.TenantID).To(Equal("tenant-a"))
        Expect(trace.UserID).To(Equal("qa-owner-01"))
        Expect(trace.Steps).NotTo(BeEmpty())

        // Step 2: 至少包含“扫描资源”和“执行删除”两个步骤
        var hasScan, hasDelete bool
        for _, step := range trace.Steps {
            if step.Type == "tool_call" && step.Actor == "resource_scanner" {
                hasScan = true
            }
            if step.Type == "tool_call" && step.Actor == "cluster_deleter" {
                hasDelete = true
            }
            // 高风险操作必须有显式风险标注
            if step.Actor == "cluster_deleter" {
                Expect(step.RiskLevel).To(Equal("high"))
                Expect(step.Guardrails).To(ContainElement("require_approval"))
            }
        }
        Expect(hasScan).To(BeTrue(), "DecisionTrace should contain a resource scan step")
        Expect(hasDelete).To(BeTrue(), "DecisionTrace should contain a delete execution step")

        // Step 3: 审批事件必须存在
        Expect(trace.Approvals).NotTo(BeEmpty())
        Expect(trace.Approvals[0].Action).To(Equal("approved"))
        Expect(trace.FinalStatus).To(BeElementOf("success", "rolled_back"))
    })
})
```

### 3.3 Ginkgo 断言 checklist

- 不仅要验证 **业务动作成功**，还要验证审计轨迹是否存在且字段齐全；
- 不仅要看 Steps 数量，还要检查是否包含预期的关键 step.type / actor；
- 对高风险操作，必须有 **risk_level=high + guardrails 中包含 require_approval**；
- 审批事件不能缺失，否则说明“实际执行了，但审计信息不完整”。

---

## 4. Python / API Testing：把审计能力做成可回归的契约

### 4.1 基于 HTTP API 的审计契约测试

```python
import requests


BASE_URL = "https://agent.example.com"


def test_audit_trace_contract():
    # 1. 先触发一条简单的高风险操作（例如演练环境的只读删除模拟）
    trigger_resp = requests.post(
        f"{BASE_URL}/api/sandbox/delete-orphan-clusters", json={"tenant_id": "tenant-a"}, timeout=30
    )
    trigger_resp.raise_for_status()
    body = trigger_resp.json()
    trace_id = body["trace_id"]
    assert trace_id

    # 2. 再根据 trace_id 回查审计接口
    audit_resp = requests.get(f"{BASE_URL}/api/audit/trace/{trace_id}", timeout=30)
    audit_resp.raise_for_status()

    data = audit_resp.json()["trace"]

    # 基本字段
    assert data["trace_id"] == trace_id
    assert data["tenant_id"] == "tenant-a"
    assert isinstance(data["steps"], list) and data["steps"]

    # 步骤字段
    for step in data["steps"]:
        assert step["type"] in {"model_call", "tool_call", "rule_eval", "user_confirm"}
        assert "actor" in step and step["actor"]
        assert "risk_level" in step

    # 审批字段
    approvals = data.get("approvals", [])
    assert isinstance(approvals, list)
    if approvals:  # 某些低风险链路可以没有审批
        assert approvals[0]["action"] in {"approved", "rejected"}
```

### 4.2 故障注入：验证“操作失败但审计仍然落盘”

```python
import requests


def test_audit_should_persist_even_when_action_fails():
    # 故障注入: 让删除动作在执行阶段故意失败
    trigger_resp = requests.post(
        f"{BASE_URL}/api/sandbox/delete-orphan-clusters",
        json={"tenant_id": "tenant-a", "fault_injection": {"delete_stage": "fail"}},
        timeout=30,
    )
    # 删除接口本身可以返回 4xx/5xx
    assert trigger_resp.status_code in (400, 409, 500)
    body = trigger_resp.json()
    trace_id = body["trace_id"]

    audit_resp = requests.get(f"{BASE_URL}/api/audit/trace/{trace_id}", timeout=30)
    audit_resp.raise_for_status()
    trace = audit_resp.json()["trace"]

    assert trace["final_status"] in {"blocked", "rolled_back"}
    # 即便业务失败，也必须留下完整审计轨迹
    assert len(trace["steps"]) > 0
```

---

## 5. Playwright 实战：让前端把“决策过程”展示给用户

### 5.1 前端可解释性 UI 的基本职责

对终端用户来说，他们不关心 JSON Schema 和内部 Trace，只关心：

- 这个答案是不是拍脑袋的，还是经过了工具调用和规则校验；
- 在执行高风险动作前，系统是否给了足够的提示和确认；
- 事后能否通过界面看到“是谁批准了什么”。

因此，前端至少要提供：

1. 一个“**决策详情 / 决策轨迹**”的入口；
2. 在高风险场景中突出展示 **风险提示 + 审批记录**；
3. 在开发者/运维视图中，展示 trace_id、step 列表、关键信息摘要。

### 5.2 Playwright E2E：高风险删除流程的可解释性验证

```python
from playwright.sync_api import Page, expect


def test_ui_should_show_decision_trace_for_high_risk_deletion(page: Page):
    # 进入演练环境 + 高风险操作场景
    page.goto("https://agent.example.com/console/sandbox")

    # Step 1: 触发高风险操作
    page.get_by_role("button", name="删除无主测试集群").click()

    # Step 2: UI 必须明确提示风险，并要求用户确认
    expect(page.get_by_text("这是高风险操作")).to_be_visible(timeout=10_000)
    expect(page.get_by_text("将删除过去 30 天内无主测试环境集群")).to_be_visible(timeout=10_000)

    # 模拟用户确认
    page.get_by_role("button", name="提交审批").click()

    # 测试环境可以直接模拟审批通过
    page.get_by_role("button", name="模拟审批通过").click()

    # Step 3: 删除完成后，页面必须出现“决策详情”入口
    expect(page.get_by_role("button", name="查看决策详情")).to_be_visible(timeout=30_000)
    page.get_by_role("button", name="查看决策详情").click()

    # Step 4: 决策详情中要能看到关键审计信息
    expect(page.get_by_text("决策轨迹")).to_be_visible()
    expect(page.get_by_text("resource_scanner")).to_be_visible()
    expect(page.get_by_text("cluster_deleter")).to_be_visible()
    expect(page.get_by_text("risk_level: high")).to_be_visible()
    expect(page.get_by_text("guardrails: require_approval")).to_be_visible()

    # Step 5: 审批人和时间也要可见
    expect(page.get_by_text("审批人")).to_be_visible()
    expect(page.get_by_text("已通过"))
```

### 5.3 前端检查清单

- 是否为所有高风险操作提供了明显的风险提示与确认对话框；
- 是否提供了独立的“决策详情/审计详情”入口，且内容与后端 DecisionTrace 对齐；
- 是否避免把关键信息只写在模糊的自然语言提示中，而是以结构化字段呈现；
- 在多租户场景下，是否避免把别的租户的审计信息暴露给当前用户。

---

## 6. K8s 与日志系统：确保审计数据“写得进、查得出、删得掉”

### 6.1 审计数据的三大工程风险

1. **写不全/写不进**：高 QPS 时审计写入被丢弃，或部分字段未填；
2. **查不出/查不准**：查询接口无法在 SLA 内返回完整轨迹，或多系统时间线对不齐；
3. **删不掉/删不干净**：在用户要求删除数据或合规清理时，审计数据无法按要求清理。

### 6.2 示例：用 K8s Job + Ginkgo 做审计写入压力与完整性测试

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: agent-audit-load-test
  namespace: ai-agent
spec:
  template:
    spec:
      containers:
        - name: runner
          image: your-registry/agent-audit-tester:latest
          env:
            - name: TARGET_BASE_URL
              value: "https://agent.example.com"
      restartPolicy: Never
  backoffLimit: 0
```

在镜像内部运行一个 Ginkgo Suite，持续触发高风险操作并验证审计写入：

```go
var _ = Describe("Audit load and integrity", Label("audit", "load"), func() {
    It("should keep ALR above 99.9% under load", func() {
        ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
        defer cancel()

        var (
            total int
            ok    int
        )

        for i := 0; i < 500; i++ {
            total++
            traceID, err := triggerHighRiskAction(ctx)
            if err != nil {
                continue
            }
            trace, err := queryAuditTrace(ctx, traceID)
            if err != nil {
                continue
            }
            if len(trace.Steps) > 0 {
                ok++
            }
        }

        Expect(float64(ok) / float64(total)).To(BeNumerically(">=", 0.999))
    })
})
```

### 6.3 数据生命周期与合规测试

对于包含个人信息或敏感业务数据的审计记录，必须验证：

- 是否支持按租户、按时间窗口做批量清理；
- 清理后，审计查询接口是否不再返回被清理的内容；
- 日志、缓存、副本存储中是否存在“幽灵副本”。

---

## 7. 课后思考题

1. 你所在的系统里，哪些操作可以被视为“高风险动作”？目前是否已经有结构化的 DecisionTrace 或审计记录？
2. 如果让你为现有系统增加一个“可解释性详情页”，你会选择展示哪些信息？哪些是给普通用户看的，哪些是给开发/运维看的？
3. 在多 Agent 协同的场景中，如果一次错误决策是由下游 Agent 的误判引起的，你会如何设计责任归因与审计标记？
4. 思考如何用现有的链路追踪系统（如 OpenTelemetry）与审计模块打通，避免重复采集与存储。

---

## 8. 今日小结

- AI Agent 的可解释性不只是“把 Prompt 打出来”，而是要对 **决策过程本身建模**；
- 一个好的决策审计体系，必须能回答 Who/What/When/Why/Result 五个问题；
- 工程上可以通过 **DecisionTrace 结构 + 审计查询 API + 前端决策详情页** 把决策过程变成可测试的对象；
- Ginkgo 适合做“执行高风险动作 + 回查审计轨迹”的端到端验证；
- Python/API 测试可以把审计接口固化为契约，避免 Schema 演进时悄悄破坏可解释性；
- Playwright 负责验证用户视角的可解释性体验：风险提示、审批记录、决策轨迹展示；
- K8s 与日志系统层面，需要关注审计数据在高负载下的完整性、可查询性与合规清理能力；
- 作为 QA，我们的目标不仅是“系统能跑起来”，更是“当出问题时，能说清楚发生了什么、为什么会这样、以后如何避免”。
