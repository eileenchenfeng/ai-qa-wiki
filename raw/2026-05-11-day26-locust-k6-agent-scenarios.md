---
title: "每日 AI 学习笔记｜Day 26：面向 Agent 场景的 Locust/k6 性能压测工程化"
date: 2026-05-11
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, performance, load-testing, Locust, k6]
---

# 每日 AI 学习笔记 Day 26｜面向 Agent 场景的 Locust/k6 性能压测工程化

## 核心总结

面向 Senior SDET 的 Agent 性能压测，不应停留在“用 Locust 或 k6 打接口”的层面，而要把真实用户旅程、工作负载模型、性能 SLO、可观测证据和 CI 门禁连接成一条端到端质量链路。Locust 更适合表达复杂业务行为、动态数据准备和多步骤用户流；k6 更适合在工程流水线中固化阈值、趋势指标和快速回归门禁。对 AI Agent 来说，核心指标必须同时覆盖 **TTFT、E2E 完成耗时、业务成功率、阶段耗时、错误分桶和降级结果**，否则很容易出现“压测曲线好看，但用户任务失败”的假阳性结论。

{/* truncate */}

## 0. 今日目标

今天延续性能质量主题，重点从“脚本示例”升级到“工程化压测体系”。完成今天的学习后，你应该能够做到四件事。第一，能把 Agent 产品中的真实用户任务建模为 E2E 压测场景，而不是把模型接口、工具接口、检索接口拆成孤立压测点。第二，能判断 Locust 与 k6 在 Agent 性能测试中的边界，并让二者服务于同一套场景资产。第三，能设计可落地的 TTFT、P95/P99、业务成功率、阶段耗时与错误分桶门禁。第四，能把压测结果回写到研发工作流中，形成“发现退化、定位阶段、阻断发布、沉淀基线”的闭环。

本篇内容面向有后端、自动化、可观测与 CI/CD 经验的 Senior SDET，因此不会把重点放在工具安装，而是放在如何设计可信的 Agent 压测模型。

---

## 1. 核心理论：Agent 压测的对象是“用户任务”，不是单个接口

### 1.1 为什么传统 API 压测方法会失真

传统 API 压测通常默认请求路径稳定、响应结构确定、依赖数量可控。AI Agent 的真实链路则更接近动态工作流：一次用户任务可能包含规划、检索、工具调用、模型推理、结果校验、权限过滤和状态落盘。Prompt 版本、上下文长度、缓存命中、模型路由、工具返回质量都会改变执行路径。

因此，Agent 压测如果只盯一个 `/chat/completions` 或 `/agent/run` 接口的平均耗时，会遗漏至少三类风险。第一类是体验风险，例如连接成功但首 token 很慢。第二类是业务风险，例如最终状态是 `failed` 或 `partial`，但 HTTP 状态码仍然是 200。第三类是可运营风险，例如 P99 退化来自 RAG 或工具调用，却没有 trace 能解释。

Senior SDET 的压测设计要把请求看成一条完整业务旅程：用户触发任务，Agent 接收上下文，系统完成规划与工具调用，前端或 API 返回可观察结果，最终状态可追踪、可复盘、可审计。

### 1.2 Agent 性能 SLO 的五层模型

一条可信的 Agent 性能 SLO 至少应覆盖五层。

1. **入口层**：连接建立成功率、鉴权成功率、请求排队时间、网关 4xx/5xx。
2. **体验层**：TTFT、流式 token 间隔、页面首个可见反馈时间、用户等待时长。
3. **任务层**：E2E 完成耗时、最终状态、业务产物是否生成、用户是否可继续下一步。
4. **阶段层**：planner、retriever、tool call、model prefill、model decode、post-process 的耗时与错误。
5. **运营层**：错误分桶、降级比例、重试次数、熔断触发、trace 完整率、结果可解释率。

这五层可以映射成一个压测门禁原则：**请求快不等于成功，成功不等于体验好，体验好不等于系统可解释。** 对 Agent 产品来说，必须让性能指标和最终业务结果同时过关。

### 1.3 Locust 与 k6 的定位差异

Locust 和 k6 都能发压测流量，但它们的最佳使用场景不同。

Locust 的优势在于 Python 生态和用户行为建模。它适合表达多步骤 E2E 流程，例如创建测试项目、上传接口文档、触发 Agent 生成用例、轮询任务状态、下载结果并做业务断言。它也适合接入动态数据、测试账号、Mock 工具和复杂前置条件。

