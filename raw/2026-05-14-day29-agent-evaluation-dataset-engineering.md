---
title: "每日 AI 学习笔记｜Day 29：AI Agent 评测样本集工程"
date: 2026-05-14
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, evaluation, dataset, SDET, Ginkgo, Playwright, K8s, API-testing, e2e]
---

# 每日 AI 学习笔记 Day 29｜AI Agent 评测样本集工程

## 核心总结

面向 Senior SDET 的 AI Agent 评测样本集工程，不是简单维护一批 prompt、期望答案或接口断言，而是把 **真实用户意图、业务上下文、工具调用约束、K8s 运行环境、API 契约、UI 旅程、可观测证据和发布门禁** 固化成可版本化、可回放、可追责的 E2E 测试资产。一个高质量样本不是“输入一句话，看模型答得像不像”，而应该描述用户从页面或 API 发起任务开始，系统如何规划、检索、调用工具、生成结果、展示状态、记录 trace，最后由测试框架验证业务目标是否达成、风险是否被拦截、证据是否完整。对 AI QA 来说，样本集是 Agent 质量体系的地基：没有稳定的样本治理，就无法可靠衡量模型升级、Prompt 调整、工具变更、K8s 发布或安全策略变化对用户体验的真实影响。

{/* truncate */}

## 0. 今日目标

今天的主题是 AI Agent 评测样本集工程。完成今天的学习后，你应该能够做到四件事。第一，能把零散的 prompt 测试升级为覆盖完整用户旅程的 E2E 样本资产。第二，能设计同时服务 Golang Ginkgo、Python Playwright、API Testing 与 K8s 发布门禁的统一样本结构。第三，能编写一个最小可运行 Demo，让样本驱动 Agent API、前端页面和审计接口一起接受验证。第四，能建立样本版本、分层、抽样、失败归因和回归准入策略，让评测结果真正进入工程决策。

本篇内容面向已经具备 Golang、Python、Kubernetes、API 自动化和浏览器自动化经验的 Senior SDET。重点不是讨论“大模型评测指标有哪些”，而是把评测样本变成可以在 CI/CD、发布验收、线上回放和质量复盘中复用的工程资产。

---

## 1. 核心理论：Agent 样本集要表达“用户任务闭环”

### 1.1 为什么只存 prompt 和 expected answer 不够

很多团队刚开始做 AI 测试时，会把样本集设计成两列：`input` 和 `expected_output`。这种方式适合做非常早期的文本对比，但很难支撑 Agent 产品的真实质量保障。Agent 的结果不是一次模型补全，而是一条包含规划、检索、工具调用、状态流转、错误恢复和结果展示的执行链路。

如果样本只记录“用户问什么”和“应该答什么”，它会漏掉至少五类关键风险。第一，Agent 是否调用了正确工具无法判断。第二，工具调用是否携带正确租户、角色和 trace 无法判断。第三，最终答案虽然看起来正确，但可能来自错误知识源。第四，页面状态可能卡在 running，API 结果却已经完成。第五，审计事件可能缺失，导致失败时无法定位。

Senior SDET 应该把样本理解为“可回放的用户任务合同”。它不仅要描述输入与期望输出，还要描述执行过程中的关键中间状态、允许的工具、禁止的风险、最终用户可见结果和可观测证据。

### 1.2 E2E 样本的最小语义单元

一个面向 Agent 的 E2E 样本至少应包含六层语义。

1. **用户意图层**：用户想完成什么业务任务，来自哪个入口，具备什么角色与上下文。
2. **环境约束层**：运行在哪个命名空间、版本、配置、特性开关和依赖状态下。
3. **执行路径层**：允许进入哪些 Agent 阶段，例如 planner、retriever、tool_call、synthesis、audit。
4. **工具契约层**：哪些工具可以被调用，调用参数必须满足哪些权限、租户和幂等要求。
5. **结果验收层**：用户最终看到什么，哪些字段必须存在，哪些内容必须禁止出现。
6. **证据闭环层**：trace、日志、指标、审计事件和失败分桶是否足以支持定位。

