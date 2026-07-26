# LinkedIn AI Content Agent

Fully automated daily LinkedIn pipeline: research → generate → PR approval → auto-post.

## The daily loop (zero terminal work)
1. **7:00 AM (GitHub Actions):** research brief is built, 4 posts are generated via the Kimi API (one per top story), and a PR titled "Drafts for YYYY-MM-DD" is opened.
2. **You (phone):** review the PR. Edit any post inline; delete a `post-N.md` file to drop that slot.
3. **Merge = approve.** A GitHub Action schedules all 4 posts to LinkedIn via Buffer at 4-hour intervals (07:00, 11:00, 15:00, 19:00 local — see `post_times` in `config/schedule.yaml`). Done.

## One-time setup

### Repo secrets (Settings → Secrets and variables → Actions)
| Secret | Where to get it |
|---|---|
| `KIMI_API_KEY` | platform.moonshot.ai (or platform.moonshot.cn) |
| `BUFFER_API_KEY` | publish.buffer.com/settings/api (free plan: 1 key) |
| `BUFFER_CHANNEL_ID` | run `BUFFER_API_KEY=... python3 scheduler/buffer_setup.py` |

### Workflows (add once, from your machine)
GitHub requires the `workflow` scope to push these, so create them locally:
- `.github/workflows/daily_agent.yml` — the 7 AM run (research → generate → PR)
- `.github/workflows/publish_on_merge.yml` — merge-triggered Buffer posting

Both files are in the repo discussion/README history; copy them from there or ask the agent to print them.

### Optional: local run instead of Actions
```bash
pip install feedparser pyyaml
cat > .env <<'EOF'
KIMI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...      # classic PAT, repo scope
EOF
0 7 * * * cd /home/delta/Linkendin-Agent && bash scheduler/daily_run.sh >> logs/daily.log 2>&1
```

## Manual equivalents
```bash
python3 main.py                        # research brief only
python3 generate.py                    # drafts via Kimi API
python3 scheduler/open_pr.py           # open/update today's approval PR
python3 scheduler/check_approved.py    # list merged (approved) drafts
python3 scheduler/publish_buffer.py --ref drafts/YYYY-MM-DD   # post manually
```

## Notes on Buffer's GraphQL API
- Posts are created with `createPost` + `mode: customScheduled` and a `dueAt` timestamp (UTC), which lands each post at its configured 4-hour slot. Use `mode: addToQueue` instead if you prefer Buffer's own queue slots.
- The API supports creation, deletion, and retrieval — but no editing. Your PR review is the edit step.
- Media upload is unreliable in the beta: posts go out **text-only** for now.
- Post metrics are exposed via `post { metrics { type name value unit } }` and `aggregatedPostMetrics` — this is what will power the Phase 5 analytics loop without manual stat-pasting.

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
- [x] Phase 4: merge-triggered posting via Buffer (GraphQL)
- [ ] Phase 5: analytics loop feeding back into voice.md
