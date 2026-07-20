#!/usr/bin/env python3
"""Fetch today's stories from the RSS feeds configured in config/niche.yaml.

Usage: python3 research/fetch_trends.py [--days 1]
Output: research/raw/YYYY-MM-DD.json
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import feedparser
except ImportError:
    sys.exit("pip install feedparser pyyaml  (then re-run)")

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    with open(ROOT / "config" / "niche.yaml") as f:
        return yaml.safe_load(f)


def today_track(cfg):
    weekday = datetime.now().strftime("%a").lower()
    rotation = cfg.get("weekly_rotation", {})
    choice = rotation.get(weekday, "primary")
    if choice == "primary":
        return cfg["primary_track"]
    for t in cfg.get("secondary_tracks", []):
        if choice in t["name"].lower().replace(" + ", "-").replace(" ", "-"):
            return t
    return cfg["primary_track"]


def fetch(feed_url, since):
    parsed = feedparser.parse(feed_url)
    items = []
    for e in parsed.entries:
        published = None
        for key in ("published_parsed", "updated_parsed"):
            if getattr(e, key, None):
                published = datetime(*getattr(e, key)[:6], tzinfo=timezone.utc)
                break
        if published and published < since:
            continue
        items.append({
            "title": e.get("title", "").strip(),
            "link": e.get("link", ""),
            "summary": e.get("summary", "")[:500],
            "published": published.isoformat() if published else None,
            "source": parsed.feed.get("title", feed_url),
        })
    return items


def main():
    days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 1
    cfg = load_config()
    track = today_track(cfg)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    stories = []
    for url in track.get("rss_feeds", []):
        try:
            stories.extend(fetch(url, since))
        except Exception as exc:  # one bad feed shouldn't kill the run
            print(f"warn: {url}: {exc}", file=sys.stderr)

    for story in stories:  # tag with the track for ranking
        story["track"] = track["name"]
        story["keywords"] = track["keywords"]

    out_dir = ROOT / "research" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{datetime.now():%Y-%m-%d}.json"
    out.write_text(json.dumps(stories, indent=2))
    print(f"{len(stories)} stories from track '{track['name']}' -> {out}")


if __name__ == "__main__":
    main()
