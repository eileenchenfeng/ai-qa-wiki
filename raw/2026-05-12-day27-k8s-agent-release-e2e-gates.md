---
title: "每日 AI 学习笔记｜Day 27：K8s 环境下 AI Agent 的端到端发布验收"
date: 2026-05-12
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, SDET, K8s, Ginkgo, Playwright, API-testing, release-gates]
---

# 每日 AI 学习笔记 Day 27｜K8s 环境下 AI Agent 的端到端发布验收

## 核心总结

面向 Senior SDET 的 AI Agent 发布验收，不能只验证 Pod 是否 Running、接口是否 200、页面是否能打开，而要把 **K8s 部署状态、API 契约、Agent 业务任务、Playwright 用户旅程、Ginkgo 后端断言和可观测证据** 串成一条端到端质量门禁。真正可靠的发布检查应从用户触发 Agent 任务开始，经过网关鉴权、服务路由、任务排队、模型或工具调用、状态轮询、结果展示和 trace 归档，最后验证用户能得到可解释、可追踪、可恢复的业务结果。K8s 不是单独的运维对象，而是 E2E 质量链路中的运行时边界：资源限制、探针、滚动发布、网络策略、Secret 注入和 HPA 都会直接影响 AI Agent 的稳定性与用户体验。

{/* truncate */}

## 0. 今日目标

今天把前几天的性能、混沌和回归门禁主题落到发布验收场景。完成今天的学习后，你应该能够做到四件事。第一，能为 AI Agent 服务设计 K8s-native 的 E2E 发布门禁，而不是把 Kubernetes 检查、API 测试和 UI 自动化拆成互不关联的任务。第二，能用 Golang Ginkgo 编写面向真实业务链路的 API 验收测试，验证创建任务、轮询状态、结果断言和 trace 证据。第三，能用 Python Playwright 从用户视角验证页面提交任务、等待完成和查看结果。第四，能把这些检查接入 CI/CD，让一次发布只有在运行时状态、业务结果和用户体验全部通过时才允许继续。

本篇内容面向有 Golang、Python、K8s、API Testing 与 E2E 自动化经验的 Senior SDET。示例代码采用最小可运行 Demo，便于你在本地、kind、minikube 或测试集群中快速改造成自己的 Agent 发布验收资产。

---

## 1. 核心理论：AI Agent 发布验收要验证“运行时业务闭环”

### 1.1 为什么只看 K8s 状态会产生发布假阳性

传统服务发布验收经常从 Kubernetes 对象状态开始：Deployment 是否完成 rollout，Pod 是否 Ready，Service 是否有 Endpoint，Ingress 是否可访问。这些检查很重要，但对 AI Agent 来说远远不够。Agent 服务的用户价值不是“容器启动成功”，而是“用户提交一个任务后，系统能稳定完成规划、检索、工具调用、生成结果和证据归档”。

AI Agent 的发布假阳性通常来自三类断层。第一类是运行时断层：Pod Ready，但模型 API Key 注入错误、工具服务网络不可达、队列消费者未启动。第二类是业务断层：`POST /agent/runs` 返回 200，但任务最终卡在 `running`，页面没有结果。第三类是观测断层：任务成功了，但没有 `trace_id`、没有阶段耗时、无法在故障时定位 planner、retriever、tool call 或 model stage。

Senior SDET 的发布验收应该把这些断层合并到一条 E2E 链路里：发布完成只是起点，用户旅程通过才是终点。

### 1.2 K8s-native E2E 门禁的五层模型

一个可落地的 AI Agent 发布门禁可以分为五层。

1. **部署层**：Deployment rollout 成功，Pod Ready，镜像版本、配置版本和资源限制符合预期。
2. **网络层**：Service、Ingress、DNS、NetworkPolicy、mTLS 或鉴权链路可用。
3. **API 层**：核心契约稳定，创建任务、查询任务、取消任务、结果读取等接口返回结构符合约定。
4. **业务层**：Agent 任务最终进入 `succeeded` 或可解释的 `degraded`，结果内容满足业务断言，错误被分桶。
5. **体验层**：用户在 Web 页面能提交任务、看到进行中状态、获得最终结果，并能查看 trace 或证据链接。

这五层不是五条孤立测试用例，而是一条发布验收旅程中的不同验证点。单点检查应下沉为 E2E 步骤中的中间状态，例如“Deployment rollout 成功”是用户旅程执行前的环境前置验证，“API 返回 run_id”是任务创建步骤的中间状态，“页面展示结果”是最终用户可观测结果。

### 1.3 发布门禁的核心原则