k6 的优势在于性能门禁和基础设施集成。它适合把阈值写入脚本，在 CI 中直接失败；也适合对 WebSocket、HTTP streaming、REST API 进行轻量、可重复、可版本化的趋势回归。

更成熟的做法不是二选一，而是让二者复用同一份 **E2E 场景资产**：场景定义、输入数据、业务标签、trace 规范、SLO 阈值保持一致；Locust 负责复杂行为和长时压测，k6 负责快速门禁和趋势回归。

---

## 2. E2E 工作负载模型：从真实用户旅程抽样

### 2.1 不要随机拼 Prompt，要抽样业务旅程

Agent 压测的工作负载不应是随机 Prompt 集合，而应来自真实使用场景。下面是一组可复用的 E2E 场景组合。

- **短任务规划场景**：用户输入一个清晰目标，Agent 只需要规划和简短输出，主要验证 TTFT、planner 延迟和入口稳定性。
- **RAG 问答场景**：用户基于知识库提问，Agent 需要检索、重排和引用生成，主要验证 retriever、上下文构造和模型 prefill。
- **工具重度场景**：用户要求 Agent 调用多个工具完成任务，主要验证工具链路、重试、超时、幂等和降级。
- **长上下文审阅场景**：用户提交较长文档或报告，Agent 需要总结、判断风险、输出结构化结论，主要验证上下文窗口、长尾延迟和结果完整性。
- **交互式修正场景**：用户在首轮结果基础上追问或要求改写，主要验证会话状态、缓存命中、历史上下文和连续体验。

每个场景都应从用户动作开始，到最终可观察结果结束。单个 API 的响应、单个工具的返回、单次模型调用的速度，都应作为 E2E 链路中的中间状态或验证点，而不是独立成一条脱离业务的压测用例。

### 2.2 场景资产的最小字段

建议用 JSON 或 YAML 保存场景资产，便于 Locust、k6、Ginkgo 和 Playwright 共用。一个场景至少包含以下字段：

```json
{
  "case_id": "agent-perf-tool-heavy-001",
  "scenario": "tool-heavy-test-plan-generation",
  "weight": 20,
  "user_action": "Submit an Agent task to generate an API regression test plan from service metadata.",
  "input": {
    "task": "Generate an API regression plan for order creation and refund flows.",
    "context_size": "medium",
    "stream": true
  },
  "expected_intermediate_states": [
    "planner_started",
    "retriever_completed",
    "tool_call_completed",
    "first_token_emitted"
  ],
  "final_checks": [
    "status in ['succeeded', 'degraded']",
    "result_artifact_url exists",
    "trace_id exists",
    "error_bucket is empty or classified"
  ],
  "slo": {
    "ttft_p95_ms": 2000,
    "e2e_p95_ms": 20000,
    "business_success_rate": 0.99
  }
}
```

这份资产的关键价值在于：它不是只服务压测脚本，而是服务整个质量体系。Ginkgo 可以拿它做功能 E2E，Playwright 可以拿它验证页面结果，Locust 可以拿它组织混合负载，k6 可以拿它做 CI 门禁。

### 2.3 工作负载比例的设计原则

工作负载比例要反映真实产品使用，而不是只压最容易写脚本的路径。对于 Agent 产品，可以从以下比例开始，再根据线上观测调整：短任务规划 40%，RAG 问答 25%，工具重度 20%，长上下文审阅 10%，交互式修正 5%。

比例设计还要区分三个阶段。Smoke 阶段使用小并发，快速发现功能与配置问题。Baseline 阶段固定环境、固定数据、固定模型版本，用于建立可对比基线。Stress 或 Soak 阶段拉高并发或延长时间，用于观察队列堆积、连接耗尽、内存泄漏和长尾抖动。

---

## 3. Locust 实战：把 Agent 用户旅程写成可执行负载

### 3.1 Locust 脚本结构

下面的示例不是单点压接口，而是围绕“用户提交 Agent 任务并等待最终状态”的完整链路。脚本会记录 TTFT、E2E 耗时和业务成功率，并按场景打标签。

