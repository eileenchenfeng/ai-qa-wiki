---
title: "每日 AI 学习笔记｜Day 67：AI Agent 混沌工程（ChaosMesh 与故障注入实战）"
date: 2026-06-21
authors: [xiaoai]
tags: [learning-notes, AI, QA, chaos-engineering, chaosmesh, fault-injection, agent, kubernetes]
---

## 核心总结

AI Agent 系统天然是一个高度依赖外部服务的分布式系统：LLM 网关、向量库、Tool 后端、消息队列、对象存储……任何一个抖一抖，Agent 的"用户体验"就会瞬间崩塌——要么变慢、要么幻觉、要么死循环、要么把半成品答案吐给用户。**混沌工程的价值就是：在生产出事之前，主动把故障"打"进来，验证系统是否还能优雅降级**。本篇用 ChaosMesh 作为主力武器，给出一套针对 Agent 场景的故障注入剧本：网络延时/丢包打 LLM 网关、Pod kill 打 tool 后端、IO 故障打向量库、DNS 故障打外部依赖、再叠加 Stress 模拟资源紧张。配套给出 Golang Ginkgo 的"实验编排 + SLO 断言"框架，以及 Python Playwright 的端到端用户体验校验。重点：**混沌实验不是"搞破坏"，而是带假设、带 SLO、带回滚的科学实验**。

{/* truncate */}

## 一、核心理论

### 1.1 为什么 AI Agent 比传统服务更需要混沌工程

| 维度 | 传统微服务 | AI Agent |
|---|---|---|
| 依赖深度 | 2-3 层调用链 | LLM + 向量库 + N 个 tool + 子 Agent，常 5-10 层 |
| 失败模式 | HTTP 500/超时 | 还要叠加幻觉、空答、循环、token 爆炸 |
| 重试代价 | 几乎免费 | 每次重试 = 真金白银的 token |
| 用户感知 | 报错页 | "答非所问" 比报错更难发现 |

结论：Agent 系统的故障不是非黑即白，**"灰色失败"才是杀手**——必须靠主动注入才能暴露。

### 1.2 混沌工程的 5 条原则（Netflix 经典 → Agent 改造版）

1. **建立稳态假设**：定义 Agent 的 SLO，如"P95 端到端 < 8s、任务完成率 > 95%、幻觉率 < 2%"。
2. **多样化真实事件**：网络抖动、Pod 重启、磁盘满、LLM 429、tool 返回脏数据。
3. **生产环境（或仿真生产）运行**：在影子流量或灰度集群上跑，不在 dev 上"自欺欺人"。
4. **持续自动化**：实验进 CI/CD，而不是手工演练一次就归档。
5. **最小爆炸半径**：用 namespace/label selector 圈定范围，配置自动 abort。

### 1.3 ChaosMesh 故障类型速查（针对 Agent 常用）

- **NetworkChaos**：delay / loss / corrupt / partition / bandwidth —— 打 LLM 网关、Tool HTTP。
- **PodChaos**：pod-kill / pod-failure / container-kill —— 打 Agent worker、Tool 后端。
- **StressChaos**：CPU / Memory —— 打模型推理 Pod、向量库节点。
- **IOChaos**：latency / fault / attrOverride —— 打 PVC（向量库、知识库索引）。
- **DNSChaos**：random / error —— 打外部 API 依赖（搜索、第三方 SaaS）。
- **HTTPChaos**：abort / delay / replace —— 直接劫持 LLM 请求/响应，模拟 429、幻觉响应、超长响应。

### 1.4 Agent 场景的"假设矩阵"

| 故障 | 假设（应有的优雅行为） | SLO 容忍度 |
|---|---|---|
| LLM 网关 +3s 延时 | 触发 backup model 路由 | P95 退化 ≤ 1.5x |
| 向量库 Pod kill | 重试 + 切只读副本 | 错误率 < 1% |
| Tool 返回 500 | 不重试超过 3 次，最终向用户致歉 | 无死循环、无幻觉编造 |
| DNS 解析失败 | 命中本地缓存，10s 内恢复 | 完成率 > 90% |
| 内存压力 80% | OOMKill 前主动拒绝新会话 | 无 cascading failure |

## 二、工程实践

### 2.1 环境准备：在 K8s 集群安装 ChaosMesh

```bash
# 单命令安装（开发集群）
curl -sSL https://mirrors.chaos-mesh.org/v2.6.3/install.sh | bash -s -- \
  --local kind --name chaos-mesh

# 验证
kubectl get pods -n chaos-mesh
kubectl port-forward -n chaos-mesh svc/chaos-dashboard 2333:2333
```

