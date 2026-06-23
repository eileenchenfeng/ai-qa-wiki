#!/usr/bin/env python3
"""Hybrid search over wiki/ pages.

Modes:
  --mode vector   (default) FAISS semantic search on wiki/index/
  --mode keyword  legacy keyword scoring (title*5 + tag*3 + body)
  --mode hybrid   vector score (×100) + keyword score, merged

Usage:
  python3 scripts/query.py 多租户隔离
  python3 scripts/query.py "Prompt Injection 红队" --top 5 --mode hybrid
"""
from __future__ import annotations
import os, sys, re, glob, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = os.path.join(ROOT, "wiki", "days")
IDX  = os.path.join(ROOT, "wiki", "index")
OUT_DIR = os.path.join(ROOT, "demo_output")


# ---------- keyword path (legacy) ----------
def _snippet(text: str, term: str, width: int = 80) -> str:
    idx = text.lower().find(term.lower())
    if idx < 0: return ""
    s = max(0, idx - width // 2); e = min(len(text), idx + width // 2)
    return "…" + text[s:e].replace("\n", " ") + "…"


def keyword_search(query: str, top_k: int = 5):
    terms = [t for t in re.split(r"\s+", query.strip()) if t]
    results = []
    for fp in sorted(glob.glob(os.path.join(DAYS, "*.md"))):
        with open(fp, encoding="utf-8") as f:
            text = f.read()
        lines = text.splitlines()
        title = lines[0] if lines else ""
        tag_line = next((l for l in lines[:6] if "标签" in l), "")
        score = 0
        for t in terms:
            tl = t.lower(); tx = text.lower()
            score += title.lower().count(tl) * 5
            score += tag_line.lower().count(tl) * 3
            score += tx.count(tl)
        if score > 0:
            snips = [s for s in (_snippet(text, t) for t in terms) if s][:2]
            results.append({"file": os.path.relpath(fp, ROOT),
                            "title": title.lstrip("# ").strip(),
                            "score": float(score), "snippets": snips})
    results.sort(key=lambda x: -x["score"])
    return results[:top_k]


# ---------- vector path ----------
_VEC_CACHE = {}
def _load_vector():
    if _VEC_CACHE: return _VEC_CACHE
    import faiss
    from sentence_transformers import SentenceTransformer
    model_name = open(os.path.join(IDX, "model.txt")).read().strip()
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    model = SentenceTransformer(model_name)
    index = faiss.read_index(os.path.join(IDX, "faiss.index"))
    meta  = json.load(open(os.path.join(IDX, "meta.json"), encoding="utf-8"))
    _VEC_CACHE.update(model=model, index=index, meta=meta, model_name=model_name)
    return _VEC_CACHE


def vector_search(query: str, top_k: int = 5):
    c = _load_vector()
    emb = c["model"].encode([query], normalize_embeddings=True,
                            convert_to_numpy=True).astype("float32")
    D, I = c["index"].search(emb, top_k)
    out = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0: continue
        m = c["meta"][idx]
        out.append({"file": m["file"], "title": m["title"],
                    "score": float(score), "snippets": [m.get("preview", "")[:160]]})
    return out


def hybrid_search(query: str, top_k: int = 5):
    v = {r["file"]: r for r in vector_search(query, top_k * 2)}
    k = {r["file"]: r for r in keyword_search(query, top_k * 2)}
    files = set(v) | set(k)
    merged = []
    for f in files:
        vr = v.get(f); kr = k.get(f)
        score = (vr["score"] * 100 if vr else 0) + (kr["score"] if kr else 0)
        base = vr or kr
        merged.append({"file": f, "title": base["title"], "score": round(score, 2),
                       "snippets": (vr or kr)["snippets"]})
    merged.sort(key=lambda x: -x["score"])
    return merged[:top_k]


# ---------- CLI ----------
def main():
    args = sys.argv[1:]
    if not args:
        print("usage: query.py <keywords...> [--top N] [--mode vector|keyword|hybrid]"); sys.exit(1)
    top_k = 5; mode = "hybrid"
    if "--top" in args:
        i = args.index("--top"); top_k = int(args[i+1]); args = args[:i] + args[i+2:]
    if "--mode" in args:
        i = args.index("--mode"); mode = args[i+1]; args = args[:i] + args[i+2:]
    q = " ".join(args)
    fn = {"vector": vector_search, "keyword": keyword_search, "hybrid": hybrid_search}[mode]
    res = fn(q, top_k)

    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = re.sub(r"[^\w]+", "_", q)[:40]
    out_path = os.path.join(OUT_DIR, f"query_{mode}_{stamp}_{fname}.md")

    md = [f"# Query: `{q}`  · mode=`{mode}`\n",
          f"- 时间：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}",
          f"- Top-K：{top_k} · 命中：{len(res)}\n", "## 结果\n"]
    print(f"\n🔍 [{mode}] Query: {q}\n" + "=" * 60)
    if not res:
        print("(no hits)"); md.append("_无命中_")
    for i, r in enumerate(res, 1):
        line = f"{i}. [score={r['score']:.3f}] {r['title']}\n   → {r['file']}"
        print(line)
        md.append(f"### {i}. {r['title']}  · score={r['score']}\n")
        md.append(f"- 路径：`{r['file']}`")
        for s in r["snippets"]:
            print(f"   ▸ {s}"); md.append(f"- 片段：{s}")
        md.append("")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"\n💾 结果已落盘：{os.path.relpath(out_path, ROOT)}")


if __name__ == "__main__":
    main()
