# 主题：`tenant-isolation`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦于 AI Agent 从单用户助手演进为多租户协作平台后所面临的隔离安全问题，核心关注点不在于回答准确性，而在于跨租户串数、跨会话串上下文、跨工作空间误调用工具、越权访问文件与记忆等结构性风险。可复用的工程实践是将隔离边界结构化建模为 tenant_id、workspace_id、session_id、resource_owner、tool_scope、memory_namespace、task_owner 七类可验证对象，并组合使用 Ginkgo 串联后端隔离链路 E2E、Python/API 覆盖鉴权契约与越权回归、Playwright 验证用户视角的工作空间切换、K8s 演练多副本缓存漂移与一致性。对 QA 落地的启发是：测试设计应从"用户能访问自己的数据"反转为"任何路径都不得触达他人数据"，并把审计留痕与异步任务归属纳入回归基线，避免隔离漏洞在缓存与后台链路中悄然下沉。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-06

## 时间线

- **Day 52** · 2026-06-06 · [每日 AI 学习笔记｜Day 52：AI Agent 多租户隔离与工作空间边界测试](../days/day-52-day52-agent-multi-tenant-isolation-workspace-boundary-testing.md)
  > 当 AI Agent 从“单用户助手”升级为“团队协作平台能力”后，最容易被低估、但一旦出事就最严重的质量问题，不是回答不准，而是 **跨租户串数、跨会话串上下文、跨工作空间误执行工具、越权访问文件或记忆**。高质量测试必须把多租户安全拆成…