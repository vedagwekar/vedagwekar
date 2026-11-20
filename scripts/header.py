#!/usr/bin/env python3
"""the one-line header at the top of my readme. edit LINE / LINK_TEXT and run: python scripts/header.py"""
import os
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import typo  # noqa: E402

LINE = "looking for summer 2027 co-ops"
LINK_TEXT = "resume ↗"

W, H = 830, 44
SIZE = 15
gap = 14
w1 = typo.width("geist", LINE, SIZE)
w2 = typo.width("geist", LINK_TEXT, SIZE)
x0 = (W - (w1 + gap + 10 + gap + w2)) / 2
dot_x = x0 + w1 + gap + 5
x2 = dot_x + 5 + gap
css = (typo.face("geist", LINE + LINK_TEXT) + f".sans{{font-family:{typo.SANS}}}"
       + typo.PALETTE_CSS + ".rule{stroke:#d0d7de}@media (prefers-color-scheme:dark){.rule{stroke:#30363d}}")
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'role="img" aria-label="{escape(LINE)}. {escape(LINK_TEXT)}">'
       f"<style>{css}</style>"
       f'<text class="sans ink" x="{x0:.1f}" y="{H / 2 + 4:.1f}" font-size="{SIZE}" font-weight="500" '
       f'letter-spacing="-.1">{escape(LINE)}</text>'
       f'<text class="sans faint" x="{dot_x:.1f}" y="{H / 2 + 4:.1f}" font-size="{SIZE}" text-anchor="middle">·</text>'
       f'<text class="sans mute" x="{x2:.1f}" y="{H / 2 + 4:.1f}" font-size="{SIZE}">{escape(LINK_TEXT)}</text>'
       f'<line class="rule" x1="{x2:.1f}" y1="{H / 2 + 8:.1f}" x2="{x2 + w2:.1f}" y2="{H / 2 + 8:.1f}" stroke-width="1"/>'
       "</svg>")
open(os.path.join(typo.ROOT, "assets", "header-2.svg"), "w").write(svg)
print("assets/header-2.svg", len(svg) // 1024, "KB")
