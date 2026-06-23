---
title: "每日 AI 学习笔记｜Day 31：AI Agent 质量 SLO 与发布评分卡"
date: 2026-05-16
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, reliability, Automation, Kubernetes, Ginkgo, Playwright]
---

# 每日 AI 学习笔记 Day 31｜AI Agent 质量 SLO 与发布评分卡

**核心总结：** AI Agent 质量运营不能停留在“今天自动化有没有通过”这一层。对面向真实用户任务的 Agent 产品来说，质量目标必须被表达成一组可度量、可追踪、可阻断发布的 **Quality SLO**：用户任务成功率、关键链路 P95/P99、工具调用正确率、安全拦截有效性、审计完整率、降级成功率与回归失败恢复时长。Senior SDET 的价值，是把这些指标从观测平台里的孤立曲线，转化为能服务发布决策的 **质量评分卡**。评分卡不是为了给团队打分，而是为了回答一个更关键的问题：当前版本是否值得继续向用户放量？如果昨天我们解决的是“失败以后如何归因”，今天要解决的就是“发布之前如何量化风险，并让风险自动进入 go/no-go 决策”。

{/* truncate */}

## 0. 今日目标

今天的主题是 AI Agent 质量 SLO 与发布评分卡。完成今天的学习后，你应该能够做到四件事。第一，能从用户 E2E 任务出发，设计一组适合 Agent 产品的质量 SLI/SLO，而不是只沿用传统接口可用率。第二，能把 API、Ginkgo、Playwright、K8s 与 Trace 证据汇总为一个 release scorecard。第三，能编写可运行的 Demo，模拟 Agent 运行结果、采集质量信号，并自动计算发布风险等级。第四，能把质量评分卡接入 CI/CD、灰度发布与每日质量复盘，形成持续运营闭环。

本篇内容面向已经具备 Golang Ginkgo、Python Playwright、Kubernetes 与 API Testing 经验的资深测试开发。重点不是讲“指标越多越好”，而是把指标设计成可以真实影响发布的工程合同。

---

## 1. 核心理论：Agent 质量 SLO 必须从用户任务闭环定义

### 1.1 为什么传统服务 SLO 不足以衡量 Agent 质量

传统后端服务的 SLO 通常围绕可用率、错误率与延迟展开。例如 HTTP 5xx 比例低于 0.1%，P95 延迟低于 300ms，服务可用率达到 99.9%。这些指标对基础服务非常重要，但放到 AI Agent 场景里，会出现一个典型盲区：**系统技术上可用，但用户任务没有成功完成**。

一个 Agent 可能所有接口都返回 200，模型也成功输出了文本，但最终仍然是质量失败。比如用户要求“分析本次发布风险并生成阻断建议”，Agent 只生成了一段泛泛总结；或者工具调用成功，但漏掉了关键环境；或者页面正常展示，但缺少审计事件，导致后续无法追责。传统服务 SLO 会认为这次链路成功，而用户视角的 E2E 质量已经失败。

因此，Agent 质量 SLO 的定义必须从“服务是否存活”升级为“用户任务是否以可信、合规、可观测的方式完成”。这也是测试开发在 Agent 时代需要转变的核心思维。

### 1.2 SLI、SLO 与 Error Budget 在 Agent 场景下如何落地

SLI 是服务质量指标，描述我们如何测量质量；SLO 是服务质量目标，描述我们承诺达到什么水平；Error Budget 是允许失败的预算，描述在一个周期内可以承受多少质量损耗。

在 Agent 场景下，这三个概念可以这样理解。SLI 不是单一的 `http_success_rate`，而是任务级别的 `task_success_rate`、`tool_correctness_rate`、`grounded_answer_rate`、`policy_violation_escape_rate`、`trace_completeness_rate`。SLO 也不是简单地写成“服务 99.9% 可用”，而是要声明 Gold 场景中 99% 的任务必须完成，P95 端到端耗时不超过阈值，关键审计字段完整率达到 100%，安全绕过率为 0。

Error Budget 则是发布节奏的约束器。当预算被消耗过快，团队应该减少新能力上线，优先修复质量债；当预算充足，团队可以更积极地灰度新模型、新工具或新 Prompt。这样，质量不再只是发布前的一次性检查，而是持续影响工程节奏的运营机制。

