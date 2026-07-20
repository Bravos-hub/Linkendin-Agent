#!/usr/bin/env python3
"""Queue the approved draft to LinkedIn via Buffer.

Runs automatically in GitHub Actions when a drafts/<date> PR is merged,
or locally for testing:
  BUFFER_ACCESS_TOKEN=... BUFFER_PROFILE_ID=... python3 scheduler/publish_buffer.py --ref drafts/2026-07-21

Which option gets posted is controlled by content/drafts/<date>/selected.txt
(edit it in the PR before merging; defaults to option-1-technical).
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="", help="e.g. drafts/2026-07-21")
    args = ap.parse_args()

    token = os.environ.get("BUFFER_ACCESS_TOKEN") or sys.exit("BUFFER_ACCESS_TOKEN missing")
    profile = os.environ.get("BUFFER_PROFILE_ID") or sys.exit("BUFFER_PROFILE_ID missing")

    date = args.ref.split("/", 1)[1] if "/" in args.ref else (args.ref or f"{datetime.now():%Y-%m-%d}")
    draft_dir = ROOT / "content" / "drafts" / date
    if not draft_dir.is_dir():
        sys.exit(f"no drafts at {draft_dir}")

    sel_file = draft_dir / "selected.txt"
    selected = sel_file.read_text().strip() if sel_file.exists() else "option-1-technical"
    post = draft_dir / f"{selected}.md"
    if not post.exists():
        sys.exit(f"selected file {post.name} not found in {draft_dir}")

    text = post.read_text().strip()
    data = urllib.parse.urlencode({
        "profile_ids[]": profile,
        "text": text,
        "access_token": token,
    }).encode()
    req = urllib.request.Request("https://api.bufferapp.com/1/updates/create.json", data=data)
    with urllib.request.urlopen(req) as r:
        resp = json.loads(r.read())

    if resp.get("success"):
        print(f"queued to LinkedIn via Buffer: {selected} from {date}")
    else:
        sys.exit(f"buffer error: {json.dumps(resp)[:500]}")


if __name__ == "__main__":
    main()
