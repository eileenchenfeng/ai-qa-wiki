---
title: "每日 AI 学习笔记｜Day 35：AI Agent 测试数据管理与环境治理"
date: 2026-05-20
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, test-data-management, environment-governance, SDET, Ginkgo, Playwright, K8s, fixture, ephemeral-env]
---
# 每日 AI 学习笔记｜Day 35：AI Agent 测试数据管理与环境治理

AI Agent 系统的测试数据管理远比传统微服务复杂——多轮对话的状态依赖、工具调用的副作用链、Embedding 向量的版本漂移、以及 Prompt 中不可避免的 PII 泄露风险，都要求 QA 团队建立从数据生成、注入、隔离、清理到审计的全生命周期治理体系。本篇围绕 Ginkgo TestDataFactory、Playwright Fixture Manager、K8s 短命名空间供给器、数据脱敏工具和 CI 数据播种流水线五大工程实践，给出可直接落地的代码方案，帮助 SDET 在日常工作中实现"测试数据即代码、环境即声明、隔离即默认"的工程目标。

{/* truncate */}

## 0. 今日目标

1. 理解 AI Agent 系统在测试数据管理上的独特挑战：非确定性输出、有状态会话、工具副作用、向量数据版本管理。
2. 掌握测试数据全生命周期模型：Generation → Injection → Isolation → Cleanup → Audit。
3. 能够使用 Ginkgo + client-go 实现 K8s 短命名空间的自动创建与 TTL 清理。
4. 能够使用 Playwright + pytest fixtures 管理 Agent UI 的测试会话数据。
5. 设计 CI 集成的 Golden Dataset 播种与新鲜度校验流水线。

## 1. 核心理论

### 1.1 为什么 AI Agent 让测试数据管理更难

| 挑战维度 | 传统微服务 | AI Agent 系统 |
|---------|-----------|--------------|
| 输出确定性 | 给定输入 → 固定输出 | 同一 Prompt 可能产生不同回答 |
| 状态管理 | 无状态或简单 Session | 多轮对话上下文窗口、Memory Store |
| 副作用 | 数据库写入、MQ 发送 | 工具调用链（搜索→计算→写文件→发邮件） |
| 数据维度 | 结构化 JSON/SQL | Prompt 文本 + Embedding 向量 + Function Schema |
| 隐私风险 | 字段级脱敏 | 自然语言中散布 PII，难以正则匹配 |

**核心矛盾**：Agent 测试需要"真实到足以触发正确行为"的数据，但又必须"隔离到不会污染生产环境或泄露隐私"。

### 1.2 测试数据生命周期

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│Generation│───▶│Injection │───▶│Isolation │───▶│ Cleanup  │───▶│  Audit   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
 • 合成对话       • Fixture 注入    • 命名空间隔离    • TTL 自动回收    • 血缘追踪
 • 黄金数据集     • API Seeding     • 网络策略        • AfterSuite      • 新鲜度校验
 • 向量快照       • DB Migration    • 数据面隔离      • Finalizer       • 合规审计
```

- **Generation**：使用 LLM 合成对话、通过 Schema 生成结构化 Fixture、从生产日志脱敏后提取。
- **Injection**：通过 API 直接写入 Agent Memory Store，或通过 DB Migration 预置对话历史。
- **Isolation**：每个测试套件独占 K8s Namespace，网络策略禁止跨命名空间访问。
- **Cleanup**：TTL Controller 自动删除过期命名空间；AfterSuite Hook 确保测试结束后资源释放。
- **Audit**：记录每条测试数据的来源、使用场景、脱敏状态，支持合规检查。

### 1.3 环境治理：共享 vs 短生命周期

共享环境的痛点：测试之间数据互相污染、资源争抢导致 Flaky Test、清理不彻底引发"幽灵失败"。

**短生命周期（Ephemeral）环境方案核心设计**：

- 每个测试套件获得独立 K8s Namespace，带 TTL 注解的自动回收
- **控制面**（Agent Orchestrator、LLM Gateway）共享部署，通过 Header 路由到测试租户
- **数据面**（Memory Store、Vector DB、Tool Sandbox）每个测试套件独立实例

### 1.4 数据脱敏与匿名化

AI 测试数据的脱敏难点在于 PII 嵌入自然语言。脱敏策略分四层：

| 层级 | 策略 | 适用场景 |
|-----|------|---------|
| L1 | 正则替换（手机号、身份证、邮箱） | 结构化字段 |
| L2 | NER 模型（人名、地址、组织） | 自然语言文本 |
| L3 | 差分隐私（Embedding 向量扰动） | 向量数据库测试 |
| L4 | 合成替代（LLM 生成等价虚构对话） | 端到端场景 |

## 2. 工程实践

### 2.1 Ginkgo 测试数据工厂（Go）

```go
package testdata

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

