---
title: "每日 AI 学习笔记｜Day 52：AI Agent 多租户隔离与工作空间边界测试"
date: 2026-06-06
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, tenant-isolation, workspace-security, Ginkgo, Playwright, Kubernetes, API-Testing]
---

# 每日 AI 学习笔记｜Day 52：AI Agent 多租户隔离与工作空间边界测试

<callout icon="star" bgc="4">

**核心总结：** 当 AI Agent 从“单用户助手”升级为“团队协作平台能力”后，最容易被低估、但一旦出事就最严重的质量问题，不是回答不准，而是 **跨租户串数、跨会话串上下文、跨工作空间误执行工具、越权访问文件或记忆**。高质量测试必须把多租户安全拆成 **身份归属、资源作用域、会话隔离、工具权限、缓存边界、异步任务归属、审计留痕** 七类可验证对象，并采用 **Ginkgo 做后端隔离链路 E2E、Python / API 做鉴权契约与越权回归、Playwright 做用户视角的工作空间切换验证、K8s 做缓存漂移与多副本一致性演练** 的组合方案。核心原则：**不是验证“用户能不能访问自己的数据”，而是验证“任何时候都绝不能访问到别人的数据”。**

</callout>

在很多 AI Agent 系统里，团队早期往往优先打通模型、工具、记忆、审批和长任务能力，等功能越来越全之后，才开始遇到真正的平台化问题：多个租户共用一套服务、多个空间共享一个向量库、多个会话共用缓存池、后台异步任务跨 Pod 漂移执行、一个用户在 A 空间发起的任务意外读取到 B 空间的上下文。

这类问题有一个共同特点：**功能测试很容易通过，但线上事故一旦发生，影响范围极大且难以补救。** 因为它不是“结果不够智能”，而是“安全边界直接失效”。所以，多租户隔离测试必须从一开始就作为 P0 质量能力纳入回归，而不是等到上线前才临时补一轮鉴权检查。

{/* truncate */}

## 0. 今日核心要点

1. **多租户测试的核心不是“账号 A 无法看到账号 B 页面”，而是“任意系统层都不能混淆资源归属”**。
2. **隔离边界必须结构化建模**：tenant_id、workspace_id、session_id、resource_owner、tool_scope、memory_namespace、task_owner 缺一不可。
3. **缓存、异步任务、重试恢复、搜索召回是最容易漏测的串租户高风险点**。
4. **E2E 用例必须围绕完整链路组织**：用户在租户 A 发起任务 → Agent 调工具 / 读记忆 / 读文件 / 写结果 → 切换到租户 B 验证不可见且不可操作。
5. **前端展示正确不等于真正隔离**：后端检索、对象存储路径、队列消费者、审计日志都必须验证归属一致性。
6. **没有审计与告警的隔离能力，不算可上线的隔离能力**。

---

## 1. 核心理论：为什么多租户隔离是 AI Agent 平台的 P0 质量红线

### 1.1 Agent 平台的隔离问题，远比普通 SaaS 更复杂

普通 SaaS 系统的隔离边界，很多时候集中在“谁能看哪条记录”。但 AI Agent 平台会把更多对象纳入执行链路：模型上下文、工具执行权限、向量检索召回、会话记忆、异步任务、审批记录、文件资产、插件配置。这意味着只要其中一个环节的作用域计算错了，就可能出现“页面没串，后台已经串了”的情况。

例如下面几类线上事故，都不一定能在简单 UI 检查里暴露：

1. 向量召回时少带了 `tenant_id` 过滤，导致把别的租户知识片段拼进当前回答；
2. Worker 从队列里拿到任务后只认 `task_id`，不校验 `workspace_id`，结果把修复动作执行到了错误环境；
3. 缓存 key 只用了 `session_id`，不同租户恰好命中同名 session，造成上下文串读；
4. 文件下载接口校验了登录态，却没有校验文件所属空间，导致“知道 file_id 就能下载”。

对 QA 来说，这意味着多租户隔离不能只做“接口 403 测试”，而要围绕 **完整业务链路中的每个状态转移点** 建立断言。

### 1.2 AI Agent 多租户最常见的七类质量事故

