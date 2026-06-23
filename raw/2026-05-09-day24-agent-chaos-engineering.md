---
title: "每日 AI 学习笔记｜Day 24：AI Agent 混沌工程与故障注入（Chaos Mesh + Ginkgo E2E）"
date: 2026-05-09
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, reliability, chaos, Kubernetes]
---

# 每日 AI 学习笔记 Day 24｜AI Agent 混沌工程与故障注入（Chaos Mesh + Ginkgo E2E）

面向：资深测试开发（Golang Ginkgo / Python Playwright / K8s / API Testing）

关键词：**Chaos Engineering / Fault Injection / Steady State / Blast Radius / Ginkgo E2E / Playwright / K8s / Agent Reliability**

Day 23 讨论了可观测性与链路追踪，解决的是“出问题后能不能看清楚”。Day 24 继续向前推进一步：在上线前主动制造可控故障，验证 AI Agent 在工具超时、检索失败、模型限流、Pod 抖动、网络延迟等真实异常下，是否仍能完成端到端业务任务，并留下可复盘的证据。

{/* truncate */}

## 0. 今日目标

今天不是单独验证某个故障注入工具是否可用，而是围绕一条真实业务链路建立混沌工程能力：用户触发一个 Agent 任务，系统完成规划、检索、工具调用、模型生成、结果落盘与前端展示；在链路中的某个依赖发生异常时，产品仍然要给出可解释、可恢复、可追踪的结果。

完成今天的学习后，你应该能够做到四件事。第一，能把 AI Agent 的故障模型拆成可执行的实验假设，而不是只写“模拟异常”。第二，能用 Python FastAPI 构造一个可注入故障的最小 Agent 服务，方便本地调试。第三，能用 Go + Ginkgo 写一条 E2E 可靠性用例，把“故障发生后仍可恢复”变成自动化断言。第四，能把 K8s / Chaos Mesh 这类基础设施故障接入预发验证，形成可重复、可回放、可门禁的质量工程闭环。

## 1. 核心理论：Agent 混沌工程不是“随机搞坏系统”

### 1.1 什么是适合 QA 的混沌工程

混沌工程的核心不是破坏系统，而是验证系统在受控扰动下是否仍满足用户可感知的稳定状态。对测试开发来说，最重要的不是“注入了多少种故障”，而是每个实验都能回答一个业务问题：当某个依赖变慢、失败或抖动时，用户的端到端任务是否还能完成，失败是否可解释，恢复是否可观测。

一个合格的 Agent 混沌实验至少包含五个要素：稳定状态假设、故障注入点、影响范围、E2E 判定标准、证据采集方式。

稳定状态假设描述系统正常时应该保持什么能力，例如“生成 API 回归测试方案任务在 60 秒内完成，最终页面展示任务状态为 succeeded，并返回 trace_id”。故障注入点描述异常发生在哪里，例如 RAG 服务延迟 2 秒、工具服务返回 503、模型网关返回 429、K8s Pod 被重启。影响范围约束实验只影响测试租户、预发命名空间或指定用例批次，避免扩大风险。E2E 判定标准描述用户链路是否成功，例如“系统降级到缓存知识库，最终产物仍可查看”。证据采集方式要求保留 trace、日志、指标、前端截图、接口响应等材料。

### 1.2 Agent 场景的典型故障模型

AI Agent 的链路比传统 API 更动态，因此故障模型也要覆盖更多阶段。

- **规划阶段故障**：Prompt 版本切换后计划为空、计划步骤重复、任务状态机卡住。
- **RAG 阶段故障**：向量库超时、召回为空、重排服务慢、知识库索引版本不一致。
- **工具调用故障**：工具返回 429/5xx、JSON Schema 不匹配、部分流式 chunk 丢失、幂等重试失败。
- **模型阶段故障**：TTFT 过高、输出中断、模型路由失败、fallback 后答案格式变化。
- **K8s 基础设施故障**：Pod kill、容器 CPU throttling、网络延迟、DNS 异常、节点资源紧张。
- **前端体验故障**：长任务进度不刷新、失败后无法重试、结果落盘成功但 UI 没有展示。

