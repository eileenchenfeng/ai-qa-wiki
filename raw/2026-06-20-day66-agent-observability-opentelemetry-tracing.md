---
title: "每日 AI 学习笔记｜Day 66：AI Agent 可观测性与链路追踪（OpenTelemetry + Trace）"
date: 2026-06-20
authors: [xiaoai]
tags: [learning-notes, AI, QA, observability, opentelemetry, tracing, agent]
---

## 核心总结

AI Agent 的可观测性不是"加几个日志"就够了。一个 Agent 请求里通常嵌套着 LLM 调用 → tool 调用 → 子 Agent 调用 → 向量检索 → 外部 HTTP，每一层都可能成为延时尖刺或质量塌方的元凶。**没有结构化的 Trace，根因定位就是猜谜**。本篇用 OpenTelemetry（OTel） + GenAI Semantic Conventions 给出一套可落地方案：Trace/Span/Attribute 怎么建模、Python/Go SDK 接入示例、如何把 prompt/tool I/O 安全脱敏后写进 span event、如何在 Tempo/Jaeger 上做"按 session_id 聚合 + 异常 span 下钻"、如何把 Trace 数据反哺到压测和回归测试。重点：**Trace 是 Agent 系统的"X 光"，测试开发必须会读、会埋、会断言**。

{/* truncate */}

## 一、核心理论

### 1.1 为什么 Agent 必须做分布式追踪

| 场景 | 没有 Trace | 有 Trace |
|---|---|---|
| 单次会话 30s 才返回 | 不知道时间花在哪 | 一眼看到是 vector_search 25s |
| 偶发幻觉 | 复现不了，看不到 prompt | 按 trace_id 调出完整 prompt + tool 结果 |
| 成本飙升 | 只能看账单总量 | 按 span 聚合 token，定位到具体 tool |
| 跨服务故障 | 各服务日志各看各的 | 一条 trace 串起 Gateway → Agent → Tool |

### 1.2 OpenTelemetry 三大概念在 Agent 中的映射

- **Trace**：一次用户请求/一次 Agent Session。`trace_id` 是排障的唯一索引。
- **Span**：一个逻辑单元，例如 `llm.chat`、`tool.call`、`vector.search`、`agent.plan`。Span 之间是父子关系。
- **Attribute / Event**：Span 上的 K-V 标签（如 `gen_ai.system="openai"`、`gen_ai.usage.input_tokens=1234`），以及时间点事件（如 `prompt`、`tool_result`）。

### 1.3 GenAI Semantic Conventions（必看）

OpenTelemetry 在 2024-2025 推出了 GenAI 语义规范，**强烈建议直接遵循**，否则后续接 Langfuse / Phoenix / Datadog LLM Observability 时会反复返工。关键 attribute：

- `gen_ai.system`：openai / anthropic / azure.ai.inference
- `gen_ai.request.model` / `gen_ai.response.model`
- `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens`
- `gen_ai.operation.name`：chat / embeddings / tool_call
- Span name 建议格式：`{operation} {model}`，例如 `chat gpt-4o-mini`

### 1.4 Agent Trace 的最小可用模型

```
session (root span)
├─ agent.plan
├─ llm.chat (round 1)
├─ tool.call: search_kb
│   └─ vector.search
├─ llm.chat (round 2)
├─ tool.call: create_ticket
│   └─ http.request POST /tickets
└─ agent.finalize
```

测试开发的关注点：**每一层都要能独立断言延时、错误、token、输入输出契约**。

## 二、工程实践

### 2.1 Python：用 OTel SDK 给一个 Agent 埋点

```python
# pip install opentelemetry-sdk opentelemetry-exporter-otlp
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

resource = Resource.create({"service.name": "qa-agent", "service.version": "0.66.0"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

def run_agent(session_id: str, user_query: str):
    with tracer.start_as_current_span("agent.session") as root:
        root.set_attribute("session.id", session_id)
        root.set_attribute("gen_ai.operation.name", "agent")
        # 1. plan
        with tracer.start_as_current_span("agent.plan"):
            plan = make_plan(user_query)
        # 2. LLM 调用
        for i, step in enumerate(plan):
            with tracer.start_as_current_span(f"llm.chat round-{i}") as s:
                s.set_attribute("gen_ai.system", "openai")
                s.set_attribute("gen_ai.request.model", "gpt-4o-mini")
                # 敏感内容只写 event，便于在采集端按需脱敏/采样
                s.add_event("prompt", {"content": redact(step.prompt)[:2000]})
                resp = llm_call(step.prompt)
                s.set_attribute("gen_ai.usage.input_tokens", resp.usage.input)
                s.set_attribute("gen_ai.usage.output_tokens", resp.usage.output)
                s.add_event("completion", {"content": redact(resp.text)[:2000]})
            # 3. tool 调用
            if step.tool:
                with tracer.start_as_current_span(f"tool.call {step.tool.name}") as t:
                    t.set_attribute("tool.name", step.tool.name)
                    try:
                        result = step.tool.invoke()
                        t.set_attribute("tool.status", "ok")
                    except Exception as e:
                        t.record_exception(e)
                        t.set_status(trace.Status(trace.StatusCode.ERROR))
                        raise
        return resp.text
```

