#!/usr/bin/env python3
"""Schedule the approved drafts to LinkedIn via Buffer's GraphQL API.

Runs automatically in GitHub Actions when a drafts/<date> PR is merged,
or locally for testing:
  BUFFER_API_KEY=... BUFFER_CHANNEL_ID=... python3 scheduler/publish_buffer.py --ref drafts/2026-07-21

Every post-*.md file in the drafts folder is scheduled at the matching
post_times slot from config/schedule.yaml (post-1 -> first slot, etc.),
at 4-hour intervals. Delete a post file in the PR before merging to skip
that slot.

API notes (beta): key from https://publish.buffer.com/settings/api
The API cannot edit/delete created posts, and media upload is unreliable —
posts go out text-only for now.
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parent.parent
ENDPOINT = "https://api.buffer.com"


def load_schedule():
    with open(ROOT / "config" / "schedule.yaml") as f:
        cfg = yaml.safe_load(f)
    tz = ZoneInfo(cfg.get("timezone", "UTC"))
    times = cfg.get("posting_cadence", {}).get("post_times", [])
    if not times:
        sys.exit("set posting_cadence.post_times in config/schedule.yaml")
    return tz, times


def create_post(text, channel_id, api_key, due_at):
    # values inlined via json.dumps for safe GraphQL string escaping
    query = (
        "mutation { createPost(input: {"
        f"text: {json.dumps(text)}, "
        f"channelId: {json.dumps(channel_id)}, "
        f"dueAt: {json.dumps(due_at)}, "
        "schedulingType: automatic, mode: customScheduled"
        "}) { ... on PostActionSuccess { post { id dueAt } } ... on MutationError { message } } }"
    )
    req = urllib.request.Request(
        ENDPOINT,
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps({"query": query}).encode(),
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"buffer API error {e.code}: {e.read().decode()[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="", help="e.g. drafts/2026-07-21")
    args = ap.parse_args()

    api_key = os.environ.get("BUFFER_API_KEY") or sys.exit("BUFFER_API_KEY missing")
    channel = os.environ.get("BUFFER_CHANNEL_ID") or sys.exit("BUFFER_CHANNEL_ID missing")

    date = args.ref.split("/", 1)[1] if "/" in args.ref else (args.ref or f"{datetime.now():%Y-%m-%d}")
    draft_dir = ROOT / "content" / "drafts" / date
    if not draft_dir.is_dir():
        sys.exit(f"no drafts at {draft_dir}")

    posts = sorted(draft_dir.glob("post-*.md"))
    if not posts:
        sys.exit(f"no post-*.md files found in {draft_dir}")

    tz, times = load_schedule()
    if len(posts) > len(times):
        sys.exit(f"{len(posts)} posts but only {len(times)} post_times configured")

    now = datetime.now(tz)
    for post, slot in zip(posts, times):
        local_dt = datetime.fromisoformat(f"{date}T{slot}").replace(tzinfo=tz)
        # late approval: roll past slots forward to the same time on a future day
        while local_dt <= now:
            local_dt += timedelta(days=1)
        due_at = local_dt.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
        resp = create_post(post.read_text().strip(), channel, api_key, due_at)
        if resp.get("errors"):
            sys.exit(f"buffer graphql errors: {json.dumps(resp['errors'])[:500]}")
        result = resp.get("data", {}).get("createPost", {})
        if "post" in result:
            print(f"scheduled {post.name} from {date} (due {result['post'].get('dueAt', due_at)})")
        else:
            sys.exit(f"buffer rejected {post.name}: {result.get('message', json.dumps(resp)[:500])}")


if __name__ == "__main__":
    main()
