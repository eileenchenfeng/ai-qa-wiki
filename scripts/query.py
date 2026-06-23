#!/usr/bin/env python3
"""Simple keyword search over wiki/ pages.

Score = title_hits*5 + tag_hits*3 + body_hits*1
"""
from __future__ import annotations
import os, sys, re, glob, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = os.path.join(ROOT, "wiki", "days")
OUT_DIR = os.path.join(ROOT, "demo_output")

def snippet(text: str, term: str, width: int = 80) -> str:
    idx = text.lower().find(term.lower())
    if idx < 0: return ""
    s = max(0, idx - width // 2); e = min(len(text), idx + width // 2)
    return "…" + text[s:e].replace("\n", " ") + "…"

def search(query: str, top_k: int = 5):
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
            score += tl_count(title.lower(), tl) * 5
            score += tl_count(tag_line.lower(), tl) * 3
            score += tl_count(tx, tl)
        if score > 0:
            snips = [snippet(text, t) for t in terms]
            snips = [s for s in snips if s][:2]
            results.append({"file": os.path.relpath(fp, ROOT), "title": title.lstrip("# ").strip(),
                            "score": score, "snippets": snips})
    results.sort(key=lambda x: -x["score"])
    return results[:top_k]

def tl_count(hay: str, needle: str) -> int:
    return hay.count(needle)

def main():
    if len(sys.argv) < 2:
        print("usage: query.py <keywords...> [--top N]"); sys.exit(1)
    args = sys.argv[1:]; top_k = 5
    if "--top" in args:
        i = args.index("--top"); top_k = int(args[i+1]); args = args[:i] + args[i+2:]
    q = " ".join(args)
    res = search(q, top_k)

    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = re.sub(r"[^\w]+", "_", q)[:40]
    out_path = os.path.join(OUT_DIR, f"query_{stamp}_{fname}.md")

    md = [f"# Query: `{q}`\n", f"- 时间：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}",
          f"- Top-K：{top_k} · 命中：{len(res)}\n", "## 结果\n"]
    print(f"\n🔍 Query: {q}\n" + "=" * 60)
    if not res:
        print("(no hits)"); md.append("_无命中_")
    for i, r in enumerate(res, 1):
        line = f"{i}. [score={r['score']}] {r['title']}\n   → {r['file']}"
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