这些故障不应该被拆成孤立的单点用例，而应嵌入完整业务链路。比如“工具超时”不是只断言接口返回 timeout，而是验证用户提交任务后，Agent 能识别工具超时、触发 fallback、在页面展示可理解的降级提示、最终保留 trace 和重试记录。

### 1.3 混沌实验的四个质量门槛

第一是 **Blast Radius**，即爆炸半径。实验必须限制在可控范围内，例如测试租户、预发环境、特定 namespace、特定 header 或固定 run_id。没有范围约束的故障注入不是测试能力，而是事故风险。

第二是 **Rollback**，即回滚路径。每个实验都要能停止注入、恢复网络、恢复 Pod、清理测试数据，并在自动化脚本里完成资源回收。

第三是 **Observability**，即可观测证据。混沌实验必须与 trace_id、case_id、run_id 绑定，否则失败后只能看到“系统坏了”，无法判断故障是否按预期被处理。

第四是 **E2E Outcome**，即端到端结果。测试结论要落在用户能观察到的结果上，例如任务是否完成、结果是否可打开、页面是否展示恢复入口、状态流是否一致，而不是只看某个 HTTP 状态码。

## 2. 工程实践一：Python 构造可注入故障的最小 Agent 服务

下面的示例用 FastAPI 模拟一个 Agent 服务。它不是只提供一个“返回 200”的假接口，而是包含一条完整的迷你链路：创建任务、规划、调用工具、生成结果、返回 trace_id。通过请求头 `x-fault-mode` 可以注入不同故障，方便后续 Playwright、Ginkgo 或 k6 复用同一条 E2E 场景。

安装依赖：

```bash
pip install fastapi uvicorn pydantic httpx
```

保存为 `fault_injectable_agent.py`：

```python
import asyncio
import time
import uuid
from typing import Dict, Literal, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Fault Injectable Agent Demo")

FaultMode = Literal["none", "rag_slow", "tool_timeout", "tool_503", "model_429"]


class AgentRequest(BaseModel):
    task: str
    scenario: str = "api-test-plan-generation"


class AgentResponse(BaseModel):
    run_id: str
    trace_id: str
    status: Literal["succeeded", "degraded", "failed"]
    result: Optional[str]
    evidence: Dict[str, str]


async def plan_task(task: str) -> Dict[str, str]:
    await asyncio.sleep(0.03)
    return {"step": "plan", "summary": f"Plan test strategy for: {task[:40]}"}


async def retrieve_context(fault_mode: FaultMode) -> Dict[str, str]:
    if fault_mode == "rag_slow":
        await asyncio.sleep(1.5)
        return {"source": "cache", "quality": "degraded"}
    await asyncio.sleep(0.05)
    return {"source": "vector-db", "quality": "fresh"}


async def call_tool(fault_mode: FaultMode) -> Dict[str, str]:
    if fault_mode == "tool_timeout":
        await asyncio.sleep(0.8)
        raise TimeoutError("tool call timeout")
    if fault_mode == "tool_503":
        raise RuntimeError("tool service unavailable")
    await asyncio.sleep(0.06)
    return {"tool": "api-schema-reader", "status": "ok"}


async def generate_answer(fault_mode: FaultMode, task: str, context: Dict[str, str], tool: Dict[str, str]) -> str:
    if fault_mode == "model_429":
        raise HTTPException(status_code=429, detail="model provider rate limited")
    await asyncio.sleep(0.08)
    return (
        "Generated E2E API regression test plan with auth, idempotency, "
        f"error handling and observability checks. context={context['source']}, tool={tool['status']}, task={task[:30]}"
    )


@app.post("/agent/runs", response_model=AgentResponse)
async def create_agent_run(
    payload: AgentRequest,
    x_fault_mode: FaultMode = Header(default="none"),
) -> AgentResponse:
    run_id = str(uuid.uuid4())
    trace_id = uuid.uuid4().hex
    start = time.perf_counter()
    evidence: Dict[str, str] = {
        "run_id": run_id,
        "trace_id": trace_id,
        "fault_mode": x_fault_mode,
    }

    plan = await plan_task(payload.task)
    evidence["plan"] = plan["summary"]

    context = await retrieve_context(x_fault_mode)
    evidence["rag_source"] = context["source"]

    try:
        tool = await call_tool(x_fault_mode)
    except (TimeoutError, RuntimeError) as exc:
        evidence["tool_error"] = type(exc).__name__
        evidence["fallback"] = "use-last-known-schema"
        tool = {"tool": "api-schema-reader", "status": "fallback"}

    result = await generate_answer(x_fault_mode, payload.task, context, tool)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    evidence["elapsed_ms"] = str(elapsed_ms)

    status = "degraded" if tool["status"] == "fallback" or context["source"] == "cache" else "succeeded"
    return AgentResponse(run_id=run_id, trace_id=trace_id, status=status, result=result, evidence=evidence)
```

