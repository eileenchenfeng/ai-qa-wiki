---
title: "每日 AI 学习笔记｜Day 37：AI Agent 可测试性设计与质量左移"
date: 2026-05-22
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, testability, shift-left, SDET, Ginkgo, Playwright, K8s, design-for-test, dependency-injection]
---
# 每日 AI 学习笔记｜Day 37：AI Agent 可测试性设计与质量左移

AI Agent 系统天然具有不确定性——模型输出非确定性、工具调用链路动态编排、多轮对话状态复杂——这使得"后补测试"的成本极高。真正高效的质量保障不是在系统完成后堆砌测试用例，而是从架构设计阶段就把"可测试性"作为一等公民嵌入。本篇系统阐述 AI Agent 可测试性设计的 6 大原则、质量左移的工程落地手段，以及如何通过 DI（依赖注入）、可观测钩子、确定性回放层等机制，让 Agent 系统在开发早期就能被充分验证。

{/* truncate */}

## 0. 核心总结

<callout icon="star" bgc="4">

**本篇核心要点：**

1. **可测试性是架构属性**：不可测试的 Agent 不是"测试没写好"，而是"架构没设计好"。可测试性必须在 Design Review 阶段评审，与功能需求同等优先。
2. **6 大可测试性原则**：可观测性（Observability）、可控制性（Controllability）、可隔离性（Isolability）、确定性回放（Deterministic Replay）、契约显式化（Explicit Contracts）、故障可注入性（Fault Injectability）。
3. **依赖注入（DI）是基石**：Agent 的 LLM Client、Tool Executor、Memory Store、Orchestrator 必须通过接口注入，而非硬编码实例化，这是 Mock/Stub/Fake 的前提。
4. **确定性回放层**：在 LLM 调用与工具调用之间插入 Recording/Replay Middleware，支持"录制线上 Trace → 本地确定性回放"，将非确定性测试转化为确定性断言。
5. **质量左移 4 阶段**：需求评审植入可测试性检查 → 设计评审增加 Testability Scorecard → 编码阶段强制 Test Hook → PR 门禁自动化校验接口契约。
6. **Testability Scorecard（量化打分）**：从 DI 覆盖率、Mock 可替换率、Trace 可追踪率、故障注入点覆盖率、契约文件完备度 5 个维度对 Agent 模块打分（0-100），低于 60 分禁止合并。
7. **Ginkgo + httptest 确定性回放**：通过 `httptest.NewServer` + JSON Fixture 实现 LLM 响应录制回放，每次 CI 运行结果 100% 确定。
8. **Playwright Contract Snapshot**：前端 Agent UI 的工具调用面板，通过 snapshot 对比确保 Schema 变更被感知。

</callout>

## 1. 核心理论：可测试性的 6 大原则

### 1.1 可观测性（Observability）

Agent 内部每一步决策都必须产生结构化事件，而不是只有最终输出。

<callout icon="bulb" bgc="5">

**设计要求**：
- 每次 LLM 调用必须输出 `(prompt_hash, model_version, latency_ms, token_count, response_hash)`
- 每次工具调用必须输出 `(tool_name, input_schema_hash, output_schema_hash, latency_ms, error_code)`
- 编排层每次路由决策必须输出 `(decision_point, selected_branch, confidence_score)`

</callout>

### 1.2 可控制性（Controllability）

测试代码必须能控制 Agent 的每一个外部依赖的行为：

- LLM 响应可被 Mock 替换
- 工具返回值可被注入
- Memory 状态可被预设
- 时间/随机数可被固定

### 1.3 可隔离性（Isolability）

每个 Agent 组件（Planner、Executor、Memory、Tool）可以被独立测试，不依赖其他组件的真实实现。

### 1.4 确定性回放（Deterministic Replay）

录制线上真实的 LLM 响应和工具结果，在 CI 中使用录制文件确定性回放，避免每次测试都消耗真实 Token。

### 1.5 契约显式化（Explicit Contracts）

Agent 与外部系统（LLM API、工具 API、Memory API）之间的交互契约必须以 JSON Schema / Protobuf 形式显式定义，而非隐式约定。

### 1.6 故障可注入性（Fault Injectability）

架构必须提供故障注入点（Fault Injection Points），允许测试代码模拟：
- LLM 超时 / 限流 / 幻觉响应
- 工具调用失败 / 延迟 / 返回异常格式
- Memory 读写失败 / 数据损坏

