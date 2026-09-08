#!/usr/bin/env python3
"""
body_overlay.py - the body on the right of every row, and the muscle igniting on it.

`bodymap.py` draws the figure; this decides where it sits, which way it faces,
and what happens on the frame a badge lands. It is the half of the idea that the
badges alone do not carry: a ball saying LATS is a word, and a word is read once.
The same red arriving on the back of a figure at the same instant is a place, and
a place is what the next row is compared against.

The disc under it is the guide circle the base already draws - the one the bowl
used to sit in - filled with the row's own background colour. Without it the
ghost is a translucent figure standing on a glossy wave and the two read as one
smeared shape; with it the wave ends where the organ used to end it, and the
figure has a ground that is the same on every row whatever colour the row is.

The ignition is a flash and then a settle, on the badge's own cue: white-hot for
about a tenth of a second, then down onto the tier colour with a low glow left
around it. A muscle that simply appears is a state; a muscle that flares is an
event, and it is the same event as the badge landing and the hit sounding.
"""
import json
import os

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

import bodymap
import muscles
from muscle_overlay import blend

FLASH = 0.13        # seconds of white-hot
SETTLE = 0.34       # and how long it takes to come down onto the colour
GLOW = 0.55         # how far the bloom reaches, as a fraction of the muscle
LIFT = 0.62         # how far towards white the flash goes

# The finale's own envelope, and it is not the landing envelope again. Two
# reasons it is shorter and dimmer. The last row's highlight reaches its body at
# about 7.05s and the clip's last frame is the one a feed freezes on, so
# everything has to be still by ~7.2. And the landing flash lifts towards white,
# which is right for one muscle arriving on a dark body and wrong here: at the
# finale every region on the body lights at once, and washing them all towards
# white is exactly how glutes beside hamstrings become one red mass. So the
# finale multiplies instead - every pixel of a region keeps its ratio to the
# darker rim drawn around it, and the rim is what carries the anatomy.
FIN_FLASH = 0.07    # seconds at full lift
FIN_SETTLE = 0.17   # and the fall
FIN_LIFT = 0.62     # multiplied, not mixed towards white
FIN_GLOW = 0.85     # the bloom carries the brightness the wash used to


def _glass(r, feather=2.0):
    """The ground for a photographic row, where there is no row colour to take.

    A disc built from the stripe colour is right when the row IS that colour and
    wrong the moment the row is a photograph: on the light scene rows of the
    first CONSTANT TENSION poster it came out as a pale grey coin on a white
    wall, which reads as a sticker rather than as an instrument. Biohacks met the
    same thing with its dials and put them on glass. So: near-black, mostly
    opaque, with a bright rim - it works over a bright room and a dark one alike
    because it does not try to belong to either.
    """
    D = int(round(r * 2))
    yy, xx = np.mgrid[0:D, 0:D]
    d = np.hypot(xx - (D - 1) / 2.0, yy - (D - 1) / 2.0)
    a = np.clip((r - 1 - d) / feather, 0, 1)
    rim = np.clip((d - (r - 3.0)) / 2.0, 0, 1) * a
    col = (np.float32([18, 18, 22])[None, None, :] * (1 - rim[:, :, None])
           + np.float32([235, 235, 240])[None, None, :] * rim[:, :, None])
    return np.dstack([col, a * 255.0 * 0.88]).astype(np.float32)


def _disc(r, rgb, light, feather=2.0):
    """The ground the figure stands on: the row's colour, a touch away from it,
    with a rim. Not the row's exact colour - a disc that matches its background
    perfectly is invisible, and the point is to end the wave somewhere."""
    D = int(round(r * 2))
    yy, xx = np.mgrid[0:D, 0:D]
    d = np.hypot(xx - (D - 1) / 2.0, yy - (D - 1) / 2.0)
    a = np.clip((r - 1 - d) / feather, 0, 1)
    shift = -16 if not light else 14
    body = np.clip(np.float32(rgb) + shift, 0, 255)
    rim = np.clip((d - (r - 3.0)) / 2.0, 0, 1) * np.clip((r - 1 - d) / feather, 0, 1)
    edge = np.clip(np.float32(rgb) + (52 if not light else -44), 0, 255)
    col = body[None, None, :] * (1 - rim[:, :, None]) + edge[None, None, :] * rim[:, :, None]
    return np.dstack([col, a * 255.0 * 0.97]).astype(np.float32)


