---
title: "每日 AI 学习笔记｜Day 48：AI Agent 记忆机制与有状态测试"
date: 2026-06-02
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, memory, stateful, Ginkgo, Playwright, Kubernetes, API-Testing]
---

# 每日 AI 学习笔记｜Day 48：AI Agent 记忆机制与有状态测试

<callout icon="star" bgc="4">

**核心总结：** AI Agent 一旦引入记忆（memory）和会话状态（state），测试难度会从“单轮问答是否正确”升级为“跨轮交互是否持续正确、隔离正确、回收正确、降级正确”。真正高价值的问题通常不是某一轮答错，而是 **上一轮的上下文是否被错误继承、A 用户的历史是否污染到 B 用户、摘要压缩后是否丢失关键约束、状态恢复时是否发生重复执行**。测试上建议采用 **Ginkgo 做多轮会话 E2E 与幂等校验、Python/API 做记忆契约和故障注入、Playwright 做用户视角的历史连续性验证、K8s 做持久层与副本恢复演练** 的组合方案。核心原则：**把“记忆”当作正式数据资产，而不是临时缓存。**

</callout>

很多团队在 Agent 早期只关注 prompt、模型效果和工具调用链路，但产品一旦进入真实业务场景，用户马上会期待它“记得我是谁、刚才说到哪了、上周定的偏好是什么”。这就是 Agent 从 stateless demo 走向 stateful system 的关键拐点。

问题也往往从这里开始：短期上下文窗口一变长，历史噪声会抬升；引入长期记忆后，又会遇到跨租户隔离、摘要失真、重复写入、延迟同步、故障恢复等一整套工程问题。对于 QA 来说，**记忆不是锦上添花功能，而是必须被系统性验证的质量面**。

{/* truncate */}

## 0. 今日核心要点

1. **记忆测试的核心不只是“记住了什么”，还包括“是否该忘、该隔离、该回滚”**。
2. **Stateful Agent 至少要覆盖四类状态**：会话历史、用户画像、工具执行中间态、外部持久化记忆。
3. **高风险缺陷通常出现在跨轮场景**：摘要压缩、上下文裁剪、重试补偿、会话恢复、并发写入。
4. **E2E 用例要按真实业务链路设计**：用户建立偏好 → 发起任务 → 中断恢复 → 再次追问 → 验证结果与记忆一致。
5. **记忆能力必须支持故障降级**：写入失败时是否退化为无状态模式，读超时时是否给出显式提示而不是悄悄编造。
6. **多租户隔离是 P0**：任何跨用户、跨空间、跨会话的记忆串读都应视为严重事故。

---

## 1. 核心理论：为什么“有记忆”会显著抬高质量门槛

### 1.1 Agent 的“记忆”不是一个东西，而是四层状态

在工程实现里，Agent 的 memory 往往不是单一模块，而是多层状态叠加：

- **短期会话状态（Session Context）**：当前窗口内的用户问题、系统提示词、最近几轮工具结果；
- **摘要状态（Conversation Summary）**：为了节省 token，把长对话压缩成摘要；
- **长期用户记忆（Long-term Memory）**：例如用户偏好、常用项目、组织信息、角色设定；
- **外部工作流状态（Workflow State）**：例如工具调用进度、审批状态、任务执行游标、Saga 补偿点。

这四层状态经常由不同组件维护：内存缓存、Redis、向量库、关系型数据库、对象存储，甚至消息队列。也就是说，**所谓“记忆出错”，本质上经常是多系统状态一致性问题**。

### 1.2 记忆系统最容易出现的五类质量事故

1. **记错（Wrong Recall）**：召回了不相关或过期的历史；
2. **漏记（Missing Recall）**：用户刚明确声明的偏好，下一轮就丢了；
3. **串记（Cross-session / Cross-tenant Leak）**：A 用户信息出现在 B 用户会话中；
4. **脏记（Stale / Corrupted Memory）**：摘要压缩错误、写入部分成功、缓存未失效；
5. **重复记（Duplicate / Replayed State）**：重试或恢复时重复执行写操作，导致状态翻倍。

QA 设计用例时，不应只问“系统有没有记住”，还要问：

- 这条记忆是如何写进去的？
- 后续在哪些条件下会被召回？
- 如果召回失败、延迟、超时、重复，系统如何表现？
- 记忆何时应过期、清空或被用户覆盖？

### 1.3 面向 QA 的关键质量指标

