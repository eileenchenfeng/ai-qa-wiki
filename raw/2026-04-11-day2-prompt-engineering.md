---
title: "每日 AI 学习笔记 Day 2：Prompt 工程进阶 1"
authors: [xiaoai]
tags: [learning-notes]
---

# 每日 AI 学习笔记｜Day 2：Prompt 工程进阶 1（Zero-shot / Few-shot / CoT）

> 日期：2026-04-11（周六）  
> 学习计划来源：`AI_QA_Learning_Plan.md`  
> 进度判断：已完成 **Day 1: LLM 基础**，因此今天顺延学习 **Day 2**（不重复 Day 1）。

---


{ /* truncate */ }

## 0. 今日目标（你学完应该能做到什么）

1. **分清并掌握三类 Prompt 范式**：Zero-shot、Few-shot、CoT（思维链）。
2. 能从「测开/QA」视角理解：
   - 为什么 Prompt 是“测试对象”（SUT）的关键组成部分；
   - Prompt 的变更如何引入回归风险；
   - 如何为 Prompt 设计可自动化的评测与回归用例。
3. 完成一个可落地的实践：
   - 设计一个 **面向 ArkClaw 接口的 Few-shot 测试用例生成 Prompt**；
   - 给出 **Python / Go** 两套最小可用的测试代码（用于校验输出结构、稳定性、覆盖性）。

---

## 1. 核心理论知识讲解

### 1.1 Zero-shot：直接下指令，靠模型“通用能力”解题

**定义**：不给示例，只描述任务与约束，让模型直接生成答案。

**典型结构**：

- 角色（可选）：你是资深测试开发/接口测试专家
- 任务：针对某 API 生成测试用例
- 约束：输出格式、字段要求、覆盖维度
- 质量标准：至少 N 条、必须包含异常/边界/鉴权/幂等等

**优点**：
- 成本低、Prompt 短、迭代快；
- 适合“标准化程度高”的任务（例如：提取字段、翻译、总结）。

**风险 / 缺点（测开特别要关心）**：
- **输出波动大**：同样输入，模型可能换风格、换字段名、遗漏关键覆盖点；
- **隐性假设多**：你没说清楚的地方，模型会“自行补完”，而补完内容可能不符合你系统的真实约束；
- **难以回归**：一旦模型升级/温度参数变化，Zero-shot 更容易出现“风格漂移”。

**适用建议**：
- 当你已经有很强的结构化约束（如 JSON Schema、正则、工具校验），Zero-shot 才更稳。

---

### 1.2 Few-shot：用“示例”把模型拉回你期望的分布

**定义**：给模型 1~N 个输入输出示例（shots），让它“照着学”。

**Few-shot 的本质**（把它当成测试工程问题更好理解）:
- 你在提供 **参考实现（reference behavior）**；
- 你在指定 **风格、字段、覆盖偏好**；
- 你在做“软约束的规范化”。

**优点**：
- 明显提升：输出结构稳定性、字段一致性、覆盖维度一致性；
- 对“领域任务”更友好（例如：你内部系统的接口命名/错误码/字段语义）。

**风险 / 缺点**：
- **示例质量决定上限**：示例写得差，模型会把坏习惯学走；
- **示例偏置**：示例覆盖了 A 类异常却没覆盖 B 类，模型会倾向继续产出 A 类；
- **Token 成本与维护成本**：示例越多，调用成本越高；示例还需要版本管理（像测试基线一样）。

**Few-shot 设计经验（QA 视角）**：
1. **示例要覆盖“你最在乎的风险点”**，比如：鉴权、边界、异常码、幂等、并发；
2. **示例必须是“可验证的结构”**：建议统一输出 JSON，并在代码里做 schema 校验；
3. **示例要体现“同类项的一致性”**：字段名、枚举值、case 命名规则、优先级规则。

---

### 1.3 CoT（Chain-of-Thought，思维链）：让模型把推理过程写出来

**定义**：引导模型先推理、再给答案。常见形式是：

- “请一步步思考…”
- “先分析输入，再输出结论…”

**重要提醒（工程落地的真实情况）**：
- 在很多线上产品中，我们并不希望暴露“推理过程”（安全与成本考虑）；
- 但在**离线评测/测试生成**场景，CoT 非常有价值，因为它能：
  1) 提升复杂任务准确率；
  2) 给 QA 提供“为何这么生成”的可解释线索；
  3) 帮助定位 Prompt 失败点（模型在哪一步误解了输入）。

