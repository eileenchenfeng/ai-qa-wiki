---
title: "每日 AI 学习笔记｜Day 36：AI Agent 回归测试策略与智能用例筛选"
date: 2026-05-21
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, regression-testing, intelligent-selection, SDET, Ginkgo, Playwright, K8s, test-impact-analysis, risk-scoring]
---
# 每日 AI 学习笔记｜Day 36：AI Agent 回归测试策略与智能用例筛选

AI Agent 系统的迭代速度极快——Prompt 模板、工具定义、模型版本、编排逻辑可能每天都在变——但全量回归测试的成本（时间 + Token + 基础设施）线性增长。本篇聚焦如何在"速度"与"信心"之间取得最优平衡：通过 Test Impact Analysis（TIA）、风险评分模型、变更感知路由三大核心机制，让每次 CI/CD 只跑"必须跑的"用例，同时保证覆盖率不降级。结合 Ginkgo Label + Decorator 分层选择器、Playwright Tag Filter、K8s Job 弹性编排三套工程实践，给出可直接落地的代码方案。

{/* truncate */}

## 0. 核心总结

<callout icon="star" bgc="4">

**本篇核心要点：**

1. **全量回归不可持续**：AI Agent 每条用例平均消耗 0.5-2s + 数千 Token，500 条全量回归意味着 10min+ 执行时间和 \$5-20 Token 成本，必须引入智能筛选。
2. **Test Impact Analysis (TIA)**：通过代码变更 → 依赖图 → 影响用例的映射关系，将回归范围缩减 60-80%。
3. **风险评分模型**：基于历史失败率、变更频率、业务优先级、最后执行距今天数四个维度对每条用例打分，Top-N 优先执行。
4. **变更感知路由**：Prompt 变更 → 仅跑语义回归；工具 Schema 变更 → 仅跑契约 + 集成测试；模型版本变更 → 跑 Eval 基线对比。
5. **Ginkgo Label 选择器**：利用 `Label("layer", "e2e")` + `--label-filter` 实现 CI 中按风险层级动态选用例。
6. **Playwright Tag Filter**：`@regression-p0` / `@smoke` 标签配合 `--grep` 实现前端回归分层。
7. **K8s Job 弹性编排**：高风险用例并行度拉满（`parallelism: 10`），低风险用例串行节省资源。
8. **覆盖率守门员**：每次 TIA 筛选后，自动校验"被跳过的用例最近 7 天内至少执行过一次"，否则强制纳入本次回归。

</callout>

## 1. 核心理论

### 1.1 为什么 AI Agent 回归测试需要智能筛选

| 维度 | 传统服务 | AI Agent |
|------|---------|----------|
| 用例执行成本 | 毫秒级 API 调用 | 秒级（模型推理 + 多轮交互） |
| Token 成本 | 无 | 每条用例消耗数千 Token |
| 输出确定性 | 确定 | 非确定性，需要多次采样验证 |
| 变更面 | 代码 + 配置 | 代码 + Prompt + 模型版本 + 工具定义 + 向量库 |
| 全量回归频率 | 每次 MR | 不现实，需分层执行 |

### 1.2 三层智能筛选架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline Trigger                        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Change Detection (变更检测)                            │
│  ├── Code diff → affected packages                              │
│  ├── Prompt diff → affected scenarios                           │
│  ├── Model version bump → eval baseline                         │
│  └── Tool schema diff → contract tests                          │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Test Impact Analysis (影响分析)                        │
│  ├── Dependency Graph: package → test file mapping              │
│  ├── Prompt-Scenario Matrix: prompt_id → test_ids               │
│  └── Tool-Integration Map: tool_name → integration_tests        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Risk-Based Prioritization (风险优先级排序)              │
│  ├── Historical failure rate (近30天)                            │
│  ├── Change frequency (该模块本周被改几次)                        │
│  ├── Business priority (P0/P1/P2)                               │
│  └── Staleness (距离上次执行天数)                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 变更类型 → 测试策略路由

