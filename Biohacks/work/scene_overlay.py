#!/usr/bin/env python3
"""
scene_overlay.py - the left circle: the hack itself, and it lighting first.

The other two variants get this circle from an image model. That round trip is
the slowest part of their day and the only part a person has to be present for:
write the prompt, paste it, wait, drop the poster back, check the waves survived.
This variant does not need it. A hack is an action rather than an object, and a
photograph of an action at 190px across in a vertical feed is a smudge, while a
line glyph at the same size is still a snowflake.

So `./render.sh day` produces a finished clip with nobody in the loop, and the
generator becomes optional rather than structural - `--scene poster` leaves the
circle alone for the topics that want photographs. That is not a saving of five
minutes. It is the difference between five clips a day and fifty, and on a feed
the second number is the whole strategy.

**It lights first.** The row reads left to right the way the liquid runs: the
glyph at the cue, the chip 0.08s later, the dial 0.18s after that. Cause, cost,
effect, in a quarter of a second. Lit together they are three things happening at
once and the row has no direction; lit in order the viewer is told what caused
what without a word being spent on it.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

import dial
import glyphs
import hacks

# The glyph does not brighten at its cue. It **takes the colour of its own wave**
# and keeps it for the rest of the clip.
#
# Brightening was the first version and it only works on a dark row: on a light
# one the ink is near-black, "brighter" means "more black", and the bloom around
# it is a shadow. Colour works on both.
#
# The second version took the *direction* colour instead - the same green, blue or
# amber the dial at the far end of the row draws - on the exercise variant's
# argument that a colour arriving at both ends of a row is what joins them. It
# was thrown out on sight: a green snowflake and a blue coffee cup are a colour
# system fighting the objects it is colouring, and the object wins every time.
# The dial keeps the direction colours, because a ring has no opinion about what
# green means; the glyph takes the liquid it pours.
#
# So the row reads: a snowflake the colour of the cold wave leaving it, a coffee
# cup the colour of the coffee. That is the food version's own rule - "the wave
# takes the colour of its food" - read from the other end, and it is the reason
# the palette here is chosen by the hour of the day rather than by taste.
#
# A glyph that keeps its colour is also a row that stays visibly done. On the last
# frame - the one a feed freezes on - all five are lit, and the clip reads as five
# things completed rather than one thing happening.
TURN = 0.22         # seconds to take the colour
GLOW = 0.60         # the bloom at the turn, as a fraction of full
GLOW_HOLD = 0.10    # and what it keeps afterwards
FIN_FLASH = 0.06
FIN_SETTLE = 0.20
FIN_GLOW = 0.75
REST = 0.82         # how present the glyph is before its row has fired
LUMA_GAP = 60.0     # how far the lit glyph must clear its disc. Measured on the
                    # shipped palette: the coffee wave lands 14 levels off a light
                    # disc and disappears, and every other row clears 60 unaided

SCALE = 0.92        # the glyph's box as a fraction of the circle's diameter


def wave_colour(base, mask, row, k, light):
    """The row's own liquid, as one colour, lifted until it reads on its disc.

    Read from the picture rather than passed in: the palette lives in the base
    image and nowhere else, and a second copy of it in a flag is a second copy to
    keep in step. The median over the row's masked pixels rather than the mean -
    the wave carries a specular highlight that runs to white, and a mean drags
    every colour a third of the way towards it.
    """
    a, b = int(row["stripe"][0] * k), int(row["stripe"][1] * k)
    m = mask[a:b] > 0.5
    if m.sum() < 64:
        return dial.ink(light)
    col = np.median(base[a:b][m], axis=0)

    # Then made to read. The disc is the row's colour shifted a little darker, so
    # a dark wave on a dark row (violet at luma 150 is not dark, but coffee at 88
    # is) would land within a few levels of what it is drawn on. Lift or drop the
    # glyph until it clears the disc by LUMA_GAP, keeping the hue: a glyph the
    # colour of its liquid is the point, and a glyph nobody can see is not.
    lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    ground = np.clip(np.float32(np.median(base[a + 8:b - 8, 4:20].reshape(-1, 3), axis=0))
                     + (-18 if not light else -22), 0, 255)
    for _ in range(24):
        if abs(lum(col) - lum(ground)) >= LUMA_GAP:
            break
        col = np.clip(col + (10.0 if lum(col) >= lum(ground) else -10.0), 0, 255)
    return tuple(float(v) for v in col)


def plan(rows, layout, W, H, times, base=None, mask=None, scale=SCALE, dy=0.0, lead=0.0):
    """One entry per row: the disc, the glyph, and the instant it lights."""
    L = json.load(open(layout)) if isinstance(layout, str) else layout
    k = W / 1536.0
    out = []
    for i, (h, row) in enumerate(zip(rows, L["rows"])):
        r = row["r"] * k
        cx, cy = L["anchor_l"] * k, row["cy"] * k + dy * k
        light = bool(row["light"])

        bg = (30, 34, 42)
        if base is not None:
            # The row's own colour, read at the left margin where nothing is ever
            # drawn. Sampled near the circle it picks up the wave instead.
            a, b = int(row["stripe"][0] * k), int(row["stripe"][1] * k)
            bg = tuple(np.median(base[a + 8:b - 8, 4:20].reshape(-1, 3), axis=0))

        size = int(round(r * 2 * scale))
        col = (wave_colour(base, mask, row, k, light)
               if base is not None and mask is not None else hacks.colour(h))
        # Two sprites of the same glyph: the resting one in the row's own ink, and
        # the lit one in the hack's colour. Cross-faded rather than recoloured per
        # frame - a recolour is a per-pixel pass on 190px square, 192 times, for a
        # result that is two fixed images and a number between them.
        g = glyphs.render(h["icon"], size, dial.ink(light))
        lit = glyphs.render(h["icon"], size, col)
        bloom = np.array(Image.fromarray(np.clip(lit, 0, 255).astype(np.uint8), "RGBA")
                         .filter(ImageFilter.GaussianBlur(size * 0.06))).astype(np.float32)
        out.append(dict(row=i, cx=cx, cy=cy, r=r, colour=col,
                        disc=dial.disc(r, bg, light), glyph=g, lit=lit, bloom=bloom,
                        t=(times[i] if i < len(times) else times[-1]) + lead,
                        name=h["name"], icon=h["icon"]))
    return out


def _turn(e, secs):
    """How far through the colour change the glyph is, 0 before its cue, 1 after."""
    if secs < e["t"]:
        return 0.0
    return min(1.0, (secs - e["t"]) / TURN) ** 0.6      # quick off the mark, then eased


def _glow(e, secs):
    g = 0.0
    if secs >= e["t"]:
        s = secs - e["t"]
        g = GLOW_HOLD + (GLOW - GLOW_HOLD) * max(0.0, 1.0 - s / (TURN * 2.4)) ** 2
    ft = e.get("fin_t")
    if ft is not None and secs >= ft:
        s = secs - ft
        f = max(0.0, 1.0 - max(0.0, s - FIN_FLASH) / FIN_SETTLE) ** 2
        g = max(g, GLOW_HOLD + (FIN_GLOW - GLOW_HOLD) * f)
    return g


def paint(frame, pl, secs):
    for e in pl:
        D = e["disc"].shape[0]
        dial.blend(frame, e["disc"], 1.0,
                   int(round(e["cx"] - D / 2.0)), int(round(e["cy"] - D / 2.0)))
        gs = e["glyph"].shape[0]
        gx, gy = int(round(e["cx"] - gs / 2.0)), int(round(e["cy"] - gs / 2.0))
        # The glyph is there from the first frame - it is what the row is about,
        # and a row whose subject only appears a second in is a row whose caption
        # nobody has read. What the cue changes is its colour, not its presence.
        p = _turn(e, secs)
        if p < 1.0:
            dial.blend(frame, e["glyph"], REST * (1.0 - p), gx, gy)
        if p > 0.0:
            dial.blend(frame, e["lit"], p, gx, gy)
        g = _glow(e, secs)
        if g > 0.006:
            dial.blend(frame, e["bloom"], g, gx, gy)


# ---------------------------------------------------------------------------
# The seam into engine/flowanim.py --overlay scene_overlay
# ---------------------------------------------------------------------------

def add_arguments(p):
    p.add_argument("--hacks", help="the five hacks, comma separated, top row first: "
                                   "'auto:MORNING LIGHT,COLD FINISH,...'. Looked up in "
                                   "hacks.json, which carries the number and the study "
                                   "it came from")
    p.add_argument("--hack-times", default="0.7,1.85,3.0,4.15,5.3",
                   help="when each row fires, in seconds. Not the 1,2,3.2,4.4,5.6 the "
                        "other two variants ship: a row here is a glyph, a chip and "
                        "then half a second of a dial counting, which is 0.55s longer "
                        "than a badge landing, and the finale needs the last one "
                        "settled before it starts. Row 1 also fires at 0.7 rather than "
                        "1.0, because a feed decides in about 1.5s and at 1.0 the first "
                        "number was not on screen until 1.28. And an even 1.15s beat "
                        "suits what this clip is - a day passing - better than their "
                        "accelerating one")
    p.add_argument("--scene", choices=["glyph", "poster"], default="glyph",
                   help="glyph draws the left circle here and needs no generator at "
                        "all; poster leaves it as the image model returned it")
    p.add_argument("--scene-scale", type=float, default=SCALE,
                   help="the glyph's box as a fraction of the circle's diameter")
    p.add_argument("--scene-dy", type=float, default=0.0)


def build(args, ctx):
    if not args.hacks or args.scene != "glyph":
        return None
    if not ctx["layout"]:
        raise SystemExit("--hacks needs --layout: the circles are where it says")
    times = [float(t) for t in args.hack_times.split(",")]
    pl = plan(hacks.resolve(args.hacks), ctx["layout"], ctx["W"], ctx["H"], times,
              base=ctx["base"], mask=ctx["mask"],
              scale=args.scene_scale, dy=args.scene_dy)
    print(f"  {len(pl)} glyphs drawn in the left circles, "
          f"lucide {glyphs.licence()} - no generator in the loop")
    for e in pl:
        print(f"    r{e['row'] + 1}: {e['icon']:<16} in its wave's own "
              f"({e['colour'][0]:.0f},{e['colour'][1]:.0f},{e['colour'][2]:.0f}), "
              f"lights at {e['t']:.2f}s")
    # Two rows drawn with the same glyph is a poster the eye reads as four rows
    # and a repeat. It is easy to walk into - `walk after lunch` and `7000 steps`
    # were both `footprints`, which is the right icon for each of them read on
    # its own - and it is invisible in the log unless it is named. Said rather
    # than fixed: which of the two should move is a decision about the topic.
    seen = {}
    for e in pl:
        seen.setdefault(e["icon"], []).append(e["row"] + 1)
    for icon, rows_ in seen.items():
        if len(rows_) > 1:
            print(f"    rows {', '.join(str(r) for r in rows_)} all draw "
                  f"'{icon}' - two circles the same is one circle the viewer "
                  f"stops reading. Give one of them another icon in hacks.json",
                  file=sys.stderr)
    return pl


def cues(pl):
    """The glyphs are the first thing in a row, not the last, so they do not set
    the finale. Reported anyway: the engine takes the maximum over every overlay
    that answers, and a module that stays quiet about its own timing is a module
    somebody later has to read to find out."""
    return sorted(e["t"] for e in pl)


def finale(pl, t0, ctx):
    at = (ctx.get("surge") or {}).get("at")
    for e in pl:
        e["fin_t"] = float(at(e["row"], e["cx"])) if at else float(t0)


def draw(frame, pl, secs):
    paint(frame, pl, secs)