```text
MRR (Memory Recall Rate)        = 正确召回的记忆次数 / 应召回次数
MLR (Memory Leakage Rate)       = 跨用户/跨会话泄露次数 / 总抽检次数
SSR (Summary Survival Rate)     = 摘要压缩后关键约束仍保留的次数 / 压缩总次数
RIR (Recovery Idempotency Rate) = 中断恢复后未重复执行的次数 / 恢复总次数
MFT (Memory Fallback Transparency) = 记忆降级时用户可感知告警次数 / 实际降级次数
```

在 AI Agent 场景下，我更建议再补两个工程化指标：

- **TTMR（Time To Memory Ready）**：写入一条新记忆后，到下次查询可读的延迟 P95；
- **CCR（Context Compression Retention）**：长对话压缩后，P0 约束信息保留比例。

---

## 2. 测试建模：把“记忆”拆成可验证对象

### 2.1 最小可测的数据结构

如果系统里没有统一的记忆数据结构，测试就会退化成“看回答像不像记住了”。建议至少定义一个最小可测模型：

```go
package memory

type MemoryRecord struct {
    MemoryID      string            `json:"memory_id"`
    TenantID      string            `json:"tenant_id"`
    UserID        string            `json:"user_id"`
    SessionID     string            `json:"session_id"`
    Scope         string            `json:"scope"`         // session / user / tenant / workflow
    Category      string            `json:"category"`      // preference / summary / task_state / profile
    Content       string            `json:"content"`
    Version       int64             `json:"version"`
    CreatedAt     int64             `json:"created_at"`
    UpdatedAt     int64             `json:"updated_at"`
    ExpiresAt     int64             `json:"expires_at"`
    Source        string            `json:"source"`        // user_explicit / inferred / tool_output
    Attributes    map[string]string `json:"attributes"`
}

type RecallResult struct {
    Query         string         `json:"query"`
    Returned      []MemoryRecord `json:"returned"`
    UsedSummary   bool           `json:"used_summary"`
    FallbackMode  string         `json:"fallback_mode"` // none / stateless / stale_cache
}
```

有了这层数据结构，至少能把以下断言从“主观体验”变成“机器可校验” ：

- 当前回答到底用了哪些记忆；
- 这些记忆来自哪个租户、哪个用户、哪个 session；
- 写入来源是用户显式声明，还是模型推断；
- 如果走了降级，系统有没有显式标记 `fallback_mode`。

### 2.2 高价值 E2E 场景：用户偏好建立 → 长对话压缩 → 中断恢复 → 再次追问

建议把记忆相关验证组织成一条完整链路，而不是拆成“记住偏好”“查看历史”“恢复会话”三个孤立用例：

1. 用户首次进入系统，声明偏好：“以后默认用英文回复，但测试报告标题保留中文”；
2. Agent 确认并写入用户长期记忆；
3. 用户继续发起多轮复杂任务，触发上下文压缩；
4. 中途网络抖动或服务重启，会话需要恢复；
5. 用户再次追问：“继续刚才的报告，并沿用我的默认语言偏好”；
6. 系统应同时满足：恢复上一个任务状态、保留语言偏好、不重复执行已完成步骤；
7. 最后由用户或 API 查询验证写入的 MemoryRecord、摘要版本、恢复状态。

这类 E2E 用例的价值在于：**把“记忆正确性 + 状态恢复 + 幂等性 + 用户体验”一次性串起来。**

---

## 3. Ginkgo 实战：验证跨轮记忆、隔离与恢复幂等

### 3.1 抽象一个最小客户端接口

```go
//go:build memory_e2e

package memory_test

import (
    "context"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type AgentClient interface {
    SendMessage(ctx context.Context, tenantID, userID, sessionID, text string) (reply string, err error)
    RestartSessionWorker(ctx context.Context, tenantID, sessionID string) error
    GetMemory(ctx context.Context, tenantID, userID, sessionID string) ([]MemoryRecord, error)
    GetWorkflowState(ctx context.Context, tenantID, sessionID string) (map[string]string, error)
}
```

### 3.2 E2E 用例：偏好记忆 + 重启恢复 + 不重复执行