### 1.3 Agent 质量评分卡的目标不是“统计”，而是“决策”

很多质量看板会展示大量指标，但发布负责人仍然很难判断是否可以上线。问题通常不是缺少数据，而是数据没有被组织成决策语言。

一个可落地的 Agent 质量评分卡至少要回答下面五个问题。

1. **用户任务是否成功**：Gold E2E 场景通过率是否达到门禁要求。
2. **失败是否可解释**：失败是否已经被归因到明确 bucket，并具备证据链。
3. **质量风险是否可接受**：延迟、工具正确率、召回质量、安全拦截是否处于 SLO 内。
4. **观测证据是否完整**：trace、audit、session、tool call 与 K8s 运行时证据是否足够支撑复盘。
5. **发布动作是什么**：continue、canary only、manual review、block release，还是 rollback。

评分卡的价值不在于展示更多图，而在于让自动化系统直接输出 go/no-go 建议。

---

## 2. SLO 设计：为 Agent E2E 链路建立质量指标体系

### 2.1 推荐的质量 SLI/SLO 分层

Agent 质量指标建议按 E2E 链路分为五层：任务成功、智能质量、工具可靠性、安全合规、可观测性。每一层都要能被自动化采集，并最终进入发布评分卡。

<table header-row="true" header-col="false" col-widths="160,230,210,280">
  <tr>
    <td>质量层</td>
    <td>典型 SLI</td>
    <td>建议 SLO</td>
    <td>发布含义</td>
  </tr>
  <tr>
    <td>任务成功</td>
    <td>`task_success_rate`、`golden_path_pass_rate`</td>
    <td>Gold 场景 ≥ 99%，关键回归 100%</td>
    <td>用户核心任务是否真正完成</td>
  </tr>
  <tr>
    <td>智能质量</td>
    <td>`grounded_answer_rate`、`required_field_coverage`</td>
    <td>关键字段覆盖率 ≥ 98%</td>
    <td>结果是否可信、完整、可执行</td>
  </tr>
  <tr>
    <td>工具可靠性</td>
    <td>`tool_success_rate`、`tool_p95_latency_ms`</td>
    <td>关键工具成功率 ≥ 99.5%</td>
    <td>Agent 编排链路是否稳定</td>
  </tr>
  <tr>
    <td>安全合规</td>
    <td>`policy_escape_count`、`audit_completeness_rate`</td>
    <td>安全绕过为 0，审计完整率 100%</td>
    <td>是否允许继续放量</td>
  </tr>
  <tr>
    <td>可观测性</td>
    <td>`trace_completeness_rate`、`triage_coverage_rate`</td>
    <td>Trace 完整率 ≥ 99%，失败归因覆盖 ≥ 95%</td>
    <td>失败后是否可定位、可复盘</td>
  </tr>
</table>

这个表格里最重要的是“发布含义”。如果一个指标无法影响发布动作，它就应该留在观测看板，而不是进入发布评分卡。

### 2.2 质量评分建议：分数只是表达方式，规则才是核心

可以给每个维度设置权重，最终计算 0 到 100 的质量分。但不要让分数掩盖硬性红线。比如安全绕过、审计缺失、Gold 场景失败这类问题，即使总分仍然很高，也必须直接阻断发布。

推荐使用“硬门禁 + 加权评分”的组合模型。硬门禁用于不可妥协的风险，例如 P0 场景失败、安全绕过、审计缺失、跨租户数据泄露。加权评分用于衡量可接受风险，例如 P95 延迟轻微升高、非核心场景少量失败、部分 triage 证据缺失。

一个简单的规则可以是：如果存在 hard blocker，发布状态为 `block`；如果无 hard blocker 且总分 ≥ 90，状态为 `continue`；如果总分在 80 到 90 之间，状态为 `canary_only`；如果总分低于 80，状态为 `manual_review` 或 `block`。

### 2.3 Scorecard Contract 示例

下面是一份最小可用的质量评分卡合同。它适合作为 CI 产物、发布门禁输入、飞书通知内容和每日质量复盘的数据源。

