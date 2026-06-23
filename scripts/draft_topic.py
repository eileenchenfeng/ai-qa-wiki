#!/usr/bin/env python3
"""LLM-draft a 150-200 字 Chinese 综述 (overview) for topic pages.

For each `wiki/topics/<topic>.md`:
  1. Parse the linked day pages from the timeline section.
  2. Read each day page, extract title + first ~500 chars (key points).
  3. Call an OpenAI-compatible chat API to draft a 150-200 字 中文综述.
  4. Insert/replace the draft between markers under "## 主题综述（LLM 自动起草）".

Idempotent: re-running on the same topic replaces the previous draft.

Usage:
  python3 scripts/draft_topic.py agent.md security.md ...
  python3 scripts/draft_topic.py --all          # all 125 topics
  python3 scripts/draft_topic.py --top 5        # top-5 topics by entry count

Env:
  OPENAI_BASE_URL  (default: $OPENAI_BASE_URL)
  OPENAI_API_KEY   (default: $OPENAI_API_KEY)
  AIQAWIKI_DRAFT_MODEL  (default: ep-m-20260526121005-57m8t, falls back to $AIME_MODEL)
"""
from __future__ import annotations
import os, sys, re, json, glob, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "wiki", "topics")
DAYS_DIR   = os.path.join(ROOT, "wiki", "days")

BASE = os.environ.get("OPENAI_BASE_URL", "").rstrip("/")
KEY  = os.environ.get("OPENAI_API_KEY", "")
MODEL_PRIMARY = os.environ.get("AIQAWIKI_DRAFT_MODEL", "ep-m-20260526121005-57m8t")
MODEL_FALLBACK = os.environ.get("AIME_MODEL", "")

BEGIN = "<!-- LLM-DRAFT:BEGIN -->"
END   = "<!-- LLM-DRAFT:END -->"
SECTION_HEADING = "## 主题综述（LLM 自动起草）"

PROMPT_TMPL = """你是一名资深 AI 测试开发工程师，正在为内部知识库的「主题聚合页」起草顶部综述。

主题：`{topic}`
该主题下共 {n} 篇笔记，标题与要点摘要如下：

{bullets}

请用 **简体中文**、**150-200 字**、**一段话**（不要换行、不要分点、不要 Markdown 标题），完成以下 3 件事：
1. 概括这些笔记共同关注的核心问题；
2. 提炼跨笔记可复用的关键测试方法 / 工程实践 / 技术栈关键词；
3. 给出 1-2 条该主题对 QA 工作的启发或落地建议。
要求：行文专业克制，避免空话与套话，可以出现具体的工具名（Ginkgo / Playwright / FAISS 等）。直接输出综述正文，不要写"综述："等前缀。"""


def parse_topic_links(topic_path: str):
    """Return list of (day_label, day_file_relpath_from_topic) from timeline."""
    text = open(topic_path, encoding="utf-8").read()
    # lines like: - **Day 65** · 2026-06-19 · [title](../days/day-65-xxx.md)
    pat = re.compile(r"\*\*(Day\s*\d+)\*\*.*?\[(.*?)\]\((\.\./days/[^)]+)\)")
    return [(m.group(1), m.group(2), m.group(3)) for m in pat.finditer(text)]


def extract_day_brief(day_md_path: str, max_chars: int = 500) -> str:
    if not os.path.exists(day_md_path): return ""
    text = open(day_md_path, encoding="utf-8").read()
    # strip leading H1 + meta block, take next ~max_chars chars
    body = re.sub(r"^#.*\n", "", text, count=1)
    body = re.sub(r"^- 📅.*\n|^- 🏷️.*\n|^- 📄.*\n", "", body, flags=re.M)
    body = body.strip()
    return body[:max_chars].replace("\n", " ").strip()


def call_llm(prompt: str) -> str:
    if not BASE or not KEY:
        raise RuntimeError("OPENAI_BASE_URL / OPENAI_API_KEY not set")
    last_err = None
    for model in [m for m in [MODEL_PRIMARY, MODEL_FALLBACK] if m]:
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 600,
            "temperature": 0.5,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {KEY}",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
            content = data["choices"][0]["message"]["content"].strip()
            return content
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            last_err = f"{model}: HTTP {e.code} {body[:200]}"
            print(f"  [llm] {last_err}", flush=True)
            continue
        except Exception as e:
            last_err = f"{model}: {e}"
            print(f"  [llm] {last_err}", flush=True)
            continue
    raise RuntimeError(f"all models failed: {last_err}")


def draft_topic(topic_file: str) -> bool:
    topic_path = os.path.join(TOPICS_DIR, topic_file)
    if not os.path.exists(topic_path):
        print(f"  ✗ not found: {topic_file}"); return False
    topic = os.path.splitext(topic_file)[0]
    entries = parse_topic_links(topic_path)
    if not entries:
        print(f"  ⏭ {topic}: no entries"); return False

    bullets = []
    for day, title, rel in entries[:8]:  # cap to avoid context blow-up
        day_path = os.path.normpath(os.path.join(TOPICS_DIR, rel))
        brief = extract_day_brief(day_path)
        bullets.append(f"- {day}｜{title}\n  > {brief}")
    prompt = PROMPT_TMPL.format(topic=topic, n=len(entries), bullets="\n".join(bullets))

    print(f"  → {topic}: drafting (n={len(entries)})...", flush=True)
    summary = call_llm(prompt)
    summary = summary.strip().strip("`").strip()

    block = f"\n{SECTION_HEADING}\n\n{BEGIN}\n{summary}\n{END}\n"

    raw = open(topic_path, encoding="utf-8").read()
    if BEGIN in raw and END in raw:
        new_raw = re.sub(
            re.escape(SECTION_HEADING) + r".*?" + re.escape(END) + r"\n?",
            block.strip() + "\n", raw, count=1, flags=re.S)
    else:
        # insert after first H1 line
        lines = raw.splitlines(keepends=True)
        out, inserted = [], False
        for ln in lines:
            out.append(ln)
            if not inserted and ln.startswith("# "):
                out.append(block); inserted = True
        new_raw = "".join(out) if inserted else block + raw

    open(topic_path, "w", encoding="utf-8").write(new_raw)
    print(f"  ✓ {topic}: {len(summary)} chars written", flush=True)
    return True


def main():
    args = sys.argv[1:]
    targets = []
    if "--all" in args:
        targets = sorted(os.listdir(TOPICS_DIR))
    elif "--top" in args:
        i = args.index("--top"); k = int(args[i+1])
        scored = []
        for f in os.listdir(TOPICS_DIR):
            if not f.endswith(".md"): continue
            try:
                n = len(parse_topic_links(os.path.join(TOPICS_DIR, f)))
            except Exception:
                n = 0
            scored.append((n, f))
        scored.sort(reverse=True)
        targets = [f for _, f in scored[:k]]
        print("Top topics:", targets)
    else:
        targets = [a if a.endswith(".md") else a + ".md" for a in args]
    if not targets:
        print(__doc__); sys.exit(1)

    ok = 0
    for f in targets:
        try:
            if draft_topic(f): ok += 1
        except Exception as e:
            print(f"  ✗ {f}: {e}")
    print(f"\nDone: {ok}/{len(targets)} topics drafted.")


if __name__ == "__main__":
    main()
