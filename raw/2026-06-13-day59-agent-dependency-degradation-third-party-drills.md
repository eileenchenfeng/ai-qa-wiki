---
title: "每日 AI 学习笔记｜Day 59：AI Agent 外部依赖降级与第三方故障演练"
date: 2026-06-13
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, resilience, dependency-failure, degradation, Ginkgo, Playwright, Kubernetes, API-Testing]
---

# 每日 AI 学习笔记｜Day 59：AI Agent 外部依赖降级与第三方故障演练

<callout icon="star" bgc="4">
**核心总结：** AI Agent 真正难测的地方，往往不在主流程本身，而在它高度依赖外部世界：模型网关、向量检索、工作流引擎、审批系统、对象存储、Webhook、搜索服务，任何一个依赖抖动、限流、慢响应、半失败，都会沿着编排链路被放大成“回答慢”“工具失效”“页面一直转圈”“重复执行副作用”等用户可感知事故。对资深测试开发来说，质量目标不能停留在“依赖挂了系统也报错”，而要验证 **系统是否识别了故障、是否按预期降级、是否避免副作用扩散、是否向用户诚实暴露当前能力边界**：用 **Ginkgo** 断言后端编排在第三方超时/429/5xx 下的降级路径与幂等行为，用 **Python / API Testing** 做依赖契约探测和熔断状态校验，用 **Playwright** 验证页面在降级模式下的提示、按钮可见性和结果一致性，用 **Kubernetes** 注入故障并定时演练恢复。稳定的 AI 质量体系，不是依赖永远不出错，而是依赖出错时系统仍能回答：**现在降到了哪一层、哪些能力已关闭、用户还能安全完成什么。**
</callout>

AI Agent 与传统后端系统相比，更像一个“依赖编排器”。一次用户请求，可能要同时经过模型推理、知识检索、工具调用、异步任务、权限校验和前端状态刷新。也正因为如此，线上最常见的问题并不是单点 crash，而是 **依赖部分可用、部分超时、部分返回脏数据** 的灰色故障。

因此，今天这篇学习笔记聚焦一个非常实战的话题：**如何为 AI Agent 设计外部依赖降级与第三方故障演练体系**，让系统在依赖出问题时，不只是“别挂掉”，而是能稳定降级、正确止损、可观测、可回归。

{/* truncate */}

## 0. 今日核心要点

1. **AI Agent 的大多数严重事故，本质都是依赖故障被编排层放大。**
2. **降级不是简单兜底文案，而是要明确能力边界、状态迁移和副作用控制。**
3. **429、超时、半成功、脏数据、回调丢失** 都必须分别建模，不能统称“第三方失败”。
4. **最有价值的 E2E 用例，是验证“依赖失败后系统仍然安全且可解释”**。
5. **前端必须同步感知后端降级状态**，否则就会出现“后台已降级，页面还在假装正常”的体验事故。
6. **故障演练的目标不是证明系统会失败，而是证明失败被收敛在可接受爆炸半径内。**

---

## 1. 核心理论：为什么 AI Agent 比传统服务更怕第三方依赖故障

### 1.1 AI Agent 天生是“多依赖编排型系统”

对普通 CRUD 服务来说，一次请求通常依赖数据库和少量内部服务；但 AI Agent 一次任务常常同时依赖：

- 模型推理网关
- 检索 / RAG 服务
- 工具平台或工作流系统
- 审批 / 工单 / IM 等办公系统
- 对象存储、文件服务、向量索引
- 回调、消息队列和异步任务状态机

这意味着同一个用户请求里，**成功路径很长，失败路径更多**。任何一个环节轻微抖动，都可能被上层误解为“模型不稳定”或“产品偶发抽风”。

### 1.2 依赖故障最危险的不是“报错”，而是“半对半错”

真正难处理的依赖问题，往往不是彻底不可用，而是下面这些灰度状态：

