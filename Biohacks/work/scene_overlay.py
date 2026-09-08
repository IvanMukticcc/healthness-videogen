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

**It lights first, and it sends something.** The row reads left to right the way
the liquid runs:

    t0 + 0.00   the glyph takes its colour        the hack
    t0 + 0.02   a pulse leaves it down the wave   the effect, travelling
    t0 + 0.08   the chip lands                    what it costs you
    t0 + 0.30   the pulse arrives, the dial       what it changes
                starts counting

Lit together they are three things happening at once and the row has no
direction. Lit in order they are a sentence, and nobody has to be told it.

The pulse is why the liquid is here at all. In the food version the wave *is* the
food, pouring into the organ it feeds - the whole design is that one image. A
hack does not pour, so for three cuts this variant had a row where the glyph lit,
a chip landed and a dial counted, with a river running underneath that belonged
to none of it. The pulse joins them: the light leaves the thing you did and
arrives at the thing that changed, and the dial starts on the frame it lands.
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

# The pulse. Light and nothing else, exactly like the engine's `--surge`, and for
# the same reason: the surface travels a whole number of ribbon lengths over the
# clip and that is what makes the loop seamless, so nothing may push the liquid
# faster. What it can do is put more light in it and move the light.
#
# **Added, not multiplied**, and that is the second thing this got wrong.
#
# A multiply is what the engine's own surge does and what every other light pass
# in this repository does, so it was the obvious choice. It clips. The palette
# here is chosen by the hour of the day, so row 1 is dawn amber at luminance 177
# with specular highlights already near 255, and 1.12x of 250 is 280 - the lift
# is thrown away exactly where the wave is brightest. Measured against a control
# render with the pulse off, one amount for all five rows gave:
#
#     r1 amber  luma 177   +3.89        r4 coffee luma  97   +8.61
#     r2 blue   luma 113  +10.14        r5 violet luma 153   +7.20
#     r3 lime   luma 183   +7.20
#
# A luminance trim was tried first - scale the multiply by 150/luma - on the
# theory that a dark wave needs more of it. That is the wrong model twice over:
# lift = luma x amount says the trim should have equalised them exactly, and it
# did not, because the ceiling and not the luminance is what row 1 was hitting.
#
# Adding a fixed number of levels, bounded by the headroom each pixel actually
# has, is equal across rows by construction and cannot clip. The wave's gloss
# survives because the addition is small and uniform: a specular pixel at 250
# takes what is left of 255 and a mid-tone at 120 takes all 7, so the highlight
# stays the brightest thing in the liquid.
PULSE = 10.0        # levels the crest adds at its centre
PULSE_DUR = 0.28    # glyph to dial. Under 0.20 it is a flash with no direction
PULSE_W = 0.13      # the crest's width, as a fraction of the ribbon's arc length
PULSE_LEAD = 0.02   # after the glyph. Not 0: the eye needs the cause first
PULSE_ROOM = 0.90   # of the headroom a pixel has left, at most

_PARAMS = [PULSE, PULSE_DUR, PULSE_W]


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


def pulses(layout, W, H, geo, mask, times, base=None, lead=PULSE_LEAD):
    """One entry per row: which pixels of the liquid it lights, and where each of
    them sits along the wave.

    **In arc length, not in x.** The engine's own surge says why: a band placed
    at a column is a vertical line, and a vertical line across a wave that is
    climbing cuts across it instead of running with it. `ctx["geo"]` carries the
    arc length of every column, which is the same coordinate the engine's streaks
    and its finale highlight both use, so this travels the way they do.

    The row's ribbon is found the way `wave_centre_curves` finds it - the geo
    whose middle is nearest the layout row's centre - rather than by index, so a
    row the animator failed to detect shifts nothing.
    """
    L = json.load(open(layout)) if isinstance(layout, str) else layout
    k = W / 1536.0
    m = mask > 0.5
    out = []
    for i, row in enumerate(L["rows"]):
        cy = row["cy"] * k
        g = min(geo, key=lambda g: abs(0.5 * (g["top"].mean() + g["bot"].mean()) - cy))
        y0 = max(0, int(row["stripe"][0] * k))
        y1 = min(H, int(row["stripe"][1] * k))
        idx = np.nonzero(m[y0:y1])
        if len(idx[0]) < 64:
            print(f"    r{i + 1}: no liquid found in the stripe - no pulse")
            continue
        arc = np.asarray(g["arc"], np.float32)
        span = float(arc[-1] - arc[0])
        if span <= 1:
            continue
        a = (arc - arc[0]) / span
        col = np.clip(idx[1] - g["x0"], 0, len(a) - 1)

        lum = float(np.dot(np.median(base[y0:y1][m[y0:y1]], axis=0),
                           (0.299, 0.587, 0.114))) if base is not None else 0.0
        out.append(dict(row=i, y0=y0, iy=idx[0], ix=idx[1], pos=a[col].astype(np.float32),
                        t=(times[i] if i < len(times) else times[-1]) + lead,
                        px=int(len(idx[0])), lum=lum))
    return out