AI Agent 发布门禁应遵循三个原则。

第一，**以用户任务为主线**。不要只测 `/healthz` 或 `/version`，而要选择一条真实业务任务，例如“生成 API 回归测试方案”“基于知识库回答发布风险”“调用工具生成测试数据并汇总结论”。

第二，**用 trace 串联证据**。Ginkgo、Playwright、服务端日志、Prometheus 指标和 OpenTelemetry trace 应共享同一个 `qa_run_id` 或 `trace_id`。当门禁失败时，报告要能直接定位到请求、Pod、日志和阶段耗时。

第三，**允许可解释降级，不允许无声失败**。Agent 可以因为模型限流或工具超时进入 `degraded`，但必须给出降级原因、用户可继续操作的结果和可排查的错误分桶。`running` 卡死、空结果、未分类错误都不应通过发布门禁。

---

## 2. 工程实践一：准备一个可运行的 Agent Demo 服务

下面的 Demo 提供三个能力：`/healthz` 用于 K8s 探针，`/api/agent/runs` 用于创建 Agent 任务，`/api/agent/runs/{run_id}` 用于轮询最终状态，同时根路径提供一个最小 Web 页面，供 Playwright 执行用户旅程。

安装依赖：

```bash
pip install fastapi uvicorn pydantic
```

保存为 `agent_release_demo.py`：

```python
import time
import uuid
from typing import Dict

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Agent Release Gate Demo")
RUNS: Dict[str, dict] = {}


class CreateRunRequest(BaseModel):
    task: str = Field(min_length=3)
    scenario: str = "api-regression-plan"
    trace_id: str | None = None


@app.get("/healthz")
def healthz():
    return {"status": "ok", "component": "agent-release-demo"}


@app.post("/api/agent/runs", status_code=201)
def create_run(payload: CreateRunRequest):
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    trace_id = payload.trace_id or f"trace-{uuid.uuid4().hex[:12]}"
    RUNS[run_id] = {
        "run_id": run_id,
        "trace_id": trace_id,
        "scenario": payload.scenario,
        "task": payload.task,
        "status": "running",
        "created_at": time.time(),
        "stage": "planner",
        "error_bucket": "none",
    }
    return {"run_id": run_id, "trace_id": trace_id, "status": "running"}


@app.get("/api/agent/runs/{run_id}")
def get_run(run_id: str):
    run = RUNS[run_id]
    elapsed = time.time() - run["created_at"]
    if elapsed > 1.2:
        run["status"] = "succeeded"
        run["stage"] = "completed"
        run["result"] = (
            "Created an API regression test plan with contract checks, "
            "Ginkgo E2E assertions, Playwright user journey, and trace evidence."
        )
    elif elapsed > 0.6:
        run["stage"] = "tool_call"
    return run


@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!doctype html>
<html>
  <head><title>Agent Release Gate Demo</title></head>
  <body>
    <h1>Agent Release Gate Demo</h1>
    <label for="task">Task</label>
    <textarea id="task">Generate an API regression test plan for checkout and refund flows.</textarea>
    <button id="submit">Run Agent</button>
    <pre id="status">idle</pre>
    <script>
      async function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
      document.querySelector('#submit').addEventListener('click', async () => {
        const task = document.querySelector('#task').value;
        const traceId = `pw-${Date.now()}`;
        const createResp = await fetch('/api/agent/runs', {
          method: 'POST',
          headers: {'content-type': 'application/json', 'x-trace-id': traceId},
          body: JSON.stringify({task, scenario: 'playwright-release-gate', trace_id: traceId})
        });
        const created = await createResp.json();
        document.querySelector('#status').textContent = `running ${created.run_id}`;
        for (let i = 0; i < 10; i++) {
          const pollResp = await fetch(`/api/agent/runs/${created.run_id}`);
          const run = await pollResp.json();
          document.querySelector('#status').textContent = JSON.stringify(run, null, 2);
          if (run.status === 'succeeded' || run.status === 'degraded') return;
          await sleep(300);
        }
      });
    </script>
  </body>
</html>
"""
```

本地启动：

```bash
uvicorn agent_release_demo:app --host 0.0.0.0 --port 8080
```

快速验证：

```bash
curl -s http://127.0.0.1:8080/healthz
curl -s -X POST http://127.0.0.1:8080/api/agent/runs \
  -H 'content-type: application/json' \
  -d '{"task":"Generate an API regression test plan","trace_id":"manual-smoke-001"}'
```

这个 Demo 虽然很小，但已经包含发布验收需要的关键元素：健康检查、任务创建、状态轮询、最终结果、阶段状态和 trace 标识。