```json
{
  "release_id": "agent-release-2026-05-16",
  "environment": "staging",
  "window": "24h",
  "score": 91,
  "decision": "continue",
  "hard_blockers": [],
  "sli": {
    "task_success_rate": 0.992,
    "golden_path_pass_rate": 1.0,
    "tool_success_rate": 0.997,
    "p95_e2e_latency_ms": 8420,
    "audit_completeness_rate": 1.0,
    "trace_completeness_rate": 0.995,
    "triage_coverage_rate": 0.966,
    "policy_escape_count": 0
  },
  "evidence": {
    "ginkgo_report": "reports/ginkgo-agent-slo.json",
    "playwright_report": "reports/playwright-agent-e2e.json",
    "k8s_namespace": "agent-quality-gates",
    "trace_query": "service=agent-runtime release=2026-05-16"
  },
  "recommendation": "Continue rollout. Keep monitoring tool latency budget during canary."
}
```

这个 contract 的关键点是：它把“质量状态”变成了可被机器消费的结构化对象，而不是散落在多个测试报告里的文字结论。

---

## 3. 工程实践一：构建可运行的 Agent SLO Demo 服务

下面的 Demo 模拟一个 Agent 质量采集服务。它可以创建不同场景的 Agent run，并输出 quality scorecard。真实系统中这些数据会来自 trace、audit、tool call、Ginkgo、Playwright 与 K8s 事件；Demo 中用内存数据模拟，方便本地运行和理解。

安装依赖：

```bash
pip install fastapi uvicorn pydantic
```

保存为 `agent_quality_slo_demo.py`：

