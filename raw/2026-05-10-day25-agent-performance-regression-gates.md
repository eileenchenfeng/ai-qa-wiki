---
title: "每日 AI 学习笔记｜Day 25：AI Agent 性能压测资产化与回归门禁（k6 WebSocket + Locust + Ginkgo）"
date: 2026-05-10
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, performance, load-testing, k6, Locust, Ginkgo, Playwright]
---

# 每日 AI 学习笔记 Day 25｜AI Agent 性能压测资产化与回归门禁（k6 WebSocket + Locust + Ginkgo）

面向：资深测试开发（Golang Ginkgo / Python Playwright / API Testing / K8s）

关键词：**Performance Regression / k6 WebSocket / Locust / TTFT / P99 / Ginkgo E2E / Playwright / Scenario Asset**

Day 24 讨论了 AI Agent 的混沌工程：通过受控故障验证系统是否可用、可解释、可恢复。Day 25 继续把质量能力向“可持续运营”推进：把性能压测从一次性的专项活动，升级为可复用的场景资产库和 CI/CD 回归门禁。重点不再是“跑通一份脚本”，而是让每条真实用户旅程都能沉淀工作负载、指标、阈值、证据与复盘结论。

{/* truncate */}

## 0. 今日目标

今天的目标是把 AI Agent 性能压测做成一套可维护的工程体系，而不是临时拉起 Locust 或 k6 打一波流量。完成今天的学习后，你应该能够做到四件事。第一，能把用户体验指标、系统指标和 Agent 阶段指标连接起来，形成可解释的性能 SLO。第二，能用 k6 编写 WebSocket 流式 Agent 压测脚本，统计 TTFT、总耗时、成功率和业务错误。第三，能用 Locust 组织真实业务工作负载，并把不同 Agent 场景按权重混合起来。第四，能把 Ginkgo 与 Playwright 的 E2E 验证接入性能门禁，避免只看平均耗时而忽略最终用户结果。

## 1. 核心理论：性能压测要从“指标活动”变成“场景资产”

### 1.1 为什么 Agent 性能回归比传统 API 更难

传统 API 的性能回归通常围绕固定接口展开，输入结构稳定，调用路径相对确定。AI Agent 则不同，同一个用户任务可能因为 Prompt 版本、上下文长度、RAG 命中、工具选择、模型路由和安全策略而走出不同路径。只盯 `http_req_duration` 或平均响应时间，很容易把真实风险藏在整体均值里。

对 QA 来说，Agent 性能回归至少要覆盖三层结果。第一层是用户可感知体验，例如 TTFT、流式 token 中断、页面状态刷新和最终结果是否可见。第二层是系统吞吐能力，例如并发会话、WebSocket 连接数、任务队列堆积、CPU/GPU/内存和连接池。第三层是 Agent 内部阶段，例如规划、检索、工具调用、模型生成、Guardrail、结果落盘。只有三层结果能通过 `trace_id` 串起来，压测结论才可解释。

### 1.2 资深 QA 的性能 SLO 建模方式

不要先问“系统能打到多少 QPS”，而要先定义真实业务旅程。例如“用户在 Web 控制台提交生成 API 回归测试方案任务，Agent 进行规划、检索相关接口文档、调用用例生成工具、流式输出方案，并在页面展示可下载结果”。这条旅程的性能 SLO 可以拆成以下形式：

- **入口体验**：WebSocket 连接建立成功率不低于 99.5%，TTFT P95 小于 2 秒，TTFT P99 小于 4 秒。
- **任务完成**：E2E P95 小于 20 秒，E2E P99 小于 45 秒，业务成功率不低于 99%。
- **阶段健康**：RAG 检索 P99 小于 1.5 秒，工具调用 P99 小于 5 秒，模型生成阶段不能连续 30 秒无 token。
- **恢复能力**：当工具返回 429 或短时超时时，最终状态必须是 `succeeded` 或 `degraded`，不能卡在 `running`。
- **证据闭环**：每次压测请求必须携带 `qa.case_id`、`qa.run_id` 和 `trace_id`，便于关联日志、指标和 trace。

