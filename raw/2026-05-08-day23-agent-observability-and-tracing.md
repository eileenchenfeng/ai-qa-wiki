---
title: "每日 AI 学习笔记｜Day 23：可观测性与链路追踪（OpenTelemetry + Trace）"
date: 2026-05-08
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, observability, tracing, OpenTelemetry]
---

# 每日 AI 学习笔记 Day 23｜可观测性与链路追踪（OpenTelemetry + Trace）

面向：资深测试开发（Golang Ginkgo / Python Playwright / K8s / API Testing）
关键词：**OpenTelemetry / Trace / Span / Context Propagation / OTLP / Jaeger / Tempo / E2E 诊断**

今天这篇笔记聚焦一个非常典型、也最容易在 AI Agent 项目里被低估的问题：**系统明明“偶发变慢”或“偶发失败”，但没有足够的链路证据告诉你到底慢在哪、错在哪、谁先错了。**

如果没有可观测性，很多线上问题最后都会退化成“翻日志 + 猜测 + 重跑”；而一旦把 `trace_id`、关键阶段 span、日志字段和 SLO 指标串起来，测试开发就能把“难复现的偶发问题”沉淀成可回放、可定位、可门禁的工程能力。

{/* truncate */}

## 0. 今日目标

- 把 AI Agent 里的“慢”“卡”“偶发失败”拆解成可观测的阶段证据，而不是只看最终接口耗时；
- 理解 **OpenTelemetry** 在 Agent 场景下的主链路建模方式：用户入口、规划、检索、工具调用、模型生成、审核与结果返回；
- 给出可直接运行的 **Python FastAPI + OpenTelemetry** 示例，打通基础 trace；
- 给出 **Go + Ginkgo** 的端到端 trace 连续性断言示例，把“链路没断”变成可自动化校验的质量规则。

## 1. 核心理论：为什么 Agent 场景必须把 Trace 当成一等公民

### 1.1 为什么传统接口日志不够用？

在传统后端系统里，很多问题靠“接口日志 + 错误码 + 平均耗时”还能勉强定位；但在 Agent 场景里，这套方法经常会失效，因为**同一个用户请求背后并不是单阶段执行，而是一条动态工作流**。

一次看似普通的“生成测试方案”请求，真实链路可能会经过：

- API Gateway 入站；
- Agent Orchestrator 规划任务；
- RAG 检索知识库；
- 多次工具调用；
- LLM 推理生成；
- Guardrail / Policy 检查；
- 结果格式化、落盘与通知。

这意味着“接口 7 秒返回”这个事实本身没有太大价值。真正有价值的问题是：

- 7 秒里到底是 **规划阶段慢**，还是 **检索慢**，还是 **工具调用重试把尾延迟拖长**？
- 错误是发生在模型、工具、权限、超时，还是链路追踪本身断掉了？
- 是所有场景都慢，还是只有某一类业务场景、某个模型版本、某个工具依赖变慢？

这正是 Trace 的价值：它不是替代日志和指标，而是把**用户请求的完整因果链**显式展开。

### 1.2 Agent 链路里最应该打哪些 Span？

一个适合测试开发落地的 Agent Trace，一般至少包含以下层次：

- **入口 Span**：接收用户请求，记录场景、租户、是否流式输出、请求版本；
- **规划 Span**：记录规划耗时、候选工具数、计划版本、是否命中缓存；
- **检索 Span**：记录知识库、召回数、重排数、超时与 fallback；
- **工具调用 Span**：记录目标服务、重试次数、超时时间、降级路径；
- **模型生成 Span**：记录模型名、输入输出 token、TTFT、完成耗时；
- **审核/安全 Span**：记录是否命中策略、是否做脱敏、是否被拦截；
- **出站 Span**：记录最终状态码、响应大小、整体成功/失败标签。

其中最关键的不是“span 打得多”，而是 **span 能反映真实阶段边界**。如果你只在入口打一条总 span，最后得到的仍然只是一条“7 秒”的粗粒度事实，定位价值非常有限。

