#!/usr/bin/env python3
"""List merged draft PRs (approved content) and sync them locally.

A merged drafts/<date> PR means: approved, ready to post manually.
Run any time:  python3 scheduler/check_approved.py
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_repo():
    with open(ROOT / "config" / "schedule.yaml") as f:
        cfg = yaml.safe_load(f)
    repo = cfg.get("approval", {}).get("repo", "")
    if not repo or "/" not in repo:
        sys.exit("set approval.repo in config/schedule.yaml")
    return repo.split("/", 1)


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("export GITHUB_TOKEN=<personal access token with repo scope>")
    owner, repo = load_repo()

    req = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls?state=closed&per_page=50",
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"},
    )
    with urllib.request.urlopen(req) as resp:
        pulls = json.loads(resp.read())

    approved = [p for p in pulls if p.get("merged_at") and p["head"]["ref"].startswith("drafts/")]
    if not approved:
        print("no approved drafts yet — merge a drafts/<date> PR to approve content")
        return

    subprocess.run(["git", "-C", str(ROOT), "pull", "--ff-only"], capture_output=True)
    print("Approved and ready to post (newest first):\n")
    for p in approved[:10]:
        date = p["head"]["ref"].split("/", 1)[1]
        folder = ROOT / "content" / "drafts" / date
        local = "on disk" if folder.is_dir() else "run: git pull"
        print(f"  {date}  merged {p['merged_at'][:10]}  ({local})")
        print(f"    {p['html_url']}")
    print("\nPost manually from content/drafts/<date>/ — pick one option, publish, done.")


if __name__ == "__main__":
    main()