<table header-row="true" col-widths="140,180,220,220">
  <tr>
    <td>故障类型</td>
    <td>典型表现</td>
    <td>用户侧风险</td>
    <td>测试关注点</td>
  </tr>
  <tr>
    <td>超时</td>
    <td>第三方长时间无响应</td>
    <td>页面一直 loading、任务误重试</td>
    <td>超时阈值、取消传播、兜底路径</td>
  </tr>
  <tr>
    <td>429 / 限流</td>
    <td>依赖因流量突增拒绝服务</td>
    <td>核心功能集体失败、雪崩重试</td>
    <td>退避重试、熔断阈值、优先级保护</td>
  </tr>
  <tr>
    <td>5xx / 显式失败</td>
    <td>第三方直接报错</td>
    <td>任务中断、错误提示不清</td>
    <td>错误映射、降级能力关闭</td>
  </tr>
  <tr>
    <td>半成功</td>
    <td>工单创建成功但回包失败</td>
    <td>重复执行、副作用放大</td>
    <td>幂等键、状态回查、补偿逻辑</td>
  </tr>
  <tr>
    <td>脏数据</td>
    <td>检索召回错数据、Schema 不兼容</td>
    <td>模型规划偏航、答案误导</td>
    <td>契约校验、结果可信度断言</td>
  </tr>
</table>

### 1.3 降级体系的目标不是“尽量成功”，而是“安全且可解释”

依赖出问题时，系统不一定非要返回完整结果，但至少应做到：

1. **知道自己失败在哪一层**；
2. **明确关闭哪些高风险能力**；
3. **避免重复副作用**；
4. **把降级状态透明告诉用户**；
5. **留下可回放的证据链路**。

<callout icon="bulb" bgc="3">
**工程建议：** 如果系统在依赖失败后虽然“还能返回一句话”，但没有暴露降级事实、没有收敛副作用、没有保留根因证据，这不算高可用，只能算“把风险藏起来了”。
</callout>

---

## 2. 方法框架：建立依赖故障到降级策略的映射表

### 2.1 先做依赖分级，而不是统一 try-catch

建议把依赖按业务价值与副作用风险分成三层：

1. **关键强依赖**：失败后主任务不能继续，例如审批提交、生产变更执行；
2. **可降级依赖**：失败后可退化为简化模式，例如检索服务、推荐服务；
3. **增强型依赖**：失败后只影响体验，不影响任务主闭环，例如富文本格式化、次要提示信息。

### 2.2 每类依赖都要绑定预期降级动作

<table header-row="true" col-widths="170,220,240,170">
  <tr>
    <td>依赖类型</td>
    <td>失败后系统动作</td>
    <td>用户可见结果</td>
    <td>建议优先级</td>
  </tr>
  <tr>
    <td>审批 / 工单系统</td>
    <td>停止执行高风险动作，转为草稿或待人工确认</td>
    <td>明确提示“已生成草稿，待人工补提”</td>
    <td>P0</td>
  </tr>
  <tr>
    <td>检索 / 知识库</td>
    <td>降为无检索回答或仅使用缓存摘要</td>
    <td>提示“当前参考资料不完整，请谨慎复核”</td>
    <td>P0/P1</td>
  </tr>
  <tr>
    <td>通知 / Webhook</td>
    <td>主任务继续，通知异步补偿</td>
    <td>任务完成但显示“通知稍后重试”</td>
    <td>P1</td>
  </tr>
  <tr>
    <td>文件 / 对象存储</td>
    <td>切换本地临时输出或只返回文本摘要</td>
    <td>提示附件未生成，结果正文可先使用</td>
    <td>P1</td>
  </tr>
  <tr>
    <td>观测 / 埋点系统</td>
    <td>主流程继续，但打标 trace incomplete</td>
    <td>用户无感，但运维有告警</td>
    <td>P2</td>
  </tr>
</table>

### 2.3 推荐采用“四问法”评估降级设计是否合格

面对任一第三方依赖，测试设计前先回答：

1. **它挂了以后，系统应该继续还是停止？**
2. **如果继续，哪些能力必须关闭？**
3. **如果停止，能否保存已完成的中间产物？**
4. **用户是否能一眼看懂当前处于降级模式？**

