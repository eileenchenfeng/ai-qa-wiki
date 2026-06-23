---
title: "每日 AI 学习笔记｜Day 30：AI Agent 失败归因与自动化分诊"
date: 2026-05-15
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, failure-analysis, triage, observability, SDET, Ginkgo, Playwright, K8s, API-testing, e2e]
---

# 每日 AI 学习笔记 Day 30｜AI Agent 失败归因与自动化分诊

## 核心总结

面向 Senior SDET 的 AI Agent 失败分析，不能把一次失败简单归结为“接口超时”“模型答错了”或“前端没展示出来”。真正有工程价值的失败归因，必须沿着 **用户任务、Agent 阶段、工具调用、运行时环境、可观测证据与最终用户可见结果** 这条完整 E2E 链路来判断：问题到底是出在任务创建、规划、检索、工具执行、模型综合、UI 状态同步、K8s 依赖、观测缺失，还是测试本身的环境抖动。如果没有一套稳定的归因模型，团队就会长期陷入同一种低效循环：CI 只告诉你“failed”，QA 手工翻日志，研发凭经验猜问题，发布负责人无法判断该不该阻断。对 AI QA 来说，自动化分诊的目标不是“生成一份更漂亮的失败报告”，而是把失败变成 **可分类、可定位、可分派、可阻断、可复盘** 的工程事件，让一次 E2E 失败能直接驱动后续修复与发布决策。

{/* truncate */}

## 0. 今日目标

今天的主题是 AI Agent 失败归因与自动化分诊。完成今天的学习后，你应该能够做到四件事。第一，能把一次 Agent E2E 失败拆解成用户旅程中的具体断点，而不是只盯着某个报错字符串。第二，能设计一套统一的 triage contract，把 API、Ginkgo、Playwright、trace、audit 与 K8s 证据汇总成结构化归因结果。第三，能编写最小可运行 Demo，让自动化测试在失败后自动输出 bucket、severity、owner 和 go/no-go 建议。第四，能把失败归因接入发布门禁、质量看板和回归治理，减少“红了但不知道该找谁”的组织摩擦。

本篇内容面向已经具备 Golang、Python、Kubernetes、API 自动化和浏览器自动化经验的 Senior SDET。重点不是讲“日志怎么搜”，而是把失败归因做成质量系统的一部分，让一次失败从用户视角出发，最终落成可执行动作。

---

## 1. 核心理论：失败归因的对象不是报错，而是“任务闭环中的断点”

### 1.1 为什么传统的失败判定方式在 Agent 场景里经常不够用

在传统 API 自动化里，很多失败都可以通过 HTTP 状态码、接口响应体或单个日志定位。例如 500 说明服务异常，404 说明资源不存在，403 说明权限不足。这类方法在稳定的 CRUD 系统里通常够用，但放到 AI Agent 系统中就会迅速失效。

原因很简单：Agent 不是单次调用，而是一条多阶段执行链路。一个用户点击“生成测试计划”，系统可能要经历 run 创建、planner 选择策略、RAG 检索上下文、调用多个工具、综合生成答案、同步前端状态、写入审计事件和指标。用户看到的“失败”只是最终现象，不一定是根因所在。

举例来说，页面显示“生成失败”，根因可能完全不同。第一种情况，后端工具调用超时，最终答案为空。第二种情况，工具调用其实成功了，但前端轮询状态机没有从 running 切到 failed。第三种情况，最终答案已经生成，但审计事件缺失，导致发布门禁主动拦截。第四种情况，系统一切正常，真正的问题是测试环境 DNS 抖动或测试数据污染。若你只看最后一个报错字段，四类问题会被错误地聚合成同一个“Agent failed”。

Senior SDET 要做的不是给失败起一个更大的名字，而是明确：**失败归因的最小单位是任务旅程中的可观测断点**。也就是说，失败应该回答的是“用户旅程在哪一段断了、为什么断、证据是什么、是否应阻断发布”。

### 1.2 一次 Agent E2E 失败至少要回答哪五个问题

一个成熟的归因系统，至少应该对每次失败给出五个维度的答案。

1. **失败发生在哪个阶段**：是 task creation、planner、retrieval、tool_call、synthesis、delivery、audit 还是 runtime。
2. **失败对用户的影响是什么**：用户看到空结果、错误结果、延迟过高、安全拦截，还是只是内部证据不完整。
3. **失败属于哪一类 bucket**：模型回归、知识召回缺失、工具不可用、UI 契约断裂、K8s 运行时错误、观测缺失、测试抖动等。
4. **失败的处置动作是什么**：自动重试、创建缺陷、阻断发布、转人工复核、降级通过，还是忽略为测试噪声。
5. **失败的责任边界在哪里**：模型/Prompt、服务端业务、工具平台、前端、基础设施、数据治理，还是测试系统自身。

