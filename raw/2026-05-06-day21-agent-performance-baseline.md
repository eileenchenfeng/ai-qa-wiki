---
title: "每日 AI 学习笔记｜Day 21：AI Agent 性能与稳定性基线测试"
date: 2026-05-06
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, performance, baseline]
---

# 每日 AI 学习笔记 Day 21｜AI Agent 性能与稳定性基线测试

面向：资深测试开发（Golang Ginkgo / Python Playwright / K8s / API Testing）
关键词：**TTFT / TPS / P99 延迟 / 成功率 / 稳定性 / 压测模型 / 基线门禁 / CI Gate / 可观测**

---

{/* truncate */}

## 0. 今日目标

- 把"Agent 变慢了/不稳定了"从主观感受变成可量化的指标：能说清楚问题是 TTFT 变差？P99 变差？还是成功率下降？
- 建立"可长期复用"的性能与稳定性基线：基线可版本化、可对比、可在 CI/预发自动跑。
- 用测开工程化方式把基线变成门禁：新版本若性能退化超过阈值，自动失败并输出可定位的证据。

---

## 1. 核心理论：AI Agent 性能与稳定性基线

### 1.1 为什么 AI Agent 特别需要"性能与稳定性基线"？

传统后端系统做性能基线，核心对象通常是：**固定逻辑 + 可预测耗时**。而 AI Agent 的链路更像"动态工作流引擎"：

- **路径不固定**：同一用户问题，Agent 可能走不同的计划（planning）、不同的工具链、不同的检索路径。
- **调用外部依赖多**：模型推理、向量检索、第三方工具、内部服务……任何一个抖动都会成为长尾。
- **输出是流式的**：用户感知强依赖 **TTFT（首 token 延迟）**，而不是完整结束的耗时。
- **非确定性**：模型自身波动（采样、多副本负载、KV cache 状态、GPU 争用）让性能具有天然噪声。

因此，你需要的是一套能长期复用的方法：
1. 在同等负载与环境下，定义可重复的基线
2. 能把波动当噪声处理（统计分位数与置信）
3. 能把退化当回归处理（版本差异对比与门禁）

### 1.2 性能、稳定性、可用性：三个概念别混在一起

| 维度 | 关注点 |
|---|---|
| **性能（Performance）** | 同样请求在一定并发/吞吐下，响应有多快？ |
| **稳定性（Stability）** | 长时间运行/高负载下，系统是否出现明显波动、抖动、内存泄漏、超时增多、错误激增？ |
| **可用性（Availability）** | 从用户视角看，请求是否能完成？例如 success rate、5xx、工具调用失败。 |

### 1.3 指标体系：从用户体验到链路分解

#### 用户体验核心指标（SLI）

- **TTFT（Time To First Token）**：首 token 延迟。用户感知"有没有反应"。
- **TTLB / TTLM（Time To Last Byte / Last Message）**：完整响应耗时。
- **P50 / P90 / P95 / P99 延迟**：分位数指标，观察长尾。Agent 性能回归经常首先体现在 **P99 变差**，平均值反而变化不大。
- **TPS（Tokens Per Second）**：生成阶段吞吐。注意区分 **prefill**（首 token 前）与 **decode**（持续生成）。

#### 可靠性/稳定性指标

- **成功率（Success Rate）**：成功请求数 / 总请求数（注意定义"成功"的边界）
- **错误率分桶**：超时 / 429 限流 / 5xx / tool_error / model_error
- **抖动（Jitter）**：P99 在时间维度上的波动幅度
- **资源稳定性**：CPU/GPU/显存/内存/goroutine 是否"越跑越高"

#### Agent 链路分解指标

| 阶段 | 说明 |
|---|---|
| Gateway | 排队/鉴权/路由/连接建立 |
| Agent Orchestrator | planning、路由、状态机推进 |
| Retriever（RAG） | embedding、向量检索、重排 |
| Tool Calls | 外部 HTTP/RPC 调用 |
| Model | prefill + decode（TTFT/TPS 的根源） |
| Post-process | 结构化校验、敏感信息过滤、格式化输出 |

**经验规律：**
- TTFT 退化 → 多发生在网关排队、Orchestrator 规划、RAG 检索、模型 prefill
- TTLM 退化但 TTFT 不变 → 工具调用变慢、模型 decode 变慢、输出变长
- 成功率下降 → 依赖错误、限流或熔断策略变化

### 1.4 基线建立方法论：从"跑一次"到"能长期对比"

**Step 1：明确基线目标**
- SLO（服务目标）：如 TTFT P99 < 3s
- 回归对比（相对指标）：如 P99 不得比 baseline 退化超过 15%

**Step 2：定义 Workload Model（负载模型）**
固定：请求类型集合 + 比例权重 + 上下文长度分布 + 并发/吞吐模式

