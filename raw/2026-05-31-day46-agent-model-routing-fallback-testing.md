---
title: "每日 AI 学习笔记｜Day 46：AI Agent 模型路由与降级回退测试"
date: 2026-05-31
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, routing, fallback, reliability, Ginkgo, Playwright, Kubernetes, API-Testing]
---
# 每日 AI 学习笔记｜Day 46：AI Agent 模型路由与降级回退测试

<callout icon="star" bgc="4">

**核心总结：** AI Agent 进入生产后，最常见的线上事故往往不是“模型完全不可用”，而是 **模型路由选错、回退不及时、降级不透明**：本该走高质量模型的高风险请求被打到轻量模型，导致答案失真；主模型超时后没有及时 fallback，造成整条链路雪崩；系统虽然触发了降级，但前端和日志都没有把真实决策暴露出来，结果排障困难、用户体验也失控。测试侧要把 **路由规则正确性、fallback 成功率、降级透明度、熔断隔离能力、成本与时延平衡** 一起纳入 E2E 质量基线。落地上建议采用 **Ginkgo 后端编排链路验证 + Python/API 路由契约测试 + Playwright 前端降级告知验证 + K8s 配置灰度与熔断演练** 的组合方案。核心原则：**不仅要验证“有没有答案”，更要验证“系统为什么选这个模型、失败后如何退、退完后用户是否可感知且可追溯”。**

</callout>

在单模型时代，测试重点更多放在正确率、延迟和稳定性；而进入多模型与多供应商并存的 Agent 时代，系统质量的关键节点已经前移到“路由决策层”。一次用户请求到来后，系统要先判断这是普通问答、工具规划、长文本总结，还是高风险代码生成，再决定走高质量模型、低成本模型、推理模型，还是直接进入缓存/规则兜底。一旦这个决策层不稳定，后续工具调用、上下文构造、前端展示、审计追踪都会一起失真。因此，模型路由测试不是附属优化项，而是 AI Agent 生产可用性的核心门禁。

{/* truncate */}

## 1. 核心理论：为什么“模型路由”会成为新的质量分水岭

### 1.1 多模型架构把故障点从“单点失效”变成“决策失真”

一个成熟的 AI Agent 往往至少包含四类能力路径：

1. **高质量主模型**：负责复杂推理、工具规划、长链路决策；
2. **低成本副模型**：负责轻量问答、总结、改写和高频请求；
3. **规则或缓存兜底**：负责热点问题、固定模版、静态结果；
4. **失败回退链路**：主模型超时、限流或报错时切到备选模型或最小能力模式。

问题在于，这不再是“调用某个模型”这么简单，而是在每个请求开始前都要做一次带业务语义的调度决策。路由一旦错，系统并不一定报错，反而可能“看起来可用、实际上失真”，这是最难测、也最容易漏掉的风险。

<table header-row="true" header-col="false" col-widths="180,220,280,260">
<tr>
<td>故障类型</td>
<td>表面现象</td>
<td>真实风险</td>
<td>测试关注点</td>
</tr>
<tr>
<td>路由选错模型</td>
<td>请求成功返回，但答案质量显著下降</td>
<td>复杂任务被轻量模型处理，工具规划遗漏或推理断裂</td>
<td>高风险/高复杂度请求是否命中预期模型档位</td>
</tr>
<tr>
<td>回退不生效</td>
<td>主模型超时后整条请求失败</td>
<td>单点故障扩散成全链路不可用</td>
<td>超时、429、5xx 后是否在预算内切到备选模型</td>
</tr>
<tr>
<td>降级不透明</td>
<td>用户看到回答，但不知道能力被裁剪</td>
<td>误信结果、误触高风险动作、排障困难</td>
<td>前端、日志、审计是否明确记录 degradation reason</td>
</tr>
<tr>
<td>熔断范围过大</td>
<td>一个模型异常导致所有流量都失败</td>
<td>单 provider 故障放大为平台级事故</td>
<td>熔断是否按模型/租户/能力域隔离</td>
</tr>
<tr>
<td>成本控制失灵</td>
<td>全部请求都走高价模型</td>
<td>预算失控，回归后难以及时发现</td>
<td>路由策略是否兼顾质量、时延、预算和配额</td>
</tr>
</table>

