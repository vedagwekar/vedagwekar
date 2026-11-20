#!/usr/bin/env python3
"""'the year, annotated' — contributions as a radial bloom, with ved's year marked on it."""
import datetime as dt
import math
from xml.sax.saxutils import escape

import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_contributions():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        query = ("query{user(login:\"vedagwekar\"){contributionsCollection{contributionCalendar"
                 "{weeks{contributionDays{date contributionCount}}}}}}")
        q = json.dumps({"query": query})
        req = urllib.request.Request("https://api.github.com/graphql", data=q.encode(),
                                     headers={"Authorization": f"bearer {token}"})
        data = json.load(urllib.request.urlopen(req))
        days = [d for w in data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
                for d in w["contributionDays"]]
        days.sort(key=lambda d: d["date"])
        return dt.date.fromisoformat(days[0]["date"]), [d["contributionCount"] for d in days]
    start_s, cs = open(sys.argv[1]).read().strip().split("|")
    return dt.date.fromisoformat(start_s), [int(c) for c in cs.split()]


sys.path.insert(0, HERE)
import typo  # noqa: E402

START, counts = load_contributions()
N = len(counts)
END = START + dt.timedelta(days=N - 1)
TOTAL = sum(counts)

W, H = 830, 470
CX, CY = 590, 236
R0 = 100
DRAW = 3.6                      # seconds for the year to play back on load
used = {"geist": set(), "geistmono": set()}


def T(family, s):
    used[family].update(s)
    return escape(s)


def ang(i):
    return -math.pi / 2 + 2 * math.pi * i / N


def pt(r, a):
    return CX + r * math.cos(a), CY + r * math.sin(a)


def idx(d):
    return (d - START).days


def bar_len(c):
    return 3 if c == 0 else 7 + 19 * math.log2(1 + c)


def level(c, mx):
    if c == 0:
        return 0
    return 1 + min(3, int(3.999 * math.log1p(c) / math.log1p(mx)))


def load_events():
    """milestones come from events.txt, plus any open github issue labelled 'milestone'."""
    events = []
    path = os.path.join(ROOT, "events.txt")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("|")]
            try:
                d = dt.date.fromisoformat(parts[0])
            except ValueError:
                print(f"skipping line with a bad date: {line!r}")
                continue
            if len(parts) < 2 or not parts[1]:
                continue
            events.append((d, parts[2].lower() if len(parts) > 2 and parts[2] else None, parts[1].lower()))
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if token and repo:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/issues?labels=milestone&state=open&per_page=100",
            headers={"Authorization": f"bearer {token}", "Accept": "application/vnd.github+json"})
        for iss in json.load(urllib.request.urlopen(req)):
            if "pull_request" in iss:
                continue
            body = (iss.get("body") or "").strip()
            d = dt.date.fromisoformat(iss["created_at"][:10])
            tag = None
            for ln in body.splitlines():
                ln = ln.strip()
                if ln[:10].count("-") == 2:
                    try:
                        d = dt.date.fromisoformat(ln[:10])
                        continue
                    except ValueError:
                        pass
                if ln.lower().startswith("label:"):
                    tag = ln.split(":", 1)[1].strip().lower() or None
            events.append((d, tag, iss["title"].strip().lower()))
    return events



body = []
mx = max(counts)

# ── milestones: newest at the top ────────────────────────────────
MAX_LABELS = 7
placed = []
for d, tag, text in load_events():
    i = idx(d)
    if 0 <= i < N:
        placed.append((d, i, tag or d.strftime("%b").lower(), text))
placed.sort(key=lambda p: p[0], reverse=True)
placed = placed[:MAX_LABELS]
marked = {p[1] for p in placed}

