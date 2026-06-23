# AGENTS.md｜AI QA Wiki 操作手册

> 灵感来源：Karpathy LLM Wiki 模式（https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f）
> 目标：把过去 69 天线性的 `ai-qa-learning-site` Day N 日记，升级为可检索、可回链、可演进的「AI 测开知识网」。

## 1. 目录约定

```
ai-qa-wiki/
├── AGENTS.md              # 本手册（人 + Agent 共同遵守）
├── index.md               # 知识网总索引（按主题域 + 时间线双视图）
├── log.md                 # 摄入/重写/查询日志（追加写）
├── raw/                   # 原始素材（从 ai-qa-learning-site/blog 拷贝，只读）
├── wiki/
│   ├── days/              # 每天一篇浓缩页（day-XX-slug.md）
│   └── topics/            # 主题聚合页（按 tag 聚合，含反向链接）
├── scripts/
│   ├── ingest.py          # raw/ → wiki/ 摄入器
│   └── query.py           # 关键词检索 demo
└── demo_output/           # 演示产物（查询结果快照）
```

## 2. 工作流（Agent 必读）

1. **Ingest（摄入）**：`python3 scripts/ingest.py`
   - 扫描 `raw/*.md`，解析 front-matter（title/date/tags）+ 核心总结 callout + 今日核心要点列表。
   - 输出到 `wiki/days/day-XX-<slug>.md`，每页结构固定：摘要 → 核心要点 → 关键概念 → 反向链接 → 原文路径。
   - 按 tag 聚合输出 `wiki/topics/<tag>.md`。
   - 追加一条记录到 `log.md`。
2. **Query（检索）**：`python3 scripts/query.py "<关键词>"`
   - 在 `wiki/` 上做关键词 + 标签匹配打分（TF + 标题加权 + tag bonus）。
   - 返回 Top-K 结果及 60 字命中片段，结果同时落盘到 `demo_output/`。
3. **Augment（增补）**：当某主题积累 ≥ 5 篇时，人或 Agent 在 `wiki/topics/<tag>.md` 顶部补一段「主题综述」（≤300 字），手动撰写不重新生成。

## 3. 写作风格

- 浓缩页 ≤ 200 行，去掉示例代码，只留**结论 + 链接**。
- 反向链接使用相对路径，例：`[Day 17 RAG 测试](../days/day-17-rag-testing.md)`。
- 主题页顶部必须有「最近更新」时间，便于一眼判断新鲜度。

## 4. 红线

- `raw/` 是只读快照，不得修改原文。
- 不引入企业敏感词：公司名 / 飞书内部域名 / 真实姓名。
- 任何重写都要在 `log.md` 追加一行（who / when / what / how-many-files）。