| 变更类型 | 触发的测试子集 | 预期耗时 |
|---------|--------------|---------|
| Prompt 模板修改 | 语义回归（Eval Metric 对比） | 2-5min |
| 工具 Schema 变更 | 契约测试 + 集成测试 | 1-3min |
| 编排逻辑代码变更 | 单元测试 + 链路测试 | 30s-2min |
| 模型版本升级 | 全量 Eval 基线对比 + P0 E2E | 10-20min |
| Memory/向量库 Schema 迁移 | Memory 读写测试 + 回放测试 | 3-5min |
| 前端 UI 变更 | Playwright 视觉回归 + 交互测试 | 3-8min |

## 2. 工程实践

### 2.1 Ginkgo 标签分层选择器（Golang）

```go
package regression_test

import (
    "os"
    "testing"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

func TestRegression(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "AI Agent Regression Suite")
}

// Label 分层：smoke < regression-p0 < regression-p1 < regression-full
var _ = Describe("Agent Chat Regression", Label("module:chat"), func() {

    Context("核心对话能力", Label("layer:smoke", "priority:p0"), func() {
        It("单轮问答应返回有效响应", Label("change:prompt", "change:model"), func() {
            // 无论什么变更都必须跑的最小集
            resp := sendChat("你好，请介绍一下你自己")
            Expect(resp.StatusCode).To(Equal(200))
            Expect(resp.Content).NotTo(BeEmpty())
            Expect(len(resp.Content)).To(BeNumerically(">", 10))
        })

        It("多轮对话上下文保持", Label("change:prompt", "change:memory"), func() {
            sessionID := createSession()
            sendChat("我叫张三", WithSession(sessionID))
            resp := sendChat("我叫什么名字？", WithSession(sessionID))
            Expect(resp.Content).To(ContainSubstring("张三"))
        })
    })

    Context("工具调用回归", Label("layer:regression-p0", "priority:p0"), func() {
        It("天气查询工具正确路由", Label("change:tool-schema"), func() {
            resp := sendChat("北京今天天气怎么样？")
            Expect(resp.ToolCalls).To(HaveLen(1))
            Expect(resp.ToolCalls[0].Name).To(Equal("get_weather"))
            Expect(resp.ToolCalls[0].Args).To(HaveKey("city"))
        })
    })

    Context("多租户隔离回归", Label("layer:regression-p1", "priority:p1"), func() {
        It("租户A无法访问租户B的会话", Label("change:code"), func() {
            sessionB := createSessionAs("tenant-B")
            resp := getSessionAs("tenant-A", sessionB)
            Expect(resp.StatusCode).To(Equal(403))
        })
    })
})
```

**CI 中动态选择用例：**

```bash
# Smoke（每次 commit 必跑，<30s）
ginkgo --label-filter="layer:smoke" ./...

# P0 回归（MR 合入时，<3min）
ginkgo --label-filter="priority:p0" ./...

# 仅 Prompt 相关变更
ginkgo --label-filter="change:prompt" ./...

# 仅工具 Schema 相关变更
ginkgo --label-filter="change:tool-schema" ./...

# 全量回归（每日定时，10-20min）
ginkgo --label-filter="layer:regression-full || layer:regression-p0 || layer:regression-p1" ./...
```

### 2.2 Test Impact Analysis 引擎（Golang）

