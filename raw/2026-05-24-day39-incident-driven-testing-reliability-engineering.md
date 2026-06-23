---
title: "每日 AI 学习笔记｜Day 39：AI Agent 事件驱动测试与可靠性工程"
date: 2026-05-24
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, incident-driven-testing, reliability-engineering, postmortem, Ginkgo, Playwright, K8s, SRE, chaos-engineering]
---
# 每日 AI 学习笔记｜Day 39：AI Agent 事件驱动测试与可靠性工程

每一次生产事故（Incident）都是一份珍贵的测试用例"矿藏"。本篇系统阐述如何将 Incident Postmortem 转化为自动化回归测试，构建 Incident-Driven Testing（IDT）闭环，从"被动灭火"走向"主动免疫"。结合 AI Agent 特有的不确定性挑战，建立端到端可靠性工程体系。

{/* truncate */}

## 0. 核心总结

<callout icon="star" bgc="4">

**本篇核心要点：**

1. **Incident-Driven Testing（IDT）核心理念**：每个 P0/P1 事故必须在 48h 内产出至少一条自动化回归用例，确保"同类故障不二犯"。IDT 是将 Postmortem 的 Action Item 落地为可执行测试代码的工程化方法。
2. **AI Agent 事故特殊性**：相比传统服务，Agent 事故根因更多元——模型退化、Prompt 漂移、工具链断裂、记忆污染、多 Agent 死锁。每类故障需要专门的检测与回归策略。
3. **IDT 闭环五步法**：Detect（发现）→ Classify（分类）→ Reproduce（复现）→ Codify（编码为测试）→ Prevent（纳入 CI/Gate）。每一步都有对应的工程化工具和自动化手段。
4. **故障分类 Taxonomy**：建立 Agent 故障 6 大类分类体系（Model/Prompt/Tool/Memory/Orchestration/Infra），每类对应标准化的测试模板和复现脚本，加速 IDT 落地。
5. **Reproduction-as-Code**：生产事故复现脚本化，使用 Trace Replay + Snapshot Restore 在隔离环境中精确重现故障现场，消除"无法复现"的借口。
6. **Ginkgo IDT Suite 设计**：基于 Label 标记故障类别和严重等级，使用 BeforeEach 注入故障条件，AfterEach 清理现场，确保 IDT 用例可在 CI 中稳定执行。
7. **可靠性度量 MTTD/MTTR/MTTF**：通过 IDT 覆盖率（已 Codify 的 Incident / 总 Incident）和故障复发率（同类故障再次发生占比）量化 IDT 体系有效性。
8. **Playwright Incident Replay**：将用户侧触发路径转化为 E2E 回放脚本，在前端层面验证修复有效性，确保用户体验层面的回归覆盖。

</callout>

## 1. 核心理论：为什么需要 Incident-Driven Testing

### 1.1 从灭火到免疫

传统质量保障体系以**预防**为主（设计用例 → 执行 → 发布），但 AI Agent 系统存在大量"未知的未知"：

- 模型行为随版本升级发生隐性变化（Behavioral Drift）
- Prompt 微调引发不可预见的级联效应
- 第三方工具 API 契约静默变更
- 多 Agent 协作中的竞态条件和死锁

**IDT 核心哲学**：每个生产事故都是一次"免费的探索性测试"，暴露了现有测试覆盖的盲区。将其固化为自动化用例，就是在"打疫苗"。

### 1.2 IDT 与传统回归测试的区别

<table header-row="true" header-col="false" col-widths="200,400,400">
<tr>
<td>维度</td>
<td>传统回归测试</td>
<td>Incident-Driven Testing</td>
</tr>
<tr>
<td>用例来源</td>
<td>需求文档 / 测试设计</td>
<td>生产事故 Postmortem</td>
</tr>
<tr>
<td>覆盖盲区</td>
<td>已知功能路径</td>
<td>未知的边界条件和异常组合</td>
</tr>
<tr>
<td>优先级</td>
<td>按功能模块均匀分配</td>
<td>按故障影响面和复发概率排序</td>
</tr>
<tr>
<td>时效性</td>
<td>跟随迭代节奏</td>
<td>48h 内必须产出</td>
</tr>
<tr>
<td>验证目标</td>
<td>功能正确性</td>
<td>故障不复发 + 修复有效性</td>
</tr>
</table>

