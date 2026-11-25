"""The Tamil Journal: a Wall Street Journal-style front page image for the morning briefing."""
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle

FONTS = Path(__file__).resolve().parents[1] / "assets" / "fonts"
for f in FONTS.glob("*.ttf"):
    font_manager.fontManager.addfont(str(f))
HEAD, BODY, SANS = "Playfair Display", "Source Serif 4", "Inter"
PAPER, INK, GREY, RULE, ACCENT = "#FBF9F4", "#121212", "#5E5E5E", "#BDB8AE", "#0B4F8A"
W, H = 1080, 2400


def _t(ax, x, y, s, size, font=BODY, color=INK, weight="normal", ha="left", va="top", style="normal"):
    ax.text(x, y, s, fontsize=size, family=font, color=color, weight=weight, ha=ha, va=va, style=style)


def _rule(ax, y, x0=60, x1=W - 60, lw=1.0, color=INK):
    ax.plot([x0, x1], [y, y], color=color, lw=lw, solid_capstyle="butt")


PX = 150 / 72        # points to pixels at 150 dpi


def render(path, date_line, greeting, energy, stories, companies):
    fig = plt.figure(figsize=(W / 150, H / 150), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    fig.patch.set_facecolor(PAPER)

    # masthead
    _t(ax, W / 2, 34, "The Tamil Journal", 38, HEAD, ha="center")
    _rule(ax, 136, lw=2.2); _rule(ax, 142, lw=.6)
    _t(ax, W / 2, 154, date_line.upper(), 8.5, SANS, GREY, ha="center")
    _rule(ax, 184, lw=.6)

    # today's energy
    msg = textwrap.wrap(energy["message"], 76)[:3]
    top, box_h = 206, 150 + len(msg) * 30 + 52
    ax.add_patch(Rectangle((60, top), W - 120, box_h, facecolor="#F1EDE4", edgecolor="none"))
    _t(ax, 86, top + 22, "TODAY'S ENERGY", 8, SANS, ACCENT, weight="bold")
    _t(ax, 86, top + 50, greeting, 21, HEAD)
    _t(ax, 86, top + 112, f"Moon in {energy['moon_star']}  ·  {energy['tara']}, {energy['tara_meaning']}", 10.5, BODY, GREY, style="italic")
    for i, line in enumerate(msg):
        _t(ax, 86, top + 150 + i * 30, line, 12, BODY)
    _t(ax, 86, top + 150 + len(msg) * 30 + 6, energy["weekday"], 9.5, BODY, GREY, style="italic")

    # what's news
    y = top + box_h + 34
    _t(ax, 60, y, "WHAT'S NEWS", 9.5, SANS, INK, weight="bold")
    _rule(ax, y + 30, lw=.6)
    y += 50
    shown = stories[:5]
    for i, s in enumerate(shown):
        _t(ax, 60, y, (s.get("company") or "AI").upper(), 8, SANS, ACCENT, weight="bold")
        y += 28
        for line in textwrap.wrap(s["title"], 52)[:2]:
            _t(ax, 60, y, line, 16, HEAD); y += 42
        for line in (textwrap.wrap(s["summary"], 84)[:2] if s.get("summary") else []):
            _t(ax, 60, y + 2, line, 10.5, BODY, GREY); y += 28
        src = "Official announcement" if s["official"] and len(s["pubs"]) < 2 else f"Confirmed by {len(s['pubs'])} sources"
        _t(ax, 60, y + 6, "✓ " + src, 8, SANS, GREY)
        y += 44
        if i < len(shown) - 1:
            _rule(ax, y - 14, lw=.4, color=RULE)

    # who made news: real counts of independent reports in the last 24 hours
    top_c = [(k, v) for k, v in sorted(companies.items(), key=lambda kv: -kv[1]) if v > 0][:6]
    if top_c:
        y0 = y + 6
        _rule(ax, y0, lw=.6)
        _t(ax, 60, y0 + 18, "WHO MADE NEWS", 9.5, SANS, INK, weight="bold")
        _t(ax, 262, y0 + 19, "Independent reports in the last 24 hours", 9, BODY, GREY, style="italic")
        mx = top_c[0][1]
        for i, (k, v) in enumerate(top_c):
            yy = y0 + 66 + i * 42
            _t(ax, 60, yy, k, 11, BODY)
            ax.add_patch(Rectangle((230, yy + 2), (W - 380) * v / mx, 24, facecolor=ACCENT if i == 0 else "#A9BFD2", edgecolor="none"))
            _t(ax, 230 + (W - 380) * v / mx + 12, yy + 3, str(v), 10, SANS, INK)
        y = y0 + 66 + len(top_c) * 42

    page_h = y + 90
    _rule(ax, page_h - 62, lw=.6)
    _t(ax, W / 2, page_h - 46, "Verified: every story is confirmed by the company itself or by two or more independent newsrooms.",
       8, BODY, GREY, ha="center", style="italic")
    ax.set_ylim(page_h, 0); fig.set_size_inches(W / 150, page_h / 150)
    fig.savefig(path, facecolor=PAPER)
    plt.close(fig)
    return path