---

## 2. 工程实践：依赖注入架构

### 2.1 Go 接口设计（Ginkgo 测试友好）

```go
package agent

// LLMClient 定义 LLM 调用契约
type LLMClient interface {
    ChatCompletion(ctx context.Context, req *ChatRequest) (*ChatResponse, error)
}

// ToolExecutor 定义工具执行契约
type ToolExecutor interface {
    Execute(ctx context.Context, toolName string, input json.RawMessage) (json.RawMessage, error)
}

// MemoryStore 定义记忆存取契约
type MemoryStore interface {
    Load(ctx context.Context, sessionID string) ([]Message, error)
    Save(ctx context.Context, sessionID string, msgs []Message) error
}

// AgentCore 通过构造函数注入所有依赖
type AgentCore struct {
    llm    LLMClient
    tools  ToolExecutor
    memory MemoryStore
    tracer Tracer
}

func NewAgentCore(llm LLMClient, tools ToolExecutor, mem MemoryStore, tracer Tracer) *AgentCore {
    return &AgentCore{llm: llm, tools: tools, memory: mem, tracer: tracer}
}
```

### 2.2 Ginkgo 测试中的 Mock 注入

```go
package agent_test

import (
    "context"
    "encoding/json"
    "testing"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

// FakeLLM 实现 LLMClient 接口，返回预设响应
type FakeLLM struct {
    Responses []*ChatResponse
    CallLog   []*ChatRequest
    callIdx   int
}

func (f *FakeLLM) ChatCompletion(ctx context.Context, req *ChatRequest) (*ChatResponse, error) {
    f.CallLog = append(f.CallLog, req)
    resp := f.Responses[f.callIdx%len(f.Responses)]
    f.callIdx++
    return resp, nil
}

// FakeToolExecutor 返回预设工具结果
type FakeToolExecutor struct {
    Results map[string]json.RawMessage
    Errors  map[string]error
}

func (f *FakeToolExecutor) Execute(ctx context.Context, name string, input json.RawMessage) (json.RawMessage, error) {
    if err, ok := f.Errors[name]; ok {
        return nil, err
    }
    return f.Results[name], nil
}

var _ = Describe("AgentCore Testability", Label("testability", "unit"), func() {
    var (
        agent   *AgentCore
        fakeLLM *FakeLLM
        fakeTool *FakeToolExecutor
        fakeMem *FakeMemoryStore
    )

    BeforeEach(func() {
        fakeLLM = &FakeLLM{
            Responses: []*ChatResponse{
                {Content: `{"action": "search", "input": {"query": "weather in Beijing"}}`},
                {Content: `北京今天晴，气温 28°C。`},
            },
        }
        fakeTool = &FakeToolExecutor{
            Results: map[string]json.RawMessage{
                "search": json.RawMessage(`{"result": "sunny, 28°C"}`),
            },
        }
        fakeMem = &FakeMemoryStore{}
        agent = NewAgentCore(fakeLLM, fakeTool, fakeMem, NoopTracer{})
    })

    It("should complete a tool-use turn with deterministic behavior", func() {
        resp, err := agent.Run(context.Background(), "今天北京天气怎么样？")
        Expect(err).NotTo(HaveOccurred())
        Expect(resp).To(ContainSubstring("28°C"))

        // 验证 LLM 被调用了 2 次（规划 + 总结）
        Expect(fakeLLM.CallLog).To(HaveLen(2))
        // 验证工具被正确调用
        Expect(fakeTool.CallLog).To(HaveKey("search"))
    })

    It("should gracefully degrade when tool fails", func() {
        fakeTool.Errors["search"] = errors.New("timeout")

        resp, err := agent.Run(context.Background(), "今天北京天气怎么样？")
        Expect(err).NotTo(HaveOccurred())
        // Agent 应降级为直接回答，而非崩溃
        Expect(resp).NotTo(BeEmpty())
        Expect(fakeLLM.CallLog).To(HaveLen(2)) // 规划 + 降级回答
    })
})
```

---

## 3. 工程实践：确定性回放层

### 3.1 录制-回放架构