```go
package tia

import (
    "encoding/json"
    "os"
    "os/exec"
    "strings"
)

// DependencyMap 记录包 → 测试文件的映射关系
type DependencyMap struct {
    PackageToTests map[string][]string `json:"package_to_tests"`
    PromptToTests  map[string][]string `json:"prompt_to_tests"`
    ToolToTests    map[string][]string `json:"tool_to_tests"`
}

// ChangeSet 代表本次 MR 的变更集
type ChangeSet struct {
    ModifiedPackages []string `json:"modified_packages"`
    ModifiedPrompts  []string `json:"modified_prompts"`
    ModifiedTools    []string `json:"modified_tools"`
    ModelBump        bool     `json:"model_bump"`
}

// SelectTests 根据变更集计算需要执行的测试文件
func SelectTests(depMap *DependencyMap, changes *ChangeSet) []string {
    selected := make(map[string]bool)

    // 代码变更 → 影响的测试
    for _, pkg := range changes.ModifiedPackages {
        for _, test := range depMap.PackageToTests[pkg] {
            selected[test] = true
        }
    }

    // Prompt 变更 → 语义回归测试
    for _, prompt := range changes.ModifiedPrompts {
        for _, test := range depMap.PromptToTests[prompt] {
            selected[test] = true
        }
    }

    // 工具 Schema 变更 → 契约测试
    for _, tool := range changes.ModifiedTools {
        for _, test := range depMap.ToolToTests[tool] {
            selected[test] = true
        }
    }

    // 模型版本升级 → 全量 Eval
    if changes.ModelBump {
        for _, tests := range depMap.PackageToTests {
            for _, t := range tests {
                selected[t] = true
            }
        }
    }

    result := make([]string, 0, len(selected))
    for t := range selected {
        result = append(result, t)
    }
    return result
}

// DetectChanges 从 git diff 解析变更集
func DetectChanges(baseBranch string) (*ChangeSet, error) {
    cmd := exec.Command("git", "diff", "--name-only", baseBranch+"...HEAD")
    out, err := cmd.Output()
    if err != nil {
        return nil, err
    }

    cs := &ChangeSet{}
    for _, file := range strings.Split(string(out), "\n") {
        file = strings.TrimSpace(file)
        switch {
        case strings.HasPrefix(file, "prompts/"):
            cs.ModifiedPrompts = append(cs.ModifiedPrompts, file)
        case strings.HasPrefix(file, "tools/") && strings.HasSuffix(file, ".json"):
            cs.ModifiedTools = append(cs.ModifiedTools, file)
        case strings.Contains(file, "model_config"):
            cs.ModelBump = true
        case strings.HasSuffix(file, ".go"):
            pkg := file[:strings.LastIndex(file, "/")]
            cs.ModifiedPackages = append(cs.ModifiedPackages, pkg)
        }
    }
    return cs, nil
}
```

### 2.3 风险评分模型（Python）