---

## 3. 工程实践二：把 Demo 部署到 K8s 测试命名空间

下面的 Kubernetes 清单适合 kind、minikube 或测试集群。真实环境中应把镜像、资源、Secret、Ingress 和 NetworkPolicy 替换为团队标准配置。

保存为 `k8s-agent-release-demo.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-release-demo
  labels:
    app: agent-release-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: agent-release-demo
  template:
    metadata:
      labels:
        app: agent-release-demo
    spec:
      containers:
        - name: app
          image: ghcr.io/example/agent-release-demo:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 3
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: agent-release-demo
spec:
  selector:
    app: agent-release-demo
  ports:
    - name: http
      port: 80
      targetPort: 8080
```

如果你在本地构建镜像，可以使用以下 Dockerfile：

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn pydantic
COPY agent_release_demo.py /app/agent_release_demo.py
EXPOSE 8080
CMD ["uvicorn", "agent_release_demo:app", "--host", "0.0.0.0", "--port", "8080"]
```

在 kind 中运行的一种方式如下：

```bash
docker build -t agent-release-demo:local .
kind load docker-image agent-release-demo:local
kubectl create namespace qa-release-gate --dry-run=client -o yaml | kubectl apply -f -
kubectl -n qa-release-gate set image deployment/agent-release-demo app=agent-release-demo:local --local -o yaml -f k8s-agent-release-demo.yaml | kubectl apply -f -
kubectl -n qa-release-gate rollout status deployment/agent-release-demo --timeout=90s
kubectl -n qa-release-gate port-forward svc/agent-release-demo 8080:80
```

如果你的集群无法使用 `kind load`，可以先把镜像推送到测试镜像仓库，再把 `image` 字段改成对应地址。发布门禁不应依赖固定环境，而应通过 `AGENT_BASE_URL` 指向本次发布的入口。

---

## 4. 工程实践三：用 Golang Ginkgo 验证 Agent API 业务链路

Ginkgo 测试不应该只断言接口状态码，而要覆盖“创建任务、轮询状态、验证结果、校验证据”的完整链路。下面示例通过环境变量读取服务入口，适合接入 CI/CD，也适合本地 port-forward 后执行。

初始化依赖：

```bash
go mod init agent-release-gate
go get github.com/onsi/ginkgo/v2 github.com/onsi/gomega
```

保存为 `agent_release_gate_test.go`：

```go
package releasegate_test