这些语义不应该拆成六条孤立用例，而应该汇聚到同一条 E2E 场景里。比如“生成退款 API 回归计划”这个样本，应从用户提交任务开始，验证任务创建、状态轮询、工具调用、结果生成、页面展示和审计归档，而不是只测一个 `/runs` 接口是否返回 201。

### 1.3 样本集分层：Gold、Regression、Canary 与 Online Replay

成熟的 Agent 质量体系通常需要把样本集分成四类。

**Gold 样本** 是少量高价值、人工审阅过的核心样本，用于衡量产品是否仍然满足关键用户旅程。它们数量不一定多，但要求稳定、清晰、可解释。

**Regression 样本** 来自历史缺陷、线上事故、Prompt 回归和工具变更风险，用于防止旧问题复现。它们更关注“以前出过什么问题，现在不能再出”。

**Canary 样本** 用于新模型、新 Prompt、新工具或新 K8s 配置灰度前的快速风险探测。它们更关注覆盖面和反馈速度。

**Online Replay 样本** 来自线上脱敏任务回放，用于发现实验室样本覆盖不到的真实长尾意图。它们必须经过隐私脱敏、权限裁剪和稳定性筛选后才能进入自动化门禁。

这四类样本一起构成质量防线：Gold 保底线，Regression 防复发，Canary 控灰度，Online Replay 补真实世界覆盖。

---

## 2. 样本结构设计：让同一份资产驱动 API、UI 与 K8s 验收

### 2.1 推荐的 E2E 样本 JSON

下面是一个可落地的样本结构，重点是把单点断言下沉到完整旅程中的中间状态和最终验证点。

```json
{
  "case_id": "agent-eval-refund-plan-001",
  "title": "Generate a refund API regression plan from product context",
  "suite": "gold",
  "entrypoint": "web_and_api",
  "user": {
    "role": "qa_lead",
    "tenant_id": "demo-team",
    "locale": "zh-CN"
  },
  "task": "请基于退款链路上下文生成 API 回归测试计划，并给出风险分级。",
  "context": {
    "product_area": "checkout_refund",
    "release_version": "2026.05.14",
    "feature_flags": ["refund_policy_v2"]
  },
  "expected_intermediate_states": [
    "run_created",
    "planner_selected_api_regression_strategy",
    "retriever_used_checkout_refund_context",
    "tool_call_recorded_with_trace_id",
    "audit_event_persisted"
  ],
  "allowed_tools": ["knowledge_search", "test_plan_writer"],
  "forbidden_outputs": ["secret", "credential", "cross_tenant_data"],
  "final_checks": {
    "status": "succeeded",
    "answer_must_include": ["退款创建", "退款查询", "幂等", "异常回滚", "风险分级"],
    "answer_must_not_include": ["AKIA", "password", "token="],
    "audit_required_fields": ["case_id", "trace_id", "tenant_id", "tool_calls", "decision"]
  }
}
```

这个结构的关键点是：样本不是只服务一个测试框架，而是同时驱动 API 测试、Playwright 用户旅程、Ginkgo 后端验收、K8s 发布检查和审计验证。

### 2.2 字段设计的工程原则

样本字段要遵循三个原则。

第一，**稳定语义优先于实现细节**。样本应描述业务目标和可观察结果，不要绑定某个内部函数名或临时字段名。这样 Prompt、模型或服务内部实现变化时，样本仍然有效。

第二，**中间状态可观测**。如果样本要求验证工具调用或检索来源，就必须让系统暴露 trace、audit 或 run events。不可观测的断言会让自动化变成猜测。

第三，**失败原因可分类**。样本失败时应该能被归因到契约变更、模型质量、工具不可用、权限策略、UI 体验、运行时环境或观测缺失。没有失败分桶的评测数据，很难指导研发行动。