1. **跨租户串数（Cross-Tenant Data Leak）**：租户 A 可读到租户 B 的会话、文件、记忆或检索结果；
2. **跨空间误执行（Cross-Workspace Action）**：Agent 在错误的工作空间执行工具、变更配置或发送通知；
3. **会话污染（Session Contamination）**：同一用户或不同用户在不同空间的上下文发生混写；
4. **缓存越界（Cache Scope Break）**：缓存 key 不完整导致召回、权限、结果复用到了其他租户；
5. **异步任务漂移（Async Ownership Drift）**：任务恢复、重试或重调度后，归属信息丢失；
6. **审计缺口（Audit Gap）**：出了问题后无法证明是谁、在什么租户、对哪个资源执行了什么动作；
7. **越权旁路（Authorization Bypass）**：接口、工具或内部 RPC 有一层没校验 owner/scope，导致通过间接链路越权。

这些问题里，最危险的通常不是“看得见的 403 缺失”，而是 **检索、缓存、异步执行和恢复路径** 的边界错误，因为这些路径往往不会直接出现在前端页面上。

### 1.3 面向 QA 的关键指标设计

```text
TIR (Tenant Isolation Rate)         = 隔离场景中被正确拒绝或正确隔离的次数 / 总隔离场景次数
MSR (Memory Scope Rate)             = 记忆与检索命中均限定在正确 namespace 的次数 / 总记忆读取次数
WCR (Workspace Consistency Rate)    = 工具执行、结果写回、审计归属都与 workspace 一致的次数 / 总任务次数
CAR (Cache Attribution Rate)        = 缓存命中且归属正确的次数 / 总缓存命中次数
AOR (Async Ownership Rate)          = 异步任务恢复后 owner / tenant 信息保持正确的次数 / 总恢复次数
ULR (Unauthorized Leak Rate)        = 越权请求中实际泄露数据的次数 / 总越权请求次数
ATR (Audit Traceability Rate)       = 能完整还原租户、用户、资源、动作四元组的任务数 / 总任务数
```

如果系统已进入生产发布阶段，建议再补两个门禁指标：

- **P95 Scope Enforcement Latency**：权限与作用域校验带来的附加耗时，既要安全，也不能劣化到不可用；
- **Cross-Tenant Incident Count**：任何真实或演练中发现的串租户事件数，必须长期保持为 0。

---

## 2. 测试建模：先把隔离边界显式建出来

### 2.1 最小可测的作用域模型

很多团队的隔离问题，不是没有鉴权，而是“作用域对象不完整”。建议至少暴露下面这类结构化模型：

```go
package multitenant

type ResourceScope struct {
    TenantID      string            `json:"tenant_id"`
    WorkspaceID   string            `json:"workspace_id"`
    SessionID     string            `json:"session_id"`
    UserID        string            `json:"user_id"`
    ResourceType  string            `json:"resource_type"`
    ResourceID    string            `json:"resource_id"`
    Namespace     string            `json:"namespace"`
    Labels        map[string]string `json:"labels"`
}

type AgentTask struct {
    TaskID         string         `json:"task_id"`
    Goal           string         `json:"goal"`
    Scope          ResourceScope  `json:"scope"`
    AllowedTools   []string       `json:"allowed_tools"`
    CheckpointID   string         `json:"checkpoint_id"`
    Status         string         `json:"status"`
}

type AuditEvent struct {
    EventID        string `json:"event_id"`
    TenantID       string `json:"tenant_id"`
    WorkspaceID    string `json:"workspace_id"`
    UserID         string `json:"user_id"`
    Action         string `json:"action"`
    ResourceType   string `json:"resource_type"`
    ResourceID     string `json:"resource_id"`
    Result         string `json:"result"`
}
```

这个模型至少能帮助我们做五类关键断言：

1. 当前任务是在哪个租户、哪个空间下发起的；
2. 允许访问的工具、记忆、文件范围是什么；
3. 异步任务恢复后是否仍继承原始 scope；
4. 审计日志是否记录了完整归属信息；
5. 资源读取失败时，是“真的不存在”还是“存在但无权限”。

### 2.2 高价值 E2E 场景：租户 A 创建知识与会话，租户 B 验证不可见不可执行

建议把多租户测试放进一条完整业务链路，而不是只做几个分散接口：

1. 用户 A 在租户 `tenant-a` / 工作空间 `ws-a` 上传知识文件并创建会话；
2. Agent 基于该知识完成总结，写入记忆与执行日志；
3. 同一用户切换到 `ws-b` 或另一用户进入 `tenant-b`；
4. 发起“读取刚才文件 / 继续刚才会话 / 查询同名任务 / 执行同一工具”的请求；
5. 验证页面不可见、接口返回拒绝、检索结果不召回、异步任务无法借用旧 checkpoint；
6. 最终验证审计日志：A 的动作留在 A，B 的拒绝也要有清晰记录。

