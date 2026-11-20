#!/usr/bin/env python3
"""'the year, annotated' — contributions as a radial bloom, with ved's year marked on it."""
import base64
import datetime as dt
import io
import math
from xml.sax.saxutils import escape
from fontTools.ttLib import TTFont
from fontTools import subset

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


START, counts = load_contributions()
N = len(counts)
END = START + dt.timedelta(days=N - 1)
TOTAL = sum(counts)

W, H = 830, 505
CX, CY = 580, 282
R0 = 104
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
LM = os.path.join(ROOT, "assets", "fonts") + "/"
SERIF_FILES = {"sr": "lmroman10-regular.otf", "si": "lmroman10-italic.otf"}
serif_text = {k: set() for k in SERIF_FILES}


def ang(i):
    return -math.pi / 2 + 2 * math.pi * i / N


def pt(r, a):
    return CX + r * math.cos(a), CY + r * math.sin(a)


def idx(d):
    return (d - START).days


_lmf = TTFont(LM + "lmroman10-regular.otf")
_cm, _hm, _upm = _lmf.getBestCmap(), _lmf["hmtx"], _lmf["head"].unitsPerEm


def text_w(t, size):
    return sum(_hm[_cm.get(ord(ch), _cm[ord("?")])][0] for ch in t) * size / _upm


def serif(cls, text):
    serif_text[cls].update(text)
    return escape(text)


def colour(c, mx):
    t = math.log1p(c) / math.log1p(mx)
    stops = [(0.0, (201, 176, 146)), (0.5, (230, 146, 66)), (1.0, (229, 72, 118))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if t <= b:
            u = (t - a) / (b - a)
            return "#%02x%02x%02x" % tuple(round(ca[k] + (cb[k] - ca[k]) * u) for k in range(3))
    return "#e54876"


def arc_path(r, i0, i1):
    a0, a1 = ang(i0), ang(i1)
    x0, y0 = pt(r, a0)
    x1, y1 = pt(r, a1)
    large = 1 if (i1 - i0) / N > 0.5 else 0
    return f"M {x0:.1f} {y0:.1f} A {r} {r} 0 {large} 1 {x1:.1f} {y1:.1f}"


body, defs = [], []
DRAW = 3.6  # seconds for the year to play back
mx = max(counts)

# ── the bloom ────────────────────────────────────────────────────
for i, c in enumerate(counts):
    a = ang(i)
    ln = 3 if c == 0 else 8 + 20 * math.log2(1 + c)
    x1, y1 = pt(R0, a)
    x2, y2 = pt(R0 + ln, a)
    b = f"{DRAW * i / N:.3f}s"
    if c == 0:
        body.append(f'<line class="zero" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke-width=".9" '
                    f'opacity="0"><animate attributeName="opacity" to="1" begin="{b}" dur=".3s" fill="freeze"/></line>')
    else:
        body.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{colour(c, mx)}" '
                    f'stroke-width="{1.3 + min(c, 20) * .06:.2f}" stroke-linecap="round" '
                    f'stroke-dasharray="{ln:.1f}" stroke-dashoffset="{ln:.1f}"><animate attributeName="stroke-dashoffset" '
                    f'to="0" begin="{b}" dur=".5s" fill="freeze"/></line>')

# ── annotations (callouts with elbow leaders) ────────────────────
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


MAX_LABELS = 7
LX, FS_ANN = 18, 16
placed = []
for d, tag, text in load_events():
    i = idx(d)
    if not 0 <= i < N:
        continue
    a = ang(i)
    c = counts[i]
    tip = R0 + (3 if c == 0 else 8 + 20 * math.log2(1 + c)) + 5
    x1, y1 = pt(tip, a)
    placed.append([d, x1, y1, i, tag or d.strftime("%b").lower(), text])
placed.sort(key=lambda p: p[0], reverse=True)          # newest first
placed = placed[:MAX_LABELS]
TOP, BOTTOM = 52, H - 92
gap = min(48, (BOTTOM - TOP) / max(1, len(placed) - 1))
for k, p in enumerate(placed):                         # newest at the top, oldest at the bottom
    p.append(TOP + k * gap)
