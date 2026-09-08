#!/usr/bin/env python3
"""
muscle_overlay.py - the muscle badges popping onto a finished frame.

`flowanim.py` owns the liquid and nothing else; this owns the badges. It is a
module, not a script: `plan()` works out once where every badge goes and when,
and `paint()` draws whichever ones are alive into the frame it is handed.

Where they go is read from the same `_layout.json` the base wrote, so the badges
sit on the row the way the bowl and the organ do - between the two guide circles,
on the row's centre line, centred on the gap. Working it out from the picture
would drift the moment a palette changes.

How they enter: nothing for the first frames, then a back-eased pop from zero
through about 15% over-scale and down onto 1.0, with a thin ring thrown off at
the moment of arrival. The over-scale is the whole trick - a badge that fades in
is furniture, a badge that overshoots is an event, and an event is what stops a
thumb.

The landing time is also the instant the muscle lights on the body to its right
(`body_overlay`) and the instant the hit sounds (`muscle_audio`). All three read
the same cue list, which `flowanim.py` writes, because three tables of times is
three chances for one of them to be a frame out.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import muscles

HERE = os.path.dirname(os.path.abspath(__file__))
MUSCLE_DIR = os.path.join(HERE, "icons")
EXERCISES = os.path.join(HERE, "exercises.json")

POP = 0.42          # seconds from nothing to settled
RISE = 0.10         # of that, how long the badge is still fading up
RING = 0.34         # how long the shock ring lives
SHADOW = 1.30       # sprite canvas, as a multiple of the ball


# ------------------------------------------------------------------ sprites

def sprite(path, shadow=0.34):
    """The ball on a larger transparent canvas with a soft shadow under it, so a
    badge landing on a bright wave still has an edge."""
    ball = Image.open(path).convert("RGBA")
    D = ball.width
    C = int(D * SHADOW)
    off = int(D * 0.035)
    pad = (C - D) // 2
    sh = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    m = Image.new("L", (C, C), 0)
    ImageDraw.Draw(m).ellipse((pad, pad + off, pad + D, pad + D + off), fill=int(255 * shadow))
    m = m.filter(ImageFilter.GaussianBlur(D * 0.045))
    sh.putalpha(m)
    out = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    out.alpha_composite(sh)
    out.alpha_composite(ball, (pad, pad))
    return np.array(out).astype(np.float32)


def resolve(spec, table=None):
    """'auto:BENCH PRESS,PULL-UP,...' -> the muscles each lift works.

    Anything else is taken literally: rows separated by ';', muscles by ',',
    each optionally with its tier - 'Chest:p,Triceps:s;Lats:p,Biceps:s'. Both
    forms come back as rows of (key, tier), which is what everything downstream
    wants: the badge file, the colour on the body, and the note of the hit.
    """
    if not spec:
        return []
    if spec.startswith("auto:"):
        table = table or json.load(open(EXERCISES))
        # Longest key first, or 'INCLINE BENCH PRESS' and 'BENCH PRESS' both
        # answer to 'bench press' and whichever the file lists first wins.
        keys = sorted((k for k in table if not k.startswith("_")), key=len, reverse=True)
        rows = []
        for name in spec[5:].split(","):
            q = name.strip().lower()
            hit = table.get(q)
            if hit is None:                      # 'BARBELL BACK SQUAT' -> 'back squat'
                for k in keys:
                    if k in q:
                        hit = table[k]
                        break
            if hit is None:
                raise SystemExit(f"no muscles known for '{name.strip()}' "
                                 f"- add it to {os.path.basename(EXERCISES)}")
            rows.append([muscles.parse(m) for m in hit])
        return rows
    return [[muscles.parse(m) for m in row.split(",") if m.strip()]
            for row in spec.split(";")]


# ------------------------------------------------------------------ planning

def plan(rows, layout, W, H, times, diameter=210.0, gap=22.0, stagger=0.09,
         dy=0.0, muscle_dir=MUSCLE_DIR, seconds=8.0, fade=0.4, curves=None):
    """One entry per badge: its sprite, where it lands, and when.

    `curves` is one x -> y callable per row, the wave's own centre line. Given it,
    a badge sits where the liquid actually is at its column rather than on the
    row's centre, so a row of badges rides the S instead of cutting across it."""
    L = json.load(open(layout)) if isinstance(layout, str) else layout
    k = W / 1536.0
    cache = {}
    out = []
    for i, (names, row) in enumerate(zip(rows, L["rows"])):
        if not names:
            continue
        t0 = times[i] if i < len(times) else times[-1]
        n = len(names)
        d = diameter * k
        g = gap * k
        # The gap between the two guide circles is all the room there is: the
        # bowl fills one and the organ the other, and a badge over either of them
        # covers the thing the row is about.
        x_lo = (L["anchor_l"] + row["r"]) * k + 16 * k
        x_hi = (L["anchor_r"] - row["r"]) * k - 16 * k
        room = x_hi - x_lo
        if n * d + (n - 1) * g > room:                 # shrink to fit, never overflow
            d = (room - (n - 1) * g) / n
        span = n * d + (n - 1) * g
        x = (x_lo + x_hi) / 2.0 - span / 2.0 + d / 2.0
        cy = row["cy"] * k + dy * k
        for j, (name, tier) in enumerate(names):
            p = os.path.join(muscle_dir, f"{name}_{tier}.png")
            if not os.path.exists(p):
                raise SystemExit(f"no badge for {muscles.label(name)} at tier '{tier}' "
                                 f"- build them with muscle_icons.py --all")
            if p not in cache:
                cache[p] = sprite(p)
            by = cy
            if curves and i < len(curves) and curves[i] is not None:
                # Clamped to the row: the wave is free to ripple, the badge is not
                # free to climb into the row above or sit on the caption.
                lo = row["stripe"][0] * k + d * 0.5 + 6 * k
                hi = row["cap_top"] * k - d * 0.5 - 6 * k
                by = float(np.clip(curves[i](x) + dy * k, lo, hi))
            out.append(dict(img=cache[p], cx=x, cy=by, d=d, row=i,
                            t=t0 + j * stagger, name=name, tier=tier))
            x += d + g
    for b in out:
        b["fade_at"] = seconds - fade if fade > 0 else None
        b["fade"] = fade
    return out


