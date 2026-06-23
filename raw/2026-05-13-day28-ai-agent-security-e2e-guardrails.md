---
title: "每日 AI 学习笔记｜Day 28：AI Agent 安全测试的端到端防线设计"
date: 2026-05-13
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, security, SDET, Ginkgo, Playwright, K8s, e2e]
---

# 每日 AI 学习笔记 Day 28｜AI Agent 安全测试的端到端防线设计

## 核心总结

面向 Senior SDET 的 AI Agent 安全测试，不能停留在“接口是否鉴权”“Prompt Injection 是否命中一条规则”这样的单点验证，而要把 **身份边界、会话上下文、工具权限、敏感数据、K8s 运行时、审计证据与最终用户可见结果** 串成一条完整的 E2E 安全链路。真正可靠的安全质量门禁，应从用户提交一个真实 Agent 任务开始，经过身份鉴别、权限校验、上下文过滤、工具调用、结果生成、日志与 trace 归档，最终验证系统既完成了业务目标，又没有越权、泄露、污染记忆或突破运行时边界。对 AI Agent 来说，安全不是一个“前置网关功能”，而是贯穿整个任务生命周期的工程属性：任何一个环节失守，都可能把一次正常请求演变成数据泄露、横向越权或高危工具误调用。

{/* truncate */}

## 0. 今日目标

今天正式进入安全质量主题，聚焦 AI Agent 在真实业务链路中的 E2E 安全设计。完成今天的学习后，你应该能够做到四件事。第一，能把 AI Agent 的安全问题建模为端到端用户旅程，而不是拆成互不关联的鉴权、Prompt、防注入和日志检查。第二，能用 Golang Ginkgo 为 Agent 设计覆盖身份、权限、数据隔离与工具调用的安全 E2E 用例。第三，能用 Python Playwright 从真实用户视角验证前端页面、会话状态和越权结果是否被正确拦截。第四，能把 K8s 运行时安全、应用层权限控制和审计证据纳入同一条发布前安全门禁。

本篇内容面向已经具备 API 自动化、浏览器自动化、Kubernetes 与基础安全工程经验的 Senior SDET。重点不是介绍零散概念，而是教你如何把 AI Agent 的安全风险落成可执行、可复现、可接入 CI/CD 的 E2E 测试资产。

---

## 1. 核心理论：AI Agent 的安全对象是“完整任务闭环”

### 1.1 为什么传统安全测试方法容易漏掉 Agent 真风险

传统 Web 或 API 系统的安全测试，往往围绕几个固定边界展开：登录态是否合法、接口鉴权是否生效、参数是否存在注入、响应是否泄露敏感字段。这些方法在普通 CRUD 系统中很有效，但在 AI Agent 场景里，只验证单个接口通常只能看到“入口是否安全”，看不到“整个任务是否安全”。

AI Agent 的真实执行链路通常包含用户输入理解、系统 Prompt 拼装、知识检索、外部工具调用、模型生成、状态持久化、结果展示和操作审计。风险也因此被扩散到了多个环节。例如，入口接口已经鉴权通过，但 Agent 在调用工具时没有重新做租户隔离；页面只显示当前用户的数据，但 trace 或日志却暴露了上一个会话的上下文；Prompt Injection 没有直接触发危险输出，却成功诱导 Agent 调用了不该调用的内部工具。

Senior SDET 在 Agent 安全测试中要重点识别三类“假安全”。第一类是 **入口安全、链路失守**：API 网关通过了鉴权，但下游工具没有继承用户权限。第二类是 **界面安全、证据泄露**：页面显示正常，但日志、trace、缓存或下载产物中暴露了敏感信息。第三类是 **单点拦截、全链路绕过**：一条 Prompt Injection 测试被阻断了，但用户换一种表达、换一类工具或换一个会话上下文后仍然可以越权成功。

### 1.2 AI Agent 安全 E2E 的五层防线

一个可落地的 Agent 安全测试模型，至少应覆盖五层。

1. **身份层**：用户身份、会话令牌、租户标识、角色声明是否真实且可传递。
2. **授权层**：每一步工具调用、知识访问、结果下载是否重新校验最小权限，而不是只信任入口鉴权。
3. **数据层**：Prompt、检索片段、记忆缓存、日志、trace 与导出结果中是否存在敏感数据泄露。
4. **执行层**：模型、工具、工作流与 K8s 运行时是否被限制在允许的资源和网络边界内。
5. **审计层**：失败、拦截、降级与越权尝试是否留下可追踪、可归因、可复盘的证据。