这种 E2E 场景的价值在于，它能一次性串起 **读路径、写路径、检索路径、恢复路径、审计路径**，比单点鉴权更接近真实事故模式。

---

## 3. Ginkgo 实战：验证后端多租户作用域与异步恢复边界

### 3.1 抽象最小客户端接口

```go
//go:build tenant_isolation_e2e

package multitenant_test

import (
    "context"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type TenantClient interface {
    CreateKnowledge(ctx context.Context, scope ResourceScope, name string, content []byte) (string, error)
    CreateSession(ctx context.Context, scope ResourceScope, goal string) (string, error)
    ExecuteTask(ctx context.Context, scope ResourceScope, sessionID, goal string) (string, error)
    QueryMemory(ctx context.Context, scope ResourceScope, keyword string) ([]string, error)
    GetTask(ctx context.Context, scope ResourceScope, taskID string) (*AgentTask, error)
    ResumeTask(ctx context.Context, scope ResourceScope, checkpointID string) error
    SearchKnowledge(ctx context.Context, scope ResourceScope, query string) ([]string, error)
    GetAuditEvents(ctx context.Context, scope ResourceScope, taskID string) ([]AuditEvent, error)
}
```

### 3.2 E2E 用例：租户 A 的知识与记忆不得被租户 B 召回

```go
var _ = Describe("Agent tenant isolation", Label("tenant", "P0", "e2e"), func() {
    var client TenantClient

    scopeA := ResourceScope{
        TenantID:    "tenant-a",
        WorkspaceID: "ws-a",
        SessionID:   "session-a-001",
        UserID:      "qa-owner-a",
        Namespace:   "mem-tenant-a",
    }
    scopeB := ResourceScope{
        TenantID:    "tenant-b",
        WorkspaceID: "ws-b",
        SessionID:   "session-b-001",
        UserID:      "qa-owner-b",
        Namespace:   "mem-tenant-b",
    }

    BeforeEach(func() {
        client = NewTenantClientFromEnv()
    })

    It("should isolate knowledge search and memory recall across tenants", func() {
        ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
        defer cancel()

        _, err := client.CreateKnowledge(
            ctx,
            scopeA,
            "release-a.md",
            []byte("tenant-a 内部发布窗口为 02:00-03:00，仅在工作空间 ws-a 可见"),
        )
        Expect(err).NotTo(HaveOccurred())

        sessionID, err := client.CreateSession(ctx, scopeA, "总结租户 A 的发布约束")
        Expect(err).NotTo(HaveOccurred())

        _, err = client.ExecuteTask(ctx, scopeA, sessionID, "读取知识库并总结发布窗口")
        Expect(err).NotTo(HaveOccurred())

        By("在租户 A 中应能召回自己的知识与记忆")
        Eventually(func(g Gomega) {
            hits, err := client.SearchKnowledge(ctx, scopeA, "发布窗口")
            g.Expect(err).NotTo(HaveOccurred())
            g.Expect(hits).NotTo(BeEmpty())

            memories, err := client.QueryMemory(ctx, scopeA, "发布窗口")
            g.Expect(err).NotTo(HaveOccurred())
            g.Expect(memories).To(ContainElement(ContainSubstring("02:00-03:00")))
        }).WithTimeout(90 * time.Second).WithPolling(5 * time.Second).Should(Succeed())

        By("切换到租户 B 后，相同关键词不得召回租户 A 的内容")
        Consistently(func(g Gomega) {
            hits, err := client.SearchKnowledge(ctx, scopeB, "发布窗口")
            g.Expect(err).NotTo(HaveOccurred())
            g.Expect(hits).To(BeEmpty())

            memories, err := client.QueryMemory(ctx, scopeB, "发布窗口")
            g.Expect(err).NotTo(HaveOccurred())
            g.Expect(memories).To(BeEmpty())
        }).WithTimeout(20 * time.Second).WithPolling(3 * time.Second).Should(Succeed())
    })
})
```

### 3.3 P0 补充用例：错误 workspace 不得恢复别人的 checkpoint

