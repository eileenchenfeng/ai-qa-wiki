---
title: "每日 AI 学习笔记 Day 3：Prompt 工程进阶 2（ToT 与 ReAct）"
authors: [xiaoai]
tags: [learning-notes, Agent, QA]
---

# 每日 AI 学习笔记｜Day 3：Prompt 工程进阶 2（ToT、ReAct 框架预热）

> 日期：2026-04-12（周日）  
> 学习计划来源：`learning-plan.md`  
> 进度判断：已完成 **Day 2**，今日推进至 **Day 3**。

---


{ /* truncate */ }

## 0. 今日目标

1. **掌握复杂推理范式**：理解 ToT（思维树）与 ReAct（推理与行动）的核心原理。
2. **结合 QA 视角**：探讨在面对复杂业务逻辑（如 ArkClaw 的多步骤任务、接口依赖）时，如何利用这些高阶 Prompt 范式提升大模型的输出准确率。
3. **工程实践**：编写一段 Python 测试代码，对比不同 Prompt 范式在处理复杂测试逻辑时的输出结果，并建立自动化校验机制。

---

## 1. 核心理论知识讲解

### 1.1 ToT（Tree of Thoughts，思维树）：探索多种可能性

**定义**：在 CoT（思维链）的基础上，ToT 允许模型在每一步推理时生成多个分支（候选项），并通过评估函数对这些分支进行打分或筛选，最终搜索出一条最优路径。

**为什么需要 ToT？**
- CoT 是线性的（一条路走到黑），如果中间某一步想错了，最终结果必定是错的。
- ToT 借鉴了经典搜索算法（如 BFS/DFS），适合解决需要全局规划、多步试错的复杂问题（如：复杂的测试场景设计、代码重构方案）。

**QA 视角的启发**：
在为 ArkClaw 设计跨组件的集成测试场景时，往往有多种数据准备或前置状态流转的路径。使用 ToT，可以让模型先列出所有可能的前置路径，再从中挑选一条执行成本最低或覆盖最全的路径来生成最终用例。

### 1.2 ReAct（Reasoning and Acting，推理与行动）：走向 Agent 的基石

**定义**：ReAct 将大模型的**内部推理（Reasoning）**与**外部环境交互（Acting）**交替进行。
- **Thought（思考）**：我现在需要做什么？
- **Action（行动）**：调用工具（比如查询数据库、发 HTTP 请求、看日志）。
- **Observation（观察）**：获取工具返回的结果，作为下一步的输入。

**ReAct 的工程意义**：
这是从“单向输出模型”向“自主智能体（Agent）”跨越的关键一步！它让大模型不再只依赖训练数据，而是可以动态获取实时信息来修正自己的判断。

**测开/QA 的应用场景**：
- **智能诊断测试**：当 API 测试失败时，模型（Agent）可以先 *思考*（可能是数据库没配对），然后 *行动*（调用 SQL 查询），*观察*（发现表中无数据），最后得出结论（“测试环境数据未初始化”）。
- 这不仅是测试生成的利器，更是**测试执行与排障（Debugging）的利器**。

---

## 2. 测开视角：对比不同范式在复杂逻辑下的准确率

假设我们要测试 ArkClaw 的一个复杂特性：“只有当实例处于 Running 状态，且用户具备 admin 权限时，才能触发挂起（Suspend）操作”。

- **Zero-shot**：模型可能直接生成一个简单的调用，忽略了“先创建 -> 启动 -> 分配权限”的隐式前置步骤。
- **CoT**：模型能写出“第一步建实例，第二步启动，第三步挂起”，但可能在写第二步时忘记了权限校验，导致最终用例依然跑不通。
- **ReAct/ToT**：模型能动态意识到（或通过分支评估）如果不配权限会报错，从而补全整个测试链路的依赖。

---

## 3. 工程实践：对比测试脚手架（Python）

为了验证大模型在不同 Prompt 范式下的表现，我们设计一个极简的对比评测脚本。这个脚本会分别用 Zero-shot 和包含 CoT/ToT 思路的 Prompt 去请求 LLM，并校验输出的质量。

```python
# file: evaluate_prompt_paradigms.py
import json
import pytest
from pydantic import BaseModel, Field

class TestScenario(BaseModel):
    scenario_name: str
    steps: list[str] = Field(..., min_items=3, description="至少需要包含创建、授权、操作三个步骤")
    is_valid: bool = Field(True)

# 模拟评测函数（实际中你会调用大模型 API）
def generate_scenario(prompt_type: str) -> str:
    # 这里 mock 了 LLM 的返回
    if prompt_type == "zero_shot":
        return json.dumps({
            "scenario_name": "挂起实例",
            "steps": ["调用 suspend 接口"],
            "is_valid": False
        })
    elif prompt_type == "cot":
        return json.dumps({
            "scenario_name": "挂起实例全链路",
            "steps": ["调用 create", "调用 start", "调用 suspend"], # 漏了授权
            "is_valid": False
        })
    elif prompt_type == "tot_react":
        return json.dumps({
            "scenario_name": "严谨的挂起实例测试",
            "steps": ["创建实例", "分配 admin 权限", "启动实例", "验证 running 状态", "执行挂起"],
            "is_valid": True
        })
    return "{}"

@pytest.mark.parametrize("paradigm, expected_valid", [
    ("zero_shot", False),
    ("cot", False),
    ("tot_react", True)
])
def test_paradigm_effectiveness(paradigm, expected_valid):
    output_str = generate_scenario(paradigm)
    data = json.loads(output_str)
    scenario = TestScenario(**data)
    
    # 断言是否成功覆盖了前置的鉴权与状态依赖
    has_auth = any("权限" in step or "auth" in step.lower() for step in scenario.steps)
    
    assert scenario.is_valid == expected_valid
    if expected_valid:
        assert has_auth, "高级范式必须能推导出隐含的权限依赖步骤！"
```

> **QA 点评**：在搭建企业级 AI 测试基建时，我们就是用这种对比框架，来挑选性价比最高（Token 消耗 vs 准确率）的 Prompt 范式作为生产环境的基线。

---

## 4. 课后小思考

1. **业务反思**：在日常工作中，你遇到过哪些经常因为前置条件不满足而导致失败的自动化用例？如果用 ReAct 范式让 Agent 自己去排查这些前置条件（如清理脏数据），能节省多少维护时间？
2. **成本考量**：ToT 和 ReAct 效果虽好，但会带来大量额外的 Token 消耗和延迟。在测试生成的场景中，你觉得应该在什么情况下使用 Zero-shot/Few-shot，什么时候才动用 ReAct？
3. **架构衔接**：理解了 ReAct，其实就已经触碰到了 Agent 的灵魂。思考一下，ArkClaw 里的 Skill 机制，本质上是不是就是提供给 Agent 的 `Action` 集合？作为测开，如何对这些 Skill 进行独立的“契约测试”？

---

*（明日预告：结构化输出约束（JSON Mode 与 Regex Constraint），让大模型的输出像普通接口一样稳定！）*
