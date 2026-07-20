#!/usr/bin/env python3
"""Queue the approved draft to LinkedIn via Buffer's GraphQL API.

Runs automatically in GitHub Actions when a drafts/<date> PR is merged,
or locally for testing:
  BUFFER_API_KEY=... BUFFER_CHANNEL_ID=... python3 scheduler/publish_buffer.py --ref drafts/2026-07-21

Which option gets posted is controlled by content/drafts/<date>/selected.txt
(edit it in the PR before merging; defaults to option-1-technical).

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
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENDPOINT = "https://api.buffer.com"


def create_post(text, channel_id, api_key):
    # values inlined via json.dumps for safe GraphQL string escaping
    query = (
        "mutation { createPost(input: {"
        f"text: {json.dumps(text)}, "
        f"channelId: {json.dumps(channel_id)}, "
        "schedulingType: automatic, mode: addToQueue"
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

    sel_file = draft_dir / "selected.txt"
    selected = sel_file.read_text().strip() if sel_file.exists() else "option-1-technical"
    post = draft_dir / f"{selected}.md"
    if not post.exists():
        sys.exit(f"selected file {post.name} not found in {draft_dir}")

    resp = create_post(post.read_text().strip(), channel, api_key)
    if resp.get("errors"):
        sys.exit(f"buffer graphql errors: {json.dumps(resp['errors'])[:500]}")
    result = resp.get("data", {}).get("createPost", {})
    if "post" in result:
        due = result["post"].get("dueAt", "next queue slot")
        print(f"queued to LinkedIn via Buffer: {selected} from {date} (due {due})")
    else:
        sys.exit(f"buffer rejected the post: {result.get('message', json.dumps(resp)[:500])}")


if __name__ == "__main__":
    main()