```go
var _ = Describe("Agent memory and recovery", Label("memory", "P0", "e2e"), func() {
    var client AgentClient

    BeforeEach(func() {
        client = NewAgentClientFromEnv()
    })

    It("should preserve user preference and resume workflow without duplicated execution", func() {
        ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
        defer cancel()

        tenantID := "tenant-a"
        userID := "qa-user-01"
        sessionID := "session-memory-e2e-001"

        By("用户先建立长期偏好")
        reply, err := client.SendMessage(ctx, tenantID, userID, sessionID,
            "以后默认用英文回复，但测试报告标题保留中文")
        Expect(err).NotTo(HaveOccurred())
        Expect(reply).To(ContainSubstring("默认"))

        By("用户发起一个需要多步执行的任务")
        reply, err = client.SendMessage(ctx, tenantID, userID, sessionID,
            "请生成一个发布检查清单，并先整理为三段：环境检查、冒烟验证、回滚预案")
        Expect(err).NotTo(HaveOccurred())
        Expect(reply).To(ContainSubstring("环境检查"))

        By("模拟 worker 重启，验证系统可恢复")
        Expect(client.RestartSessionWorker(ctx, tenantID, sessionID)).To(Succeed())

        By("用户继续追问，系统应沿用偏好且不重复执行已完成步骤")
        reply, err = client.SendMessage(ctx, tenantID, userID, sessionID,
            "继续刚才的内容，并沿用我的默认语言偏好")
        Expect(err).NotTo(HaveOccurred())

        // ✅ 最终结果：正文可为英文，但标题仍需保留中文语义
        Expect(reply).To(ContainSubstring("发布检查清单"))

        By("回查记忆存储，确认偏好已落盘")
        records, err := client.GetMemory(ctx, tenantID, userID, sessionID)
        Expect(err).NotTo(HaveOccurred())
        Expect(records).NotTo(BeEmpty())

        var hasPreference bool
        for _, r := range records {
            if r.Category == "preference" && r.Scope == "user" {
                if r.Attributes["reply_language"] == "en" && r.Attributes["title_language"] == "zh" {
                    hasPreference = true
                }
            }
        }
        Expect(hasPreference).To(BeTrue(), "user preference memory should be persisted")

        By("回查工作流状态，确认没有重复执行")
        state, err := client.GetWorkflowState(ctx, tenantID, sessionID)
        Expect(err).NotTo(HaveOccurred())
        Expect(state["checklist_generated_count"]).To(Equal("1"))
    })
})
```

### 3.3 P0 补充用例：跨租户记忆绝不串读

```go
It("should never leak memory across tenants", func() {
    ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
    defer cancel()

    _, err := client.SendMessage(ctx, "tenant-a", "user-a", "session-a",
        "记住：我的主项目是 phoenix，默认环境是 staging")
    Expect(err).NotTo(HaveOccurred())

    reply, err := client.SendMessage(ctx, "tenant-b", "user-b", "session-b",
        "我刚才默认环境是什么？")
    Expect(err).NotTo(HaveOccurred())

    // ✅ 中间状态 / 最终验证点：不能引用 tenant-a 的任何记忆
    Expect(reply).NotTo(ContainSubstring("staging"))
    Expect(reply).NotTo(ContainSubstring("phoenix"))
})
```

这个用例看起来简单，但实际上是 memory 体系里最关键的红线。**只要出现一次跨租户串读，就足以定级为安全事故。**

---

## 4. Python / API Testing：把记忆契约与故障注入做扎实

### 4.1 记忆读写契约测试

```python
import requests

BASE_URL = "https://agent.example.com"


def test_memory_contract_round_trip():
    session_id = "api-memory-001"
    tenant_id = "tenant-a"
    user_id = "qa-user-01"

    # Step 1: 写入用户偏好
    write_resp = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "tenant_id": tenant_id,
            "user_id": user_id,
            "session_id": session_id,
            "message": "记住：我只看 markdown 格式的接口变更说明",
        },
        timeout=30,
    )
    write_resp.raise_for_status()

    # Step 2: 回查记忆
    memory_resp = requests.get(
        f"{BASE_URL}/api/memory",
        params={"tenant_id": tenant_id, "user_id": user_id, "session_id": session_id},
        timeout=30,
    )
    memory_resp.raise_for_status()
    data = memory_resp.json()

    assert "records" in data and isinstance(data["records"], list)
    assert any(r["category"] == "preference" for r in data["records"])
    assert all(r["tenant_id"] == tenant_id for r in data["records"])
    assert all(r["user_id"] == user_id for r in data["records"])
```

### 4.2 摘要压缩测试：关键约束不能被吞掉

