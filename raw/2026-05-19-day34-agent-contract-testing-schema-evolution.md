---
title: "每日 AI 学习笔记｜Day 34：AI Agent 契约测试与 Schema 演进"
date: 2026-05-19
authors: [xiaoai]
tags: [learning-notes, AI, QA, Agent, contract-testing, schema-evolution, SDET, Ginkgo, Playwright, API-testing, pact, protobuf, backward-compatibility]
---

# 每日 AI 学习笔记 Day 34｜AI Agent 契约测试与 Schema 演进

**核心总结：** AI Agent 系统本质上是由多个松耦合服务组成的分布式系统——网关、编排器、模型推理、工具服务、Memory 存储、安全过滤等组件通过 API 契约协作。当任何一方单方面修改接口（新增字段、修改枚举、废弃参数、调整语义），都可能在运行时引发级联故障，而这类问题在 E2E 环境中往往表现为"偶发失败"或"某个版本组合才复现"。契约测试（Contract Testing）的核心目标是：让每个服务在自己的 CI 流水线中就能验证"我的接口变更不会破坏任何消费者"，而不必等到集成环境才发现不兼容。对 AI Agent 来说，契约不仅包括传统的 HTTP/gRPC Schema，还包括工具调用的 JSON Schema、Prompt 模板的变量契约、Memory 读写的数据结构契约和模型输出的结构化格式契约。资深测试开发需要掌握：如何建立多层契约基线、如何在 CI 中自动检测 Breaking Change、如何用 Pact/Protobuf/JSON Schema 实现 Consumer-Driven Contract Testing、以及如何设计 Schema 演进策略保障向后兼容。

{/* truncate */}

## 0. 今日目标

今天的主题是 AI Agent 契约测试与 Schema 演进。完成学习后，你应该能够做到五件事：

1. 能区分 Provider-Driven 与 Consumer-Driven 契约测试的适用场景，并为 Agent 系统选择合适策略
2. 能识别 AI Agent 系统中的四类契约边界（HTTP/gRPC API、工具调用 Schema、Prompt 变量、Memory 数据结构）
3. 能用 Pact（Go/Python）实现 Consumer-Driven 契约测试，覆盖编排器与工具服务之间的交互
4. 能用 Protobuf + buf breaking 或 JSON Schema + ajv 在 CI 中自动检测 Breaking Change
5. 能设计 Schema 演进策略（Additive-Only、版本化 Endpoint、Sunset Header），保障 Agent 组件独立部署

---

## 1. 核心理论

### 1.1 为什么 AI Agent 需要契约测试

传统微服务的契约测试已经有成熟实践（Pact、Spring Cloud Contract、Protovalidate 等）。AI Agent 对契约测试的需求更强烈，原因在于：

**组件迭代节奏不同步。** 模型推理服务可能每周更新一次，工具服务可能每天部署多次，Prompt 模板可能通过配置中心热更新。如果没有契约测试，任何一方的变更都可能在运行时出现不兼容。

**接口语义比传统 API 更模糊。** 传统 REST API 的字段类型和含义是固定的。但 Agent 系统中，模型输出的 JSON 结构可能因 Prompt 微调而变化，工具参数的枚举值可能随业务扩展而增加，Memory 中存储的上下文格式可能跨版本不兼容。

**集成测试的成本极高。** Agent 系统的完整 E2E 环境需要模型服务、向量数据库、工具链、安全服务等全部就绪。契约测试的价值在于：让每个组件在单元测试阶段就能验证接口兼容性，大幅减少对集成环境的依赖。

### 1.2 AI Agent 的四类契约边界

<table header-row="true" header-col="false" col-widths="180,280,280,260">
<tr>
<td>契约类型</td>
<td>Provider（提供者）</td>
<td>Consumer（消费者）</td>
<td>典型 Breaking Change</td>
</tr>
<tr>
<td>**HTTP/gRPC API 契约**</td>
<td>工具服务、Memory 服务、模型网关</td>
<td>编排器（Orchestrator）</td>
<td>删除字段、修改类型、移除 Endpoint</td>
</tr>
<tr>
<td>**工具调用 Schema 契约**</td>
<td>工具注册中心 / 工具 Manifest</td>
<td>模型推理（Function Calling）</td>
<td>新增必填参数、修改枚举值、变更返回结构</td>
</tr>
<tr>
<td>**Prompt 变量契约**</td>
<td>Prompt 模板管理系统</td>
<td>编排器、模型推理</td>
<td>删除变量占位符、修改变量格式要求</td>
</tr>
<tr>
<td>**Memory 数据结构契约**</td>
<td>Memory 写入方（Session Manager）</td>
<td>Memory 读取方（Context Builder）</td>
<td>修改 JSON 结构、删除历史字段、变更编码</td>
</tr>
</table>

