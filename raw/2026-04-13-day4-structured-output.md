---
title: "每日 AI 学习笔记 Day 4：结构化输出约束（JSON Mode 与 Regex Constraint）"
authors: [xiaoai]
tags: [learning-notes, AI, QA, LLM]
date: 2026-04-13
---

> 学习计划来源：`AI_QA_Learning_Plan.md`  
> 进度判断：已完成 **Day 1（LLM Basics）/ Day 2（Prompt Engineering）/ Day 3（ToT & ReAct）**，因此今天推进至 **Day 4**。  
> 今日主题：**让大模型“像接口一样”稳定输出：结构化输出约束（JSON Mode 与 Regex Constraint）**

{ /* truncate */ }

## 0. 今日目标（你学完应该能做到什么）

1. 说清楚：**为什么 LLM 输出经常“不好测/不好接入”**，结构化约束能解决什么问题。
2. 分清楚两类约束手段：
   - **JSON Mode / JSON Schema / Function Calling**（偏“结构约束”）
   - **Regex Constraint**（偏“格式约束”）
3. 从测开视角落地：
   - 写一个 **Python 用例生成器**：强制模型输出 JSON 格式测试用例
   - 用 **Pydantic 做合同校验（contract test）**
   - 给出一套**可回归的质量指标**（解析成功率、字段完整率、覆盖率）

---

## 1. 核心理论知识讲解

### 1.1 为什么“结构化输出”是 AI QA 的第一块基建

在传统软件里，最稳定、最可测的交互通常长这样：
- 请求：固定协议（HTTP/JSON）
- 响应：固定 schema（字段存在性、类型、枚举、约束）
- 验证：断言 + 解析 + 兼容性策略

但 LLM 天生输出自由文本，常见问题包括：
- **不可解析**：夹杂解释性文字、markdown、代码块、中文引号、末尾多逗号
- **字段漂移**：`expected` 变成 `expectation`，`steps` 变成 `step_list`
- **类型漂移**：本该是数组却输出字符串；布尔值输出 `"true"`
- **语义漂移**：字段齐了，但内容不满足业务约束（例如：优先级枚举写成 `P3`）

所以对测开而言，结构化约束的意义是：
> 把 LLM 从“写作文”拉回“写接口响应”。

当输出可解析、可校验，你才能：
- 做自动化回归（CI 门禁）
- 做差异比对（diff）
- 做统计指标（解析成功率 / 缺字段率 / 类别覆盖率）
- 做故障定位（到底是模型问题、Prompt 问题、还是工具链问题）

---

### 1.2 JSON Mode：让模型“只说 JSON”

**JSON Mode**（不同平台叫法不同）通常指：
- 你在请求中声明：输出必须是合法 JSON
- 服务端在解码/采样时对输出做约束（或者做后处理）

它解决的是：
- 输出中夹杂自然语言解释
- 结构不闭合 / 不合法

但要注意：JSON Mode 通常只能保证“语法合法”，并不保证：
- 字段齐全
- 类型正确
- 枚举合法
- 语义正确

因此工程上常见组合是：
- **JSON Mode + JSON Schema（或 Pydantic）校验**
- 校验失败 → **自动修复（repair）或二次追问（self-heal）**

---

### 1.3 JSON Schema / Function Calling：让结构更“像合同”

如果平台支持 **Function Calling（工具调用）** 或 **JSON Schema 输出约束**，它们的核心价值是：
- 模型不是“随便写一段 JSON”
- 而是“填一个你给定的结构模板”

对 QA 的启发是：
> 你可以把 LLM 的输出当作一个“外部依赖接口”，给它定义契约（Contract），然后像测接口一样测它。

常见测试点：
- Schema 合法率（必须达到阈值，例如 ≥ 99%）
- 必填字段缺失率
- 枚举越界率（例如 priority 只能 P0/P1/P2）
- 长度约束越界率（steps 最多 30 条）

---

### 1.4 Regex Constraint：用“格式规则”卡住最关键的部分

**Regex Constraint** 可以理解为：
- 你不一定能把所有结构都约束死
- 但你可以把“最容易漂移、最影响解析/执行”的部分卡住

