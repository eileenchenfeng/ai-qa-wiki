# 主题：`workspace-security`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦 AI Agent 从单用户场景升级为多租户协作平台后所引入的工作空间安全隔离问题，核心关注点不在功能正确性，而在于跨租户串数据、跨会话串上下文、跨工作空间误调用工具以及越权访问文件与长期记忆等高危缺陷。可复用的工程实践是将隔离边界结构化建模为 tenant_id、workspace_id、session_id、resource_owner、tool_scope、memory_namespace、task_owner 七类可验证对象，并以 Ginkgo 驱动后端隔离链路 E2E、Python/API 层做鉴权契约与越权回归、Playwright 模拟用户视角切换工作空间、K8s 演练多副本缓存漂移一致性。对 QA 的启发是：测试用例设计需从"我能访问我的数据"反转为"我绝不能访问别人的数据"，并在 CI 中固化一套跨租户越权回归集，将隔离断言下沉到缓存与异步任务归属层。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-06

## 时间线

- **Day 52** · 2026-06-06 · [每日 AI 学习笔记｜Day 52：AI Agent 多租户隔离与工作空间边界测试](../days/day-52-day52-agent-multi-tenant-isolation-workspace-boundary-testing.md)
  > 当 AI Agent 从“单用户助手”升级为“团队协作平台能力”后，最容易被低估、但一旦出事就最严重的质量问题，不是回答不准，而是 **跨租户串数、跨会话串上下文、跨工作空间误执行工具、越权访问文件或记忆**。高质量测试必须把多租户安全拆成…