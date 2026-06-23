#!/usr/bin/env python3
"""Ingest raw Day-N blog posts into condensed wiki pages + topic pages.

Inspired by Karpathy's LLM Wiki pattern: turn a linear journal into a graph.
"""
from __future__ import annotations
import os, re, json, sys, glob, datetime
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
WIKI = os.path.join(ROOT, "wiki")
DAYS = os.path.join(WIKI, "days")
TOPICS = os.path.join(WIKI, "topics")
LOG = os.path.join(ROOT, "log.md")
INDEX = os.path.join(ROOT, "index.md")

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
CALLOUT_RE = re.compile(r"<callout[^>]*>\s*(.*?)\s*</callout>", re.S)
DAY_RE = re.compile(r"day(\d+)", re.I)
KEYPOINT_HEADER_RE = re.compile(r"^##+\s*(?:0\.\s*)?今日核心要点", re.M)
NUMBERED_RE = re.compile(r"^\s*\d+\.\s+(.+?)$", re.M)

def parse_front_matter(text: str) -> tuple[dict, str]:
    m = FM_RE.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",") if x.strip()]
        else:
            v = v.strip('"').strip("'")
        meta[k.strip()] = v
    return meta, text[m.end():]

def extract_core_summary(body: str) -> str:
    m = CALLOUT_RE.search(body)
    if not m:
        return ""
    raw = m.group(1)
    raw = re.sub(r"\*\*核心总结：\*\*\s*", "", raw)
    return raw.strip().replace("\n", " ")

def extract_keypoints(body: str) -> list[str]:
    m = KEYPOINT_HEADER_RE.search(body)
    if not m:
        return []
    chunk = body[m.end(): m.end() + 4000]
    chunk = chunk.split("\n## ")[0]
    pts = NUMBERED_RE.findall(chunk)
    return [re.sub(r"\*\*", "", p).strip().rstrip("。") for p in pts[:10]]

def slugify(path: str) -> str:
    base = os.path.basename(path).replace(".md", "")
    base = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", base)
    return base

def ingest():
    os.makedirs(DAYS, exist_ok=True)
    os.makedirs(TOPICS, exist_ok=True)
    files = sorted(glob.glob(os.path.join(RAW, "*day*.md")))
    pages = []
    topic_map: dict[str, list[dict]] = defaultdict(list)

    for fp in files:
        with open(fp, encoding="utf-8") as f:
            text = f.read()
        meta, body = parse_front_matter(text)
        title = meta.get("title", os.path.basename(fp))
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        date = str(meta.get("date", ""))
        dm = DAY_RE.search(os.path.basename(fp))
        day_num = int(dm.group(1)) if dm else 0

        summary = extract_core_summary(body)
        keypoints = extract_keypoints(body)
        slug = slugify(fp)

        page = {
            "day": day_num,
            "slug": slug,
            "title": title,
            "date": date,
            "tags": tags,
            "summary": summary,
            "keypoints": keypoints,
            "raw": os.path.relpath(fp, ROOT),
        }
        pages.append(page)
        for t in tags:
            topic_map[t].append(page)

    # write per-day wiki pages with backlinks (via shared tags)
    for p in pages:
        related = []
        for t in p["tags"]:
            for sibling in topic_map.get(t, []):
                if sibling["slug"] != p["slug"]:
                    related.append((sibling, t))
        seen = set(); uniq_related = []
        for s, t in related:
            if s["slug"] in seen: continue
            seen.add(s["slug"]); uniq_related.append((s, t))
        uniq_related = uniq_related[:8]

        out = []
        out.append(f"# Day {p['day']:02d}｜{p['title']}\n")
        out.append(f"- 📅 日期：{p['date']}")
        out.append(f"- 🏷️ 标签：{', '.join(p['tags'])}")
        out.append(f"- 📄 原文：[`{p['raw']}`](../../{p['raw']})\n")
        if p["summary"]:
            out.append("## 核心总结\n")
            out.append(p["summary"] + "\n")
        if p["keypoints"]:
            out.append("## 今日核心要点\n")
            for i, kp in enumerate(p["keypoints"], 1):
                out.append(f"{i}. {kp}")
            out.append("")
        if uniq_related:
            out.append("## 反向链接（同主题）\n")
            for s, t in uniq_related:
                out.append(f"- `[{t}]` → [Day {s['day']:02d} {s['slug']}](./day-{s['day']:02d}-{s['slug']}.md)")
            out.append("")
        out_path = os.path.join(DAYS, f"day-{p['day']:02d}-{p['slug']}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))

    # write topic pages
    for t, items in topic_map.items():
        items_sorted = sorted(items, key=lambda x: x["day"])
        safe = re.sub(r"[^\w\-]+", "_", t)
        lines = [f"# 主题：`{t}`\n",
                 f"- 共 **{len(items_sorted)}** 篇笔记 · 最近更新：{items_sorted[-1]['date']}\n",
                 "## 时间线\n"]
        for it in items_sorted:
            lines.append(f"- **Day {it['day']:02d}** · {it['date']} · [{it['title']}](../days/day-{it['day']:02d}-{it['slug']}.md)")
            if it["summary"]:
                lines.append(f"  > {it['summary'][:120]}…")
        with open(os.path.join(TOPICS, f"{safe}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # write index.md
    pages_sorted = sorted(pages, key=lambda x: x["day"])
    top_topics = sorted(topic_map.items(), key=lambda kv: -len(kv[1]))[:20]
    idx = ["# AI QA Wiki · 总索引\n",
           f"- 摄入时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
           f"- 浓缩页：**{len(pages_sorted)}** 篇 · 主题数：**{len(topic_map)}**\n",
           "## 🔥 Top 主题（按频次）\n"]
    for t, items in top_topics:
        safe = re.sub(r"[^\w\-]+", "_", t)
        idx.append(f"- [`{t}`](wiki/topics/{safe}.md) — {len(items)} 篇")
    idx.append("\n## 📅 时间线\n")
    for p in pages_sorted:
        idx.append(f"- **Day {p['day']:02d}** · {p['date']} · [{p['title']}](wiki/days/day-{p['day']:02d}-{p['slug']}.md)")
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write("\n".join(idx))

    # append log
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"- {datetime.datetime.now().isoformat(timespec='seconds')} · ingest · 解析 {len(pages)} 篇 raw → 生成 {len(pages)} 篇 days + {len(topic_map)} 个 topics\n")

    print(f"[ingest] {len(pages)} day-pages, {len(topic_map)} topic-pages → {WIKI}")

if __name__ == "__main__":
    ingest()