适用场景举例：
- 用例 ID 必须符合 `TC-\d{4}`
- 时间戳必须符合 ISO 8601
- 错误码必须符合 `^[A-Z_]+$`
- 输出必须以 `{` 开头、以 `}` 结尾（最小可行版本）

Regex 的边界：
- 它不擅长表达深层 JSON 结构（正则不是解析器）
- 更适合作为“第一道闸门”：先保证能被下游接住

工程上推荐使用：
- **Regex 做“入口过滤”**（挡住明显不合格输出）
- **Schema 做“深度校验”**（类型、字段、枚举、约束）

---

## 2. 测开视角：把 LLM 输出变成“可回归的产物”

今天我们把目标定得非常具体：
> **让大模型输出标准 JSON 测试用例，并且像接口一样被自动化校验。**

你可以把它直接落成三类资产：
1. `prompts/`：Prompt 模板（像代码一样版本化）
2. `schemas/`：输出 Schema（合同）
3. `tests/`：合同测试（contract tests），作为 CI 门禁

---

## 3. 工程实践：Python 强制输出 JSON 用例 + Pydantic 校验

> 实践目标：
> 1) 让模型输出“只包含 JSON”
> 2) 用 Pydantic 校验结构、枚举、长度
> 3) 若失败：自动触发一次“修复回合”（可选）

### 3.1 先定义“测试用例输出合同”（Pydantic Schema）

```python
# file: case_schema.py
from __future__ import annotations
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

Priority = Literal["P0", "P1", "P2"]
Category = Literal["happy_path", "boundary", "negative", "auth", "idempotency", "concurrency"]

class APIInfo(BaseModel):
    name: str = Field(..., min_length=1)
    method: Literal["GET", "POST", "PUT", "DELETE"]
    path: str = Field(..., pattern=r"^/.*")

class Request(BaseModel):
    headers: Dict[str, str] = Field(default_factory=dict)
    query: Dict[str, object] = Field(default_factory=dict)
    body: Dict[str, object] = Field(default_factory=dict)

class Expected(BaseModel):
    http_status: int = Field(..., ge=100, le=599)
    body_contains: List[str] = Field(default_factory=list)
    error_code: Optional[str] = Field(default=None, pattern=r"^[A-Z_]+$")

class TestCase(BaseModel):
    id: str = Field(..., pattern=r"^TC-\d{4}$")
    title: str = Field(..., min_length=4)
    priority: Priority
    category: Category
    precondition: str = ""
    steps: List[str] = Field(..., min_length=2, max_length=30)
    request: Request
    expected: Expected

class CaseGenOutput(BaseModel):
    api: APIInfo
    testcases: List[TestCase] = Field(..., min_length=6)
```

**为什么先写 Schema（而不是先写 Prompt）？**
- QA 思维：先定义“可验收标准”，再让模型去满足它
- 工程效果：后续 Prompt 迭代时，你可以用这份 Schema 当回归门禁

---

### 3.2 Prompt：把“只输出 JSON”写成硬约束

```text
你是一名资深测试开发工程师（Test Dev）。

【任务】
根据输入的 API 契约信息，生成接口测试用例。

【强制输出格式】
1) 你只能输出 JSON（纯 JSON 文本），禁止输出 Markdown、代码块标记、解释性文字。
2) JSON 顶层必须只有两个字段：api、testcases。
3) 每条用例必须包含字段：id、title、priority、category、precondition、steps、request、expected。
4) 字段约束：
   - id 必须符合：TC-\d{4}
   - priority 只能是：P0/P1/P2
   - category 只能是：happy_path/boundary/negative/auth/idempotency/concurrency
   - steps 必须是数组，元素是字符串
   - expected.http_status 必须是 100~599
5) 用例必须覆盖：happy_path、boundary、negative、auth、idempotency。

【输入】
{{API_CONTRACT_JSON}}
```

这里已经混合使用了两类约束：
- **结构约束**：只能 JSON、顶层字段固定
- **Regex 约束**：`id` 必须 `TC-\d{4}`

---

### 3.3 校验与“自愈”：Pydantic 校验失败就触发修复回合

现实里最常见的失败不是“完全乱写”，而是 JSON 语法合法，但字段缺失/类型不对，或枚举写错（`P3`）。
因此推荐：**校验失败 → 让模型根据错误信息修复输出**。