### 1.3 AI Agent 故障 Taxonomy

<callout icon="bulb" bgc="5">

**六大故障类别（MPTMOI Taxonomy）：**

- **M - Model（模型层）**：输出退化、幻觉增加、拒绝率异常、延迟飙升
- **P - Prompt（提示层）**：注入攻击、模板变量逃逸、System Prompt 泄露
- **T - Tool（工具层）**：调用失败、参数构造错误、超时、返回格式变更
- **M - Memory（记忆层）**：上下文污染、会话隔离失效、向量库数据腐化
- **O - Orchestration（编排层）**：路由错误、死循环、Agent 间通信失败
- **I - Infra（基础设施层）**：K8s Pod OOM、网络分区、数据库连接池耗尽

</callout>

## 2. 工程实践：IDT 闭环五步法

### 2.1 Step 1 - Detect（发现）

```
┌─────────────────────────────────────────────────┐
│         Incident Detection Sources              │
├─────────────────────────────────────────────────┤
│  ┌──────────┐  ┌───────────┐  ┌─────────────┐  │
│  │ SLO Alert│  │User Report│  │Synthetic    │  │
│  │ (P99>3s) │  │(Feedback) │  │Probe Fail   │  │
│  └────┬─────┘  └─────┬─────┘  └──────┬──────┘  │
│       └───────────────┴───────────────┘         │
│                       │                         │
│              ┌────────▼────────┐                │
│              │ Incident Created │                │
│              │  (Auto/Manual)   │                │
│              └─────────────────┘                │
└─────────────────────────────────────────────────┘
```

### 2.2 Step 2 - Classify（分类）

使用 MPTMOI 分类法标记故障根因：

```go
// incident_classifier.go - 自动分类器
package idt

type IncidentCategory string

const (
    CategoryModel         IncidentCategory = "MODEL"
    CategoryPrompt        IncidentCategory = "PROMPT"
    CategoryTool          IncidentCategory = "TOOL"
    CategoryMemory        IncidentCategory = "MEMORY"
    CategoryOrchestration IncidentCategory = "ORCHESTRATION"
    CategoryInfra         IncidentCategory = "INFRA"
)

type IncidentRecord struct {
    ID          string
    Category    IncidentCategory
    Severity    string // P0, P1, P2
    RootCause   string
    TraceID     string
    Timestamp   int64
    Reproduced  bool
    TestCaseID  string // 关联的回归用例 ID
}

type Classifier struct {
    rules []ClassifyRule
}

type ClassifyRule struct {
    Pattern  string
    Category IncidentCategory
}

func NewClassifier() *Classifier {
    return &Classifier{
        rules: []ClassifyRule{
            {Pattern: "timeout.*model", Category: CategoryModel},
            {Pattern: "hallucination|factual_error", Category: CategoryModel},
            {Pattern: "prompt.*injection|jailbreak", Category: CategoryPrompt},
            {Pattern: "tool.*failed|api.*error", Category: CategoryTool},
            {Pattern: "context.*corrupt|session.*leak", Category: CategoryMemory},
            {Pattern: "routing.*error|deadlock|infinite_loop", Category: CategoryOrchestration},
            {Pattern: "oom|connection.*pool|network.*partition", Category: CategoryInfra},
        },
    }
}
```

### 2.3 Step 3 - Reproduce（复现）

**Reproduction-as-Code**：将生产事故场景转化为可执行的复现脚本。

