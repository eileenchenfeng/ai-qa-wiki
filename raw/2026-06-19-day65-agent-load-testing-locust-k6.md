---
title: "每日 AI 学习笔记｜Day 65：AI Agent 性能压测实战（Locust + k6 + Agent 场景）"
date: 2026-06-19
authors: [xiaoai]
tags: [learning-notes, AI, QA, performance-testing, locust, k6, load-testing, agent]
---

## 核心总结

AI Agent 的性能压测和传统 Web/API 压测最大的差异在于：**单次请求成本高（LLM token 计费 + 多轮工具调用）、响应时间分布长尾严重（p99 可能是 p50 的 10 倍以上）、状态多（会话/记忆/工具上下文）**。盲目套用传统 RPS 思路只会烧钱并掩盖真实瓶颈。本篇从工具选型（Locust 适合写复杂 Agent 业务流，k6 适合做高并发恒定负载和 CI 集成）、压测模型（Open Model vs Closed Model）、Agent 场景化压测脚本，到指标设计（不仅看 RPS / latency，还要看 token throughput、tool-call fan-out、cost per session、SLO 错误预算消耗），给出一套可直接落地的工程方案。

{/* truncate */}

## 一、核心理论

### 1.1 为什么 Agent 压测不能照搬传统接口压测

| 维度 | 传统 API 压测 | AI Agent 压测 |
|---|---|---|
| 单请求成本 | 微秒级 CPU、可忽略 | 数秒~数十秒、按 token 计费 |
| 响应时间分布 | 接近正态，p99 ≈ 1.5×p50 | 重尾，p99 经常 5~10×p50 |
| 状态 | 多为无状态/轻状态 | 强状态：session、memory、tool ctx |
| 失败语义 | HTTP 4xx/5xx | 还包含语义错误、幻觉、tool 失败、超 token |
| 容量瓶颈 | CPU/DB/连接池 | LLM 配额、tool 下游、向量库、显存 |

### 1.2 Open Model vs Closed Model

- **Closed Model（Locust 默认）**：固定并发用户数 N，每个用户串行发请求。压低延时会自然降低 RPS。**适合模拟真实用户会话**（用户必须等上一轮 Agent 回复才能发下一轮）。
- **Open Model（k6 `constant-arrival-rate`）**：按目标到达率注入请求，与系统响应快慢无关。**适合做容量规划和 SLO 验证**，能暴露排队、超时雪崩。

> Agent 压测建议：**业务真实性场景用 Closed（Locust），容量上限/SLO 验证用 Open（k6）**，两者互补。

### 1.3 Agent 压测必须看的指标

1. **延时**：TTFT（Time To First Token，流式场景关键）、端到端 latency p50/p95/p99
2. **吞吐**：sessions/sec、tool-calls/sec、**tokens/sec（input + output 分开看）**
3. **质量**：成功率（schema 合法 + 语义合格）、幻觉率、工具调用成功率
4. **成本**：$/session、$/successful-task（失败的会话也烧 token）
5. **饱和度**：LLM 配额使用率、下游 tool 错误率、context window 使用率

---

## 二、工程实践

### 2.1 Locust：模拟真实多轮 Agent 会话

适合写复杂业务流：登录 → 创建会话 → 多轮对话 → 调用工具 → 验收结果。

```python
# locustfile.py
from locust import HttpUser, task, between, events
import uuid, time, json

class AgentUser(HttpUser):
    wait_time = between(1, 3)  # 模拟用户思考时间，Closed Model 关键

    def on_start(self):
        self.session_id = str(uuid.uuid4())
        self.headers = {"Authorization": f"Bearer {self.environment.parsed_options.token}"}

    @task(3)
    def multi_turn_conversation(self):
        """端到端 E2E：用户提问 → Agent 调工具 → 返回结果"""
        turns = [
            "帮我查一下上海明天的天气",
            "如果下雨，推荐一家室内餐厅",
            "帮我预订晚上 7 点 2 人位",
        ]
        for turn_idx, msg in enumerate(turns):
            start = time.time()
            with self.client.post(
                "/v1/agent/chat",
                json={"session_id": self.session_id, "message": msg, "stream": False},
                headers=self.headers,
                name=f"/agent/chat[turn={turn_idx}]",
                catch_response=True,
            ) as resp:
                if resp.status_code != 200:
                    resp.failure(f"http {resp.status_code}")
                    return
                data = resp.json()
                # 关键：业务语义校验，不只看 200
                if not data.get("reply") or data.get("tool_error"):
                    resp.failure(f"semantic fail: {data.get('error')}")
                    return
                # 自定义指标：token 消耗
                events.request.fire(
                    request_type="TOKEN",
                    name="output_tokens",
                    response_time=data["usage"]["output_tokens"],
                    response_length=0,
                )

    @task(1)
    def tool_heavy_query(self):
        """重工具链场景：Agent 触发多次 tool call"""
        self.client.post("/v1/agent/chat",
            json={"session_id": str(uuid.uuid4()),
                  "message": "对比 iPhone 15 / Pixel 8 / 小米 14 的相机评测",
                  "stream": False},
            headers=self.headers, name="/agent/tool-heavy")
```

启动：

```bash
locust -f locustfile.py --host=https://agent.example.com \
       -u 50 -r 5 --run-time 10m \
       --html report.html --csv results
```

### 2.2 k6：恒定到达率 + SLO 校验（CI 友好）