```python
# file: generate_and_validate.py
import json
from case_schema import CaseGenOutput
from llm_client import call_llm_json

def validate_or_raise(output_str: str) -> CaseGenOutput:
    data = json.loads(output_str)
    return CaseGenOutput.model_validate(data)

def repair_prompt(bad_json: str, err: str) -> str:
    return f"""你之前输出的 JSON 不符合合同，请你只修复 JSON 本身，不要输出任何解释性文字。

【校验错误】\n{err}

【待修复 JSON】\n{bad_json}

【输出要求】
- 只能输出修复后的 JSON（纯 JSON 文本）
- 必须保持顶层字段 api/testcases
"""

def generate_cases(api_contract_json: str, base_prompt: str, max_repair: int = 1) -> CaseGenOutput:
    prompt = base_prompt.replace("{{API_CONTRACT_JSON}}", api_contract_json)
    out = call_llm_json(prompt)

    for _ in range(max_repair + 1):
        try:
            return validate_or_raise(out)
        except Exception as e:
            out = call_llm_json(repair_prompt(out, str(e)))

    raise RuntimeError("unreachable")
```

**QA 点评：为什么这是“工程化”的关键一步？**
- 你不再把 LLM 当成“必须一次成功的黑盒”
- 而是像对待不稳定依赖一样：给它错误信息 -> 让它自我修复 -> 直到满足合同

---

## 4. 工程实践补充：Go 侧如何接住（适合你们 Go 测试体系）

如果你们后端主要是 Go，建议至少做两层：
1) **JSON 能否 Unmarshal**（语法 + 字段类型基础）
2) **业务合同校验**（枚举/长度/覆盖）

```go
// file: casegen/contract_test.go
package casegen

import (
	"encoding/json"
	"os"
	"testing"
)

type Output struct {
	API struct {
		Name   string `json:"name"`
		Method string `json:"method"`
		Path   string `json:"path"`
	} `json:"api"`
	Testcases []struct {
		ID       string   `json:"id"`
		Priority string   `json:"priority"`
		Category string   `json:"category"`
		Expected struct {
			HTTPStatus int `json:"http_status"`
		} `json:"expected"`
	} `json:"testcases"`
}

func TestCaseGenContract(t *testing.T) {
	b, _ := os.ReadFile("../snapshots/day4_casegen.json")
	var out Output
	json.Unmarshal(b, &out)

	if len(out.Testcases) < 6 {
		t.Fatalf("want >= 6 cases, got %d", len(out.Testcases))
	}
    // ... 补充自定义枚举与范围断言 ...
}
```

---

## 5. 常见坑与 QA 对策（经验总结）

### 5.1 “只输出 JSON”仍然会失败，怎么办？
常见现象：模型输出 `Here is the JSON:` + JSON，或者用 ` ```json ` 包裹。
对策（从轻到重）：
1) **Prompt 强约束**：明确禁止解释、禁止代码块
2) **入口 Regex 过滤**：例如只截取第一个 `{` 到最后一个 `}`
3) **JSON Mode / Function Calling**：平台级约束
4) **修复回合（repair）**：把错误扔回模型让它改

### 5.2 你应该监控哪些指标？
把 LLM 输出质量做成可观测指标：
- `json_parse_success_rate`：JSON 解析成功率
- `schema_valid_rate`：Schema 校验成功率
- `repair_needed_rate`：需要修复回合的比例（越低越好）
- `required_category_coverage_rate`：必选类别覆盖率

---

## 6. 课后小思考（建议写进你的学习资产）

1. 在你的业务里，哪些 LLM 输出属于“必须可执行”的产物？测试用例？测试数据？SQL？发布单检查项？你会优先把哪一类纳入 **JSON Schema + 合同测试**？
2. 如果把这条流水线放进 CI：你会选择 **固定模型 + 回归 Prompt**，还是 **固定 Prompt + 回归模型**？哪个对你们团队更现实？

---

*（明日预告 Day 5：如何评测 Prompt 的稳定性？构建一个 Python/Go 的批量 Prompt 自动化测试脚本，让“回归”真正跑起来。）*
