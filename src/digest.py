"""Tamil · AI News — a verified, 3-minute AI briefing delivered to WhatsApp.

    python src/digest.py daily      # the morning briefing
    python src/digest.py breaking   # only major, multi-source stories since the last check (max 2 a day)

No language model is involved, so a run costs nothing: stories are collected from free RSS feeds,
grouped when several newsrooms report the same event, and kept only if they are verified:
  * announced by the company itself (an official blog), or
  * reported by at least two independent, established newsrooms.
"""
import html, json, math, os, re, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

sys.path.insert(0, str(Path(__file__).parent))
from sources import AGGREGATE, AI_WORDS, HF_TRENDING, HN, LEARN, OFFICIAL, OUTLETS, TRUSTED
import send

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state" / "seen.json"
NOW = datetime.now(timezone.utc)
UA = {"User-Agent": "Mozilla/5.0 (TamilAINews; personal digest)"}
STOP = set("""a an the and or of to in on for with by from at as is are was were be been it its this that these those
new news says say said will can could may how why what who after over into about amid more than up out not just
first now launches launch launched announces announced report reports""".split())


# ------------------------------------------------------------------ collecting
def clean(s, n=None):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    if n and len(s) > n:
        s = s[:n].rsplit(" ", 1)[0].rstrip(",;:—-") + "…"
    return s


def first_sentences(s, n=170):
    s = clean(s)
    parts = re.split(r"(?<=[.!?])\s+", s)
    out = ""
    for p in parts:
        if len(out) + len(p) > n and out:
            break
        out = (out + " " + p).strip()
    return clean(out, n)


def when(e):
    for k in ("published_parsed", "updated_parsed"):
        if e.get(k):
            return datetime.fromtimestamp(time.mktime(e[k]), timezone.utc)
    return None


def feed(url):
    try:
        r = requests.get(url, headers=UA, timeout=20)
        r.raise_for_status()
        return feedparser.parse(r.content).entries
    except Exception as ex:  # one broken feed never stops the briefing
        print("skip feed", url[:70], type(ex).__name__)
        return []


