# Tamil · AI News

**A verified, 3-minute AI briefing on WhatsApp every morning, plus alerts when something big breaks.**

Part of **Tamil**, my personal AI agent system. It runs entirely on free infrastructure and uses no language model, so it costs nothing to run.

## What arrives

| | |
|---|---|
| **Top stories** | Up to five of the day's most important AI stories, each with a one-line summary, the number of sources and a link. |
| **Tools to try** | Models trending on Hugging Face. |
| **Learn** | One fresh tutorial or explainer. |
| **Prompt to try** | A practical prompt that rotates daily. |
| **Breaking** | Up to two alerts a day, only for stories that four or more newsrooms are already reporting, or official announcements confirmed elsewhere. |

## How it decides what's true and what matters

1. **Collect.** Free RSS feeds from the AI labs themselves (OpenAI, Google DeepMind, Google, Microsoft, NVIDIA, Hugging Face, AWS), established newsrooms (TechCrunch, The Verge, MIT Technology Review, Ars Technica, VentureBeat, Wired, The Decoder), Google News searches limited to trusted publishers such as Reuters, Bloomberg and AP, and the Hacker News front page.
2. **Group.** Headlines describing the same event are merged into one story.
3. **Verify.** A story is kept only if the company announced it itself, or at least two independent, established newsrooms reported it. Single-source rumours never reach the briefing.
4. **Rank.** Official announcements, the number of independent sources, Hacker News engagement and freshness decide the order.
5. **Remember.** Stories already sent in the last seven days are skipped.

## Cost

Zero. GitHub Actions is free for public repositories, the feeds need no keys, and delivery uses a free WhatsApp gateway (Green-API's Developer plan or CallMeBot). Every run is logged in `digests/`.

## Setup

Add your WhatsApp gateway details as repository secrets (Settings → Secrets and variables → Actions); see `src/send.py` for the names. Without them, the briefing is still written to `digests/` every day.

```
src/sources.py    the feeds and trusted publishers
src/digest.py     collect, group, verify, rank, format
src/send.py       WhatsApp delivery
src/prompts.json  the daily prompt rotation
```

---

<sub>Hemanth Kumar Gopi · <a href="https://hemanthkumargopi.vercel.app">hemanthkumargopi.vercel.app</a></sub>
