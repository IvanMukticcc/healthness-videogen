#!/usr/bin/env python3
"""
caption_glass.py - put a plate of frosted glass under the left captions.

In the engine because the failure is not one variant's. `add_labels.py` picks its
ink from the layout's light/dark flag, which is a guarantee on a flat row and a
guess on a photograph - so every variant that ships a scene mode inherits it.
Exercise wrote it after losing SLED PUSH to a black sled on a light row; Biohacks
asked for it rather than copying it, having measured its own thinnest shipped row
at a luminance gap of 86 where the rest run 153-243. Two users is the signal, the
same one that promoted `refine_art`.

On a coloured row the caption is safe: `add_labels.py` takes its ink from whether
the row is light or dark, and the row is one flat colour, so white-on-dark and
black-on-light always read. On a photographic row that guarantee is gone. The
row's flag still says light or dark, but what actually lies under the caption is
whatever the photograph put there - and on NO GYM REQUIRED row 4 it was the black
sled, on a light row, so `SLED PUSH` was drawn in near-black ink on it and
vanished completely. The right caption never has this problem: the body's disc is
opaque and the caption sits under it on a known colour.

The fix is the one the user's own app uses for text over photographs: a rounded
plate of blurred background behind the words, light enough to sit under the ink
and transparent enough to belong to the picture. Not a box - a pane.

    ../.venv/bin/python ../../engine/caption_glass.py \
        <topic>_clean.png <topic>_labelled.png \
        -l base_<topic>_layout.json -o <topic>_labelled.png

WHY IT RUNS AFTER add_labels AND NOT BEFORE

A plate should hug its words, and the width of the words is known only to the
tool that drew them - the font, the size it chose to make the longest caption
fit, the tracking. Guessing it here would be a second copy of that arithmetic,
which is the fault this repository spends most of its time avoiding.

So this reads the answer instead. Given the poster before labelling and the
poster after, the ink is the only difference, and its coverage comes back
exactly: `labelled = a * ink + (1 - a) * clean` solves for `a` per pixel. That
gives both the bounding box to fit the plate to and a clean way to put the words
back on top of it - re-composited from `a` rather than copied, because copying
the drawn pixels would carry a halo of the old background around every letter.
"""
import argparse
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PAD_X = 26          # how far the plate reaches past the words
PAD_Y = 9
BLUR = 14.0         # the frost. Large enough that no detail survives to compete
FILL = 0.55         # how far the plate moves towards its own tone
RIM = 0.30          # a brighter edge, so the pane has a boundary without a border
INK_MIN = 0.06      # below this, a pixel is background rather than a letter


def _alpha(clean, labelled, ink):
    """How much of each pixel the ink accounts for, from the two posters."""
    d = labelled - clean
    k = ink[None, None, :] - clean
    num = (d * k).sum(2)
    den = (k * k).sum(2)
    a = np.divide(num, den, out=np.zeros_like(num), where=den > 1e-6)
    return np.clip(a, 0.0, 1.0)


def _plate(region, light_plate, radius):
    """A pane of the background, frosted and lifted, with rounded ends."""
    h, w = region.shape[:2]
    blurred = np.asarray(
        Image.fromarray(region.astype(np.uint8)).filter(ImageFilter.GaussianBlur(BLUR)),
        dtype=np.float32)
    tone = np.float32([255, 255, 255]) if light_plate else np.float32([16, 16, 20])
    pane = blurred * (1.0 - FILL) + tone[None, None, :] * FILL

    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    mask = np.asarray(m, dtype=np.float32) / 255.0

    # The rim: the mask minus an eroded copy of itself, which is the same trick
    # bodymap.py uses for a muscle's edge and for the same reason - a stroked
    # rounded rectangle shows its joins and this does not.
    inner = Image.new("L", (w, h), 0)
    ImageDraw.Draw(inner).rounded_rectangle([2, 2, w - 3, h - 3], radius=max(1, radius - 2), fill=255)
    rim = np.clip(mask - np.asarray(inner, dtype=np.float32) / 255.0, 0, 1)
    edge = np.float32([255, 255, 255]) if light_plate else np.float32([210, 210, 220])
    pane = pane * (1 - (rim * RIM)[:, :, None]) + edge[None, None, :] * (rim * RIM)[:, :, None]
    return pane, mask