只有这五个问题都被回答，分诊结果才真正可执行。否则“AI Agent 回归失败”只是一个通知，不是一个决策输入。

### 1.3 失败 bucket 不是为了统计，而是为了驱动行动

很多团队会建立失败分类枚举，但这些枚举往往停留在报表层。例如 dashboard 上显示 `tool_error=5`、`model_error=2`、`ui_error=1`，看起来很整齐，却无法真正指导处理。原因在于 bucket 只有名字，没有行为语义。

好的 bucket 设计应该天然携带后续动作。比如：

- `contract_breaking`：默认阻断发布，优先分派给后端 owner。
- `tool_unavailable`：若影响 Gold 场景，阻断发布；若只影响 Canary，可按阈值判定。
- `retrieval_miss`：不一定意味着系统不可用，但必须进入知识与数据治理队列。
- `ui_state_desync`：如果 API 已完成但 UI 卡住，说明用户体验失败，应由前端与状态同步 owner 处理。
- `audit_missing`：即使用户结果正确，也可能因合规和可追责要求而阻断上线。
- `test_flake`：不进入产品缺陷列表，但必须进入测试治理和稳定性治理。

因此，bucket 设计的核心不是“让失败看起来有条理”，而是“让机器能够基于失败结果直接选择处理路径”。

---

## 2. 归因模型设计：把多源证据收敛成一个 triage contract

### 2.1 为什么必须有统一的 triage contract

如果 API 测试只输出 `assert failed`，Playwright 输出截图，K8s Job 输出容器日志，trace 平台输出 span 树，而审计服务再输出另一套 JSON，那么失败虽有大量证据，却仍然很难自动化分诊。人肉能看懂，不代表系统能处理。

统一 triage contract 的作用，是让所有证据最终收敛到同一张“失败合同”上。这个合同不要求覆盖所有底层细节，但必须把发布判断需要的关键信息表达完整：这次用户任务是什么、失败阶段是什么、最终 bucket 是什么、风险严重度如何、证据列表有哪些、责任 owner 是谁、是否允许继续放量。

### 2.2 推荐的 triage JSON 结构

下面是一份适合 Agent E2E 使用的最小 triage contract。它的核心思想是：把单点校验都折叠进一次完整用户任务的执行证据里。

```json
{
  "run_id": "run-a7f92d1c",
  "trace_id": "trace-9c1a3e77",
  "case_id": "agent-release-risk-001",
  "scenario": "generate_release_risk_summary",
  "entrypoint": "web_and_api",
  "stage": "tool_call",
  "user_visible_status": "failed",
  "triage": {
    "bucket": "tool_unavailable",
    "severity": "high",
    "go_no_go": "block",
    "owner": "agent-tools-team",
    "summary": "The release-summary tool timed out after the planner selected the expected path.",
    "candidate_root_causes": [
      "downstream timeout",
      "tool dependency unavailable",
      "egress/network issue"
    ]
  },
  "evidence": {
    "api_status": "failed",
    "ui_state": "error_banner_rendered",
    "tool_calls": [
      {
        "name": "release_summary_tool",
        "status": "timeout",
        "latency_ms": 12034
      }
    ],
    "audit": {
      "decision": "block",
      "event_present": true
    },
    "runtime": {
      "namespace": "qa-gates",
      "pod_restart_count": 0
    }
  }
}
```

这个结构有四个关键特征。第一，它不是只描述“出错了”，而是描述“用户任务在什么阶段以什么方式失败”。第二，它把用户可见状态和系统内部证据同时纳入。第三，它天然适合作为 Ginkgo、Playwright 和 K8s gate 的共同输出格式。第四，它已经包含了 go/no-go 决策，不需要发布负责人再去手工解读十几份日志。

### 2.3 bucket 设计建议：从“现象枚举”升级为“责任边界枚举”

建议至少为 Agent 失败维护下面这组 bucket。它们不是唯一答案，但足够覆盖大多数 E2E 质量门禁场景。

