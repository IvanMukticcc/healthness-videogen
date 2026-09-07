#!/usr/bin/env python3
"""
micro_overlay.py - the micronutrient badges popping onto a finished frame.

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
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
MICRO_DIR = os.path.join(HERE, "ASSETS", "Micro")
NUTRIENTS = os.path.join(HERE, "nutrients.json")

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
    """'auto:LEAFY GREENS,BEETROOT,...' -> the nutrients each food is known for.
    Anything else is taken literally: rows separated by ';', badges by ','."""
    if not spec:
        return []
    if spec.startswith("auto:"):
        table = table or json.load(open(NUTRIENTS))
        # Longest key first, or 'RED APPLES' and 'PINEAPPLE' both answer to
        # 'apple' and whichever the file happens to list first wins.
        keys = sorted((k for k in table if not k.startswith("_")), key=len, reverse=True)
        rows = []
        for food in spec[5:].split(","):
            key = food.strip().lower()
            hit = table.get(key)
            if hit is None:                      # 'RED APPLES' -> 'apple'
                for k in keys:
                    if k in key:
                        hit = table[k]
                        break
            if hit is None:
                raise SystemExit(f"no micronutrients known for '{food.strip()}' "
                                 f"- add it to {os.path.basename(NUTRIENTS)}")
            rows.append(list(hit))
        return rows
    return [[b.strip() for b in row.split(",") if b.strip()] for row in spec.split(";")]


# ------------------------------------------------------------------ planning

def plan(rows, layout, W, H, times, diameter=210.0, gap=22.0, stagger=0.09,
         dy=0.0, micro_dir=MICRO_DIR, seconds=8.0, fade=0.4, curves=None):
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
        for j, name in enumerate(names):
            p = os.path.join(micro_dir, f"{name.upper().replace(' ', '').replace('-', '')}.png")
            if not os.path.exists(p):
                raise SystemExit(f"no badge for '{name}' - build it with "
                                 f"micro_icons.py --one '{name}:v|m|o'")
            if p not in cache:
                cache[p] = sprite(p)
            by = cy
            if curves and i < len(curves) and curves[i] is not None:
                # Clamped to the row: the wave is free to ripple, the badge is not
                # free to climb into the row above or sit on the caption.
                lo = row["stripe"][0] * k + d * 0.5 + 6 * k
                hi = row["cap_top"] * k - d * 0.5 - 6 * k
                by = float(np.clip(curves[i](x) + dy * k, lo, hi))
            out.append(dict(img=cache[p], cx=x, cy=by, d=d,
                            t=t0 + j * stagger, name=name))
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


def _blend(dst, src, alpha, x0, y0):
    """src is HxWx4 float; alpha scales its own. Clipped to the frame."""
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
        _blend(frame, np.array(im).astype(np.float32), alpha,
               int(round(b["cx"] - side / 2.0)), int(round(b["cy"] - side / 2.0)))


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
    _blend(frame, src, 1.0, int(round(b["cx"] - c)), int(round(b["cy"] - c)))


# ---------------------------------------------------------------------------
# The seam into engine/flowanim.py --overlay micro_overlay
#
# Everything above is this variant's own. These three functions are the whole of
# what the animator needs to know about it, and they are why there is no fork of
# flowanim.py here any more: it was 77 lines apart from the engine, and all 77
# were an import, some flags, a plan and a paint call.
# ---------------------------------------------------------------------------

def add_arguments(p):
    p.add_argument("--micro", help="badges per row: 'A,C;Iron,Zinc;...' (';' between "
                                   "rows), or 'auto:FOOD,FOOD,...' to look each food "
                                   "up in nutrients.json")
    p.add_argument("--micro-times", default="1,2,4,5.5,7",
                   help="when each row's badges land, in seconds")
    p.add_argument("--micro-d", type=float, default=210.0, help="badge diameter at 1536 wide")
    p.add_argument("--micro-gap", type=float, default=22.0)
    p.add_argument("--micro-stagger", type=float, default=0.09,
                   help="delay between badges of the same row")
    p.add_argument("--micro-dy", type=float, default=0.0,
                   help="nudge off the row centre line, at 1536 wide")
    p.add_argument("--micro-fade", type=float, default=0.0,
                   help="seconds of fade-out at the end; 0 leaves them up, which is "
                        "what the clip ships with - a badge fading out passes through "
                        "a stretch where it is a soft coloured smudge, and that is the "
                        "frame a feed freezes on")
    p.add_argument("--micro-ring", type=int, default=1, help="0 drops the shock ring")
    p.add_argument("--micro-follow", type=int, default=1,
                   help="1 sits the badges on the wave's own centre line, 0 on the row's")
    p.add_argument("--micro-dir", default=MICRO_DIR)
    p.add_argument("--micro-cues", help="write the landing times here, for the SFX")


def build(args, ctx):
    if not args.micro:
        return None
    if not ctx["layout"]:
        sys.exit("--micro needs --layout: the badges sit on the row the layout describes")
    times = [float(t) for t in args.micro_times.split(",")]
    pl = plan(resolve(args.micro), ctx["layout"], ctx["W"], ctx["H"], times,
              curves=ctx["curves"] if args.micro_follow else None,
              diameter=args.micro_d, gap=args.micro_gap, stagger=args.micro_stagger,
              dy=args.micro_dy, micro_dir=args.micro_dir, seconds=ctx["seconds"],
              fade=args.micro_fade)
    cues = pop_times(pl)
    print(f"  {len(pl)} micronutrient badges land at "
          f"{', '.join(f'{t:.2f}' for t in cues)}s")
    if args.micro_cues:
        with open(args.micro_cues, "w") as fh:
            fh.write(",".join(f"{t:.3f}" for t in cues) + "\n")
    _RING[0] = bool(args.micro_ring)
    return pl


_RING = [True]


def draw(frame, pl, secs):
    paint(frame, pl, secs, ring=_RING[0])