```python
import statistics
import time
import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Agent Quality SLO Demo")
RUNS: Dict[str, dict] = {}


class CreateRunRequest(BaseModel):
    scenario: str
    task: str
    tenant_id: str = "tenant-a"


class SloThreshold(BaseModel):
    min_task_success_rate: float = 0.98
    min_tool_success_rate: float = 0.995
    max_p95_latency_ms: int = 10000
    min_audit_completeness_rate: float = 1.0
    min_trace_completeness_rate: float = 0.99
    max_policy_escape_count: int = 0


def build_run(request: CreateRunRequest) -> dict:
    scenario_profile = {
        "happy_path": {
            "status": "succeeded",
            "latency_ms": 4200,
            "tool_status": "succeeded",
            "audit_present": True,
            "trace_complete": True,
            "policy_escape": False,
            "required_fields": ["summary", "risk", "owner", "next_action"],
        },
        "slow_tool": {
            "status": "succeeded",
            "latency_ms": 12800,
            "tool_status": "succeeded",
            "audit_present": True,
            "trace_complete": True,
            "policy_escape": False,
            "required_fields": ["summary", "risk", "owner", "next_action"],
        },
        "tool_failed": {
            "status": "failed",
            "latency_ms": 7600,
            "tool_status": "failed",
            "audit_present": True,
            "trace_complete": True,
            "policy_escape": False,
            "required_fields": ["summary", "risk"],
        },
        "audit_missing": {
            "status": "succeeded",
            "latency_ms": 5100,
            "tool_status": "succeeded",
            "audit_present": False,
            "trace_complete": True,
            "policy_escape": False,
            "required_fields": ["summary", "risk", "owner", "next_action"],
        },
        "unsafe_escape": {
            "status": "succeeded",
            "latency_ms": 4800,
            "tool_status": "succeeded",
            "audit_present": True,
            "trace_complete": True,
            "policy_escape": True,
            "required_fields": ["summary", "risk", "owner", "next_action"],
        },
    }.get(request.scenario)

    if scenario_profile is None:
        scenario_profile = {
            "status": "failed",
            "latency_ms": 9000,
            "tool_status": "failed",
            "audit_present": False,
            "trace_complete": False,
            "policy_escape": False,
            "required_fields": [],
        }

    run_id = f"run-{uuid.uuid4().hex[:10]}"
    run = {
        "run_id": run_id,
        "trace_id": f"trace-{uuid.uuid4().hex[:10]}",
        "task": request.task,
        "tenant_id": request.tenant_id,
        "scenario": request.scenario,
        "created_at": int(time.time()),
        **scenario_profile,
    }
    RUNS[run_id] = run
    return run


def percentile_95(values: List[int]) -> int:
    if not values:
        return 0
    if len(values) == 1:
        return values[0]
    ordered_values = sorted(values)
    percentile_index = int(round((len(ordered_values) - 1) * 0.95))
    return ordered_values[percentile_index]


def build_scorecard(threshold: SloThreshold) -> dict:
    runs = list(RUNS.values())
    total_runs = len(runs)
    if total_runs == 0:
        return {
            "score": 0,
            "decision": "manual_review",
            "hard_blockers": ["no_quality_data"],
            "sli": {},
            "recommendation": "No quality data was collected. Block release until E2E evidence exists.",
        }

    successful_runs = [run for run in runs if run["status"] == "succeeded"]
    successful_tools = [run for run in runs if run["tool_status"] == "succeeded"]
    audit_complete_runs = [run for run in runs if run["audit_present"]]
    trace_complete_runs = [run for run in runs if run["trace_complete"]]
    policy_escape_count = len([run for run in runs if run["policy_escape"]])
    latency_values = [run["latency_ms"] for run in runs]

    task_success_rate = len(successful_runs) / total_runs
    tool_success_rate = len(successful_tools) / total_runs
    audit_completeness_rate = len(audit_complete_runs) / total_runs
    trace_completeness_rate = len(trace_complete_runs) / total_runs
    p95_latency_ms = percentile_95(latency_values)

    hard_blockers: List[str] = []
    if policy_escape_count > threshold.max_policy_escape_count:
        hard_blockers.append("policy_escape_detected")
    if audit_completeness_rate < threshold.min_audit_completeness_rate:
        hard_blockers.append("audit_incomplete")
    if task_success_rate < threshold.min_task_success_rate:
        hard_blockers.append("task_success_slo_breached")

    score = 100
    score -= max(0, int((threshold.min_task_success_rate - task_success_rate) * 100))
    score -= max(0, int((threshold.min_tool_success_rate - tool_success_rate) * 80))
    score -= max(0, int((p95_latency_ms - threshold.max_p95_latency_ms) / 500))
    score -= max(0, int((threshold.min_trace_completeness_rate - trace_completeness_rate) * 50))
    score = max(0, min(score, 100))

    if hard_blockers:
        decision = "block"
    elif score >= 90:
        decision = "continue"
    elif score >= 80:
        decision = "canary_only"
    else:
        decision = "manual_review"

    return {
        "score": score,
        "decision": decision,
        "hard_blockers": hard_blockers,
        "sli": {
            "total_runs": total_runs,
            "task_success_rate": round(task_success_rate, 4),
            "tool_success_rate": round(tool_success_rate, 4),
            "p95_e2e_latency_ms": p95_latency_ms,
            "average_latency_ms": int(statistics.mean(latency_values)),
            "audit_completeness_rate": round(audit_completeness_rate, 4),
            "trace_completeness_rate": round(trace_completeness_rate, 4),
            "policy_escape_count": policy_escape_count,
        },
        "recommendation": build_recommendation(decision, hard_blockers),
    }


def build_recommendation(decision: str, hard_blockers: List[str]) -> str:
    if decision == "block":
        return f"Block release because hard blockers exist: {', '.join(hard_blockers)}."
    if decision == "canary_only":
        return "Allow canary only and keep monitoring Agent quality budget."
    if decision == "manual_review":
        return "Require manual QA and owner review before rollout."
    return "Continue rollout. Quality SLO stays within the release budget."


@app.post("/runs")
def create_run(request: CreateRunRequest) -> dict:
    return build_run(request)


@app.get("/runs")
def list_runs() -> dict:
    return {"runs": list(RUNS.values())}


@app.post("/scorecard")
def create_scorecard(threshold: Optional[SloThreshold] = None) -> dict:
    return build_scorecard(threshold or SloThreshold())


@app.delete("/runs")
def reset_runs() -> dict:
    RUNS.clear()
    return {"status": "reset"}
```

启动服务：

```bash
uvicorn agent_quality_slo_demo:app --reload --port 8088
```

构造一组质量样本：