### 1.3 Consumer-Driven vs Provider-Driven

**Provider-Driven 契约测试**：由接口提供者定义 Schema（如 OpenAPI Spec、Protobuf），消费者根据 Schema 生成客户端。适合工具服务等具有明确 API 文档的场景。

**Consumer-Driven 契约测试**：由消费者定义"我期望从你那里得到什么"，提供者运行消费者生成的契约来验证是否满足。适合编排器与多个工具服务交互的场景——每个工具服务只需满足编排器实际使用到的字段子集。

在 Agent 系统中，推荐的策略是**混合模式**：
- 工具 Schema → Provider-Driven（工具定义 JSON Schema，模型按 Schema 生成调用）
- 编排器 ↔ 后端服务 → Consumer-Driven（编排器定义期望，服务验证满足）
- Memory 结构 → Schema Registry + 版本化（读写双方通过版本号协商格式）

---

## 2. 工程实践

### 2.1 Pact Consumer-Driven 契约测试（Go Ginkgo 版本）

以下示例演示：编排器（Consumer）期望从工具服务（Provider）获取天气数据，使用 Pact-Go 生成并验证契约。

```go
//go:build contract

package contract_test

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "testing"

    "github.com/onsi/ginkgo/v2"
    "github.com/onsi/gomega"
    "github.com/pact-foundation/pact-go/v2/consumer"
    "github.com/pact-foundation/pact-go/v2/matchers"
)

func TestContract(t *testing.T) {
    gomega.RegisterFailHandler(ginkgo.Fail)
    ginkgo.RunSpecs(t, "Agent Contract Suite")
}

var _ = ginkgo.Describe("Orchestrator -> WeatherTool Contract", func() {
    var mockProvider *consumer.V2HTTPMockProvider

    ginkgo.BeforeEach(func() {
        var err error
        mockProvider, err = consumer.NewV2Pact(consumer.MockHTTPProviderConfig{
            Consumer: "agent-orchestrator",
            Provider: "weather-tool-service",
            PactDir:  "./pacts",
        })
        gomega.Expect(err).NotTo(gomega.HaveOccurred())
    })

    ginkgo.It("should return weather data with required fields", func() {
        err := mockProvider.
            AddInteraction().
            Given("Beijing weather is available").
            UponReceiving("a request for current weather").
            WithCompleteRequest(consumer.Request{
                Method: "POST",
                Path:   matchers.String("/api/v1/tools/weather/execute"),
                Body: map[string]interface{}{
                    "location": "Beijing",
                    "unit":     "celsius",
                },
            }).
            WithCompleteResponse(consumer.Response{
                Status: 200,
                Body: matchers.MapMatcher{
                    "temperature": matchers.Like(22.5),
                    "unit":        matchers.Term("celsius", `celsius|fahrenheit`),
                    "condition":   matchers.Like("sunny"),
                    "humidity":    matchers.Like(45),
                    "wind_speed":  matchers.Like(12.3),
                    "timestamp":   matchers.Regex("2026-05-19T10:00:00Z", `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z`),
                },
            }).
            ExecuteTest(func(config consumer.MockServerConfig) error {
                url := fmt.Sprintf("http://%s:%d/api/v1/tools/weather/execute", config.Host, config.Port)
                body := `{"location":"Beijing","unit":"celsius"}`
                resp, err := http.Post(url, "application/json", io.NopCloser(strings.NewReader(body)))
                if err != nil {
                    return err
                }
                defer resp.Body.Close()

                gomega.Expect(resp.StatusCode).To(gomega.Equal(200))

                var result map[string]interface{}
                err = json.NewDecoder(resp.Body).Decode(&result)
                gomega.Expect(err).NotTo(gomega.HaveOccurred())
                gomega.Expect(result).To(gomega.HaveKey("temperature"))
                gomega.Expect(result).To(gomega.HaveKey("condition"))
                gomega.Expect(result).To(gomega.HaveKey("timestamp"))
                return nil
            })
        gomega.Expect(err).NotTo(gomega.HaveOccurred())
    })

    ginkgo.It("should handle tool not found gracefully", func() {
        err := mockProvider.
            AddInteraction().
            Given("unknown tool requested").
            UponReceiving("a request for non-existent tool").
            WithCompleteRequest(consumer.Request{
                Method: "POST",
                Path:   matchers.String("/api/v1/tools/unknown_tool/execute"),
                Body:   map[string]interface{}{"query": "test"},
            }).
            WithCompleteResponse(consumer.Response{
                Status: 404,
                Body: matchers.MapMatcher{
                    "error_code": matchers.Like("TOOL_NOT_FOUND"),
                    "message":    matchers.Like("Tool 'unknown_tool' is not registered"),
                },
            }).
            ExecuteTest(func(config consumer.MockServerConfig) error {
                url := fmt.Sprintf("http://%s:%d/api/v1/tools/unknown_tool/execute", config.Host, config.Port)
                resp, err := http.Post(url, "application/json", io.NopCloser(strings.NewReader(`{"query":"test"}`)))
                if err != nil {
                    return err
                }
                defer resp.Body.Close()
                gomega.Expect(resp.StatusCode).To(gomega.Equal(404))
                return nil
            })
        gomega.Expect(err).NotTo(gomega.HaveOccurred())
    })
})
```

