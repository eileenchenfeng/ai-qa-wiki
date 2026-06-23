---
title: "每日 AI 学习笔记｜Day 40：AI Agent 端到端测试编排与流水线集成"
date: 2026-05-25
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, E2E-testing, test-orchestration, CI-CD, pipeline, Ginkgo, Playwright, K8s, GitHub-Actions]
---
# 每日 AI 学习笔记｜Day 40：AI Agent 端到端测试编排与流水线集成

AI Agent 系统的 E2E 测试不同于传统微服务——它涉及非确定性模型输出、多步异步交互、外部工具调用及状态流转。本篇系统阐述如何设计分层 E2E 测试编排策略，并将其无缝集成到 CI/CD 流水线中，实现"代码变更 → 自动验证 → 安全发布"的闭环。

{/* truncate */}

## 0. 核心总结

<callout icon="star" bgc="4">

**本篇核心要点：**

1. **E2E 测试编排的核心挑战**：AI Agent E2E 测试面临三大难题——非确定性输出（同一输入不同结果）、长链路依赖（模型→编排→工具→存储）、执行时间不可控（模型推理延迟波动大）。编排策略必须针对这些特性设计。
2. **三阶段编排模型**：Setup（环境就绪+依赖注入）→ Execute（场景驱动的多轮交互）→ Verify（语义+结构+副作用三维断言）。每个阶段都有明确的超时熔断和失败隔离机制。
3. **场景编排 DSL 设计**：通过 YAML/Go Struct 定义可复用的测试场景模板（ScenarioSpec），将用户意图、预期工具调用序列、断言规则声明化，支持参数化和数据驱动。
4. **CI/CD 分层集成策略**：Smoke（≤2min，PR Gate）→ Core（≤10min，Merge Gate）→ Full（≤30min，Nightly）→ Chaos（≤60min，Weekly）。通过 Label 选择器实现灵活的用例子集执行。
5. **并行化与资源隔离**：利用 K8s Namespace + 独立 Agent 实例实现测试并行化，避免共享状态污染。每个 CI Job 创建临时 Namespace，测试完成后自动清理。
6. **非确定性容忍策略**：引入 Semantic Assertion（LLM-as-Judge）+ Retry with Tolerance（允许 N 次中 M 次通过）+ Golden Response Bank（参考答案库）三层机制处理输出不确定性。
7. **流水线可观测性**：每次 Pipeline 执行生成 Test Report（JUnit XML）+ Trace Link（OpenTelemetry）+ Cost Report（Token 消耗），三者关联形成完整执行画像。
8. **失败快速反馈**：通过 Webhook + 飞书卡片/Slack Bot 实现失败即时通知，附带失败用例的 Trace 链接和 LLM 输出 diff，帮助开发者 5 分钟内定位根因。

</callout>

## 1. 核心理论：AI Agent E2E 测试编排的独特挑战

### 1.1 为什么传统 E2E 框架不够用

传统 E2E 测试假设系统行为是确定性的：给定输入 A，总是得到输出 B。但 AI Agent 打破了这一假设：

<table header-row="true" header-col="false" col-widths="200,400,400">
<tr>
<td>**挑战维度**</td>
<td>**传统微服务**</td>
<td>**AI Agent 系统**</td>
</tr>
<tr>
<td>输出确定性</td>
<td>同一输入 → 同一输出</td>
<td>同一 Prompt → 每次输出不同（温度、采样）</td>
</tr>
<tr>
<td>执行路径</td>
<td>固定调用链</td>
<td>动态选择工具、可能多轮重试</td>
</tr>
<tr>
<td>执行时间</td>
<td>毫秒级，可预测</td>
<td>秒~分钟级，波动大（模型排队）</td>
</tr>
<tr>
<td>状态管理</td>
<td>数据库事务，可回滚</td>
<td>Memory/Context Window，不可逆</td>
</tr>
<tr>
<td>断言方式</td>
<td>精确匹配</td>
<td>语义相似度 + 结构校验 + 副作用验证</td>
</tr>
</table>