```bash
curl -X DELETE http://127.0.0.1:8088/runs
curl -X POST http://127.0.0.1:8088/runs -H 'Content-Type: application/json' -d '{"scenario":"happy_path","task":"Generate release risk summary"}'
curl -X POST http://127.0.0.1:8088/runs -H 'Content-Type: application/json' -d '{"scenario":"slow_tool","task":"Generate release risk summary"}'
curl -X POST http://127.0.0.1:8088/scorecard -H 'Content-Type: application/json' -d '{}'
```

当你再加入 `audit_missing` 或 `unsafe_escape` 场景时，评分卡会从 `continue` 变为 `block`。这就是 hard gate 的意义：总分可以解释风险，但红线决定发布动作。

---

## 4. 工程实践二：用 Ginkgo 校验 Scorecard Contract 与发布门禁

后端 API 自动化不应该只校验单个接口字段，而要模拟完整发布前质量评估链路：先重置样本，再创建多条 Agent run，最后请求 scorecard，并验证最终发布决策。

下面是一个 Ginkgo v1 风格的示例。假设 Demo 服务已经运行在 `http://127.0.0.1:8088`。

```go
package agentquality_test

import (
    "bytes"
    "encoding/json"
    "net/http"
    "testing"
    "time"

    . "github.com/onsi/ginkgo"
    . "github.com/onsi/gomega"
)

func TestAgentQualitySLO(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Agent Quality SLO Suite")
}

var _ = Describe("Agent release scorecard E2E gate", func() {
    const baseURL = "http://127.0.0.1:8088"

    httpClient := &http.Client{Timeout: 3 * time.Second}

    resetRuns := func() {
        request, requestErr := http.NewRequest(http.MethodDelete, baseURL+"/runs", nil)
        Expect(requestErr).NotTo(HaveOccurred())
        response, responseErr := httpClient.Do(request)
        Expect(responseErr).NotTo(HaveOccurred())
        defer response.Body.Close()
        Expect(response.StatusCode).To(Equal(http.StatusOK))
    }

    createRun := func(scenario string) {
        payload := map[string]string{
            "scenario": scenario,
            "task":     "Generate release risk summary",
        }
        payloadBytes, marshalErr := json.Marshal(payload)
        Expect(marshalErr).NotTo(HaveOccurred())

        response, responseErr := httpClient.Post(baseURL+"/runs", "application/json", bytes.NewReader(payloadBytes))
        Expect(responseErr).NotTo(HaveOccurred())
        defer response.Body.Close()
        Expect(response.StatusCode).To(Equal(http.StatusOK))
    }

    readScorecard := func() map[string]interface{} {
        response, responseErr := httpClient.Post(baseURL+"/scorecard", "application/json", bytes.NewReader([]byte(`{}`)))
        Expect(responseErr).NotTo(HaveOccurred())
        defer response.Body.Close()
        Expect(response.StatusCode).To(Equal(http.StatusOK))

        var scorecard map[string]interface{}
        decodeErr := json.NewDecoder(response.Body).Decode(&scorecard)
        Expect(decodeErr).NotTo(HaveOccurred())
        return scorecard
    }

    BeforeEach(func() {
        resetRuns()
    })

    It("continues rollout when Gold E2E scenarios stay within quality budget", func() {
        createRun("happy_path")
        createRun("happy_path")
        createRun("slow_tool")

        scorecard := readScorecard()

        Expect(scorecard["decision"]).To(Equal("continue"))
        Expect(scorecard["hard_blockers"]).To(BeEmpty())
        Expect(scorecard["score"].(float64)).To(BeNumerically(">=", 90))
    })

    It("blocks release when audit completeness is breached even if the task succeeds", func() {
        createRun("happy_path")
        createRun("audit_missing")

        scorecard := readScorecard()

        Expect(scorecard["decision"]).To(Equal("block"))
        Expect(scorecard["hard_blockers"]).To(ContainElement("audit_incomplete"))
    })

    It("blocks release when policy escape is detected in an Agent response", func() {
        createRun("happy_path")
        createRun("unsafe_escape")

        scorecard := readScorecard()

        Expect(scorecard["decision"]).To(Equal("block"))
        Expect(scorecard["hard_blockers"]).To(ContainElement("policy_escape_detected"))
    })
})
```

运行方式：

```bash
go test ./... -run TestAgentQualitySLO -v
```