```python
"""
Risk-Based Test Prioritization Engine
根据历史数据对测试用例进行风险评分，输出优先级排序
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class TestCase:
    id: str
    name: str
    labels: list[str]
    priority: str  # p0, p1, p2
    last_run: datetime
    recent_failures: int  # 近30天失败次数
    recent_runs: int      # 近30天运行次数
    module_change_freq: int  # 该模块本周变更次数

@dataclass
class RiskScore:
    test_id: str
    score: float
    breakdown: dict

def calculate_risk_score(tc: TestCase, now: datetime = None) -> RiskScore:
    """
    四维风险评分模型：
    - failure_rate (0-40分)：历史失败率越高越优先
    - change_freq (0-25分)：模块变更越频繁越优先
    - priority_weight (0-20分)：业务优先级权重
    - staleness (0-15分)：距上次执行越久越优先
    """
    now = now or datetime.now()
    
    # 维度1：历史失败率 (权重 40%)
    failure_rate = tc.recent_failures / max(tc.recent_runs, 1)
    failure_score = min(failure_rate * 100, 40.0)
    
    # 维度2：模块变更频率 (权重 25%)
    change_score = min(tc.module_change_freq * 5, 25.0)
    
    # 维度3：业务优先级 (权重 20%)
    priority_map = {"p0": 20.0, "p1": 12.0, "p2": 5.0}
    priority_score = priority_map.get(tc.priority, 5.0)
    
    # 维度4：新鲜度/陈旧度 (权重 15%)
    days_since_run = (now - tc.last_run).days
    staleness_score = min(days_since_run * 2, 15.0)
    
    total = failure_score + change_score + priority_score + staleness_score
    
    return RiskScore(
        test_id=tc.id,
        score=total,
        breakdown={
            "failure_rate": round(failure_score, 2),
            "change_freq": round(change_score, 2),
            "priority": round(priority_score, 2),
            "staleness": round(staleness_score, 2),
        }
    )

def select_top_n(test_cases: list[TestCase], n: int) -> list[RiskScore]:
    """选取风险评分最高的 N 条用例"""
    scores = [calculate_risk_score(tc) for tc in test_cases]
    scores.sort(key=lambda s: s.score, reverse=True)
    return scores[:n]

# 示例用法
if __name__ == "__main__":
    cases = [
        TestCase("tc_001", "核心对话", ["smoke"], "p0",
                 datetime.now() - timedelta(days=1), 3, 30, 4),
        TestCase("tc_002", "工具调用", ["regression-p0"], "p0",
                 datetime.now() - timedelta(days=3), 5, 20, 2),
        TestCase("tc_003", "多租户隔离", ["regression-p1"], "p1",
                 datetime.now() - timedelta(days=7), 0, 10, 0),
        TestCase("tc_004", "历史记录导出", ["regression-p2"], "p2",
                 datetime.now() - timedelta(days=14), 1, 5, 1),
    ]
    
    top = select_top_n(cases, n=3)
    for s in top:
        print(f"  {s.test_id}: score={s.score:.1f} | {s.breakdown}")
```

### 2.4 Playwright 标签过滤与分层回归（TypeScript）

```typescript
// tests/regression/agent-chat.spec.ts
import { test, expect } from '@playwright/test';

// 标签通过 test.describe 或 test() 的 tag 选项标记
test.describe('Agent 对话回归 @regression-p0', () => {
  
  test('单轮对话基本可用 @smoke @change-prompt', async ({ page }) => {
    await page.goto('/chat');
    await page.getByPlaceholder('输入消息').fill('你好');
    await page.getByRole('button', { name: '发送' }).click();
    
    // 等待 Agent 响应
    const response = page.locator('.message-bubble.agent').last();
    await expect(response).toBeVisible({ timeout: 30000 });
    await expect(response).not.toHaveText('');
    
    // 语义校验：回复应包含问候相关内容
    const text = await response.textContent();
    expect(text!.length).toBeGreaterThan(5);
  });

  test('工具调用结果正确渲染 @regression-p0 @change-tool', async ({ page }) => {
    await page.goto('/chat');
    await page.getByPlaceholder('输入消息').fill('帮我查一下北京天气');
    await page.getByRole('button', { name: '发送' }).click();
    
    // 工具调用卡片应出现
    const toolCard = page.locator('[data-testid="tool-call-card"]');
    await expect(toolCard).toBeVisible({ timeout: 30000 });
    await expect(toolCard).toContainText('天气');
  });

  test('对话历史持久化 @regression-p1 @change-memory', async ({ page }) => {
    await page.goto('/chat');
    
    // 第一轮
    await page.getByPlaceholder('输入消息').fill('记住我的名字是测试员');
    await page.getByRole('button', { name: '发送' }).click();
    await page.locator('.message-bubble.agent').last().waitFor();
    
    // 刷新页面模拟重新进入
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // 第二轮验证记忆
    await page.getByPlaceholder('输入消息').fill('我叫什么名字？');
    await page.getByRole('button', { name: '发送' }).click();
    
    const response = page.locator('.message-bubble.agent').last();
    await expect(response).toContainText('测试员', { timeout: 30000 });
  });
});
```

**Playwright 分层执行命令：**