```python
# locustfile.py
import json
import random
import time
import uuid

from locust import HttpUser, between, events, task

SCENARIOS = [
    {
        "name": "short-planning",
        "weight": 40,
        "task": "Create a concise smoke test plan for a checkout API.",
        "slo_ttft_ms": 1500,
    },
    {
        "name": "rag-answer",
        "weight": 25,
        "task": "Answer release risk questions from the QA knowledge base.",
        "slo_ttft_ms": 2500,
    },
    {
        "name": "tool-heavy",
        "weight": 20,
        "task": "Generate regression cases, call test data tools, and summarize evidence.",
        "slo_ttft_ms": 3000,
    },
    {
        "name": "long-context-review",
        "weight": 10,
        "task": "Review a long incident report and extract performance regression risks.",
        "slo_ttft_ms": 4000,
    },
    {
        "name": "interactive-revision",
        "weight": 5,
        "task": "Revise the previous Agent output with stricter acceptance criteria.",
        "slo_ttft_ms": 2500,
    },
]


def choose_scenario():
    return random.choices(
        SCENARIOS,
        weights=[item["weight"] for item in SCENARIOS],
        k=1,
    )[0]


class AgentE2ELoadUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def run_agent_journey(self):
        scenario = choose_scenario()
        trace_id = f"locust-{uuid.uuid4().hex}"
        payload = {
            "case_id": f"agent-perf-{scenario['name']}",
            "task": scenario["task"],
            "stream": True,
            "trace_id": trace_id,
            "metadata": {
                "scenario": scenario["name"],
                "source": "locust-e2e-load",
            },
        }

        started_at = time.perf_counter()
        first_token_at = None
        final_status = "unknown"
        error_bucket = "none"

        with self.client.post(
            "/agent/run",
            json=payload,
            name=f"agent:e2e:{scenario['name']}",
            stream=True,
            catch_response=True,
            timeout=60,
            headers={"x-trace-id": trace_id},
        ) as response:
            try:
                for raw_line in response.iter_lines():
                    if not raw_line:
                        continue
                    event = json.loads(raw_line.decode("utf-8"))
                    if event.get("type") == "token" and first_token_at is None:
                        first_token_at = time.perf_counter()
                    if event.get("type") == "completed":
                        final_status = event.get("status", "unknown")
                        error_bucket = event.get("error_bucket", "none")
                        break

                e2e_ms = (time.perf_counter() - started_at) * 1000
                ttft_ms = (first_token_at - started_at) * 1000 if first_token_at else None

                if ttft_ms is not None:
                    events.request.fire(
                        request_type="METRIC",
                        name=f"agent:ttft:{scenario['name']}",
                        response_time=ttft_ms,
                        response_length=0,
                        exception=None,
                    )

                business_ok = final_status in {"succeeded", "degraded"} and error_bucket != "unclassified"
                if response.status_code == 200 and business_ok:
                    response.success()
                else:
                    response.failure(
                        f"business failure status={final_status} error_bucket={error_bucket} trace_id={trace_id}"
                    )

                events.request.fire(
                    request_type="METRIC",
                    name=f"agent:e2e:{scenario['name']}",
                    response_time=e2e_ms,
                    response_length=0,
                    exception=None,
                )
            except Exception as exc:
                response.failure(f"stream parse error: {type(exc).__name__}: {exc}")
```

这段脚本的重点不是语法，而是设计思想：每一次请求都带 `case_id`、`scenario` 和 `trace_id`；每一次成功都必须通过最终业务状态判定；TTFT 作为独立指标上报；错误必须分桶，不能只留下“失败了”三个字。

### 3.2 Locust 适合验证的 E2E 中间状态

在 Locust 中，可以把单点验证下沉为 E2E 旅程的中间状态。例如工具重度场景的压测步骤可以这样组织：用户提交任务后，预期中间状态包括 `planner_started`、`tool_call_started`、`tool_call_completed`、`first_token_emitted`；最终验证点包括状态为 `succeeded` 或可解释的 `degraded`、结果产物存在、trace 中包含工具 span、未出现未分类错误。

这样设计符合真实用户视角，也能避免“工具 API 单独压测通过，但 Agent 编排在高并发下失败”的割裂。

---

## 4. k6 实战：把性能阈值固化为 CI 门禁

### 4.1 k6 脚本结构

k6 更适合做可重复的快速门禁。下面示例针对 HTTP streaming Agent 接口，统计 TTFT、E2E 耗时、业务成功率和未分类错误。