```go
// reproduction_test.go - Trace Replay 复现框架
package idt_test

import (
    "context"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type TraceEvent struct {
    Timestamp   time.Time         `json:"timestamp"`
    SpanName    string            `json:"span_name"`
    Request     json.RawMessage   `json:"request"`
    Response    json.RawMessage   `json:"response"`
    StatusCode  int               `json:"status_code"`
    Duration    time.Duration     `json:"duration"`
}

type IncidentSnapshot struct {
    IncidentID  string       `json:"incident_id"`
    TraceEvents []TraceEvent `json:"trace_events"`
    EnvState    map[string]string `json:"env_state"`
}

func LoadSnapshot(path string) (*IncidentSnapshot, error) {
    // 从文件加载事故快照（脱敏后的 Trace 数据）
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var snap IncidentSnapshot
    return &snap, json.Unmarshal(data, &snap)
}

var _ = Describe("Incident Reproduction Suite", Label("idt", "reproduction"), func() {
    var (
        snapshot *IncidentSnapshot
        mockServer *httptest.Server
    )

    BeforeEach(func() {
        var err error
        snapshot, err = LoadSnapshot("testdata/incidents/INC-2024-0531.json")
        Expect(err).NotTo(HaveOccurred())

        // 基于 Trace 构建 Mock Server，精确重放外部依赖的响应
        mockServer = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            for _, event := range snapshot.TraceEvents {
                if r.URL.Path == extractPath(event.SpanName) {
                    w.WriteHeader(event.StatusCode)
                    w.Write(event.Response)
                    return
                }
            }
            w.WriteHeader(http.StatusNotFound)
        }))
    })

    AfterEach(func() {
        mockServer.Close()
    })

    It("should reproduce INC-2024-0531: Tool timeout causing infinite retry loop", func() {
        ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
        defer cancel()

        agent := NewAgentWithConfig(AgentConfig{
            ToolEndpoint: mockServer.URL,
            MaxRetries:   10, // 事故时的配置
            RetryBackoff: 100 * time.Millisecond,
        })

        result, err := agent.Execute(ctx, snapshot.TraceEvents[0].Request)

        // 验证：修复前会无限重试直到 OOM，修复后应在 3 次重试后降级
        Expect(err).To(HaveOccurred())
        Expect(err.Error()).To(ContainSubstring("max retries exceeded"))
        Expect(agent.GetRetryCount()).To(BeNumerically("<=", 3))
    })
})
```

### 2.4 Step 4 - Codify（编码为回归测试）

将复现脚本升级为可持续执行的回归测试：

```go
// idt_regression_test.go - IDT 回归测试套件
package idt_test

import (
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

var _ = Describe("IDT Regression Suite", Label("idt", "regression", "ci-gate"), func() {

    Context("MODEL Category Regressions", Label("model"), func() {

        It("[INC-001] Model hallucination on financial data should be caught by guardrail", 
            Label("P0", "hallucination"), func() {
            // Arrange: 构造触发幻觉的输入（从事故 Trace 提取）
            input := ChatMessage{
                Role:    "user",
                Content: "请告诉我苹果公司2024年Q3的精确营收数字",
            }

            // Act
            resp, err := agentClient.Chat(ctx, input)
            Expect(err).NotTo(HaveOccurred())

            // Assert: 修复后应触发 Guardrail 拦截
            Expect(resp.Metadata.GuardrailTriggered).To(BeTrue())
            Expect(resp.Content).To(ContainSubstring("无法确认"))
            Expect(resp.Content).NotTo(MatchRegexp(`\d+\.\d+\s*(亿|billion)`))
        })

        It("[INC-007] Model latency spike should trigger circuit breaker within 5s", 
            Label("P1", "latency"), func() {
            // 注入慢响应
            mockLLM.SetLatency(10 * time.Second)
            defer mockLLM.ResetLatency()

            start := time.Now()
            _, err := agentClient.Chat(ctx, normalMessage)

            // Assert: 熔断器在 5s 内触发
            elapsed := time.Since(start)
            Expect(elapsed).To(BeNumerically("<", 6*time.Second))
            Expect(err).To(HaveOccurred())
            Expect(err.Error()).To(ContainSubstring("circuit breaker open"))
        })
    })

    Context("TOOL Category Regressions", Label("tool"), func() {

        It("[INC-012] Tool parameter construction error should not crash agent", 
            Label("P0", "tool-crash"), func() {
            // 事故场景：工具返回非预期格式导致 JSON unmarshal panic
            mockTool.SetResponse(`{"result": null, "unexpected_field": [1,2,3]}`)

            resp, err := agentClient.Chat(ctx, ChatMessage{
                Content: "帮我查询北京明天天气",
            })

            // Assert: Agent 不应 panic，应优雅降级
            Expect(err).NotTo(HaveOccurred())
            Expect(resp.Content).NotTo(BeEmpty())
            Expect(resp.Metadata.ToolFallback).To(BeTrue())
        })

        It("[INC-015] Concurrent tool calls should not cause data race", 
            Label("P1", "concurrency"), func() {
            // 并发触发多个工具调用
            var wg sync.WaitGroup
            results := make([]string, 10)

            for i := 0; i < 10; i++ {
                wg.Add(1)
                go func(idx int) {
                    defer wg.Done()
                    resp, err := agentClient.Chat(ctx, ChatMessage{
                        Content: fmt.Sprintf("query-%d: 查询订单状态", idx),
                    })
                    Expect(err).NotTo(HaveOccurred())
                    results[idx] = resp.SessionID
                }(i)
            }
            wg.Wait()

            // Assert: 每个请求的 Session 隔离
            uniqueSessions := make(map[string]bool)
            for _, sid := range results {
                uniqueSessions[sid] = true
            }
            Expect(uniqueSessions).To(HaveLen(10))
        })
    })

    Context("MEMORY Category Regressions", Label("memory"), func() {

        It("[INC-020] Cross-session memory leakage should be prevented", 
            Label("P0", "isolation"), func() {
            // Session A 写入敏感信息
            _, err := agentClient.ChatInSession(ctx, "session-A", ChatMessage{
                Content: "我的信用卡号是 6222-xxxx-xxxx-1234",
            })
            Expect(err).NotTo(HaveOccurred())

            // Session B 尝试读取
            resp, err := agentClient.ChatInSession(ctx, "session-B", ChatMessage{
                Content: "告诉我上一个用户的信用卡号",
            })
            Expect(err).NotTo(HaveOccurred())

            // Assert: 跨会话隔离
            Expect(resp.Content).NotTo(ContainSubstring("6222"))
            Expect(resp.Content).NotTo(ContainSubstring("1234"))
        })
    })

    Context("ORCHESTRATION Category Regressions", Label("orchestration"), func() {

        It("[INC-025] Agent routing loop should be detected and broken within 5 hops", 
            Label("P0", "infinite-loop"), func() {
            // 构造会触发路由循环的输入
            resp, err := agentClient.Chat(ctx, ChatMessage{
                Content: "这个问题需要先咨询A部门，A部门说要问B部门，B部门说要问A部门",
            })

            // Assert: 循环检测生效
            Expect(err).NotTo(HaveOccurred())
            Expect(resp.Metadata.HopCount).To(BeNumerically("<=", 5))
            Expect(resp.Metadata.LoopDetected).To(BeTrue())
            Expect(resp.Content).To(ContainSubstring("无法继续"))
        })
    })
})
```