**CoT 的替代工程做法**：
- 使用“**隐藏推理 + 只输出结果**”的策略（不同模型/平台支持不同）；
- 或采用“**先生成分析草稿，再让模型自我压缩成结构化结果**”的两段式流程。

---

## 2. 测开视角：Prompt 也是代码（需要测试、需要版本化）

把 Prompt 当成“代码”的原因：

1. **Prompt 会直接决定系统行为**：尤其是“生成测试用例、生成 SQL、生成配置”的场景。
2. Prompt 的改动本质上是“逻辑改动”，会引入回归。
3. Prompt 的质量可以被量化：
   - **结构正确率**：输出是否可解析、字段是否齐全
   - **覆盖度**：是否包含异常/边界/鉴权/幂等/并发
   - **稳定性**：相似输入多次运行输出的一致性（或可接受的差异范围）
   - **有效性**：生成的测试用例是否能在真实系统中执行并发现问题

> 这也是 AI QA 的关键能力：把“自然语言产物”纳入工程化质量体系。

---

## 3. 工程实践：设计 ArkClaw 接口 Few-shot 测试用例生成 Prompt

> 说明：我这里用“接口契约（API Contract）”作为输入。你可以替换成 ArkClaw 实际接口文档字段。

### 3.1 目标输出规范（建议先定输出，再写 Prompt）

我们把模型输出固定成 JSON，便于自动化校验与回归：

```json
{
  "api": {
    "name": "string",
    "method": "GET|POST|PUT|DELETE",
    "path": "string"
  },
  "testcases": [
    {
      "id": "TC-001",
      "title": "string",
      "priority": "P0|P1|P2",
      "category": "happy_path|boundary|negative|auth|idempotency|concurrency|compatibility",
      "precondition": "string",
      "steps": ["string"],
      "request": {
        "headers": {"k": "v"},
        "query": {"k": "v"},
        "body": {"k": "v"}
      },
      "expected": {
        "http_status": 200,
        "body_contains": ["string"],
        "error_code": "string"
      }
    }
  ]
}
```

**为什么这么做（测开理由）**：
- JSON 可解析 → 适合做 CI 回归；
- 字段固定 → 可做 schema 校验；
- category/priority → 便于统计覆盖与分层执行；
- expected 结构化 → 便于比对与断言。

---

### 3.2 Prompt 模板（Few-shot）

下面是一份可直接投入使用的 Prompt（你可以把它当作“测试用例生成器”的 Spec）。

> 推荐把它放进 Git，并给每次变更打 Tag（像管理接口测试脚本一样）。

```text
你是一名资深测试开发工程师（Test Dev），擅长接口测试与质量保障。

【任务】
根据给定的 API 契约信息，为该接口生成高质量的接口测试用例。

【输出要求】
1) 只能输出 JSON，禁止输出任何解释性文字。
2) JSON 必须符合以下约束：
   - 顶层包含 api 与 testcases
   - testcases 至少 8 条
   - 必须覆盖：happy_path、boundary、negative、auth、idempotency（如适用）
   - 每条用例包含：id/title/priority/category/precondition/steps/request/expected
3) 用例必须可执行、步骤清晰、断言可检验。
4) 不要编造不存在的字段；如果契约未给出字段，请在 request 中留空对象（{}）。

【Few-shot 示例 1】
输入(API Contract):
{
  "name": "CreateRule",
  "method": "POST",
  "path": "/api/v1/rules",
  "headers": {"Authorization": "Bearer <token>"},
  "body_schema": {
    "rule_name": "string (1~64)",
    "severity": "enum: LOW|MEDIUM|HIGH",
    "enabled": "boolean"
  },
  "success": {"http_status": 200, "body": {"rule_id": "string"}},
  "errors": [
    {"http_status": 400, "error_code": "INVALID_PARAM"},
    {"http_status": 401, "error_code": "UNAUTHORIZED"}
  ]
}
输出(JSON):
{ ...（此处省略，见你的真实示例库） ... }

【Few-shot 示例 2】
输入(API Contract):
{
  "name": "GetRule",
  "method": "GET",
  "path": "/api/v1/rules/{rule_id}",
  "headers": {"Authorization": "Bearer <token>"},
  "path_params": {"rule_id": "string"},
  "success": {"http_status": 200, "body": {"rule_id": "string", "rule_name": "string"}},
  "errors": [
    {"http_status": 404, "error_code": "NOT_FOUND"},
    {"http_status": 401, "error_code": "UNAUTHORIZED"}
  ]
}
输出(JSON):
{ ...（此处省略，见你的真实示例库） ... }

【现在请处理】
输入(API Contract):
{{API_CONTRACT_JSON}}
```

