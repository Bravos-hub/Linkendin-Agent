#!/usr/bin/env python3
"""Open (or update) a GitHub PR with today's drafts. Merging the PR = approval.

Usage:
  export GITHUB_TOKEN=<pat with repo scope>
  python3 scheduler/open_pr.py [--date YYYY-MM-DD]

Flow: create branch drafts/<date> -> commit content/drafts/<date>/ -> push -> open PR.
If a PR for the branch already exists, the new commit is simply added to it.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def git(*args, check=True):
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def api(method, url, token, payload=None):
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        data=json.dumps(payload).encode() if payload is not None else None,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read() or b"{}"), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}"), e.code


def load_repo():
    with open(ROOT / "config" / "schedule.yaml") as f:
        cfg = yaml.safe_load(f)
    repo = cfg.get("approval", {}).get("repo", "")
    if not repo or "/" not in repo:
        sys.exit("set approval.repo in config/schedule.yaml (e.g. Bravos-hub/Linkendin-Agent)")
    return repo.split("/", 1)


def pr_body(draft_dir):
    parts = [
        "## Today's LinkedIn posts",
        "",
        "Review the posts below. **Merging this PR approves all of them and schedules them to LinkedIn via Buffer at 4-hour intervals** (post-1 at the first `post_times` slot, and so on).",
        "",
        "**To drop a post:** delete its `post-N.md` file in this PR before merging.",
        "Edit posts inline before merging, or close the PR to discard.",
        "",
    ]
    for f in sorted(draft_dir.glob("*.md")):
        text = f.read_text().strip()
        preview = text[:600] + ("..." if len(text) > 600 else "")
        parts += [f"<details><summary><b>{f.name}</b></summary>", "", preview, "", "</details>", ""]
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=f"{datetime.now():%Y-%m-%d}")
    date = ap.parse_args().date

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("export GITHUB_TOKEN=<personal access token with repo scope>")

    draft_dir = ROOT / "content" / "drafts" / date
    if not draft_dir.is_dir() or not any(draft_dir.iterdir()):
        sys.exit(f"no drafts found at {draft_dir} - run the generation step first")

    owner, repo = load_repo()
    branch = f"drafts/{date}"

    git("checkout", "-B", branch)
    git("add", f"content/drafts/{date}")
    status = git("status", "--porcelain", f"content/drafts/{date}")
    if status:
        git("commit", "-m", f"drafts: LinkedIn content for {date}")
    git("push", "-u", "origin", branch)
    git("checkout", "main")

    body, code = api("POST", f"https://api.github.com/repos/{owner}/{repo}/pulls", token, {
        "title": f"Drafts for {date} - approve by merging",
        "head": branch,
        "base": "main",
        "body": pr_body(draft_dir),
    })
    if code == 201:
        print(f"PR opened: {body['html_url']}")
    elif code == 422:
        existing, _ = api("GET", f"https://api.github.com/repos/{owner}/{repo}/pulls?head={owner}:{branch}&state=open", token)
        if existing:
            print(f"PR already open, new commit added: {existing[0]['html_url']}")
        else:
            sys.exit(f"github rejected the PR: {body}")
    else:
        sys.exit(f"github API error {code}: {body}")


if __name__ == "__main__":
    main()