// AgentSession represents a test session for an AI Agent.
type AgentSession struct {
	ID             string
	Namespace      string
	ConversationID string
	Messages       []ConversationMessage
	ToolCalls      []ToolCallFixture
	CreatedAt      time.Time
}

type ConversationMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
	ToolID  string `json:"tool_id,omitempty"`
}

type ToolCallFixture struct {
	Name       string            `json:"name"`
	Parameters map[string]string `json:"parameters"`
	Response   string            `json:"response"`
}

// TestDataFactory manages test data lifecycle for Agent tests.
type TestDataFactory struct {
	clientset  kubernetes.Interface
	namespace  string
	sessions   []*AgentSession
	cleanupFns []func() error
}

// Builder provides a fluent API to construct TestDataFactory.
type Builder struct {
	namespacePrefix string
	ttlSeconds      int
	cpuLimit        string
	memLimit        string
	labels          map[string]string
}

func NewBuilder() *Builder {
	return &Builder{
		namespacePrefix: "agent-test",
		ttlSeconds:      3600,
		cpuLimit:        "2",
		memLimit:        "4Gi",
		labels:          map[string]string{"managed-by": "test-data-factory"},
	}
}

func (b *Builder) WithPrefix(p string) *Builder   { b.namespacePrefix = p; return b }
func (b *Builder) WithTTL(s int) *Builder          { b.ttlSeconds = s; return b }
func (b *Builder) WithQuota(cpu, mem string) *Builder { b.cpuLimit = cpu; b.memLimit = mem; return b }

// Build creates the factory with an ephemeral K8s namespace.
func (b *Builder) Build(ctx context.Context) (*TestDataFactory, error) {
	config, err := rest.InClusterConfig()
	if err != nil {
		return nil, fmt.Errorf("get in-cluster config: %w", err)
	}
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("create clientset: %w", err)
	}

	nsName := fmt.Sprintf("%s-%s", b.namespacePrefix, uuid.New().String()[:8])
	ns := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name:   nsName,
			Labels: b.labels,
			Annotations: map[string]string{
				"ttl-seconds": fmt.Sprintf("%d", b.ttlSeconds),
				"created-at":  time.Now().UTC().Format(time.RFC3339),
			},
		},
	}
	if _, err = clientset.CoreV1().Namespaces().Create(ctx, ns, metav1.CreateOptions{}); err != nil {
		return nil, fmt.Errorf("create namespace %s: %w", nsName, err)
	}

	// Apply resource quota
	quota := &corev1.ResourceQuota{
		ObjectMeta: metav1.ObjectMeta{Name: "test-quota", Namespace: nsName},
		Spec: corev1.ResourceQuotaSpec{
			Hard: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse(b.cpuLimit),
				corev1.ResourceMemory: resource.MustParse(b.memLimit),
				corev1.ResourcePods:   resource.MustParse("20"),
			},
		},
	}
	if _, err = clientset.CoreV1().ResourceQuotas(nsName).Create(ctx, quota, metav1.CreateOptions{}); err != nil {
		return nil, fmt.Errorf("create resource quota: %w", err)
	}

	return &TestDataFactory{clientset: clientset, namespace: nsName}, nil
}

func (f *TestDataFactory) CreateSession(msgs []ConversationMessage, tools []ToolCallFixture) *AgentSession {
	s := &AgentSession{
		ID: uuid.New().String(), Namespace: f.namespace,
		ConversationID: fmt.Sprintf("conv-%s", uuid.New().String()[:8]),
		Messages: msgs, ToolCalls: tools, CreatedAt: time.Now(),
	}
	f.sessions = append(f.sessions, s)
	return s
}