### 1.2 路由测试要回答的 5 个核心问题

1. **这类请求为什么走这个模型**：复杂度、风险级别、上下文长度、工具需求是否真的驱动了路由决策；
2. **主模型失败后系统怎么退**：是换模型、走缓存、做摘要化降级，还是只返回错误；
3. **降级后能力边界是否清晰**：工具调用是否被禁用、输出是否打标、前端是否明确提示；
4. **不同租户和流量层是否彼此隔离**：一个租户的热点或故障不能拖垮其他租户；
5. **决策是否可复盘**：每次路由都要能回放出 strategy version、candidate list、chosen model、fallback chain、degrade reason。

### 1.3 面向 QA 的关键指标

```text
RAR (Routing Accuracy Rate)      = 命中预期模型档位的请求数 / 需要路由校验的请求总数
FSR (Fallback Success Rate)      = 主模型失败后成功回退的请求数 / 触发回退的请求总数
DTR (Degrade Transparency Rate)  = 降级后被正确告知并落审计的请求数 / 降级请求总数
CIR (Circuit Isolation Rate)     = 单模型故障未扩散到其他模型池的次数 / 单模型故障总次数
CBR (Cost Budget Respect Rate)   = 满足预算策略的请求数 / 全部请求数
```

对 AI Agent 来说，建议再补两个工程指标：

- **TPR（Tool Preservation Rate）**：降级后仍被允许的工具集合是否符合设计预期，避免“模型降级了，危险工具却还开着”；
- **RVR（Route Visibility Rate）**：日志、trace、响应 metadata 中是否完整保留 route decision 证据，便于线上排障与回放。

---

## 2. 工程实践：把“模型路由”做成一条可验证的质量链路

### 2.1 推荐的五段式验证模型

<callout icon="bulb" bgc="5">

**推荐验证顺序：**

1. **请求分级**：先判断任务复杂度、风险级别、上下文长度、是否需要工具。
2. **候选集筛选**：基于租户配额、模型可用性、区域策略、成本预算生成 candidate list。
3. **决策打分**：按质量、时延、成本、稳定性综合选择主模型。
4. **失败回退**：主模型超时/限流/5xx 时，按预设顺序切到 secondary / cached / rule-based path。
5. **结果披露**：把 chosen model、fallback chain、degrade reason 写入 metadata、日志和前端提示。

</callout>

### 2.2 一条高价值 E2E 场景如何设计

不要把“路由命中正确”“fallback 成功”“前端提示已降级”拆成三条孤立小用例。更高价值的方式，是用一条完整场景串起整个链路。例如：

1. 用户发起“请基于最近 7 天工单和监控日志，分析根因并给出修复优先级”的复杂请求；
2. 编排层识别这是 **长上下文 + 高复杂度 + 需要推理总结** 的任务；
3. 路由器优先选择高质量主模型 `gpt-premium`；
4. 主模型在 8 秒 SLA 内超时；
5. 系统自动切到 `gpt-balanced`，并关闭高成本的深度链式推理开关；
6. 响应 metadata 记录 `route_decision=degraded_fallback`、`primary_timeout=true`、`chosen_model=gpt-balanced`；
7. 前端明确展示“已切换到降级模式，结果可能更简略”；
8. 审计中心保留本次模型切换链路，支持复盘与回放。

### 2.3 场景矩阵

