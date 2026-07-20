#!/usr/bin/env python3
"""Rank fetched stories by niche relevance and recency; emit a research brief.

Usage: python3 research/rank_topics.py [path-to-raw.json]
Output: research/briefs/YYYY-MM-DD.md
"""
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def score(story):
    text = (story["title"] + " " + story["summary"]).lower()
    kw_hits = sum(1 for kw in story.get("keywords", []) if kw.lower() in text)
    recency = 1.0
    if story.get("published"):
        age_h = (datetime.now(timezone.utc) - datetime.fromisoformat(story["published"])).total_seconds() / 3600
        recency = math.exp(-age_h / 36)  # half-life ~25h
    return kw_hits * 2 + recency


def main():
    raw_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        ROOT / "research" / "raw" / f"{datetime.now():%Y-%m-%d}.json")
    stories = json.loads(raw_path.read_text())
    if not stories:
        sys.exit("no stories to rank — run fetch_trends.py first (try --days 2)")

    ranked = sorted(stories, key=score, reverse=True)
    top, runners_up = ranked[0], ranked[1:6]

    brief_dir = ROOT / "research" / "briefs"
    brief_dir.mkdir(parents=True, exist_ok=True)
    brief = brief_dir / f"{datetime.now():%Y-%m-%d}.md"
    lines = [
        f"# Research brief — {datetime.now():%Y-%m-%d}",
        f"Track: {top['track']}",
        "",
        "## Top story",
        f"**{top['title']}**",
        f"Source: {top['source']} — {top['link']}",
        "",
        top["summary"],
        "",
        "## Runners-up (use only if the top story is unusable)",
    ]
    lines += [f"- [{s['title']}]({s['link']}) — {s['source']}" for s in runners_up]
    brief.write_text("\n".join(lines))
    print(f"brief -> {brief}\ntop story: {top['title']}")


if __name__ == "__main__":
    main()
