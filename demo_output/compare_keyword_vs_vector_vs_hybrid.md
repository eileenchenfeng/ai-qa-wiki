# Query Comparison: keyword vs vector vs hybrid

- 时间：2026-06-23
- 模型：`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384d, cn/en)
- 索引：FAISS IndexFlatIP（cosine），69 篇浓缩页
- 备注：首选模型为 `BAAI/bge-m3`，因当前沙箱 HF 网络受限，回退使用 MiniLM 多语言模型；切换模型只需 `AIQAWIKI_MODEL=BAAI/bge-m3 python3 scripts/build_index.py` 重建即可。

## 三个示例查询对比

### Q1：`多租户隔离`

| 模式 | Top-1 | Top-2 | Top-3 |
|---|---|---|---|
| keyword | Day 52（6） | Day 48（1） | – |
| vector | Day 20（0.091） | Day 52（0.086） | Day 63（0.071） |
| **hybrid** | **Day 52（14.58）** | Day 20（9.06） | Day 63（7.05） |

说明：keyword 召回偏窄（只有 2 条），纯 vector 把 Day 20「多 Agent 协作」排到了 Day 52「多租户隔离」前面；**hybrid 把语义召回与关键词强信号合并，Day 52 稳居 Top-1**。

### Q2：`Prompt Injection 红队测试`

| 模式 | Top-1 | Top-2 | Top-3 |
|---|---|---|---|
| keyword | Day 68（28） | Day 53（17） | Day 43（14） |
| vector | Day 54（0.185） | Day 64（0.181） | Day 36（0.173） |
| **hybrid** | **Day 68（28.00）** | Day 54（18.47） | Day 64（18.12） |

说明：keyword 在术语完全命中时仍非常强；vector 给出了 Day 54 / 36 这类「未直接出现术语但语义相关」的补召回。hybrid 保住了 Day 68，又把语义近邻补进 Top-3。

### Q3：`长任务 checkpoint 恢复`

| 模式 | Top-1 | Top-2 | Top-3 |
|---|---|---|---|
| keyword | Day 61（33） | Day 50（16） | Day 41（7） |
| vector | Day 61（0.188） | Day 41（0.186） | Day 63（0.179） |
| **hybrid** | **Day 61（51.75）** | Day 50（33.5） | Day 41（25.57） |

说明：三模式 Top-1 一致；hybrid 综合后排序更稳。

## 结论

- 单独使用 vector：召回扩展性好，但短查询/术语场景下容易让相关性更弱的文档冒头。
- 单独使用 keyword：术语命中时极准，但词典覆盖差时召回不足（如 Q1 只命中 2 条）。
- **Hybrid 是当前最佳默认模式**（已设为 `query.py` 默认 `--mode hybrid`），既能保住关键词强信号，又能补语义近邻。

后续如需进一步提升：切换到 `BAAI/bge-m3`（更强的中英双语模型）只需重建索引即可，无需改 `query.py`。