<table header-row="true" header-col="false" col-widths="180,220,280,280">
<tr>
<td>场景</td>
<td>典型风险</td>
<td>验证重点</td>
<td>期望结果</td>
</tr>
<tr>
<td>复杂推理请求被轻量模型处理</td>
<td>答案表面可用，但推理链断裂</td>
<td>复杂度分类、模型档位命中、质量阈值</td>
<td>复杂任务必须命中高质量模型或明确降级</td>
</tr>
<tr>
<td>主模型超时</td>
<td>整条链路直接失败</td>
<td>超时阈值、fallback 顺序、重试预算</td>
<td>在预算内切到副模型并返回可接受结果</td>
</tr>
<tr>
<td>供应商 429 / 限流</td>
<td>热点时段全站抖动</td>
<td>熔断触发、租户隔离、流量转移</td>
<td>受影响范围局部化，不拖垮其他模型池</td>
</tr>
<tr>
<td>降级后继续开放危险工具</td>
<td>能力边界与模型能力不匹配</td>
<td>工具裁剪、动作限制、UI 提示</td>
<td>降级模式下仅开放安全子集能力</td>
</tr>
<tr>
<td>成本策略失效</td>
<td>低价值请求长期占用高价模型</td>
<td>预算上限、分层配额、策略版本回归</td>
<td>路由兼顾质量与成本，不出现系统性漂移</td>
</tr>
</table>

---

## 3. Ginkgo 实战：验证主模型失败后可以稳定回退

### 3.1 一个最小可测的路由接口

```go
package routing

type RouteRequest struct {
    SessionID      string
    TenantID       string
    UserID         string
    Prompt         string
    Complexity     string
    RequiresTools  bool
    MaxLatencyMS   int
}

type RouteDecision struct {
    PrimaryModel   string
    ChosenModel    string
    FallbackChain  []string
    Degraded       bool
    DegradeReason  string
    AllowedTools   []string
    StrategyVer    string
}

type ChatResponse struct {
    Content  string
    Metadata RouteDecision
}
```

### 3.2 Ginkgo E2E：主模型超时后自动切到副模型，并限制工具能力

```go
//go:build routing_e2e

package routing_test

import (
    "context"
    "errors"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type FakeModelClient struct {
    Delay   time.Duration
    Err     error
    Content string
}

func (c *FakeModelClient) Generate(ctx context.Context, _ string) (string, error) {
    select {
    case <-time.After(c.Delay):
        if c.Err != nil {
            return "", c.Err
        }
        return c.Content, nil
    case <-ctx.Done():
        return "", ctx.Err()
    }
}

var _ = Describe("Model Routing And Fallback", Label("routing", "P0", "e2e"), func() {
    It("should fallback to balanced model when premium model times out", func() {
        premium := &FakeModelClient{
            Delay: 4 * time.Second,
            Err:   context.DeadlineExceeded,
        }
        balanced := &FakeModelClient{
            Delay:   500 * time.Millisecond,
            Content: "这是一个降级后的精简分析结果。",
        }

        router := NewRouter(RouterConfig{
            PremiumTimeout: 2 * time.Second,
            PrimaryModel:   "gpt-premium",
            Fallbacks:      []string{"gpt-balanced", "rule-based-summary"},
        }, map[string]ModelClient{
            "gpt-premium":        premium,
            "gpt-balanced":       balanced,
            "rule-based-summary": NewRuleBasedSummaryClient(),
        })

        ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
        defer cancel()

        resp, err := router.Chat(ctx, RouteRequest{
            SessionID:     "route-001",
            TenantID:      "tenant-a",
            UserID:        "qa-owner-01",
            Prompt:        "请综合最近 7 天日志和工单，分析故障根因并给出优先级。",
            Complexity:    "high",
            RequiresTools: true,
            MaxLatencyMS:  8000,
        })
        Expect(err).NotTo(HaveOccurred())

        // Step 1: 初始主模型选择正确
        Expect(resp.Metadata.PrimaryModel).To(Equal("gpt-premium"))

        // Step 2: 超时后完成 fallback
        Expect(resp.Metadata.ChosenModel).To(Equal("gpt-balanced"))
        Expect(resp.Metadata.FallbackChain).To(Equal([]string{"gpt-premium", "gpt-balanced"}))
        Expect(resp.Metadata.Degraded).To(BeTrue())
        Expect(resp.Metadata.DegradeReason).To(Equal("primary_timeout"))

        // Step 3: 降级后工具能力应收敛
        Expect(resp.Metadata.AllowedTools).NotTo(ContainElement("deep_tool_planner"))
        Expect(resp.Metadata.AllowedTools).To(ContainElement("retrieval_summary"))

        // Step 4: 用户得到的是明确可解释的结果，而不是静默失败
        Expect(resp.Content).To(ContainSubstring("降级后的精简分析结果"))
    })

    It("should isolate circuit breaker by model pool", func() {
        router := NewRouterWithCircuitIsolation()

        router.MarkFailure("tenant-a", "gpt-premium", errors.New("429 too many requests"))
        router.MarkFailure("tenant-a", "gpt-premium", errors.New("429 too many requests"))
        router.MarkFailure("tenant-a", "gpt-premium", errors.New("429 too many requests"))

        stateA := router.CircuitState("tenant-a", "gpt-premium")
        stateB := router.CircuitState("tenant-b", "gpt-premium")

        Expect(stateA).To(Equal("open"))
        Expect(stateB).To(Equal("closed"))
    })
})
```