**运行方式：**
```bash
go test -tags=contract -v ./contract/...
```

生成的 Pact 文件（`./pacts/agent-orchestrator-weather-tool-service.json`）会被推送到 Pact Broker，工具服务的 CI 拉取并验证。

### 2.2 JSON Schema 工具契约检测（Python 版本）

以下示例演示：如何在 CI 中自动检测工具 Schema 的 Breaking Change。

```python
"""tool_schema_compat_checker.py
CI 中运行，检测工具 JSON Schema 变更是否向后兼容。
"""
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
from deepdiff import DeepDiff


def load_schema(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def detect_breaking_changes(old_schema: dict, new_schema: dict) -> list[str]:
    """检测从 old_schema 到 new_schema 的破坏性变更。"""
    breaking = []

    old_required = set(old_schema.get("properties", {}).keys())
    new_required = set(new_schema.get("properties", {}).keys())

    # Rule 1: 删除已有字段 = Breaking
    removed = old_required - new_required
    if removed:
        breaking.append(f"REMOVED fields: {removed}")

    # Rule 2: 新增 required 字段 = Breaking（消费者未传该字段会报错）
    old_req_list = set(old_schema.get("required", []))
    new_req_list = set(new_schema.get("required", []))
    new_mandatory = new_req_list - old_req_list
    if new_mandatory:
        breaking.append(f"NEW required fields: {new_mandatory}")

    # Rule 3: 类型变更 = Breaking
    for field in old_required & new_required:
        old_type = old_schema["properties"][field].get("type")
        new_type = new_schema["properties"][field].get("type")
        if old_type != new_type:
            breaking.append(f"TYPE changed for '{field}': {old_type} -> {new_type}")

    # Rule 4: 枚举值缩减 = Breaking
    for field in old_required & new_required:
        old_enum = set(old_schema["properties"][field].get("enum", []))
        new_enum = set(new_schema["properties"][field].get("enum", []))
        if old_enum and (old_enum - new_enum):
            breaking.append(
                f"ENUM values removed for '{field}': {old_enum - new_enum}"
            )

    return breaking


def validate_sample_against_schema(sample: dict, schema: dict) -> list[str]:
    """用真实调用样本验证是否符合 schema。"""
    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for error in validator.iter_errors(sample):
        errors.append(f"{error.json_path}: {error.message}")
    return errors


if __name__ == "__main__":
    old = load_schema(sys.argv[1])
    new = load_schema(sys.argv[2])

    breaks = detect_breaking_changes(old, new)
    if breaks:
        print("❌ BREAKING CHANGES DETECTED:")
        for b in breaks:
            print(f"  - {b}")
        sys.exit(1)
    else:
        print("✅ Schema change is backward-compatible")

    # 可选：用历史调用样本验证新 schema
    if len(sys.argv) > 3:
        samples_dir = Path(sys.argv[3])
        for sample_file in samples_dir.glob("*.json"):
            sample = json.loads(sample_file.read_text())
            errs = validate_sample_against_schema(sample, new)
            if errs:
                print(f"⚠️  Sample {sample_file.name} fails new schema:")
                for e in errs:
                    print(f"    {e}")
                sys.exit(1)
        print("✅ All historical samples pass new schema")
```