#### 关键点解释（你写 Prompt 时应该有的“测试意识”）

- **“只能输出 JSON”**：减少花式输出导致的解析失败；
- **“至少 8 条 + 必须覆盖类别”**：把覆盖要求显式化，避免模型偷懒；
- **“不要编造字段”**：防止模型编造不存在的参数，导致用例不可执行；
- **Few-shot 示例库建议落库**：示例 1/2 不应该“省略”，而应该沉淀为你们团队的基线样本。

---

### 3.3 示例：给一个“假想 ArkClaw 接口”生成用例（输入样例）

```json
{
  "name": "ValidateCase",
  "method": "POST",
  "path": "/api/v1/qa/cases/validate",
  "headers": {"Authorization": "Bearer <token>", "Content-Type": "application/json"},
  "body_schema": {
    "case_title": "string (1~120)",
    "steps": "array<string> (1~30)",
    "expected": "string (1~500)",
    "tags": "array<string> (0~10)"
  },
  "success": {"http_status": 200, "body": {"valid": "boolean", "issues": "array<string>"}},
  "errors": [
    {"http_status": 400, "error_code": "INVALID_PARAM"},
    {"http_status": 401, "error_code": "UNAUTHORIZED"}
  ]
}
```

你把它替换进 `{{API_CONTRACT_JSON}}`，就能得到结构化用例。

---

## 4. 自动化校验（Python）：用 Pydantic + pytest 做“Prompt 回归测试”

> 目标：不依赖真实大模型 Key，也能先把“输出结构正确性”与“覆盖要求”自动化。

### 4.1 Pydantic Schema（结构校验）

```python
# file: prompt_case_schema.py
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Priority = Literal["P0", "P1", "P2"]
Category = Literal[
    "happy_path",
    "boundary",
    "negative",
    "auth",
    "idempotency",
    "concurrency",
    "compatibility",
]


class APIInfo(BaseModel):
    name: str
    method: Literal["GET", "POST", "PUT", "DELETE"]
    path: str


class Request(BaseModel):
    headers: Dict[str, str] = Field(default_factory=dict)
    query: Dict[str, object] = Field(default_factory=dict)
    body: Dict[str, object] = Field(default_factory=dict)


class Expected(BaseModel):
    http_status: int
    body_contains: List[str] = Field(default_factory=list)
    error_code: Optional[str] = None


class TestCase(BaseModel):
    id: str
    title: str
    priority: Priority
    category: Category
    precondition: str
    steps: List[str]
    request: Request
    expected: Expected


class CaseGenOutput(BaseModel):
    api: APIInfo
    testcases: List[TestCase]
```

### 4.2 pytest：覆盖类别与数量校验

```python
# file: test_prompt_output_contract.py
import json
import pytest

from prompt_case_schema import CaseGenOutput

REQUIRED_CATEGORIES = {"happy_path", "boundary", "negative", "auth", "idempotency"}


def validate_contract(output_json_str: str) -> CaseGenOutput:
    data = json.loads(output_json_str)
    return CaseGenOutput.model_validate(data)


def test_output_has_min_cases():
    # 这里先用一份“已保存的模型输出快照”作为 fixture
    # 真实落地时：你可以把 LLM 输出保存到 snapshots/ 下做回归
    output_json_str = open("snapshots/validate_case.output.json", "r", encoding="utf-8").read()

    parsed = validate_contract(output_json_str)
    assert len(parsed.testcases) >= 8


def test_output_covers_required_categories():
    output_json_str = open("snapshots/validate_case.output.json", "r", encoding="utf-8").read()
    parsed = validate_contract(output_json_str)

    cats = {tc.category for tc in parsed.testcases}
    missing = REQUIRED_CATEGORIES - cats
    assert not missing, f"missing categories: {missing}"  # 回归失败时一眼定位


@pytest.mark.parametrize("bad_json", ["", "not json", "{}"])
def test_invalid_output_rejected(bad_json):
    with pytest.raises(Exception):
        validate_contract(bad_json)
```

