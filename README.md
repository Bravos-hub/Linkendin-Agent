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
cp -r skills/linkedin-content-agent ~/.kimi/skills/
```

## Daily run
```bash
python3 main.py          # builds the research brief
# then in Kimi Code, in this directory:
#   "run the linkedin agent"
```

Cron (7:00 AM daily): `0 7 * * * cd /path/to/linkedin-agent && python3 main.py >> logs/daily.log 2>&1`

## Roadmap
- [x] Phase 1: research + drafting + voice profile
- [ ] Phase 2: cron + GitHub PR approval flow
- [ ] Phase 3: image generation + carousel rendering
- [ ] Phase 4: scheduling via Buffer/Typefully API
- [ ] Phase 5: analytics loop feeding back into voice.md