### 3.3 Ginkgo 断言重点

- **不仅要看返回成功**，还要看 `PrimaryModel` 与 `ChosenModel` 是否符合预期；
- **不仅要看 fallback 成功**，还要验证 `DegradeReason`、`FallbackChain`、`StrategyVer` 是否完整；
- **不仅要测单次超时**，还要测连续 429、5xx、context cancel、部分流量异常；
- **不仅测结果文本**，还要确认降级后危险工具是否被裁剪；
- **不仅测模型本身**，还要测 circuit breaker 是否按租户、模型池、能力域隔离。

---

## 4. Python / API Testing：把路由策略变成可回归的契约

### 4.1 用 pytest 验证路由 metadata 契约稳定

```python
import requests


def test_route_decision_contract():
    payload = {
        "session_id": "route-contract-001",
        "tenant_id": "tenant-a",
        "user_id": "qa-owner-01",
        "message": "请总结今天的 3 条告警",
        "complexity": "low",
        "requires_tools": False,
    }

    resp = requests.post("https://agent.example.com/api/chat", json=payload, timeout=30)
    resp.raise_for_status()
    body = resp.json()

    assert "content" in body
    assert "metadata" in body

    md = body["metadata"]
    assert isinstance(md["primary_model"], str)
    assert isinstance(md["chosen_model"], str)
    assert isinstance(md["fallback_chain"], list)
    assert isinstance(md["degraded"], bool)
    assert isinstance(md["strategy_version"], str)
    assert md["route_decision"] in {"primary", "fallback", "cached", "rule_based"}
```

### 4.2 用故障注入校验 fallback 行为

```python
import requests


def test_primary_timeout_should_fallback(monkeypatch):
    payload = {
        "session_id": "route-fallback-001",
        "tenant_id": "tenant-a",
        "user_id": "qa-owner-01",
        "message": "分析最近 7 天线上慢查询并生成排查建议",
        "complexity": "high",
        "requires_tools": True,
        "fault_injection": {"primary_model": "timeout"},
    }

    resp = requests.post("https://agent.example.com/api/chat", json=payload, timeout=60)
    resp.raise_for_status()
    body = resp.json()

    assert body["metadata"]["route_decision"] == "fallback"
    assert body["metadata"]["degraded"] is True
    assert body["metadata"]["degrade_reason"] == "primary_timeout"
    assert body["metadata"]["chosen_model"] != body["metadata"]["primary_model"]
```

### 4.3 用一个轻量策略模拟器做离线回归