<table header-row="true" header-col="false" col-widths="170,180,170,260">
  <tr>
    <td>Bucket</td>
    <td>典型阶段</td>
    <td>默认动作</td>
    <td>解释</td>
  </tr>
  <tr>
    <td>`contract_breaking`</td>
    <td>task_create / delivery</td>
    <td>block</td>
    <td>接口契约、状态字段、关键返回结构与预期不一致</td>
  </tr>
  <tr>
    <td>`planner_regression`</td>
    <td>planner</td>
    <td>review</td>
    <td>策略选择明显错误，导致后续路径偏离业务目标</td>
  </tr>
  <tr>
    <td>`retrieval_miss`</td>
    <td>retrieval</td>
    <td>review</td>
    <td>召回为空、召回错域或上下文质量不足，结果虽可生成但不可信</td>
  </tr>
  <tr>
    <td>`tool_unavailable`</td>
    <td>tool_call</td>
    <td>block</td>
    <td>工具超时、5xx、依赖不可达或执行权限异常</td>
  </tr>
  <tr>
    <td>`model_quality_regression`</td>
    <td>synthesis</td>
    <td>review</td>
    <td>模型结果不满足关键业务断言，但工具和系统运行正常</td>
  </tr>
  <tr>
    <td>`ui_state_desync`</td>
    <td>delivery</td>
    <td>block</td>
    <td>API 已完成而 UI 未同步，或页面暴露了错误状态/旧数据</td>
  </tr>
  <tr>
    <td>`audit_missing`</td>
    <td>audit</td>
    <td>block</td>
    <td>用户结果存在，但缺失关键审计字段或落盘事件</td>
  </tr>
  <tr>
    <td>`k8s_runtime_error`</td>
    <td>runtime</td>
    <td>block</td>
    <td>DNS、容器启动、配置注入、网络出口或资源限制导致链路失败</td>
  </tr>
  <tr>
    <td>`test_flake`</td>
    <td>any</td>
    <td>retry_then_review</td>
    <td>失败来自测试环境波动、数据竞争或非产品问题</td>
  </tr>
</table>

好的 bucket 体系必须允许“最终只归一个主 bucket，但保留多个候选根因”。这样既能支持发布决策，也不会丢失调查深度。

---

## 3. 工程实践一：先搭一个能暴露 triage 证据的 Agent Demo

下面的 Demo 模拟一个“生成发布风险总结”的 Agent 服务。它有三个特征。第一，它暴露了从 run 创建到终态的完整状态流转。第二，它会基于不同 `scenario` 生成不同的失败 bucket。第三，它把 run 状态、audit 和 trace 摘要分开提供，方便后续 Ginkgo 与 Playwright 共同消费。

安装依赖：

```bash
pip install fastapi uvicorn pydantic
```

保存为 `agent_triage_demo.py`：