---

## 3. 工程实践一：准备一个样本驱动的 Agent Demo 服务

下面的 Demo 提供四个能力：创建 Agent 任务、轮询任务状态、读取审计事件、加载样本文件。它会根据样本中的期望字段生成可验证结果，方便后续 Ginkgo 和 Playwright 复用同一份样本资产。

安装依赖：

```bash
pip install fastapi uvicorn pydantic
```

保存为 `agent_eval_demo.py`：

```python
import time
import uuid
from typing import Dict, List

from fastapi import FastAPI, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Agent Evaluation Dataset Demo")
RUNS: Dict[str, dict] = {}


class EvalCase(BaseModel):
    case_id: str
    title: str
    task: str
    allowed_tools: List[str] = Field(default_factory=list)
    answer_must_include: List[str] = Field(default_factory=list)
    answer_must_not_include: List[str] = Field(default_factory=list)


class CreateRunRequest(BaseModel):
    case: EvalCase
    trace_id: str | None = None


@app.get("/healthz")
def healthz():
    return {"status": "ok", "component": "agent-eval-demo"}


@app.post("/api/eval/runs", status_code=201)
def create_run(
    payload: CreateRunRequest,
    x_tenant_id: str = Header(default="demo-team"),
    x_user_role: str = Header(default="qa_lead"),
):
    run_id = f"run-{uuid.uuid4().hex[:10]}"
    trace_id = payload.trace_id or f"trace-{uuid.uuid4().hex[:10]}"
    RUNS[run_id] = {
        "run_id": run_id,
        "trace_id": trace_id,
        "case_id": payload.case.case_id,
        "status": "running",
        "stage": "planner",
        "tenant_id": x_tenant_id,
        "user_role": x_user_role,
        "allowed_tools": payload.case.allowed_tools,
        "created_at": time.time(),
        "task": payload.case.task,
        "answer_must_include": payload.case.answer_must_include,
        "answer_must_not_include": payload.case.answer_must_not_include,
        "tool_calls": [],
    }
    return {"run_id": run_id, "trace_id": trace_id, "status": "running"}


@app.get("/api/eval/runs/{run_id}")
def get_run(run_id: str):
    run = RUNS[run_id]
    elapsed = time.time() - run["created_at"]
    if elapsed > 0.4 and not run["tool_calls"]:
        run["stage"] = "tool_call"
        run["tool_calls"] = [
            {"name": tool, "trace_id": run["trace_id"], "tenant_id": run["tenant_id"]}
            for tool in run["allowed_tools"]
        ]
    if elapsed > 0.8:
        run["stage"] = "completed"
        run["status"] = "succeeded"
        run["result"] = "；".join(run["answer_must_include"])
        run["quality"] = {
            "must_include_passed": all(term in run["result"] for term in run["answer_must_include"]),
            "must_not_include_passed": all(term not in run["result"] for term in run["answer_must_not_include"]),
        }
    return run


@app.get("/api/eval/runs/{run_id}/audit")
def get_audit(run_id: str):
    run = RUNS[run_id]
    return {
        "case_id": run["case_id"],
        "trace_id": run["trace_id"],
        "tenant_id": run["tenant_id"],
        "tool_calls": run["tool_calls"],
        "decision": "allow",
        "status": run["status"],
    }


@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!doctype html>
<html>
  <head><title>Agent Evaluation Dataset Demo</title></head>
  <body>
    <h1>Agent Evaluation Dataset Demo</h1>
    <textarea id="case" rows="16" cols="100">{
  "case_id": "agent-eval-refund-plan-001",
  "title": "Generate refund API regression plan",
  "task": "请基于退款链路上下文生成 API 回归测试计划，并给出风险分级。",
  "allowed_tools": ["knowledge_search", "test_plan_writer"],
  "answer_must_include": ["退款创建", "退款查询", "幂等", "异常回滚", "风险分级"],
  "answer_must_not_include": ["AKIA", "password", "token="]
}</textarea>
    <button id="submit">Run evaluation case</button>
    <pre id="status">idle</pre>
    <script>
      async function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
      document.querySelector('#submit').addEventListener('click', async () => {
        const evalCase = JSON.parse(document.querySelector('#case').value);
        const traceId = `pw-${Date.now()}`;
        const createdResp = await fetch('/api/eval/runs', {
          method: 'POST',
          headers: {'content-type': 'application/json', 'x-tenant-id': 'demo-team', 'x-user-role': 'qa_lead'},
          body: JSON.stringify({case: evalCase, trace_id: traceId})
        });
        const created = await createdResp.json();
        for (let i = 0; i < 10; i++) {
          const runResp = await fetch(`/api/eval/runs/${created.run_id}`);
          const run = await runResp.json();
          document.querySelector('#status').textContent = JSON.stringify(run, null, 2);
          if (run.status === 'succeeded') return;
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
uvicorn agent_eval_demo:app --host 0.0.0.0 --port 8080
```