func (f *TestDataFactory) RegisterCleanup(fn func() error) { f.cleanupFns = append(f.cleanupFns, fn) }

func (f *TestDataFactory) Cleanup(ctx context.Context) error {
	for _, fn := range f.cleanupFns {
		if err := fn(); err != nil {
			GinkgoWriter.Printf("WARNING: cleanup failed: %v\n", err)
		}
	}
	return f.clientset.CoreV1().Namespaces().Delete(ctx, f.namespace, metav1.DeleteOptions{})
}

// --- Ginkgo Suite Example ---
var _ = Describe("Agent Conversation Flow", func() {
	var factory *TestDataFactory
	ctx := context.Background()

	BeforeEach(func() {
		var err error
		factory, err = NewBuilder().WithPrefix("conv-flow").WithTTL(1800).WithQuota("2", "4Gi").Build(ctx)
		Expect(err).NotTo(HaveOccurred())
	})
	AfterEach(func() { Expect(factory.Cleanup(ctx)).To(Succeed()) })

	It("should maintain context across multi-turn conversation", func() {
		session := factory.CreateSession(
			[]ConversationMessage{
				{Role: "system", Content: "You are a helpful travel assistant."},
				{Role: "user", Content: "我想去东京旅行，帮我规划三天行程"},
				{Role: "assistant", Content: "好的，我来帮您规划东京三天行程..."},
				{Role: "user", Content: "第二天能加上浅草寺吗？"},
			},
			[]ToolCallFixture{{
				Name: "search_attractions", Parameters: map[string]string{"city": "tokyo"},
				Response: `{"results": [{"name": "浅草寺", "rating": 4.5}]}`,
			}},
		)
		Expect(session.Messages).To(HaveLen(4))
		Expect(session.ToolCalls).To(HaveLen(1))
	})
})
```

### 2.2 Python Playwright Fixture Manager

```python
"""Agent UI test data & browser state management with Playwright + pytest."""
import json
import uuid
from dataclasses import dataclass, field
from typing import Generator

import pytest
from playwright.sync_api import Page, BrowserContext, Route


@dataclass
class ConversationFixture:
    conversation_id: str = field(default_factory=lambda: f"conv-{uuid.uuid4().hex[:8]}")
    messages: list = field(default_factory=list)

    def add_user(self, content: str) -> "ConversationFixture":
        self.messages.append({"role": "user", "content": content})
        return self

    def add_assistant(self, content: str, tool_calls: list = None) -> "ConversationFixture":
        msg = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)
        return self

    def add_system(self, content: str) -> "ConversationFixture":
        self.messages.insert(0, {"role": "system", "content": content})
        return self


class AgentAPIMocker:
    """Intercepts and mocks Agent backend API responses."""
    def __init__(self, page: Page):
        self.page = page
        self._routes: list[str] = []

    def mock_history(self, fixture: ConversationFixture) -> None:
        def handler(route: Route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "conversation_id": fixture.conversation_id,
                "messages": fixture.messages,
            }))
        pattern = f"**/api/conversations/{fixture.conversation_id}/messages"
        self.page.route(pattern, handler)
        self._routes.append(pattern)

    def mock_chat_response(self, content: str, tool_calls: list = None) -> None:
        def handler(route: Route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({
                "content": content, "tool_calls": tool_calls or [], "finish_reason": "stop",
            }))
        self.page.route("**/api/chat/completions", handler)
        self._routes.append("**/api/chat/completions")

    def teardown(self) -> None:
        for p in self._routes:
            self.page.unroute(p)
        self._routes.clear()


@pytest.fixture
def conversation_fixture() -> ConversationFixture:
    f = ConversationFixture()
    f.add_system("你是一个智能客服助手，负责处理退款和订单查询。")
    f.add_user("我要查一下订单 ORD-20260515-001 的状态")
    f.add_assistant("好的，我来帮您查询。", tool_calls=[{"name": "query_order", "params": {"order_id": "ORD-20260515-001"}}])
    f.add_user("如果已经发货了，帮我修改收货地址")
    return f