### 2.2 Go（Ginkgo 集成测试中读取 Trace 断言）

```go
// 在 E2E 测试里发请求后，根据 trace_id 反查 Tempo，断言关键 span
var _ = Describe("Agent E2E with tracing", func() {
    It("应保证一次会话端到端 p95 < 8s，且无 ERROR span", func() {
        traceID, body := callAgentAndExtractTraceID("帮我查上周订单")
        Expect(body).To(ContainSubstring("订单"))

        trace, err := tempo.GetTrace(ctx, traceID)
        Expect(err).NotTo(HaveOccurred())

        // 断言一：根 span 延时
        root := trace.RootSpan()
        Expect(root.DurationMs()).To(BeNumerically("<", 8000))

        // 断言二：必须至少有一次 vector.search
        Expect(trace.SpansByName("vector.search")).NotTo(BeEmpty())

        // 断言三：没有 ERROR 状态的 span
        for _, s := range trace.AllSpans() {
            Expect(s.Status).NotTo(Equal("ERROR"), "span %s 异常", s.Name)
        }

        // 断言四：token 用量不超预算
        Expect(trace.SumAttr("gen_ai.usage.output_tokens")).To(BeNumerically("<=", 2000))
    })
})
```

> 关键思路：**Trace 不只是排障工具，更是测试断言的数据源**。把 SLO 写进 E2E 用例里，每次 CI 跑完即可看到回归。

### 2.3 Playwright + OTel：把前端会话和后端 trace 串起来

在前端发起请求时主动注入 `traceparent` Header（W3C Trace Context），后端继承这个上下文。这样 Playwright 用例失败时，可以直接拿到 trace_id 跳转 Tempo/Jaeger 查全链路。

```ts
const traceparent = `00-${randomTraceId()}-${randomSpanId()}-01`;
await page.route('**/api/agent/**', route =>
  route.continue({ headers: { ...route.request().headers(), traceparent } })
);
await page.click('text=提交');
// 失败时把 traceparent 写进 testInfo.attach，方便排障
test.info().attach('traceparent', { body: traceparent });
```

### 2.4 数据脱敏与采样策略

- **PII / Secrets**：在 SDK 层用拦截器对 prompt/completion 做正则脱敏（手机号、邮箱、token），**永远不要把 Authorization header 写进 attribute**。
- **采样**：默认 head-based 采样 10%；对错误请求或高延时请求用 tail-based 采样保留 100%（OTel Collector `tailsamplingprocessor`）。
- **大对象**：prompt/completion 超过 4KB 走对象存储，span 里只存引用 URL，避免 Trace 后端被打爆。

### 2.5 OTel Collector 推荐 Pipeline

```
receivers: [otlp]
processors:
  - memory_limiter
  - tail_sampling   # 错误/慢请求 100% 采样
  - attributes      # 脱敏
  - batch
exporters:
  - otlp/tempo      # 长期存储
  - prometheusremotewrite   # span metrics（RED 指标）
  - loki            # 关联日志
```

### 2.6 与压测/混沌的联动

- 压测（Day 65）跑完，按 trace 聚合 p99 慢请求，逆向找出瓶颈 span。
- 混沌注入故障时，**断言 Trace 中能看到对应错误 span**（否则说明可观测性盲区）。
- 把 trace_id 写到 K6/Locust 的失败报告里，根因定位时间从小时级降到分钟级。

## 三、课后思考题

1. 你当前的 Agent 服务里，一次"用户问→Agent 答"的请求，能否在 30 秒内通过 trace_id 定位到具体是哪次 LLM 调用慢了？如果不能，缺哪些 span？
2. 如果一次会话产生了 50+ 个 span，UI 上很难看。如何用"父子聚合 + 关键路径高亮"提升可读性？（提示：Tempo `span metrics` + Grafana flame graph）
3. Trace 中要不要记录完整 prompt？请从合规、调试效率、存储成本三个角度给出你的方案。
4. 如何在 CI 里基于 Trace 写一条"Agent 不允许出现循环 tool 调用 > 5 次"的断言？

## 四、今日小结

- Agent 可观测性的核心是 **Trace + 结构化 attribute**，OpenTelemetry GenAI Semantic Conventions 是事实标准。
- 测试开发要把 Trace 当作**测试数据源**：E2E 用例不仅断言响应，还要断言关键 span 的存在、延时、token 用量、错误率。
- 落地优先级：**SDK 埋点 → Collector 采样脱敏 → Tempo/Jaeger 存储 → Grafana RED 看板 → CI 断言**，缺一不可。
- 明天（Day 67）进入 **混沌工程（ChaosMesh / 故障注入框架）**，在 Trace 武装好的基础上，主动制造故障来验证 Agent 的韧性。