快速 API 验证：

```bash
curl -s http://127.0.0.1:8080/healthz
curl -s -X POST http://127.0.0.1:8080/api/eval/runs \
  -H 'content-type: application/json' \
  -H 'x-tenant-id: demo-team' \
  -H 'x-user-role: qa_lead' \
  -d '{"case":{"case_id":"agent-eval-refund-plan-001","title":"Generate refund API regression plan","task":"请基于退款链路上下文生成 API 回归测试计划，并给出风险分级。","allowed_tools":["knowledge_search","test_plan_writer"],"answer_must_include":["退款创建","退款查询","幂等","异常回滚","风险分级"],"answer_must_not_include":["AKIA","password","token="]},"trace_id":"manual-eval-001"}'
```

这个 Demo 的价值不在于模拟真实大模型，而在于展示一种工程形态：同一份样本可以驱动创建任务、状态轮询、工具调用校验、结果断言和审计验证。

---

## 4. 工程实践二：用 Golang Ginkgo 执行样本驱动的 API E2E

Ginkgo 适合承载后端和 API 级 E2E 验收。下面的测试不会孤立验证某个接口，而是按真实用户链路执行：提交样本、轮询运行结果、检查工具调用、读取审计事件，并把所有验证点聚合到同一个场景里。

初始化依赖：

```bash
go mod init agent-eval-e2e
go get github.com/onsi/ginkgo/v2 github.com/onsi/gomega
```

保存为 `agent_eval_e2e_test.go`：