```python
from dataclasses import dataclass


@dataclass
class RequestProfile:
    complexity: str
    requires_tools: bool
    token_estimate: int
    risk_level: str


@dataclass
class RuntimeState:
    premium_available: bool
    premium_error_rate: float
    budget_remaining: float


def choose_model(req: RequestProfile, state: RuntimeState) -> str:
    if not state.premium_available or state.premium_error_rate > 0.2:
        return "balanced"
    if req.risk_level == "high" or req.requires_tools or req.complexity == "high":
        return "premium"
    if req.token_estimate < 1500 and state.budget_remaining < 50:
        return "mini"
    return "balanced"


def test_routing_policy():
    req = RequestProfile(complexity="high", requires_tools=True, token_estimate=5000, risk_level="high")
    state = RuntimeState(premium_available=True, premium_error_rate=0.01, budget_remaining=100)
    assert choose_model(req, state) == "premium"

    broken_state = RuntimeState(premium_available=False, premium_error_rate=0.5, budget_remaining=100)
    assert choose_model(req, broken_state) == "balanced"
```

这类离线模拟器非常适合接到：

1. 路由策略 PR 的快速回归；
2. 模型注册表变更检查；
3. 成本阈值和配额调整评审；
4. 线上事故复盘后的 replay 回放。

---

## 5. Playwright 实战：验证用户能否感知降级与能力裁剪

### 5.1 前端不是旁观者，而是“降级透明度”的最后一道门

很多系统在后端完成了 fallback，却没有把这个事实告诉用户。结果就是：用户以为自己拿到的是标准能力，实际上系统已经关闭了高级推理、文件导出或部分工具调用。对 AI Agent 来说，这会直接破坏信任。

前端至少要承担三件事：

1. **明确告知**：告诉用户本次回答是否处于降级模式；
2. **限制操作**：降级后不应继续展示不再可用的能力按钮；
3. **支持复盘**：在高级详情或调试视图中展示当前模型、fallback 信息和 trace id。

### 5.2 Playwright E2E：主模型故障后页面必须展示降级提示，并隐藏高风险动作

```python
from playwright.sync_api import Page, expect


def test_ui_should_show_fallback_banner(page: Page):
    page.goto("https://agent.example.com/console?fault=primary_timeout")

    page.get_by_placeholder("请输入你的问题").fill(
        "请分析最近 7 天线上错误趋势并给出修复优先级"
    )
    page.get_by_role("button", name="发送").click()

    # Step 1: 明确展示本次已发生降级
    expect(page.get_by_text("当前已切换为降级模式")).to_be_visible(timeout=10_000)
    expect(page.get_by_text("主模型超时，已切换至备选模型")).to_be_visible(timeout=10_000)

    # Step 2: 页面仍应给出可用结果
    expect(page.get_by_test_id("assistant-answer")).to_contain_text("修复优先级")

    # Step 3: 降级模式下高成本功能不应再可用
    deep_think = page.get_by_role("button", name="深度推理")
    expect(deep_think).to_be_disabled(timeout=10_000)

    export_report = page.get_by_role("button", name="导出完整报告")
    expect(export_report).to_be_hidden(timeout=10_000)

    # Step 4: 调试信息可见，方便排障
    page.get_by_role("button", name="查看执行详情").click()
    expect(page.get_by_text("chosen_model: gpt-balanced")).to_be_visible(timeout=10_000)
    expect(page.get_by_text("degrade_reason: primary_timeout")).to_be_visible(timeout=10_000)
```

### 5.3 前端检查清单

- 是否区分 **正常模式 / 降级模式 / 熔断模式**；
- 是否在降级后隐藏不再可用的高成本或高风险动作；
- 是否避免把“回答变短了”误当成正常现象而不告知用户；
- 是否能在刷新、重连、会话恢复后保持一致的降级状态；
- 是否给到 trace id、route decision 等最小排障信息。

---

## 6. K8s 与发布治理：把模型路由配置当成“可灰度、可回滚”的生产资产