这四个问题回答不清，后续 E2E 用例通常也会失焦。

---

## 3. Ginkgo 实战：把第三方失败路径沉淀成 E2E 断言

### 3.1 先定义依赖故障注入与运行结果结构

```go
//go:build dependencyresilience

package dependencyresilience_test

type FaultSpec struct {
    Dependency string `json:"dependency"`
    Mode       string `json:"mode"`       // timeout, rate_limit, error, partial_success
    StatusCode int    `json:"status_code"`
    DelayMS    int    `json:"delay_ms"`
}

type RunResult struct {
    FinalStatus      string   `json:"final_status"`
    Degraded         bool     `json:"degraded"`
    DegradeReason    string   `json:"degrade_reason"`
    ToolCalls        []string `json:"tool_calls"`
    SideEffects      []string `json:"side_effects"`
    UserVisibleHints []string `json:"user_visible_hints"`
}
```

这个结构的价值在于：它把“依赖挂了以后发生了什么”从模糊日志，收束成 **可断言的运行态事实**。

### 3.2 E2E：审批系统超时时必须降级为草稿，不允许重复提交

```go
package dependencyresilience_test

import (
    "context"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type AgentRunner interface {
    Run(ctx context.Context, input string, fault FaultSpec) (*RunResult, error)
}

var _ = Describe("Dependency degradation", Label("P0", "e2e", "resilience"), func() {
    var runner AgentRunner

    BeforeEach(func() {
        runner = NewAgentRunnerFromEnv()
    })

    It("should fallback to draft mode when approval service times out", func() {
        ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
        defer cancel()

        result, err := runner.Run(ctx,
            "请生成今晚发布审批并自动提交",
            FaultSpec{Dependency: "approval-service", Mode: "timeout", DelayMS: 25000},
        )
        Expect(err).NotTo(HaveOccurred())
        Expect(result.FinalStatus).To(Equal("completed_with_degradation"))
        Expect(result.Degraded).To(BeTrue())
        Expect(result.DegradeReason).To(Equal("approval-service-timeout"))
        Expect(result.ToolCalls).To(Equal([]string{"create_release_draft"}))
        Expect(result.SideEffects).NotTo(ContainElement("submit_release_approval"))
        Expect(result.UserVisibleHints).To(ContainElement("审批服务超时，已为你保留草稿，请稍后手动提交"))
    })
})
```

这条用例的重点不是“超时后有报错”，而是验证：**高风险动作被及时刹车，且不会因为重试导致重复副作用**。

### 3.3 E2E：知识库限流后可降级回答，但必须显式标注可信度下降

```go
It("should answer with degraded knowledge mode when retrieval is rate limited", func() {
    ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
    defer cancel()

    result, err := runner.Run(ctx,
        "总结本周发布风险并给出回滚建议",
        FaultSpec{Dependency: "retrieval-service", Mode: "rate_limit", StatusCode: 429},
    )
    Expect(err).NotTo(HaveOccurred())
    Expect(result.FinalStatus).To(Equal("completed_with_degradation"))
    Expect(result.Degraded).To(BeTrue())
    Expect(result.DegradeReason).To(Equal("retrieval-rate-limited"))
    Expect(result.ToolCalls).To(Equal([]string{"load_cached_release_summary"}))
    Expect(result.UserVisibleHints).To(ContainElement("当前参考资料不完整，以下建议基于缓存摘要生成，请复核关键结论"))
})
```

这类用例覆盖的是典型的 **“可回答，但不应假装完整正确”** 场景。

### 3.4 E2E：第三方半成功时必须通过幂等键收敛副作用

```go
It("should deduplicate side effects when ticket service returns partial success", func() {
    ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
    defer cancel()

    result, err := runner.Run(ctx,
        "创建发布单并同步到群公告",
        FaultSpec{Dependency: "ticket-service", Mode: "partial_success", StatusCode: 502},
    )
    Expect(err).NotTo(HaveOccurred())
    Expect(result.SideEffects).To(HaveLen(1))
    Expect(result.SideEffects[0]).To(MatchRegexp(`ticket:[a-zA-Z0-9_-]+`))
    Expect(result.ToolCalls).NotTo(ContainElement("create_ticket_again"))
})
```

