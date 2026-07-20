#!/usr/bin/env bash
# Daily 7 AM run: research -> generate (Kimi API) -> open approval PR.
# Cron: 0 7 * * * cd /home/delta/Linkendin-Agent && bash scheduler/daily_run.sh >> logs/daily.log 2>&1
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs

# load secrets (KIMI_API_KEY, GITHUB_TOKEN) from .env if present
if [ -f .env ]; then set -a; . ./.env; set +a; fi

echo "=== $(date) daily run ==="

echo "--- research ---"
python3 main.py || { echo "research failed, aborting"; exit 1; }

echo "--- generation (Kimi API) ---"
python3 generate.py || { echo "generation failed, aborting"; exit 1; }

echo "--- approval PR ---"
python3 scheduler/open_pr.py
echo "=== done ==="