这里的关键是：性能门禁不只是数字门禁，也包括端到端结果门禁。一个请求如果 2 秒返回失败页面，平均耗时很好看，但对用户没有价值。

### 1.3 工作负载模型要服务于 E2E 业务链路

Agent 压测的工作负载模型应该从真实使用场景抽样，而不是随机拼 Prompt。推荐至少保留四类场景：短任务规划、RAG 问答、工具重度调用、长上下文审阅。每类场景都要定义输入、期望中间状态、最终验证点和观测字段。

例如“工具重度调用”不是单独压某个工具 API，而是从用户提交任务开始，经过 Agent 规划、工具选择、工具调用、结果聚合、页面展示，最终验证 trace 中确实存在工具调用 span，前端结果可见，错误分桶可解释。这样设计符合 E2E 测试思想，也能避免把单点功能验证独立成无业务意义的压测脚本。

## 2. 工程实践一：可运行的 WebSocket Agent Demo

为了让 k6 WebSocket 压测脚本可本地运行，先准备一个最小 Agent 服务。它模拟真实流式输出链路：客户端建立 WebSocket 连接，发送任务，服务端先等待规划和检索，再发送首个 token，随后持续输出 token，最后发送完成事件。

安装依赖：

```bash
pip install fastapi uvicorn pydantic
```

保存为 `agent_ws_demo.py`：

```python
import asyncio
import json
import time
import uuid
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="Streaming Agent WebSocket Demo")


async def simulate_agent_run(payload: Dict[str, Any]):
    scenario = payload.get("scenario", "api-test-plan-generation")
    task = payload.get("task", "Generate an API regression test plan")
    trace_id = payload.get("trace_id") or f"trace-{uuid.uuid4().hex[:12]}"
    run_id = f"run-{uuid.uuid4().hex[:12]}"

    await asyncio.sleep(0.18)
    yield {
        "event": "planned",
        "run_id": run_id,
        "trace_id": trace_id,
        "scenario": scenario,
        "stage": "planner",
    }

    await asyncio.sleep(0.22)
    words = [
        "Plan", "API", "contract", "tests", "with", "Ginkgo,",
        "generate", "Playwright", "journeys,", "attach", "trace", "evidence,",
        "and", "apply", "performance", "regression", "gates."
    ]
    for index, word in enumerate(words):
        await asyncio.sleep(0.06)
        yield {
            "event": "token",
            "run_id": run_id,
            "trace_id": trace_id,
            "index": index,
            "token": word,
        }

    await asyncio.sleep(0.08)
    yield {
        "event": "completed",
        "run_id": run_id,
        "trace_id": trace_id,
        "status": "succeeded",
        "result": f"Created E2E QA plan for: {task[:60]}",
    }


@app.websocket("/ws/agent")
async def agent_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        raw_message = await websocket.receive_text()
        payload = json.loads(raw_message)
        started_at = time.perf_counter()
        async for event in simulate_agent_run(payload):
            event["elapsed_ms"] = round((time.perf_counter() - started_at) * 1000, 2)
            await websocket.send_text(json.dumps(event, ensure_ascii=False))
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await websocket.send_text(json.dumps({"event": "error", "message": str(exc)}))
    finally:
        await websocket.close()
```

启动服务：

```bash
uvicorn agent_ws_demo:app --host 0.0.0.0 --port 8000
```

这段 Demo 虽然很小，但保留了 E2E 压测需要的关键结构：真实连接、一次任务输入、阶段事件、流式 token、完成事件、`trace_id` 和业务状态。后面的 k6、Ginkgo、Playwright 都可以围绕同一条链路复用。

## 3. 工程实践二：k6 WebSocket 压测 Agent 流式输出

k6 很适合做性能门禁，因为它可以把阈值写进脚本，并直接在 CI 中返回失败。下面脚本会统计四个指标：WebSocket 连接成功率、TTFT、E2E 总耗时和业务成功率。它不是只判断连接是否成功，而是等待 `completed` 事件，并校验最终状态。

保存为 `agent_ws_k6.js`：

