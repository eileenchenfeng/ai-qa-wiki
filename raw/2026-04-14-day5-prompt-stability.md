---
title: "每日 AI 学习笔记｜Day 5：如何评测 Prompt 的稳定性？"
date: 2026-04-14
authors: [xiaoai]
tags: [learning-notes]
---

Agent: 今天推进到 **Day 5：如何评测 Prompt 的稳定性？**（已完成 Day 1~Day 4）。

{/* truncate */}


我已按“核心理论 + 测开工程实践(含 Python/Go) + 课后思考”整理好完整学习笔记（见下文）。

---

# 每日 AI 学习笔记｜Day 5：如何评测 Prompt 的稳定性？

> 日期：2026-04-14（周二）  
> 学习计划来源：`AI_QA_Learning_Plan.md`  
> 进度判断：已完成 Day 1~Day 4，今日推进至 **Day 5**。

---

## 0. 今天你要带走的 3 件事（学习目标）

1. **把“Prompt 稳定性”说清楚**：稳定性不是“输出永远一模一样”，而是“在可控波动下，关键质量属性保持一致”。
2. **把稳定性变成可度量指标**：从“感觉不稳定”升级成“指标掉了 12%”。
3. **做一个最小可用的 Prompt 回归框架**：能批量跑、能产出报告、能卡门禁（CI / 提交前检查）。

---

## 1. 核心理论知识讲解：什么是 Prompt 稳定性？

### 1.1 为什么同一个 Prompt 会输出不一样？（不稳定的来源）

#### A. 模型解码的随机性（Stochastic Decoding）
- `temperature` 越高，采样越“放飞”，结果越容易发散。
- `top_p` / `top_k` 会限制候选 token 范围，但仍可能有随机采样。
- 部分模型/网关支持 `seed`，但并非所有场景真正可复现。

#### B. 系统环境的非确定性（System Non-determinism）
即使 temperature=0，也可能因为：
- 模型版本/路由升级（同一个 endpoint 背后换了模型）
- 系统 Prompt 变更（平台侧“看不见”的提示词）
- RAG 检索结果波动（召回顺序、分词、向量库更新）
- 工具调用返回变化（时间、网络、外部服务数据）

测开视角一句话：**Prompt 稳定性评测，本质是把 AI 的不确定性收敛到可测范围内。**

---

### 1.2 “稳定性”到底评什么？（建议拆成 3 个层次）

| 层次 | 关注点 | 典型问题 | QA 可落地指标 |
|---|---|---|---|
| 格式稳定 | 能不能被机器解析/消费 | JSON 解析失败、字段缺失 | `json_parse_success_rate`、`schema_valid_rate` |
| 语义稳定 | 意思是否一致 | 同类需求输出用例覆盖差异大 | embedding 相似度、关键断言覆盖率 |
| 决策稳定 | 关键结论是否一致 | 同一策略建议忽左忽右 | 结论标签一致率、majority vote 一致率 |

工程建议：
- **格式稳定**：尽量逼近 100%（否则自动化无法接）。
- **语义/决策稳定**：允许波动，但用阈值管理（例如 embedding ≥0.85）。

---

### 1.3 如何定义“相似输入”？（用例设计关键）

常见方法：
1. **同义改写**：含义不变（最常用）
2. **噪声注入**：加入口头禅/无关句/标点
3. **结构变体**：列表 vs 段落
4. **边界相似**：只改一个关键参数，看输出是否合理变化

把“相似输入集”当作 **Prompt 的回归测试集**（地位≈ UI 自动化关键路径用例集）。

---

### 1.4 稳定性怎么量化？（指标清单）

（1）结构/可解析类（强烈推荐作为第一道门禁）
- JSON 解析成功率
- Schema 校验通过率
- 必填字段完整率（如 `title/steps/expected`）

（2）文本一致性类（轻量）
- 编辑距离、Jaccard 等

（3）语义一致性类（更贴近真实质量）
- Embedding cosine similarity（推荐）
- LLM-as-a-Judge（后续会系统讲）

（4）多次采样稳定性（同一输入跑 n 次）
- Majority vote 一致率
- Pass@k（探索式生成常用）

---

## 2. 测开视角的工程实践：Prompt 稳定性批测（Python + Go）

### 2.1 测试对象示例：生成结构化测试用例 JSON
评测重点：
1) 能不能解析（JSON/Schema）  
2) 相似输入下语义是否一致（建议 embedding；此处给轻量示例）  
3) 关键断言点是否稳定（如“鉴权失败/参数校验/幂等性”）

---

### 2.2 测试数据（建议 6~10 条起步）

```json
{
  "id": "login_001",
  "base_input": "登录接口：手机号+验证码登录。验证码5分钟有效，输错5次锁定10分钟。",
  "variants": [
    "用户通过手机号和短信验证码登录，验证码有效期5分钟，错误次数达到5次后锁10分钟。",
    "登录：手机号验证码；验证码 5min 过期；连续输错 5 次 -> 10min 冻结。",
    "【需求】手机号验证码登录（5分钟有效），错误5次锁10分钟。请生成测试用例。"
  ],
  "must_have_keywords": ["验证码过期", "输错次数", "锁定"]
}
```

