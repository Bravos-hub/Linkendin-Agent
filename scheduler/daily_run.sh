#!/usr/bin/env bash
# Daily 7 AM run: research -> generate -> open approval PR.
# Cron: 0 7 * * * cd /home/delta/Linkendin-Agent && bash scheduler/daily_run.sh >> logs/daily.log 2>&1
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs

echo "=== $(date) daily run ==="

echo "--- research ---"
python3 main.py || { echo "research failed, aborting"; exit 1; }

echo "--- generation ---"
# Generation is LLM work done by Kimi Code with the linkedin-content-agent skill.
# If your Kimi Code CLI supports a non-interactive/headless prompt flag, put it here, e.g.:
#   kimi -p "run the linkedin agent"
# Verify the exact flag on your install (kimi --help) and uncomment.
# Until then, this step is a reminder — run generation interactively, then open the PR.
DATE="$(date +%F)"
if [ ! -d "content/drafts/$DATE" ] || [ -z "$(ls -A "content/drafts/$DATE" 2>/dev/null)" ]; then
  echo "drafts for $DATE not found."
  echo ">> open Kimi Code in this repo and say: run the linkedin agent"
  echo ">> then re-run: python3 scheduler/open_pr.py"
  exit 0
fi

echo "--- approval PR ---"
python3 scheduler/open_pr.py
echo "=== done ==="