```go
It("should reject checkpoint resume from another workspace", func() {
    ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
    defer cancel()

    taskID, err := client.ExecuteTask(
        ctx,
        scopeA,
        "session-a-restore-001",
        "收集环境配置并在高风险步骤前暂停",
    )
    Expect(err).NotTo(HaveOccurred())

    var checkpointID string
    Eventually(func(g Gomega) {
        task, err := client.GetTask(ctx, scopeA, taskID)
        g.Expect(err).NotTo(HaveOccurred())
        g.Expect(task.CheckpointID).NotTo(BeEmpty())
        checkpointID = task.CheckpointID
    }).WithTimeout(90 * time.Second).WithPolling(5 * time.Second).Should(Succeed())

    By("租户 B / 工作空间 ws-b 试图恢复租户 A 的 checkpoint，必须失败")
    err = client.ResumeTask(ctx, scopeB, checkpointID)
    Expect(err).To(HaveOccurred())

    events, err := client.GetAuditEvents(ctx, scopeB, taskID)
    Expect(err).NotTo(HaveOccurred())
    Expect(events).To(ContainElement(HaveField("Result", Equal("denied"))))
})
```

这个用例很重要，因为很多串租户事故并不是直接“读别人的数据”，而是通过 **恢复、重试、继续执行** 这种旁路动作把别人的上下文重新拿了回来。

---

## 4. Python / API Testing：把越权接口、检索过滤与缓存边界测透

### 4.1 文件下载越权测试：知道 file_id 也不能下载别的空间文件

```python
import requests

BASE_URL = "https://agent.example.com"


def test_cross_workspace_file_download_should_be_forbidden():
    tenant_a_headers = {
        "X-Tenant-ID": "tenant-a",
        "X-Workspace-ID": "ws-a",
        "Authorization": "Bearer token-a",
    }
    tenant_b_headers = {
        "X-Tenant-ID": "tenant-b",
        "X-Workspace-ID": "ws-b",
        "Authorization": "Bearer token-b",
    }

    create_resp = requests.post(
        f"{BASE_URL}/api/files",
        headers=tenant_a_headers,
        files={"file": ("release-a.txt", b"tenant-a secret")},
        timeout=30,
    )
    create_resp.raise_for_status()
    file_id = create_resp.json()["file_id"]

    leak_resp = requests.get(
        f"{BASE_URL}/api/files/{file_id}/download",
        headers=tenant_b_headers,
        timeout=20,
    )

    assert leak_resp.status_code in {403, 404}
    assert b"tenant-a secret" not in leak_resp.content
```

### 4.2 检索隔离测试：向量召回必须带 tenant / workspace filter

```python
def test_retrieval_should_respect_tenant_scope():
    headers_a = {
        "X-Tenant-ID": "tenant-a",
        "X-Workspace-ID": "ws-a",
        "Authorization": "Bearer token-a",
    }
    headers_b = {
        "X-Tenant-ID": "tenant-b",
        "X-Workspace-ID": "ws-b",
        "Authorization": "Bearer token-b",
    }

    requests.post(
        f"{BASE_URL}/api/knowledge/index",
        headers=headers_a,
        json={"text": "tenant-a 生产发布冻结窗口是周五晚 18 点后"},
        timeout=30,
    ).raise_for_status()

    resp_a = requests.post(
        f"{BASE_URL}/api/knowledge/search",
        headers=headers_a,
        json={"query": "发布冻结窗口"},
        timeout=20,
    )
    resp_b = requests.post(
        f"{BASE_URL}/api/knowledge/search",
        headers=headers_b,
        json={"query": "发布冻结窗口"},
        timeout=20,
    )

    resp_a.raise_for_status()
    resp_b.raise_for_status()

    assert len(resp_a.json()["hits"]) >= 1
    assert resp_b.json()["hits"] == []
```

### 4.3 缓存边界测试：同 query 也不能跨租户复用结果

```python
def test_cache_key_should_include_tenant_and_workspace():
    common_query = "最近一次发布失败原因"

    resp_a = requests.post(
        f"{BASE_URL}/api/agent/query",
        headers={
            "X-Tenant-ID": "tenant-a",
            "X-Workspace-ID": "ws-a",
            "Authorization": "Bearer token-a",
        },
        json={"query": common_query},
        timeout=20,
    )
    resp_b = requests.post(
        f"{BASE_URL}/api/agent/query",
        headers={
            "X-Tenant-ID": "tenant-b",
            "X-Workspace-ID": "ws-b",
            "Authorization": "Bearer token-b",
        },
        json={"query": common_query},
        timeout=20,
    )

    resp_a.raise_for_status()
    resp_b.raise_for_status()

    body_a = resp_a.json()
    body_b = resp_b.json()

    assert body_a["scope"]["tenant_id"] == "tenant-a"
    assert body_b["scope"]["tenant_id"] == "tenant-b"
    assert body_a["trace_id"] != body_b["trace_id"]
```

