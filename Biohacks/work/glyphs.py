#!/usr/bin/env python3
"""
glyphs.py - a lucide icon, at any size, in any colour, as RGBA.

The other two variants get the thing in the left circle from an image model: a
bowl of lentils, an athlete at the bottom of a squat. A hack is not an object, it
is an action, and a photograph of "someone taking a cold shower" at 190px across
in a vertical feed is a grey smudge with a person in it. A line icon at the same
size is still a snowflake.

So this variant draws its own left circle, which is the reason it needs no
generator at all and can put out a clip in the time the animator takes to run.
`ImageSwap.txt` is still here for the topics that want photographs.

    icon-sources/package/    lucide-static, ISC. 2077 icons, downloaded once
    icons/                   what has been rasterised, cached by name+size+colour

Rasterised with rsvg-convert rather than parsed here: the svg path grammar is
small but arcs and joins are not, and a stroke drawn a pixel wrong at 24px is
drawn eight pixels wrong at 200. `currentColor` is substituted before it goes
in, because an svg with no colour context renders black and every icon in this
folder is drawn on a dark row.

    python3 glyphs.py snowflake sunrise --size 260     # look at them
    python3 glyphs.py --sheet                          # everything the table uses
"""
import hashlib
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "icon-sources", "package", "icons")
CACHE = os.path.join(HERE, "icons")
LICENCE = os.path.join(HERE, "icon-sources", "package", "LICENSE")

# Lucide draws on a 24 unit box at stroke 2. Held at 2 the line thickens with the
# icon, which is what is wanted - the glyph is one weight at every size it is
# used at, and there is only one size in the clip anyway. 2.25 rather than 2:
# measured against the caption type beside it, a plain 2 reads a shade lighter
# than the SF Compact Black it sits under, and a row whose two halves disagree
# about weight looks like two designs.
STROKE = 2.25


def _key(name, size, rgb, stroke):
    h = hashlib.sha1(f"{name}|{size}|{rgb}|{stroke}".encode()).hexdigest()[:10]
    return os.path.join(CACHE, f"{name}_{size}_{h}.png")


def render(name, size, rgb=(255, 255, 255), stroke=STROKE):
    """The icon as HxWx4 float, white-on-nothing unless told otherwise."""
    path = os.path.join(SRC, f"{name}.svg")
    if not os.path.exists(path):
        raise SystemExit(f"no lucide icon called '{name}'. "
                         f"ls icon-sources/package/icons | grep {name.split('-')[0]}")
    out = _key(name, size, rgb, stroke)
    if not os.path.exists(out):
        os.makedirs(CACHE, exist_ok=True)
        hexcol = "#%02X%02X%02X" % tuple(int(c) for c in rgb)
        svg = open(path).read() \
            .replace('stroke="currentColor"', f'stroke="{hexcol}"') \
            .replace('stroke-width="2"', f'stroke-width="{stroke}"')
        subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), "-o", out],
                       input=svg.encode(), check=True)
    return np.array(Image.open(out).convert("RGBA")).astype(np.float32)


def licence():
    return open(LICENCE).read().splitlines()[0] if os.path.exists(LICENCE) else "?"


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("names", nargs="*")
    p.add_argument("--size", type=int, default=260)
    p.add_argument("--sheet", action="store_true", help="every icon hacks.json names")
    p.add_argument("-o", "--out", default="glyph_sheet.png")
    a = p.parse_args()

    names = a.names
    if a.sheet or not names:
        import hacks
        names = sorted({v["icon"] for v in hacks.load().values()})
    imgs = [render(n, a.size) for n in names]
    print(f"  {len(imgs)} glyphs at {a.size}px, lucide {licence()}")
    cols = min(6, len(imgs))
    rows = (len(imgs) + cols - 1) // cols
    pad = a.size // 6
    W = cols * (a.size + pad) + pad
    H = rows * (a.size + pad) + pad
    sheet = Image.new("RGB", (W, H), (14, 29, 36))
    for i, (n, im) in enumerate(zip(names, imgs)):
        x = pad + (i % cols) * (a.size + pad)
        y = pad + (i // cols) * (a.size + pad)
        sheet.paste(Image.fromarray(im.astype(np.uint8), "RGBA"), (x, y),
                    Image.fromarray(im.astype(np.uint8), "RGBA"))
        print(f"    {n}")
    sheet.save(a.out)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