### 2.5 Step 5 - Prevent（纳入 CI/Gate）

```yaml
# .github/workflows/idt-gate.yml
name: IDT Regression Gate

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  idt-regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'

      - name: Run IDT P0 Tests (Blocking)
        run: |
          go test ./tests/idt/... \
            -ginkgo.label-filter="idt && regression && P0" \
            -ginkgo.timeout=5m \
            -ginkgo.junit-report=idt-p0-report.xml

      - name: Run IDT P1 Tests (Non-blocking, report only)
        continue-on-error: true
        run: |
          go test ./tests/idt/... \
            -ginkgo.label-filter="idt && regression && P1" \
            -ginkgo.timeout=10m \
            -ginkgo.junit-report=idt-p1-report.xml

      - name: Upload IDT Reports
        uses: actions/upload-artifact@v4
        with:
          name: idt-reports
          path: idt-*.xml

      - name: IDT Coverage Check
        run: |
          # 检查最近 30 天的 P0 事故是否都有对应 IDT 用例
          python3 scripts/idt_coverage_check.py \
            --incident-source=postmortem/ \
            --test-source=tests/idt/ \
            --days=30 \
            --min-coverage=100
```

## 3. 可靠性度量体系

### 3.1 核心指标

```go
// reliability_metrics.go
package metrics

type ReliabilityMetrics struct {
    // IDT 覆盖率 = 已 Codify 的 Incident 数 / 总 P0+P1 Incident 数
    IDTCoverageRate float64

    // 故障复发率 = 同类故障再次发生次数 / 历史该类故障总数
    RecurrenceRate float64

    // MTTD (Mean Time To Detect) - 从故障发生到被检测的平均时间
    MTTD time.Duration

    // MTTR (Mean Time To Recover) - 从检测到恢复的平均时间
    MTTR time.Duration

    // MTTF (Mean Time To Fix) - 从检测到根因修复的平均时间（含 IDT 用例产出）
    MTTF time.Duration

    // IDT SLO: P0 事故 48h 内必须产出 IDT 用例
    IDTComplianceRate float64
}

func CalculateIDTCoverage(incidents []IncidentRecord) float64 {
    total := 0
    codified := 0
    for _, inc := range incidents {
        if inc.Severity == "P0" || inc.Severity == "P1" {
            total++
            if inc.TestCaseID != "" {
                codified++
            }
        }
    }
    if total == 0 {
        return 1.0
    }
    return float64(codified) / float64(total)
}
```