### 1.3 测试开发最该关注哪些 Span Attributes？

Span 上的信息不应该是“能写多少写多少”，而要围绕后续排障和回归门禁来设计。常用字段包括：

- `ai.scenario`：业务场景名，例如 `test-plan-generation`、`rag-answer`；
- `ai.plan.version`：当前规划版本，便于判断问题是否出现在新老规划策略切换；
- `ai.tool.name` / `ai.tool.retry_count`：工具名与重试次数；
- `ai.model.name`：当前模型版本；
- `ai.rag.hit_count`：召回命中数；
- `ai.stream`：是否流式输出；
- `error.type` / `error.stage`：错误类型与出错阶段；
- `qa.case_id` / `qa.run_id`：自动化用例 ID 与执行批次，用于把测试平台结果与后端 Trace 关联。

一个非常重要的实践原则是：**不要把原始 prompt、用户敏感信息、邮箱、明文业务数据直接写入 span attribute。**

Trace 是排障资产，不是数据泄露通道。更推荐的做法是：

- 写入 `prompt_template_id` 而不是完整 prompt；
- 写入脱敏后的 `tenant_hash` / `user_hash`；
- 对输入输出只记录长度、类别、命中标签，而不是原文全量透传。

### 1.4 为什么说 Trace、Log、Metric 必须联动？

单独看任何一种观测数据都不完整：

- **Metric** 适合回答“现在整体是不是变差了”；
- **Log** 适合回答“某一次具体失败报了什么错误”；
- **Trace** 适合回答“这次请求沿途到底经历了什么”。

在 AI Agent 场景下，最推荐的联动方式是：

1. 用 **Metric** 发现异常，例如 `TTFT P99` 突然升高；
2. 用 **Trace** 找到最慢的阶段，例如 `tool.call` 或 `rag.retrieve`；
3. 用 **Log** 下钻到具体错误细节，例如超时、429、权限拒绝或 JSON 解析失败。

> 对测试开发来说，真正高价值的不是“平台上能看到链路图”，而是能把一条失败的 E2E 用例，稳定地关联到对应 trace、对应日志、对应指标窗口。

## 2. 工程实践（一）：Python FastAPI + OpenTelemetry 打通基础链路

下面给出一个最小可运行示例。它模拟一个 Agent 服务，对外暴露 `/agent/run` 接口，并在请求内部拆成：`plan`、`retrieve`、`tool.call`、`llm.generate` 四个阶段。

运行前安装依赖：

```bash
pip install fastapi uvicorn httpx \
  opentelemetry-api opentelemetry-sdk \
  opentelemetry-exporter-otlp \
  opentelemetry-instrumentation-fastapi \
  opentelemetry-instrumentation-httpx
```

示例代码：