### 1.2 E2E 编排三阶段模型

```
┌─────────────────────────────────────────────────────────┐
│                    E2E Test Lifecycle                     │
├──────────────┬──────────────────┬───────────────────────┤
│   SETUP      │     EXECUTE      │       VERIFY          │
│              │                  │                       │
│ • K8s NS    │ • Multi-turn     │ • Semantic Assert     │
│ • Agent     │   Conversation   │ • Tool Call Check     │
│ • Mock/Stub │ • Tool Trigger   │ • Side Effect Verify  │
│ • Seed Data │ • State Flow     │ • Latency Budget      │
│              │                  │ • Cost Guard          │
└──────────────┴──────────────────┴───────────────────────┘
     Timeout: 30s    Timeout: 120s     Timeout: 30s
```

## 2. 工程实践：场景编排 DSL 与 Ginkgo 实现

### 2.1 场景描述 DSL（Go Struct）

```go
package e2e

// ScenarioSpec defines a declarative E2E test scenario for an AI Agent.
type ScenarioSpec struct {
    Name        string            `yaml:"name"`
    Labels      []string          `yaml:"labels"` // e.g., ["smoke", "P0", "tool-call"]
    Agent       AgentConfig       `yaml:"agent"`
    Setup       SetupSpec         `yaml:"setup"`
    Turns       []ConversationTurn `yaml:"turns"`
    Assertions  AssertionSpec     `yaml:"assertions"`
    Budget      BudgetSpec        `yaml:"budget"`
}

type AgentConfig struct {
    Template    string            `yaml:"template"`
    Tools       []string          `yaml:"tools"`
    Memory      MemoryConfig      `yaml:"memory"`
}

type ConversationTurn struct {
    Role        string            `yaml:"role"` // "user" or "system"
    Content     string            `yaml:"content"`
    ExpectTools []string          `yaml:"expect_tools,omitempty"`
    MaxLatency  string            `yaml:"max_latency,omitempty"` // e.g., "10s"
}

type AssertionSpec struct {
    SemanticMatch  *SemanticRule  `yaml:"semantic_match,omitempty"`
    MustContain    []string       `yaml:"must_contain,omitempty"`
    MustNotContain []string       `yaml:"must_not_contain,omitempty"`
    ToolSequence   []string       `yaml:"tool_sequence,omitempty"`
    SideEffects    []SideEffect   `yaml:"side_effects,omitempty"`
}

type BudgetSpec struct {
    MaxTokens   int    `yaml:"max_tokens"`
    MaxDuration string `yaml:"max_duration"` // e.g., "60s"
    MaxRetries  int    `yaml:"max_retries"`
}

type SemanticRule struct {
    Reference   string  `yaml:"reference"`
    MinScore    float64 `yaml:"min_score"` // 0.0 ~ 1.0
    Judge       string  `yaml:"judge"`     // "cosine" | "llm-as-judge"
}

type SideEffect struct {
    Type     string `yaml:"type"` // "db_record", "api_call", "file_created"
    Target   string `yaml:"target"`
    Expect   string `yaml:"expect"`
}
```

### 2.2 Ginkgo E2E Suite 实现