### 6.1 很多 routing 事故，本质上是配置事故

线上真实问题经常不是代码写错，而是：

- ConfigMap 中把高复杂度阈值改低，导致大量请求错进轻量模型；
- 新 provider 上线后没有做灰度，直接把 100% 流量打进去；
- 熔断阈值过于激进，某个区域轻微抖动就把整个模型池切掉；
- 预算配置和路由规则不同步，结果高价模型异常放量。

所以，模型路由配置本身也必须被纳入发布门禁和回归体系。

### 6.2 示例：把路由策略做成可灰度的 ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-routing-policy
  namespace: ai-agent

data:
  routing.yaml: |
    strategy_version: v2026-05-31
    rules:
      - name: high-complexity-primary
        when:
          complexity: high
          requires_tools: true
        primary_model: gpt-premium
        fallbacks:
          - gpt-balanced
          - rule-based-summary
        timeout_ms: 2000
      - name: low-cost-summary
        when:
          complexity: low
          token_estimate_lt: 1500
        primary_model: gpt-mini
        fallbacks:
          - gpt-balanced
    circuit_breaker:
      failure_rate_threshold: 0.2
      consecutive_failures: 3
      half_open_after_seconds: 30
```

### 6.3 发布门禁建议

<table header-row="true" header-col="false" col-widths="180,220,280,280">
<tr>
<td>阶段</td>
<td>建议动作</td>
<td>核心校验</td>
<td>失败即阻断条件</td>
</tr>
<tr>
<td>PR 阶段</td>
<td>离线策略模拟 + 契约测试</td>
<td>路由规则是否命中预期样本</td>
<td>复杂请求误路由到低档模型</td>
</tr>
<tr>
<td>预发阶段</td>
<td>Ginkgo E2E + 故障注入</td>
<td>超时/429/5xx 后 fallback 是否生效</td>
<td>回退失败或降级后工具未收敛</td>
</tr>
<tr>
<td>灰度阶段</td>
<td>按租户/流量比例灰度</td>
<td>错误率、时延、成本、route mix 变化</td>
<td>错误率或成本突增超阈值</td>
</tr>
<tr>
<td>全量阶段</td>
<td>持续巡检 + trace 抽样回放</td>
<td>route decision 可见性与故障隔离效果</td>
<td>route metadata 丢失或熔断扩散</td>
</tr>
</table>

---

## 7. 课后思考题

1. 如果一个请求同时满足“高复杂度”和“低预算”两个条件，你会如何定义路由优先级？是优先质量、优先成本，还是按租户 SLA 分层？
2. 主模型 fallback 到副模型后，哪些工具应继续开放，哪些必须被关闭？你的判断依据是什么？
3. 如果路由策略升级后线上错误率没升，但成本翻倍，你会把它定义为质量回归吗？为什么？
4. 你们当前系统是否能在一次 trace 中完整看到 `candidate models → chosen model → fallback chain → degrade reason`？如果不能，排障成本会落在哪一步？
5. 若某个 provider 在某一地域持续抖动，你会按地域隔离、按租户隔离，还是按能力域隔离熔断？为什么？

---

## 8. 今日小结

今天这篇的核心，不是教系统“多接几个模型”就结束，而是把 **模型选择、失败回退、能力降级、用户告知、生产治理** 看作一条完整的质量链路。对于测试开发来说，真正要守住的是三条线：

1. **路由正确**：复杂任务、高风险任务、长上下文任务不能被错误地下放到低能力模型；
2. **失败可退**：主模型超时、限流、5xx 后系统要在预算内稳定 fallback，而不是直接雪崩；
3. **降级可见**：系统降级后，用户、前端、日志、审计都要知道发生了什么，能力边界要清晰。

把这三条线做成自动化之后，模型路由才不再是一个“线上玄学参数”，而会变成一套可验证、可灰度、可回滚、可复盘的工程能力。