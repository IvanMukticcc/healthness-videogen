#!/usr/bin/env python3
"""
vitamin_overlay.py - the headline vitamin sitting in the right guide circle.

Organs puts an organ there and the generator draws it. This variant puts the
vitamin the food is known for, and **the generator is not asked for it at all**:
the prompt leaves the right circle empty, this module composites the ball
afterwards. `engine/micro/icons/` already holds it, at the app's own blue, with
the letter already on it.

That is not a shortcut around the generator, it is the trade the whole design
makes everywhere else - what must be identical is never regenerated. A generator
asked for "the vitamin C in this food" draws pills, a bottle or an orange, and
it draws a different one every time; and it cannot draw the letter, because the
prompt forbids text in three places for reasons `ImageSwap.txt` lists. So the one
thing on the poster that has to be exactly right is the one thing not left to a
roll of the dice.

    ../../engine/flowanim.py poster.png --overlay vitamin_overlay,micro_overlay \\
        --vitamin 'C,C,D,K,C' --micro '...' --layout base_<topic>_layout.json

THE BALL IS AT LEAST THE SIZE OF THE CIRCLE, AND THAT IS NOT COSMETIC.

The animator never paints inside a guide circle - 5.0% of the wave lies in there
and it is real liquid standing still, which is fine while a bowl or an organ is
on top of it. An empty right circle has nothing on top of it. So a ball smaller
than the mark would leave a crescent of motionless liquid beside moving liquid,
which is the speckles-that-stand-still failure `flow.md` already records. The
guide circle is r 137.5 at 1536, so the default diameter is 290 rather than 275:
the extra 15px is the antialiased rim, not a margin anybody chose.

WHY IT DOES NOT READ --micro-times

Both overlays want the five row instants, and the obvious economy is for this one
to read the flag the other declares. Biohacks did exactly that and its three
overlays stopped being runnable separately at all - `AttributeError: 'Namespace'
object has no attribute 'dial_lead'`, thrown from a module that had declared
nothing wrong. So this declares `--vitamin-times` of its own, with the same
default, and `render.sh` passes one shell variable into both. One source, two
flags, and either module still runs alone.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "engine"))

import micro_overlay as mo                                      # noqa: E402

# The gesture is micro_overlay's, imported rather than restated. An organ
# answering its row and a vitamin answering its row are the same event in two
# variants of one series, and a second copy of these numbers is a second copy
# that drifts. Rule 1's argument, one level down from the tools.
LIFT, RISE, SETTLE = mo.ORGAN_LIFT, mo.ORGAN_RISE, mo.ORGAN_SETTLE
RESIDUE = mo.ORGAN_RESIDUE
GLOW_ROW, GLOW_FIN, GLOW_SIGMA = mo.GLOW_ROW, mo.GLOW_FIN, mo.GLOW_SIGMA

DIAMETER = 290.0            # at 1536 wide; the guide circle is 275


def sprite(name, side, icon_dir):
    """The badge ball at `side` px on its shadow canvas, as a float RGBA array."""
    p = os.path.join(icon_dir, f"{name.upper().replace(' ', '').replace('-', '')}.png")
    if not os.path.exists(p):
        raise SystemExit(f"no ball for vitamin '{name}' - build it with "
                         f"../../engine/micro_icons.py --one '{name}:v'")
    a = mo.sprite(p)                       # ball + drop shadow, canvas = D * SHADOW
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    return np.array(im.resize((side, side), Image.LANCZOS)).astype(np.float32)


def plan(names, layout, W, H, times, diameter=DIAMETER, stagger=0.09,
         icon_dir=mo.MICRO_DIR, sigma=GLOW_SIGMA):
    """One ball per row: where it sits, what it looks like, when it answers.

    Its centre is the right anchor from the layout file, which is the same point
    the wave's right tip lands on - so the liquid runs into the ball the way it
    runs into an organ, rather than past it.
    """
    L = json.load(open(layout)) if isinstance(layout, str) else layout
    k = W / 1536.0
    side = max(2, int(round(diameter * k * mo.SHADOW)))
    s = max(1.0, sigma * k)
    cache, out = {}, []
    for i, (name, row) in enumerate(zip(names, L["rows"])):
        if name not in cache:
            cache[name] = sprite(name, side, icon_dir)
        img = cache[name]
        a = img[:, :, 3] / 255.0
        glow = np.dstack([np.full(a.shape + (3,), 255.0, np.float32),
                          ndimage.gaussian_filter(a, s) * 255.0])
        cx, cy = L["anchor_r"] * k, row["cy"] * k
        t0 = times[i] if i < len(times) else times[-1]
        out.append(dict(row=i, name=name, img=img, glow=glow, cx=cx, cy=cy,
                        x0=int(round(cx - side / 2.0)),
                        y0=int(round(cy - side / 2.0)),
                        d=diameter * k, side=side,
                        t=t0 + stagger))       # the row answers on its own cue
    return out


def paint(frame, pl, secs):
    """The ball is on screen from frame 0 and LIGHTS on its cue.

    Same shape as the organ, and for the same reason: something that arrives in
    the last second is a surprise, and something that has been there all along
    and then answers is a payoff. It is also what the right circle does in the
    other variant, and the two are one series.
    """
    for b in pl:
        a = mo._organ_alpha(b, secs)
        img = b["img"]
        if a > 0.004:
            # Screened towards white, not multiplied, which is micro_overlay's
            # choice and is right here for a different reason: the ball's
            # specular dots are at 255 and a multiply would take them down.
            img = img.copy()
            img[:, :, :3] = 255.0 - (255.0 - img[:, :, :3]) * (1.0 - a)
        mo._blend(frame, img, 1.0, b["x0"], b["y0"])
        if a > 0.004:
            fin = b.get("fin_t") is not None and secs >= b["fin_t"]
            g = a * (GLOW_FIN if fin else GLOW_ROW)
            if g > 0.01:
                mo._blend(frame, b["glow"], g, b["x0"], b["y0"])


# ---------------------------------------------------------------------------
# The seam into engine/flowanim.py --overlay vitamin_overlay
# ---------------------------------------------------------------------------

def add_arguments(p):
    p.add_argument("--vitamin",
                   help="the five headline vitamins, top row first: 'C,C,D,K,C'. "
                        "vitamins.py --vitamins derives them from topics.json, so "
                        "they are not typed here twice")
    p.add_argument("--vitamin-times", default="0.25,1.35,2.45,3.55,4.65",
                   help="when each row's ball lights. The same five instants the "
                        "badges use - render.sh passes one variable into both - "
                        "but its own flag, so either overlay still runs alone")
    p.add_argument("--vitamin-d", type=float, default=DIAMETER,
                   help="ball diameter at 1536 wide. The guide circle is 275 and "
                        "nothing smaller than it may be used: the animator does "
                        "not paint inside a circle, so bare circle is standing "
                        "liquid next to moving liquid")
    p.add_argument("--vitamin-stagger", type=float, default=0.09,
                   help="delay after the row's cue before the ball answers")
    p.add_argument("--vitamin-dir", default=mo.MICRO_DIR)


def build(args, ctx):
    if not args.vitamin:
        return None
    if not ctx["layout"]:
        sys.exit("--vitamin needs --layout: the ball sits on the right guide "
                 "circle, and the layout file is what says where that is")
    L = ctx["layout"]
    if isinstance(L, str):
        L = json.load(open(L))
    names = [n.strip() for n in args.vitamin.split(",") if n.strip()]
    if len(names) != len(L["rows"]):
        sys.exit(f"--vitamin has {len(names)} names for {len(L['rows'])} rows")
    if args.vitamin_d < 275.0:
        sys.exit(f"--vitamin-d {args.vitamin_d:g} is inside the guide circle (275). "
                 f"Read this module's docstring before lowering it.")
    times = [float(t) for t in args.vitamin_times.split(",")]
    pl = plan(names, L, ctx["W"], ctx["H"], times,
              diameter=args.vitamin_d, stagger=args.vitamin_stagger,
              icon_dir=args.vitamin_dir)
    lit = ", ".join(f"{b['t']:.2f}" for b in pl)
    print(f"  {len(pl)} vitamin balls in the right circles: "
          f"{', '.join(b['name'] for b in pl)}, lighting at {lit}s")
    return pl


def finale(pl, t0, ctx):
    """The balls light once more as the surge reaches their column.

    Act one of a two-act cut has no finale - it is not the end, and a chord in
    the middle of a clip was the user's own objection - so this runs only in a
    single-act cut. It is here because the seam is the seam, not because the
    shipped Vitamins clip uses it.
    """
    at = (ctx.get("surge") or {}).get("at")
    for b in pl:
        b["fin_t"] = float(at(b["row"], b["cx"])) if at else float(t0)


def draw(frame, pl, secs):
    paint(frame, pl, secs)