### 4.4 工具越权测试：错误空间不得执行高风险动作

```python
def test_tool_execution_should_be_denied_outside_workspace_scope():
    resp = requests.post(
        f"{BASE_URL}/api/tools/execute",
        headers={
            "X-Tenant-ID": "tenant-b",
            "X-Workspace-ID": "ws-b",
            "Authorization": "Bearer token-b",
        },
        json={
            "tool_name": "restart_release",
            "resource_id": "service-in-ws-a",
            "workspace_id": "ws-a",
        },
        timeout=20,
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == "SCOPE_DENIED"
```

对于多租户平台来说，**同一个接口的 200 与 403 都不够说明问题**。真正要测的是：结果内容、缓存命中、检索召回、trace 归属、异步恢复，是否都保持在正确边界内。

---

## 5. Playwright 实战：从用户视角验证工作空间切换后的可见性与边界感知

### 5.1 前端验证重点

前端多租户测试，不只是看“列表有没有隐藏”，而是要验证用户在切换工作空间后：

- 是否只看到当前 workspace 的会话、文件、知识、审批；
- URL 切换、页面刷新、浏览器返回后，是否仍保持正确作用域；
- 搜索框输入同名关键词时，是否不会显示其他空间结果；
- 高风险按钮是否根据当前 scope 正确启用 / 禁用；
- 错误提示是否足够明确，让用户知道是“无权限”而不是“系统坏了”。

### 5.2 Playwright E2E：切换空间后旧会话不可见、旧动作不可执行

```python
from playwright.sync_api import Page, expect


def test_workspace_switch_should_hide_foreign_sessions_and_actions(page: Page):
    page.goto("https://agent.example.com/workspace/ws-a")

    # Step 1: 在 ws-a 中创建一条会话与知识摘要
    page.get_by_placeholder("输入任务目标").fill("总结 ws-a 的发布约束")
    page.get_by_role("button", name="开始执行").click()
    expect(page.get_by_text("发布约束摘要")).to_be_visible(timeout=30_000)
    expect(page.get_by_text("ws-a")).to_be_visible()

    # Step 2: 切换到 ws-b
    page.get_by_role("button", name="切换空间").click()
    page.get_by_text("ws-b").click()
    expect(page).to_have_url("https://agent.example.com/workspace/ws-b")

    # Step 3: ws-a 的历史会话不应继续显示
    expect(page.get_by_text("总结 ws-a 的发布约束")).not_to_be_visible()

    # Step 4: 搜索同关键词，也不应召回 ws-a 的内容
    page.get_by_placeholder("搜索会话、文件或知识").fill("发布约束")
    expect(page.get_by_text("ws-a")).not_to_be_visible()

    # Step 5: 试图执行针对 ws-a 资源的高风险动作，应被阻断
    page.get_by_placeholder("输入任务目标").fill("重启 ws-a 的 release 服务")
    page.get_by_role("button", name="开始执行").click()
    expect(page.get_by_text("当前空间无权限执行该操作")).to_be_visible(timeout=20_000)
```

### 5.3 UI 负向检查清单

- 页面顶部显示已经切到 `ws-b`，但列表里仍残留 `ws-a` 的历史会话；
- 浏览器刷新后，页面回到了默认空间，却继续展示上一个空间的缓存结果；
- 搜索联想先展示了旧空间命中的结果，再被后端纠正；
- 禁用按钮只是前端样式，抓包后仍可直接调用后端成功执行；
- 错误提示只有“请求失败”，没有说明是作用域 / 权限问题。

---

## 6. K8s / 工程化视角：把隔离校验纳入持续回归与运行时防线

### 6.1 多租户 Agent 在基础设施层面的常见风险

当系统跑在 K8s 上后，多租户问题经常会从业务层扩散到基础设施层：

1. **共享 Redis / Cache Key 设计不完整**：只带 task_id、不带 tenant/workspace；
2. **共享向量库过滤缺失**：索引时写了 namespace，查询时却没带过滤条件；
3. **队列消费者只认任务 ID**：重试恢复时丢失 owner scope；
4. **Sidecar / Tool Proxy 只校验 API token**：没校验资源所属租户；
5. **日志与 Trace 标签不全**：出了问题后找不到归属链路。