运行服务：

```bash
uvicorn fault_injectable_agent:app --host 0.0.0.0 --port 8080
```

正常链路调用：

```bash
curl -s -X POST http://127.0.0.1:8080/agent/runs \
  -H 'Content-Type: application/json' \
  -d '{"task":"为订单 API 生成端到端回归测试方案"}'
```

注入工具超时并验证降级：

```bash
curl -s -X POST http://127.0.0.1:8080/agent/runs \
  -H 'Content-Type: application/json' \
  -H 'x-fault-mode: tool_timeout' \
  -d '{"task":"为订单 API 生成端到端回归测试方案"}'
```

这个示例的关键点是：故障不是单独存在的，而是被放进“提交 Agent 任务 → 规划 → 检索 → 工具调用 → 生成结果 → 返回证据”的完整链路中。测试断言应该关注 `status`、`result`、`evidence.trace_id`、`evidence.fallback` 等可观测结果。

## 3. 工程实践二：Go + Ginkgo 写 E2E 故障注入回归

下面的 Ginkgo 示例不依赖真实外部服务，而是用 `httptest` 启动一个模拟 Agent API，验证一条完整业务链路：用户提交生成测试方案任务，当工具服务超时时，系统应进入 degraded 状态、触发 fallback，并返回 trace_id 与最终结果。

依赖安装：

```bash
go get github.com/onsi/ginkgo/v2 github.com/onsi/gomega
```

保存为 `agent_chaos_e2e_test.go` 后执行 `go test ./... -v`：

