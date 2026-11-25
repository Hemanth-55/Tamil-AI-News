# Tamil · AI News: session context

Hemi's free daily briefing, "The Tamil Journal": verified AI news plus the business of sport (US, India, European football), sent to WhatsApp at 7:15 AM Boston by GitHub Actions. No language model; costs nothing.
Claude: read this file, then `notes/`, at the start of every session.

## The project
- `src/digest.py daily|breaking` collects free RSS feeds (`src/sources.py`), keeps verified stories (official source, or 2+ trusted newsrooms for AI; trusted sports/business newsrooms for the sports section), formats the WhatsApp message and front page (`src/frontpage.py`), and sends it (`src/send.py`).
- Sections: What's News (AI) · **Sports Business · US · India · Europe** · From the Source · Career Edge · Tools to Try · **Advisor's Lens** (a daily consultant question) · Prompt of the Day.
- Tune the sports section in `src/sources.py`: `SPORTS_BIZ` (searches), `BIZ_WORDS` (what counts as business), `SPORTS_TRUSTED` (publishers).
- Timing: `.github/workflows/news.yml` (UTC). Resend today: edit `send-now` and push. Briefings are saved in `digests/`.

## Rules
- **North star:** Hemi is becoming a consultant / advisor to the sports industry. News should build that knowledge: AI, sports business, deals, media rights, ownership, betting, European football finance, Indian cricket business. See https://github.com/Hemanth-55/Tamil-/blob/main/notes/north-star.md
- Verified stories only. Free only: no paid APIs, no LLM calls, no paid WhatsApp tiers.

## Session routine
- Start: `/session-start` · End: `/session-end` (log, commit, `git pull --rebase`, push)

## Related
- Hub: https://github.com/Hemanth-55/Tamil- (agent instructions in `agents/tamil-ai-news`)