半成功场景最容易在真实生产里酿成事故，因为**系统以为失败了，第三方其实已经执行了一半**。

---

## 4. Python / API Testing：做依赖契约探测、熔断状态校验与回归分级

### 4.1 用脚本拉取依赖健康状态并判断是否进入降级模式

```python
from __future__ import annotations

from dataclasses import dataclass
import requests


@dataclass
class DependencyHealth:
    name: str
    status: str
    latency_ms: int
    circuit_state: str


def fetch_dependency_health(base_url: str) -> list[DependencyHealth]:
    resp = requests.get(f"{base_url}/api/dependency-health", timeout=10)
    resp.raise_for_status()
    body = resp.json()
    result: list[DependencyHealth] = []
    for item in body["items"]:
        result.append(DependencyHealth(
            name=item["name"],
            status=item["status"],
            latency_ms=item["latency_ms"],
            circuit_state=item["circuit_state"],
        ))
    return result


def degraded_dependencies(items: list[DependencyHealth]) -> list[str]:
    return [item.name for item in items if item.status != "ok" or item.circuit_state != "closed"]
```

### 4.2 依赖熔断打开后，发布门禁应自动阻断高风险任务

```python
def should_block_high_risk_release(items: list[DependencyHealth]) -> bool:
    critical = {"approval-service", "ticket-service"}
    for item in items:
        if item.name in critical and item.circuit_state == "open":
            return True
    return False


if __name__ == "__main__":
    items = fetch_dependency_health("https://agent.example.com")
    bad = degraded_dependencies(items)
    print("degraded:", bad)
    if should_block_high_risk_release(items):
        raise SystemExit("blocking release because critical dependency circuit is open")
```

这段脚本的核心意义是：把“依赖状态不太好”变成 **可用于发布门禁的自动判定信号**。

### 4.3 Contract 校验：降级接口必须返回标准能力说明

```python
import requests


def test_degradation_response_should_expose_mode_and_user_hint():
    resp = requests.post(
        "https://agent.example.com/api/agent/run?inject_fault=approval_timeout",
        json={"input": "请创建今晚发布审批并自动提交"},
        timeout=20,
    )
    resp.raise_for_status()
    body = resp.json()

    assert body["status"] == "completed_with_degradation"
    assert body["degraded"] is True
    assert body["degrade_reason"] == "approval-service-timeout"
    assert "user_hint" in body
    assert "capability_scope" in body
```

如果降级后的接口返回结构不稳定，前端和自动化平台就很难统一处理，最后用户只会看到一堆不一致的错误体验。

---

## 5. Playwright 实战：确保前端对降级事实“诚实展示”

### 5.1 为什么前端验证不能缺位

依赖故障时，用户最先感知的不是 trace、熔断器和重试计数，而是：

- 页面是否还在无限 loading；
- 高风险按钮有没有被禁用；
- 系统有没有明确说明当前是降级模式；
- 已完成部分是否被保留。

因此，前端测试的重点不是“UI 漂不漂亮”，而是 **是否忠实呈现了后端的降级事实**。

### 5.2 Playwright：审批依赖故障时必须展示草稿保留态

```python
from playwright.sync_api import Page, expect


def test_approval_timeout_should_show_draft_saved_banner(page: Page):
    page.goto("https://agent.example.com/workspace/ws-release-center?inject_fault=approval_timeout")
    page.get_by_placeholder("输入任务目标").fill("请创建今晚发布审批并自动提交")
    page.get_by_role("button", name="发送").click()

    expect(page.get_by_text("审批服务超时，已自动为你保留草稿")).to_be_visible(timeout=20_000)
    expect(page.get_by_role("button", name="立即提交审批")).to_be_disabled()
    expect(page.get_by_role("button", name="复制草稿内容")).to_be_visible()
```

### 5.3 Playwright：检索降级后必须暴露“资料不完整”提示