```go
//go:build e2e_agent

package e2e_test

import (
    "context"
    "os"
    "testing"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
    "k8s.io/client-go/kubernetes"
    "sigs.k8s.io/controller-runtime/pkg/client/config"
)

func TestAgentE2E(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Agent E2E Test Orchestration Suite")
}

var (
    k8sClient  kubernetes.Interface
    namespace  string
    agentURL   string
    ctx        context.Context
    cancel     context.CancelFunc
)

var _ = BeforeSuite(func() {
    ctx, cancel = context.WithTimeout(context.Background(), 5*time.Minute)

    cfg, err := config.GetConfig()
    Expect(err).NotTo(HaveOccurred())

    k8sClient, err = kubernetes.NewForConfig(cfg)
    Expect(err).NotTo(HaveOccurred())

    namespace = "e2e-agent-" + generateShortID()
    createNamespace(ctx, k8sClient, namespace)

    agentURL = deployAgentInstance(ctx, k8sClient, namespace)
    waitForAgentReady(ctx, agentURL, 60*time.Second)
})

var _ = AfterSuite(func() {
    deleteNamespace(ctx, k8sClient, namespace)
    cancel()
})

var _ = Describe("Agent E2E Orchestration", Label("e2e"), func() {

    Context("Smoke Tests", Label("smoke", "P0"), func() {
        It("should complete a single-turn QA interaction", func() {
            scenario := LoadScenario("scenarios/smoke_single_turn.yaml")
            result := ExecuteScenario(ctx, agentURL, scenario)

            Expect(result.Error).NotTo(HaveOccurred())
            Expect(result.TotalLatency).To(BeNumerically("<", 10*time.Second))
            Expect(result.SemanticScore).To(BeNumerically(">=", 0.8))
            Expect(result.TokensUsed).To(BeNumerically("<=", scenario.Budget.MaxTokens))
        })

        It("should handle tool-calling round-trip", func() {
            scenario := LoadScenario("scenarios/smoke_tool_call.yaml")
            result := ExecuteScenario(ctx, agentURL, scenario)

            Expect(result.Error).NotTo(HaveOccurred())
            Expect(result.ToolCallSequence).To(Equal(scenario.Assertions.ToolSequence))
            Expect(result.SideEffectsVerified).To(BeTrue())
        })
    })

    Context("Core Scenarios", Label("core", "P1"), func() {
        It("should maintain context across multi-turn conversation", func() {
            scenario := LoadScenario("scenarios/core_multi_turn_context.yaml")
            result := ExecuteScenario(ctx, agentURL, scenario)

            Expect(result.Error).NotTo(HaveOccurred())
            for i, turn := range result.TurnResults {
                Expect(turn.Latency).To(BeNumerically("<",
                    parseDuration(scenario.Turns[i].MaxLatency)))
            }
            Expect(result.ContextCoherence).To(BeNumerically(">=", 0.85))
        })

        It("should recover from tool failure with graceful degradation", func() {
            scenario := LoadScenario("scenarios/core_tool_failure_recovery.yaml")
            injectToolFault(ctx, namespace, "search-api", FaultConfig{
                Type: "error", Rate: 1.0, Duration: 30 * time.Second,
            })
            defer clearToolFault(ctx, namespace, "search-api")

            result := ExecuteScenario(ctx, agentURL, scenario)

            Expect(result.Error).NotTo(HaveOccurred())
            Expect(result.DegradationTriggered).To(BeTrue())
            Expect(result.FinalResponse).NotTo(BeEmpty())
        })
    })

    Context("Full Regression", Label("full", "nightly"), func() {
        scenarios := LoadScenariosFromDir("scenarios/regression/")

        for _, s := range scenarios {
            scenario := s
            It("Scenario: "+scenario.Name, func() {
                result := ExecuteScenarioWithRetry(ctx, agentURL, scenario,
                    RetryPolicy{MaxAttempts: 3, PassThreshold: 2})
                Expect(result.PassCount).To(BeNumerically(">=", 2))
            })
        }
    })
})
```

### 2.3 场景执行引擎（核心编排逻辑）