这五层不是五条割裂的测试集合，而是一条 E2E 安全用例中的连续验证点。单点检查应下沉到步骤中。例如“JWT 合法”是用户发起任务前的前置状态，“工具调用携带正确租户头”是中间状态，“页面未展示敏感内容且审计事件完整落盘”才是最终安全验证结果。

### 1.3 Agent 安全门禁的核心原则

AI Agent 的安全门禁应遵循三个原则。

第一，**以真实攻击路径为主线**。不要只测“接口 403”或“敏感词命中”，而要模拟真实用户任务，例如“让 Agent 读取另一个项目的测试报告”“诱导 Agent 导出内部配置”“借助上下文污染让 Agent 调错工具权限”。

第二，**以最终可观察结果判断风险**。一次攻击即使没有直接拿到敏感数据，只要它成功触发了越权工具调用、跨租户检索或错误的审计归属，就应视为安全失败。对 QA 来说，`403` 只是一个中间信号，不是全部结论。

第三，**以证据闭环支撑阻断决策**。当安全门禁失败时，报告必须能直接回答四个问题：谁发起了请求、走到了哪一步、越过了哪条边界、最终暴露了什么结果。没有 `trace_id`、`user_id`、`tenant_id`、`tool_name` 与错误分桶的安全测试，很难真正帮助研发修复问题。

---

## 2. 风险建模：把 Agent 安全场景翻译成 E2E 用户旅程

### 2.1 Senior SDET 需要优先覆盖的高风险场景

对 AI Agent 产品，下面四类场景通常应优先进入 E2E 安全资产池。

- **跨租户数据访问场景**：用户 A 请求 Agent 总结用户 B 或另一个项目的测试记录、发布报告或私有知识。
- **高危工具误调用场景**：用户诱导 Agent 调用数据库、Shell、工单审批、部署或文件下载工具。
- **会话污染与记忆泄露场景**：当前会话无权访问的数据，经由历史记忆、缓存、RAG 召回或系统提示残留暴露出来。
- **运行时逃逸与配置暴露场景**：Agent 在 K8s 中通过环境变量、挂载文件、Metadata 服务、Node 网络或 Sidecar 配置泄露敏感信息。

这些场景都不应该设计成“单点工具验证”或“单一 API 断言”，而应该从用户动作开始，到用户最终看到的结果、系统留下的审计证据结束。

### 2.2 推荐的安全场景资产字段

建议把安全场景沉淀成统一 JSON/YAML 资产，让 Ginkgo、Playwright、Mock 服务与 CI 门禁复用。一个最小安全场景建议包含以下字段：

```json
{
  "case_id": "agent-sec-cross-tenant-001",
  "scenario": "cross-tenant-report-access",
  "user_role": "qa_member",
  "tenant_id": "team-a",
  "user_action": "Ask the Agent to summarize Team B's failed release report.",
  "attack_vector": "prompt_injection_or_direct_request",
  "expected_intermediate_states": [
    "request_authenticated",
    "authorization_checked",
    "knowledge_scope_filtered",
    "tool_call_blocked"
  ],
  "final_checks": [
    "http status in [200, 403] depending on product contract",
    "final answer contains refusal or safe fallback",
    "no secret or cross-tenant data exposed",
    "audit event contains user_id tenant_id trace_id decision"
  ]
}
```

这类资产的价值在于把安全测试从“人工想到什么测什么”升级成“围绕攻击路径版本化管理”。一旦资产规范稳定，功能回归、发布门禁与事故复盘都可以共享同一套安全语义。

### 2.3 E2E 安全用例如何避免碎片化

很多团队做安全自动化时，容易把鉴权、越权、敏感词、日志检查拆成几十条碎片用例，最后每一条都通过，但用户仍然能绕过系统。更好的方法是把这些检查都折叠进一条完整旅程里。

比如“跨租户报告访问”这条 E2E 安全用例，可以从用户登录并进入页面开始，随后提交一个包含越权意图的任务，验证 API 返回 run_id 与 trace_id，轮询任务状态，校验服务端没有调用高危工具，最终验证页面输出拒绝结果、导出产物为空、日志中没有泄露目标租户信息、审计事件记录了拦截决策。这样设计既符合真实攻击路径，也更利于失败后的定位。