```javascript
import ws from 'k6/ws';
import { check } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomSeed } from 'k6';

randomSeed(20260510);

export const ttft = new Trend('agent_ttft_ms', true);
export const e2e = new Trend('agent_e2e_ms', true);
export const businessSuccess = new Rate('agent_business_success');
export const streamErrors = new Counter('agent_stream_errors');

export const options = {
  scenarios: {
    agent_ws_smoke: {
      executor: 'ramping-vus',
      stages: [
        { duration: '30s', target: 10 },
        { duration: '1m', target: 30 },
        { duration: '30s', target: 0 },
      ],
    },
  },
  thresholds: {
    agent_business_success: ['rate>0.99'],
    agent_ttft_ms: ['p(95)<2000', 'p(99)<4000'],
    agent_e2e_ms: ['p(95)<20000', 'p(99)<45000'],
    agent_stream_errors: ['count<5'],
  },
};

const scenarios = [
  { name: 'short-planning', weight: 4, task: 'Generate smoke API checks for order creation.' },
  { name: 'rag-answer', weight: 3, task: 'Answer release risk questions from service documentation.' },
  { name: 'tool-heavy', weight: 2, task: 'Create E2E test data, call mock tools, and summarize evidence.' },
  { name: 'long-context-review', weight: 1, task: 'Review a long regression report and extract flaky risk patterns.' },
];

function pickScenario() {
  const total = scenarios.reduce((sum, item) => sum + item.weight, 0);
  let cursor = Math.random() * total;
  for (const item of scenarios) {
    cursor -= item.weight;
    if (cursor <= 0) return item;
  }
  return scenarios[0];
}

export default function () {
  const scenario = pickScenario();
  const url = __ENV.WS_URL || 'ws://localhost:8000/ws/agent';
  const traceId = `k6-${__VU}-${__ITER}-${Date.now()}`;
  const startedAt = Date.now();
  let firstTokenAt = 0;
  let completed = false;
  let finalStatus = 'unknown';

  const response = ws.connect(url, { tags: { scenario: scenario.name } }, function (socket) {
    socket.on('open', function () {
      socket.send(JSON.stringify({
        scenario: scenario.name,
        task: scenario.task,
        trace_id: traceId,
        qa_run_id: __ENV.QA_RUN_ID || 'local-k6-run',
      }));
    });

    socket.on('message', function (message) {
      const event = JSON.parse(message);
      if (event.event === 'token' && firstTokenAt === 0) {
        firstTokenAt = Date.now();
        ttft.add(firstTokenAt - startedAt, { scenario: scenario.name });
      }
      if (event.event === 'completed') {
        completed = true;
        finalStatus = event.status;
        e2e.add(Date.now() - startedAt, { scenario: scenario.name });
        businessSuccess.add(event.status === 'succeeded' || event.status === 'degraded');
        socket.close();
      }
      if (event.event === 'error') {
        streamErrors.add(1, { scenario: scenario.name });
        businessSuccess.add(false);
        socket.close();
      }
    });

    socket.setTimeout(function () {
      streamErrors.add(1, { scenario: scenario.name, reason: 'timeout' });
      businessSuccess.add(false);
      socket.close();
    }, 60000);
  });

  check(response, {
    'websocket handshake succeeded': (res) => res && res.status === 101,
  });

  check({ completed, finalStatus }, {
    'agent run completed with acceptable status': (result) =>
      result.completed && ['succeeded', 'degraded'].includes(result.finalStatus),
  });
}
```

本地执行：

```bash
k6 run -e WS_URL=ws://localhost:8000/ws/agent -e QA_RUN_ID=day25-local agent_ws_k6.js
```

在 CI 里，阈值失败就应该让流水线失败。需要注意的是，k6 的阈值最好分层设置：全局阈值控制整体体验，按 `scenario` 标签拆分的阈值控制关键业务链路。如果只有总体 P99，很可能被大量短任务稀释，导致长上下文或工具重度场景退化没有被发现。

## 4. 工程实践三：Locust 组织真实工作负载