```
┌─────────────────────────────────────────────────────┐
│                  Agent Runtime                        │
│                                                       │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │  Planner  │──▶│ Replay Layer │──▶│  Real LLM    │ │
│  └──────────┘   └──────────────┘   └──────────────┘ │
│                        │                              │
│                   ┌────▼────┐                         │
│                   │ Fixture  │                         │
│                   │  Store   │                         │
│                   └─────────┘                         │
└─────────────────────────────────────────────────────┘
```

- **录制模式**（CI nightly / staging）：真实调用 LLM，同时将 `(request_hash, response)` 写入 Fixture 文件
- **回放模式**（CI PR gate / 本地开发）：根据 `request_hash` 匹配 Fixture 文件，直接返回录制结果

### 3.2 Go 实现：Recording Middleware

```go
package replay

import (
    "context"
    "crypto/sha256"
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
)

type RecordingLLM struct {
    Real       LLMClient
    FixtureDir string
    Mode       string // "record" or "replay"
}

func (r *RecordingLLM) ChatCompletion(ctx context.Context, req *ChatRequest) (*ChatResponse, error) {
    hash := r.hashRequest(req)
    fixturePath := filepath.Join(r.FixtureDir, fmt.Sprintf("%s.json", hash))

    if r.Mode == "replay" {
        data, err := os.ReadFile(fixturePath)
        if err == nil {
            var resp ChatResponse
            json.Unmarshal(data, &resp)
            return &resp, nil
        }
        // Fixture not found, fall through to real call
    }

    resp, err := r.Real.ChatCompletion(ctx, req)
    if err != nil {
        return nil, err
    }

    // Record
    data, _ := json.MarshalIndent(resp, "", "  ")
    os.MkdirAll(r.FixtureDir, 0755)
    os.WriteFile(fixturePath, data, 0644)

    return resp, nil
}

func (r *RecordingLLM) hashRequest(req *ChatRequest) string {
    data, _ := json.Marshal(req)
    h := sha256.Sum256(data)
    return fmt.Sprintf("%x", h[:8])
}
```

### 3.3 Ginkgo 集成确定性回放

```go
var _ = Describe("Agent E2E with Replay", Label("e2e", "replay"), func() {
    var agent *AgentCore

    BeforeEach(func() {
        replayLLM := &RecordingLLM{
            Real:       nil, // replay 模式不需要真实 client
            FixtureDir: "testdata/fixtures/llm",
            Mode:       os.Getenv("REPLAY_MODE"), // "replay" in CI
        }
        agent = NewAgentCore(replayLLM, realToolExecutor, realMemory, otelTracer)
    })

    It("should produce consistent output across runs", func() {
        resp1, _ := agent.Run(ctx, "解释量子计算的基本原理")
        resp2, _ := agent.Run(ctx, "解释量子计算的基本原理")
        // 回放模式下，相同输入必须产生完全相同的输出
        Expect(resp1).To(Equal(resp2))
    })
})
```

---

## 4. 工程实践：Testability Scorecard

### 4.1 评分模型

<callout icon="first_place_medal" bgc="11">

**Testability Score = Σ(维度权重 × 维度得分)**

| 维度 | 权重 | 满分条件 |
|------|------|---------|
| DI 覆盖率 | 30% | 所有外部依赖均通过接口注入 |
| Mock 可替换率 | 25% | 每个接口都有对应的 Fake/Mock 实现 |
| Trace 覆盖率 | 20% | 所有关键决策点都有结构化 Trace |
| 故障注入点覆盖率 | 15% | 每个外部调用都有失败路径测试 |
| 契约文件完备度 | 10% | 每个 API 交互都有 JSON Schema 定义 |

**门禁**：Score < 60 → PR 禁止合并；Score < 80 → 标记 Warning；Score ≥ 80 → 通过

</callout>

### 4.2 自动化 Scorecard 计算（CI 集成）