---

## 3. 工程实践一：搭建一个可验证安全边界的 Agent Demo

下面的 Demo 用于模拟“用户请求 Agent 读取发布报告”的场景。它会根据 `x-user-role` 与 `x-tenant-id` 决定是否允许访问指定租户的数据，并在响应中返回 `trace_id` 与审计结果，方便后续 Ginkgo 和 Playwright 走完整链路。

安装依赖：

```bash
pip install fastapi uvicorn pydantic
```

保存为 `agent_security_demo.py`：

```python
import time
import uuid
from typing import Dict

from fastapi import FastAPI, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Agent Security Demo")
RUNS: Dict[str, dict] = {}
REPORTS = {
    "team-a": "Team A release report: one flaky test fixed, no secrets.",
    "team-b": "Team B release report: contains internal release notes and restricted evidence.",
}


class CreateRunRequest(BaseModel):
    task: str
    target_tenant: str


@app.get("/healthz")
def healthz():
    return {"status": "ok", "component": "agent-security-demo"}


@app.post("/api/agent/runs", status_code=201)
def create_run(
    payload: CreateRunRequest,
    x_user_id: str = Header(...),
    x_user_role: str = Header(...),
    x_tenant_id: str = Header(...),
    x_trace_id: str | None = Header(default=None),
):
    trace_id = x_trace_id or f"trace-{uuid.uuid4().hex[:10]}"
    run_id = f"run-{uuid.uuid4().hex[:10]}"
    same_tenant = x_tenant_id == payload.target_tenant
    privileged = x_user_role in {"security_admin", "release_admin"}

    decision = "allow" if same_tenant or privileged else "deny"
    RUNS[run_id] = {
        "run_id": run_id,
        "trace_id": trace_id,
        "requester": x_user_id,
        "role": x_user_role,
        "source_tenant": x_tenant_id,
        "target_tenant": payload.target_tenant,
        "status": "running",
        "stage": "authorization",
        "decision": decision,
        "created_at": time.time(),
        "audit": {
            "user_id": x_user_id,
            "tenant_id": x_tenant_id,
            "target_tenant": payload.target_tenant,
            "trace_id": trace_id,
            "policy": "cross_tenant_report_access",
            "decision": decision,
        },
    }
    return {"run_id": run_id, "trace_id": trace_id, "status": "running"}


@app.get("/api/agent/runs/{run_id}")
def get_run(run_id: str):
    run = RUNS[run_id]
    elapsed = time.time() - run["created_at"]
    if elapsed > 0.8:
        if run["decision"] == "allow":
            run["status"] = "succeeded"
            run["stage"] = "completed"
            run["result"] = REPORTS[run["target_tenant"]]
        else:
            run["status"] = "blocked"
            run["stage"] = "policy_denied"
            run["result"] = "Access denied: you are not allowed to access another tenant's release report."
    return run


@app.get("/audit/{run_id}")
def get_audit(run_id: str):
    return RUNS[run_id]["audit"]


@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!doctype html>
<html>
  <head><title>Agent Security Demo</title></head>
  <body>
    <h1>Agent Security Demo</h1>
    <label for="tenant">Target tenant</label>
    <input id="tenant" value="team-b" />
    <button id="submit">Read report</button>
    <pre id="status">idle</pre>
    <script>
      async function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
      document.querySelector('#submit').addEventListener('click', async () => {
        const targetTenant = document.querySelector('#tenant').value;
        const traceId = `pw-${Date.now()}`;
        const createResp = await fetch('/api/agent/runs', {
          method: 'POST',
          headers: {
            'content-type': 'application/json',
            'x-user-id': 'qa-user-a',
            'x-user-role': 'qa_member',
            'x-tenant-id': 'team-a',
            'x-trace-id': traceId,
          },
          body: JSON.stringify({
            task: 'Summarize the release report.',
            target_tenant: targetTenant,
          })
        });
        const created = await createResp.json();
        for (let i = 0; i < 10; i++) {
          const pollResp = await fetch(`/api/agent/runs/${created.run_id}`);
          const run = await pollResp.json();
          document.querySelector('#status').textContent = JSON.stringify(run, null, 2);
          if (run.status === 'succeeded' || run.status === 'blocked') return;
          await sleep(250);
        }
      });
    </script>
  </body>
</html>
"""
```