def pop_times(pl):
    """The instants a badge lands, for the sound to be cut against."""
    return sorted(b["t"] for b in pl)


# ------------------------------------------------------------------ painting

def _ease(p):
    """easeOutBack. Starts at exactly 0, overshoots ~15%, settles on 1."""
    c1, c3 = 2.2, 3.2
    q = p - 1.0
    return 1.0 + c3 * q * q * q + c1 * q * q


def blend(dst, src, alpha, x0, y0):
    """src is HxWx4 float; alpha scales its own. Clipped to the frame.

    Shared with body_overlay, which composites the same way and had its own copy
    of this for exactly one afternoon."""
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


def paint(frame, pl, secs, ring=True):
    """Draw every badge that is alive at `secs` into `frame` (H x W x 3 float)."""
    for b in pl:
        s = secs - b["t"]
        if s < 0:
            continue
        alpha = min(1.0, s / RISE) if RISE > 0 else 1.0
        if b["fade_at"] is not None and secs > b["fade_at"]:
            alpha *= max(0.0, 1.0 - (secs - b["fade_at"]) / b["fade"])
        if alpha <= 0.002:
            continue
        scale = _ease(min(1.0, s / POP))
        if scale <= 0.01:
            continue

        if ring and s < RING:
            _ring(frame, b, s / RING)

        side = max(2, int(round(b["d"] * SHADOW * scale)))
        im = Image.fromarray(np.clip(b["img"], 0, 255).astype(np.uint8), "RGBA")
        im = im.resize((side, side), Image.LANCZOS)
        arr = np.array(im).astype(np.float32)
        x0 = int(round(b["cx"] - side / 2.0))
        y0 = int(round(b["cy"] - side / 2.0))
        blend(frame, arr, alpha, x0, y0)
        if b.get("fin_t") is not None:
            _sweep(frame, b, arr, secs - b["fin_t"], alpha, x0, y0)


SWEEP = 0.29        # seconds for the highlight to cross one ball
SWEEP_W = 0.26      # its width, as a fraction of the ball
SWEEP_A = 0.50      # peak alpha of the white


def _sweep(frame, b, arr, s, alpha, x0, y0):
    """A specular band crossing the ball as the surge passes its column.

    Deliberately not a second pop. A badge that scales up again reads as landing
    a second time, and a second landing wants a second hit under it - which is
    the one thing the sound cannot give it, because the finale is a chord, not
    five more strikes. A highlight sliding across glass says the light moved,
    not the ball, and that is what actually happened.

    It rides the ball's own alpha, so it never spills past the sphere onto the
    row behind it, and it is tilted slightly with y so it reads as a curved
    surface rather than a wipe.
    """
    if not 0.0 <= s <= SWEEP:
        return
    p = s / SWEEP
    side = arr.shape[0]
    xn = np.linspace(0.0, 1.0, side, dtype=np.float32)[None, :]
    yn = np.linspace(0.0, 1.0, side, dtype=np.float32)[:, None]
    u = xn * 0.82 + yn * 0.18
    centre = -0.25 + 1.5 * p
    band = np.exp(-((u - centre) / SWEEP_W) ** 2)
    a = band * (np.sin(np.pi * p) ** 0.7) * SWEEP_A * alpha * (arr[:, :, 3] / 255.0)
    if a.max() < 0.01:
        return
    src = np.dstack([np.full((side, side, 3), 255.0, np.float32), a * 255.0])
    blend(frame, src, 1.0, x0, y0)