def is_ai(text):
    t = f" {text.lower()} "
    return any(re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", t) for w in AI_WORDS)


def collect(hours):
    since = NOW - timedelta(hours=hours)
    items = []
    for kind, group in (("official", OFFICIAL), ("outlet", OUTLETS)):
        for name, url in group.items():
            for e in feed(url):
                d = when(e)
                if not d or d < since:
                    continue
                title, summ = clean(e.get("title")), first_sentences(e.get("summary", ""))
                if kind == "outlet" and not is_ai(title + " " + summ):
                    continue
                if kind == "official" and name in ("NVIDIA", "Microsoft AI", "AWS Machine Learning") and not is_ai(title):
                    continue
                items.append(dict(kind=kind, pub=name, title=title, summary=summ, link=e.get("link"), at=d.isoformat()))
    for name, url in AGGREGATE.items():
        for e in feed(url):
            d = when(e)
            if not d or d < since:
                continue
            pub = clean((e.get("source") or {}).get("title", ""))
            title = clean(e.get("title"))
            if pub and title.endswith(" - " + pub):
                title = title[: -len(pub) - 3]
            if pub.lower() not in TRUSTED:
                continue
            items.append(dict(kind="aggregate", pub=pub, title=title, summary="", link=e.get("link"), at=d.isoformat()))
    # Hacker News front page: engineers' signal of what matters (points), not a source on its own
    try:
        hits = requests.get(HN, headers=UA, timeout=20).json().get("hits", [])
        for h in hits:
            if is_ai(h.get("title", "")) and h.get("created_at_i", 0) >= since.timestamp():
                items.append(dict(kind="hn", pub="Hacker News", title=h["title"], summary="", points=h.get("points", 0),
                                  link=h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                                  at=datetime.fromtimestamp(h["created_at_i"], timezone.utc).isoformat()))
    except Exception as ex:
        print("skip hn", type(ex).__name__)
    return items


# ------------------------------------------------------------------ grouping and verifying
def tokens(title):
    words = re.findall(r"[a-z0-9][a-z0-9.\-]+", title.lower())
    return {w.strip(".-") for w in words if w not in STOP and len(w) > 2}


def cluster(items):
    groups = []
    for it in sorted(items, key=lambda x: {"official": 0, "outlet": 1, "aggregate": 2, "hn": 3}[x["kind"]]):
        tk = tokens(it["title"])
        best, score = None, 0
        for g in groups:
            shared = len(tk & g["tokens"])
            sim = shared / max(1, min(len(tk), len(g["tokens"])))
            if shared >= 3 and sim >= .5 and sim > score:
                best, score = g, sim
        if best:
            best["items"].append(it)
            best["tokens"] |= tk
        else:
            groups.append({"items": [it], "tokens": set(tk)})
    out = []
    for g in groups:
        its = g["items"]
        pubs = {i["pub"].lower() for i in its if i["kind"] != "hn"}
        official = [i for i in its if i["kind"] == "official"]
        points = max([i.get("points", 0) for i in its] + [0])
        lead = (official or [i for i in its if i["kind"] == "outlet"] or [i for i in its if i["kind"] == "aggregate"] or its)[0]
        newest = max(datetime.fromisoformat(i["at"]) for i in its)
        age_h = (NOW - newest).total_seconds() / 3600
        verified = bool(official) or len(pubs) >= 2
        score = 4 * bool(official) + 2.2 * len(pubs) + 1.2 * math.log1p(points) - .04 * age_h
        summary = next((i["summary"] for i in its if i["summary"] and i["kind"] in ("official", "outlet")), "")
        out.append(dict(title=lead["title"], link=lead["link"], summary=summary, pubs=sorted({i["pub"] for i in its if i["kind"] != "hn"}),
                        official=bool(official), points=points, verified=verified, score=round(score, 2),
                        key=" ".join(sorted(g["tokens"])[:12])))
    return sorted(out, key=lambda s: -s["score"])


# ------------------------------------------------------------------ tools, learning, prompt
def tools(seen):
    out = []
    try:
        for m in requests.get(HF_TRENDING, headers=UA, timeout=20).json():
            mid = m.get("id") or m.get("modelId")
            if not mid or f"hf:{mid}" in seen:
                continue
            task = (m.get("pipeline_tag") or "model").replace("-", " ")
            out.append(dict(key=f"hf:{mid}", line=f"*{mid}* — trending {task} on Hugging Face ({m.get('likes', 0):,} likes)",
                            link=f"https://huggingface.co/{mid}"))
            if len(out) == 2:
                break
    except Exception as ex:
        print("skip hf", type(ex).__name__)
    return out


def learn(seen):
    best = []
    for name, url in LEARN.items():
        for e in feed(url)[:5]:
            d = when(e)
            if d and d > NOW - timedelta(days=3) and f"learn:{e.get('link')}" not in seen and is_ai(e.get("title", "") + " " + e.get("summary", "")[:300]):
                best.append((d, name, clean(e.get("title"), 90), e.get("link")))
    best.sort(reverse=True)
    return [dict(key=f"learn:{l}", line=f"*{t}* — {n}", link=l) for _, n, t, l in best[:1]]


def prompt_of_the_day():
    prompts = json.loads((ROOT / "src" / "prompts.json").read_text())
    return prompts[NOW.timetuple().tm_yday % len(prompts)]


# ------------------------------------------------------------------ state
def load_state():
    try:
        s = json.loads(STATE.read_text())
    except Exception:
        s = {"seen": {}, "breaking": {}}
    cutoff = (NOW - timedelta(days=7)).date().isoformat()
    s["seen"] = {k: v for k, v in s["seen"].items() if v >= cutoff}
    return s


NAMES = re.compile(r"\b([A-Z][a-zA-Z0-9\-]+(?:\s+[A-Z][a-zA-Z0-9\-]+)*)")


def subjects(title):
    """Proper names in a headline (people, companies, products), used to keep one story per subject."""
    found = {m.lower() for m in NAMES.findall(title) if m.lower() not in ("the", "how", "why", "what", "ai", "a")}
    return {f for f in found if len(f) > 2} - {t for t in found if " " not in t and t in {"new", "first"}}


def diverse(stories, n):
    picked = []
    for s in stories:
        sub = subjects(s["title"])
        if any(len(sub & subjects(p["title"])) >= 1 and (sub & subjects(p["title"])) - {"nvidia", "openai", "google", "microsoft", "meta", "apple", "amazon"} for p in picked):
            continue
        picked.append(s)
        if len(picked) == n:
            break
    return picked


def is_seen(story, seen):
    tk = set(story["key"].split())
    return any(len(tk & set(k.split())) >= max(3, .6 * min(len(tk), len(k.split()))) for k in seen if not k.startswith(("hf:", "learn:")))


# ------------------------------------------------------------------ formatting
def daily_message(stories, tool_list, learn_list, prompt):
    d = NOW.astimezone(timezone(timedelta(hours=-5)))
    lines = [f"*Tamil · AI News*  ·  {d.strftime('%a %d %b')}", "_3-minute read · verified stories only_", ""]
    lines.append("*Top stories*")
    for i, s in enumerate(stories, 1):
        src = "official announcement" if s["official"] and len(s["pubs"]) < 2 else f"{len(s['pubs'])} sources"
        lines.append(f"{i}. *{clean(s['title'], 110)}*")
        if s["summary"]:
            lines.append(f"   {s['summary']}")
        lines.append(f"   ✓ {src} · {s['link']}")
    if not stories:
        lines.append("A quiet day: no story met the verification bar.")
    if tool_list:
        lines += ["", "*Tools to try*"] + [f"• {t['line']}\n  {t['link']}" for t in tool_list]
    if learn_list:
        lines += ["", "*Learn*"] + [f"• {t['line']}\n  {t['link']}" for t in learn_list]
    lines += ["", "*Prompt to try*", f"_{prompt['use']}_", f"```{prompt['prompt']}```", "", "— Tamil"]
    return "\n".join(lines)


def breaking_message(s):
    return (f"*Tamil · AI News · Breaking*\n\n*{clean(s['title'], 140)}*\n"
            + (f"{s['summary']}\n" if s["summary"] else "") + f"✓ {len(s['pubs'])} sources · {s['link']}")


# ------------------------------------------------------------------ main
def main(mode):
    state = load_state()
    today = NOW.date().isoformat()
    if mode == "daily":
        if (ROOT / "digests" / f"{today}-daily.md").exists() and not os.environ.get("FORCE"):
            print("today's briefing was already sent"); return
        stories = diverse([s for s in cluster(collect(28)) if s["verified"] and not is_seen(s, state["seen"])], 5)
        tl, ll = tools(state["seen"]), learn(state["seen"])
        msg = daily_message(stories, tl, ll, prompt_of_the_day())
        keys = [s["key"] for s in stories] + [t["key"] for t in tl + ll]
    else:
        sent_today = state["breaking"].get(today, 0)
        big = [s for s in cluster(collect(4)) if s["verified"] and not is_seen(s, state["seen"])
               and (len(s["pubs"]) >= 4 or (s["official"] and len(s["pubs"]) >= 2))]
        if not big or sent_today >= 2:
            print("no breaking story"); return
        msg, keys = breaking_message(big[0]), [big[0]["key"]]
        state["breaking"] = {today: sent_today + 1}
    (ROOT / "digests").mkdir(exist_ok=True)
    (ROOT / "digests" / f"{today}-{mode}.md").write_text(msg + "\n")
    print(msg)
    ok, how = send.whatsapp(msg)
    STATE.parent.mkdir(exist_ok=True)
    (STATE.parent / "last_send.json").write_text(json.dumps({"at": NOW.isoformat(), "mode": mode, "delivered_by": how, "ok": ok}, indent=1))
    if ok:
        for k in keys:
            state["seen"][k] = today
        STATE.parent.mkdir(exist_ok=True)
        STATE.write_text(json.dumps(state, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "daily")
