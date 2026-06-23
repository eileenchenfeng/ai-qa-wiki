# 主题：`timeout`

- 共 **1** 篇笔记 · 最近更新：2026-06-15

## 时间线

- **Day 61** · 2026-06-15 · [每日 AI 学习笔记｜Day 61：AI Agent 超时控制、取消传播与 Checkpoint 恢复测试](../days/day-61-day61-agent-timeout-cancellation-checkpoint-recovery-testing.md)
  > 对 AI Agent 来说，很多高风险故障并不是“执行失败”，而是**任务该停的时候没停、该取消的时候没取消、worker 重启后不知道从哪继续**。一次长任务可能同时经历模型推理、工具调用、异步轮询、文件上传、审批回调和前端状态刷新；如果…