```javascript
// agent_load.js
import http from 'k6/http';
import { check } from 'k6';
import { Trend, Counter } from 'k6/metrics';

const ttft = new Trend('agent_ttft_ms', true);
const tokenCost = new Counter('agent_output_tokens');

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-arrival-rate',
      rate: 20,            // 20 sessions/sec，与响应快慢无关
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 100,
      maxVUs: 500,
    },
  },
  thresholds: {
    'http_req_duration{name:chat}': ['p(95)<8000', 'p(99)<15000'],
    'http_req_failed': ['rate<0.02'],
    'agent_ttft_ms': ['p(95)<2000'],
  },
};

export default function () {
  const start = Date.now();
  const res = http.post(
    'https://agent.example.com/v1/agent/chat',
    JSON.stringify({ session_id: __VU + '-' + __ITER, message: '总结今天的 AI 新闻' }),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'chat' } }
  );
  ttft.add(Date.now() - start);
  if (res.status === 200) {
    const body = res.json();
    tokenCost.add(body.usage?.output_tokens || 0);
    check(res, {
      'reply not empty': (r) => r.json('reply') && r.json('reply').length > 0,
      'no tool_error': (r) => !r.json('tool_error'),
    });
  }
}
```

CI 集成（GitHub Actions 片段）：

```yaml
- name: k6 load test
  run: k6 run --quiet --summary-export=summary.json agent_load.js
- name: Fail on SLO violation
  run: |
    jq -e '.metrics.http_req_duration.values["p(95)"] < 8000' summary.json
```

### 2.3 Ginkgo（Golang）做轻量并发 smoke

复杂多轮和 SLO 用 Locust/k6；但**回归测试中**可用 Ginkgo + `errgroup` 跑一组并发的代表性 case，与 K8s HPA 联动验证扩缩容：

```go
var _ = Describe("Agent concurrent smoke", func() {
    It("50 concurrent sessions complete under 10s p95", func() {
        eg, ctx := errgroup.WithContext(context.Background())
        latencies := make([]time.Duration, 50)
        for i := 0; i < 50; i++ {
            i := i
            eg.Go(func() error {
                t0 := time.Now()
                _, err := agentClient.Chat(ctx, &pb.ChatReq{
                    SessionId: fmt.Sprintf("smoke-%d", i),
                    Message:   "ping",
                })
                latencies[i] = time.Since(t0)
                return err
            })
        }
        Expect(eg.Wait()).To(Succeed())
        sort.Slice(latencies, func(i, j int) bool { return latencies[i] < latencies[j] })
        p95 := latencies[int(float64(len(latencies))*0.95)]
        Expect(p95).To(BeNumerically("<", 10*time.Second))
    })
})
```

### 2.4 Playwright：UI 端到端的并发验证

UI 侧不追求高 RPS，而是验证**前端在后端被压时的退化体验**（loading 状态、超时提示、流式打字效果）：

```typescript
test('Agent UI degrades gracefully under load', async ({ browser }) => {
  const contexts = await Promise.all(
    Array.from({ length: 10 }, () => browser.newContext())
  );
  await Promise.all(contexts.map(async (ctx) => {
    const page = await ctx.newPage();
    await page.goto('/chat');
    await page.fill('[data-testid=input]', '复杂的多步推理任务');
    await page.click('[data-testid=send]');
    // 关键：流式 TTFT 必须在 3s 内出现首 token
    await expect(page.locator('[data-testid=streaming]')).toBeVisible({ timeout: 3000 });
  }));
});
```

### 2.5 K8s 视角：压测时必看的资源信号

```bash
# 压测期间持续观察
kubectl top pods -l app=agent --containers
kubectl get hpa agent-hpa -w
kubectl logs -l app=agent --tail=100 | grep -E "rate_limit|context_overflow|tool_timeout"
```

**经验**：HPA 仅看 CPU 经常误判，需要接入**自定义指标**（pending_sessions、llm_queue_depth）通过 Prometheus Adapter 暴露给 HPA。

---

## 三、课后思考题

1. 你的 Agent 服务在 k6 `constant-arrival-rate=50/s` 下 p99 飙到 30s，但 CPU 只用了 40%，最可能的瓶颈在哪三个地方？如何分别验证？
2. Closed Model 压测得到 RPS=12，Open Model 想验证 SLO 设到多少 arrival rate 才合理？为什么不能直接设 12？
3. 单次压测烧掉了 $80 token 费用，如何在不损失代表性的前提下把成本压到 $10 以内？（提示：mock 分层、代表性子集、缓存）
4. HPA 基于 CPU 扩容时，Agent 出现"扩容了但延迟没降"，背后可能是什么模型问题？

---

## 今日小结

- Agent 压测必须区分 **Closed Model（真实会话）** 和 **Open Model（容量/SLO）**，两者搭配使用。
- **Locust 写业务流，k6 跑 SLO，Ginkgo 做并发 smoke，Playwright 验证降级 UX**——四件套各司其职。
- 指标不能只看 RPS / latency，必须加上 **token throughput、$/session、tool-call 成功率、context 使用率**。
- CI 中接入 k6 thresholds 是把性能 SLO 守门员化的最低成本方案。
- 真正的瓶颈往往不在自家服务，而在 **LLM 配额、向量库、第三方 tool**——压测脚本要具备区分上下游的能力。

明日预告：**Day 66 — 可观测性与链路追踪（OpenTelemetry + Trace）**，把今天压测发现的长尾问题，用 trace 定位到具体的 span。