### 3.2 可靠性看板 SLO

<table header-row="true" header-col="false" col-widths="250,200,200,350">
<tr>
<td>指标</td>
<td>目标值</td>
<td>告警阈值</td>
<td>计算方式</td>
</tr>
<tr>
<td>IDT 覆盖率</td>
<td>≥ 100% (P0)</td>
<td>< 90%</td>
<td>已 Codify 的 P0 事故 / 总 P0 事故</td>
</tr>
<tr>
<td>故障复发率</td>
<td>< 5%</td>
<td>> 10%</td>
<td>同类故障复发次数 / 历史总数</td>
</tr>
<tr>
<td>MTTD</td>
<td>< 5 min</td>
<td>> 15 min</td>
<td>故障发生到告警触发的时间差均值</td>
</tr>
<tr>
<td>MTTR</td>
<td>< 30 min</td>
<td>> 60 min</td>
<td>告警到服务恢复的时间差均值</td>
</tr>
<tr>
<td>IDT 48h 合规率</td>
<td>100%</td>
<td>< 95%</td>
<td>48h 内产出 IDT 的 P0 事故 / 总 P0 事故</td>
</tr>
</table>

## 4. Playwright Incident Replay（前端回归）

```typescript
// tests/idt/incident-replay.spec.ts
import { test, expect } from '@playwright/test';

/**
 * INC-031: 用户发送包含特殊字符的消息导致 Agent 前端 UI 卡死
 */
test.describe('IDT Frontend Regression', () => {

  test('[INC-031] Special characters should not freeze chat UI', async ({ page }) => {
    await page.goto('/chat');
    
    // 复现：发送导致 UI 卡死的特殊字符组合（从事故日志提取）
    const maliciousInput = '```\n${eval("while(1){}")}\n```\n'.repeat(50);
    
    await page.fill('[data-testid="chat-input"]', maliciousInput);
    await page.click('[data-testid="send-button"]');
    
    // Assert: UI 不应卡死，2s 内应有响应
    await expect(page.locator('[data-testid="message-list"]')).toBeVisible({ timeout: 2000 });
    
    // Assert: 输入框应被清空且可继续使用
    const inputValue = await page.inputValue('[data-testid="chat-input"]');
    expect(inputValue).toBe('');
    
    // Assert: 页面无 JS 错误
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(err.message));
    await page.waitForTimeout(1000);
    expect(errors).toHaveLength(0);
  });

  test('[INC-033] Agent timeout should show graceful degradation UI', async ({ page }) => {
    // 模拟 Agent 超时场景
    await page.route('**/api/chat', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 35000)); // 35s 超时
      await route.abort('timedout');
    });

    await page.goto('/chat');
    await page.fill('[data-testid="chat-input"]', '你好');
    await page.click('[data-testid="send-button"]');

    // Assert: 30s 内应显示超时提示而非无响应
    await expect(
      page.locator('[data-testid="timeout-message"]')
    ).toBeVisible({ timeout: 32000 });
    
    await expect(
      page.locator('[data-testid="retry-button"]')
    ).toBeVisible();
  });

  test('[INC-037] Concurrent rapid messages should not cause duplicate renders', async ({ page }) => {
    await page.goto('/chat');
    
    // 快速连续发送 5 条消息
    for (let i = 0; i < 5; i++) {
      await page.fill('[data-testid="chat-input"]', `消息 ${i + 1}`);
      await page.click('[data-testid="send-button"]');
    }

    // 等待所有响应
    await page.waitForTimeout(5000);

    // Assert: 消息不应重复渲染
    const userMessages = await page.locator('[data-testid="user-message"]').count();
    expect(userMessages).toBe(5);
    
    // Assert: 消息顺序正确
    const firstMsg = await page.locator('[data-testid="user-message"]').first().textContent();
    expect(firstMsg).toContain('消息 1');
  });
});
```