```javascript
// agent-e2e-load.js
import http from 'k6/http';
import { check } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

export const agentTTFT = new Trend('agent_ttft_ms', true);
export const agentE2E = new Trend('agent_e2e_ms', true);
export const businessSuccess = new Rate('agent_business_success');
export const unclassifiedErrors = new Counter('agent_unclassified_errors');

export const options = {
  scenarios: {
    smoke_gate: {
      executor: 'ramping-vus',
      stages: [
        { duration: '30s', target: 5 },
        { duration: '1m', target: 20 },
        { duration: '30s', target: 0 },
      ],
    },
  },
  thresholds: {
    agent_business_success: ['rate>=0.99'],
    agent_ttft_ms: ['p(95)<2500', 'p(99)<5000'],
    agent_e2e_ms: ['p(95)<25000', 'p(99)<60000'],
    agent_unclassified_errors: ['count==0'],
    http_req_failed: ['rate<0.01'],
  },
};

const scenarios = [
  { name: 'short-planning', weight: 40, task: 'Create smoke checks for checkout API.' },
  { name: 'rag-answer', weight: 25, task: 'Answer a QA release risk question from knowledge base.' },
  { name: 'tool-heavy', weight: 20, task: 'Generate regression cases and call test data tools.' },
  { name: 'long-context-review', weight: 10, task: 'Review a long report and extract risk signals.' },
  { name: 'interactive-revision', weight: 5, task: 'Revise the prior answer using stricter acceptance criteria.' },
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

function parseStreamingBody(body) {
  let firstTokenMs = null;
  let finalStatus = 'unknown';
  let errorBucket = 'none';

  const lines = body.split('\n').filter(Boolean);
  for (const line of lines) {
    const event = JSON.parse(line);
    if (event.type === 'token' && firstTokenMs === null) {
      firstTokenMs = Number(event.elapsed_ms || 0);
    }
    if (event.type === 'completed') {
      finalStatus = event.status || 'unknown';
      errorBucket = event.error_bucket || 'none';
    }
  }

  return { firstTokenMs, finalStatus, errorBucket };
}

export default function () {
  const scenario = pickScenario();
  const traceId = `k6-${__VU}-${__ITER}-${Date.now()}`;
  const url = `${__ENV.AGENT_BASE_URL || 'http://localhost:8080'}/agent/run`;

  const payload = JSON.stringify({
    case_id: `agent-perf-${scenario.name}`,
    task: scenario.task,
    stream: true,
    trace_id: traceId,
    metadata: {
      scenario: scenario.name,
      source: 'k6-ci-gate',
    },
  });

  const startedAt = Date.now();
  const response = http.post(url, payload, {
    headers: {
      'content-type': 'application/json',
      'x-trace-id': traceId,
    },
    tags: {
      scenario: scenario.name,
    },
    timeout: '60s',
  });

  const e2eMs = Date.now() - startedAt;
  agentE2E.add(e2eMs, { scenario: scenario.name });

  let parsed = { firstTokenMs: null, finalStatus: 'unknown', errorBucket: 'parse_error' };
  try {
    parsed = parseStreamingBody(response.body || '');
  } catch (error) {
    unclassifiedErrors.add(1, { scenario: scenario.name });
  }

  if (parsed.firstTokenMs !== null) {
    agentTTFT.add(parsed.firstTokenMs, { scenario: scenario.name });
  }

  const ok = check(response, {
    'http status is 200': (r) => r.status === 200,
    'agent final status is acceptable': () => ['succeeded', 'degraded'].includes(parsed.finalStatus),
    'agent error is classified': () => parsed.errorBucket !== 'unclassified',
    'agent emitted first token': () => parsed.firstTokenMs !== null,
  });

  businessSuccess.add(ok, { scenario: scenario.name });
  if (parsed.errorBucket === 'unclassified') {
    unclassifiedErrors.add(1, { scenario: scenario.name });
  }
}
```

### 4.2 k6 门禁不要只写全局阈值

全局阈值容易掩盖场景差异。短任务规划的 TTFT P99 可以要求更严格，而长上下文审阅天然更慢。如果所有场景共用一个阈值，可能出现两种问题：要么阈值过宽，短任务退化无法发现；要么阈值过窄，长任务持续误报。

更好的做法是按场景打标签，再逐步沉淀分场景阈值。例如 `short-planning` 关注入口和 planner，`rag-answer` 关注 retriever 与 prefill，`tool-heavy` 关注工具调用和重试，`long-context-review` 关注上下文长度和 decode。

---

## 5. Senior SDET 的压测诊断路径

### 5.1 从现象到阶段定位

当压测失败时，不要直接说“系统慢”。先根据指标组合判断退化阶段。

如果 TTFT 变差但 E2E 没有明显变化，优先看网关排队、planner、RAG 检索和模型 prefill。如果 TTFT 稳定但 E2E 变差，优先看工具调用、模型 decode、输出长度和后处理。如果成功率下降但耗时不变，优先看限流、熔断、权限、工具错误和业务状态机。如果 P99 抖动明显但 P50 稳定，优先看连接池、队列、缓存击穿、下游长尾和资源争用。