def _ring(frame, b, p):
    """A thin light ring thrown off at the landing. Costs one small draw and is
    the difference between a badge that appears and a badge that arrives."""
    r0, r1 = b["d"] * 0.30, b["d"] * 0.78
    r = r0 + (r1 - r0) * (1 - (1 - p) ** 2)
    a = (1.0 - p) ** 1.6 * 0.55
    if a < 0.01:
        return
    w = max(1.0, b["d"] * 0.055 * (1 - p) + 1.0)
    side = int(r * 2 + w * 2 + 4)
    im = Image.new("L", (side, side), 0)
    c = side / 2.0
    ImageDraw.Draw(im).ellipse((c - r, c - r, c + r, c + r), outline=255, width=int(round(w)))
    m = np.array(im).astype(np.float32)[:, :, None] / 255.0 * a
    src = np.dstack([np.full((side, side, 3), 255.0, np.float32), m[:, :, 0] * 255.0])
    blend(frame, src, 1.0, int(round(b["cx"] - c)), int(round(b["cy"] - c)))


# ---------------------------------------------------------------------------
# The seam into engine/flowanim.py --overlay body_overlay,muscle_overlay
#
# Everything above is this variant's own. These functions are the whole of what
# the animator needs to know about it, and they are why there is no fork of
# flowanim.py here any more: it was 152 lines apart from the engine, and all of
# that was an import, some flags, a plan and two paint calls.
#
# The body is a separate module and is named first on --overlay, because it ends
# the wave where the organ used to end it and a badge is never behind it.
# ---------------------------------------------------------------------------

def add_arguments(p):
    p.add_argument("--muscles", help="muscles per row: 'Chest:p,Triceps:s;Lats:p,...' "
                                     "(';' between rows), or 'auto:LIFT,LIFT,...' to "
                                     "look each lift up in exercises.json")
    p.add_argument("--muscle-times", default="1,2,4,5.5,7",
                   help="when each row's badges land, in seconds")
    p.add_argument("--muscle-d", type=float, default=210.0, help="badge diameter at 1536 wide")
    p.add_argument("--muscle-gap", type=float, default=22.0)
    p.add_argument("--muscle-stagger", type=float, default=0.09,
                   help="delay between badges of the same row")
    p.add_argument("--muscle-dy", type=float, default=0.0,
                   help="nudge off the row centre line, at 1536 wide")
    p.add_argument("--muscle-fade", type=float, default=0.0,
                   help="seconds of fade-out at the end; 0 leaves them up, which is "
                        "what the clip ships with - a badge fading out passes through "
                        "a stretch where it is a soft coloured smudge, and that is the "
                        "frame a feed freezes on")
    p.add_argument("--muscle-ring", type=int, default=1, help="0 drops the shock ring")
    p.add_argument("--muscle-follow", type=int, default=1,
                   help="1 sits the badges on the wave's own centre line, 0 on the row's")
    p.add_argument("--muscle-dir", default=MUSCLE_DIR)
    p.add_argument("--muscle-cues", help="write the landing times here, for the SFX")


def build(args, ctx):
    if not args.muscles:
        return None
    if not ctx["layout"]:
        sys.exit("--muscles needs --layout: the badges sit on the row the layout "
                 "describes, and the body sits in its circle")
    times = [float(t) for t in args.muscle_times.split(",")]
    pl = plan(resolve(args.muscles), ctx["layout"], ctx["W"], ctx["H"], times,
              curves=ctx["curves"] if args.muscle_follow else None,
              diameter=args.muscle_d, gap=args.muscle_gap, stagger=args.muscle_stagger,
              dy=args.muscle_dy, muscle_dir=args.muscle_dir, seconds=ctx["seconds"],
              fade=args.muscle_fade)
    cues = pop_times(pl)
    print(f"  {len(pl)} muscle badges land at {', '.join(f'{t:.2f}' for t in cues)}s")
    if args.muscle_cues:
        with open(args.muscle_cues, "w") as fh:
            fh.write(",".join(f"{t:.3f}" for t in cues) + "\n")
    _RING[0] = bool(args.muscle_ring)
    return pl


_RING = [True]


def finale(pl, t0, ctx):
    """Each ball catches the light as the highlight passes its own column.

    The badges are the reason the surge is worth having at all: 22.7% of the
    wave is behind a circle and most of the rest is behind these, so the band
    itself is barely visible - what the eye sees is the row of balls flaring in
    order. So each one is timed to its own x, not to the row's.
    """
    at = (ctx.get("surge") or {}).get("at")
    for b in pl:
        b["fin_t"] = float(at(b["row"], b["cx"])) if at else float(t0)
    ts = sorted(b["fin_t"] for b in pl)
    print(f"  badges catch the light {ts[0]:.2f}-{ts[-1]:.2f}s, "
          f"last one done at {ts[-1] + SWEEP:.2f}s")


def draw(frame, pl, secs):
    paint(frame, pl, secs, ring=_RING[0])