这个用例不是单点验证 `/scorecard` 是否返回 200，而是覆盖了“准备质量样本 → 模拟真实 Agent 运行 → 生成评分卡 → 判断发布动作”的端到端链路。单点字段断言被下沉到了每个步骤的中间状态与最终验证点中。

---

## 5. 工程实践三：用 Playwright 从用户视角校验质量评分卡

UI 侧的 E2E 重点不是重复后端 API 校验，而是验证用户是否能在发布前看到可信的质量结论。下面示例使用 Playwright APIRequestContext 调用 Demo 服务，再模拟“发布负责人打开质量评分卡”的断言逻辑。真实产品中可以替换为页面操作，例如进入 Release Dashboard、选择版本、查看 go/no-go 卡片。

安装依赖：

```bash
pip install pytest playwright
playwright install chromium
```

保存为 `test_agent_quality_scorecard.py`：

```python
import pytest
from playwright.sync_api import APIRequestContext, Playwright


@pytest.fixture(scope="session")
def api_context(playwright: Playwright) -> APIRequestContext:
    request_context = playwright.request.new_context(base_url="http://127.0.0.1:8088")
    yield request_context
    request_context.dispose()


def create_run(api_context: APIRequestContext, scenario: str) -> None:
    response = api_context.post(
        "/runs",
        data={"scenario": scenario, "task": "Generate release risk summary"},
    )
    assert response.ok


def reset_runs(api_context: APIRequestContext) -> None:
    response = api_context.delete("/runs")
    assert response.ok


def get_scorecard(api_context: APIRequestContext) -> dict:
    response = api_context.post("/scorecard", data={})
    assert response.ok
    return response.json()


def test_release_owner_can_continue_when_quality_budget_is_healthy(api_context: APIRequestContext):
    reset_runs(api_context)
    create_run(api_context, "happy_path")
    create_run(api_context, "happy_path")
    create_run(api_context, "slow_tool")

    scorecard = get_scorecard(api_context)

    assert scorecard["decision"] == "continue"
    assert scorecard["score"] >= 90
    assert scorecard["sli"]["task_success_rate"] == 1.0


def test_release_owner_is_blocked_when_audit_evidence_is_missing(api_context: APIRequestContext):
    reset_runs(api_context)
    create_run(api_context, "happy_path")
    create_run(api_context, "audit_missing")

    scorecard = get_scorecard(api_context)

    assert scorecard["decision"] == "block"
    assert "audit_incomplete" in scorecard["hard_blockers"]
    assert scorecard["recommendation"].startswith("Block release")
```

运行方式：

```bash
pytest -q test_agent_quality_scorecard.py
```

这个 Playwright 示例的核心价值在于：它让 UI/E2E 测试参与发布决策，而不是只验证页面有没有按钮。真实落地时，可以把后端 scorecard contract 和前端展示做双向校验：API 返回 `block` 时，页面必须展示阻断状态；API 返回 `canary_only` 时，页面必须禁用全量发布按钮；API 返回 `continue` 时，页面必须显示关键 SLI 与证据链接。

---

## 6. 工程实践四：把质量评分卡接入 K8s 与 CI/CD

### 6.1 用 Kubernetes Job 跑发布前质量门禁

在 K8s 环境里，可以把质量评分卡计算做成一个 release gate Job。Job 的职责是拉取当前版本的测试结果、trace 摘要和审计数据，计算 scorecard，如果决策为 `block` 就返回非零退出码。

下面是一个简化版 Job 模板：

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: agent-quality-scorecard-gate
  namespace: agent-quality-gates
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: scorecard-gate
          image: python:3.11-slim
          command:
            - /bin/sh
            - -c
            - |
              pip install requests
              python /workspace/check_scorecard.py
          env:
            - name: SCORECARD_URL
              value: "http://agent-quality-slo-demo:8088/scorecard"
          volumeMounts:
            - name: scorecard-script
              mountPath: /workspace
      volumes:
        - name: scorecard-script
          configMap:
            name: agent-quality-scorecard-script
```

`check_scorecard.py` 的逻辑可以非常简单：

```python
import os
import sys

import requests

scorecard_url = os.environ["SCORECARD_URL"]
response = requests.post(scorecard_url, json={}, timeout=5)
response.raise_for_status()
scorecard = response.json()