本地启动：

```bash
uvicorn agent_security_demo:app --host 0.0.0.0 --port 8080
```

快速验证：

```bash
curl -s http://127.0.0.1:8080/healthz
curl -s -X POST http://127.0.0.1:8080/api/agent/runs \
  -H 'content-type: application/json' \
  -H 'x-user-id: qa-user-a' \
  -H 'x-user-role: qa_member' \
  -H 'x-tenant-id: team-a' \
  -H 'x-trace-id: manual-sec-001' \
  -d '{"task":"Summarize release report","target_tenant":"team-b"}'
```

这个 Demo 虽然简单，但已经包含安全 E2E 需要的关键结构：身份头、租户隔离、授权决策、最终结果拦截和独立审计接口。

---

## 4. 工程实践二：用 Golang Ginkgo 验证跨租户访问是否被真正阻断

安全测试最常见的误区之一，是只断言接口返回 403 或 200，而没有继续验证最终任务状态、审计证据与用户可见结果。下面这条 Ginkgo 用例围绕“普通 QA 用户尝试读取其他租户发布报告”这条完整业务链路展开。

初始化依赖：

```bash
go mod init agent-security-gate
go get github.com/onsi/ginkgo/v2 github.com/onsi/gomega
```

保存为 `agent_security_gate_test.go`：

```go
package securitygate_test

import (
    "bytes"
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "os"
    "testing"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

func TestSecurityGate(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Agent Security Gate Suite")
}

type createRunResponse struct {
    RunID   string `json:"run_id"`
    TraceID string `json:"trace_id"`
    Status  string `json:"status"`
}

type runStatusResponse struct {
    RunID        string `json:"run_id"`
    TraceID      string `json:"trace_id"`
    Status       string `json:"status"`
    Stage        string `json:"stage"`
    Result       string `json:"result"`
    Decision     string `json:"decision"`
    TargetTenant string `json:"target_tenant"`
    SourceTenant string `json:"source_tenant"`
}

type auditResponse struct {
    UserID       string `json:"user_id"`
    TenantID     string `json:"tenant_id"`
    TargetTenant string `json:"target_tenant"`
    TraceID      string `json:"trace_id"`
    Policy       string `json:"policy"`
    Decision     string `json:"decision"`
}

var _ = Describe("AI Agent security gate", Ordered, func() {
    var baseURL string
    var httpClient *http.Client

    BeforeAll(func() {
        baseURL = os.Getenv("AGENT_BASE_URL")
        if baseURL == "" {
            baseURL = "http://127.0.0.1:8080"
        }
        httpClient = &http.Client{Timeout: 5 * time.Second}
    })

    It("blocks a normal QA user from reading another tenant's release report and leaves audit evidence", func(ctx SpecContext) {
        By("checking runtime health before starting the user journey")
        healthReq, err := http.NewRequestWithContext(ctx, http.MethodGet, baseURL+"/healthz", nil)
        Expect(err).NotTo(HaveOccurred())
        healthResp, err := httpClient.Do(healthReq)
        Expect(err).NotTo(HaveOccurred())
        defer healthResp.Body.Close()
        Expect(healthResp.StatusCode).To(Equal(http.StatusOK))

        By("creating a cross-tenant Agent task as a regular QA member")
        traceID := fmt.Sprintf("ginkgo-sec-%d", time.Now().UnixNano())
        payload := map[string]string{
            "task": "Summarize the target release report.",
            "target_tenant": "team-b",
        }
        body, err := json.Marshal(payload)
        Expect(err).NotTo(HaveOccurred())

        createReq, err := http.NewRequestWithContext(ctx, http.MethodPost, baseURL+"/api/agent/runs", bytes.NewReader(body))
        Expect(err).NotTo(HaveOccurred())
        createReq.Header.Set("content-type", "application/json")
        createReq.Header.Set("x-user-id", "qa-user-a")
        createReq.Header.Set("x-user-role", "qa_member")
        createReq.Header.Set("x-tenant-id", "team-a")
        createReq.Header.Set("x-trace-id", traceID)

        createResp, err := httpClient.Do(createReq)
        Expect(err).NotTo(HaveOccurred())
        defer createResp.Body.Close()
        Expect(createResp.StatusCode).To(Equal(http.StatusCreated))

        var created createRunResponse
        Expect(json.NewDecoder(createResp.Body).Decode(&created)).To(Succeed())
        Expect(created.RunID).To(HavePrefix("run-"))
        Expect(created.TraceID).To(Equal(traceID))
        Expect(created.Status).To(Equal("running"))

        By("polling until the Agent reaches a terminal security decision")
        var final runStatusResponse
        Eventually(func(g Gomega) string {
            pollReq, err := http.NewRequestWithContext(ctx, http.MethodGet, baseURL+"/api/agent/runs/"+created.RunID, nil)
            g.Expect(err).NotTo(HaveOccurred())
            pollResp, err := httpClient.Do(pollReq)
            g.Expect(err).NotTo(HaveOccurred())
            defer pollResp.Body.Close()
            g.Expect(pollResp.StatusCode).To(Equal(http.StatusOK))
            g.Expect(json.NewDecoder(pollResp.Body).Decode(&final)).To(Succeed())
            g.Expect(final.TraceID).To(Equal(traceID))
            g.Expect(final.TargetTenant).To(Equal("team-b"))
            g.Expect(final.SourceTenant).To(Equal("team-a"))
            return final.Status
        }).WithContext(ctx).WithTimeout(5 * time.Second).WithPolling(250 * time.Millisecond).Should(Or(Equal("blocked"), Equal("succeeded")))

        By("verifying the final user-visible security result")
        Expect(final.Status).To(Equal("blocked"))
        Expect(final.Stage).To(Equal("policy_denied"))
        Expect(final.Decision).To(Equal("deny"))
        Expect(final.Result).To(ContainSubstring("Access denied"))
        Expect(final.Result).NotTo(ContainSubstring("Team B release report"))

        By("checking the audit record for the denied decision")
        auditReq, err := http.NewRequestWithContext(ctx, http.MethodGet, baseURL+"/audit/"+created.RunID, nil)
        Expect(err).NotTo(HaveOccurred())
        auditResp, err := httpClient.Do(auditReq)
        Expect(err).NotTo(HaveOccurred())
        defer auditResp.Body.Close()
        Expect(auditResp.StatusCode).To(Equal(http.StatusOK))

        var audit auditResponse
        Expect(json.NewDecoder(auditResp.Body).Decode(&audit)).To(Succeed())
        Expect(audit.UserID).To(Equal("qa-user-a"))
        Expect(audit.TenantID).To(Equal("team-a"))
        Expect(audit.TargetTenant).To(Equal("team-b"))
        Expect(audit.TraceID).To(Equal(traceID))
        Expect(audit.Policy).To(Equal("cross_tenant_report_access"))
        Expect(audit.Decision).To(Equal("deny"))
    }, SpecTimeout(10*time.Second))
})
```