```go
package e2e

import (
    "context"
    "fmt"
    "time"

    "github.com/go-resty/resty/v2"
)

type ExecutionResult struct {
    Error                error
    TotalLatency         time.Duration
    TokensUsed           int
    SemanticScore        float64
    ContextCoherence     float64
    ToolCallSequence     []string
    SideEffectsVerified  bool
    DegradationTriggered bool
    FinalResponse        string
    TurnResults          []TurnResult
    PassCount            int
    TraceID              string
}

type TurnResult struct {
    Response  string
    Latency   time.Duration
    ToolCalls []string
    Tokens    int
}

func ExecuteScenario(ctx context.Context, agentURL string, spec ScenarioSpec) ExecutionResult {
    client := resty.New().SetTimeout(parseDuration(spec.Budget.MaxDuration))
    sessionID := createSession(ctx, client, agentURL, spec.Agent)
    result := ExecutionResult{TraceID: generateTraceID()}

    var allToolCalls []string
    totalTokens := 0
    start := time.Now()

    for i, turn := range spec.Turns {
        turnStart := time.Now()
        turnCtx, turnCancel := context.WithTimeout(ctx, parseDuration(turn.MaxLatency))

        resp, err := sendMessage(turnCtx, client, agentURL, sessionID, turn.Content)
        turnCancel()

        if err != nil {
            result.Error = fmt.Errorf("turn %d failed: %w", i, err)
            return result
        }

        turnResult := TurnResult{
            Response:  resp.Content,
            Latency:   time.Since(turnStart),
            ToolCalls: resp.ToolCalls,
            Tokens:    resp.TokensUsed,
        }
        result.TurnResults = append(result.TurnResults, turnResult)
        allToolCalls = append(allToolCalls, resp.ToolCalls...)
        totalTokens += resp.TokensUsed

        if totalTokens > spec.Budget.MaxTokens {
            result.Error = fmt.Errorf("token budget exceeded: %d > %d", totalTokens, spec.Budget.MaxTokens)
            return result
        }
    }

    result.TotalLatency = time.Since(start)
    result.TokensUsed = totalTokens
    result.ToolCallSequence = allToolCalls
    result.FinalResponse = result.TurnResults[len(result.TurnResults)-1].Response

    // Semantic assertion
    if spec.Assertions.SemanticMatch != nil {
        result.SemanticScore = evaluateSemantic(
            result.FinalResponse,
            spec.Assertions.SemanticMatch.Reference,
            spec.Assertions.SemanticMatch.Judge,
        )
    }

    // Tool sequence assertion
    if spec.Assertions.ToolSequence != nil {
        result.ToolCallSequence = allToolCalls
    }

    // Side effects verification
    if len(spec.Assertions.SideEffects) > 0 {
        result.SideEffectsVerified = verifySideEffects(ctx, spec.Assertions.SideEffects)
    }

    return result
}

func ExecuteScenarioWithRetry(ctx context.Context, agentURL string, spec ScenarioSpec, policy RetryPolicy) ExecutionResult {
    var lastResult ExecutionResult
    passCount := 0

    for attempt := 0; attempt < policy.MaxAttempts; attempt++ {
        lastResult = ExecuteScenario(ctx, agentURL, spec)
        if lastResult.Error == nil && lastResult.SemanticScore >= 0.75 {
            passCount++
        }
        if passCount >= policy.PassThreshold {
            break
        }
    }
    lastResult.PassCount = passCount
    return lastResult
}
```

## 3. CI/CD 分层集成策略

### 3.1 Pipeline 分层架构