@pytest.fixture
def agent_page(context: BrowserContext, conversation_fixture: ConversationFixture) -> Generator[Page, None, None]:
    page = context.new_page()
    mocker = AgentAPIMocker(page)
    mocker.mock_history(conversation_fixture)
    mocker.mock_chat_response("订单已发货，当前在途中。需要修改收货地址吗？")

    page.context.add_cookies([{"name": "auth_token", "value": "test-jwt", "domain": "localhost", "path": "/"}])
    page.goto(f"http://localhost:3000/chat/{conversation_fixture.conversation_id}")
    page.wait_for_selector("[data-testid='chat-container']", timeout=10000)

    yield page
    mocker.teardown()
    page.close()


class TestAgentConversationUI:
    def test_displays_history(self, agent_page: Page):
        messages = agent_page.locator("[data-testid='message-bubble']")
        assert messages.count() >= 3
        first_user = agent_page.locator("[data-testid='message-bubble'][data-role='user']").first
        assert "ORD-20260515-001" in first_user.text_content()

    def test_send_new_message(self, agent_page: Page):
        agent_page.locator("[data-testid='chat-input']").fill("把地址改成上海市浦东新区世纪大道100号")
        agent_page.locator("[data-testid='chat-input']").press("Enter")
        resp = agent_page.locator("[data-testid='message-bubble'][data-role='assistant']").last
        resp.wait_for(timeout=5000)
        assert "已发货" in resp.text_content()
```

### 2.3 K8s 短生命周期环境供给器

```go
package ephemeral

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	corev1 "k8s.io/api/core/v1"
	networkingv1 "k8s.io/api/networking/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

type EnvConfig struct {
	Prefix       string
	TTL          time.Duration
	CPULimit     string
	MemoryLimit  string
	MaxPods      int
	AllowedCIDRs []string
}

func DefaultConfig() *EnvConfig {
	return &EnvConfig{
		Prefix: "agent-ephemeral", TTL: 30 * time.Minute,
		CPULimit: "4", MemoryLimit: "8Gi", MaxPods: 30,
		AllowedCIDRs: []string{"10.0.0.0/8"},
	}
}

type EphemeralEnv struct {
	Namespace string
	clientset kubernetes.Interface
	createdAt time.Time
}

type Provisioner struct {
	clientset kubernetes.Interface
	envs      []*EphemeralEnv
}

func NewProvisioner() (*Provisioner, error) {
	cfg, err := rest.InClusterConfig()
	if err != nil {
		return nil, err
	}
	cs, err := kubernetes.NewForConfig(cfg)
	if err != nil {
		return nil, err
	}
	return &Provisioner{clientset: cs}, nil
}

func (p *Provisioner) Provision(ctx context.Context, cfg *EnvConfig) (*EphemeralEnv, error) {
	if cfg == nil {
		cfg = DefaultConfig()
	}
	nsName := fmt.Sprintf("%s-%s", cfg.Prefix, uuid.New().String()[:8])
	now := time.Now().UTC()

	// Create namespace with TTL annotation
	ns := &corev1.Namespace{ObjectMeta: metav1.ObjectMeta{
		Name:   nsName,
		Labels: map[string]string{"managed-by": "ephemeral-provisioner", "purpose": "agent-testing"},
		Annotations: map[string]string{
			"ephemeral.test/expires-at": now.Add(cfg.TTL).Format(time.RFC3339),
		},
	}}
	if _, err := p.clientset.CoreV1().Namespaces().Create(ctx, ns, metav1.CreateOptions{}); err != nil {
		return nil, fmt.Errorf("create namespace: %w", err)
	}

	// Resource quota
	quota := &corev1.ResourceQuota{
		ObjectMeta: metav1.ObjectMeta{Name: "ephemeral-quota", Namespace: nsName},
		Spec: corev1.ResourceQuotaSpec{Hard: corev1.ResourceList{
			corev1.ResourceCPU:    resource.MustParse(cfg.CPULimit),
			corev1.ResourceMemory: resource.MustParse(cfg.MemoryLimit),
			corev1.ResourcePods:   resource.MustParse(fmt.Sprintf("%d", cfg.MaxPods)),
		}},
	}
	if _, err := p.clientset.CoreV1().ResourceQuotas(nsName).Create(ctx, quota, metav1.CreateOptions{}); err != nil {
		return nil, fmt.Errorf("create quota: %w", err)
	}

	// Network policy: deny external, allow internal + DNS
	if err := applyNetworkPolicies(ctx, p.clientset, nsName, cfg.AllowedCIDRs); err != nil {
		return nil, err
	}

	env := &EphemeralEnv{Namespace: nsName, clientset: p.clientset, createdAt: now}
	p.envs = append(p.envs, env)
	return env, nil
}