执行方式：

```bash
AGENT_BASE_URL=http://127.0.0.1:8080 go test ./... -v
```

这条 Ginkgo 用例符合安全 E2E 的设计方式：它不是单独立一条“鉴权接口返回什么”的单点用例，而是从用户身份出发，经过任务创建、状态轮询、最终阻断与审计验证，形成完整安全链路。

---

## 5. 工程实践三：用 Python Playwright 验证前端页面不会暴露越权结果

安全测试如果只跑后端 API，很容易漏掉前端展示层的问题。例如后端已经把结果标记为 blocked，但页面仍然把缓存中的旧数据、错误提示详情或调试信息渲染给了用户。Playwright 在这里的价值，是从用户真实可见结果出发补齐最后一公里。

安装依赖：

```bash
pip install pytest pytest-playwright
python -m playwright install chromium
```

保存为 `test_agent_security_ui.py`：

```python
import os

from playwright.sync_api import Page, expect


def test_cross_tenant_access_is_blocked_in_ui(page: Page):
    base_url = os.getenv("AGENT_BASE_URL", "http://127.0.0.1:8080")

    page.goto(base_url)
    expect(page.get_by_role("heading", name="Agent Security Demo")).to_be_visible()

    page.locator("#tenant").fill("team-b")
    page.locator("#submit").click()

    status = page.locator("#status")
    expect(status).to_contain_text('"status": "blocked"', timeout=5000)
    expect(status).to_contain_text('"decision": "deny"')
    expect(status).to_contain_text("Access denied")
    expect(status).not_to_contain_text("restricted evidence")
    expect(status).not_to_contain_text("Team B release report")
```