```yaml
# .github/workflows/agent-e2e-pipeline.yaml
name: Agent E2E Test Pipeline

on:
  pull_request:
    branches: [main, release/*]
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'   # Nightly full regression
    - cron: '0 4 * * 0'   # Weekly chaos testing

env:
  AGENT_IMAGE: registry.example.com/agent:${{ github.sha }}
  K8S_CLUSTER: e2e-cluster
  TRACE_ENDPOINT: http://otel-collector:4318

jobs:
  smoke-gate:
    name: "🚦 Smoke Gate (PR Blocker)"
    runs-on: ubuntu-latest
    timeout-minutes: 5
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: Run Smoke Tests
        run: |
          go test -v -tags=e2e_agent \
            -run "TestAgentE2E" \
            --ginkgo.label-filter="smoke" \
            --ginkgo.timeout=2m \
            --ginkgo.junit-report=smoke-report.xml \
            ./tests/e2e/...
      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: smoke-report
          path: smoke-report.xml

  core-gate:
    name: "🔒 Core Gate (Merge Blocker)"
    runs-on: ubuntu-latest
    timeout-minutes: 15
    needs: smoke-gate
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy Agent to Test Namespace
        run: |
          kubectl create ns e2e-${{ github.run_id }}
          helm install agent ./charts/agent \
            --namespace e2e-${{ github.run_id }} \
            --set image=${{ env.AGENT_IMAGE }} \
            --wait --timeout=120s
      - name: Run Core Tests
        run: |
          go test -v -tags=e2e_agent \
            -run "TestAgentE2E" \
            --ginkgo.label-filter="core" \
            --ginkgo.timeout=10m \
            --ginkgo.junit-report=core-report.xml \
            ./tests/e2e/...
      - name: Cleanup
        if: always()
        run: kubectl delete ns e2e-${{ github.run_id }} --ignore-not-found

  nightly-full:
    name: "🌙 Nightly Full Regression"
    runs-on: ubuntu-latest
    timeout-minutes: 45
    if: github.event.schedule == '0 2 * * *' || github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      - name: Run Full Regression
        run: |
          go test -v -tags=e2e_agent \
            -run "TestAgentE2E" \
            --ginkgo.label-filter="full || core || smoke" \
            --ginkgo.timeout=30m \
            --ginkgo.junit-report=full-report.xml \
            --ginkgo.procs=4 \
            ./tests/e2e/...
      - name: Notify on Failure
        if: failure()
        run: |
          python3 scripts/notify_failure.py \
            --report full-report.xml \
            --webhook ${{ secrets.FEISHU_WEBHOOK }}

  weekly-chaos:
    name: "💥 Weekly Chaos Testing"
    runs-on: ubuntu-latest
    timeout-minutes: 90
    if: github.event.schedule == '0 4 * * 0'
    steps:
      - uses: actions/checkout@v4
      - name: Run Chaos Scenarios
        run: |
          go test -v -tags=e2e_agent \
            -run "TestAgentE2E" \
            --ginkgo.label-filter="chaos" \
            --ginkgo.timeout=60m \
            ./tests/e2e/...
```

### 3.2 并行执行与资源隔离（K8s 方案）

```go
package e2e

import (
    "context"
    "fmt"

    corev1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/client-go/kubernetes"
)

func createNamespace(ctx context.Context, client kubernetes.Interface, name string) {
    ns := &corev1.Namespace{
        ObjectMeta: metav1.ObjectMeta{
            Name: name,
            Labels: map[string]string{
                "purpose":    "e2e-testing",
                "managed-by": "ginkgo-e2e",
                "ttl":        "1h",
            },
            Annotations: map[string]string{
                "janitor/ttl": "3600",
            },
        },
    }
    _, err := client.CoreV1().Namespaces().Create(ctx, ns, metav1.CreateOptions{})
    if err != nil {
        panic(fmt.Sprintf("failed to create namespace %s: %v", name, err))
    }
}

func deployAgentInstance(ctx context.Context, client kubernetes.Interface, namespace string) string {
    // Deploy via Helm or raw manifests
    // Returns the agent service URL within the namespace
    return fmt.Sprintf("http://agent-svc.%s.svc.cluster.local:8080", namespace)
}

func deleteNamespace(ctx context.Context, client kubernetes.Interface, name string) {
    _ = client.CoreV1().Namespaces().Delete(ctx, name, metav1.DeleteOptions{})
}
```

## 4. 非确定性容忍与语义断言

### 4.1 三层断言策略