**Step 3：固定环境并做 Warm-up**
基线要分 Warm-up 阶段（不计入指标）和 Measure 阶段（计入 P99/成功率）

**Step 4：统计口径：分位数 + 多次重复抵抗噪声**
每次基线至少 Warm-up + 2~3 轮测量，使用 P50/P90/P99 + 标准差/IQR

**Step 5：版本化 + 可对比 + 可门禁**
以 JSON/CSV 保存基线，附上版本号、环境信息、workload 配置 hash。

---

## 2. 工程实践（可运行代码）

### 2.1 压测用例分层设计

| 类型 | 目标 | 典型权重 |
|---|---|---|
| S 类（Short）短输入短输出 | 测 TTFT 与网关/调度开销 | 50% |
| L 类（Long）短输入长输出 | 测 TPS 与长尾输出 | 30% |
| R 类（RAG）检索型 | 测检索耗时、召回波动 | 10% |
| T 类（Tool）工具调用型 | 测工具调用链路、重试/熔断 | 10% |

### 2.2 Python 基线脚本：collect + gate 二合一

```python
# 文件名：agent_perf_baseline.py
# 用途：AI Agent 性能与稳定性基线采集 + 门禁
# 运行示例：
#   1) 采集基线：
#      python agent_perf_baseline.py collect --url http://127.0.0.1:8080/agent/run --concurrency 10 --requests 200 --out baseline.json
#   2) 门禁对比：
#      python agent_perf_baseline.py gate --url http://127.0.0.1:8080/agent/run --concurrency 10 --requests 200 --baseline baseline.json --max-regression-pct 15

import argparse
import asyncio
import json
import math
import statistics
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import aiohttp


@dataclass
class OneRun:
    ok: bool
    latency_ms: float
    ttft_ms: Optional[float]
    gen_ms: Optional[float]
    completion_tokens: Optional[int]
    output_chars: Optional[int]
    error: Optional[str]


def percentile(values: List[float], p: float) -> float:
    if not values:
        return float("nan")
    if p <= 0:
        return min(values)
    if p >= 100:
        return max(values)
    xs = sorted(values)
    k = (len(xs) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return xs[int(k)]
    return xs[f] * (c - k) + xs[c] * (k - f)


def summarize(name: str, values: List[float]) -> Dict[str, Any]:
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "avg": statistics.mean(values),
        "p50": percentile(values, 50),
        "p90": percentile(values, 90),
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
        "min": min(values),
        "max": max(values),
        "name": name,
    }


async def run_one(session, url, payload, timeout_s, stream) -> OneRun:
    headers = {"x-request-id": str(uuid.uuid4()), "content-type": "application/json"}
    start = time.perf_counter()
    try:
        t = aiohttp.ClientTimeout(total=timeout_s)
        async with session.post(url, headers=headers, json=payload, timeout=t) as resp:
            if resp.status != 200:
                body = await resp.text()
                return OneRun(ok=False, latency_ms=(time.perf_counter()-start)*1000,
                              ttft_ms=None, gen_ms=None, completion_tokens=None,
                              output_chars=None, error=f"http_{resp.status}: {body[:200]}")
            if stream:
                first_t = None
                chunks = []
                async for chunk in resp.content.iter_chunked(1024):
                    if chunk and first_t is None:
                        first_t = time.perf_counter()
                    chunks.append(chunk)
                end = time.perf_counter()
                ttft_ms = (first_t - start) * 1000 if first_t else None
                gen_ms = (end - first_t) * 1000 if first_t else None
                output_chars = len(b"".join(chunks).decode("utf-8", errors="ignore"))
                return OneRun(ok=True, latency_ms=(end-start)*1000, ttft_ms=ttft_ms,
                              gen_ms=gen_ms, completion_tokens=None, output_chars=output_chars, error=None)
            data = await resp.json(content_type=None)
            end = time.perf_counter()
            ct = data.get("usage", {}).get("completion_tokens") if isinstance(data, dict) else None
            oc = len(data.get("output", "") or data.get("text", "")) if isinstance(data, dict) else None
            return OneRun(ok=True, latency_ms=(end-start)*1000, ttft_ms=None,
                          gen_ms=None, completion_tokens=ct, output_chars=oc, error=None)
    except asyncio.TimeoutError:
        return OneRun(ok=False, latency_ms=(time.perf_counter()-start)*1000,
                      ttft_ms=None, gen_ms=None, completion_tokens=None, output_chars=None, error="timeout")
    except Exception as e:
        return OneRun(ok=False, latency_ms=(time.perf_counter()-start)*1000,
                      ttft_ms=None, gen_ms=None, completion_tokens=None, output_chars=None,
                      error=f"exception: {type(e).__name__}: {e}")


async def run_load(url, concurrency, total_requests, timeout_s, stream, warmup):
    sem = asyncio.Semaphore(concurrency)
    prompts = [
        "你好，简单介绍一下你能做什么？",
        "请用 5 个要点总结一下如何做性能基线测试。",
        "给我一个最小可行的 HTTP API 性能测试用例设计思路。",
        "当系统 P99 延迟突然升高时，你会怎么分层定位？",
    ]
    async with aiohttp.ClientSession() as session:
        runs = []
        async def _one(i):
            async with sem:
                payload = {"input": prompts[i % len(prompts)], "stream": stream}
                r = await run_one(session, url, payload, timeout_s, stream)
                runs.append(r)
        await asyncio.gather(*[asyncio.create_task(_one(i)) for i in range(total_requests + warmup)])
    return runs[:warmup], runs[warmup:]


def compute_metrics(runs):
    ok_runs = [r for r in runs if r.ok]
    fail_runs = [r for r in runs if not r.ok]
    latency_ms = [r.latency_ms for r in ok_runs]
    ttft_ms = [r.ttft_ms for r in ok_runs if r.ttft_ms is not None]
    strict_tps = [r.completion_tokens/(r.gen_ms/1000) for r in ok_runs
                  if r.completion_tokens and r.gen_ms and r.gen_ms > 0]
    approx_tps = [r.output_chars/(r.gen_ms/1000) for r in ok_runs
                  if not r.completion_tokens and r.output_chars and r.gen_ms and r.gen_ms > 0]
    err_buckets = {}
    for r in fail_runs:
        err_buckets[r.error or "unknown"] = err_buckets.get(r.error or "unknown", 0) + 1
    return {
        "total": len(runs), "ok": len(ok_runs), "fail": len(fail_runs),
        "success_rate": len(ok_runs)/len(runs) if runs else 0.0,
        "latency_ms": summarize("latency_ms", latency_ms),
        "ttft_ms": summarize("ttft_ms", ttft_ms) if ttft_ms else {"count": 0},
        "tps_strict": summarize("tps_strict", strict_tps) if strict_tps else {"count": 0},
        "tps_approx_chars_per_s": summarize("tps_approx", approx_tps) if approx_tps else {"count": 0},
        "errors": err_buckets,
    }


def gate_against_baseline(current, baseline, max_regression_pct, min_success_rate):
    cur_sr = float(current.get("success_rate", 0.0))
    if cur_sr < min_success_rate:
        raise SystemExit(f"[GATE FAIL] success_rate={cur_sr:.4f} < {min_success_rate:.4f}")
    for key, label in [("latency_ms", "P99 延迟"), ("ttft_ms", "TTFT P99")]:
        cur_p99 = current.get(key, {}).get("p99")
        base_p99 = baseline.get(key, {}).get("p99")
        if not cur_p99 or not base_p99 or math.isnan(cur_p99) or math.isnan(base_p99):
            print(f"[GATE SKIP] {label}: missing data"); continue
        allowed = base_p99 * (1.0 + max_regression_pct / 100.0)
        if cur_p99 > allowed:
            raise SystemExit(f"[GATE FAIL] {label}: {cur_p99:.1f}ms > {allowed:.1f}ms (base={base_p99:.1f}ms)")
        print(f"[GATE PASS] {label}: {cur_p99:.1f}ms <= {allowed:.1f}ms (base={base_p99:.1f}ms)")


def main():
    p = argparse.ArgumentParser(description="AI Agent 性能与稳定性基线测试")
    sub = p.add_subparsers(dest="cmd", required=True)
    def add_common(sp):
        sp.add_argument("--url", required=True); sp.add_argument("--concurrency", type=int, default=10)
        sp.add_argument("--requests", type=int, default=200); sp.add_argument("--warmup", type=int, default=20)
        sp.add_argument("--timeout", type=float, default=60.0); sp.add_argument("--stream", action="store_true")
    c = sub.add_parser("collect"); add_common(c); c.add_argument("--out", required=True)
    g = sub.add_parser("gate"); add_common(g); g.add_argument("--baseline", required=True)
    g.add_argument("--max-regression-pct", type=float, default=15.0)
    g.add_argument("--min-success-rate", type=float, default=0.99)
    args = p.parse_args()
    warm, meas = asyncio.run(run_load(args.url, args.concurrency, args.requests,
                                       args.timeout, args.stream, args.warmup))
    current = compute_metrics(meas)
    if args.cmd == "collect":
        out = {"meta": {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "url": args.url, "concurrency": args.concurrency,
                        "requests": args.requests, "stream": args.stream}, **current}
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"[OK] Baseline written to: {args.out}")
    elif args.cmd == "gate":
        with open(args.baseline, "r", encoding="utf-8") as f:
            baseline = json.load(f)
        gate_against_baseline(current, baseline, args.max_regression_pct, args.min_success_rate)
        print("[OK] Gate passed")

if __name__ == "__main__":
    main()
```