```bash
# Smoke（每次 commit）
npx playwright test --grep "@smoke"

# P0 回归（MR 合入）
npx playwright test --grep "@regression-p0"

# 仅 Prompt 相关
npx playwright test --grep "@change-prompt"

# 全量回归（每日定时）
npx playwright test --grep "@regression"
```

### 2.5 K8s Job 弹性回归编排

```yaml
# regression-job-template.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: agent-regression-${RUN_ID}
  namespace: qa-regression
  labels:
    app: agent-regression
    risk-tier: ${RISK_TIER}  # high / medium / low
spec:
  # 高风险用例：并行拉满快速出结果
  # 低风险用例：串行节省资源
  parallelism: ${PARALLELISM}  # high=10, medium=5, low=1
  completions: ${TOTAL_SHARDS}
  backoffLimit: 2
  activeDeadlineSeconds: 1200  # 20min 超时熔断
  template:
    metadata:
      labels:
        app: agent-regression
    spec:
      restartPolicy: Never
      containers:
        - name: ginkgo-runner
          image: registry.internal/qa/ginkgo-runner:latest
          env:
            - name: LABEL_FILTER
              value: "${LABEL_FILTER}"
            - name: SHARD_INDEX
              valueFrom:
                fieldRef:
                  fieldPath: metadata.annotations['batch.kubernetes.io/job-completion-index']
            - name: TOTAL_SHARDS
              value: "${TOTAL_SHARDS}"
          command:
            - /bin/sh
            - -c
            - |
              ginkgo --label-filter="${LABEL_FILTER}" \
                     --procs=4 \
                     --output-dir=/results \
                     --json-report=report-${SHARD_INDEX}.json \
                     ./tests/...
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
          volumeMounts:
            - name: results
              mountPath: /results
      volumes:
        - name: results
          emptyDir: {}
```

### 2.6 覆盖率守门员：防止用例被永久跳过

```go
package coverage_guard

import (
    "fmt"
    "time"
)

type TestExecution struct {
    TestID    string
    LastRunAt time.Time
    Result    string // pass, fail, skip
}

type CoverageGuard struct {
    MaxStaleDays int // 用例最多允许几天不执行
    executions   map[string]*TestExecution
}

func NewCoverageGuard(maxStaleDays int) *CoverageGuard {
    return &CoverageGuard{
        MaxStaleDays: maxStaleDays,
        executions:   make(map[string]*TestExecution),
    }
}

// LoadHistory 加载历史执行记录
func (cg *CoverageGuard) LoadHistory(records []TestExecution) {
    for i := range records {
        existing, ok := cg.executions[records[i].TestID]
        if !ok || records[i].LastRunAt.After(existing.LastRunAt) {
            cg.executions[records[i].TestID] = &records[i]
        }
    }
}

// EnforceMinCoverage 检查被 TIA 跳过的用例是否超过新鲜度阈值
// 返回必须强制纳入本次回归的用例列表
func (cg *CoverageGuard) EnforceMinCoverage(
    allTests []string,
    selectedByTIA []string,
) []string {
    selectedSet := make(map[string]bool)
    for _, t := range selectedByTIA {
        selectedSet[t] = true
    }

    now := time.Now()
    var forced []string

    for _, testID := range allTests {
        if selectedSet[testID] {
            continue // 已被 TIA 选中，无需强制
        }

        exec, ok := cg.executions[testID]
        if !ok {
            // 从未执行过，必须纳入
            forced = append(forced, testID)
            continue
        }

        staleDays := int(now.Sub(exec.LastRunAt).Hours() / 24)
        if staleDays > cg.MaxStaleDays {
            forced = append(forced, testID)
            fmt.Printf("[CoverageGuard] 强制纳入 %s (已 %d 天未执行)\n",
                testID, staleDays)
        }
    }
    return forced
}
```

### 2.7 CI Pipeline 集成示例（GitHub Actions）