### 6.2 示例：用 CronJob 跑夜间隔离回归

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: agent-tenant-isolation-nightly
  namespace: ai-agent
spec:
  schedule: "10 3 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: tenant-isolation-suite
              image: registry.example.com/qa/agent-e2e:latest
              env:
                - name: TARGET_BASE_URL
                  value: "https://agent.example.com"
                - name: GINKGO_LABEL_FILTER
                  value: "tenant && (P0 || e2e)"
                - name: REPORT_TO_SLACK
                  value: "false"
              command:
                - /bin/sh
                - -c
                - |
                  ginkgo -r ./tests/e2e \
                    --label-filter="${GINKGO_LABEL_FILTER}" \
                    --json-report=/reports/tenant-isolation.json
```

### 6.3 工程建议：上线前必须有三道防线

1. **开发态防线**：所有资源对象必须显式包含 tenant/workspace scope；
2. **测试态防线**：P0 回归覆盖跨租户读、写、检索、恢复、审计五条链路；
3. **运行态防线**：日志、trace、告警必须能快速识别“跨租户访问尝试”与“串空间执行尝试”。

如果系统已经接入 OpenTelemetry，我建议至少统一以下标签：

```text
tenant.id
workspace.id
session.id
task.id
resource.type
resource.id
auth.result
scope.result
```

这样一旦出现可疑访问，就可以快速按租户、空间、资源维度做回溯，而不是在海量日志里盲查。

---

## 7. 测试策略沉淀：如何组织一套可长期维护的多租户回归体系

### 7.1 按风险分层组织回归

建议把多租户相关测试拆成四层：

1. **Contract 层**：接口必须要求 tenant/workspace 信息，缺失即拒绝；
2. **Service 层**：资源查询、缓存访问、向量检索必须带 scope filter；
3. **E2E 层**：完整业务链路下验证不可见、不可读、不可执行、不可恢复；
4. **Runtime 层**：生产巡检中持续扫描异常 audit / trace / denied 事件。

### 7.2 用例设计建议：坚持端到端场景而不是碎片权限点

对 QA 来说，最有价值的用例不是“接口 A 返回 403”，而是这种业务链路：

1. 用户在租户 A 上传文档并触发 Agent 总结；
2. 系统将知识入库、生成记忆、写入审计；
3. 租户 B 使用相同关键词检索、尝试继续任务、尝试引用同一文件；
4. 最终验证：页面不可见、接口被拒、检索为空、恢复失败、审计有记录。

这样的 E2E 设计更贴近真实用户行为，也更容易暴露“链路某一层漏了 scope”的问题。

### 7.3 建议优先级

- **P0**：跨租户读写、检索串数、checkpoint 越权恢复、工具误执行；
- **P1**：缓存污染、空间切换后残留数据、审计不完整；
- **P2**：错误提示文案不清晰、列表刷新短暂闪现旧数据、边界告警不够友好。

---

## 8. 课后思考题

1. 你当前负责的 Agent 系统里，哪些对象已经显式带上 `tenant_id / workspace_id / session_id`，哪些还依赖隐式上下文传递？
2. 如果今天要做一次串租户演练，你会优先挑“检索召回”“异步恢复”“文件下载”“工具执行”中的哪一条链路？为什么？
3. 你们的缓存 key、向量检索 filter、审计日志字段，能否支持快速证明“没有发生跨租户泄露”？
4. 如果同一用户同时加入多个 workspace，前端切换空间时有哪些缓存与浏览器状态最容易残留？
5. 如果上线后真的发生了一次跨空间误执行，团队能否在 30 分钟内通过 trace 和 audit 还原完整责任链？

---

## 9. 今日小结

今天这篇笔记聚焦的是 **AI Agent 多租户隔离与工作空间边界测试**。和传统权限测试相比，它更强调“完整链路中的归属一致性”：不仅要验证用户看不到别人的东西，还要验证系统不会在检索、缓存、异步恢复、工具执行和审计路径里偷偷混淆边界。

从工程实践上，我建议优先落地三件事：

1. **先补模型**：把 tenant / workspace / session / namespace 结构化，不要依赖隐式上下文；
2. **先补 P0 E2E**：围绕“读、写、检索、恢复、执行”五条链路建立端到端隔离用例；
3. **先补可追溯性**：把 audit 和 trace 里的归属字段补齐，否则出了事故很难快速定界。

一句话总结今天的主题：**多租户质量的目标，从来不是“功能可用”，而是“边界绝不出错”。**