**CI 集成（GitHub Actions）：**
```yaml
- name: Check Tool Schema Compatibility
  run: |
    python tool_schema_compat_checker.py \
      schemas/weather_tool_v1.json \
      schemas/weather_tool_v2.json \
      samples/weather_tool_calls/
```

### 2.3 Protobuf Breaking Change 检测（buf CLI）

对于使用 gRPC 的 Agent 内部通信，用 `buf` 工具检测 Breaking Change：

```yaml
# buf.yaml
version: v2
modules:
  - path: proto
breaking:
  use:
    - WIRE_JSON
  except:
    - FIELD_SAME_JSON_NAME
```

```bash
# CI 中执行
buf breaking proto --against '.git#branch=main'
```

**常见 Agent gRPC Breaking Change 类型：**

```protobuf
// v1: 原始定义
message ToolCallRequest {
  string tool_name = 1;
  string parameters_json = 2;  // 自由格式 JSON
  string session_id = 3;
}

// v2: Breaking! 删除了 parameters_json，改用强类型
message ToolCallRequest {
  string tool_name = 1;
  ToolParameters parameters = 2;  // 类型变更 = wire 不兼容
  string session_id = 3;
  string trace_id = 4;  // 新增可选字段 = 安全
}
```

### 2.4 Prompt 变量契约测试（Ginkgo 版本）

Prompt 模板中的变量占位符也是一种契约。如果模板引用了 `{{.user_history}}` 但编排器只传了 `{{.chat_history}}`，渲染会失败。

```go
//go:build contract

package prompt_contract_test

import (
    "os"
    "regexp"
    "strings"
    "testing"

    "github.com/onsi/ginkgo/v2"
    "github.com/onsi/gomega"
)

func TestPromptContract(t *testing.T) {
    gomega.RegisterFailHandler(ginkgo.Fail)
    ginkgo.RunSpecs(t, "Prompt Variable Contract Suite")
}

var _ = ginkgo.Describe("Prompt Template Variable Contract", func() {
    var (
        templateContent string
        variableRegex   = regexp.MustCompile(`\{\{\s*\.(\w+)\s*\}\}`)
    )

    // 编排器承诺提供的变量集合
    orchestratorVariables := map[string]bool{
        "system_prompt":   true,
        "user_message":    true,
        "chat_history":    true,
        "tool_results":    true,
        "user_context":    true,
        "current_time":    true,
        "session_id":      true,
        "available_tools": true,
    }

    ginkgo.BeforeEach(func() {
        content, err := os.ReadFile("../../prompts/agent_main_v2.tmpl")
        gomega.Expect(err).NotTo(gomega.HaveOccurred())
        templateContent = string(content)
    })

    ginkgo.It("should only reference variables provided by orchestrator", func() {
        matches := variableRegex.FindAllStringSubmatch(templateContent, -1)
        var unknownVars []string
        for _, match := range matches {
            varName := match[1]
            if !orchestratorVariables[varName] {
                unknownVars = append(unknownVars, varName)
            }
        }
        gomega.Expect(unknownVars).To(gomega.BeEmpty(),
            "Template references unknown variables: %v", unknownVars)
    })

    ginkgo.It("should not have empty variable placeholders", func() {
        gomega.Expect(templateContent).NotTo(gomega.ContainSubstring("{{.}}"),
            "Template contains bare '{{.}}' which indicates missing variable name")
    })

    ginkgo.It("should use consistent variable naming convention", func() {
        matches := variableRegex.FindAllStringSubmatch(templateContent, -1)
        for _, match := range matches {
            varName := match[1]
            // 所有变量应该是 snake_case
            gomega.Expect(varName).To(gomega.MatchRegexp(`^[a-z][a-z0-9_]*$`),
                "Variable '%s' violates snake_case convention", varName)
        }
    })

    ginkgo.It("should not exceed max variable count per template", func() {
        matches := variableRegex.FindAllStringSubmatch(templateContent, -1)
        uniqueVars := make(map[string]bool)
        for _, match := range matches {
            uniqueVars[match[1]] = true
        }
        // 单个模板引用超过 15 个变量通常意味着需要拆分
        gomega.Expect(len(uniqueVars)).To(gomega.BeNumerically("<=", 15),
            "Template uses %d variables, consider splitting", len(uniqueVars))
    })
})
```