print(scorecard)

if scorecard["decision"] == "block":
    sys.exit(1)

sys.exit(0)
```

CI/CD 只需要监听这个 Job 的结果。成功则继续灰度，失败则阻断发布并把 scorecard 发到飞书或质量看板。

### 6.2 推荐的流水线接入顺序

建议不要一开始就把所有指标都做成硬门禁，而是分三步推进。

第一步，先把 scorecard 作为只读报告接入 CI，让团队熟悉指标含义。第二步，把 P0 Gold 场景失败、安全绕过、审计缺失设置为硬门禁。第三步，再逐步把延迟预算、工具正确率、trace 完整率纳入灰度策略。这样可以降低组织切换成本，避免一上线就因为指标口径不成熟导致频繁误阻断。

### 6.3 与每日质量复盘结合

质量评分卡每天都应该被自动归档，至少记录 release_id、score、decision、hard_blockers、Top failure buckets 与 owner。这样可以回答一类非常重要的问题：过去一周质量预算消耗在哪里？是模型质量在回退，还是工具稳定性下降？是前端状态同步问题变多，还是观测缺失导致分诊失败？

当这些趋势被沉淀下来，QA 就不只是“发现问题的人”，而是“用数据推动工程优先级的人”。

---

## 7. 常见反模式与风险提示

### 7.1 把所有指标平均加权

平均加权看起来公平，但会掩盖红线风险。安全绕过、审计缺失、跨租户污染这类问题不能被其他高分指标抵消。正确做法是硬门禁优先，加权评分其次。

### 7.2 只看自动化通过率

自动化通过率很重要，但它只能说明“测试定义的断言是否通过”。如果断言没有覆盖 groundedness、工具正确性、审计完整性和用户可见结果，自动化通过率会给团队错误安全感。

### 7.3 指标没有 owner

没有 owner 的指标最终会变成看板噪声。每个核心 SLI 都应该能映射到治理 owner，例如工具平台、Agent Runtime、知识平台、安全、前端体验或测试基础设施。

### 7.4 Scorecard 只在发布当天生成

如果评分卡只在发布当天生成，它就只能告诉你“今天不能发”。更好的方式是每天持续计算，让团队提前看到预算消耗趋势，在发布前就完成修复。

---

## 8. 课后思考题

1. 你负责的 Agent 产品中，哪些场景应该被定义为 Gold E2E 场景？这些场景是否已经覆盖用户触发、工具执行、结果展示、审计落盘和可观测证据？
2. 如果某次发布的任务成功率为 99%，但审计完整率只有 98%，你会允许继续灰度吗？你的硬门禁规则是什么？
3. 你的自动化报告现在是否能直接输出 go/no-go 决策？如果不能，缺少的是指标、证据、规则，还是 owner 映射？
4. 对于模型质量回归，你会把哪些指标放进 scorecard？哪些指标只适合放在离线评测报告里？
5. 如果质量评分卡连续三天处于 `canary_only`，团队应该优先排查工具稳定性、Prompt 质量、K8s 环境，还是测试噪声？你会如何用证据排序？

---

## 9. 今日小结

今天我们把 AI Agent 测试从“失败后归因”推进到了“发布前量化风险”。核心观点是：Agent 质量 SLO 必须围绕用户任务闭环定义，而不能只复用传统服务可用率。一个成熟的质量评分卡需要同时覆盖任务成功、智能质量、工具可靠性、安全合规与可观测性，并把这些信号转化为明确的发布决策。

工程实践上，我们实现了一个可运行的 FastAPI Demo，用它模拟 Agent run、计算质量 SLI、生成 release scorecard；随后用 Ginkgo 覆盖后端发布门禁，用 Playwright 从用户视角校验质量结论，并讨论了如何通过 K8s Job 接入 CI/CD。对 Senior SDET 来说，真正的目标不是让测试报告更丰富，而是让质量数据进入发布系统，成为工程节奏和风险治理的一部分。

明天可以继续深入一个相关主题：如何把 Agent 质量评分卡与生产观测、线上回放和自动化缺陷创建打通，让质量运营从“发布前门禁”扩展到“线上持续守护”。