执行方式：

```bash
AGENT_BASE_URL=http://127.0.0.1:8080 pytest -q test_agent_security_ui.py
```

这条 Playwright 用例的重点不是“按钮能不能点”，而是验证用户通过页面发起一次越权请求后，最终看到的是安全拒绝结果，而不是目标租户的数据、调试细节或意外暴露的缓存内容。

---

## 6. 工程实践四：把 K8s 运行时边界纳入安全门禁

AI Agent 的安全风险不只发生在应用层。对运行在 Kubernetes 上的 Agent 服务来说，容器权限、网络出口、Secret 注入方式、ServiceAccount 权限与 Pod 安全上下文都会直接影响攻击面。很多“应用层已拦截”的系统，最终仍因为运行时配置过宽而泄露敏感信息。

下面是一份适合测试环境演练的 Deployment 片段，重点在于展示几个安全边界：非 root 运行、只读根文件系统、最小能力集、受限 ServiceAccount，以及通过环境变量显式注入租户安全配置。

保存为 `k8s-agent-security-demo.yaml`：

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: agent-security-demo
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-security-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: agent-security-demo
  template:
    metadata:
      labels:
        app: agent-security-demo
    spec:
      serviceAccountName: agent-security-demo
      automountServiceAccountToken: false
      containers:
        - name: app
          image: ghcr.io/example/agent-security-demo:latest
          ports:
            - containerPort: 8080
          env:
            - name: DEFAULT_TENANT_POLICY
              value: deny-cross-tenant
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            runAsNonRoot: true
            capabilities:
              drop: ["ALL"]
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8080
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agent-security-demo
spec:
  podSelector:
    matchLabels:
      app: agent-security-demo
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - namespaceSelector: {}
  egress:
    - to:
        - namespaceSelector: {}
```

Senior SDET 在安全门禁里至少要验证四类运行时信号。第一，Pod 是否以非 root 身份运行，避免工具或依赖被恶意利用后进一步提权。第二，是否禁用了不必要的 ServiceAccount Token 自动挂载，降低凭证被窃取风险。第三，网络出口是否受限，避免 Agent 被 Prompt Injection 诱导后对任意外部地址出网。第四，Secret 与配置是否通过合规方式注入，并在日志与错误页中不会直接泄露。

### 6.1 K8s 安全检查也要服务 E2E 场景

不要把 `kubectl get pod`、`kubectl describe`、`kubectl auth can-i` 这些检查孤立成安全完成的证明。它们只是 E2E 安全链路中的运行时前置验证。真正的结果仍然要回到用户旅程：一个普通用户发起越权请求后，系统有没有成功拦截，工具有没有被限制，运行时有没有出网，最终有没有留下可审计证据。

---

## 7. 工程实践五：把安全 E2E 接入 CI/CD 发布门禁

在 CI/CD 中，Agent 安全门禁可以拆成三个连续阶段，但仍围绕同一条攻击路径或高风险用户旅程。

第一阶段是 **runtime security gate**：部署到测试命名空间后，验证 Pod 安全上下文、ServiceAccount、网络策略和健康状态。第二阶段是 **API security business gate**：运行 Ginkgo，验证跨租户访问、工具权限和审计记录是否符合预期。第三阶段是 **UI security experience gate**：运行 Playwright，验证页面不会把越权结果、缓存数据或调试信息暴露给用户。

下面给出一个 GitHub Actions 风格的示例。实际落地时，可以替换为团队现有的 CI 系统或发布流水线。

```yaml
name: agent-security-gate

on:
  workflow_dispatch:

jobs:
  security-gate:
    runs-on: ubuntu-latest
    env:
      NAMESPACE: qa-security-gate
      AGENT_BASE_URL: http://127.0.0.1:8080
    steps:
      - uses: actions/checkout@v4

      - name: Verify runtime security context
        run: |
          kubectl -n $NAMESPACE get deploy agent-security-demo -o yaml
          kubectl -n $NAMESPACE get networkpolicy

      - name: Open local tunnel to candidate service
        run: |
          kubectl -n $NAMESPACE port-forward svc/agent-security-demo 8080:80 > port-forward.log 2>&1 &
          sleep 5
          curl -fsS $AGENT_BASE_URL/healthz

      - name: Run Ginkgo security journey gate
        run: |
          go test ./... -v

      - name: Run Playwright security exposure gate
        run: |
          pip install pytest pytest-playwright
          python -m playwright install chromium
          pytest -q test_agent_security_ui.py
