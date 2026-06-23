#!/usr/bin/env python3
"""Build site manifest.json for the static wiki front-end.

Scans wiki/days/ + wiki/topics/, extracts title/tags/preview, writes manifest.json
at repo root for the SPA (index.html) to consume.
"""
from __future__ import annotations
import os, json, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS_DIR   = os.path.join(ROOT, "wiki", "days")
TOPICS_DIR = os.path.join(ROOT, "wiki", "topics")
OUT = os.path.join(ROOT, "manifest.json")

LLM_DRAFT_RE = re.compile(r"<!--\s*LLM-DRAFT:BEGIN\s*-->\s*(.*?)\s*<!--\s*LLM-DRAFT:END\s*-->", re.S)
HUMAN_RE = re.compile(r"<!--\s*HUMAN-REVIEWED:BEGIN\s*-->\s*(.*?)\s*<!--\s*HUMAN-REVIEWED:END\s*-->", re.S)


def parse_day(fp: str):
    text = open(fp, encoding="utf-8").read()
    lines = text.splitlines()
    title = (lines[0] if lines else "").lstrip("# ").strip()
    date = ""
    tags = []
    for l in lines[:8]:
        if "📅" in l:
            m = re.search(r"(\d{4}-\d{2}-\d{2})", l); date = m.group(1) if m else ""
        if "🏷️" in l or "标签" in l:
            payload = re.sub(r"^[^:：]*[:：]", "", l).strip()
            tags = [t.strip() for t in re.split(r"[,，]", payload) if t.strip()]
    preview = re.sub(r"^#.*\n", "", text, count=1)
    preview = re.sub(r"^- (📅|🏷️|📄).*\n", "", preview, flags=re.M)
    preview = preview.strip()[:280].replace("\n", " ")
    return {"path": os.path.relpath(fp, ROOT).replace("\\", "/"),
            "title": title, "date": date, "tags": tags, "preview": preview}


def parse_topic(fp: str):
    text = open(fp, encoding="utf-8").read()
    name = os.path.splitext(os.path.basename(fp))[0]
    entries = re.findall(r"\*\*(Day\s*\d+)\*\*", text)
    n = len(entries)
    m = HUMAN_RE.search(text) or LLM_DRAFT_RE.search(text)
    summary = (m.group(1).strip() if m else "")[:400]
    return {"path": os.path.relpath(fp, ROOT).replace("\\", "/"),
            "name": name, "count": n, "summary": summary}


def main():
    days = sorted([parse_day(p) for p in glob.glob(os.path.join(DAYS_DIR, "*.md"))],
                  key=lambda x: x["path"])
    topics = sorted([parse_topic(p) for p in glob.glob(os.path.join(TOPICS_DIR, "*.md"))],
                    key=lambda x: -x["count"])
    manifest = {
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "days": days,
        "topics": topics,
        "counts": {"days": len(days), "topics": len(topics),
                   "topics_with_summary": sum(1 for t in topics if t["summary"])},
    }
    json.dump(manifest, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✓ manifest.json: {len(days)} days, {len(topics)} topics, "
          f"{manifest['counts']['topics_with_summary']} with LLM summary")


if __name__ == "__main__":
    main()