压测报告要给出可行动结论，而不是只贴曲线。一个成熟的结论应包含退化场景、影响指标、疑似阶段、证据链接、复现命令、回滚或修复建议。

### 5.2 Trace 规范决定压测可解释性

每条压测请求都应携带统一追踪字段。建议至少包含 `qa_run_id`、`case_id`、`scenario`、`trace_id`、`build_sha`、`model_version`、`prompt_version` 和 `dataset_version`。这些字段应贯穿入口日志、Agent 编排日志、RAG span、工具 span、模型调用指标和最终业务结果。

没有这些字段，压测只能回答“慢了没有”；有这些字段，压测才能回答“哪类用户任务、在哪个版本、哪个阶段、因为什么慢了”。

### 5.3 报告模板建议

一份高质量的 Agent 性能报告应包含以下内容：测试目标、版本信息、工作负载模型、环境约束、SLO 阈值、通过/失败结论、Top 退化场景、阶段耗时分解、错误分桶、trace 样本、下一步行动。对于 CI 门禁报告，应把内容控制在“能让研发 10 分钟内判断是否需要阻断发布”的粒度。

---

## 6. CI/CD 集成：把压测变成发布前的质量门禁

### 6.1 推荐流水线结构

Agent 性能门禁可以分三层进入流水线。

第一层是 PR 或合并前的轻量 Smoke Gate，只跑少量 E2E 场景，目标是发现明显功能破坏、连接失败、未分类错误和 TTFT 大幅退化。第二层是预发 Baseline Gate，使用固定数据和固定环境跑标准负载，目标是对比历史基线，阻断不可接受的 P95/P99 或成功率退化。第三层是发布后的 Canary Watch，接入真实观测指标，目标是发现灰度用户下的长尾、降级和错误分桶变化。

这种结构能平衡速度和可信度。PR 阶段不追求完整容量评估，预发阶段不追求每次都极限压测，线上阶段不依赖合成数据做唯一判断。

### 6.2 基线版本化

基线不是一个固定数字，而是一份可追溯资产。建议基线文件记录以下信息：测试时间、代码版本、模型版本、Prompt 版本、数据集版本、环境规格、场景权重、并发模型、Warm-up 设置、P50/P95/P99、成功率、错误分桶和 trace 样本。

当压测门禁失败时，SDET 应区分三种情况。第一，真实性能退化，需要阻断发布。第二，基线已过期，需要重新建立并记录原因。第三，测试环境不稳定，需要标记无效运行并修复环境，而不是随意放宽阈值。

---

## 7. 今日 E2E 练习题

### 7.1 练习一：为“生成测试方案 Agent”设计 Locust 工作负载

请设计一条完整 E2E 压测链路：用户上传接口说明，点击生成测试方案，Agent 进行规划、检索历史用例、调用用例生成工具、流式输出方案，最终生成可下载产物。执行步骤中需要包含中间状态验证，例如任务状态从 `queued` 到 `running`，trace 中出现 retriever span 和 tool span，首 token 在阈值内出现。最终验证点需要包含业务状态成功、产物存在、错误已分类、P95/P99 满足 SLO。

### 7.2 练习二：用 k6 固化 PR 性能门禁

请把同一条 E2E 场景资产转化为 k6 门禁脚本，要求在 CI 中输出四类指标：TTFT、E2E 耗时、业务成功率、未分类错误数。门禁失败时需要能通过 `trace_id` 找到至少三条失败样本，并在报告中说明失败集中在哪个场景。

### 7.3 练习三：诊断一次 P99 退化

假设新版本中 `tool-heavy` 场景的 E2E P99 从 18 秒退化到 42 秒，但 TTFT P99 基本不变，业务成功率仍为 99.3%。请设计后续排查路径：你会如何从工具调用耗时、重试次数、连接池、下游限流、模型 decode 和结果后处理几个方向逐步缩小范围？最终报告中应如何给出阻断发布或放行的依据？

---

## 8. 结语

Agent 性能压测的成熟度，不取决于使用了 Locust 还是 k6，而取决于是否真正围绕用户任务建立了可重复、可解释、可门禁的 E2E 质量体系。Locust 帮你把复杂业务行为压出来，k6 帮你把关键阈值守住；场景资产、trace 规范和基线治理则决定压测结果能否推动工程改进。

对 Senior SDET 来说，最重要的能力是把“性能指标”翻译成“用户影响”和“工程行动”。只有当每一次压测都能回答谁受影响、哪个场景退化、哪个阶段可疑、是否应该阻断发布，性能测试才真正从工具操作升级为质量工程。