```

门禁失败时，建议至少统一输出五类证据：请求 trace_id、请求用户与租户信息、最终决策与阻断阶段、关键审计记录、相关 Pod/Ingress/应用日志。这样研发可以快速判断失败属于授权设计问题、运行时配置问题、缓存污染问题，还是前端展示问题。

---

## 8. Senior SDET 的安全诊断路径

### 8.1 从失败结果反推突破边界的位置

当一条安全 E2E 用例失败时，不要笼统地写“存在越权风险”。先根据最终结果判断边界是在哪里被突破的。

如果页面拿到了敏感结果，先判断是后端真正放行，还是前端错误缓存/渲染。如果后端返回 blocked，但审计记录缺失，说明系统具备阻断能力但证据链不完整。如果工具没有被调用，但 RAG 召回了其他租户片段，说明问题在知识范围过滤而不是工具权限。如果运行时网络策略失效，说明即使应用层策略存在，仍可能被高危工具绕过。

### 8.2 Agent 安全测试必须关注“安全降级”

很多 Agent 产品并不是简单地允许或拒绝，而是返回一个安全降级结果，例如只给摘要不给原文、只给公共结论不给敏感细节、只返回安全模板不给真实配置。这类系统不能只用 allow/deny 二分法测试，而要验证降级内容是否真的安全、是否仍然可用、是否可审计。

对 QA 来说，下面三个问题很关键：第一，降级结果是否还保留了敏感字段或可逆线索；第二，降级路径是否仍记录了策略命中与用户上下文；第三，降级是否会被前端或下游系统误判为正常成功，从而绕过人工审查。

### 8.3 推荐的安全报告结论结构

一份高质量的 Agent 安全门禁报告，建议至少包含以下内容：攻击场景、受影响角色、目标边界、最终结果、是否存在真实泄露、阻断阶段、trace 与审计证据、复现方式、建议修复优先级。对于发布门禁来说，报告粒度应足以支撑“是否阻断发布”的决策，而不是只堆砌安全术语。

---

## 9. 今日 E2E 练习题

### 9.1 练习一：设计“高危工具调用”安全链路

请围绕“普通 QA 用户诱导 Agent 调用数据库导出工具”设计一条 E2E 安全用例。要求从用户页面输入开始，覆盖 API 创建任务、工具权限判断、任务轮询、最终页面结果与审计记录。单点验证例如“工具返回 403”“按钮可点击”“日志包含 tool_name”不要单独成用例，而要下沉到链路的步骤校验与最终验证点中。

### 9.2 练习二：补齐 K8s 运行时安全信号

请为今天的 Demo 增加一组运行时安全检查：验证 Pod 非 root、只读根文件系统、ServiceAccount Token 未自动挂载、Egress 出网受限。思考这些检查分别应该放在 E2E 安全旅程的哪个阶段，哪些是前置验证，哪些会直接影响最终攻击结果。

### 9.3 练习三：诊断一次“已拦截但仍泄露”的事故

假设系统最终返回 `blocked`，但前端页面的调试面板仍渲染了目标租户报告片段。请设计后续定位路径：你会如何区分是前端缓存、接口旁路字段、trace 回显、SSR 预取还是浏览器本地存储导致的泄露？最终报告中应如何判断这次事故是否必须阻断发布？

---

## 10. 结语

AI Agent 安全测试的成熟度，不取决于你写了多少条敏感词规则或多少个 403 断言，而取决于你是否真正围绕用户任务建立了可复现、可解释、可阻断的 E2E 安全体系。身份、权限、数据、运行时与审计这些传统安全概念，在 Agent 世界里并没有消失，只是被拉长成了一条更复杂的链路。

对 Senior SDET 来说，最关键的能力是把抽象的安全风险翻译成具体的用户旅程、工程资产与发布决策。只有当一次安全测试既能复现真实攻击路径，又能明确指出突破边界的位置，并留下足够证据推动修复，安全测试才真正从“检查项”升级为“质量门禁”。