placed = [[p[2], p[1], p[3], p[4], p[5], p[6]] for p in placed]
for k, (y1, x1, i, mon, text, ly) in enumerate(placed, 1):
    t0 = DRAW * i / N + 0.2
    a = ang(i)
    c = counts[i]
    br = R0 + (3 if c == 0 else 8 + 20 * math.log2(1 + c)) + 13
    bx, by = pt(br, a)
    body.append(f'<g opacity="0"><circle class="badge" cx="{bx:.1f}" cy="{by:.1f}" r="8.5"/>'
                f'<text class="bnum" x="{bx:.1f}" y="{by + 3.4:.1f}" text-anchor="middle">{k}</text>'
                f'<circle class="badge" cx="{LX + 8.5:.1f}" cy="{ly - 5:.1f}" r="8.5"/>'
                f'<text class="bnum" x="{LX + 8.5:.1f}" y="{ly - 1.6:.1f}" text-anchor="middle">{k}</text>'
                f'<text class="mon" x="{LX + 28}" y="{ly:.1f}">{serif("si", mon)}</text>'
                f'<text class="ann" x="{LX + 104}" y="{ly:.1f}">{serif("sr", text)}</text>'
                f'<animate attributeName="opacity" to="1" begin="{t0:.2f}s" dur=".5s" fill="freeze"/></g>')

# ── today marker ─────────────────────────────────────────────────
tx, ty = pt(R0 - 4, ang(N - 1))
body.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="3" fill="#e54876" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;.35;1" begin="{DRAW:.1f}s" dur="2.4s" repeatCount="indefinite"/></circle>')

# ── centre ───────────────────────────────────────────────────────
body.append(f'<text class="nm" x="{CX}" y="{CY - 12}" text-anchor="middle">{serif("sr", "ved agwekar")}</text>')
body.append(f'<text class="sub" x="{CX}" y="{CY + 10}" text-anchor="middle">{serif("si", "math, uwaterloo")}</text>')
body.append(f'<text class="num" x="{CX}" y="{CY + 34}" text-anchor="middle">{TOTAL} contributions</text>')


# footer
body.append(f'<text class="seek" x="{LX}" y="{H - 18}">{serif("si", "looking for summer 2027 co-ops")}</text>')
body.append(f'<text class="foot" x="{W - 14}" y="{H - 18}" text-anchor="end">'
            f"{START.strftime('%b %Y').lower()} → {END.strftime('%b %Y').lower()} · one line per day · redrawn nightly</text>")


def face(cls, file):
    opts = subset.Options()
    opts.flavor = "woff"
    f = TTFont(LM + file)
    s = subset.Subsetter(opts)
    s.populate(text="".join(serif_text[cls]) + " ")
    s.subset(f)
    f.flavor = "woff"
    buf = io.BytesIO()
    f.save(buf)
    return (f"@font-face{{font-family:{cls};src:url(data:font/woff;base64,"
            f"{base64.b64encode(buf.getvalue()).decode()}) format('woff')}}")


css = "".join(face(k, v) for k, v in SERIF_FILES.items())
SR = "sr,'Latin Modern Roman',Georgia,serif"
SI = "si,'Latin Modern Roman',Georgia,serif"
css += (f".ann{{font-family:{SR};font-size:16px;fill:#3b322a}}.mon{{font-family:{SI};font-size:16px;fill:#9a8b7d}}"
        f".nm{{font-family:{SR};font-size:24px;fill:#2b241e}}"
        f".sub,.trk,.rec{{font-family:{SI};fill:#7b6d60}}.sub{{font-size:15px}}.trk{{font-size:9.5px}}.rec{{font-size:13px}}"
        f".seek{{font-family:{SI};font-size:18px;fill:#e54876}}.num,.foot{{font-family:{MONO}}}.num{{font-size:11.5px;fill:#7b6d60}}"
        f".foot{{font-size:11px;fill:#a3958a}}"
        ".zero{stroke:#d6ccc0}.badge{fill:#e54876}"f".bnum{{font-family:{MONO};font-size:10px;font-weight:700;fill:#fff}}"
        "@media (prefers-color-scheme:dark){.ann{fill:#e6ddd1}.mon{fill:#8b949e}.nm{fill:#f3ebe0}.sub,.trk,.rec,.num{fill:#9aa3ad}"
        ".foot{fill:#6e7681}.zero{stroke:#30363d}}")

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'role="img" aria-label="ved agwekar: the year, annotated">'
       f"<style>{css}</style><defs>{''.join(defs)}</defs>{''.join(body)}</svg>")
open(os.path.join(ROOT, "assets", "year.svg"), "w").write(svg)
print(f"year.svg {W}x{H} {len(svg)//1024} KB")