```go
package chaose2e_test

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

func TestAgentChaosE2E(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Agent Chaos E2E Suite")
}

type agentResponse struct {
    RunID    string            `json:"run_id"`
    TraceID  string            `json:"trace_id"`
    Status   string            `json:"status"`
    Result   string            `json:"result"`
    Evidence map[string]string `json:"evidence"`
}

func newAgentServer() *httptest.Server {
    mux := http.NewServeMux()
    mux.HandleFunc("/agent/runs", func(w http.ResponseWriter, r *http.Request) {
        faultMode := r.Header.Get("x-fault-mode")
        response := agentResponse{
            RunID:   "run-e2e-001",
            TraceID: "trace-e2e-001",
            Status:  "succeeded",
            Result:  "Generated API regression test plan",
            Evidence: map[string]string{
                "plan":       "created",
                "rag_source": "vector-db",
                "tool":       "api-schema-reader",
                "fault_mode": faultMode,
            },
        }

        if faultMode == "tool_timeout" {
            response.Status = "degraded"
            response.Evidence["tool_error"] = "TimeoutError"
            response.Evidence["fallback"] = "use-last-known-schema"
        }

        w.Header().Set("Content-Type", "application/json")
        _ = json.NewEncoder(w).Encode(response)
    })
    return httptest.NewServer(mux)
}

var _ = Describe("Agent reliability under injected faults", func() {
    It("keeps the API test-plan generation journey recoverable when the tool dependency times out", func() {
        server := newAgentServer()
        defer server.Close()

        payload := []byte(`{"task":"generate an E2E API regression test plan for order creation"}`)
        req, err := http.NewRequest(http.MethodPost, server.URL+"/agent/runs", bytes.NewReader(payload))
        Expect(err).NotTo(HaveOccurred())
        req.Header.Set("Content-Type", "application/json")
        req.Header.Set("x-fault-mode", "tool_timeout")

        resp, err := http.DefaultClient.Do(req)
        Expect(err).NotTo(HaveOccurred())
        defer resp.Body.Close()
        Expect(resp.StatusCode).To(Equal(http.StatusOK))

        var body agentResponse
        Expect(json.NewDecoder(resp.Body).Decode(&body)).To(Succeed())

        Expect(body.RunID).NotTo(BeEmpty())
        Expect(body.TraceID).NotTo(BeEmpty())
        Expect(body.Status).To(Equal("degraded"))
        Expect(body.Result).To(ContainSubstring("API regression test plan"))
        Expect(body.Evidence).To(HaveKeyWithValue("tool_error", "TimeoutError"))
        Expect(body.Evidence).To(HaveKeyWithValue("fallback", "use-last-known-schema"))
    })
})
```

这条用例看起来是在验证“工具超时”，但真正的测试对象是一条端到端业务旅程：任务提交成功、Agent 进入计划阶段、工具依赖异常、系统走 fallback、最终仍生成结果、证据链可查询。单点断言都被下沉到了 E2E 步骤的中间状态与最终验证点中。

## 4. 工程实践三：Playwright 验证前端可恢复体验

后端降级成功并不等于用户体验成功。对于长任务型 Agent 产品，前端必须让用户看见状态变化、失败原因、重试入口和最终产物。下面示例假设页面上存在任务输入框、提交按钮、状态区和结果区，用 Playwright 验证“注入工具超时后，页面仍能展示 degraded 状态与结果”。

安装依赖：

```bash
pip install pytest-playwright
playwright install chromium
```

保存为 `test_agent_fault_recovery.py`：

```python
import re
from playwright.sync_api import Page, expect


def test_agent_journey_recovers_from_tool_timeout(page: Page):
    page.route("**/agent/runs", lambda route: route.fulfill(
        status=200,
        json={
            "run_id": "run-ui-001",
            "trace_id": "trace-ui-001",
            "status": "degraded",
            "result": "Generated API regression test plan with fallback schema.",
            "evidence": {
                "tool_error": "TimeoutError",
                "fallback": "use-last-known-schema",
            },
        },
    ))

    page.goto("http://localhost:3000/agent")
    page.get_by_label("Task").fill("Generate an API regression test plan for order creation")
    page.get_by_role("button", name="Run Agent").click()

    expect(page.get_by_test_id("run-status")).to_have_text(re.compile("degraded", re.I))
    expect(page.get_by_test_id("result-panel")).to_contain_text("API regression test plan")
    expect(page.get_by_test_id("evidence-panel")).to_contain_text("trace-ui-001")
    expect(page.get_by_role("button", name="Retry")).to_be_visible()
```

这条 Playwright 用例的价值不在于 mock 了一个接口响应，而在于把 UI 体验纳入可靠性闭环：用户提交任务后，即使后端走了 fallback，页面仍要给出可理解的状态、可查看的结果、可追踪的 trace_id 和可恢复的重试入口。

## 5. 工程实践四：K8s / Chaos Mesh 注入基础设施故障

当本地故障注入用例稳定后，下一步可以把实验移到 K8s 预发环境。Chaos Mesh 适合模拟 Pod kill、网络延迟、DNS 错误、CPU 压力等基础设施扰动。下面示例会对带有 `app=agent-api` 标签的 Pod 注入网络延迟，持续 2 分钟。

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: agent-api-network-delay
  namespace: qa-chaos