---

### 2.3 Python：批量跑 + Schema 校验（可直接扩展到 embedding）

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
import json

from pydantic import BaseModel, Field, ValidationError

class TestCase(BaseModel):
    title: str
    steps: List[str]
    expected: List[str]

class TestCaseSet(BaseModel):
    cases: List[TestCase] = Field(min_length=1)

def call_llm(prompt: str) -> str:
    # TODO: 替换成你实际的模型调用（HTTP/SDK）
    raise NotImplementedError

def parse_and_validate(raw: str) -> TestCaseSet:
    obj = json.loads(raw)
    return TestCaseSet.model_validate(obj)

@dataclass
class RunResult:
    ok_parse: bool
    ok_schema: bool
    raw: str
    error: str | None = None

def run_prompt_stability_case(prompt_template: str, inputs: List[str], runs_per_input: int = 3) -> Dict[str, Any]:
    results: Dict[str, List[RunResult]] = {}
    for x in inputs:
        key = x[:30] + ("..." if len(x) > 30 else "")
        results[key] = []
        for _ in range(runs_per_input):
            prompt = prompt_template.format(requirement=x)
            try:
                raw = call_llm(prompt)
                _ = parse_and_validate(raw)
                results[key].append(RunResult(True, True, raw))
            except json.JSONDecodeError as e:
                results[key].append(RunResult(False, False, raw if 'raw' in locals() else "", f"json error: {e}"))
            except ValidationError as e:
                results[key].append(RunResult(True, False, raw, f"schema error: {e}"))
            except Exception as e:
                results[key].append(RunResult(False, False, raw if 'raw' in locals() else "", f"unknown error: {e}"))

    total = sum(len(v) for v in results.values())
    parse_ok = sum(1 for v in results.values() for r in v if r.ok_parse)
    schema_ok = sum(1 for v in results.values() for r in v if r.ok_schema)

    return {
        "total_runs": total,
        "json_parse_success_rate": parse_ok / max(1, total),
        "schema_valid_rate": schema_ok / max(1, total),
        "fail_samples": [
            {"input": k, "error": r.error, "raw": r.raw[:300]}
            for k, v in results.items()
            for r in v
            if not r.ok_schema
        ][:10],
    }
```

工程化落地（适合你们 ArkClaw/HTL 流程）：
- 用 `pytest.parametrize` 批量跑；
- 每次 raw 输出落盘（用于回放与 diff）；
- CI 门禁示例：
  - `schema_valid_rate >= 0.98`
  - “must-have 关键字”覆盖率 ≥ 0.90

---

### 2.4 Go：把 Prompt 稳定性纳入 CI（门禁风格）

```go
package prompttest

import (
    "encoding/json"
    "testing"
)

type TestCase struct {
    Title    string   `json:"title"`
    Steps    []string `json:"steps"`
    Expected []string `json:"expected"`
}

type TestCaseSet struct {
    Cases []TestCase `json:"cases"`
}

func CallLLM(prompt string) (string, error) {
    // TODO: 替换为真实调用（HTTP/SDK）
    return "", nil
}

func TestPromptSchemaStability(t *testing.T) {
    prompt := "你是资深测试开发...（省略）"

    raw, err := CallLLM(prompt)
    if err != nil {
        t.Fatalf("llm call failed: %v", err)
    }

    var set TestCaseSet
    if err := json.Unmarshal([]byte(raw), &set); err != nil {
        t.Fatalf("json parse failed: %v\nraw=%s", err, raw)
    }

    if len(set.Cases) == 0 {
        t.Fatalf("no cases generated")
    }

    for i, c := range set.Cases {
        if c.Title == "" || len(c.Steps) == 0 || len(c.Expected) == 0 {
            t.Fatalf("case[%d] invalid: %+v", i, c)
        }
    }
}
```

---

### 2.5 不写代码也能做：稳定性测试用例设计模板
1) 同义改写一致性（5 变体）  
2) 噪声鲁棒性（口头禅/无关句）  
3) 边界扰动合理性（只改一个参数）  
4) 结构门禁（JSON+Schema）  
5) 稳定性阈值（embedding 均值/方差 或 majority vote）

---

## 3. 课后小思考

1. 稳定性阈值怎么定？你更偏“保守”还是“敏感”？  
2. “语义一致但覆盖点不同”算不算不稳定？在 ArkClaw/HTL 的质量目标下你更希望哪种？  
3. 模型升级导致输出变化：更新金标（Golden）还是先卡住？是否需要“人工审核开关”？  
4. 对你当前负责的系统，优先保证：格式稳定 / 语义稳定 / 决策稳定？为什么？

---

明天预告（Day 6）：**Embedding 与相似度计算**（把“语义一致”彻底量化落地）。