```python
import time
import uuid
from typing import Dict, List

from fastapi import FastAPI, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Agent Triage Demo")
RUNS: Dict[str, dict] = {}


class CreateRunRequest(BaseModel):
    scenario: str
    task: str
    expected_tools: List[str]


def build_triage(run: dict) -> dict:
    scenario = run["scenario"]

    if scenario == "tool_timeout":
        return {
            "bucket": "tool_unavailable",
            "severity": "high",
            "go_no_go": "block",
            "owner": "agent-tools-team",
            "summary": "release_summary_tool timed out during tool_call stage",
        }
    if scenario == "retrieval_gap":
        return {
            "bucket": "retrieval_miss",
            "severity": "medium",
            "go_no_go": "review",
            "owner": "knowledge-platform-team",
            "summary": "retrieval returned unrelated release context",
        }
    if scenario == "ui_contract_gap":
        return {
            "bucket": "ui_state_desync",
            "severity": "high",
            "go_no_go": "block",
            "owner": "frontend-agent-team",
            "summary": "API finished but UI state payload misses terminal marker",
        }
    return {
        "bucket": "model_quality_regression",
        "severity": "medium",
        "go_no_go": "review",
        "owner": "agent-quality-team",
        "summary": "final answer missed required release risk fields",
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok", "component": "agent-triage-demo"}


@app.post("/api/runs", status_code=201)
def create_run(
    payload: CreateRunRequest,
    x_trace_id: str | None = Header(default=None),
    x_tenant_id: str = Header(default="qa-gates"),
    x_user_role: str = Header(default="qa_lead"),
):
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    trace_id = x_trace_id or f"trace-{uuid.uuid4().hex[:8]}"
    RUNS[run_id] = {
        "run_id": run_id,
        "trace_id": trace_id,
        "scenario": payload.scenario,
        "task": payload.task,
        "expected_tools": payload.expected_tools,
        "tenant_id": x_tenant_id,
        "user_role": x_user_role,
        "status": "running",
        "stage": "planner",
        "created_at": time.time(),
        "tool_calls": [],
        "result": None,
    }
    return {"run_id": run_id, "trace_id": trace_id, "status": "running"}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    run = RUNS[run_id]
    elapsed = time.time() - run["created_at"]

    if elapsed > 0.3 and not run["tool_calls"]:
        run["stage"] = "tool_call"
        scenario = run["scenario"]
        if scenario == "tool_timeout":
            run["tool_calls"] = [
                {"name": "release_summary_tool", "status": "timeout", "latency_ms": 12034}
            ]
        elif scenario == "retrieval_gap":
            run["tool_calls"] = [
                {"name": "knowledge_search", "status": "ok", "latency_ms": 182}
            ]
        elif scenario == "ui_contract_gap":
            run["tool_calls"] = [
                {"name": "release_summary_tool", "status": "ok", "latency_ms": 320}
            ]
        else:
            run["tool_calls"] = [
                {"name": "release_summary_tool", "status": "ok", "latency_ms": 410}
            ]

    if elapsed > 0.8 and run["status"] == "running":
        triage = build_triage(run)
        run["triage"] = triage

        if run["scenario"] == "ui_contract_gap":
            run["status"] = "succeeded"
            run["stage"] = "completed"
            run["result"] = "Release summary generated but ui_terminal_state=false"
        else:
            run["status"] = "failed"
            run["stage"] = "triaged"
            run["result"] = triage["summary"]

    return run


@app.get("/api/runs/{run_id}/audit")
def get_audit(run_id: str):
    run = RUNS[run_id]
    triage = run.get("triage") or build_triage(run)
    return {
        "run_id": run_id,
        "trace_id": run["trace_id"],
        "tenant_id": run["tenant_id"],
        "user_role": run["user_role"],
        "decision": triage["go_no_go"],
        "bucket": triage["bucket"],
        "owner": triage["owner"],
        "event_present": True,
    }


@app.get("/api/runs/{run_id}/trace")
def get_trace(run_id: str):
    run = RUNS[run_id]
    return {
        "trace_id": run["trace_id"],
        "spans": [
            {"name": "planner", "status": "ok"},
            {"name": "tool_call", "status": run["tool_calls"][0]["status"] if run["tool_calls"] else "running"},
            {"name": "delivery", "status": "pending" if run["status"] == "running" else "done"},
        ],
    }


@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!doctype html>
<html>
  <head><title>Agent Triage Demo</title></head>
  <body>
    <h1>Agent Triage Demo</h1>
    <label for="scenario">Scenario</label>
    <select id="scenario">
      <option value="tool_timeout">tool_timeout</option>
      <option value="retrieval_gap">retrieval_gap</option>
      <option value="ui_contract_gap">ui_contract_gap</option>
      <option value="model_gap">model_gap</option>
    </select>
    <button id="submit">Run scenario</button>
    <pre id="status">idle</pre>
    <script>
      async function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
      document.querySelector('#submit').addEventListener('click', async () => {
        const scenario = document.querySelector('#scenario').value;
        const traceId = `pw-${Date.now()}`;
        const createResp = await fetch('/api/runs', {
          method: 'POST',
          headers: {
            'content-type': 'application/json',
            'x-trace-id': traceId,
            'x-tenant-id': 'qa-gates',
            'x-user-role': 'qa_lead'
          },
          body: JSON.stringify({
            scenario,
            task: 'Generate release risk summary for the candidate build.',
            expected_tools: ['release_summary_tool']
          })
        });
        const created = await createResp.json();
        for (let i = 0; i < 12; i++) {
          const resp = await fetch(`/api/runs/${created.run_id}`);
          const run = await resp.json();
          document.querySelector('#status').textContent = JSON.stringify(run, null, 2);
          if (run.status === 'failed' || run.status === 'succeeded') return;
          await sleep(250);
        }
      });
    </script>
  </body>
</html>
"""
```

本地启动：

```bash
uvicorn agent_triage_demo:app --host 0.0.0.0 --port 8080
```

快速 API 验证：

```bash
curl -s http://127.0.0.1:8080/healthz
curl -s -X POST http://127.0.0.1:8080/api/runs \
  -H 'content-type: application/json' \
  -H 'x-trace-id: manual-triage-001' \
  -H 'x-tenant-id: qa-gates' \
  -H 'x-user-role: qa_lead' \
  -d '{"scenario":"tool_timeout","task":"Generate release risk summary for the candidate build.","expected_tools":["release_summary_tool"]}'
```

这个 Demo 的价值不在于模拟真实 LLM，而在于构造一个可被自动化消费的失败归因环境：你可以稳定复现不同 bucket，并验证测试框架是否能把这些 bucket 正确识别出来。

---

## 4. 工程实践二：用 Golang Ginkgo 把失败分诊嵌进完整 API E2E 旅程

Ginkgo 示例的重点不是“某个接口是否返回 failed”，而是按真实用户路径完成一次任务创建、状态轮询、trace 拉取、audit 校验和 triage 决策输出。单点断言都会下沉到这条旅程里的每一步。

初始化依赖：

```bash
go mod init agent-triage-gate
go get github.com/onsi/ginkgo/v2 github.com/onsi/gomega
```

保存为 `agent_triage_e2e_test.go`：