def main():
    p = argparse.ArgumentParser()
    p.add_argument("clean", help="the poster before add_labels.py")
    p.add_argument("labelled", help="the poster after it")
    p.add_argument("-l", "--layout", required=True)
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--side", default="left", choices=("left", "right", "both"),
                   help="which captions get a plate. The right one sits on the body's "
                        "own disc, which is opaque and a known colour, so it does not "
                        "need one")
    p.add_argument("--alpha", type=float, default=0.90,
                   help="the most solid a pane is allowed to get, for the row that "
                        "needs it")
    p.add_argument("--min-alpha", type=float, default=0.42,
                   help="the least. A caption that already reads gets this one")
    p.add_argument("--target", type=float, default=95.0,
                   help="how far the ink must sit from the plate it lies on, in mean "
                        "luminance. Every pane is the lightest one that clears this, "
                        "so a caption over plain concrete stays nearly transparent and "
                        "the one over the black sled does not")
    args = p.parse_args()

    clean = np.asarray(Image.open(args.clean).convert("RGB"), dtype=np.float32)
    lab = np.asarray(Image.open(args.labelled).convert("RGB"), dtype=np.float32)
    if clean.shape != lab.shape:
        raise SystemExit("the two posters are different sizes")
    L = json.load(open(args.layout))
    out = lab.copy()
    W = clean.shape[1]
    half = L.get("caption_w", 380) / 2 + 14

    sides = {"left": ["anchor_l"], "right": ["anchor_r"], "both": ["anchor_l", "anchor_r"]}[args.side]
    for i, row in enumerate(L["rows"], 1):
        light_row = bool(row["light"])
        ink = np.float32([24, 26, 32] if light_row else [255, 255, 255])
        y0, y1 = int(row["cap_top"]) - 8, int(row["cap_top"] + row["cap_h"]) + 8
        for key in sides:
            cx = L[key]
            x0, x1 = int(max(0, cx - half)), int(min(W, cx + half))
            a = _alpha(clean[y0:y1, x0:x1], lab[y0:y1, x0:x1], ink)
            ys, xs = np.where(a > INK_MIN)
            if len(xs) == 0:
                print(f"  r{i} {key}: no caption found")
                continue
            bx0 = max(0, xs.min() - PAD_X); bx1 = min(x1 - x0, xs.max() + PAD_X + 1)
            by0 = max(0, ys.min() - PAD_Y); by1 = min(y1 - y0, ys.max() + PAD_Y + 1)
            gx0, gy0 = x0 + bx0, y0 + by0
            region = clean[gy0:y0 + by1, gx0:x0 + bx1]
            h, w = region.shape[:2]
            pane, mask = _plate(region, light_row, radius=h // 2)

            # The lightest pane that still separates the ink from what it lies on.
            # One fixed strength cannot do both jobs: at 0.62 every caption on this
            # poster read except SLED PUSH, which sat on the black sled and came in
            # at 16 luminance apart, and at 0.82 that one reads and the other four
            # are heavier than they need to be.
            sub = a[by0:by1, bx0:bx1][:, :, None]
            ink_l = float(ink.mean())
            chosen = args.alpha
            for cand in np.arange(args.min_alpha, args.alpha + 0.001, 0.04):
                trial = region * (1 - (mask * cand)[:, :, None]) + pane * (mask * cand)[:, :, None]
                lit = trial.mean(2)[(sub[:, :, 0] > INK_MIN)]
                if lit.size and abs(ink_l - float(lit.mean())) >= args.target:
                    chosen = float(cand)
                    break

            dst = out[gy0:y0 + by1, gx0:x0 + bx1]
            m = (mask * chosen)[:, :, None]
            dst *= (1 - m)
            dst += pane * m
            # and the words back on top, from their own coverage rather than by
            # copying pixels that still carry the photograph around their edges
            dst *= (1 - sub)
            dst += ink[None, None, :] * sub
            print(f"  r{i} {key}: pane {w}x{h} at {chosen:.2f}")

    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