### 2.2 实验一：给 LLM 网关注入 2s 网络延时

```yaml
# experiments/llm-gateway-delay.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: llm-gateway-delay
  namespace: agent-staging
spec:
  action: delay
  mode: all
  selector:
    namespaces: [agent-staging]
    labelSelectors:
      app: llm-gateway
  delay:
    latency: "2000ms"
    correlation: "50"
    jitter: "200ms"
  duration: "5m"
  # 关键：最小爆炸半径——只打 staging，且 5 分钟自动恢复
```

### 2.3 实验二：HTTPChaos 直接伪造 LLM 429 响应

模拟 LLM 厂商限流是 Agent 测试里最高频的场景：

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: HTTPChaos
metadata:
  name: llm-rate-limit-429
spec:
  mode: all
  selector:
    labelSelectors:
      app: agent-worker
  target: Request
  port: 443
  path: "/v1/chat/completions"
  abort: false
  replace:
    code: 429
    body: '{"error":{"type":"rate_limit","message":"Too Many Requests"}}'
  duration: "3m"
```

### 2.4 Ginkgo：把混沌实验封装成 E2E 用例

我们要的不是"手动 kubectl apply 看一眼"，而是**实验进自动化用例**，让 SLO 失败时直接挂红：

```go
// tests/chaos/agent_resilience_test.go
package chaos_test

import (
    "context"
    "time"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
    "sigs.k8s.io/controller-runtime/pkg/client"
    chaosv1 "github.com/chaos-mesh/chaos-mesh/api/v1alpha1"
)

var _ = Describe("Agent 混沌韧性 E2E", Ordered, func() {
    var k8s client.Client
    var agent *AgentClient // 内部封装：调 /api/chat、记录 trace

    BeforeAll(func() {
        k8s = newK8sClient()
        agent = NewAgentClient("https://agent-staging.internal/api")
    })

    Context("当 LLM 网关延时 2s 时", func() {
        var chaos *chaosv1.NetworkChaos

        BeforeEach(func() {
            chaos = buildLLMDelayChaos("2000ms", 5*time.Minute)
            Expect(k8s.Create(context.TODO(), chaos)).To(Succeed())
            // 等待实验真正注入（ChaosMesh 异步）
            Eventually(func() string {
                _ = k8s.Get(context.TODO(), client.ObjectKeyFromObject(chaos), chaos)
                return string(chaos.Status.Experiment.DesiredPhase)
            }, 30*time.Second, 2*time.Second).Should(Equal("Run"))
        })

        AfterEach(func() {
            _ = k8s.Delete(context.TODO(), chaos)
        })

        It("应触发 backup model 路由且 P95 不退化超过 1.5x", func() {
            results := agent.RunConcurrent(50, "请帮我总结上周项目进展")

            // 中间状态断言：trace 中应能看到 backup model
            Expect(results.TraceAttr("gen_ai.request.model")).
                To(ContainElement(ContainSubstring("backup")))

            // 最终 SLO 断言
            Expect(results.P95Latency()).To(BeNumerically("<", 12*time.Second)) // baseline 8s * 1.5
            Expect(results.SuccessRate()).To(BeNumerically(">=", 0.95))
            Expect(results.HallucinationRate()).To(BeNumerically("<", 0.02))
        })
    })

    Context("当向量库 Pod 被 kill 时", func() {
        It("应在 30s 内自愈，且无用户可见错误", func() {
            chaos := buildPodKillChaos("vector-db", 1)
            Expect(k8s.Create(context.TODO(), chaos)).To(Succeed())
            DeferCleanup(func() { _ = k8s.Delete(context.TODO(), chaos) })

            // 持续流量 60s
            results := agent.RunSteady(60*time.Second, 5 /* QPS */)
            Expect(results.UserVisibleErrors()).To(Equal(0))
            Expect(results.RecoveryTime()).To(BeNumerically("<", 30*time.Second))
        })
    })
})
```

### 2.5 Playwright：端到端校验"用户视角"是否优雅

底层指标 OK 不等于用户体验 OK——必须再加一层端到端：

```python
# tests/e2e/test_chaos_ux.py
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.chaos("llm-gateway-delay")
def test_user_sees_typing_indicator_during_llm_delay(page: Page, chaos_runner):
    """LLM 延时时，用户应看到打字指示器而不是空白卡死。"""
    with chaos_runner.inject("llm-gateway-delay"):
        page.goto("https://agent-staging.internal/chat")
        page.fill('[data-testid="chat-input"]', "帮我写一份周报")
        page.click('[data-testid="send-btn"]')

        # 中间状态：必须出现打字指示器（说明前端没卡死）
        expect(page.locator('[data-testid="typing-indicator"]')).to_be_visible(timeout=2000)

        # 最终状态：12s 内出现回答（backup model 兜底）
        expect(page.locator('[data-testid="assistant-message"]').last) \
            .to_be_visible(timeout=12_000)

        # ✅ 不应出现错误 toast
        expect(page.locator('[data-testid="error-toast"]')).not_to_be_visible()