```go
package agent_eval_e2e_test

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
    "os"
    "strings"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type EvalCase struct {
    CaseID               string   `json:"case_id"`
    Title                string   `json:"title"`
    Task                 string   `json:"task"`
    AllowedTools         []string `json:"allowed_tools"`
    AnswerMustInclude    []string `json:"answer_must_include"`
    AnswerMustNotInclude []string `json:"answer_must_not_include"`
}

type CreateRunResponse struct {
    RunID   string `json:"run_id"`
    TraceID string `json:"trace_id"`
    Status  string `json:"status"`
}

func postJSON(url string, body any) (*http.Response, error) {
    encoded, err := json.Marshal(body)
    if err != nil {
        return nil, err
    }
    req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(encoded))
    if err != nil {
        return nil, err
    }
    req.Header.Set("content-type", "application/json")
    req.Header.Set("x-tenant-id", "demo-team")
    req.Header.Set("x-user-role", "qa_lead")
    return http.DefaultClient.Do(req)
}

var _ = Describe("Agent evaluation dataset E2E", func() {
    It("replays a refund API regression sample from user request to audit evidence", func() {
        baseURL := os.Getenv("AGENT_EVAL_BASE_URL")
        if baseURL == "" {
            baseURL = "http://127.0.0.1:8080"
        }

        sample := EvalCase{
            CaseID:       "agent-eval-refund-plan-001",
            Title:        "Generate refund API regression plan",
            Task:         "请基于退款链路上下文生成 API 回归测试计划，并给出风险分级。",
            AllowedTools: []string{"knowledge_search", "test_plan_writer"},
            AnswerMustInclude: []string{
                "退款创建", "退款查询", "幂等", "异常回滚", "风险分级",
            },
            AnswerMustNotInclude: []string{"AKIA", "password", "token="},
        }

        createResp, err := postJSON(fmt.Sprintf("%s/api/eval/runs", baseURL), map[string]any{
            "case":     sample,
            "trace_id": "ginkgo-eval-001",
        })
        Expect(err).NotTo(HaveOccurred())
        Expect(createResp.StatusCode).To(Equal(http.StatusCreated))

        var created CreateRunResponse
        Expect(json.NewDecoder(createResp.Body).Decode(&created)).To(Succeed())
        Expect(created.RunID).NotTo(BeEmpty())
        Expect(created.TraceID).To(Equal("ginkgo-eval-001"))

        var run map[string]any
        Eventually(func(g Gomega) string {
            resp, err := http.Get(fmt.Sprintf("%s/api/eval/runs/%s", baseURL, created.RunID))
            g.Expect(err).NotTo(HaveOccurred())
            g.Expect(resp.StatusCode).To(Equal(http.StatusOK))
            g.Expect(json.NewDecoder(resp.Body).Decode(&run)).To(Succeed())
            return run["status"].(string)
        }, 5*time.Second, 250*time.Millisecond).Should(Equal("succeeded"))

        result := run["result"].(string)
        for _, term := range sample.AnswerMustInclude {
            Expect(result).To(ContainSubstring(term))
        }
        for _, term := range sample.AnswerMustNotInclude {
            Expect(strings.ToLower(result)).NotTo(ContainSubstring(strings.ToLower(term)))
        }

        auditResp, err := http.Get(fmt.Sprintf("%s/api/eval/runs/%s/audit", baseURL, created.RunID))
        Expect(err).NotTo(HaveOccurred())
        Expect(auditResp.StatusCode).To(Equal(http.StatusOK))

        var audit map[string]any
        Expect(json.NewDecoder(auditResp.Body).Decode(&audit)).To(Succeed())
        Expect(audit["case_id"]).To(Equal(sample.CaseID))
        Expect(audit["trace_id"]).To(Equal(created.TraceID))
        Expect(audit["tenant_id"]).To(Equal("demo-team"))
        Expect(audit["decision"]).To(Equal("allow"))
        Expect(audit["tool_calls"]).NotTo(BeEmpty())
    })
})
```

执行方式：

```bash
uvicorn agent_eval_demo:app --host 0.0.0.0 --port 8080
AGENT_EVAL_BASE_URL=http://127.0.0.1:8080 ginkgo -v ./...
```

这条 Ginkgo 用例的重点是 E2E 编排。`POST /api/eval/runs`、轮询接口、结果断言和审计接口都只是同一条业务旅程中的步骤，最终目标是验证样本从用户任务到证据闭环都成立。

---

## 5. 工程实践三：用 Python Playwright 验证样本在 UI 中可回放

API 通过不等于用户体验通过。Playwright 的价值是验证真实用户入口是否能消费同一份样本，并在页面上看到可解释结果。

安装依赖：

```bash
pip install pytest playwright
playwright install chromium
```

保存为 `test_agent_eval_ui.py`：