```python
def test_summary_should_preserve_p0_constraints():
    session_id = "summary-keep-constraints-001"
    constraints = [
        "不能访问生产环境",
        "输出必须脱敏",
        "审批前不能执行删除",
    ]

    # 连续注入长对话，迫使系统生成摘要
    for idx in range(30):
        text = f"第{idx}轮讨论：请记住 {'；'.join(constraints)}，并补充一些背景说明 {idx}"
        resp = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "tenant_id": "tenant-a",
                "user_id": "qa-user-01",
                "session_id": session_id,
                "message": text,
            },
            timeout=30,
        )
        resp.raise_for_status()

    summary_resp = requests.get(
        f"{BASE_URL}/api/session/summary",
        params={"session_id": session_id},
        timeout=30,
    )
    summary_resp.raise_for_status()
    summary = summary_resp.json()["summary"]

    for item in constraints:
        assert item in summary, f"P0 constraint lost after compression: {item}"
```

### 4.3 故障注入：记忆写失败时必须显式降级

```python
def test_should_fallback_to_stateless_mode_when_memory_write_fails():
    resp = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "tenant_id": "tenant-a",
            "user_id": "qa-user-01",
            "session_id": "fallback-001",
            "message": "记住：我的默认输出语言是英文",
            "fault_injection": {"memory_write": "timeout"},
        },
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()

    # ✅ 最终验证点：不能假装写成功
    assert body["fallback_mode"] == "stateless"
    assert "memory degraded" in body["warnings"][0].lower()
```

这一点非常重要。很多系统会在 memory 写失败时默默继续返回一个“像是成功”的结果，用户下一轮追问才发现系统并没有记住。**这种静默失败，比显式失败更危险。**

---

## 5. Playwright 实战：从用户视角验证“系统真的记得刚才说了什么”

### 5.1 前端验证关注点

前端不是只测聊天气泡有没有渲染，而是要验证用户能否感知到以下事实：

- 当前回答是否引用了历史记忆；
- 当记忆系统降级或不可用时，页面是否有明确提示；
- 用户能否查看、修正、删除自己的长期偏好；
- 会话恢复后，页面是否还能正确展示任务进度与历史上下文。

### 5.2 Playwright E2E：偏好建立 + 刷新恢复 + 历史连续性

```python
from playwright.sync_api import Page, expect


def test_ui_should_restore_preference_and_progress(page: Page):
    page.goto("https://agent.example.com/chat")

    # Step 1: 建立偏好
    page.get_by_placeholder("输入你的问题").fill("记住：以后默认输出英文，但测试报告标题保留中文")
    page.get_by_role("button", name="发送").click()
    expect(page.get_by_text("已记住你的偏好")).to_be_visible(timeout=10_000)

    # Step 2: 发起任务
    page.get_by_placeholder("输入你的问题").fill("请生成一个接口回归测试清单")
    page.get_by_role("button", name="发送").click()
    expect(page.get_by_text("接口回归测试清单")).to_be_visible(timeout=20_000)

    # Step 3: 刷新页面，模拟前端中断恢复
    page.reload()
    expect(page.get_by_text("继续上次会话")).to_be_visible(timeout=10_000)

    # Step 4: 继续追问，验证偏好仍生效
    page.get_by_placeholder("输入你的问题").fill("继续补充，并沿用我的默认偏好")
    page.get_by_role("button", name="发送").click()

    # ✅ 中间验证点：页面有“引用记忆/已恢复上下文”提示
    expect(page.get_by_text("已恢复历史上下文")).to_be_visible(timeout=10_000)

    # ✅ 最终验证点：标题中文，正文可按偏好输出英文
    expect(page.get_by_text("接口回归测试清单")).to_be_visible()
```

### 5.3 UI 负向检查清单

- 删除历史会话后，页面是否仍能错误显示旧偏好；
- 切换账号或租户后，浏览器本地缓存是否导致串会话；
- “已记住你的偏好”提示是否与后端真实写入结果一致；
- summary 生成后，详情页是否仍能展示关键约束，而不是只保留模糊摘要。

---

## 6. K8s / 云原生视角：记忆层也是要做演练的基础设施

### 6.1 记忆系统的基础设施风险

一旦 Agent 引入 Redis、向量库、PostgreSQL、Kafka 等组件来承载记忆，就必须把下面这些风险纳入测试范围：