def plan(rows, layout, W, H, times, stagger=0.09, base=None, scale=2.20,
         dy=0.0, disc=True):
    """One entry per row: the disc, the figure, and one plane per muscle with the
    instant it lights.

    `scale` is the figure's height as a multiple of the circle's radius. At 2.20
    the head and the feet run a little past the disc, which is what stops the
    figure reading as a sticker inside a button.
    """
    L = json.load(open(layout)) if isinstance(layout, str) else layout
    k = W / 1536.0
    out = []
    for i, (names, row) in enumerate(zip(rows, L["rows"])):
        if not names:
            continue
        t0 = times[i] if i < len(times) else times[-1]
        r = row["r"] * k
        cx = L["anchor_r"] * k
        cy = row["cy"] * k + dy * k
        light = bool(row["light"])
        # On glass the ground is near-black whatever the row is, so the figure is
        # drawn for a dark ground even on a light row. Left on the row's own flag
        # it comes out dark on dark: the first scene render put a charcoal figure
        # on a charcoal coin and only the lit muscles were visible.
        fig_light = light and disc != "glass"
        view = muscles.view_for(names)

        bg = (30, 34, 42)
        if base is not None:
            # The row's own colour, read where nothing is ever drawn: the left
            # margin of the stripe. Sampling near the circle picks up the wave.
            a, b = int(row["stripe"][0] * k), int(row["stripe"][1] * k)
            bg = tuple(np.median(base[a + 8:b - 8, 4:20].reshape(-1, 3), axis=0))

        # `scale` is the figure's HEIGHT against the radius, not against the
        # diameter: at 2.20 the figure stands 296px tall in a 275px circle, so
        # the head and the feet run about ten pixels past it. Read as a diameter
        # this is 4.4r and the arms hang a quarter of the poster out either side.
        size = int(round(r * scale))
        tiers = {m: t for m, t in names}
        fig, planes = bodymap.layers(view, size, tiers, light=fig_light,
                                     height=size * 0.98, top=size * 0.01)

        muscle = []
        for j, (m, tier) in enumerate(names):
            p = planes.get(m)
            if p is None:
                # Nothing of it shows from this side. The badge still lands and
                # still sounds - but it is a dead beat on the body, so say so
                # rather than letting it pass unnoticed in a finished cut.
                print(f"    r{i + 1}: {muscles.label(m)} does not show from the "
                      f"{view} - its badge lands over an unlit body")
                continue
            g = Image.fromarray(np.clip(p, 0, 255).astype(np.uint8), "RGBA") \
                     .filter(ImageFilter.GaussianBlur(size * 0.035))
            muscle.append(dict(plane=p, glow=np.array(g).astype(np.float32),
                               t=t0 + j * stagger, name=m, tier=tier))

        out.append(dict(row=i, cx=cx, cy=cy, r=r, size=size, view=view, fig=fig,
                        muscle=muscle, light=light,
                        disc=(_glass(r) if disc == "glass"
                              else _disc(r, bg, light) if disc else None)))
    return out


