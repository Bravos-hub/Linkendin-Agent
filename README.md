# LinkedIn AI Content Agent

Daily semi-autonomous LinkedIn content pipeline, built to run with Kimi Code.

## How it works
1. **Research (Python):** `main.py` fetches RSS stories for today's track and ranks them into a research brief.
2. **Generation (Kimi Code):** the `linkedin-content-agent` skill reads the brief + `config/voice.md` and drafts 3 on-voice post options, a carousel outline (on carousel days), and an image prompt.
3. **Approval (you):** review drafts in `content/drafts/YYYY-MM-DD/`. Phase 2 adds GitHub PR-based approval.

## Setup
```bash
pip install feedparser pyyaml
# install the skill for Kimi Code:
cp -r skills/linkedin-content-agent ~/.kimi-code/skills/   # use ~/.kimi/skills/ if your install uses that path
```

## Daily run (automated, Phase 2)
```bash
# one-time: token with repo scope for PR creation
export GITHUB_TOKEN=<your PAT>     # add to ~/.bashrc to persist

# cron entry (crontab -e):
0 7 * * * cd /home/delta/Linkendin-Agent && bash scheduler/daily_run.sh >> logs/daily.log 2>&1
```
Each morning: research brief is built, drafts are generated (via Kimi Code skill), and a PR titled "Drafts for YYYY-MM-DD" is opened. **Merging the PR = approval.**

Manual equivalents:
```bash
python3 main.py                        # research brief only
python3 scheduler/open_pr.py           # open/update today's approval PR
python3 scheduler/check_approved.py    # list merged (approved) drafts ready to post
```

## Roadmap
- [x] Phase 1: research + drafting + voice profile
- [x] Phase 2: cron + GitHub PR approval flow
- [ ] Phase 3: image generation + carousel rendering
- [ ] Phase 4: scheduling via Buffer/Typefully API
- [ ] Phase 5: analytics loop feeding back into voice.md