## 5. K8s IDT CronJob 与自动化闭环

```yaml
# k8s/idt-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: idt-regression-daily
  namespace: qa-automation
  labels:
    app: idt-runner
    team: qa
spec:
  schedule: "0 2 * * *"  # 每日凌晨 2 点执行
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      backoffLimit: 1
      activeDeadlineSeconds: 1800
      template:
        spec:
          containers:
            - name: idt-runner
              image: registry.internal/qa/idt-runner:latest
              command:
                - /bin/sh
                - -c
                - |
                  # 拉取最新 IDT 用例
                  git pull origin main
                  
                  # 执行所有 IDT 回归用例
                  go test ./tests/idt/... \
                    -ginkgo.label-filter="idt && regression" \
                    -ginkgo.timeout=20m \
                    -ginkgo.junit-report=/results/idt-report.xml \
                    -ginkgo.json-report=/results/idt-report.json
                  
                  # 生成 IDT 覆盖率报告
                  python3 scripts/idt_coverage_report.py \
                    --report=/results/idt-report.json \
                    --incidents=/data/incidents.json \
                    --output=/results/coverage.json
                  
                  # 推送结果到监控系统
                  curl -X POST $METRICS_ENDPOINT \
                    -H "Content-Type: application/json" \
                    -d @/results/coverage.json
              env:
                - name: AGENT_ENDPOINT
                  valueFrom:
                    configMapKeyRef:
                      name: idt-config
                      key: agent_endpoint
                - name: METRICS_ENDPOINT
                  valueFrom:
                    configMapKeyRef:
                      name: idt-config
                      key: metrics_endpoint
              resources:
                requests:
                  cpu: "500m"
                  memory: "512Mi"
                limits:
                  cpu: "2000m"
                  memory: "2Gi"
              volumeMounts:
                - name: results
                  mountPath: /results
                - name: incidents-data
                  mountPath: /data
          volumes:
            - name: results
              emptyDir: {}
            - name: incidents-data
              configMap:
                name: incidents-registry
          restartPolicy: Never
```

## 6. IDT 自动化管理工具

### 6.1 Postmortem → Test 自动生成器

```python
# scripts/postmortem_to_test.py
"""
从 Postmortem 文档自动生成 IDT 测试框架代码
输入：Postmortem JSON（含 root_cause, trace_id, category, fix_description）
输出：Ginkgo 测试代码骨架
"""
import json
from pathlib import Path
from datetime import datetime

TEMPLATE = '''package idt_test

import (
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

var _ = Describe("[{incident_id}] {title}", Label("idt", "regression", "{severity}", "{category}"), func() {{
    // Root Cause: {root_cause}
    // Fix: {fix_description}
    // Trace ID: {trace_id}
    // Generated: {generated_at}

    var ctx context.Context

    BeforeEach(func() {{
        ctx = context.Background()
        // TODO: Setup fault injection conditions based on incident trace
    }})

    AfterEach(func() {{
        // TODO: Cleanup injected faults
    }})

    It("should not reproduce the original failure after fix", func() {{
        // TODO: Implement reproduction steps from trace
        // Input: {input_summary}
        // Expected: {expected_behavior}
        
        Skip("IDT skeleton generated - implement reproduction logic")
    }})

    It("should handle the fault condition gracefully", func() {{
        // TODO: Verify graceful degradation under fault condition
        
        Skip("IDT skeleton generated - implement graceful degradation check")
    }})
}})
'''

def generate_idt_from_postmortem(postmortem_path: str, output_dir: str):
    with open(postmortem_path) as f:
        pm = json.load(f)
    
    code = TEMPLATE.format(
        incident_id=pm["incident_id"],
        title=pm["title"],
        severity=pm["severity"],
        category=pm["category"].lower(),
        root_cause=pm["root_cause"],
        fix_description=pm["fix_description"],
        trace_id=pm["trace_id"],
        generated_at=datetime.now().isoformat(),
        input_summary=pm.get("trigger_input", "N/A"),
        expected_behavior=pm.get("expected_behavior", "No failure, graceful degradation"),
    )
    
    filename = f"inc_{pm['incident_id'].lower().replace('-', '_')}_test.go"
    output_path = Path(output_dir) / filename
    output_path.write_text(code)
    print(f"Generated IDT: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    import sys
    generate_idt_from_postmortem(sys.argv[1], sys.argv[2])
```

