#!/usr/bin/env python3
"""Daily orchestrator for the LinkedIn AI Content Agent.

Phase 1-2 behavior:
  1. fetch_trends  -> research/raw/YYYY-MM-DD.json
  2. rank_topics   -> research/briefs/YYYY-MM-DD.md
  3. print the Kimi Code command that runs the generation skill
     (generation itself is LLM work — it happens in Kimi Code,
      guided by skills/linkedin-content-agent/SKILL.md)

Cron entry (crontab -e):
  0 7 * * * cd /path/to/linkedin-agent && python3 main.py >> logs/daily.log 2>&1
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(step):
    print(f"== {Path(step).name} ==")
    result = subprocess.run([sys.executable, str(ROOT / step)], capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(result.returncode)


def main():
    run("research/fetch_trends.py")
    run("research/rank_topics.py")
    print("\nNext: open Kimi Code in this directory and say:")
    print('  "run the linkedin agent"')


if __name__ == "__main__":
    main()
