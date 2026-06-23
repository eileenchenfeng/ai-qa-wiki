#!/usr/bin/env python3
"""Build a FAISS vector index over wiki/days/*.md using a multilingual SBERT model.

Default model: BAAI/bge-m3 (cn/en, 1024-dim). Override with env AIQAWIKI_MODEL.
Fallback: paraphrase-multilingual-MiniLM-L12-v2 (smaller, 384-dim).

Output (under wiki/index/):
  - faiss.index : cosine-similarity (IndexFlatIP on normalized vectors)
  - meta.json   : list of {file, title, tags, preview}
  - model.txt   : model name actually used
"""
from __future__ import annotations
import os, sys, json, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = os.path.join(ROOT, "wiki", "days")
OUT  = os.path.join(ROOT, "wiki", "index")
os.makedirs(OUT, exist_ok=True)

MODEL_NAME = os.environ.get("AIQAWIKI_MODEL", "BAAI/bge-m3")
FALLBACK   = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def parse_doc(fp: str):
    with open(fp, encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else os.path.basename(fp)
    tag_line = next((l for l in lines[:8] if "标签" in l or "tags" in l.lower()), "")
    tags = re.sub(r"^[^:：]*[:：]", "", tag_line).strip()
    # body for embedding: keep first ~2000 chars (浓缩页本身就短)
    body = text[:2000]
    embed_text = f"{title}\n{tags}\n{body}"
    return {
        "file": os.path.relpath(fp, ROOT),
        "title": title,
        "tags": tags,
        "preview": body[:240].replace("\n", " "),
    }, embed_text


def load_model(name: str):
    from sentence_transformers import SentenceTransformer
    print(f"[build_index] loading model: {name}", flush=True)
    return SentenceTransformer(name)


def main():
    files = sorted(glob.glob(os.path.join(DAYS, "*.md")))
    print(f"[build_index] {len(files)} docs under wiki/days/")
    metas, texts = [], []
    for fp in files:
        m, t = parse_doc(fp)
        metas.append(m); texts.append(t)

    try:
        model = load_model(MODEL_NAME)
        used = MODEL_NAME
    except Exception as e:
        print(f"[build_index] {MODEL_NAME} failed ({e}); falling back to {FALLBACK}")
        model = load_model(FALLBACK)
        used = FALLBACK

    import numpy as np, faiss
    embs = model.encode(texts, batch_size=8, show_progress_bar=True,
                        normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embs)

    faiss.write_index(index, os.path.join(OUT, "faiss.index"))
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(metas, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUT, "model.txt"), "w") as f:
        f.write(used + "\n")
    print(f"[build_index] ✅ saved {len(metas)} vectors (dim={dim}) using {used}")


if __name__ == "__main__":
    main()