Locust 的优势是用 Python 描述复杂用户行为，适合把现有测试数据、账号池、租户配置和业务权重串起来。下面示例通过 HTTP 入口模拟 Agent 任务，并把不同业务场景作为加权任务组织起来。

保存为 `agent_locustfile.py`：

```python
import json
import time
import uuid
from locust import HttpUser, between, task


SCENARIOS = {
    "short_planning": {
        "weight": 5,
        "task": "Generate API smoke checks for order creation.",
        "slo_ms": 8000,
    },
    "rag_answer": {
        "weight": 3,
        "task": "Answer QA risk questions from release documentation.",
        "slo_ms": 15000,
    },
    "tool_heavy": {
        "weight": 2,
        "task": "Create test data, invoke tools, and summarize evidence.",
        "slo_ms": 25000,
    },
}


class AgentApiUser(HttpUser):
    wait_time = between(1, 3)

    def run_agent(self, scenario_name: str):
        scenario = SCENARIOS[scenario_name]
        trace_id = f"locust-{uuid.uuid4().hex[:12]}"
        started_at = time.perf_counter()
        payload = {
            "task": scenario["task"],
            "scenario": scenario_name,
            "stream": False,
            "trace_id": trace_id,
            "qa_run_id": "day25-locust",
        }
        with self.client.post(
            "/agent/runs",
            data=json.dumps(payload),
            headers={"content-type": "application/json", "x-trace-id": trace_id},
            name=f"agent:{scenario_name}",
            catch_response=True,
            timeout=60,
        ) as response:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            if response.status_code >= 500:
                response.failure(f"server error: {response.status_code}")
                return
            try:
                body = response.json()
            except Exception as exc:
                response.failure(f"invalid json: {exc}")
                return
            status = body.get("status")
            if status not in {"succeeded", "degraded"}:
                response.failure(f"unacceptable business status: {status}")
                return
            if not body.get("trace_id"):
                response.failure("missing trace_id")
                return
            if elapsed_ms > scenario["slo_ms"]:
                response.failure(f"scenario SLO exceeded: {elapsed_ms:.0f}ms")
                return
            response.success()

    @task(SCENARIOS["short_planning"]["weight"])
    def short_planning(self):
        self.run_agent("short_planning")

    @task(SCENARIOS["rag_answer"]["weight"])
    def rag_answer(self):
        self.run_agent("rag_answer")

    @task(SCENARIOS["tool_heavy"]["weight"])
    def tool_heavy(self):
        self.run_agent("tool_heavy")
```

执行示例：

```bash
locust -f agent_locustfile.py --host http://localhost:8000 --users 50 --spawn-rate 5 --run-time 5m --headless
```

Locust 的 `catch_response=True` 很适合做业务级判定。只要最终状态、trace、SLO、页面证据不满足要求，就算 HTTP 返回 200，也应该标记为失败。这种设计能把性能压测和 E2E 业务质量统一起来。

## 5. 工程实践四：Ginkgo 性能门禁验证端到端结果

Ginkgo 不适合直接替代 k6 或 Locust 做大流量压测，但非常适合在压测前后做门禁验证：确认关键 E2E 链路可用、trace 可查、状态机没有卡住、性能指标没有明显退化。下面示例假设压测平台会暴露一次运行的汇总结果，Ginkgo 负责判定这次运行是否允许合入。

保存为 `agent_performance_gate_test.go`：

