"""shared type + colour for the profile images: geist and geist mono, embedded so they look the same everywhere."""
import base64
import io
import os
from fontTools.ttLib import TTFont
from fontTools import subset

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")
FILES = {"geist": "Geist.ttf", "geistmono": "GeistMono.ttf"}
_metrics = {}


def face(family, text):
    """an @font-face rule with just the glyphs we use, keeping the weight axis."""
    opts = subset.Options()
    opts.flavor = "woff"
    f = TTFont(os.path.join(FONTS, FILES[family]))
    s = subset.Subsetter(opts)
    s.populate(text=text + " 0123456789")
    s.subset(f)
    f.flavor = "woff"
    buf = io.BytesIO()
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:{family};font-weight:100 900;"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}")


def width(family, text, size):
    if family not in _metrics:
        f = TTFont(os.path.join(FONTS, FILES[family]))
        _metrics[family] = (f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm)
    cm, hm, upm = _metrics[family]
    return sum(hm[cm.get(ord(c), cm[ord("?")])][0] for c in text) * size / upm


SANS = "geist,'Geist',ui-sans-serif,system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "geistmono,'Geist Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# github's own light/dark greys, so it sits naturally on the page
PALETTE_CSS = (
    ".ink{fill:#1f2328}.mute{fill:#656d76}.faint{fill:#8c959f}"
    ".l0{stroke:#d8dee4}.l1{stroke:#afb8c1}.l2{stroke:#8c959f}.l3{stroke:#57606a}.l4{stroke:#1f2328}"
    ".dotf{fill:#1f2328}"
    "@media (prefers-color-scheme:dark){.ink{fill:#e6edf3}.mute{fill:#8b949e}.faint{fill:#6e7681}"
    ".l0{stroke:#262c33}.l1{stroke:#3d444d}.l2{stroke:#6e7681}.l3{stroke:#9da7b3}.l4{stroke:#e6edf3}"
    ".dotf{fill:#e6edf3}}"
)