### 2.5 Memory 数据结构契约（Schema Registry 方案）

```go
//go:build contract

package memory_contract_test

import (
    "encoding/json"
    "testing"

    "github.com/onsi/ginkgo/v2"
    "github.com/onsi/gomega"
    "github.com/xeipuuv/gojsonschema"
)

func TestMemoryContract(t *testing.T) {
    gomega.RegisterFailHandler(ginkgo.Fail)
    ginkgo.RunSpecs(t, "Memory Schema Contract Suite")
}

// 定义 Memory 写入的 schema 契约
const memoryEntrySchemaV2 = `{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["session_id", "role", "content", "timestamp", "schema_version"],
  "properties": {
    "session_id": {"type": "string", "minLength": 1},
    "role": {"type": "string", "enum": ["user", "assistant", "system", "tool"]},
    "content": {"type": "string"},
    "timestamp": {"type": "string", "format": "date-time"},
    "schema_version": {"type": "integer", "minimum": 1},
    "metadata": {
      "type": "object",
      "properties": {
        "tool_call_id": {"type": "string"},
        "model_id": {"type": "string"},
        "token_count": {"type": "integer", "minimum": 0}
      }
    }
  },
  "additionalProperties": false
}`

var _ = ginkgo.Describe("Memory Entry Schema Contract", func() {
    var schemaLoader gojsonschema.JSONLoader

    ginkgo.BeforeEach(func() {
        schemaLoader = gojsonschema.NewStringLoader(memoryEntrySchemaV2)
    })

    ginkgo.DescribeTable("valid memory entries should pass schema",
        func(entry map[string]interface{}) {
            docLoader := gojsonschema.NewGoLoader(entry)
            result, err := gojsonschema.Validate(schemaLoader, docLoader)
            gomega.Expect(err).NotTo(gomega.HaveOccurred())
            gomega.Expect(result.Valid()).To(gomega.BeTrue(),
                "Validation errors: %v", result.Errors())
        },
        ginkgo.Entry("user message", map[string]interface{}{
            "session_id":     "sess_abc123",
            "role":           "user",
            "content":        "What is the weather in Beijing?",
            "timestamp":      "2026-05-19T09:00:00Z",
            "schema_version": 2,
        }),
        ginkgo.Entry("tool result with metadata", map[string]interface{}{
            "session_id":     "sess_abc123",
            "role":           "tool",
            "content":        `{"temperature": 22.5, "condition": "sunny"}`,
            "timestamp":      "2026-05-19T09:00:01Z",
            "schema_version": 2,
            "metadata": map[string]interface{}{
                "tool_call_id": "call_weather_001",
                "token_count":  150,
            },
        }),
    )

    ginkgo.DescribeTable("invalid entries should be rejected",
        func(entry map[string]interface{}, expectedError string) {
            docLoader := gojsonschema.NewGoLoader(entry)
            result, err := gojsonschema.Validate(schemaLoader, docLoader)
            gomega.Expect(err).NotTo(gomega.HaveOccurred())
            gomega.Expect(result.Valid()).To(gomega.BeFalse())
            errMessages := ""
            for _, e := range result.Errors() {
                errMessages += e.String() + "; "
            }
            gomega.Expect(errMessages).To(gomega.ContainSubstring(expectedError))
        },
        ginkgo.Entry("missing session_id", map[string]interface{}{
            "role": "user", "content": "hello",
            "timestamp": "2026-05-19T09:00:00Z", "schema_version": 2,
        }, "session_id"),
        ginkgo.Entry("invalid role enum", map[string]interface{}{
            "session_id": "sess_abc", "role": "admin", "content": "x",
            "timestamp": "2026-05-19T09:00:00Z", "schema_version": 2,
        }, "role"),
        ginkgo.Entry("extra field rejected", map[string]interface{}{
            "session_id": "sess_abc", "role": "user", "content": "x",
            "timestamp": "2026-05-19T09:00:00Z", "schema_version": 2,
            "unknown_field": "should_fail",
        }, "additional"),
    )
})
```