```python
#!/usr/bin/env python3
"""testability_scorecard.py - 在 CI 中自动计算模块可测试性分数"""

import ast
import sys
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ScoreResult:
    di_coverage: float = 0.0       # DI 覆盖率 (0-100)
    mock_rate: float = 0.0         # Mock 可替换率 (0-100)
    trace_coverage: float = 0.0    # Trace 覆盖率 (0-100)
    fault_injection: float = 0.0   # 故障注入点覆盖率 (0-100)
    contract_completeness: float = 0.0  # 契约完备度 (0-100)

    @property
    def total(self) -> float:
        return (
            self.di_coverage * 0.30 +
            self.mock_rate * 0.25 +
            self.trace_coverage * 0.20 +
            self.fault_injection * 0.15 +
            self.contract_completeness * 0.10
        )

    @property
    def passed(self) -> bool:
        return self.total >= 60.0

def analyze_go_module(module_path: Path) -> ScoreResult:
    """分析 Go 模块的可测试性"""
    score = ScoreResult()

    go_files = list(module_path.rglob("*.go"))
    test_files = [f for f in go_files if f.name.endswith("_test.go")]
    src_files = [f for f in go_files if not f.name.endswith("_test.go")]

    # 1. DI 覆盖率：检查构造函数是否接收接口参数
    total_structs = 0
    di_structs = 0
    for f in src_files:
        content = f.read_text()
        if "interface {" in content or "interface{" in content:
            total_structs += 1
        if "func New" in content and "interface" in content:
            di_structs += 1
    score.di_coverage = (di_structs / max(total_structs, 1)) * 100

    # 2. Mock 可替换率：检查 test 文件中是否有 Fake/Mock 实现
    mock_count = 0
    for f in test_files:
        content = f.read_text()
        mock_count += content.count("Fake") + content.count("Mock")
    score.mock_rate = min((mock_count / max(len(test_files), 1)) * 50, 100)

    # 3. Trace 覆盖率：检查 span/trace 调用
    trace_calls = 0
    for f in src_files:
        content = f.read_text()
        trace_calls += content.count("StartSpan") + content.count("tracer.")
    score.trace_coverage = min((trace_calls / max(len(src_files), 1)) * 33, 100)

    # 4. 故障注入覆盖率：检查 error 路径测试
    error_tests = 0
    for f in test_files:
        content = f.read_text()
        error_tests += content.count("error") + content.count("timeout") + content.count("fault")
    score.fault_injection = min((error_tests / max(len(test_files), 1)) * 25, 100)

    # 5. 契约完备度：检查 schema 文件
    schema_files = list(module_path.rglob("*.schema.json")) + list(module_path.rglob("*.proto"))
    score.contract_completeness = min(len(schema_files) * 20, 100)

    return score

if __name__ == "__main__":
    module_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = analyze_go_module(module_path)

    print(f"\n{'='*50}")
    print(f"  Testability Scorecard: {module_path.name}")
    print(f"{'='*50}")
    print(f"  DI 覆盖率 (30%):        {result.di_coverage:.1f}")
    print(f"  Mock 可替换率 (25%):     {result.mock_rate:.1f}")
    print(f"  Trace 覆盖率 (20%):      {result.trace_coverage:.1f}")
    print(f"  故障注入覆盖率 (15%):    {result.fault_injection:.1f}")
    print(f"  契约完备度 (10%):        {result.contract_completeness:.1f}")
    print(f"{'='*50}")
    print(f"  总分: {result.total:.1f} / 100")
    print(f"  状态: {'✅ PASS' if result.passed else '❌ BLOCKED'}")
    print(f"{'='*50}\n")

    sys.exit(0 if result.passed else 1)
```

---

## 5. 工程实践：Playwright 前端可测试性验证

### 5.1 Agent UI 工具调用面板的 Schema Snapshot

