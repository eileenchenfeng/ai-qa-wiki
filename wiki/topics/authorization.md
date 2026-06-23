# 主题：`authorization`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 在代替用户执行工具调用与数据访问时的授权失真风险，核心问题是 Agent 容易以系统身份的最大权限运行，而非用户被允许的最小权限，由此衍生出越权调用、原始数据泄露、绕过审批门禁等高风险缺陷，并与 Prompt Injection 形成叠加攻击面。可复用的测试方法包括用户身份透传与作用域约束校验、最小权限裁剪、审批门禁与执行审计的 E2E 验证，以及策略契约测试；技术栈层面常组合使用 Ginkgo 做后端授权链路校验、Python/API 层做策略契约断言、Playwright 验证前端审批与告知流程、K8s 做工作负载身份隔离。落地建议是将"用户身份—作用域—审批—审计"四段式校验沉淀为 Agent 类需求的准入基线，并在 CI 中针对每个新增工具调用强制补齐越权用例与注入对抗用例，避免授权回归被功能迭代淹没。
<!-- LLM-DRAFT:END -->

- 共 **2** 篇笔记 · 最近更新：2026-06-22

## 时间线

- **Day 45** · 2026-05-30 · [每日 AI 学习笔记｜Day 45：AI Agent 委托授权与最小权限测试](../days/day-45-day45-agent-delegated-authorization-least-privilege-testing.md)
  > AI Agent 一旦具备“代替用户调用工具、查询数据、执行动作”的能力，最危险的质量缺陷就不再只是回答不准，而是 **权限代理失真**：用户只有读权限，Agent 却借系统身份拿到了写能力；用户只能看摘要，Agent 却通过检索链路拿到了…
- **Day 68** · 2026-06-22 · [每日 AI 学习笔记｜Day 68：AI 安全测试（Prompt Injection / 越权 / 数据泄露）](../days/day-68-day68-agent-security-testing-prompt-injection-data-leakage.md)