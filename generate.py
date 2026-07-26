#!/usr/bin/env python3
"""Headless draft generation via the Kimi API — no interactive session needed.

Usage:
  export KIMI_API_KEY=sk-...
  python3 generate.py [--date YYYY-MM-DD]

Reads voice.md + prompts + today's research brief, calls the Kimi chat API,
and writes the drafts to content/drafts/<date>/ exactly like the skill would.
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

ROOT = Path(__file__).resolve().parent


def build_system_prompt():
    parts = []
    for p in ["skills/linkedin-content-agent/SKILL.md", "config/voice.md",
              "prompts/linkedin_post.md", "prompts/carousel.md", "prompts/image_prompt.md"]:
        parts.append(f"===== {p} =====\n{(ROOT / p).read_text()}")
    return "\n\n".join(parts)


def parse_files(text):
    """Split model output on '=== filename ===' marker lines."""
    files, current, buf = {}, None, []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("=== ") and s.endswith(" ==="):
            if current:
                files[current] = "\n".join(buf).strip()
            current, buf = s[4:-4].strip(), []
        elif current is not None:
            buf.append(line)
    if current:
        files[current] = "\n".join(buf).strip()
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=f"{datetime.now():%Y-%m-%d}")
    date = ap.parse_args().date

    key = os.environ.get("KIMI_API_KEY")
    if not key:
        sys.exit("export KIMI_API_KEY=sk-... (or put it in .env)")

    sched = yaml.safe_load((ROOT / "config" / "schedule.yaml").read_text())
    gen = sched.get("generation", {})
    base = gen.get("base_url", "https://api.moonshot.ai/v1").rstrip("/")
    model = gen.get("model", "kimi-k2-0711-preview")

    brief = ROOT / "research" / "briefs" / f"{date}.md"
    if not brief.exists():
        subprocess.run([sys.executable, str(ROOT / "research" / "fetch_trends.py")], check=False)
        subprocess.run([sys.executable, str(ROOT / "research" / "rank_topics.py")], check=False)
    if not brief.exists():
        sys.exit("no research brief available for today")

    weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%a").lower()
    is_carousel = weekday in sched.get("posting_cadence", {}).get("carousel_days", [])

    required = ["post-1.md", "post-2.md", "post-3.md", "post-4.md",
                "image-prompt.md", "meta.md"] + (["carousel.md"] if is_carousel else [])
    user_msg = (
        f"Today is {date} ({weekday}).\n"
        f"Carousel day: {'yes — also produce carousel.md' if is_carousel else 'no — skip the carousel'}.\n\n"
        f"Here is today's research brief:\n\n{brief.read_text()}\n\n"
        "Follow the workflow exactly (steps 1-6; skip the interactive PR/report steps). "
        "Write one post per story, numbered in posting order. "
        "Output ONLY the files, each introduced by a marker line in this exact format:\n"
        "=== post-1.md ===\n<file content>\n=== post-2.md ===\n<file content>\n"
        f"Files required: {', '.join(required)}"
    )

    payload = {
        "model": model,
        "temperature": 0.7,
        "max_tokens": 8192,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": user_msg},
        ],
    }
    req = urllib.request.Request(
        f"{base}/chat/completions", method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        data=json.dumps(payload).encode())
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            resp = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Kimi API error {e.code}: {e.read().decode()[:500]}")

    text = resp["choices"][0]["message"]["content"]
    files = parse_files(text)
    if not files:
        sys.exit("could not parse files from model output:\n" + text[:500])

    outdir = ROOT / "content" / "drafts" / date
    outdir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        safe = name.replace("/", "_")
        (outdir / safe).write_text(content + "\n")
        print(f"wrote {outdir / safe}")
    missing = [f for f in required if f not in files]
    if missing:
        print(f"warn: missing expected files: {', '.join(missing)}")
    print("done - next: python3 scheduler/open_pr.py")


if __name__ == "__main__":
    main()