func applyNetworkPolicies(ctx context.Context, cs kubernetes.Interface, ns string, cidrs []string) error {
	// Deny all egress
	denyAll := &networkingv1.NetworkPolicy{
		ObjectMeta: metav1.ObjectMeta{Name: "deny-external", Namespace: ns},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: metav1.LabelSelector{},
			PolicyTypes: []networkingv1.PolicyType{networkingv1.PolicyTypeEgress},
			Egress:      []networkingv1.NetworkPolicyEgressRule{},
		},
	}
	if _, err := cs.NetworkingV1().NetworkPolicies(ns).Create(ctx, denyAll, metav1.CreateOptions{}); err != nil {
		return fmt.Errorf("deny-all policy: %w", err)
	}

	// Allow internal CIDRs + DNS
	dnsPort := intstr.FromInt(53)
	udp := corev1.ProtocolUDP
	var rules []networkingv1.NetworkPolicyEgressRule
	for _, cidr := range cidrs {
		rules = append(rules, networkingv1.NetworkPolicyEgressRule{
			To: []networkingv1.NetworkPolicyPeer{{IPBlock: &networkingv1.IPBlock{CIDR: cidr}}},
		})
	}
	rules = append(rules, networkingv1.NetworkPolicyEgressRule{
		Ports: []networkingv1.NetworkPolicyPort{{Port: &dnsPort, Protocol: &udp}},
	})

	allow := &networkingv1.NetworkPolicy{
		ObjectMeta: metav1.ObjectMeta{Name: "allow-internal", Namespace: ns},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: metav1.LabelSelector{},
			PolicyTypes: []networkingv1.PolicyType{networkingv1.PolicyTypeEgress},
			Egress:      rules,
		},
	}
	_, err := cs.NetworkingV1().NetworkPolicies(ns).Create(ctx, allow, metav1.CreateOptions{})
	return err
}

func (env *EphemeralEnv) Destroy(ctx context.Context) error {
	return env.clientset.CoreV1().Namespaces().Delete(ctx, env.Namespace, metav1.DeleteOptions{})
}

// CleanExpired removes namespaces past their TTL — designed for CronJob usage.
func (p *Provisioner) CleanExpired(ctx context.Context) (int, error) {
	nsList, err := p.clientset.CoreV1().Namespaces().List(ctx, metav1.ListOptions{
		LabelSelector: "managed-by=ephemeral-provisioner",
	})
	if err != nil {
		return 0, err
	}
	cleaned := 0
	for _, ns := range nsList.Items {
		expStr := ns.Annotations["ephemeral.test/expires-at"]
		if expStr == "" {
			continue
		}
		expiry, _ := time.Parse(time.RFC3339, expStr)
		if time.Now().UTC().After(expiry) {
			_ = p.clientset.CoreV1().Namespaces().Delete(ctx, ns.Name, metav1.DeleteOptions{})
			cleaned++
		}
	}
	return cleaned, nil
}
```

### 2.4 测试数据脱敏工具

```go
package anonymizer

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"regexp"
	"strings"
	"sync"
)

type EntityType string

const (
	EntityPhone  EntityType = "PHONE"
	EntityIDCard EntityType = "ID_CARD"
	EntityEmail  EntityType = "EMAIL"
	EntityName   EntityType = "NAME"
)

type AnonymizeResult struct {
	Original   string            `json:"original"`
	Anonymized string            `json:"anonymized"`
	Counts     map[EntityType]int `json:"counts"`
}

type Anonymizer struct {
	mu       sync.Mutex
	patterns map[EntityType]*regexp.Regexp
	counters map[EntityType]int
	mapping  map[string]string // Ensures consistent replacement
	names    []string
}