@pytest.mark.chaos("llm-rate-limit-429")
def test_rate_limit_shows_friendly_retry_hint(page: Page, chaos_runner):
    """429 场景下，应给用户友好提示而不是技术错误码。"""
    with chaos_runner.inject("llm-rate-limit-429"):
        page.goto("https://agent-staging.internal/chat")
        page.fill('[data-testid="chat-input"]', "你好")
        page.click('[data-testid="send-btn"]')

        msg = page.locator('[data-testid="assistant-message"]').last
        expect(msg).to_contain_text("当前访问量较大", timeout=10_000)
        # ✅ 绝不应把 "429" / "rate_limit" 暴露给用户
        expect(msg).not_to_contain_text("429")
        expect(msg).not_to_contain_text("rate_limit")
```

### 2.6 自动化编排：让混沌进 CI

```yaml
# .github/workflows/chaos-nightly.yml
name: Chaos Nightly
on:
  schedule: [{cron: '0 18 * * *'}]   # 每天 18:00 跑
jobs:
  chaos-suite:
    runs-on: [self-hosted, k8s-staging]
    steps:
      - uses: actions/checkout@v4
      - name: Run Ginkgo chaos suite
        run: ginkgo -v --label-filter="chaos" ./tests/chaos/...
      - name: Run Playwright UX checks
        run: pytest tests/e2e -m chaos --html=report.html
      - name: Auto-abort all chaos on failure
        if: failure()
        run: kubectl delete networkchaos,httpchaos,podchaos --all -n agent-staging
```

### 2.7 最小爆炸半径与回滚保护（划重点）

- **强制 duration**：所有实验必须带 `duration`，禁止无限期实验。
- **dry-run gate**：CI 里先 `kubectl apply --dry-run=server` 校验 YAML。
- **kill switch**：准备一个 `scripts/abort-all-chaos.sh`，CI failure 步骤里强制调用。
- **流量隔离**：用 namespace + label selector 锁死作用范围，绝对不允许 `mode: all` 配合宽松 selector 打到生产 namespace。

## 三、课后思考题

1. ChaosMesh 的 `HTTPChaos` 可以伪造 LLM 响应内容——如何用它来构造"幻觉回归测试"？如何避免被业务方误用成"造假流量"？
2. 当一个 Agent 同时依赖 5 个 tool，混沌实验该按"单点故障"逐个打，还是按"组合故障"一起打？组合爆炸怎么收敛？
3. SLO 中"幻觉率 < 2%"在混沌实验里如何度量？需要 LLM-as-Judge 还是规则匹配？两者各有什么坑？
4. 混沌实验跑出来的 trace 数据，怎么反哺给 Day 65 的压测和 Day 66 的可观测性体系，形成"故障数据飞轮"？
5. 在多租户 Agent 平台上做混沌，如何确保**只影响自己的租户**而不殃及他人？label selector 够用吗？

## 四、今日小结

- 混沌工程对 AI Agent 是"刚需"，因为它的失败模式比传统服务更"灰"——延时、429、幻觉、死循环往往叠加发生。
- ChaosMesh 提供了从网络/Pod/IO/DNS/HTTP 全维度的故障原语，**HTTPChaos 尤其适合 LLM 场景**（直接劫持请求/响应）。
- 真正可落地的混沌实验必须满足：**带假设、带 SLO、带自动回滚、进 CI**——单纯 kubectl apply 不算混沌工程，只算"事故演练"。
- Ginkgo 负责"底层 SLO 断言"，Playwright 负责"用户视角 UX 断言"，两层缺一不可。
- 明日预告：**Day 68 — AI 安全测试（Prompt Injection / 越权 / 数据泄露）**，把"打自己"升级到"防别人打"。