def paint(frame, pl, secs):
    """The body is there from the first frame; only the muscles are timed. A
    figure that fades in with its first badge leaves the right third of the
    poster empty for a second, and a feed's first frame is the whole audition."""
    for b in pl:
        if b["disc"] is not None:
            d = b["disc"]
            blend(frame, d, 1.0,
                  int(round(b["cx"] - d.shape[1] / 2.0)),
                  int(round(b["cy"] - d.shape[0] / 2.0)))
        x0 = int(round(b["cx"] - b["size"] / 2.0))
        y0 = int(round(b["cy"] - b["size"] / 2.0))
        blend(frame, b["fig"], 1.0, x0, y0)
        for m in b["muscle"]:
            s = secs - m["t"]
            if s < 0:
                continue
            # Up in a couple of frames, then the flash decays. Squared, so most
            # of the white is gone before the badge has finished its overshoot
            # and the two events read as one.
            up = min(1.0, s / 0.05)
            f = max(0.0, 1.0 - max(0.0, s - FLASH) / SETTLE) ** 2
            pl_ = m["plane"]
            if f > 0.02:
                lit = pl_.copy()
                lit[:, :, :3] = lit[:, :, :3] * (1 - LIFT * f) + 255.0 * (LIFT * f)
                blend(frame, lit, up, x0, y0)
            else:
                blend(frame, pl_, up, x0, y0)
            g = 0.30 + 0.70 * f
            if g > 0.02:
                blend(frame, m["glow"], up * g * GLOW, x0, y0)

        # The finale: every region on this body, at once, on the frame the
        # highlight reaches its circle. One pass over the planes already held -
        # nothing new is planned or drawn, they are simply lit again.
        ft = b.get("fin_t")
        if ft is None or secs < ft:
            continue
        s = secs - ft
        f = max(0.0, 1.0 - max(0.0, s - FIN_FLASH) / FIN_SETTLE) ** 2
        if f <= 0.02:
            continue
        for m in b["muscle"]:
            if secs < m["t"]:
                continue                    # not lit yet; the finale does not pre-light it
            lit = m["plane"].copy()
            lit[:, :, :3] = np.clip(lit[:, :, :3] * (1.0 + FIN_LIFT * f), 0, 255)
            blend(frame, lit, 1.0, x0, y0)
            blend(frame, m["glow"], f * FIN_GLOW * GLOW, x0, y0)


def cues(pl):
    """The instants a muscle lights, for anything that has to agree with them."""
    return sorted(m["t"] for b in pl for m in b["muscle"])


# ---------------------------------------------------------------------------
# The seam into engine/flowanim.py. Named before muscle_overlay on --overlay:
# the body is drawn first, so a badge is never behind it.
# ---------------------------------------------------------------------------

def add_arguments(p):
    p.add_argument("--body", type=int, default=1,
                   help="0 leaves the right circle empty, for a poster that fills it itself")
    p.add_argument("--body-scale", type=float, default=2.20,
                   help="figure height as a multiple of the guide circle's radius; over "
                        "2.0 the head and feet run past the disc, which is what stops it "
                        "reading as a sticker inside a button")
    p.add_argument("--body-disc", default="1",
                   help="1 takes the row's own colour, which is right when the row IS "
                        "a colour. 'glass' is for a photographic row, where there is no "
                        "row colour to take and a stripe-coloured coin reads as a "
                        "sticker. 0 stands the figure straight on the picture")
    p.add_argument("--lifter-r", type=float, default=200.0,
                   help="how far out from the left circle to look for the lifter, in "
                        "1536-wide poster pixels. 0 leaves the animator's own reading "
                        "of what is artwork alone")