func New() *Anonymizer {
	return &Anonymizer{
		patterns: map[EntityType]*regexp.Regexp{
			EntityPhone:  regexp.MustCompile(`1[3-9]\d{9}`),
			EntityIDCard: regexp.MustCompile(`[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]`),
			EntityEmail:  regexp.MustCompile(`[\w.+-]+@[\w-]+\.[\w.-]+`),
		},
		counters: make(map[EntityType]int),
		mapping:  make(map[string]string),
	}
}

func (a *Anonymizer) WithNames(names []string) *Anonymizer {
	a.names = names
	return a
}

func (a *Anonymizer) placeholder(t EntityType, original string) string {
	a.mu.Lock()
	defer a.mu.Unlock()
	key := fmt.Sprintf("%s:%s", t, original)
	if p, ok := a.mapping[key]; ok {
		return p
	}
	a.counters[t]++
	p := fmt.Sprintf("[%s_%d]", t, a.counters[t])
	a.mapping[key] = p
	return p
}

func (a *Anonymizer) AnonymizeText(text string) *AnonymizeResult {
	result := &AnonymizeResult{Original: text, Counts: make(map[EntityType]int)}
	out := text

	// Pass 1: Regex patterns
	for et, pat := range a.patterns {
		out = pat.ReplaceAllStringFunc(out, func(match string) string {
			result.Counts[et]++
			return a.placeholder(et, match)
		})
	}

	// Pass 2: Name dictionary
	for _, name := range a.names {
		if strings.Contains(out, name) {
			result.Counts[EntityName]++
			out = strings.ReplaceAll(out, name, a.placeholder(EntityName, name))
		}
	}

	result.Anonymized = out
	return result
}

// AnonymizeConversation processes all messages in a conversation.
func (a *Anonymizer) AnonymizeConversation(messages []map[string]string) []map[string]string {
	out := make([]map[string]string, len(messages))
	for i, msg := range messages {
		out[i] = make(map[string]string)
		for k, v := range msg {
			if k == "content" {
				out[i][k] = a.AnonymizeText(v).Anonymized
			} else {
				out[i][k] = v
			}
		}
	}
	return out
}

// HashForAudit generates truncated SHA-256 for audit trail without exposing PII.
func HashForAudit(original string) string {
	h := sha256.Sum256([]byte(original))
	return hex.EncodeToString(h[:8])
}
```

### 2.5 数据播种流水线

```python
"""CI-integrated golden dataset seeding pipeline with freshness validation."""
import hashlib, json, time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import httpx


@dataclass
class GoldenDataset:
    name: str
    version: str
    conversations: list = field(default_factory=list)
    expected_tool_sequences: list = field(default_factory=list)
    embeddings_snapshot: Optional[str] = None
    checksum: str = ""
    expires_at: str = field(default_factory=lambda: (datetime.now() + timedelta(days=7)).isoformat())

    def compute_checksum(self) -> str:
        content = json.dumps({"c": self.conversations, "t": self.expected_tool_sequences}, sort_keys=True)
        self.checksum = hashlib.sha256(content.encode()).hexdigest()[:16]
        return self.checksum

    def is_expired(self) -> bool:
        return datetime.now() > datetime.fromisoformat(self.expires_at)


@dataclass
class SeedResult:
    dataset: str
    success: bool
    records: int
    duration_s: float
    errors: list = field(default_factory=list)


