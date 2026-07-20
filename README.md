# LinkedIn AI Content Agent

Fully automated daily LinkedIn pipeline: research → generate → PR approval → auto-post.

## The daily loop (zero terminal work)
1. **7:00 AM (cron):** research brief is built, drafts are generated via the Kimi API, and a PR titled "Drafts for YYYY-MM-DD" is opened.
2. **You (phone):** review the PR. Optionally edit `selected.txt` to pick which option posts (default: option-1-technical). Edit any draft inline.
3. **Merge = approve.** A GitHub Action queues the selected draft to LinkedIn via Buffer. Done.

## One-time setup
```bash
pip install feedparser pyyaml

# secrets — .env is gitignored, cron loads it automatically
cat > .env <<'EOF'
KIMI_API_KEY=sk-...        # platform.moonshot.ai key
GITHUB_TOKEN=ghp_...       # classic PAT, repo scope
EOF

# cron (crontab -e):
0 7 * * * cd /home/delta/Linkendin-Agent && bash scheduler/daily_run.sh >> logs/daily.log 2>&1
```

### Buffer (auto-posting)
1. Create an app at https://buffer.com/developers/apps/create → copy the access token.
2. `BUFFER_ACCESS_TOKEN=... python3 scheduler/buffer_setup.py` → copy your LinkedIn channel's profile ID.
3. Repo → Settings → Secrets and variables → Actions → add `BUFFER_ACCESS_TOKEN` and `BUFFER_PROFILE_ID`.

## Manual equivalents
```bash
python3 main.py                        # research brief only
python3 generate.py                    # drafts via Kimi API
python3 scheduler/open_pr.py           # open/update today's approval PR
python3 scheduler/check_approved.py    # list merged (approved) drafts
python3 scheduler/publish_buffer.py --ref drafts/YYYY-MM-DD   # post manually
```

## Interactive mode
Prefer reviewing in Kimi Code? Install the skill and say "run the linkedin agent":
```bash
cp -r skills/linkedin-content-agent ~/.kimi-code/skills/
```

## Roadmap
- [x] Phase 1: research + drafting + voice profile
- [x] Phase 2: cron + GitHub PR approval flow
- [x] Phase 2.5: headless generation via Kimi API
- [ ] Phase 3: image generation + carousel rendering
- [x] Phase 4: merge-triggered posting via Buffer
- [ ] Phase 5: analytics loop feeding back into voice.md
