# AI QA Wiki · Demo Readme

> Karpathy LLM Wiki 模式的 ai-qa 落地 demo。把过去 69 天 `ai-qa-learning-site` Day N 博客，
> 从「线性日记」升级为「主题知识网 + 关键词检索」。

## ✅ Demo 已跑通的成果

| 维度 | 数量 / 路径 |
|---|---|
| Raw 摄入 | **69** 篇 Day N 博客 → `raw/` |
| 浓缩 Day 页 | **69** 篇 → `wiki/days/day-XX-*.md` |
| 主题聚合页 | **125** 个（按 tag 聚合）→ `wiki/topics/*.md` |
| 总索引 | `index.md`（Top 主题 + 时间线双视图） |
| 查询脚本 | `scripts/query.py "<keyword>" --top N` |
| 查询快照 | `demo_output/query_*.md`（3 条已跑） |
| 摄入日志 | `log.md` |
| 操作手册 | `AGENTS.md` |

## 🚀 复现命令

```bash
cd ai-qa-wiki
# 1) 摄入（已执行过；如改了 raw/ 再跑）
python3 scripts/ingest.py
# 2) 查询示例
python3 scripts/query.py "RAG 评测"      --top 3
python3 scripts/query.py "chaos 混沌"    --top 3
python3 scripts/query.py "多租户隔离"    --top 3
```

## 🔍 已跑 Query 示例（命中 Top1）

| Query | Top1 命中 | Score |
|---|---|---|
| `RAG 评测` | Day 09 RAG 评测体系（RAGAS） | 24 |
| `chaos 混沌` | Day 67 AI Agent 混沌工程（ChaosMesh） | 24 |
| `多租户隔离` | Day 52 多租户隔离与工作空间边界测试 | 6 |

## 🧭 与 Karpathy 模式的对应

| Karpathy LLM Wiki | 本 demo 实现 |
|---|---|
| `AGENTS.md` 操作约定 | `AGENTS.md` |
| `raw/` 原始素材只读 | `raw/`（拷贝自 blog） |
| `wiki/` 浓缩 + 反向链接 | `wiki/days/` + `wiki/topics/` |
| Ingest pipeline | `scripts/ingest.py`（解析 front-matter + callout + 要点 + tag-graph） |
| Query | `scripts/query.py`（TF + 标题/标签加权打分） |
| Log | `log.md`（追加写） |

## 🌱 后续可扩展（非本次 demo 范围）

1. 把 `query.py` 升级为 **embedding 向量检索**（OpenAI / bge-m3 + faiss）。
2. 把 `topic` 页顶部综述用 LLM 自动 draft → 人工 review。
3. 起独立 GitHub repo `ai-qa-wiki`，CI 增量摄入：每次 `ai-qa-learning-site` 新博客合入，自动 PR 一次 wiki 更新。
4. 接入飞书：把 `wiki/topics/<tag>.md` 同步到飞书 Wiki，支持团队检索。