```go
package e2e

import (
    "context"
    "math"
    "strings"

    "github.com/sashabaranov/go-openai"
)

type AssertionEngine struct {
    openaiClient *openai.Client
    embedModel   string
    judgeModel   string
}

func (ae *AssertionEngine) AssertSemantic(actual, reference string, minScore float64) (float64, error) {
    // Layer 1: Cosine similarity of embeddings
    score, err := ae.cosineSimilarity(actual, reference)
    if err != nil {
        return 0, err
    }
    if score >= minScore {
        return score, nil
    }

    // Layer 2: LLM-as-Judge for borderline cases
    judgeScore, err := ae.llmJudge(actual, reference)
    if err != nil {
        return score, err
    }
    return math.Max(score, judgeScore), nil
}

func (ae *AssertionEngine) cosineSimilarity(a, b string) (float64, error) {
    ctx := context.Background()
    resp, err := ae.openaiClient.CreateEmbeddings(ctx, openai.EmbeddingRequest{
        Model: openai.EmbeddingModel(ae.embedModel),
        Input: []string{a, b},
    })
    if err != nil {
        return 0, err
    }
    return cosine(resp.Data[0].Embedding, resp.Data[1].Embedding), nil
}

func (ae *AssertionEngine) llmJudge(actual, reference string) (float64, error) {
    ctx := context.Background()
    prompt := fmt.Sprintf(`You are a QA judge. Score how well the ACTUAL response matches the REFERENCE on a scale of 0.0 to 1.0.
Consider: factual accuracy, completeness, and relevance. Respond with only a decimal number.

REFERENCE: %s

ACTUAL: %s

Score:`, reference, actual)

    resp, err := ae.openaiClient.CreateChatCompletion(ctx, openai.ChatCompletionRequest{
        Model:       ae.judgeModel,
        Messages:    []openai.ChatCompletionMessage{{Role: "user", Content: prompt}},
        Temperature: 0.0,
    })
    if err != nil {
        return 0, err
    }
    score := parseFloat(strings.TrimSpace(resp.Choices[0].Message.Content))
    return score, nil
}

func cosine(a, b []float32) float64 {
    var dot, normA, normB float64
    for i := range a {
        dot += float64(a[i]) * float64(b[i])
        normA += float64(a[i]) * float64(a[i])
        normB += float64(b[i]) * float64(b[i])
    }
    return dot / (math.Sqrt(normA) * math.Sqrt(normB))
}
```

### 4.2 Retry with Tolerance 策略

```go
package e2e

type RetryPolicy struct {
    MaxAttempts    int
    PassThreshold  int     // At least M out of N must pass
    BackoffBase    time.Duration
}

func DefaultRetryPolicy() RetryPolicy {
    return RetryPolicy{
        MaxAttempts:   3,
        PassThreshold: 2,  // 3 次中至少 2 次通过
        BackoffBase:   2 * time.Second,
    }
}
```

## 5. Playwright 前端 E2E 编排