def refine_art(art, ctx):
    """The lifter fills the left circle, and he is half again as wide as the mark.

    The animator reads artwork off the base: a patch that differs from it, or one
    carrying detail the flat stripe underneath does not. Both tests are right
    about a bowl and wrong about a photographed athlete. On PULL DAY the
    generator returned each lifter on an opaque disc of radius 180 against the
    circle's 138, inverted against its row - a white disc on the dark rows, a
    near-black one on the light. Inside it, his black singlet on a dark row is
    within the colour threshold of the row behind him and as flat as it is, so
    the liquid was painted across his chest, and pale crescents of his disc were
    sampled into the wave's texture and carried downstream, arriving in the
    middle of the row as blocks of the wrong colour. 8497 px of him moved.

    What the generator will draw there cannot be predicted, but where it will
    draw it can: it fills the circle it is given, centred on it, opaque, because
    the prompt asks it to cover the mark completely. So the shape is found rather
    than described - out from the circle's centre along every angle, to the
    furthest pixel that still differs from the base, and everything nearer than
    that is the lifter whatever colour it happens to be. An athlete smaller than
    the search radius yields a smaller silhouette; the radius is only where
    looking stops.

    It is deliberately not a plain difference test over the whole row. The wave
    is the one thing in there that legitimately differs from the base - the
    generator repaints it glossier - and protecting it would freeze the liquid
    the clip is made of.
    """
    if getattr(ctx["args"], "lifter_r", 0) <= 0:
        return art
    L = ctx["layout"]
    L = json.load(open(L)) if isinstance(L, str) else L
    W, H, k = ctx["W"], ctx["H"], ctx["W"] / 1536.0
    R = ctx["args"].lifter_r * k
    d = np.abs(np.float32(ctx["poster"]) - np.float32(ctx["base"])).max(axis=2)
    # The same 45 levels the animator's own colour test uses, opened so that jpeg
    # speckle on the wave's gloss is not an edge.
    strong = ndimage.binary_opening(d > 45, np.ones((3, 3)))
    yy, xx = np.mgrid[0:H, 0:W]
    BINS = 720
    added = 0
    for row in L["rows"]:
        cx, cy = L["anchor_l"] * k, row["cy"] * k
        lo, hi = row["stripe"][0] * k, row["stripe"][1] * k
        rad = np.hypot(xx - cx, yy - cy)
        win = (rad < R) & (yy >= lo) & (yy < hi)      # never past the row's own stripe
        b = (((np.arctan2(yy - cy, xx - cx) + np.pi) / (2 * np.pi) * BINS)
             .astype(np.int32) % BINS)
        edge = np.zeros(BINS, np.float32)
        sel = win & strong
        np.maximum.at(edge, b[sel], rad[sel])
        # One stray pixel would otherwise hold a ray of live liquid all the way
        # out to it. A real edge is hundreds of bins wide and survives a median
        # across its neighbours; a speck is one or two and does not.
        edge = ndimage.median_filter(edge, size=9, mode="wrap")
        keep = win & (rad <= edge[b])
        added += int((keep & ~art).sum())
        art = art | keep
    print(f"  lifters: {added} px taken back from the liquid, "
          f"searched to {ctx['args'].lifter_r:.0f}px of the left circle")
    return art


def build(args, ctx):
    if not args.muscles or not args.body:
        return None
    import muscle_overlay
    times = [float(t) for t in args.muscle_times.split(",")]
    # The same rows and the same times as the badges: a muscle lights on the frame
    # its badge lands. The clean base lets each row's disc take that row's own
    # background colour instead of one grey for all five.
    pl = plan(muscle_overlay.resolve(args.muscles), ctx["layout"], ctx["W"], ctx["H"],
              times, stagger=args.muscle_stagger, base=ctx["base"],
              scale=args.body_scale, dy=args.muscle_dy,
              disc=("glass" if str(args.body_disc).lower() == "glass"
                    else bool(int(args.body_disc))))
    print("  bodies: " + ", ".join(f"r{i + 1} {x['view']}" for i, x in enumerate(pl)))
    return pl


def finale(pl, t0, ctx):
    """Light every body again, each one as the highlight reaches its circle.

    Not on one frame for all five. The surge is a cascade - one row every 0.06s,
    top to bottom - and a body that lights before the light gets to it reads as
    two unrelated events; lit as it arrives, the whole poster reads as one
    gesture travelling down it. `at(row, x)` is the engine's, because only it
    has the arc length the band actually travels.

    Without --surge there is no cascade to follow, so they light together on the
    finale's own instant, which is still better than not answering the count.
    """
    at = (ctx.get("surge") or {}).get("at")
    for b in pl:
        b["fin_t"] = float(at(b["row"], b["cx"])) if at else float(t0)
    ts = sorted(b["fin_t"] for b in pl)
    print(f"  bodies light again at {', '.join(f'{t:.2f}' for t in ts)}s, "
          f"settled by {ts[-1] + FIN_FLASH + FIN_SETTLE:.2f}s")


def draw(frame, pl, secs):
    paint(frame, pl, secs)