```typescript
// tests/agent-ui/testability.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Agent UI Testability Verification', () => {
  test('tool call panel should expose structured data for testing', async ({ page }) => {
    await page.goto('/agent/chat');

    // 发送触发工具调用的消息
    await page.getByRole('textbox').fill('查询今天北京的天气');
    await page.getByRole('button', { name: '发送' }).click();

    // 等待工具调用面板渲染
    const toolPanel = page.locator('[data-testid="tool-call-panel"]');
    await expect(toolPanel).toBeVisible({ timeout: 15000 });

    // 验证面板暴露了结构化的测试钩子
    const toolName = toolPanel.locator('[data-testid="tool-name"]');
    await expect(toolName).toHaveText('weather_search');

    const toolInput = toolPanel.locator('[data-testid="tool-input"]');
    const inputJson = JSON.parse(await toolInput.textContent() || '{}');
    expect(inputJson).toHaveProperty('query');
    expect(inputJson.query).toContain('北京');

    // Snapshot 对比：确保 Schema 没有发生非预期变更
    const toolSchema = toolPanel.locator('[data-testid="tool-schema"]');
    await expect(toolSchema).toMatchAriaSnapshot(`
      - text: weather_search
      - text: query (string, required)
      - text: location (string, optional)
    `);
  });

  test('agent debug panel should expose trace IDs for backend correlation', async ({ page }) => {
    await page.goto('/agent/chat?debug=true');

    await page.getByRole('textbox').fill('帮我预约明天的会议室');
    await page.getByRole('button', { name: '发送' }).click();

    // 验证 Debug 面板暴露了 Trace ID（可测试性设计的关键）
    const debugPanel = page.locator('[data-testid="debug-panel"]');
    await expect(debugPanel).toBeVisible();

    const traceId = debugPanel.locator('[data-testid="trace-id"]');
    await expect(traceId).toHaveText(/^[a-f0-9]{32}$/);

    // 验证每个步骤都有 Span ID
    const spans = debugPanel.locator('[data-testid="span-item"]');
    await expect(spans).toHaveCount({ minimum: 3 }); // planner + tool + summarizer
  });
});
```

### 5.2 前端 Testability Checklist 自动化

```typescript
// tests/agent-ui/testability-checklist.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Frontend Testability Checklist', () => {
  test('all interactive elements must have data-testid', async ({ page }) => {
    await page.goto('/agent/chat');

    // 所有按钮必须有 data-testid
    const buttons = page.locator('button:not([data-testid])');
    const count = await buttons.count();
    expect(count).toBe(0); // 0 个缺失 = 满分

    // 所有输入框必须有 aria-label 或 data-testid
    const inputs = page.locator('input:not([data-testid]):not([aria-label])');
    expect(await inputs.count()).toBe(0);
  });

  test('agent response should have semantic HTML structure', async ({ page }) => {
    await page.goto('/agent/chat');
    await page.getByRole('textbox').fill('你好');
    await page.getByRole('button', { name: '发送' }).click();

    const response = page.locator('[data-testid="agent-response"]');
    await expect(response).toBeVisible({ timeout: 10000 });

    // 验证响应使用语义化标签（而非纯 div 嵌套）
    const hasSemanticStructure = await response.evaluate((el) => {
      const semanticTags = ['p', 'ul', 'ol', 'code', 'pre', 'h1', 'h2', 'h3'];
      return semanticTags.some(tag => el.querySelector(tag) !== null);
    });
    expect(hasSemanticStructure).toBe(true);
  });
});
```

---

## 6. 工程实践：K8s 环境中的 Testability 门禁

### 6.1 PR 门禁 Job

```yaml
# .github/workflows/testability-gate.yml
name: Testability Gate

on:
  pull_request:
    paths:
      - 'pkg/agent/**'
      - 'internal/orchestrator/**'

jobs:
  testability-scorecard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Calculate Testability Score
        run: |
          python3 scripts/testability_scorecard.py pkg/agent
          python3 scripts/testability_scorecard.py internal/orchestrator

      - name: Verify DI Pattern Compliance
        run: |
          # 检查所有 New* 构造函数是否接收接口参数
          grep -rn "func New" pkg/agent/ | while read line; do
            if ! echo "$line" | grep -q "interface\|Client\|Store\|Executor"; then
              echo "WARNING: $line may not use DI pattern"
            fi
          done

      - name: Check Replay Fixtures Freshness
        run: |
          # 确保 fixture 文件不超过 7 天
          find testdata/fixtures -name "*.json" -mtime +7 | while read f; do
            echo "STALE FIXTURE: $f (older than 7 days, needs refresh)"
          done

  contract-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - name: Detect Schema Changes
        run: |
          CHANGED=$(git diff HEAD~1 --name-only | grep -E '\.(schema\.json|proto)$' || true)
          if [ -n "$CHANGED" ]; then
            echo "Schema files changed, running contract tests..."
            go test -tags=contract ./pkg/agent/...
          fi
```

### 6.2 K8s CronJob：定期刷新 Replay Fixtures

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: refresh-replay-fixtures
  namespace: qa-automation