```typescript
// tests/e2e/agent-chat-flow.spec.ts
import { test, expect } from '@playwright/test';

interface AgentResponse {
  content: string;
  toolCalls: string[];
  latencyMs: number;
}

test.describe('Agent Chat E2E Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agent/chat');
    await page.waitForSelector('[data-testid="chat-ready"]', { timeout: 30000 });
  });

  test('complete multi-turn conversation with tool use', async ({ page }) => {
    // Turn 1: User sends query
    const inputBox = page.locator('[data-testid="chat-input"]');
    await inputBox.fill('帮我查一下北京今天的天气，并创建一个提醒事项');
    await inputBox.press('Enter');

    // Wait for agent response with tool indicator
    const toolIndicator = page.locator('[data-testid="tool-calling-indicator"]');
    await expect(toolIndicator).toBeVisible({ timeout: 15000 });

    // Wait for final response
    const response = page.locator('[data-testid="agent-response"]').last();
    await expect(response).toBeVisible({ timeout: 30000 });

    // Verify tool call badges are shown
    const toolBadges = page.locator('[data-testid="tool-badge"]');
    await expect(toolBadges).toHaveCount(2); // weather + reminder

    // Verify response contains weather info
    const responseText = await response.textContent();
    expect(responseText).toMatch(/温度|天气|℃/);
    expect(responseText).toMatch(/提醒|已创建|reminder/i);

    // Turn 2: Follow-up question
    await inputBox.fill('把温度转换成华氏度');
    await inputBox.press('Enter');

    const followUpResponse = page.locator('[data-testid="agent-response"]').last();
    await expect(followUpResponse).toBeVisible({ timeout: 15000 });

    const followUpText = await followUpResponse.textContent();
    expect(followUpText).toMatch(/°F|华氏/);

    // Verify context coherence (references Beijing weather from Turn 1)
    expect(followUpText).toMatch(/北京|beijing/i);
  });

  test('handles agent timeout gracefully', async ({ page }) => {
    await page.route('**/api/agent/chat', async route => {
      await new Promise(resolve => setTimeout(resolve, 35000));
      await route.abort('timedout');
    });

    const inputBox = page.locator('[data-testid="chat-input"]');
    await inputBox.fill('复杂的分析任务');
    await inputBox.press('Enter');

    // Should show timeout message within UX budget
    const errorMsg = page.locator('[data-testid="error-message"]');
    await expect(errorMsg).toBeVisible({ timeout: 40000 });
    await expect(errorMsg).toContainText(/超时|timeout/i);

    // Retry button should be available
    const retryBtn = page.locator('[data-testid="retry-button"]');
    await expect(retryBtn).toBeVisible();
  });

  test('streaming response renders progressively', async ({ page }) => {
    const inputBox = page.locator('[data-testid="chat-input"]');
    await inputBox.fill('写一首关于测试的诗');
    await inputBox.press('Enter');

    // Verify streaming indicator
    const streamingDot = page.locator('[data-testid="streaming-indicator"]');
    await expect(streamingDot).toBeVisible({ timeout: 5000 });

    // Content should grow over time
    const responseEl = page.locator('[data-testid="agent-response"]').last();
    const initialLen = (await responseEl.textContent())?.length ?? 0;

    await page.waitForTimeout(2000);
    const laterLen = (await responseEl.textContent())?.length ?? 0;
    expect(laterLen).toBeGreaterThan(initialLen);

    // Wait for completion
    await expect(streamingDot).toBeHidden({ timeout: 30000 });
  });
});
```

## 6. 流水线可观测性与失败通知

### 6.1 Test Report + Trace 关联

```go
package e2e

import (
    "context"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/trace"
)

var tracer = otel.Tracer("e2e-agent-tests")

func ExecuteScenarioWithTracing(ctx context.Context, agentURL string, spec ScenarioSpec) ExecutionResult {
    ctx, span := tracer.Start(ctx, "e2e.scenario."+spec.Name,
        trace.WithAttributes(
            attribute.String("scenario.name", spec.Name),
            attribute.StringSlice("scenario.labels", spec.Labels),
            attribute.Int("scenario.turns", len(spec.Turns)),
            attribute.Int("scenario.budget.max_tokens", spec.Budget.MaxTokens),
        ),
    )
    defer span.End()

    result := ExecuteScenario(ctx, agentURL, spec)

    span.SetAttributes(
        attribute.Float64("result.semantic_score", result.SemanticScore),
        attribute.Int64("result.latency_ms", result.TotalLatency.Milliseconds()),
        attribute.Int("result.tokens_used", result.TokensUsed),
        attribute.Bool("result.passed", result.Error == nil),
    )

    if result.Error != nil {
        span.RecordError(result.Error)
    }

    result.TraceID = span.SpanContext().TraceID().String()
    return result
}
```

### 6.2 失败通知脚本（飞书 Webhook）