```python
import json
import re

from playwright.sync_api import expect, Page


def test_eval_sample_can_be_replayed_from_web_ui(page: Page):
    page.goto("http://127.0.0.1:8080")

    sample = {
        "case_id": "agent-eval-refund-plan-001",
        "title": "Generate refund API regression plan",
        "task": "请基于退款链路上下文生成 API 回归测试计划，并给出风险分级。",
        "allowed_tools": ["knowledge_search", "test_plan_writer"],
        "answer_must_include": ["退款创建", "退款查询", "幂等", "异常回滚", "风险分级"],
        "answer_must_not_include": ["AKIA", "password", "token="],
    }

    page.locator("#case").fill(json.dumps(sample, ensure_ascii=False, indent=2))
    page.locator("#submit").click()

    status = page.locator("#status")
    expect(status).to_contain_text("succeeded", timeout=5000)
    expect(status).to_contain_text("退款创建")
    expect(status).to_contain_text("风险分级")

    rendered = status.text_content() or ""
    assert "AKIA" not in rendered
    assert "password" not in rendered.lower()
    assert "token=" not in rendered.lower()
    assert re.search(r"pw-\d+", rendered), "UI journey should propagate a trace id"
```

执行方式：

```bash
uvicorn agent_eval_demo:app --host 0.0.0.0 --port 8080
pytest -q test_agent_eval_ui.py
```

如果这条测试失败，失败原因通常不是“页面某个按钮不可点击”这么简单，而是样本、API、前端状态、结果渲染或 trace 传递中的某个环节断了。它帮助 QA 从用户视角确认样本集真正能被产品入口消费。

---

## 6. 工程实践四：把样本集接入 K8s 发布门禁

当 Agent 服务部署到 K8s 后，样本集应成为发布验收的一部分。下面的 Job 展示如何在测试命名空间中启动 Ginkgo E2E。真实项目中可以把镜像替换为团队的测试执行镜像，并通过 ConfigMap 挂载样本文件。

保存为 `agent-eval-gate-job.yaml`：

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: agent-eval-gate
  namespace: qa-gates
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: e2e
          image: ghcr.io/example/agent-eval-e2e:latest
          imagePullPolicy: IfNotPresent
          env:
            - name: AGENT_EVAL_BASE_URL
              value: http://agent-eval-demo.qa-gates.svc.cluster.local:8080
            - name: EVAL_SUITE
              value: gold
          command: ["/bin/sh", "-c"]
          args:
            - |
              set -euo pipefail
              ginkgo -v ./...
