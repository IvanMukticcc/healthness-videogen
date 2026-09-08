#!/usr/bin/env python3
"""
dial.py - the right circle: a ring that closes and a number that counts up to it.

This is the whole difference between this variant and the two beside it. In the
food version the right circle holds an organ, and the organ does nothing for
eight seconds. In the exercise version it holds a body, and the body lights. Here
it holds a measurement, and the measurement **counts** - 0, 43, 96, 168, 250 -
in fourteen frames, with a ring closing round it at the same rate.

A number arriving is a fact. A number counting is an event, and an event is what
a thumb stops for. It is also the one gesture on a phone that cannot be taken in
at a glance, so the eye has to stay on the row until it settles, which is the
whole of what retention is.

Drawn, not generated, for the same reason the exercise version draws its body:
five posters whose dials disagree about where the ring starts is five different
dials, and the comparison the clip is about - this costs two minutes and moves
that, the next costs ten and moves this - does not survive it. An image model
cannot draw the same ring twice, so it is not asked to.

    THE RING is thin and at the very edge of the disc, not a fat gauge in the
    middle. The circle is 275px across in a 1536 poster and it is fixed by the
    base, so every pixel the ring takes is a pixel off the number. At r*0.94 and
    7% width the number gets 236px to live in and reads at 56px in the finished
    1080 video; the fat gauge this replaced left it 178 and 42.

    python3 dial.py --demo          # the five shipped dials, as a still
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import hacks

FONT = "/Users/ivanmuktic/Library/Fonts/SF-Compact-Display-Black.otf"

SS = 4              # supersampling. An arc drawn at 1x has a staircase on it, and
                    # a staircase lit at the finale is a row of bright steps
R_RING = 0.94       # ring radius, as a fraction of the guide circle
W_RING = 0.075      # and its width
PAD = 0.075         # clear space inside the ring before the number starts
ARCS = 48           # pre-rendered sweep steps. 48 over 0.55s at 24fps is two per
                    # frame, so nothing is ever drawn twice at the same angle
GLOW = 5.0          # bloom sigma at 1536. The disc's outer edge is x=1407 and the
                    # safe area ends at 1426, so 3 sigma is all the room there is

# The ink on a disc, by the kind of row it sits on. Everything drawn inside a
# circle in this folder reads it - the glyph on the left, the number on the
# right - because a white number on a light row is not a dim number, it is no
# number, and that is what the first cut of this shipped with on rows 2 and 4.
INK_DARK = (255, 255, 255)
INK_LIGHT = (18, 26, 32)


def ink(light):
    return INK_LIGHT if light else INK_DARK


def blend(dst, src, alpha, x0, y0):
    """src is HxWx4 float; alpha scales its own. Clipped to the frame.

    The one drawing primitive the three overlay modules share, and it lives here
    because this is the file that makes the sprites. Three copies of eleven lines
    is how the tools in this repository drifted in the first place.
    """
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(W, x0 + w), min(H, y0 + h)
    if dx1 <= dx0 or dy1 <= dy0:
        return
    s = src[sy0:sy0 + (dy1 - dy0), sx0:sx0 + (dx1 - dx0)]
    a = s[:, :, 3:4] / 255.0 * alpha
    r = dst[dy0:dy1, dx0:dx1]
    r *= (1.0 - a)
    r += s[:, :, :3] * a


def disc(r, rgb, light, feather=2.0):
    """The ground the ring sits on, covering the guide circle the base drew.

    Not the row's exact colour - a disc that matches its background perfectly is
    invisible, and the point of it is to end the wave somewhere. The rim is what
    makes it read as a component rather than a stain.
    """
    D = int(round(r * 2))
    yy, xx = np.mgrid[0:D, 0:D]
    d = np.hypot(xx - (D - 1) / 2.0, yy - (D - 1) / 2.0)
    a = np.clip((r - 1 - d) / feather, 0, 1)
    # A touch DARKER than its row, whichever kind of row it is. Lighter on a
    # light row was the first version and it put a white disc on a near-white
    # stripe with a white glyph on top of it: the left circle of rows 2 and 4
    # disappeared completely and their dials read as empty rings. Darker in both
    # directions also means the ink rule below has one branch and not two.
    body = np.clip(np.float32(rgb) + (-18 if not light else -22), 0, 255)
    rim = np.clip((d - (r - 3.0)) / 2.0, 0, 1) * a
    edge = np.clip(np.float32(rgb) + (54 if not light else -52), 0, 255)
    col = body[None, None, :] * (1 - rim[:, :, None]) + edge[None, None, :] * rim[:, :, None]
    return np.dstack([col, a * 255.0 * 0.97]).astype(np.float32)


def _ring(D, r, w, rgb, alpha, deg=360.0, start=-90.0):
    """One ring, or one arc of one, anti-aliased by drawing it four times too big."""
    S = D * SS
    im = Image.new("L", (S, S), 0)
    c, rr, ww = S / 2.0, r * SS, max(1.0, w * SS)
    box = (c - rr, c - rr, c + rr, c + rr)
    if deg >= 359.9:
        ImageDraw.Draw(im).ellipse(box, outline=255, width=int(round(ww)))
    elif deg > 0.05:
        ImageDraw.Draw(im).arc(box, start, start + deg, fill=255, width=int(round(ww)))
    m = np.array(im.resize((D, D), Image.LANCZOS)).astype(np.float32) / 255.0 * alpha
    return np.dstack([np.broadcast_to(np.float32(rgb), (D, D, 3)), m * 255.0]).copy()


def fit_number(values, avail, start=200):
    """One size for all five dials, found from the widest number.

    The same rule `add_labels.py` follows for the captions, for the same reason:
    fitted one at a time, '+250%' comes out at 62px beside '-2 H' at 104, and the
    poster reads as five decisions rather than one instrument. The price is that
    one long value shrinks all five, which is the reason to keep them short.
    """
    size = start
    while size > 16:
        f = ImageFont.truetype(FONT, size)
        if all(f.getbbox(v)[2] - f.getbbox(v)[0] <= avail for v in values):
            return f
        size -= 2
    return ImageFont.truetype(FONT, 16)


def _text(D, s, font, rgb, alpha=1.0):
    """A string centred in a DxD canvas, on its ink rather than on its line box.

    Centring on the font's line box drops the number a few pixels low, because
    the box carries descender room no digit uses - and a number that sits low in
    a ring reads as a number that has slipped.
    """
    im = Image.new("L", (D * SS, D * SS), 0)
    f = ImageFont.truetype(FONT, int(round(font.size * SS)))
    b = f.getbbox(s)
    ImageDraw.Draw(im).text(((D * SS - (b[2] - b[0])) / 2 - b[0],
                             (D * SS - (b[3] - b[1])) / 2 - b[1]), s, font=f, fill=255)
    m = np.array(im.resize((D, D), Image.LANCZOS)).astype(np.float32) / 255.0 * alpha
    return np.dstack([np.broadcast_to(np.float32(rgb), (D, D, 3)), m * 255.0]).copy()


def build(h, r, rgb_row, light, font, frames, k=1.0):
    """Everything one dial ever draws, made once.

    `frames` is how many steps the count takes. Rendering the number per frame
    would be 192 text draws a dial; there are only ever fourteen distinct
    numbers, so they are made here and indexed at draw time.
    """
    D = int(round(r * 2))
    col = hacks.colour(h)
    rr, ww = r * R_RING, r * W_RING

    dsc = disc(r, rgb_row, light)
    # The unfilled ring. Row colour rather than the accent - a track as bright as
    # the value is not a track. But it has to be clearly there: at +46 on a dark
    # row it was dark grey on a dark disc, and for the first 0.7s of the clip all
    # five right circles read as holes cut in the poster rather than as five
    # instruments waiting. +80 is the smallest step that reads at 540 wide.
    track_rgb = np.clip(np.float32(rgb_row) + (80 if not light else -70), 0, 255)
    track = _ring(D, rr, ww, track_rgb, 0.92)

    arcs = [_ring(D, rr, ww, col, 1.0, deg=360.0 * i / (ARCS - 1)) for i in range(ARCS)]

    target, fmt = hacks.count_to(h["value"])
    avail = 2 * (rr - ww / 2 - r * PAD)
    if target is None:
        nums = [_text(D, h["value"], font, ink(light))]
    else:
        # Eased the same way the ring sweeps, so the digits and the arc arrive
        # together. Counted linearly against an eased ring, the number is ahead
        # of it for the whole of the middle and the two read as two animations.
        nums = [_text(D, fmt(target * _ease(i / max(1, frames - 1))), font,
                      ink(light)) for i in range(frames)]

    # The finale lifts the ring towards white but never to it, and the bloom
    # carries the rest. A pure white ring vanishes on a light row exactly the way
    # the white number did, and washing an accent all the way out also throws
    # away the one thing the ring is saying - which direction this number went.
    hot = tuple(np.clip(np.float32(col) + (255.0 - np.float32(col)) * 0.45, 0, 255))
    lit = _ring(D, rr, ww, hot, 1.0)
    g = Image.fromarray(np.clip(arcs[-1], 0, 255).astype(np.uint8), "RGBA") \
             .filter(ImageFilter.GaussianBlur(max(1.0, GLOW * k)))
    return dict(D=D, disc=dsc, track=track, arcs=arcs, nums=nums, lit=lit,
                glow=np.array(g).astype(np.float32), colour=col,
                value=h["value"], metric=h["metric"], avail=avail)


def _ease(p):
    """easeOutCubic. No overshoot: a counter that goes past its number and comes
    back is a counter nobody believes."""
    return 1.0 - (1.0 - p) ** 3


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--hacks", default="auto:MORNING LIGHT,COLD FINISH,WALK AFTER LUNCH,"
                                      "LAST COFFEE,LIGHTS DOWN")
    p.add_argument("-r", type=float, default=137.5)
    p.add_argument("-o", "--out", default="dial_demo.png")
    a = p.parse_args()
    rows = hacks.resolve(a.hacks)
    D = int(round(a.r * 2))
    font = fit_number([h["value"] for h in rows],
                      2 * (a.r * R_RING - a.r * W_RING / 2 - a.r * PAD))
    print(f"  every dial at {font.size}px, the size '"
          f"{max((h['value'] for h in rows), key=len)}' fits in")
    sheet = Image.new("RGB", (len(rows) * (D + 40) + 40, D + 80), (14, 29, 36))
    for i, h in enumerate(rows):
        d = build(h, a.r, (26, 42, 50), False, font, 14)
        f = np.zeros((D, D, 3), np.float32)
        for layer, al in ((d["disc"], 1.0), (d["track"], 1.0), (d["arcs"][-1], 1.0),
                          (d["nums"][-1], 1.0)):
            al_ = layer[:, :, 3:4] / 255.0 * al
            f = f * (1 - al_) + layer[:, :, :3] * al_
        sheet.paste(Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)),
                    (40 + i * (D + 40), 40))
        print(f"    {h['name']:<20} {h['value']:>7}  {h['dir']}")
    sheet.save(a.out)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