### 2.6 Schema 演进策略：E2E 验证（Playwright + API）

```python
"""test_schema_evolution_e2e.py
验证工具服务在 Schema 升级后，Agent 前端 + 编排器仍能正常工作。
"""
import pytest
from playwright.sync_api import Page, expect
import httpx

AGENT_API = "http://localhost:8080"
TOOL_SERVICE = "http://localhost:9090"


class TestSchemaEvolutionE2E:
    """E2E 验证 Schema 演进不破坏用户可见行为。"""

    def test_v1_client_works_with_v2_server(self):
        """旧版编排器请求仍能被新版工具服务正确处理。"""
        # v1 格式：parameters 是 flat JSON
        v1_request = {
            "tool_name": "weather",
            "parameters": {"location": "Beijing", "unit": "celsius"},
            "version": "v1",
        }
        resp = httpx.post(f"{TOOL_SERVICE}/api/v1/tools/execute", json=v1_request)
        assert resp.status_code == 200
        data = resp.json()
        # v2 服务应该能处理 v1 请求并返回 v1 兼容格式
        assert "temperature" in data
        assert "condition" in data

    def test_v2_client_gets_enhanced_response(self):
        """新版编排器能获取 v2 增强字段。"""
        v2_request = {
            "tool_name": "weather",
            "parameters": {"location": "Beijing", "unit": "celsius"},
            "version": "v2",
            "include_forecast": True,
        }
        resp = httpx.post(f"{TOOL_SERVICE}/api/v2/tools/execute", json=v2_request)
        assert resp.status_code == 200
        data = resp.json()
        assert "temperature" in data
        assert "forecast" in data  # v2 新增字段
        assert len(data["forecast"]) > 0

    def test_sunset_header_present_on_deprecated_endpoint(self):
        """废弃端点应返回 Sunset header 通知消费者迁移。"""
        resp = httpx.post(
            f"{TOOL_SERVICE}/api/v1/tools/execute",
            json={"tool_name": "weather", "parameters": {"location": "Beijing"}},
        )
        assert resp.status_code == 200
        # RFC 8594: Sunset header
        assert "Sunset" in resp.headers
        assert "Deprecation" in resp.headers

    def test_ui_handles_new_fields_gracefully(self, page: Page):
        """前端在工具返回新增字段时不崩溃。"""
        page.goto(f"{AGENT_API}/chat")
        page.fill('[data-testid="chat-input"]', "What is the weather in Shanghai?")
        page.click('[data-testid="send-button"]')

        # 等待 Agent 回复
        response_box = page.locator('[data-testid="agent-response"]').last
        expect(response_box).to_be_visible(timeout=30000)

        # 验证回复包含天气信息，不因新字段而报错
        response_text = response_box.text_content()
        assert "Shanghai" in response_text or "上海" in response_text
        assert "error" not in response_text.lower()

        # 验证无前端 console 错误
        errors = page.evaluate("() => window.__console_errors || []")
        schema_errors = [e for e in errors if "schema" in e.lower() or "undefined" in e.lower()]
        assert len(schema_errors) == 0, f"Frontend schema errors: {schema_errors}"
```

---

## 3. CI/CD 集成：契约测试流水线

### 3.1 完整的契约测试 CI 流程

