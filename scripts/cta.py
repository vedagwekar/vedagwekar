#!/usr/bin/env python3
"""The 'looking for co-ops' line, as its own image so the readme can link it to my resume.
Edit LINE / SUB below and run: python scripts/cta.py"""
import base64
import io
import os
from xml.sax.saxutils import escape
from fontTools.ttLib import TTFont
from fontTools import subset

LINE = "looking for summer 2027 co-ops"
SUB = "read my resume"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")
W, H = 830, 96


def face(fam, file, text):
    opts = subset.Options()
    opts.flavor = "woff"
    f = TTFont(os.path.join(FONTS, file))
    s = subset.Subsetter(opts)
    s.populate(text=text + " ")
    s.subset(f)
    f.flavor = "woff"
    buf = io.BytesIO()
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:{fam};src:url(data:font/woff;base64,{b64}) format('woff')}}"


def width(file, text, size):
    f = TTFont(os.path.join(FONTS, file))
    cm, hm, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hm[cm[ord(c)]][0] for c in text) * size / upm


sub_w = width("InstrumentSerif-Regular.ttf", SUB, 19)
css = (face("isi", "InstrumentSerif-Italic.ttf", LINE) + face("isr", "InstrumentSerif-Regular.ttf", SUB)
       + ".big{font-family:isi,'Instrument Serif',Georgia,serif;font-style:italic;font-size:40px;fill:#e54876}"
       ".sub{font-family:isr,'Instrument Serif',Georgia,serif;font-size:19px;fill:#5a4d42}"
       ".ul{stroke:#e54876}"
       "@media (prefers-color-scheme:dark){.sub{fill:#d9cfc2}}")
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'role="img" aria-label="{escape(LINE)}. {escape(SUB)}.">'
       f"<style>{css}</style>"
       f'<text class="big" x="{W / 2}" y="44" text-anchor="middle">{escape(LINE)}</text>'
       f'<text class="sub" x="{W / 2}" y="78" text-anchor="middle">{escape(SUB)}</text>'
       f'<line class="ul" x1="{W / 2 - sub_w / 2:.1f}" y1="84" x2="{W / 2 + sub_w / 2:.1f}" y2="84" stroke-width="1.2"/>'
       "</svg>")
open(os.path.join(ROOT, "assets", "coops.svg"), "w").write(svg)
print("assets/coops.svg", len(svg) // 1024, "KB")
