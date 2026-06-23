# 主题：`Skill`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 Skill 作为 Agent 可调用能力单元的开发范式与编排机制，核心问题在于如何将松散的 Prompt 与工具调用沉淀为可注册、可版本化、可被多 Agent 复用的标准化技能，并解决技能选择、参数填充与执行链路的可观测性问题。可复用的工程实践包括：以 JSON Schema 约束 Skill 入参与结构化输出、通过 Manifest 注册与语义检索（FAISS 等向量索引）完成技能路由、用 Ginkgo 等 BDD 框架对单技能与编排链路做契约测试，以及借助 Playwright 模拟前端触发端到端验证。对 QA 工作的启发是：应将每个 Skill 视为独立被测单元，建立"单技能契约测试 + 编排回归测试"双层用例库，并在 CI 中接入 Schema 校验与调用轨迹断言，避免 Agent 升级后出现静默的技能漂移。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-04-28

## 时间线

- **Day 14** · 2026-04-28 · [每日 AI 学习笔记｜Day 14：Skill 技能的开发与编排机制](../days/day-14-day14-skill-development-and-orchestration.md)