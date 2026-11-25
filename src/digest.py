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
from sources import (AGGREGATE, AI_WORDS, BIZ_WORDS, COMPANIES, HF_TRENDING, HN, LEARN, OFFICIAL, OUTLETS, SPORTS_AI,
                     SPORTS_BIZ, SPORTS_TRUSTED, TRUSTED, YOUTUBE)
import astro, frontpage, send

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


# ------------------------------------------------------------------ companies
def company_of(text):
    t = f" {text.lower()} "
    hits = [(min((t.find(k) for k in kws if k in t), default=10**6), name) for name, kws in COMPANIES.items()]
    hits = [h for h in hits if h[0] < 10**6]
    return min(hits)[1] if hits else None


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
        company = company_of(lead["title"]) or company_of(" ".join(i["title"] for i in its))
        if company:
            score += 3
        strong = bool(re.search(r"launch|releas|introduc|unveil|announc|acquir|partnership|ipo|raises|funding|lawsuit|"
                                r"ban|regulat|resign|steps down|fired|outage|breach|open.?source|gpt-|claude|gemini|llama", lead["title"].lower()))
        out.append(dict(title=lead["title"], link=lead["link"], summary=summary, company=company, strong=strong, pubs=sorted({i["pub"] for i in its if i["kind"] != "hn"}),
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
    return any(len(tk & set(k.split())) >= max(3, .6 * min(len(tk), len(k.split()))) for k in seen if not k.startswith(("hf:", "learn:", "yt:", "sp:", "sb:")))


# ------------------------------------------------------------------ social: official YouTube channels, career
def youtube(seen):
    """New videos from official company channels (free RSS). Channel ids are resolved once and cached."""
    cache_f = ROOT / "state" / "youtube_ids.json"
    try:
        cache = json.loads(cache_f.read_text())
    except Exception:
        cache = {}
    out = []
    for name, handle in YOUTUBE.items():
        cid = cache.get(handle)
        if not cid:
            try:
                page = requests.get(f"https://www.youtube.com/{handle}", headers=UA, timeout=20).text
                m = re.search(r'"externalId":"(UC[\w-]{22})"', page) or re.search(r'channel_id=(UC[\w-]{22})', page)
                cid = m.group(1) if m else None
                if cid:
                    cache[handle] = cid
            except Exception:
                cid = None
        if not cid:
            continue
        for e in feed(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")[:3]:
            d = when(e)
            if d and d > NOW - timedelta(hours=48) and f"yt:{e.get('link')}" not in seen:
                out.append(dict(key=f"yt:{e.get('link')}", at=d, line=f"*{name}* · {clean(e.get('title'), 90)}", link=e.get("link")))
    cache_f.parent.mkdir(exist_ok=True)
    cache_f.write_text(json.dumps(cache, indent=1))
    return sorted(out, key=lambda x: x["at"], reverse=True)[:2]


def career(seen):
    """AI in sport, from trusted newsrooms: closest to Hemanth's career."""
    out = []
    for e in feed(SPORTS_AI):
        pub = clean((e.get("source") or {}).get("title", ""))
        title = clean(e.get("title"))
        if pub and title.endswith(" - " + pub):
            title = title[: -len(pub) - 3]
        if pub.lower() in TRUSTED and f"sp:{e.get('link')}" not in seen and is_ai(title):
            out.append(dict(key=f"sp:{e.get('link')}", line=f"*{clean(title, 100)}* · {pub}", link=e.get("link")))
    return out[:1]


def sports_business(seen):
    """The business of sport (US, India, European football) from trusted newsrooms: up to 2 per region, 5 in all."""
    out, keys = [], set()
    for region, url in SPORTS_BIZ.items():
        got = 0
        for e in feed(url):
            pub = clean((e.get("source") or {}).get("title", ""))
            title = clean(e.get("title"))
            if pub and title.endswith(" - " + pub):
                title = title[: -len(pub) - 3]
            low = title.lower()
            key = f"sb:{e.get('link')}"
            tk = " ".join(sorted(tokens(title)))
            if (pub.lower() not in SPORTS_TRUSTED or key in seen or tk in keys
                    or not any(w in low for w in BIZ_WORDS)):
                continue
            d = when(e)
            if d and d < NOW - timedelta(hours=48):
                continue
            keys.add(tk)
            out.append(dict(key=key, line=f"*{region}* · {clean(title, 110)} · _{pub}_", link=e.get("link")))
            got += 1
            if got == 2:
                break
    return out[:5]


ADVISOR_LENS = [
    "Who gains and who loses money from today's biggest deal, and why?",
    "If you advised the club or league in today's top story, what would you recommend first?",
    "What data would you need to prove today's top deal is worth the price?",
    "Which fans does today's story affect most, and how would you measure it?",
    "What is the one-sentence recommendation for the owner in today's top story?",
    "What could go wrong with today's biggest deal, and how would you hedge it?",
    "How could AI change the decision behind today's top sports story?",
]


def company_counts(items):
    counts = {}
    for it in items:
        if it["kind"] in ("official", "outlet", "aggregate"):
            c = company_of(it["title"])
            if c:
                counts[c] = counts.get(c, 0) + 1
    return counts


# ------------------------------------------------------------------ formatting (WhatsApp)
LINE = "━━━━━━━━━━━━━━━━━━━━"


def boston_now():
    return NOW.astimezone(timezone(timedelta(hours=-5)))


def src_line(s):
    return "Official announcement" if s["official"] and len(s["pubs"]) < 2 else f"Confirmed by {len(s['pubs'])} sources"


def daily_message(stories, energy, extras):
    d = boston_now()
    L = ["*THE TAMIL JOURNAL*", f"_{d.strftime('%A, %B %-d, %Y')} · AI & Sports Business Edition_", LINE, "",
         "*Vanakkam, Hemanth.*",
         f"_Moon in {energy['moon_star']} · {energy['tara']}, {energy['tara_meaning']}_", energy["message"],
         f"_{energy['weekday']}_", "", LINE, "*WHAT'S NEWS*", ""]
    for i, s in enumerate(stories, 1):
        L += [f"*{i} · {(s['company'] or 'AI').upper()}*", f"*{clean(s['title'], 120)}*"]
        if s["summary"]:
            L.append(s["summary"])
        L += [f"✓ {src_line(s)}", s["link"], ""]
    if not stories:
        L += ["A quiet day: no story met the verification bar.", ""]
    for title, rows in extras:
        if rows:
            L += [LINE, f"*{title}*", ""] + [f"▸ {r['line']}\n{r['link']}" for r in rows] + [""]
    lens = ADVISOR_LENS[boston_now().timetuple().tm_yday % len(ADVISOR_LENS)]
    L += [LINE, "*ADVISOR'S LENS*", "_Think like a consultant: one question on today's news._", lens, ""]
    p = prompt_of_the_day()
    L += [LINE, "*PROMPT OF THE DAY*", f"_{p['use']}_", p["prompt"], "", LINE,
          "_Verified: every story is confirmed by the company itself or by two or more independent newsrooms._"]
    return "\n".join(L)


def breaking_message(s):
    t = boston_now().strftime("%-I:%M %p")
    return "\n".join(["*BREAKING · THE TAMIL JOURNAL*", LINE, f"*{(s['company'] or 'AI').upper()}*",
                      f"*{clean(s['title'], 140)}*"] + ([s["summary"]] if s["summary"] else []) +
                     [f"✓ {src_line(s)} · {t} Boston", s["link"]])


# ------------------------------------------------------------------ main
def main(mode):
    state = load_state()
    today = boston_now().date().isoformat()
    out_dir = ROOT / "digests"; out_dir.mkdir(exist_ok=True)
    image = None
    if mode == "daily":
        if (out_dir / f"{today}-daily.md").exists() and not os.environ.get("FORCE"):
            print("today's briefing was already sent"); return
        items = collect(28)
        fresh = os.environ.get("IGNORE_SEEN")
        ranked = [s for s in cluster(items) if s["verified"] and (fresh or not is_seen(s, state["seen"]))]
        stories = diverse(ranked, 5)
        energy = astro.today(NOW, boston_now().weekday())
        sn = {} if fresh else state["seen"]
        extras = [("SPORTS BUSINESS · US · INDIA · EUROPE", sports_business(sn)), ("FROM THE SOURCE", youtube(sn)),
                  ("CAREER EDGE", career(sn) + learn(sn)), ("TOOLS TO TRY", tools(sn))]
        msg = daily_message(stories, energy, extras)
        image = str(out_dir / f"{today}-front-page.png")
        frontpage.render(image, f"{boston_now().strftime('%A, %B %-d, %Y')} · Boston · AI & Sports Business Edition", "Vanakkam, Hemanth.",
                         energy, stories, company_counts(items))
        keys = [s["key"] for s in stories] + [r["key"] for _, rows in extras for r in rows]
    else:
        sent_today = state["breaking"].get(today, 0)
        big = [s for s in cluster(collect(3)) if s["verified"] and s["company"] and not is_seen(s, state["seen"])
               and ((s["official"] and s["strong"]) or len(s["pubs"]) >= 3)]
        if not big or sent_today >= 4:
            print("no breaking story"); return
        msg, keys = breaking_message(big[0]), [big[0]["key"]]
        state["breaking"] = {today: sent_today + 1}
    stamp = today if mode == "daily" else boston_now().strftime("%Y-%m-%d-%H%M")
    (out_dir / f"{stamp}-{mode}.md").write_text(msg + "\n")
    print(msg)
    ok, how = send.whatsapp(msg, image=image, caption="*THE TAMIL JOURNAL* · today's front page")
    STATE.parent.mkdir(exist_ok=True)
    (STATE.parent / "last_send.json").write_text(json.dumps({"at": NOW.isoformat(), "mode": mode, "delivered_by": how, "ok": ok}, indent=1))
    if ok:
        for k in keys:
            state["seen"][k] = today
        STATE.write_text(json.dumps(state, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "daily")