```go
package triagee2e_test

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
    "os"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type createRunResponse struct {
    RunID   string `json:"run_id"`
    TraceID string `json:"trace_id"`
    Status  string `json:"status"`
}

type runResponse struct {
    RunID    string                 `json:"run_id"`
    TraceID  string                 `json:"trace_id"`
    Status   string                 `json:"status"`
    Stage    string                 `json:"stage"`
    Result   string                 `json:"result"`
    ToolCall []map[string]any       `json:"tool_calls"`
    Triage   map[string]interface{} `json:"triage"`
}

type auditResponse struct {
    Decision string `json:"decision"`
    Bucket   string `json:"bucket"`
    Owner    string `json:"owner"`
}

type traceResponse struct {
    TraceID string                   `json:"trace_id"`
    Spans   []map[string]interface{} `json:"spans"`
}

var _ = Describe("Agent triage E2E", func() {
    It("classifies a release-summary failure from user request to final go/no-go decision", func() {
        baseURL := os.Getenv("AGENT_TRIAGE_BASE_URL")
        if baseURL == "" {
            baseURL = "http://127.0.0.1:8080"
        }

        payload := map[string]any{
            "scenario":       "tool_timeout",
            "task":           "Generate release risk summary for the candidate build.",
            "expected_tools": []string{"release_summary_tool"},
        }
        body, err := json.Marshal(payload)
        Expect(err).NotTo(HaveOccurred())

        req, err := http.NewRequest(http.MethodPost, baseURL+"/api/runs", bytes.NewReader(body))
        Expect(err).NotTo(HaveOccurred())
        req.Header.Set("content-type", "application/json")
        req.Header.Set("x-trace-id", "ginkgo-triage-001")
        req.Header.Set("x-tenant-id", "qa-gates")
        req.Header.Set("x-user-role", "qa_lead")

        createResp, err := http.DefaultClient.Do(req)
        Expect(err).NotTo(HaveOccurred())
        defer createResp.Body.Close()
        Expect(createResp.StatusCode).To(Equal(http.StatusCreated))

        var created createRunResponse
        Expect(json.NewDecoder(createResp.Body).Decode(&created)).To(Succeed())
        Expect(created.Status).To(Equal("running"))
        Expect(created.TraceID).To(Equal("ginkgo-triage-001"))

        var finalRun runResponse
        Eventually(func(g Gomega) string {
            resp, err := http.Get(fmt.Sprintf("%s/api/runs/%s", baseURL, created.RunID))
            g.Expect(err).NotTo(HaveOccurred())
            defer resp.Body.Close()
            g.Expect(resp.StatusCode).To(Equal(http.StatusOK))
            g.Expect(json.NewDecoder(resp.Body).Decode(&finalRun)).To(Succeed())
            g.Expect(finalRun.TraceID).To(Equal(created.TraceID))
            if len(finalRun.ToolCall) > 0 {
                g.Expect(finalRun.ToolCall[0]["name"]).To(Equal("release_summary_tool"))
            }
            return finalRun.Status
        }, 5*time.Second, 250*time.Millisecond).Should(Equal("failed"))

        Expect(finalRun.Stage).To(Equal("triaged"))
        Expect(finalRun.Triage["bucket"]).To(Equal("tool_unavailable"))
        Expect(finalRun.Triage["severity"]).To(Equal("high"))
        Expect(finalRun.Triage["go_no_go"]).To(Equal("block"))
        Expect(finalRun.Result).To(ContainSubstring("timed out"))

        auditResp, err := http.Get(fmt.Sprintf("%s/api/runs/%s/audit", baseURL, created.RunID))
        Expect(err).NotTo(HaveOccurred())
        defer auditResp.Body.Close()
        Expect(auditResp.StatusCode).To(Equal(http.StatusOK))

        var audit auditResponse
        Expect(json.NewDecoder(auditResp.Body).Decode(&audit)).To(Succeed())
        Expect(audit.Decision).To(Equal("block"))
        Expect(audit.Bucket).To(Equal("tool_unavailable"))
        Expect(audit.Owner).To(Equal("agent-tools-team"))

        traceResp, err := http.Get(fmt.Sprintf("%s/api/runs/%s/trace", baseURL, created.RunID))
        Expect(err).NotTo(HaveOccurred())
        defer traceResp.Body.Close()
        Expect(traceResp.StatusCode).To(Equal(http.StatusOK))

        var trace traceResponse
        Expect(json.NewDecoder(traceResp.Body).Decode(&trace)).To(Succeed())
        Expect(trace.TraceID).To(Equal(created.TraceID))
        Expect(trace.Spans).NotTo(BeEmpty())
        Expect(trace.Spans[1]["name"]).To(Equal("tool_call"))
        Expect(trace.Spans[1]["status"]).To(Equal("timeout"))
    })
})
```

执行方式：

```bash
uvicorn agent_triage_demo:app --host 0.0.0.0 --port 8080
AGENT_TRIAGE_BASE_URL=http://127.0.0.1:8080 ginkgo -v ./...
```