class SeedingPipeline:
    def __init__(self, agent_api: str, vector_db: str, registry: Path):
        self.agent_api = agent_api
        self.vector_db = vector_db
        self.registry = registry
        self.client = httpx.Client(timeout=30.0)
        self.results: list[SeedResult] = []

    def _is_fresh(self, ds: GoldenDataset) -> bool:
        reg_file = self.registry / f"{ds.name}.json"
        if not reg_file.exists():
            return False
        reg = json.loads(reg_file.read_text())
        return not ds.is_expired() and reg.get("checksum") == ds.compute_checksum()

    def _seed_conversations(self, ds: GoldenDataset, ns: str) -> int:
        seeded = 0
        for conv in ds.conversations:
            resp = self.client.post(f"{self.agent_api}/api/v1/ns/{ns}/conversations", json={
                "conversation_id": conv["id"], "messages": conv["messages"],
                "metadata": {"source": "golden", "dataset": ds.name, "version": ds.version},
            })
            if resp.is_success:
                seeded += 1
        return seeded

    def _seed_tool_sequences(self, ds: GoldenDataset, ns: str) -> int:
        seeded = 0
        for seq in ds.expected_tool_sequences:
            resp = self.client.post(f"{self.agent_api}/api/v1/ns/{ns}/tool-sequences", json=seq)
            if resp.is_success:
                seeded += 1
        return seeded

    def _update_registry(self, ds: GoldenDataset) -> None:
        self.registry.mkdir(parents=True, exist_ok=True)
        (self.registry / f"{ds.name}.json").write_text(json.dumps({
            "checksum": ds.compute_checksum(), "version": ds.version,
            "seeded_at": datetime.now().isoformat(),
        }))

    def run(self, path: Path, namespace: str, force: bool = False) -> SeedResult:
        t0 = time.time()
        ds = GoldenDataset(**json.loads(path.read_text()))
        if not force and self._is_fresh(ds):
            return SeedResult(ds.name, True, 0, time.time() - t0)

        records = self._seed_conversations(ds, namespace) + self._seed_tool_sequences(ds, namespace)
        self._update_registry(ds)
        return SeedResult(ds.name, True, records, time.time() - t0)

    def run_all(self, datasets_dir: Path, namespace: str, force: bool = False) -> dict:
        for f in sorted(datasets_dir.glob("*.json")):
            self.results.append(self.run(f, namespace, force))
        return {
            "total": len(self.results),
            "success": sum(1 for r in self.results if r.success),
            "records": sum(r.records for r in self.results),
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--datasets-dir", required=True)
    parser.add_argument("--agent-api", default="http://agent-api:8080")
    parser.add_argument("--vector-db", default="http://vector-db:6333")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    pipeline = SeedingPipeline(args.agent_api, args.vector_db, Path(".data-registry"))
    report = pipeline.run_all(Path(args.datasets_dir), args.namespace, args.force)
    print(json.dumps(report, indent=2))
    Path("seeding-report.json").write_text(json.dumps(report, indent=2))
```

CI 集成配置（GitLab CI）：

```yaml
seed-test-data:
  stage: prepare
  script:
    - python seed_pipeline.py
        --namespace ${EPHEMERAL_NS}
        --datasets-dir ./test/golden_datasets/
        --agent-api http://agent-api.${EPHEMERAL_NS}.svc:8080
  artifacts:
    paths: [seeding-report.json]
    expire_in: 7 days
```

## 3. 课后思考题

1. **数据新鲜度与稳定性的博弈**：Golden Dataset 过期后自动重新生成可以保证与最新 Schema 兼容，但频繁变更又可能引入 Flaky Test。你会如何设计"渐进式更新"策略，在新鲜度和稳定性之间取得平衡？

2. **Embedding 向量的版本管理**：当 Embedding 模型升级时（如从 ada-002 迁移到 text-embedding-3-large），向量空间发生变化，历史快照全部失效。你会如何设计向量数据的版本管理和自动迁移机制？

3. **短生命周期环境的成本控制**：每天 200 个测试套件各创建独立 Namespace（含 Agent、Vector DB、Memory Store），集群资源消耗巨大。你会如何在"完全隔离"和"资源复用"之间做权衡？考虑池化、分级隔离、服务虚拟化等方案。

## 4. 今日小结

今天我们系统梳理了 AI Agent 测试数据管理与环境治理的完整体系：

- **理论层面**：明确了 Agent 系统在非确定性、有状态、多副作用等维度上对测试数据管理的独特挑战，建立了五阶段生命周期模型。
- **工程落地**：Ginkgo TestDataFactory（Builder 模式 + K8s 命名空间自动管理）、Playwright Fixture Manager（API Mock + 浏览器状态隔离）、K8s Ephemeral Provisioner（资源配额 + 网络策略 + TTL 回收）、多层脱敏工具、CI 数据播种流水线。

核心原则三条：**测试数据即代码**——所有 Fixture 版本化存储在 Git 中；**环境即声明**——通过代码声明环境规格，由自动化负责生命周期；**隔离即默认**——每个测试套件默认获得独立的数据面，除非显式声明共享。