### 2.3 稳定性测试升级（Soak / Long Run）

两点升级方向：
1. **时间维度**：不是只跑 200 请求，而是跑 30min / 2h
2. **观测维度**：每 1 分钟输出滚动窗口统计（最近 60s 的 P99、成功率）+ K8s 指标（pod 重启、OOMKill、CPU/内存/goroutine）

> 稳定性问题往往不在"第一分钟"，而在"第 40 分钟"。

### 2.4 Go + Ginkgo 工程化落地示例

```go
// 文件名：perf_baseline_test.go
// 运行：go test -run TestPerfBaseline -v
package perf

import (
    "bytes"
    "context"
    "encoding/json"
    "io"
    "net/http"
    "sort"
    "sync"
    "testing"
    "time"
)

type reqBody struct {
    Input  string `json:"input"`
    Stream bool   `json:"stream"`
}

func pctl(xs []float64, p float64) float64 {
    if len(xs) == 0 { return 0 }
    sort.Float64s(xs)
    idx := int(float64(len(xs)-1) * p)
    if idx < 0 { idx = 0 }
    if idx >= len(xs) { idx = len(xs) - 1 }
    return xs[idx]
}

func TestPerfBaseline(t *testing.T) {
    url := "http://127.0.0.1:8080/agent/run" // TODO: 替换为预发地址
    concurrency := 10
    total := 200
    timeout := 30 * time.Second

    sem := make(chan struct{}, concurrency)
    var wg sync.WaitGroup
    var mu sync.Mutex
    var results []struct{ ok bool; latencyMs float64 }
    client := &http.Client{Timeout: timeout}

    for i := 0; i < total; i++ {
        wg.Add(1)
        sem <- struct{}{}
        go func(i int) {
            defer wg.Done()
            defer func() { <-sem }()
            bs, _ := json.Marshal(reqBody{Input: "你好，做一次性能基线测试", Stream: false})
            ctx, cancel := context.WithTimeout(context.Background(), timeout)
            defer cancel()
            start := time.Now()
            req, _ := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(bs))
            req.Header.Set("Content-Type", "application/json")
            resp, err := client.Do(req)
            latency := float64(time.Since(start).Milliseconds())
            ok := err == nil && resp.StatusCode == 200
            if resp != nil { io.ReadAll(resp.Body); resp.Body.Close() }
            mu.Lock()
            results = append(results, struct{ ok bool; latencyMs float64 }{ok, latency})
            mu.Unlock()
        }(i)
    }
    wg.Wait()

    okCnt := 0
    var lat []float64
    for _, r := range results {
        if r.ok { okCnt++; lat = append(lat, r.latencyMs) }
    }
    successRate := float64(okCnt) / float64(total)
    if successRate < 0.99 { t.Fatalf("successRate too low: %.4f", successRate) }
    p99 := pctl(lat, 0.99)
    t.Logf("successRate=%.4f, p99=%.1fms", successRate, p99)
    // 门禁阈值：示例用固定值；推荐从 baseline.json 读取并用相对阈值比较
    if p99 > 3000 { t.Fatalf("p99 too high: %.1fms", p99) }
}
```