import (
    "bytes"
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "os"
    "testing"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

func TestReleaseGate(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Agent Release Gate Suite")
}

type createRunResponse struct {
    RunID   string `json:"run_id"`
    TraceID string `json:"trace_id"`
    Status  string `json:"status"`
}

type runStatusResponse struct {
    RunID       string `json:"run_id"`
    TraceID     string `json:"trace_id"`
    Status      string `json:"status"`
    Stage       string `json:"stage"`
    Result      string `json:"result"`
    ErrorBucket string `json:"error_bucket"`
}

var _ = Describe("AI Agent release gate", Ordered, func() {
    var baseURL string
    var httpClient *http.Client

    BeforeAll(func() {
        baseURL = os.Getenv("AGENT_BASE_URL")
        if baseURL == "" {
            baseURL = "http://127.0.0.1:8080"
        }
        httpClient = &http.Client{Timeout: 5 * time.Second}
    })

    It("accepts a real QA user journey and returns traceable business result", func(ctx SpecContext) {
        By("checking the runtime health endpoint before the user journey")
        healthReq, err := http.NewRequestWithContext(ctx, http.MethodGet, baseURL+"/healthz", nil)
        Expect(err).NotTo(HaveOccurred())
        healthResp, err := httpClient.Do(healthReq)
        Expect(err).NotTo(HaveOccurred())
        defer healthResp.Body.Close()
        Expect(healthResp.StatusCode).To(Equal(http.StatusOK))

        By("creating an Agent task with a QA trace id")
        traceID := fmt.Sprintf("ginkgo-release-%d", time.Now().UnixNano())
        payload := map[string]string{
            "task": "Generate an API regression plan for checkout and refund flows.",
            "scenario": "ginkgo-release-gate",
            "trace_id": traceID,
        }
        body, err := json.Marshal(payload)
        Expect(err).NotTo(HaveOccurred())

        createReq, err := http.NewRequestWithContext(ctx, http.MethodPost, baseURL+"/api/agent/runs", bytes.NewReader(body))
        Expect(err).NotTo(HaveOccurred())
        createReq.Header.Set("content-type", "application/json")
        createReq.Header.Set("x-trace-id", traceID)

        createResp, err := httpClient.Do(createReq)
        Expect(err).NotTo(HaveOccurred())
        defer createResp.Body.Close()
        Expect(createResp.StatusCode).To(Equal(http.StatusCreated))

        var created createRunResponse
        Expect(json.NewDecoder(createResp.Body).Decode(&created)).To(Succeed())
        Expect(created.RunID).To(HavePrefix("run-"))
        Expect(created.TraceID).To(Equal(traceID))
        Expect(created.Status).To(Equal("running"))

        By("polling until the Agent reaches a business terminal state")
        var final runStatusResponse
        Eventually(func(g Gomega) string {
            pollReq, err := http.NewRequestWithContext(ctx, http.MethodGet, baseURL+"/api/agent/runs/"+created.RunID, nil)
            g.Expect(err).NotTo(HaveOccurred())
            pollResp, err := httpClient.Do(pollReq)
            g.Expect(err).NotTo(HaveOccurred())
            defer pollResp.Body.Close()
            g.Expect(pollResp.StatusCode).To(Equal(http.StatusOK))
            g.Expect(json.NewDecoder(pollResp.Body).Decode(&final)).To(Succeed())
            g.Expect(final.TraceID).To(Equal(traceID))
            g.Expect(final.ErrorBucket).To(Or(Equal(""), Equal("none")))
            return final.Status
        }).WithContext(ctx).WithTimeout(5 * time.Second).WithPolling(300 * time.Millisecond).Should(Or(Equal("succeeded"), Equal("degraded")))

        By("verifying the final observable result for the user")
        Expect(final.Stage).To(Equal("completed"))
        Expect(final.Result).To(ContainSubstring("API regression test plan"))
        Expect(final.Result).To(ContainSubstring("trace evidence"))
    }, SpecTimeout(10*time.Second))
})
```

执行方式：

```bash
AGENT_BASE_URL=http://127.0.0.1:8080 go test ./... -v
```

这条 Ginkgo 用例符合 E2E 场景设计：它从发布后的运行时健康开始，模拟真实 QA 用户提交 Agent 任务，验证 API 契约中的 `run_id` 和 `trace_id`，轮询最终状态，并以用户可见结果作为最终验证点。`/healthz`、状态码、字段校验都只是链路中的中间状态，而不是独立的孤立用例。

---

## 5. 工程实践四：用 Python Playwright 验证用户可见发布结果

Playwright 用例负责从浏览器视角验证“用户是否真的能完成任务”。它不替代 Ginkgo 的 API 断言，而是补齐页面状态、用户交互和最终结果展示。

安装依赖：

```bash
pip install pytest pytest-playwright
python -m playwright install chromium
```

保存为 `test_agent_release_ui.py`：

```python
import os

from playwright.sync_api import Page, expect


def test_agent_release_user_journey(page: Page):
    base_url = os.getenv("AGENT_BASE_URL", "http://127.0.0.1:8080")

    page.goto(base_url)
    expect(page.get_by_role("heading", name="Agent Release Gate Demo")).to_be_visible()

    page.locator("#task").fill(
        "Generate an API regression test plan for checkout, refund, and coupon flows."
    )
    page.locator("#submit").click()

    status = page.locator("#status")
    expect(status).to_contain_text("run-", timeout=3000)
    expect(status).to_contain_text("succeeded", timeout=8000)
    expect(status).to_contain_text("API regression test plan")
    expect(status).to_contain_text("trace")
```

执行方式：

```bash
AGENT_BASE_URL=http://127.0.0.1:8080 pytest -q test_agent_release_ui.py
```

这条 Playwright 用例的关键不是“按钮能不能点”，而是完整验证用户旅程：用户打开发布后的页面，输入真实任务，提交 Agent 运行，看到任务进入运行态，最终看到成功结果和 trace 证据。页面元素断言、网络请求和内容校验都服务于同一条端到端业务链路。

---

## 6. 工程实践五：把 K8s、Ginkgo、Playwright 接成 CI 门禁

在 CI/CD 中，发布验收可以拆成三个连续阶段，但仍然围绕同一条 E2E 业务目标。

第一阶段是 K8s runtime gate：部署到临时命名空间或灰度环境，等待 rollout 完成，校验 Pod Ready、Service Endpoint 和入口 URL。第二阶段是 API business gate：运行 Ginkgo，验证任务创建、状态轮询、最终结果和 trace 证据。第三阶段是 UI experience gate：运行 Playwright，验证真实页面旅程。

下面是一个 GitHub Actions 风格的示例。实际落地时，可以替换为团队内部 CI 系统、Argo CD、Tekton 或 GitLab CI。

```yaml
name: agent-release-gate

on:
  workflow_dispatch:

jobs:
  release-gate:
    runs-on: ubuntu-latest
    env:
      NAMESPACE: qa-release-gate
      AGENT_BASE_URL: http://127.0.0.1:8080
    steps:
      - uses: actions/checkout@v4

      - name: Wait for Kubernetes rollout
        run: |
          kubectl -n $NAMESPACE rollout status deployment/agent-release-demo --timeout=90s
          kubectl -n $NAMESPACE get endpoints agent-release-demo

      - name: Open local tunnel to release candidate
        run: |
          kubectl -n $NAMESPACE port-forward svc/agent-release-demo 8080:80 > port-forward.log 2>&1 &
          sleep 5
          curl -fsS $AGENT_BASE_URL/healthz

      - name: Run Ginkgo API business gate
        run: |
          go test ./... -v

      - name: Run Playwright user journey gate
        run: |
          pip install pytest pytest-playwright
          python -m playwright install chromium
          pytest -q test_agent_release_ui.py
```

门禁失败时，建议统一输出四类证据：本次镜像版本和配置版本、Ginkgo 失败步骤和 `trace_id`、Playwright 截图或 trace、K8s 事件与 Pod 日志。这样研发拿到失败报告后不需要猜测“是页面问题、接口问题、模型问题还是集群问题”。

---

## 7. 高级实践：发布验收中的风险清单

### 7.1 资源与并发风险

Agent 服务常常同时受 CPU、内存、连接池、队列长度、模型吞吐和外部工具限流影响。发布验收至少要检查资源 request 和 limit 是否符合压测基线，Pod 是否出现重启，任务队列是否堆积，外部依赖是否触发 429 或超时。对于流式输出场景，还要关注连接保持时间、网关 idle timeout 和首 token 延迟。

### 7.2 配置与 Secret 风险

K8s 发布中最常见的问题之一是配置漂移。模型路由、工具开关、RAG 索引版本、Prompt 模板、API Key、灰度比例都可能让同一镜像表现不同。发布验收应在结果中记录关键配置版本，但不要泄露 Secret 内容。测试只需要证明 Secret 可用、配置版本符合预期、依赖可访问，不需要把敏感值写入日志。

### 7.3 回滚与降级风险

发布门禁不仅要证明新版本能成功，也要证明失败时可恢复。对于 Agent 服务，建议至少验证三种可恢复结果：工具短暂失败时进入可解释降级，模型限流时返回用户可理解的重试建议，发布失败时 Deployment 能快速回滚到上一个稳定 ReplicaSet。更高阶的团队可以把这些验证接入 Day 24 的混沌工程资产。

---

## 8. After-class Questions

1. 如果某次发布中 Deployment rollout 成功、Ginkgo API 测试通过，但 Playwright 页面一直停留在 running，你会从哪些层面排查？请按浏览器、网关、服务、队列、Agent 阶段和 K8s 事件组织排查路径。
2. 你的 Agent 系统中哪些字段必须出现在每次 E2E 发布验收报告里？请设计一份最小证据模型，至少包含 `qa_run_id`、`trace_id`、镜像版本、配置版本、最终状态、错误分桶和结果链接。
3. 如果模型服务在灰度环境偶发 429，你会让发布门禁直接失败，还是允许 `degraded` 通过？请说明判断标准、用户体验要求和可观测证据要求。
4. 如何把今天的 Ginkgo API 用例和 Playwright UI 用例复用到性能压测或混沌测试中？请说明哪些断言可以复用，哪些阈值需要按场景调整。
5. 如果测试集群没有真实模型访问权限，你会如何设计 Mock 或 Fake Agent，才能既保证发布门禁稳定，又不掩盖真实生产风险？

---

## 9. Daily Wrap-up

今天的重点是把 AI Agent 发布验收从“环境检查”升级为“运行时业务闭环”。K8s 的 rollout、Pod Ready、Service Endpoint 和探针检查是必要前提，但不能代表用户任务成功。Senior SDET 应把发布后的真实用户旅程作为主线，用 Ginkgo 验证 API 业务契约和 trace 证据，用 Playwright 验证页面可见结果，用 K8s 事件和日志解释运行时状态。

最重要的工程结论是：**发布门禁要证明用户能完成任务，而不是证明系统看起来活着。** 对 AI Agent 来说，一次可信的发布必须同时回答三个问题：运行时是否健康，业务任务是否完成，用户是否看到了可解释结果。只有这三个答案都成立，发布才真正具备上线信心。