spec:
  schedule: "0 2 * * 1" # 每周一凌晨 2 点
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: fixture-refresher
              image: registry.internal/qa-tools:latest
              env:
                - name: REPLAY_MODE
                  value: "record"
                - name: LLM_API_KEY
                  valueFrom:
                    secretKeyRef:
                      name: llm-credentials
                      key: api-key
              command:
                - /bin/sh
                - -c
                - |
                  cd /workspace
                  git clone $REPO_URL .
                  go test -tags=e2e,replay -run TestRecordFixtures ./...
                  git add testdata/fixtures/
                  git commit -m "chore: refresh replay fixtures $(date +%Y%m%d)"
                  git push origin main
          restartPolicy: OnFailure
```

---

## 7. 质量左移 4 阶段实施路径

### 阶段 1：需求评审植入可测试性检查

```markdown
## 需求评审 Testability Checklist

- [ ] Agent 的外部依赖清单是否明确？（LLM / 工具 / 存储 / 第三方 API）
- [ ] 每个外部依赖是否有明确的失败模式和降级策略？
- [ ] 是否定义了可观测指标（Latency / Error Rate / Token Usage）？
- [ ] 是否有确定性测试策略（如何在不消耗真实 Token 的情况下验证？）
- [ ] 多租户隔离边界是否清晰？测试如何验证隔离性？
```

### 阶段 2：设计评审增加 Testability Scorecard

设计文档必须包含"可测试性章节"，说明：
- 所有接口定义（interface）
- Mock/Fake 实现方案
- 确定性回放策略
- 故障注入点清单

### 阶段 3：编码阶段强制 Test Hook

```go
// 每个模块必须暴露 TestHook 结构体
type AgentTestHooks struct {
    BeforeLLMCall  func(req *ChatRequest) *ChatRequest
    AfterLLMCall   func(resp *ChatResponse) *ChatResponse
    BeforeToolCall func(name string, input json.RawMessage) json.RawMessage
    AfterToolCall  func(name string, output json.RawMessage) json.RawMessage
    OnError        func(err error) error
}

func NewAgentCoreWithHooks(deps AgentDeps, hooks *AgentTestHooks) *AgentCore {
    return &AgentCore{deps: deps, hooks: hooks}
}
```

### 阶段 4：PR 门禁自动化校验

- 新增接口必须有对应 Mock 实现（lint 规则）
- 新增外部调用必须有 Trace Span（静态分析）
- 新增 API 必须有 JSON Schema 定义（CI check）
- Testability Score ≥ 60（自动计算）

---

## 8. 课后思考题

<callout icon="thought_balloon" bgc="6">

1. **DI 粒度选择**：如果 Agent 的 Planner 内部调用了 3 个不同的 LLM（一个用于意图识别、一个用于参数抽取、一个用于回复生成），你会设计成一个 `LLMClient` 接口还是三个？为什么？各自的测试利弊是什么？

2. **Fixture 漂移问题**：录制的 LLM Fixture 可能因为模型升级而"过时"（输出格式微变但语义不变），如何设计一种机制在保持确定性的同时容忍合理的语义漂移？

3. **可测试性 vs 复杂度权衡**：为每个组件都注入接口会增加代码复杂度（更多 interface、更多构造函数参数）。在一个快速迭代的创业团队中，你会如何设定"最小可测试性"标准？哪些维度可以暂缓、哪些必须从 Day 1 就做到？

4. **前端可测试性**：如果设计团队拒绝在 UI 组件上添加 `data-testid` 属性（认为"污染了生产代码"），你有哪些替代方案来保证 Playwright 测试的稳定性？

</callout>

---

## 9. 今日小结

<callout icon="star" bgc="4">

**核心收获**：

- 可测试性不是测试工程师的"额外要求"，而是架构质量的内在属性。不可测试的系统 = 不可信任的系统。
- **DI + 接口**是一切 Mock/Stub/Fake 的前提，是可测试性的地基。
- **确定性回放层**将 AI Agent 的"非确定性噩梦"转化为"确定性天堂"——每次 CI 运行结果完全一致。
- **Testability Scorecard** 将"可测试性"从主观感受变为客观指标，可以作为 PR 门禁强制执行。
- **质量左移的本质**：不是在流水线末端加更多测试，而是在流水线最前端消灭不可测试性。

**明日预告**：Day 38 将探讨 **AI Agent 线上质量巡检与异常检测**——如何在生产环境中持续监控 Agent 的行为质量，自动发现回归、漂移和异常。

</callout>