### 2.5 最容易踩的坑

| 坑 | 规避方式 |
|---|---|
| 只看平均值，不看 P99 | 长尾问题必须用分位数才能捕捉 |
| 未做 warm-up 导致基线漂移 | 严格区分 warm-up 阶段与测量阶段 |
| 输入分布不稳定导致"假回归" | 固定用例集与权重 |
| 把模型波动当成产品回归 | 记录模型版本、路由策略、并发资源 |
| 只测 E2E 不分层 | E2E 告诉你"慢了"，分层告诉你"慢在哪" |

---

## 3. 课后思考

1. **如果 TTFT P99 突然变差，但 TTLM 基本不变，你会优先怀疑链路的哪个阶段？你会设计哪些分层指标来验证？**
2. **你会如何定义"成功率"？如果 Agent 出现工具调用失败但最终 fallback 成功，这算成功还是失败？你的定义对基线门禁有什么影响？**
3. **在 CI 门禁里，你更倾向于使用"绝对阈值"（如 P99 < 3s）还是"相对阈值"（如不超过 baseline 的 1.15 倍）？为什么？在什么情况下两者需要结合？**

---

## 4. 今日小结

> **AI Agent 的性能与稳定性基线，本质是把"动态工作流 + 非确定性推理"约束成可重复、可统计、可对比、可门禁的工程体系。**