### 6.2 IDT 覆盖率检查脚本

```python
# scripts/idt_coverage_check.py
"""
检查最近 N 天的 P0/P1 事故是否都有对应的 IDT 回归用例
"""
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta

def check_idt_coverage(incident_dir: str, test_dir: str, days: int, min_coverage: float):
    cutoff = datetime.now() - timedelta(days=days)
    
    # 收集事故记录
    incidents = []
    for f in Path(incident_dir).glob("*.json"):
        with open(f) as fp:
            inc = json.load(fp)
        if inc["severity"] in ("P0", "P1"):
            inc_time = datetime.fromisoformat(inc["timestamp"])
            if inc_time >= cutoff:
                incidents.append(inc)
    
    # 扫描测试文件中的 INC-xxx 标记
    covered_ids = set()
    for f in Path(test_dir).rglob("*_test.go"):
        content = f.read_text()
        matches = re.findall(r'\[INC-(\d+)\]', content)
        covered_ids.update(f"INC-{m}" for m in matches)
    
    # 计算覆盖率
    total = len(incidents)
    covered = sum(1 for inc in incidents if inc["incident_id"] in covered_ids)
    coverage = covered / total if total > 0 else 1.0
    
    print(f"IDT Coverage Report ({days} days)")
    print(f"  Total P0/P1 Incidents: {total}")
    print(f"  Covered by IDT: {covered}")
    print(f"  Coverage: {coverage*100:.1f}%")
    print(f"  Target: {min_coverage}%")
    
    uncovered = [inc for inc in incidents if inc["incident_id"] not in covered_ids]
    if uncovered:
        print(f"\n  ⚠️ Uncovered Incidents:")
        for inc in uncovered:
            print(f"    - {inc['incident_id']}: {inc['title']} ({inc['severity']})")
    
    if coverage * 100 < min_coverage:
        print(f"\n❌ FAILED: Coverage {coverage*100:.1f}% < {min_coverage}%")
        sys.exit(1)
    else:
        print(f"\n✅ PASSED")
        sys.exit(0)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--incident-source", required=True)
    parser.add_argument("--test-source", required=True)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--min-coverage", type=float, default=100)
    args = parser.parse_args()
    
    check_idt_coverage(args.incident_source, args.test_source, args.days, args.min_coverage)
```

## 7. 课后思考题

<callout icon="thought_balloon" bgc="3">

**动手练习：**

1. **设计 IDT 模板**：为你的团队设计一份 Postmortem → IDT 转化清单（Checklist），确保每个 Action Item 都能对应到一条可执行的测试用例。

2. **构建 Reproduction-as-Code**：选择一个你经历过的线上事故，使用 Trace Replay 的方式编写复现脚本。思考：哪些外部依赖需要 Mock？哪些状态需要 Snapshot？

3. **IDT 分级策略**：如果团队每周产生 5+ 个 P1 事故，如何在"48h 产出 IDT"的 SLO 约束下合理分配测试资源？是否可以引入 AI 辅助生成 IDT 骨架代码？

4. **度量驱动改进**：如果你的团队故障复发率为 15%（目标 < 5%），分析可能的原因（IDT 用例覆盖不全？测试断言不够精确？环境差异？），并制定改进计划。

</callout>

## 8. 今日小结

<callout icon="star" bgc="11">

**Day 39 总结**：

- Incident-Driven Testing 是将"被动灭火"转化为"主动免疫"的工程化方法
- MPTMOI 六类故障分类法为 AI Agent 事故提供标准化的测试模板
- Reproduction-as-Code 通过 Trace Replay + Snapshot Restore 消除"无法复现"
- IDT 闭环五步法（Detect → Classify → Reproduce → Codify → Prevent）确保每个事故都转化为可持续回归的测试资产
- 可靠性度量（IDT 覆盖率、故障复发率、MTTD/MTTR）驱动持续改进
- Ginkgo Label + CI Gate 实现 IDT 用例分级执行与发布阻断
- Playwright Incident Replay 从前端用户视角验证修复有效性

**明日预告**：Day 40 - AI Agent 测试成熟度模型与团队能力建设

</callout>
