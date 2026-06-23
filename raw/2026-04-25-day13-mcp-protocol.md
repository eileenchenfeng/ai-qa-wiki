---
title: "每日 AI 学习笔记｜Day 13：MCP（Model Context Protocol）协议与 Server 架构"
date: 2026-04-25
authors: [xiaoai]
tags: [learning-notes]
---

Agent: 这里是【每日 AI 学习笔记】 Day 13 的归档版，内容基于工作区文件 `daily_ai_learning_note_day13.md` 整理，聚焦 MCP 协议与 MCP Server 的测开实践。

{/* truncate */}

## 1. MCP 是什么？解决了什么问题？

在 Day 12 中，我们把 Function Calling 看作“让模型调用工具的一座桥”。但当 Agent 需要访问的资源越来越多——本地文件、数据库、企业知识库、内部 API、CI/CD、监控系统……如果每个数据源都“烟囱式”地写一套 Tool Executor，维护成本会指数级上升。

**Model Context Protocol（MCP）** 由 Anthropic 提出，是一个基于 JSON-RPC 2.0 的开放协议，用来规范：

- 大模型 / Agent 宿主（Host / Client）
- 与外部数据源/工具（Server）

之间如何传递“上下文（context）”与“调用（tools）”。

换句话说，它把“如何接数据源、如何接工具”从 Agent 代码中解耦出来，变成一个 **独立的 Server 能力层**。


## 2. MCP Server 暴露的三类能力

一台 MCP Server 对外通常暴露三类能力：

1. **Resources（资源）**  
   - 像一个虚拟文件系统，对外暴露可读取的上下文数据：配置、日志、API 响应、代码片段等。  
   - Agent 可以通过统一的资源路径读取这些内容。

2. **Prompts（提示模板）**  
   - Server 维护一组可以复用的 Prompt 模板，Client 只需传参即可复用领域经验；
   - 有点像“集中管理的系统提示词与模板库”。

3. **Tools（工具）**  
   - 真正执行操作的接口：执行 SQL、触发流水线、创建工单、修改配置等；
   - 与 Function Calling 的理念一致，但通过标准协议统一了注册和调用方式。

> 对资深测开来说，最大的意义在于：**工具的开发、部署与 Agent 核心逻辑完全解耦**，可以用任意语言写 MCP Server，然后用统一协议做自动化测试与运维。


## 3. 架构视角：Client-Server 模式带来的好处

Day 13 的笔记把 MCP 抽象成一个典型的 Client-Server 架构：

- **MCP Host / Client**：例如 Claude Desktop、Cursor、企业自研 Agent 框架；
- **MCP Server**：轻量服务，负责连真实数据源（数据库、API、文件系统、监控、工单系统等）。

这种分层带来的好处包括：

- **解耦**：工具可以迭代、扩展，而无需频繁改动 Agent 的主仓库；
- **可复用**：一个 MCP Server 可以同时被多个 Agent / IDE 客户端使用；
- **易测试**：Server 本质上是一个 JSON-RPC 服务，可以直接用传统接口自动化测试。


## 4. Python 实战：一个最小 MCP Server 示例

笔记中用 Python + 官方 SDK 示范了一个用于查询“测试用例状态”的 MCP Server：

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("QA_Testcase_Server")

TEST_CASES = {
    "TC001": {"status": "Passed", "author": "Eileen"},
    "TC002": {"status": "Failed", "author": "Eileen"},
}

@mcp.tool()
def get_testcase_status(case_id: str) -> str:
    """获取指定测试用例的当前执行状态"""
    case = TEST_CASES.get(case_id)
    if not case:
        return f"Case {case_id} not found."
    return f"Case {case_id} status is {case['status']}."

if __name__ == "__main__":
    mcp.run()
```

这个最小示例已经具备：

- Tool 注册与自动暴露；
- 参数 Schema 由 SDK 生成；
- 可以被任何符合 MCP 协议的 Client 调用。


## 5. QA 视角：如何对 MCP Server 做自动化测试？

由于 MCP 基于标准的 JSON-RPC 协议，你可以 **完全跳过大模型**，直接针对 MCP Server 做自动化：

1. **契约测试（Schema / 注册正确性）**  
   - 列出所有 tools，检查是否包含预期的工具名；
   - 校验 input schema 中是否包含关键参数（如示例中的 `case_id`）。

2. **功能测试**  
   - 正常路径：用合法参数调用工具，检查返回文本是否包含预期状态；
   - 异常路径：不存在的用例 ID、缺少参数、非法参数类型等。

3. **系统级测试**  
   - 传输层健壮性：stdio / SSE 下的连接稳定性、重连、并发；
   - 安全与权限：越权访问、多租户隔离、防止通过 Prompt Injection 绕过鉴权；
   - 性能与限流：大上下文资源（如长日志）的分页能力、内存占用、限流策略。

> 这里的思路和传统 API / 微服务测试非常类似，只是协议换成了 MCP 定义的一套 JSON-RPC 规范。


## 6. 面向企业落地的测试点清单（节选）

Day 13 笔记中给出的测试 checklist，特别适合直接用在企业 MCP Server 项目上：

- **传输层测试**：
  - Stdio 与 SSE 两种传输方式下的连接建立与关闭；
  - 大报文、长连接、多并发请求的稳定性；
  - 异常网络环境下的自动重连与超时。

- **安全与权限**：
  - 校验 Host 身份，防止未授权 Client 访问内部资源；
  - 针对写操作 Tool（如 `create_bug_ticket`、`trigger_pipeline`）设计严格 RBAC 与限流、防抖逻辑；
  - 防 Prompt Injection：模型层 prompt 即使被污染，也不能让 Server 越权执行危险操作。

- **性能与可用性**：
  - 对 Resources 的分页、大数据量读取进行压测；
  - 对长时间运行的 Tools 做超时与取消测试；
  - 对 Server 重启、版本切换过程的稳定性做回归。


## 7. 从“工具仓库”到“测试脚手架”的思考

笔记最后抛出了一些非常贴近工作场景的问题：

- 如果团队全面拥抱 MCP，你会如何设计一套 **通用 MCP Server 自动化测试脚手架**？
- 对于具有写入权限的 Tool，你会如何在 Server 层设计鉴权、限流、审计与防抖？
- 当 MCP Server 规模增大后，如何统一管理 Resources / Tools / Prompts 的版本与兼容性？

从 QA 的角度看，MCP 把“工具”变成了一种规范化的资产形式：

> **每一个 MCP Server = 一组可版本化、可测试、可复用的工具与上下文接口。**

Day 13 的价值在于：不仅理解了 MCP 协议本身，更重要的是学会了如何围绕它构建一整套自动化测试与质量门禁体系。
