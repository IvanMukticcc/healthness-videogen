#!/usr/bin/env python3
"""
add_labels.py - put the row captions on a generated poster.

The generator keeps getting these wrong: above the bowl instead of under it,
beside it, or drifting once a session has been prompted a few times. They are
typography at known positions, so there is no reason to ask for them at all.
The prompt tells it to add no text; this puts the captions in afterwards, in the
same place on every poster.

    python3 add_labels.py poster.jpeg -m ribbon_mask.png \
        --labels 'GINGER|STOMACH,BEETROOT|SPLEEN,...' -o labelled.png
"""
import argparse
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

FONT = "/Users/ivanmuktic/Library/Fonts/SF-Compact-Display-Black.otf"


def fit(text, target_w, start=90):
    start = max(20, start)
    size = start
    while size > 14:
        f = ImageFont.truetype(FONT, size)
        if f.getbbox(text)[2] - f.getbbox(text)[0] <= target_w:
            return f
        size -= 2
    return ImageFont.truetype(FONT, 14)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("poster")
    p.add_argument("-l", "--layout", required=True, help="the _layout.json the base wrote")
    p.add_argument("--caption-w", type=int, default=380)
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--labels", required=True,
                   help="five 'FOOD|ORGAN' pairs, comma separated, top row first")
    args = p.parse_args()

    img = Image.open(args.poster).convert("RGB")
    W, H = img.size
    L = json.load(open(args.layout))
    pairs = [t.split("|") for t in args.labels.split(",")]
    if len(pairs) != len(L["rows"]):
        raise SystemExit(f"{len(pairs)} label pairs for {len(L['rows'])} rows")

    d = ImageDraw.Draw(img)
    for (food, organ), row in zip(pairs, L["rows"]):
        # Straight into the bar the base reserved for it. Working the position out
        # again here is how the caption and the bar drifted apart; the layout file
        # is the single answer both sides read.
        fill = (28, 28, 28) if row["light"] else (255, 255, 255)
        cy = row["cap_top"] + row["cap_h"] / 2.0
        for text, cx in ((food.strip(), L["anchor_l"]), (organ.strip(), L["anchor_r"])):
            f = fit(text, int(args.caption_w * 0.88), int(row["cap_h"] * 0.78))
            b = f.getbbox(text)
            d.text((cx - (b[2] - b[0]) / 2 - b[0], cy - (b[3] - b[1]) / 2 - b[1]),
                   text, font=f, fill=fill)
        print(f"  '{food.strip()}' and '{organ.strip()}' in the bar at y "
              f"{row['cap_top']}-{row['cap_top'] + row['cap_h']}")

    img.save(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