这条 Ginkgo 用例有三个关键点。第一，它从“用户发起发布风险总结任务”开始，而不是从某个内部方法开始。第二，它把 `tool_call`、`audit` 和 `trace` 证据合并成一个最终归因结论。第三，它不是只判断是否失败，而是输出 **为什么失败、归谁处理、是否阻断发布**。

---

## 5. 工程实践三：用 Python Playwright 校验“用户看到的失败”是否与系统归因一致

AI QA 很容易出现一种误判：后端 triage 已经正确，但前端仍然展示原始异常堆栈、错误 bucket 与 API 不一致，或者页面一直卡在 running。这时 API E2E 全绿，用户体验仍然是坏的。

Playwright 的职责不是重复后端断言，而是验证用户最终看到的状态是否与 triage contract 一致，且不会暴露不应暴露的内部细节。

安装依赖：

```bash
pip install pytest playwright
playwright install chromium
```

保存为 `test_agent_triage_ui.py`：

```python
import json

from playwright.sync_api import Page, expect


def test_tool_timeout_is_rendered_as_a_triaged_failure(page: Page):
    page.goto("http://127.0.0.1:8080")

    page.locator("#scenario").select_option("tool_timeout")
    page.locator("#submit").click()

    status = page.locator("#status")
    expect(status).to_contain_text('"status": "failed"', timeout=5000)
    expect(status).to_contain_text('"bucket": "tool_unavailable"')
    expect(status).to_contain_text('"go_no_go": "block"')
    expect(status).to_contain_text('release_summary_tool timed out')

    rendered = status.text_content() or ""
    assert "Traceback" not in rendered
    assert "ConnectionResetError" not in rendered
    assert "password" not in rendered.lower()


def test_ui_contract_gap_exposes_an_e2e_consistency_problem(page: Page):
    page.goto("http://127.0.0.1:8080")

    page.locator("#scenario").select_option("ui_contract_gap")
    page.locator("#submit").click()

    status = page.locator("#status")
    expect(status).to_contain_text('"status": "succeeded"', timeout=5000)
    expect(status).to_contain_text('"bucket": "ui_state_desync"')
    expect(status).to_contain_text('"go_no_go": "block"')
```

执行方式：

```bash
uvicorn agent_triage_demo:app --host 0.0.0.0 --port 8080
pytest -q test_agent_triage_ui.py
```

第二条用例看起来“奇怪”：为什么状态是 succeeded，却仍然应该阻断？这正是 Agent 归因系统的价值所在。对用户来说，这是一条生成成功的任务；但对质量门禁来说，它属于 `ui_state_desync`，说明 UI 契约或状态同步机制已经失真。如果没有这种 E2E 视角，团队很容易把它误判成“非阻断问题”。

---

## 6. 工程实践四：把 triage 结果接入 K8s 发布门禁

当 Agent 服务部署在 Kubernetes 上时，失败归因不能停留在应用层。一次 `tool_unavailable` 可能来自工具服务本身，也可能来自 DNS、NetworkPolicy、Sidecar、Secret 注入、资源限制或错误的服务发现。对发布门禁来说，应用层 bucket 与运行时证据必须一起看。

下面给出一份最小 Job 示例，用于在 `qa-gates` 命名空间中执行 triage E2E，并把失败时的日志和事件作为证据收集出来。

保存为 `agent-triage-gate-job.yaml`：

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: agent-triage-gate
  namespace: qa-gates
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: e2e
          image: ghcr.io/example/agent-triage-e2e:latest
          imagePullPolicy: IfNotPresent
          env:
            - name: AGENT_TRIAGE_BASE_URL
              value: http://agent-triage-demo.qa-gates.svc.cluster.local:8080
          command: ["/bin/sh", "-c"]
          args:
            - |
              set -euo pipefail
              ginkgo -v ./...