def paint_pulses(frame, ps, secs, amount=PULSE, dur=PULSE_DUR, width=PULSE_W):
    """`amount` levels added to the liquid, and to nothing else.

    Bounded by what each pixel has left before 255, so the crest never clips and
    never turns a specular highlight into a flat white patch. See the note on
    PULSE above for why this is not the multiply everything else here uses.
    """
    for e in ps:
        s = secs - e["t"]
        if s < 0 or s > dur:
            continue
        p = s / dur
        p = p * p * (3 - 2 * p)                    # ease in and out of the run
        band = np.exp(-((e["pos"] - p) / width) ** 2)
        # Faded at both ends of its run, so the crest is never cut off mid-row by
        # the clock running out - it arrives, and then it is gone.
        band *= min(1.0, 4.0 * min(p, 1.0 - p) + 0.25)
        sub = frame[e["y0"]:, :][e["iy"], e["ix"]]
        room = (255.0 - sub) * PULSE_ROOM
        frame[e["y0"]:, :][e["iy"], e["ix"]] = sub + np.minimum(
            room, amount * band[:, None])


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


class Plan(list):
    """The glyphs, with the row pulses riding along, so the seam stays the three
    functions wide it is meant to be rather than becoming a second plan the
    engine has to know about. `micro_overlay.Plan` carries its organs the same
    way and for the same reason."""
    pulses = ()


def paint(frame, pl, secs):
    # Under the glyphs and under everything the other two modules draw: it is in
    # the liquid, and the liquid runs behind all of it.
    paint_pulses(frame, getattr(pl, "pulses", ()), secs, *_PARAMS)
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
    p.add_argument("--hack-times", default="0.65,1.75,2.85,3.95,5.05",
                   help="when each row fires, in seconds. Not the 1,2,3.2,4.4,5.6 the "
                        "other two variants ship: a row here is a glyph, a chip and "
                        "then half a second of a dial counting, which is 0.55s longer "
                        "than a badge landing, and the finale needs the last one "
                        "settled before it starts, and the pulse added 0.12s to a row. Row 1 "
                        "also fires at 0.65 rather than "
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
    p.add_argument("--pulse", type=float, default=PULSE,
                   help="levels the crest running the row adds at its centre. 0 turns it "
                        "off and the liquid goes back to being a river that belongs "
                        "to none of the three things happening on top of it")
    p.add_argument("--pulse-dur", type=float, default=PULSE_DUR,
                   help="how long the crest takes to cross. It should land on the "
                        "frame the dial starts counting - see --dial-lead")
    p.add_argument("--pulse-width", type=float, default=PULSE_W)


def build(args, ctx):
    if not args.hacks or args.scene != "glyph":
        return None
    if not ctx["layout"]:
        raise SystemExit("--hacks needs --layout: the circles are where it says")
    times = [float(t) for t in args.hack_times.split(",")]
    pl = Plan(plan(hacks.resolve(args.hacks), ctx["layout"], ctx["W"], ctx["H"], times,
                   base=ctx["base"], mask=ctx["mask"],
                   scale=args.scene_scale, dy=args.scene_dy))
    _PARAMS[:] = [args.pulse, args.pulse_dur, args.pulse_width]
    if args.pulse > 0:
        pl.pulses = pulses(ctx["layout"], ctx["W"], ctx["H"], ctx["geo"],
                           ctx["mask"], times, base=ctx["base"])
        land = [e["t"] + args.pulse_dur for e in pl.pulses]
        print(f"  {len(pl.pulses)} pulses of {args.pulse:+.0f} levels cross the liquid and "
              f"land at {', '.join(f'{t:.2f}' for t in land)}s"
              f"  ({sum(e['px'] for e in pl.pulses)} px of liquid lit)")
        for e in pl.pulses:
            print(f"    r{e['row'] + 1}: wave luma {e['lum']:5.1f}, "
                  f"{e['px']} px of liquid")
        if abs((land[0] if land else 0) - (times[0] + args.dial_lead)) > 0.03:
            print(f"    the pulse lands at {land[0]:.2f} and the dial starts at "
                  f"{times[0] + args.dial_lead:.2f} - they are meant to be the same "
                  f"instant, which is the whole of what the pulse is for",
                  file=sys.stderr)
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