```python
# 文件名：agent_observability_app.py
# 运行：
#   export OTEL_SERVICE_NAME=agent-api
#   export OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
#   uvicorn agent_observability_app:app --host 0.0.0.0 --port 8000
# 如果本地暂时没有 OTLP Collector，也可以不设置 OTEL_EXPORTER_OTLP_ENDPOINT，程序会回退到 ConsoleSpanExporter。

import asyncio
import os
import random
from typing import Dict

import httpx
from fastapi import FastAPI, Request
from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def init_tracer() -> None:
    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "agent-api"),
            "service.version": "day23-demo",
            "deployment.environment": os.getenv("DEPLOY_ENV", "local"),
        }
    )
    provider = TracerProvider(resource=resource)

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")))
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)


init_tracer()
tracer = trace.get_tracer(__name__)
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()


async def fake_retrieve(question: str) -> Dict[str, str]:
    with tracer.start_as_current_span("rag.retrieve") as span:
        await asyncio.sleep(0.08)
        hit_count = 2 if "测试" in question else 1
        span.set_attribute("ai.rag.hit_count", hit_count)
        span.set_attribute("ai.rag.index", "qa-knowledge-base")
        return {"knowledge": "建议优先校验 trace 连续性、超时重试和错误分桶"}


@app.post("/mock/tool")
async def mock_tool(request: Request) -> Dict[str, str]:
    with tracer.start_as_current_span("mock.tool.handle") as span:
        span.set_attribute("ai.tool.received_traceparent", request.headers.get("traceparent", ""))
        await asyncio.sleep(0.05)
        return {"tool_result": "tool-ok"}


async def call_tool() -> Dict[str, str]:
    with tracer.start_as_current_span("tool.call") as span:
        span.set_attribute("ai.tool.name", "mock-qa-search")
        span.set_attribute("ai.tool.timeout_ms", 1000)
        headers: Dict[str, str] = {}
        propagate.inject(headers)
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.post("http://127.0.0.1:8000/mock/tool", headers=headers, json={"q": "otel"})
            response.raise_for_status()
            return response.json()


async def fake_generate(question: str, knowledge: str, tool_result: str) -> str:
    with tracer.start_as_current_span("llm.generate") as span:
        await asyncio.sleep(0.12 + random.uniform(0.01, 0.03))
        span.set_attribute("ai.model.name", "gpt-demo")
        span.set_attribute("ai.stream", False)
        span.set_attribute("ai.output.kind", "summary")
        return f"问题：{question}；知识：{knowledge}；工具结果：{tool_result}"


@app.post("/agent/run")
async def run_agent(payload: Dict[str, str], request: Request) -> Dict[str, str]:
    question = payload.get("input", "")

    with tracer.start_as_current_span("agent.plan") as span:
        span.set_attribute("ai.scenario", payload.get("scenario", "default"))
        span.set_attribute("ai.request_id", request.headers.get("x-request-id", ""))
        span.set_attribute("ai.plan.version", "v1")
        await asyncio.sleep(0.03)

    retrieved = await fake_retrieve(question)
    tool_response = await call_tool()
    final_answer = await fake_generate(question, retrieved["knowledge"], tool_response["tool_result"])

    current = trace.get_current_span().get_span_context()
    trace_id = format(current.trace_id, "032x")
    return {"trace_id": trace_id, "output": final_answer}
```

调用方式：

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H 'Content-Type: application/json' \
  -H 'x-request-id: day23-demo-001' \
  -d '{"input":"请总结 AI Agent 可观测性设计重点","scenario":"test-plan-generation"}'
```

这个示例最值得关注的不是 FastAPI 本身，而是三件工程事实：

- 入口请求、内部阶段、下游工具调用都处在 **同一条 trace** 里；
- 关键阶段的耗时和属性被显式建模，而不是只写一行“开始执行/执行完成”；
- 返回体里带回 `trace_id`，后续测试平台或日志系统就能拿这个字段完成链路关联。

## 3. 工程实践（二）：Go + Ginkgo 把 Trace 连续性变成 E2E 自动化断言

仅仅“打了 trace”还不够。对测开来说，更重要的是：**如何把 trace 连续性、span 完整性、上下游传播是否断链，变成自动化回归的一部分。**

下面这个例子模拟一条更接近 E2E 的链路：

- 测试客户端创建根 span，模拟“用户点击生成”；
- 请求进入 Agent 服务后继续沿用同一 trace；
- Agent 再调用下游工具服务，并把 `traceparent` 继续传下去；
- Ginkgo 用例最终断言：所有关键 span 共用同一条 trace，下游服务确实收到了 `traceparent`。

```go
// 文件名：agent_trace_e2e_test.go
// 依赖：
//   go get github.com/onsi/ginkgo/v2 github.com/onsi/gomega
//   go get go.opentelemetry.io/otel go.opentelemetry.io/otel/sdk/trace go.opentelemetry.io/otel/sdk/trace/tracetest
// 运行：go test ./... -v
package observability_test

import (
    "context"
    "io"
    "net/http"
    "net/http/httptest"
    "sort"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/propagation"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    "go.opentelemetry.io/otel/sdk/trace/tracetest"
)