1. **单点重启后状态丢失**：session state 在 Pod 重建后是否还能恢复；
2. **主从切换延迟**：写入刚成功，读取却因为副本延迟看不到；
3. **缓存与持久层不一致**：用户删除了偏好，但缓存仍返回旧值；
4. **多副本并发写冲突**：同一 session 在两个 worker 上同时更新版本号；
5. **TTL / GC 异常**：该清理的没清理，不该清理的被提前删除。

### 6.2 示例：用 K8s Job 做记忆恢复演练

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: agent-memory-recovery-drill
  namespace: ai-agent
spec:
  template:
    spec:
      containers:
        - name: runner
          image: your-registry/agent-memory-tester:latest
          env:
            - name: TARGET_BASE_URL
              value: "https://agent.example.com"
            - name: TARGET_NAMESPACE
              value: "ai-agent"
      restartPolicy: Never
  backoffLimit: 0
```

Job 内部可以执行这样一类流程：

1. 先写入一条长期偏好；
2. 发起一个会生成 workflow state 的长任务；
3. 主动重启对应 deployment 或杀掉会话 worker；
4. 重新调用恢复接口或继续对话；
5. 验证 memory record 仍存在、workflow state 未重复推进、版本号符合预期。

### 6.3 幂等恢复是 memory 场景里的高频故障点

如果恢复逻辑没有显式 checkpoint，系统就可能在重放时重复执行：

- 再次发送审批申请；
- 再次创建测试环境；
- 再次写入同一条摘要；
- 再次触发高成本模型调用。

所以恢复测试一定要补充以下断言：

- 是否存在全局 `operation_id` / `checkpoint_id`；
- 恢复前后副作用次数是否保持为 1；
- 如果已完成步骤被识别为 completed，系统是否能跳过而不是重跑。

---

## 7. 测试设计建议：如何把记忆能力纳入日常回归

### 7.1 按风险分层

- **P0**：跨租户串读、用户显式偏好丢失、恢复后重复执行副作用、删除后仍可读；
- **P1**：摘要压缩丢关键约束、记忆读写延迟过高、前端恢复提示缺失；
- **P2**：非关键记忆排序波动、历史展示样式问题、轻微的摘要措辞变化。

### 7.2 推荐回归套件结构

1. **Contract 层**：MemoryRecord / RecallResult schema 与字段约束；
2. **Service 层**：读写接口、TTL、版本冲突、幂等 key；
3. **E2E 层**：偏好建立、摘要生成、会话恢复、继续追问；
4. **Chaos / Recovery 层**：记忆存储超时、Pod 重启、缓存失效、主从切换；
5. **Online Patrol 层**：抽样验证近 24 小时内的 fallback_mode、重复恢复次数、leakage 告警。

### 7.3 对研发的左移建议

如果希望后续测试稳定可回归，建议在研发阶段就补齐以下可测试性设计：

- 给每条记忆分配可追踪的 `memory_id / version`；
- 对摘要压缩保留 `source_range` 或 `constraint_tags`；
- 对恢复逻辑引入 checkpoint 与幂等键；
- 在 API 响应里显式返回 `fallback_mode` 与 warning，而不是靠日志侧推断。

---

## 8. 课后思考题

1. 你当前负责的 Agent 系统里，哪些信息应该被定义为“长期记忆”，哪些只能是“短期上下文”？边界是否清晰？
2. 如果系统为了节省 token 对长对话做摘要压缩，你会如何定义“关键约束不能丢”的自动化判定标准？
3. 在多副本部署下，如何验证同一 session 不会被两个 worker 并发推进到不同状态？
4. 如果用户要求“忘记我刚才说过的内容”，你会如何同时验证数据库、缓存、向量索引和前端历史展示都被正确清理？

---

## 9. 今日小结

- Agent 一旦进入 stateful 阶段，测试重点就会从单轮正确率扩展到 **跨轮连续性、隔离性、恢复性与幂等性**；
- 记忆能力至少要拆成 **session context、summary、long-term memory、workflow state** 四层来设计测试；
- Ginkgo 适合覆盖“用户建偏好 → 执行任务 → 服务重启 → 继续追问”的全链路 E2E；
- Python/API 测试适合固化记忆 schema、摘要保真和降级语义；
- Playwright 负责验证用户是否真的感知到“系统记得/系统忘了/系统降级了”；
- K8s 层面的恢复演练和并发写冲突验证，是很多 Agent 产品从 demo 迈向生产时最容易漏掉的一环；
- 对 QA 来说，记忆不是一个“效果增强模块”，而是带有数据一致性、安全隔离和恢复幂等要求的正式系统能力。