```go
package e2e_test

import (
    "encoding/json"
    "fmt"
    "net/http"
    "os"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

type PerfSummary struct {
    RunID               string  `json:"run_id"`
    Scenario            string  `json:"scenario"`
    BusinessSuccessRate float64 `json:"business_success_rate"`
    TTFTP99MS           float64 `json:"ttft_p99_ms"`
    E2EP99MS            float64 `json:"e2e_p99_ms"`
    TraceCoverageRate   float64 `json:"trace_coverage_rate"`
    StuckRunCount       int     `json:"stuck_run_count"`
}

var _ = Describe("Agent performance regression gate", Ordered, func() {
    It("keeps the API test-plan generation journey within user-facing SLO", func(ctx SpecContext) {
        baseURL := os.Getenv("PERF_RESULT_URL")
        if baseURL == "" {
            baseURL = "http://localhost:8000/perf/runs/day25-local/summary"
        }

        req, err := http.NewRequestWithContext(ctx, http.MethodGet, baseURL, nil)
        Expect(err).NotTo(HaveOccurred())

        client := &http.Client{Timeout: 10 * time.Second}
        resp, err := client.Do(req)
        Expect(err).NotTo(HaveOccurred())
        defer resp.Body.Close()
        Expect(resp.StatusCode).To(Equal(http.StatusOK))

        var summary PerfSummary
        Expect(json.NewDecoder(resp.Body).Decode(&summary)).To(Succeed())

        By(fmt.Sprintf("checking performance run %s for scenario %s", summary.RunID, summary.Scenario))
        Expect(summary.BusinessSuccessRate).To(BeNumerically(">=", 0.99), "business result must remain reliable")
        Expect(summary.TTFTP99MS).To(BeNumerically("<", 4000), "first token latency protects user perception")
        Expect(summary.E2EP99MS).To(BeNumerically("<", 45000), "full journey must finish within SLO")
        Expect(summary.TraceCoverageRate).To(BeNumerically(">=", 0.995), "almost every run must be traceable")
        Expect(summary.StuckRunCount).To(Equal(0), "no Agent run should stay in running forever")
    }, SpecTimeout(30*time.Second))
})
```

执行示例：

```bash
go test ./test/e2e -run TestE2E -ginkgo.label-filter=performance
```

这类 Ginkgo 用例的价值在于把“压测结果是否可接受”变成代码，而不是人工看一张报告。尤其在 Agent 场景里，是否有 trace、是否有卡住任务、业务成功率是否达标，和 P99 一样重要。

## 6. 工程实践五：Playwright 校验用户真实体验

性能压测经常只覆盖后端指标，但用户最终看到的是页面是否有响应、流式输出是否连续、失败是否可恢复。下面 Playwright 示例通过浏览器侧 Performance API 和页面断言，验证用户提交任务后的 E2E 体验。

保存为 `agent-ui-performance.spec.ts`：

```typescript
import { test, expect } from '@playwright/test';

test('agent journey shows streaming output and trace evidence within UX budget', async ({ page }) => {
  await page.goto('/agent');

  await page.getByLabel('Task').fill('Generate an API regression test plan for order creation');
  await page.getByRole('button', { name: 'Run Agent' }).click();

  const firstToken = page.getByTestId('stream-token').first();
  await expect(firstToken).toBeVisible({ timeout: 4000 });

  await expect(page.getByTestId('run-status')).toHaveText(/succeeded|degraded/i, { timeout: 45000 });
  await expect(page.getByTestId('result-panel')).toContainText('API');
  await expect(page.getByTestId('trace-panel')).toContainText(/trace-/);

  const timing = await page.evaluate(() => {
    const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return {
      domContentLoaded: nav.domContentLoadedEventEnd - nav.startTime,
      load: nav.loadEventEnd - nav.startTime,
    };
  });

  expect(timing.domContentLoaded).toBeLessThan(3000);
});
```

这条用例不是单独验证“按钮能点击”，而是覆盖完整用户旅程：打开页面、提交任务、看到首个流式输出、等待最终状态、查看结果和 trace 证据。它能捕获很多后端压测看不到的问题，例如前端状态不刷新、WebSocket 断线后没有提示、结果落盘成功但页面不可见。

## 7. CI/CD 中的性能回归闭环

推荐把性能门禁分成三层。第一层是提交级轻量门禁，运行少量 Ginkgo 和 Playwright E2E，用于确认关键旅程没有明显性能退化。第二层是预发级压测门禁，运行 k6 WebSocket 和 Locust 混合场景，覆盖 TTFT、E2E P99、业务成功率和 trace 覆盖率。第三层是每日或每周基线任务，运行更长时间的 soak test，观察内存、连接数、队列堆积和错误分桶趋势。