```yaml
# .github/workflows/smart-regression.yml
name: Smart Regression

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # 每日凌晨全量回归

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      label_filter: ${{ steps.tia.outputs.label_filter }}
      risk_tier: ${{ steps.tia.outputs.risk_tier }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Run Test Impact Analysis
        id: tia
        run: |
          if [ "${{ github.event_name }}" == "schedule" ]; then
            # 定时任务：全量回归
            echo "label_filter=layer:regression-full || layer:regression-p0 || layer:regression-p1 || layer:smoke" >> $GITHUB_OUTPUT
            echo "risk_tier=full" >> $GITHUB_OUTPUT
          else
            # MR 触发：智能筛选
            CHANGES=$(go run ./cmd/tia detect --base=origin/main)
            FILTER=$(go run ./cmd/tia select --changes="$CHANGES")
            echo "label_filter=$FILTER" >> $GITHUB_OUTPUT
            echo "risk_tier=selective" >> $GITHUB_OUTPUT
          fi

  run-regression:
    needs: detect-changes
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      
      - name: Run Ginkgo with label filter
        run: |
          go install github.com/onsi/ginkgo/v2/ginkgo@latest
          ginkgo --label-filter="${{ needs.detect-changes.outputs.label_filter }}" \
                 --json-report=regression-report.json \
                 --timeout=20m \
                 ./tests/...
      
      - name: Coverage Guard Check
        if: needs.detect-changes.outputs.risk_tier == 'selective'
        run: |
          go run ./cmd/coverage-guard check \
            --report=regression-report.json \
            --max-stale-days=7 \
            --all-tests=./tests/...
      
      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: regression-report
          path: regression-report.json
```

## 3. 最佳实践清单

| 实践 | 说明 | 收益 |
|------|------|------|
| Label 分层 | smoke / p0 / p1 / full 四级 | 每次 MR 仅跑 20% 用例 |
| 变更路由 | prompt→语义/tool→契约/code→单元 | 精准匹配变更类型 |
| 风险评分 | 4 维模型自动排序 | 优先发现高风险缺陷 |
| 覆盖率守门 | 7 天未执行自动纳入 | 防止盲区 |
| 并行编排 | K8s Job + Shard | 高风险用例 3min 出结果 |
| 定时全量 | 每日凌晨 cron | 兜底覆盖 |

## 4. 课后思考题

1. **TIA 精度问题**：如果 Prompt 模板中引用了其他 Prompt（类似 include/import），你的依赖图如何处理这种传递依赖？请设计一个 Prompt 依赖解析器。
2. **风险评分调参**：四个维度的权重（40/25/20/15）在你的项目中是否合理？如何通过历史数据（Logistic Regression / Bayesian Optimization）自动调优这些权重？
3. **非确定性处理**：AI Agent 用例天然有概率性失败（flaky），如何在风险评分模型中区分"真实回归"和"概率性波动"？提示：考虑引入连续失败次数和采样方差。
4. **Token 预算约束**：如果你的团队每日 Token 预算为 \$50，如何设计一个贪心算法在预算内最大化风险覆盖率？

## 5. 今日小结

本篇系统阐述了 AI Agent 回归测试的智能筛选策略：

- **变更检测层**识别"什么变了"（代码/Prompt/模型/工具）
- **影响分析层**计算"影响了哪些测试"（依赖图映射）
- **风险排序层**决定"先跑哪些"（四维评分模型）
- **覆盖率守门员**保证"没有盲区"（7天新鲜度约束）

核心原则：**每次回归都应该是有目的的——知道为什么跑、为什么跳过、跳过的风险是否可控。** 盲目全量回归是资源浪费，盲目裁剪是风险敞口，唯有数据驱动的智能筛选才能在 AI Agent 快速迭代的节奏下保持质量信心。

> 明日预告：Day 37 将探讨 **AI Agent 可观测性驱动测试（Observability-Driven Testing）**——如何利用生产环境的 Trace/Metric/Log 数据反向生成测试用例、发现测试盲区、驱动回归优先级更新。