```python
#!/usr/bin/env python3
"""notify_failure.py - Parse JUnit XML and send failure summary to Feishu webhook."""
import json
import sys
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

def parse_junit(report_path: str) -> list[dict]:
    tree = ET.parse(report_path)
    failures = []
    for tc in tree.iter("testcase"):
        failure = tc.find("failure")
        if failure is not None:
            failures.append({
                "name": tc.get("name", "unknown"),
                "classname": tc.get("classname", ""),
                "time": tc.get("time", "0"),
                "message": failure.get("message", "")[:200],
            })
    return failures

def send_feishu_webhook(webhook_url: str, failures: list[dict]):
    if not failures:
        return
    lines = [f"**🔴 E2E 测试失败 ({len(failures)} 条)**\n---"]
    for f in failures[:10]:
        lines.append(f"• **{f['name']}** ({f['time']}s)\n  `{f['message']}`")
    if len(failures) > 10:
        lines.append(f"\n... 还有 {len(failures)-10} 条失败")

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "🚨 Agent E2E Pipeline 失败"},
                "template": "red"
            },
            "elements": [{"tag": "markdown", "content": "\n".join(lines)}]
        }
    }
    req = Request(webhook_url, json.dumps(card).encode(), {"Content-Type": "application/json"})
    urlopen(req)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--webhook", required=True)
    args = parser.parse_args()

    failures = parse_junit(args.report)
    send_feishu_webhook(args.webhook, failures)
    if failures:
        print(f"❌ {len(failures)} test(s) failed, notification sent.")
        sys.exit(1)
    print("✅ All tests passed.")
```

## 7. 最佳实践清单

<callout icon="bulb" bgc="5">

**E2E 测试编排最佳实践：**

1. **场景 > 步骤**：每个 E2E 用例必须是完整业务场景（用户视角），而非孤立的 API 验证。
2. **Budget Guard**：每个场景必须设置 Token 预算和时间预算，超出即熔断，防止 LLM 发散导致费用失控。
3. **隔离优先**：每个 CI Job 使用独立 K8s Namespace + 独立 Agent 实例，杜绝测试间状态污染。
4. **Retry ≠ Flaky**：对 AI Agent，合理的 Retry（3 次中 2 次通过）是必要的工程策略，但 Retry 阈值必须被监控。
5. **Trace 全链路**：每次测试执行都必须生成 OpenTelemetry Trace，失败时可通过 TraceID 直接跳转到完整调用链。
6. **分层执行**：PR 只跑 Smoke（≤2min），Merge 跑 Core（≤10min），Nightly 跑 Full，Weekly 跑 Chaos。
7. **Golden Dataset 版本化**：参考答案库（SemanticMatch.Reference）必须存入 Git，随代码一起版本管理。
8. **Cost Reporting**：每次 Pipeline 执行后生成 Token 消耗报告，对比历史趋势，发现异常消耗。

</callout>

## 8. 课后思考题

1. 如果你的 Agent 在 Nightly 全量回归中有 15% 的用例因为"语义断言分数低于阈值"而失败，但人工审核发现响应质量其实是 OK 的，你会如何调优断言策略？
2. 如何设计一套机制来自动检测 E2E 测试的"真失败"（Agent 行为退化）vs "假失败"（断言过于严格 / 环境问题），减少人工排查成本？
3. 在多 Agent 协作场景中（如 Orchestrator + 3 个 Worker），E2E 测试的 Setup 阶段需要部署多个 Agent 实例，如何优化启动时间，使 Core Gate 仍然控制在 10 分钟内？

## 9. 今日小结

本篇从 AI Agent E2E 测试的独特挑战出发，构建了完整的编排与流水线集成方案：

- **场景 DSL** 将测试用例声明化，提升可维护性和可复用性
- **Ginkgo Label 分层** 实现了灵活的用例选择和 CI 阶段绑定
- **K8s Namespace 隔离** 解决了并行化和状态污染问题
- **三层语义断言** 应对了 AI 输出不确定性的核心痛点
- **流水线可观测性** 让每次执行都可追溯、可审计、可优化

核心原则：**场景即代码·隔离即默认·断言即智能·反馈即实时**。