每次性能回归都应该产出五类证据：压测配置、工作负载分布、指标结果、失败样本和 trace 链接。对于失败样本，不要只保留“P99 超过阈值”，而要保留具体 `qa.case_id`、`trace_id`、场景名、阶段耗时和最终用户结果。这样失败才能回放，阈值才能持续校准。

一个可落地的流水线顺序是：部署候选版本，运行 Ginkgo 冒烟，启动 k6 WebSocket 压测，运行 Locust 混合工作负载，收集 metrics 和 traces，执行 Ginkgo 性能结果门禁，执行 Playwright 用户体验抽检，归档报告。如果任一步发现业务成功率不足、TTFT 退化、trace 缺失或卡住任务，流水线应失败。

## 8. 今日 E2E 场景模板

可以把今天的内容沉淀为一个场景资产模板：

```yaml
case_id: agent-performance-api-test-plan-001
journey: User submits an API test-plan generation task and receives streaming output plus final evidence.
entry: Web console or WebSocket API creates an Agent run.
workload:
  scenario: tool-heavy
  concurrency_profile: ramping-vus
  data_profile: medium context with API schema and release notes
expected_intermediate_states:
  - websocket handshake succeeds
  - planned event is received
  - first token arrives within TTFT SLO
  - trace_id is returned and propagated to backend spans
  - tool-call span exists when tool-heavy scenario is selected
final_validation:
  - final status is succeeded or degraded
  - result is visible in UI or API response
  - business success rate remains above threshold
  - E2E P99 stays within SLO
  - no run remains stuck in running state
observability:
  - qa.case_id is attached
  - qa.run_id is attached
  - trace coverage is above 99.5 percent
cleanup:
  - close websocket sessions
  - remove generated test data
  - archive metrics, logs, traces, and failed samples
```

这个模板的核心思想是：不要把“WebSocket 是否连上”“接口是否返回 200”“页面是否展示结果”拆成孤立用例，而是把它们放入同一条真实业务链路，用中间状态和最终验证点共同判断质量。

## 9. 课后作业

1. 基于 `agent_ws_demo.py` 启动本地服务，运行 `agent_ws_k6.js`，把并发从 10、30、50 逐步提升，记录 TTFT P95/P99、E2E P99 和业务成功率的变化。
2. 将 k6 脚本中的场景权重调整为“工具重度调用占 60%”，观察总体 P99 与 `tool-heavy` 场景 P99 的差异，并解释为什么只看总体指标可能误判风险。
3. 为 Locust 示例增加一个“长上下文审阅”场景，要求请求中包含上下文长度标签，并在失败信息中输出场景名、SLO 和 trace_id。
4. 将 Ginkgo 性能门禁接入一份模拟的 `PerfSummary` JSON 服务，补充断言：当 `trace_coverage_rate` 低于 99.5% 时，即使 P99 达标也必须失败。
5. 用 Playwright 增加一个断线恢复 E2E 场景：WebSocket 中断后页面展示可理解提示，用户点击 Retry 后任务重新进入 running 并最终 succeeded 或 degraded。

## 10. 今日小结

Day 25 的核心结论是：AI Agent 性能压测不应该停留在一次性专项，而应该沉淀为可复用的 E2E 场景资产和自动化回归门禁。k6 负责高效执行 WebSocket 流式压测并用阈值守住体验底线，Locust 负责组织贴近真实业务的工作负载，Ginkgo 负责把性能结果变成可合入的工程规则，Playwright 负责确认用户最终看到的是连续、可解释、可恢复的体验。

对资深 QA 工程师来说，最重要的不是会使用某个压测工具，而是能把用户旅程、Agent 阶段、系统指标、trace 证据和 CI/CD 门禁连接起来。只有这样，TTFT、P99、业务成功率和 trace 覆盖率才不是孤立数字，而是持续保障 AI Agent 质量的工程化资产。

明天可以继续深入一个相关主题：如何把这些性能、可靠性和可观测性场景统一纳入测试数据管理与自动化调度平台，让每天执行哪些 E2E 场景由风险、变更和历史失败数据共同决定。