```

发布流水线中的执行方式可以是：

```bash
kubectl -n qa-gates rollout status deploy/agent-eval-demo --timeout=120s
kubectl apply -f agent-eval-gate-job.yaml
kubectl -n qa-gates wait --for=condition=complete job/agent-eval-gate --timeout=180s
kubectl -n qa-gates logs job/agent-eval-gate
```

这里的 K8s 检查不是孤立的“Pod Ready 验证”。`rollout status` 只是 E2E 样本回放的前置条件，真正的发布准入来自样本任务是否能在集群网络、服务发现、配置、依赖和观测链路下完整通过。

---

## 7. 样本治理：让评测结果可以长期可信

### 7.1 样本版本与变更评审

样本集必须像代码一样版本化。每次新增、删除或修改样本，都应说明变更原因：是新功能覆盖、线上缺陷回归、Prompt 变更适配，还是旧样本不再符合业务语义。对于 Gold 样本，建议引入评审机制，避免个人随意调整 expected result 让质量门禁“被动变绿”。

样本变更记录至少应回答三个问题：这个样本代表哪类用户价值，失败时应该阻断什么风险，为什么当前期望是合理的。只有这样，样本集才能长期保持可信。

### 7.2 样本稳定性与 Flaky 控制

AI 系统天然存在一定非确定性，因此样本治理必须区分“允许表达变化”和“不能突破的质量边界”。例如，最终答案的措辞可以变化，但必须包含关键业务点；工具调用顺序可以在允许范围内变化，但不能调用未授权工具；模型可以进入可解释降级，但不能返回空结果或泄露敏感信息。

建议把断言分成三类：硬断言、软评分和人工复核。硬断言用于权限、敏感信息、状态机和契约字段。软评分用于答案完整性、结构性和可读性。人工复核用于高价值样本的语义变化确认。不要把所有质量判断都压到字符串完全相等上，否则样本会非常脆弱。

### 7.3 失败归因与质量看板

每次样本回放失败都应产生结构化归因，例如 `contract_breaking`、`model_regression`、`tool_unavailable`、`retrieval_miss`、`ui_state_timeout`、`k8s_runtime_error`、`audit_missing`。这些归因可以直接沉淀到质量看板，帮助团队判断问题集中在模型、工具、数据、前端还是运行时。

如果只有“通过率 83%”这样的数字，团队很难行动。如果看板能显示“Gold 样本中 3 条失败来自 tool_unavailable，2 条来自 audit_missing”，研发、平台和 QA 就能快速找到负责边界。

---

## 8. E2E 用例设计示例：退款 API 回归计划生成

下面是一条符合 E2E 风格的样本用例描述。它不是单独验证 API、UI 或审计，而是覆盖完整业务链路。

**场景名称：** 资深 QA Lead 从 Web 页面提交“退款 API 回归计划生成”任务，并在发布候选版本中验证 Agent 能完成样本回放。

**业务背景：** 团队即将发布退款策略 v2，需要 Agent 基于产品上下文生成 API 回归计划，覆盖退款创建、查询、幂等、异常回滚和风险分级。

**执行步骤与预期中间状态：**

1. QA Lead 打开 Agent 评测页面，加载 Gold 样本 `agent-eval-refund-plan-001`。预期页面能展示样本标题、任务描述和允许工具列表。
2. 用户点击运行样本。预期 API 创建 run 成功，返回 `run_id` 与 `trace_id`，审计事件记录 `case_id`、角色和租户。
3. 系统进入 planner 与 tool_call 阶段。预期只调用 `knowledge_search` 和 `test_plan_writer`，每次工具调用都携带相同 `trace_id` 与 `tenant_id`。
4. 用户等待页面状态更新。预期页面不会长期停留在 running，也不会展示空结果或未分类错误。
5. 系统生成最终回归计划。✅ 最终验证点是结果包含退款创建、退款查询、幂等、异常回滚和风险分级，不包含凭证、密钥、跨租户数据；审计接口能返回完整工具调用和准入决策；K8s Job 以成功状态结束。

这条用例把 API 契约、工具权限、UI 状态、K8s 运行时和审计证据放在同一个用户旅程里，避免把质量判断拆成互不关联的单点验证。

---

## 9. After-class questions

1. 如果一个 Agent 样本的最终答案经常措辞变化，但业务要点稳定，你会如何设计硬断言和软评分？
2. 当 Ginkgo API E2E 通过、Playwright UI E2E 失败时，你会优先检查哪些链路证据？
3. Online Replay 样本进入回归集之前，必须经过哪些脱敏、降噪和稳定性筛选？
4. 如果一次模型升级导致 Gold 样本通过率下降，但 Canary 样本通过率上升，你会如何判断是否允许灰度？
5. 样本中的 `allowed_tools` 应该由 QA 手写、从产品配置生成，还是从线上 trace 学习？分别有什么风险？

---

## 10. Daily wrap-up

今天我们把 AI QA 的关注点从“如何测一次 Agent 输出”推进到“如何建设长期可信的评测样本集”。核心结论是：Agent 样本不是 prompt 表格，而是可回放的用户任务合同。它要同时描述用户意图、执行环境、工具约束、中间状态、最终结果和审计证据，并能被 Ginkgo、Playwright、API 测试和 K8s 发布门禁共同消费。

从工程实践上看，一份好样本应该能驱动完整链路：用户提交任务，API 创建 run，Agent 执行 planner 与 tool_call，页面展示结果，审计接口返回证据，K8s Job 给出发布准入结论。单点断言不是消失了，而是被放进每一步的预期中间状态和最终验证点中。

明天可以继续深入“AI Agent 评测指标与质量分层”，把今天的样本资产进一步连接到准确性、完整性、安全性、稳定性、成本和用户体验等多维指标，形成可持续运营的 AI QA 质量看板。