```

发布流水线中的执行方式可以是：

```bash
kubectl -n qa-gates rollout status deploy/agent-triage-demo --timeout=120s
kubectl apply -f agent-triage-gate-job.yaml
kubectl -n qa-gates wait --for=condition=complete job/agent-triage-gate --timeout=180s || true
kubectl -n qa-gates logs job/agent-triage-gate
kubectl -n qa-gates describe job agent-triage-gate
kubectl -n qa-gates get pods -l job-name=agent-triage-gate -o wide
kubectl -n qa-gates get events --sort-by=.lastTimestamp | tail -n 30
```

如果 Job 失败，Senior SDET 不应该直接把所有失败都归为 `k8s_runtime_error`。更好的做法是用规则把应用层与基础设施层证据合并起来。例如：

- 如果 Ginkgo 报告 `tool_unavailable`，同时 Pod 无重启、DNS 正常、工具服务 5xx 激增，那么主 bucket 保持 `tool_unavailable`。
- 如果 Ginkgo 报告工具超时，但事件里有 `FailedMount` 或 DNS 解析失败，那么主 bucket 应升级为 `k8s_runtime_error`，工具超时只是表象。
- 如果应用层全部通过，但 Job 因环境抖动偶发失败且重跑恢复，则更接近 `test_flake`。

真正成熟的 triage gate，不是简单拼接日志，而是要有 **主 bucket 选择规则**。

---

## 7. 分诊规则设计：如何区分产品回归、环境问题和测试抖动

### 7.1 不要让 test flake 吞掉真实回归

很多团队一看到不稳定失败，就倾向于把它们全部归为 flaky。这样做的短期收益很诱人：看板马上干净，CI 通过率上升，报警减少。但它最大的风险是把真实回归伪装成了噪声。

对 Agent 场景，建议至少满足下面三个条件，才能把失败认定为 `test_flake`：

1. 同一构建、同一数据、同一环境下重试可稳定恢复。
2. 恢复后产品证据链完整，没有隐藏的 bucket 残留。
3. 失败模式与已知环境噪声特征匹配，例如 browser 启动抖动、测试账号竞争、暂态网络失败。

如果一次失败在重试后通过，但 audit 缺失、trace 断裂或 UI 仍出现不一致，就不能轻易归为 flake。它更可能是“高恢复性的真实缺陷”。

### 7.2 用主 bucket + 候选根因，替代“一个失败贴十个标签”

失败分析里另一个常见问题，是把一条失败同时贴上太多标签：tool、ui、model、infra、data 全都有关，结果没有任何实际价值。为了支持自动化决策，建议每次失败必须选出一个 **主 bucket**，同时保留一个候选根因列表。

主 bucket 的选择建议遵循“距离用户任务断点最近、且最能解释阻断动作”的原则。例如：

- 工具调用超时导致最终结果为空，UI 只是正确展示错误，那么主 bucket 是 `tool_unavailable`，不是 `ui_state_desync`。
- API 成功，结果正确，但前端没有展示终态，用户持续看到 running，那么主 bucket 是 `ui_state_desync`。
- 用户结果正确，但审计事件缺失，而你的发布策略明确要求可追责，那么主 bucket 是 `audit_missing`。
- 任务失败时同时出现 DNS 失败与工具超时，且所有工具都不可达，那么主 bucket 应优先归到 `k8s_runtime_error`。

### 7.3 自动化规则应明确哪些 bucket 可以 review，哪些必须 block

为了让分诊结果能真正进入发布流程，bucket 需要映射到处置等级。下面是一个常见但有效的映射思路：

- **必须 block**：`contract_breaking`、`tool_unavailable`（Gold 样本）、`ui_state_desync`、`audit_missing`、`k8s_runtime_error`
- **默认 review**：`retrieval_miss`、`model_quality_regression`
- **先 retry 再 review**：`test_flake`

这里最重要的不是映射本身，而是要把这张表制度化。只有当发布负责人、QA 和研发对 bucket-to-action 的规则有共识，自动分诊才能成为可信输入，而不是“系统的一个建议”。

---

## 8. 组织化治理：让 triage 输出能被团队长期消费

### 8.1 owner 映射要稳定，不能每次手工猜

如果一次失败被归为 `retrieval_miss`，但系统没有固定 owner mapping，最终仍然需要 QA 自己去找知识平台、业务研发还是 Prompt 负责人，那就说明 triage 只完成了一半。建议对每个主 bucket 维护长期稳定的 owner map，并随着组织变化集中更新。

例如：

- `tool_unavailable` → tools/platform owner
- `ui_state_desync` → frontend owner
- `audit_missing` → agent platform / governance owner
- `model_quality_regression` → model quality / prompt owner
- `k8s_runtime_error` → infra / SRE owner

owner map 的意义不是完全替代人工判断，而是把 80% 的常见失败直接路由到最可能的处理方。

### 8.2 质量看板不要只看 pass rate，要看 triage 分布

对 Agent 质量系统来说，单独看通过率是远远不够的。一次模型升级把 pass rate 从 95% 打到 91%，这件事本身不说明问题严重不严重；真正关键的是下降发生在哪些 bucket。

如果新增失败主要来自 `model_quality_regression`，说明是语义质量变化。如果新增失败主要来自 `audit_missing`，说明合规链路回归。如果失败集中在 `test_flake`，说明测试系统稳定性需要治理。如果 `tool_unavailable` 暴增，就要重点检查依赖服务和运行时边界。

所以更有行动价值的看板，至少应包含四条主视图：

1. 按 bucket 的失败数量与趋势。
2. 按 owner 的待处理失败分布。
3. 按 suite（Gold/Regression/Canary）区分的阻断比例。
4. 按构建版本聚合的 go/no-go 决策结果。

### 8.3 triage 输出应该进入缺陷模板，而不是停留在测试日志里

自动化分诊的最终归宿不应该只是 CI 控制台。更好的方式是：当失败达到阈值或属于阻断 bucket 时，系统自动生成标准化缺陷或回归记录，把 `case_id`、`run_id`、`trace_id`、主 bucket、证据链接、建议 owner 和复现步骤一起带上。

这样研发拿到的不是“某条用例 failed”，而是一份结构化的失败包。对排查效率的提升通常比单纯增加日志更大。

---

## 9. E2E 用例设计示例：发布风险总结任务的自动化分诊

下面是一条符合 E2E 风格的用例设计。它不会单独拆成“工具超时测试”“UI 状态测试”“审计字段测试”三条碎片用例，而是把所有验证点组织到同一条业务旅程里。

**场景名称：** QA Lead 在候选版本发布前，从 Web 页面发起“生成发布风险总结”任务；若 Agent 依赖工具超时，系统应将失败归类为 `tool_unavailable`，阻断发布，并输出完整可定位证据。

**业务背景：** 团队准备放量一个新的发布候选版本，希望 Agent 自动汇总本次构建的高风险项，包括失败用例、告警、依赖变更和回滚建议。

**执行步骤与预期中间状态：**

1. QA Lead 打开 Agent 页面，选择 `tool_timeout` 场景并点击运行。预期 run 创建成功，返回 `run_id` 与 `trace_id`，页面进入 running。
2. 后端进入 planner 和 tool_call 阶段。预期系统尝试调用 `release_summary_tool`，并把相同 `trace_id` 贯穿到 tool_call 记录与 audit 事件。
3. 工具发生超时。预期最终 run 进入 `failed`，主 bucket 为 `tool_unavailable`，severity 为 `high`，go/no-go 为 `block`。
4. 前端收到终态。预期页面展示结构化失败结果，而不是原始堆栈、浏览器默认异常或永远停留在 running。
5. 测试框架拉取 audit 和 trace。✅ 最终验证点是：audit 中存在 bucket、owner、decision；trace 中能看到 `tool_call=timeout`；K8s gate 将本次任务判定为 block；失败被路由到工具平台 owner，而不是被误报为 flaky。

这条用例的价值在于，它把“失败后如何判断与如何行动”纳入了 E2E 验收范围。不是等失败发生后再让人手工 triage，而是让 triage 本身成为被测试的产品能力。

---

## 10. Exercises

1. **扩展 bucket 设计：** 在 `agent_triage_demo.py` 中新增一个 `audit_gap` 场景，让任务结果成功返回，但 `/audit` 缺少 `decision` 字段。思考这类失败为什么通常应该归到 `audit_missing` 而不是 `contract_breaking`。
2. **增加二次判定规则：** 让 Ginkgo 在第一次失败后自动重试一次。如果第二次通过，你会保留 `tool_unavailable` 还是降级为 `test_flake`？请给出你的规则与理由。
3. **补齐 UI 证据：** 修改 Playwright 用例，在失败时同时截图并保存页面中的 triage JSON 摘要。思考哪些字段适合展示给用户，哪些字段只应该进入内部证据。
4. **接入运行时信号：** 在 K8s gate 中额外采集 `kubectl top pod`、`describe pod` 与最近 30 条 event，设计一个简单规则，让系统在 `tool_unavailable` 与 `k8s_runtime_error` 之间自动选择主 bucket。
5. **设计看板指标：** 假设连续三天 Gold 样本通过率从 97% 降到 92%，但新增失败全部来自 `model_quality_regression`。你会如何决定是否继续灰度，以及应要求哪些补充证据？

---

## 11. Daily wrap-up

今天我们把 AI QA 的关注点从“如何发现失败”推进到“如何让失败自动产生工程动作”。核心结论是：Agent 失败归因不是报错文本分类，而是对完整用户任务闭环进行断点定位。只有把 run 状态、tool_call、trace、audit、UI 状态和 K8s 运行时证据放到同一个 triage contract 里，失败才真正具备可分派、可阻断、可复盘的价值。

从工程实践上看，一次有质量的 E2E 分诊至少要做到四件事：第一，证明失败发生在用户旅程的哪一个阶段。第二，给出主 bucket、severity 和 go/no-go 动作。第三，把 API、UI 与运行时证据聚合成统一事实。第四，让 owner 路由和后续治理自动发生，而不是继续依赖 QA 人肉解释。

对 Senior SDET 来说，真正成熟的质量门禁不是“有失败就红灯”，而是“红灯一亮，系统已经告诉你这是什么问题、应该找谁、是否要挡发布”。明天可以继续深入“AI Agent 发布评分卡与 Go/No-Go 决策”，把今天的 triage 结果进一步汇总为版本级风险判断，让质量系统从单次失败分析升级到全局发布决策。
