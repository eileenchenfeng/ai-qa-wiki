# 主题：`config-drift`

## 主题综述（LLM 自动起草）

<!-- LLM-DRAFT:BEGIN -->
本主题聚焦 AI Agent 在生产环境中因 Prompt 模板热更新、工具 schema 变更、特征开关分租户不一致、ConfigMap/Secret 滚动不完整、灰度包与后端版本错位等导致的配置漂移与环境一致性缺口，揭示了大量"模型变笨"类事故的真正根因并非代码逻辑而是配置面失控。可复用的工程实践包括：以 Ginkgo 对后端关键配置快照与能力矩阵做契约式断言、用 Python 与 API Testing 做配置 diff 与基线比对、借 Playwright 在多配置下回归用户可见行为、以 Kubernetes 声明式固化环境并通过定时任务巡检漂移。对 QA 的启发是：质量门禁需从"接口成功率"扩展到配置、依赖、特征开关与模型路由的可观测可断言范围，并在 CI 中引入"线上配置快照 vs 验证基线"的强制比对，确保任何一次发布都能明确回答当前线上究竟跑着哪一套配置。
<!-- LLM-DRAFT:END -->

- 共 **1** 篇笔记 · 最近更新：2026-06-12

## 时间线

- **Day 58** · 2026-06-12 · [每日 AI 学习笔记｜Day 58：AI Agent 配置漂移检测与环境一致性测试](../days/day-58-day58-agent-config-drift-environment-parity-testing.md)
  > 很多 AI Agent 线上事故，表面看像“模型变笨了”“工具突然不可用了”“同一条用例今天过、明天挂”，但真正根因并不是代码逻辑本身，而是 **配置漂移（Config Drift）** 和 **环境不一致（Environment Pari…