```python
from playwright.sync_api import Page, expect


def test_retrieval_degradation_should_show_confidence_warning(page: Page):
    page.goto("https://agent.example.com/workspace/ws-risk-summary?inject_fault=retrieval_429")
    page.get_by_placeholder("输入任务目标").fill("总结本周发布风险")
    page.get_by_role("button", name="发送").click()

    expect(page.get_by_text("当前参考资料不完整")).to_be_visible(timeout=20_000)
    expect(page.get_by_text("建议复核关键结论后再执行后续动作")).to_be_visible()
    expect(page.get_by_text("已基于缓存摘要生成结果")).to_be_visible()
```

如果前端把降级模式包装成“普通成功”，那用户就会错误放大对结果的信任，这本身就是质量缺陷。

---

## 6. Kubernetes 实战：把第三方故障演练做成持续能力

### 6.1 用 Chaos / CronJob 定期演练第三方依赖超时

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: agent-dependency-drill
spec:
  schedule: "0 10 * * 2,5"
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
                  python run_dependency_drill.py \
                    --scenario=approval_timeout \
                    --target-env=staging \
                    --assert-mode=degraded-safe
              env:
                - name: BASE_URL
                  value: "https://agent.example.com"
                - name: ALERT_WEBHOOK
                  valueFrom:
                    secretKeyRef:
                      name: qa-drill-secret
                      key: webhook
```

### 6.2 故障演练推荐覆盖的 5 类场景

1. **固定超时**：验证超时阈值与取消传播；
2. **持续 429**：验证退避、熔断和核心流量保护；
3. **单次 5xx 后恢复**：验证短抖动不会触发过度降级；
4. **半成功回包丢失**：验证幂等与状态回查；
5. **返回脏数据 / 字段缺失**：验证契约守卫与安全拒绝。

### 6.3 演练结果必须沉淀成什么

一次演练结束后，至少应产出：

- **故障场景编号**：哪一个依赖、哪一种故障模式；
- **预期降级动作**：应该切到什么安全模式；
- **实际表现**：后端状态、前端提示、是否有副作用泄露；
- **回归资产**：新增或更新哪条 E2E / Contract / 巡检规则。

<callout icon="bulb" bgc="3">
**质量建议：** 故障演练如果只停留在“压一下第三方看看会不会挂”，价值很有限。更高价值的做法是把每次演练都沉淀成标准场景库，并明确它对应哪条发布门禁、哪条巡检规则、哪条 E2E 用例。
</callout>

---

## 7. 课后思考题

1. 如果审批系统不可用，但生成草稿功能可用，你会把“自动提交失败但草稿保留成功”判为通过、部分通过还是失败？依据是什么？
2. 对于检索服务限流的场景，你会接受系统继续回答吗？需要满足哪些前提条件才能放行？
3. 第三方半成功最容易引发哪些重复副作用？在你的业务里，哪一类副作用最不能接受？
4. 如果后端已经进入降级模式，但前端没有展示任何提示，你会把问题优先归类为体验缺陷、契约缺陷还是可靠性缺陷？为什么？
5. 你的团队目前最缺的依赖韧性资产是什么：故障场景库、熔断状态观测、幂等校验、还是用户降级提示规范？如果只能先补一个，你会选哪个？

---

## 8. 今日小结

今天我们把视角从“系统本身是否稳定”进一步推进到 **系统依赖外部世界时是否稳定**。对 AI Agent 而言，很多真实事故并不是主代码逻辑直接写错，而是外部依赖出现超时、限流、半成功或脏数据后，编排层没有正确止损，最终把局部故障放大成用户事故。

因此，外部依赖降级与第三方故障演练的本质，不是做一堆“错误返回码测试”，而是建立一套完整的质量闭环：**先识别依赖的重要性，再为不同故障模式定义明确降级策略，最后用 Ginkgo、Python、Playwright 和 Kubernetes 把这些策略固化成可持续执行的自动化资产。** 当系统能在依赖异常时清楚地回答“哪里坏了、降到了什么模式、哪些动作不会再执行、用户现在还能安全做什么”时，这套 AI 质量体系才算真正成熟。