spec:
  action: delay
  mode: one
  selector:
    namespaces:
      - qa-chaos
    labelSelectors:
      app: agent-api
  delay:
    latency: "800ms"
    correlation: "50"
    jitter: "100ms"
  duration: "2m"
```

执行实验前建议先做好三类保护。第一，所有实验资源只放在 `qa-chaos` 这类测试命名空间中，不影响生产流量。第二，所有自动化请求都带上 `x-chaos-run-id`，便于日志和 trace 过滤。第三，实验结束后由流水线自动删除 Chaos 对象，并检查 Agent 服务恢复到稳定状态。

一个推荐的流水线顺序如下：部署预发版本，运行无故障 E2E 冒烟，创建 Chaos Mesh 实验，运行 Ginkgo / Playwright E2E 可靠性用例，采集 trace 与指标，删除 Chaos 对象，再运行一次恢复后冒烟。如果故障期间任务无法降级、恢复后状态不一致、trace 缺失或错误分桶异常，流水线应失败。

## 6. 今日 E2E 场景模板

可以把今天的内容沉淀成一个通用 E2E 用例模板：

```yaml
case_id: agent-chaos-api-test-plan-001
journey: User submits an API test-plan generation task and receives a recoverable result under injected dependency failure.
entry: Web console or public API creates an Agent run.
fault:
  stage: tool_call
  mode: timeout
  blast_radius: qa namespace + test tenant + x-chaos-run-id
expected_intermediate_states:
  - run status moves from queued to running
  - plan step is created and visible in trace
  - tool timeout is recorded in evidence
  - fallback path is selected
final_validation:
  - run status is degraded or succeeded, not stuck
  - final result is viewable
  - trace_id is returned and searchable
  - retry action is available when degraded
  - metrics contain the expected fault bucket
cleanup:
  - delete chaos object
  - remove test run data
  - verify service returns to steady state
```

这个模板遵循一个原则：单点验证不单独成用例，而是嵌入完整用户旅程。每个故障点都要对应一个中间状态、一个最终验证点和一组可复盘证据。

## 7. 课后思考题

1. 如果“生成 API 回归测试方案”任务依赖 RAG、工具服务和模型网关三类外部能力，你会如何设计一组最小但高价值的故障矩阵，既覆盖主要风险，又避免实验数量爆炸？
2. 当工具服务超时后，系统选择 fallback 并最终返回 degraded，你会如何定义“这是可接受降级”还是“应该判定失败”？需要哪些用户可见结果和证据？
3. 如果 Chaos Mesh 注入网络延迟后，Ginkgo 后端用例通过但 Playwright 前端用例失败，你会如何从 trace、浏览器录屏、接口响应、状态机几个维度定位问题？
4. 对于流式输出的 Agent，如何模拟“前半段 token 正常、后半段中断”的故障，并把 UI 恢复体验纳入 E2E 验证？
5. 如何把混沌实验接入 CI/CD 门禁，同时控制执行时长、实验风险和误报率？

## 8. 今日小结

Day 24 的核心结论是：AI Agent 的可靠性不能只靠“正常路径回归”证明，而要通过受控故障验证系统在异常路径下是否仍然可用、可解释、可恢复、可追踪。

对资深 QA 工程师来说，混沌工程的落地重点不是引入某个工具，而是把故障注入组织成端到端业务场景：从用户触发开始，到系统经历规划、检索、工具调用、模型生成、降级恢复、前端展示、证据留存为止。只有这样，工具超时、模型限流、Pod 抖动、网络延迟这些异常才不会停留在“模拟过”，而会真正变成可持续回归的质量资产。

明天可以继续深入一个相关主题：如何把这些 E2E 可靠性场景沉淀成场景资产库，并按风险、频率、成本自动选择每天需要执行的回归集合。