# ── the bloom ────────────────────────────────────────────────────
for i, c in enumerate(counts):
    a = ang(i)
    ln = bar_len(c)
    x1, y1 = pt(R0, a)
    x2, y2 = pt(R0 + ln, a)
    b = f"{DRAW * i / N:.3f}s"
    cls = "l4" if i in marked else f"l{level(c, mx)}"
    w = 1.9 if i in marked else 1.5
    body.append(f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke-width="{w}" stroke-linecap="round" stroke-dasharray="{ln:.1f}" stroke-dashoffset="{ln:.1f}">'
                f'<animate attributeName="stroke-dashoffset" to="0" begin="{b}" dur=".5s" fill="freeze"/></line>')

# ── milestone list + matching numerals on the bloom ─────────────
LX, TOP = 24, 70
gap = min(44, (H - 120 - TOP) / max(1, len(placed) - 1))
for k, (d, i, mon, text) in enumerate(placed, 1):
    ly = TOP + (k - 1) * gap
    n = f"{len(placed) - k + 1:02d}"          # oldest is 01 at the bottom, newest on top
    t0 = DRAW * i / N + 0.2
    a = ang(i)
    near = max(bar_len(counts[j]) for j in range(max(0, i - 5), min(N, i + 6)))
    bx, by = pt(R0 + near + 12, a)
    body.append(f'<g opacity="0">'
                f'<text class="mono faint" x="{bx:.1f}" y="{by + 3.5:.1f}" text-anchor="middle" font-size="10">{T("geistmono", n)}</text>'
                f'<text class="mono faint" x="{LX}" y="{ly:.1f}" font-size="11">{T("geistmono", n)}</text>'
                f'<text class="mono mute" x="{LX + 30}" y="{ly:.1f}" font-size="11">{T("geistmono", mon)}</text>'
                f'<text class="sans ink" x="{LX + 92}" y="{ly:.1f}" font-size="15">{T("geist", text)}</text>'
                f'<animate attributeName="opacity" to="1" begin="{t0:.2f}s" dur=".5s" fill="freeze"/></g>')

# small heading over the list
body.append(f'<text class="mono faint" x="{LX}" y="{TOP - 34}" font-size="10.5" letter-spacing="1.2">'
            f'{T("geistmono", "THE PAST YEAR")}</text>')

# ── today ────────────────────────────────────────────────────────
tx, ty = pt(R0 - 6, ang(N - 1))
body.append(f'<circle class="dotf" cx="{tx:.1f}" cy="{ty:.1f}" r="2.4" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;.3;1" begin="{DRAW:.1f}s" dur="2.4s" repeatCount="indefinite"/></circle>')

# ── centre ───────────────────────────────────────────────────────
body.append(f'<text class="sans ink" x="{CX}" y="{CY - 6}" text-anchor="middle" font-size="19" font-weight="500" '
            f'letter-spacing="-.2">{T("geist", "ved agwekar")}</text>')
body.append(f'<text class="sans mute" x="{CX}" y="{CY + 14}" text-anchor="middle" font-size="12">'
            f'{T("geist", "math · uwaterloo")}</text>')
body.append(f'<text class="mono faint" x="{CX}" y="{CY + 36}" text-anchor="middle" font-size="10.5">'
            f'{T("geistmono", f"{TOTAL} contributions")}</text>')

# ── footer ───────────────────────────────────────────────────────
foot = f"{START.strftime('%b %Y').lower()} → {END.strftime('%b %Y').lower()} · one line per day · redrawn nightly"
body.append(f'<text class="mono faint" x="{W / 2}" y="{H - 16}" text-anchor="middle" font-size="10.5">'
            f'{T("geistmono", foot)}</text>')

css = (typo.face("geist", "".join(used["geist"])) + typo.face("geistmono", "".join(used["geistmono"]))
       + f".sans{{font-family:{typo.SANS}}}.mono{{font-family:{typo.MONO}}}" + typo.PALETTE_CSS)
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'role="img" aria-label="ved agwekar: the past year, one line per day of commits, with milestones">'
       f"<style>{css}</style>{''.join(body)}</svg>")
open(os.path.join(ROOT, "assets", "year.svg"), "w").write(svg)
print(f"year.svg {W}x{H} {len(svg)//1024} KB")