```yaml
# .github/workflows/contract-tests.yml
name: Agent Contract Tests

on:
  push:
    paths:
      - 'proto/**'
      - 'schemas/**'
      - 'prompts/**'
  pull_request:
    paths:
      - 'proto/**'
      - 'schemas/**'
      - 'prompts/**'

jobs:
  protobuf-breaking:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: bufbuild/buf-setup-action@v1
      - run: buf breaking proto --against '.git#branch=main'

  json-schema-compat:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install jsonschema deepdiff
      - run: |
          for schema in schemas/*.json; do
            base=$(basename "$schema")
            git show HEAD~1:"schemas/$base" > /tmp/old_schema.json 2>/dev/null || continue
            python tool_schema_compat_checker.py /tmp/old_schema.json "$schema"
          done

  pact-consumer:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - run: go test -tags=contract -v ./contract/...
      - run: |
          # 推送 Pact 到 Broker
          pact-broker publish ./pacts \
            --consumer-app-version=${{ github.sha }} \
            --branch=${{ github.ref_name }}

  prompt-contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - run: go test -tags=contract -v ./prompt_contract/...
```

### 3.2 Pact Webhook：Provider 自动验证

当 Consumer 推送新契约到 Pact Broker 后，Broker 通过 Webhook 触发 Provider CI：

```bash
# Provider 验证命令
pact-verifier-go \
  --provider-base-url=http://localhost:9090 \
  --pact-broker-url=https://pact-broker.internal.com \
  --provider=weather-tool-service \
  --provider-app-version=$(git rev-parse HEAD) \
  --publish-verification-results
```

---

## 4. Schema 演进最佳实践

### 4.1 Additive-Only 规则

```
✅ 安全变更（非 Breaking）：
  - 新增可选字段
  - 新增新的 enum 值（在已有值之外）
  - 新增新的 API endpoint
  - 放宽字段约束（如 minLength 变小）

❌ 破坏性变更（Breaking）：
  - 删除已有字段
  - 修改字段类型
  - 新增 required 字段
  - 删除 enum 值
  - 重命名字段
  - 收紧字段约束（如 maxLength 变小）
```

### 4.2 版本化端点 + Sunset 策略

```
Timeline:
  v1 发布 ──→ v2 发布 ──→ v1 标记 Sunset ──→ v1 下线
                          (Sunset: 2026-08-19)
                          (Deprecation: true)
```

每个废弃接口在下线前至少保留 90 天。Sunset Header 告知消费者精确下线日期，CI 中可检测到并产生 Warning。

### 4.3 Schema Registry 模式

对于 Memory 等需要多版本共存的场景，推荐使用 Schema Registry：

```json
{
  "schema_version": 2,
  "session_id": "sess_abc",
  "role": "user",
  "content": "hello"
}
```

Reader 根据 `schema_version` 选择对应的反序列化逻辑，实现多版本并行读取。

---

## 5. 课后思考题

1. **场景设计**：你的 Agent 系统中，编排器依赖 5 个工具服务。某天其中一个工具服务新增了一个 required 参数但未通知编排器团队。请设计一个完整的契约测试方案，确保这类问题在 CI 阶段就被发现。

2. **演进策略**：Memory 服务需要将 `chat_history` 字段从 `string`（纯文本）改为 `object`（结构化 JSON）。请设计一个三阶段迁移方案，保证：(a) 旧 Reader 不崩溃，(b) 新 Writer 兼容旧 Reader，(c) 有明确的"全量迁移完成"判断标准。

3. **工具链选型**：对比 Pact、Spring Cloud Contract 和 buf breaking 三个工具在 AI Agent 场景中的优劣。考虑因素：多语言支持、Schema 表达力、CI 集成难度、学习曲线。

---

## 6. 今日小结

今天我们深入探讨了 AI Agent 系统中契约测试的完整实践。核心要点：

- **四类契约边界**：AI Agent 系统不仅有传统的 API 契约，还有工具调用 Schema、Prompt 变量、Memory 数据结构三类特有契约
- **Consumer-Driven 优先**：在多工具服务场景中，由编排器定义"我需要什么"比由工具定义"我提供什么"更能避免过度耦合
- **自动化检测**：通过 `buf breaking`、JSON Schema diff、Pact Broker Webhook 实现 Breaking Change 的 CI 级拦截
- **演进策略**：Additive-Only + Sunset Header + Schema Registry 三板斧，保证组件可独立部署、接口可渐进演进
- **E2E 兜底**：契约测试发现接口不兼容，E2E 测试验证用户可见行为不受影响——两者互补，不可替代

契约测试的最大价值不是发现"接口坏了"，而是让每个团队在发布前就知道"我的变更对谁有影响"，从而把集成风险从运行时前移到编码时。