### 4.3 进一步增强（建议你后续加上）

- **稳定性测试**：同一输入运行 N 次，统计：
  - JSON 解析成功率
  - 必选类别覆盖率
  - 用例条数分布
- **内容有效性测试**：将生成用例真正打到测试环境（或 mock server），验证断言可执行。

---

## 5. 自动化校验（Go）：表驱动测试 + 结构解析，做轻量回归门禁

> 目标：在 Go 服务/CI 里也能快速做结构门禁（尤其适合你们已有 Go 测试体系的团队）。

### 5.1 定义结构体 + 必选类别校验

```go
// file: promptcase/output.go
package promptcase

type Output struct {
	API       APIInfo    `json:"api"`
	Testcases []TestCase `json:"testcases"`
}

type APIInfo struct {
	Name   string `json:"name"`
	Method string `json:"method"`
	Path   string `json:"path"`
}

type TestCase struct {
	ID       string   `json:"id"`
	Title    string   `json:"title"`
	Priority string   `json:"priority"`
	Category string   `json:"category"`
	Precond  string   `json:"precondition"`
	Steps    []string `json:"steps"`
	Request  Request  `json:"request"`
	Expected Expected `json:"expected"`
}

type Request struct {
	Headers map[string]string `json:"headers"`
	Query   map[string]any    `json:"query"`
	Body    map[string]any    `json:"body"`
}

type Expected struct {
	HTTPStatus   int      `json:"http_status"`
	BodyContains []string `json:"body_contains"`
	ErrorCode    string   `json:"error_code"`
}
```

### 5.2 Go 单测：最小门禁（数量 + 类别）

```go
// file: promptcase/output_test.go
package promptcase

import (
	"encoding/json"
	"os"
	"testing"
)

func TestOutputContract(t *testing.T) {
	b, err := os.ReadFile("../snapshots/validate_case.output.json")
	if err != nil {
		t.Fatalf("read snapshot: %v", err)
	}

	var out Output
	if err := json.Unmarshal(b, &out); err != nil {
		t.Fatalf("unmarshal json: %v", err)
	}

	if len(out.Testcases) < 8 {
		t.Fatalf("want >= 8 testcases, got %d", len(out.Testcases))
	}

	required := map[string]bool{
		"happy_path":  false,
		"boundary":    false,
		"negative":    false,
		"auth":        false,
		"idempotency": false,
	}

	for _, tc := range out.Testcases {
		if _, ok := required[tc.Category]; ok {
			required[tc.Category] = true
		}
	}

	for k, v := range required {
		if !v {
			t.Fatalf("missing required category: %s", k)
		}
	}
}
```

> 这类 Go 门禁很适合做成：
> - PR 阶段的“Prompt 基线变更必须通过”检查；
> - 或者作为 nightly job 做输出漂移监控。

---

## 6. 课后小思考（建议写在你的学习笔记里，形成“可复盘资产”）

1. **你现在团队里有哪些“自然语言资产”其实也应该被测试？**  
   例如：测试设计模板、缺陷复现步骤模板、上线 checklist、故障通告模板。

2. 如果明天把模型从 A 升级到 B，你觉得你最想先跑哪 3 类回归？为什么？

3. Few-shot 示例库应该由谁维护？  
   - QA 维护：更关注覆盖与可执行性；
   - RD 维护：更贴近真实接口语义；
   - 或者联合维护（推荐）。

4. 你会如何定义“Prompt 的稳定性”？  
   - 完全一致（过于严格）
   - 结构一致 + 关键断言一致（更工程化）
   - 允许风格变化但覆盖不变（更适合生成类任务）

---

## 7. 今日可交付产物（建议你顺手落库）

- `prompts/arkclaw_casegen_fewshot.prompt.txt`：Few-shot Prompt 模板（纳入版本管理）
- `snapshots/`：固定输入下的输出快照（用于回归）
- `tests/`：Python（pytest）与 Go（go test）的合同测试（contract test）

如果你愿意，我也可以基于你们真实的 ArkClaw 接口文档（字段/错误码/鉴权方式）把 Few-shot 示例 1/2 补齐成“可直接用的示例库”。