var _ = Describe("Agent trace E2E", func() {
    It("should preserve one trace from client entry to downstream tool", func() {
        recorder := tracetest.NewSpanRecorder()
        tp := sdktrace.NewTracerProvider(sdktrace.WithSpanProcessor(recorder))
        defer func() { _ = tp.Shutdown(context.Background()) }()

        otel.SetTracerProvider(tp)
        otel.SetTextMapPropagator(propagation.TraceContext{})
        tracer := otel.Tracer("day23-e2e")

        toolTraceparent := make(chan string, 1)
        toolServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            toolTraceparent <- r.Header.Get("Traceparent")
            w.WriteHeader(http.StatusOK)
            _, _ = w.Write([]byte(`{"ok":true}`))
        }))
        defer toolServer.Close()

        agentServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            ctx := otel.GetTextMapPropagator().Extract(r.Context(), propagation.HeaderCarrier(r.Header))
            ctx, runSpan := tracer.Start(ctx, "agent.run")
            defer runSpan.End()

            _, planSpan := tracer.Start(ctx, "agent.plan")
            time.Sleep(10 * time.Millisecond)
            planSpan.End()

            ctx, toolSpan := tracer.Start(ctx, "tool.call")
            req, err := http.NewRequestWithContext(ctx, http.MethodPost, toolServer.URL, nil)
            if err != nil {
                w.WriteHeader(http.StatusInternalServerError)
                toolSpan.RecordError(err)
                toolSpan.End()
                return
            }
            otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header))

            resp, err := http.DefaultClient.Do(req)
            if err != nil {
                w.WriteHeader(http.StatusBadGateway)
                toolSpan.RecordError(err)
                toolSpan.End()
                return
            }
            _, _ = io.Copy(io.Discard, resp.Body)
            _ = resp.Body.Close()
            toolSpan.End()

            w.WriteHeader(http.StatusOK)
            _, _ = w.Write([]byte(`{"status":"ok"}`))
        }))
        defer agentServer.Close()

        clientCtx, clientSpan := tracer.Start(context.Background(), "ui.click.generate")
        req, err := http.NewRequestWithContext(clientCtx, http.MethodPost, agentServer.URL, nil)
        Expect(err).NotTo(HaveOccurred())
        otel.GetTextMapPropagator().Inject(clientCtx, propagation.HeaderCarrier(req.Header))

        resp, err := http.DefaultClient.Do(req)
        Expect(err).NotTo(HaveOccurred())
        _, _ = io.Copy(io.Discard, resp.Body)
        _ = resp.Body.Close()
        clientSpan.End()

        Eventually(toolTraceparent).Should(Receive(Not(BeEmpty())))

        spans := recorder.Ended()
        names := make([]string, 0, len(spans))
        traceIDs := map[string]struct{}{}
        for _, span := range spans {
            names = append(names, span.Name())
            traceIDs[span.SpanContext().TraceID().String()] = struct{}{}
        }
        sort.Strings(names)

        Expect(names).To(ContainElements(
            "ui.click.generate",
            "agent.run",
            "agent.plan",
            "tool.call",
        ))
        Expect(traceIDs).To(HaveLen(1))
    })
})
```

这个用例的价值在于，它不是只验证“接口返回 200”，而是验证一条完整链路里最核心的可观测性不变量：

- 用户入口与服务端 span 是否属于同一 trace；
- 子阶段 span 是否真的被创建；
- 下游工具服务是否接收到了传播过来的 `traceparent`；
- 一旦链路断掉，这个问题能否在回归测试阶段就被拦住。

## 4. 工程实践（三）：OTel Collector 的最小闭环

在本地 demo 里可以先把 trace 输出到控制台，但只要进入测试环境、预发或 K8s 集群，通常都需要一个统一入口来接收 OTLP 数据。下面是一份最小化的 Collector 配置：

```yaml
# 文件名：otel-collector.yaml
receivers:
  otlp:
    protocols:
      grpc:
      http:

processors:
  batch:

exporters:
  debug:
    verbosity: detailed
  otlp/tempo:
    endpoint: tempo.monitoring.svc.cluster.local:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug, otlp/tempo]
```

一个比较稳妥的落地顺序是：

1. **本地先跑通 Console / Debug Exporter**，确保 span 层次和属性合理；
2. **接入 Collector**，统一收敛 OTLP 数据，而不是每个服务各自直连后端；
3. **在测试平台里回填 trace_id**，让失败用例能一键跳转到链路详情；
4. **把关键指标门禁化**，例如按业务场景看 `TTFT P99`、`tool timeout rate`、`rag miss rate`。

如果你的链路里还有前端页面或控制台入口，比较好的做法是让 Playwright E2E 用例也携带统一的 `x-request-id` 或业务主键。这样 UI 自动化、接口自动化和后端 Trace 才能真正串成一条线。

## 5. 最容易踩的坑：链路打通了，不代表可观测性做好了

### 5.1 只有入口 Span，没有阶段 Span

这是最常见的问题。链路图上看起来“有 trace”，但只有一条粗线，仍然无法判断慢在哪个阶段。

### 5.2 Trace 在同步调用里能通，到了异步任务就断掉

很多 Agent 系统会把工具执行、审核或通知下沉到异步 worker。如果 `traceparent` 没有跟着任务消息一起传递，到队列或后台任务这里就会断链。

### 5.3 Span Attribute 写得太随意

最典型的问题是：

- 写入明文 prompt；
- 写入完整用户输入；
- 不区分错误阶段，只写一个 `error=true`；
- 把高基数字段（如原始 query）直接写成 metric label。

这些做法要么带来隐私/合规风险，要么会让观测系统本身变得难以维护。

### 5.4 只在失败时看 Trace，不把它纳入回归测试

可观测性的价值不应该只体现在“出问题后排障”，还应该体现在“平时就能验证链路没有悄悄退化”。

例如：

- 新版本上线后，`tool.call` span 突然消失；
- `ai.model.name` attribute 不再上报；
- 下游调用虽然成功，但 trace continuity 已经断掉。

这些问题如果不写进自动化回归，通常要到线上排障时才会第一次被发现。

## 6. 课后思考题（按完整 E2E 业务链路来设计）

1. **如果你要为“生成 API 回归测试方案”这条业务链路补一套可观测性设计，你会从“用户点击按钮”到“测试方案落盘并可下载”之间定义哪些关键 span、哪些中间验证点、哪些最终 SLO？**
2. **如果线上现象是“TTFT P99 基本稳定，但成功率下降”，你会如何结合 trace、log、metric 去区分：问题来自工具调用超时、检索 miss、还是模型输出被 guardrail 拦截？** 请按完整链路给出排查顺序。
3. **如果系统里有异步审核 worker，导致请求主链路和后台任务分成两段 trace，你会如何设计传播机制与 Ginkgo / Playwright 的 E2E 回归用例，确保 trace 不会在队列边界断掉？**

## 7. 今日小结

今天这篇内容最核心的收获是：

> **AI Agent 的可观测性，不是“多打一套日志”，而是把用户请求拆成可追踪、可验证、可门禁的执行链。**

对资深测试开发来说，Trace 的意义不只是排障方便，而是它能把很多“凭感觉”的问题变成确定性的工程对象：

- 从“系统偶发变慢”变成“`tool.call` 阶段 P99 退化”；
- 从“偶发失败难复现”变成“某类场景在 `rag.retrieve` 后进入 fallback”；
- 从“链路可能断了”变成“Ginkgo E2E 已经把 trace continuity 写成自动化断言”。

下一步最值得做的事，是把今天的思路直接接入你手头真实项目的测试环境：让每条高价值 E2E 用例都带着 `trace_id` 跑，让每次失败都能一键回看链路，让可观测性真正成为质量体系的一部分，而不是故障发生后才想起来补的一层“外挂”。
