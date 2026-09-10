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
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
MICRO_DIR = os.path.join(HERE, "icons")
NUTRIENTS = os.path.join(HERE, "nutrients.json")

POP = 0.42          # seconds from nothing to settled
RISE = 0.10         # of that, how long the badge is still fading up
RING = 0.34         # how long the shock ring lives
SHADOW = 1.30       # sprite canvas, as a multiple of the ball

# The organ answering its own row, and then answering the finale. Both are light
# on pixels that are already there: the organ is poster artwork, pinned in place
# by the animator, and behind it is the clean base rather than the poster, so
# anything that moves or scales it opens a hole. The lift is a multiply, not a
# mix towards white - tissue that washes out stops being tissue.
ORGAN_TH = 45       # levels away from the clean base before it counts as organ
ORGAN_LIFT = 0.26   # how far up its own row's cue takes it
ORGAN_RISE = 0.07   # seconds to full lift
ORGAN_SETTLE = 0.38 # and down onto the residue it keeps
ORGAN_RESIDUE = 0.06
FIN_LIFT = 0.45     # the finale, which is the same gesture with the volume up
FIN_RISE = 0.08
FIN_SETTLE = 0.24
FIN_RESIDUE = 0.14  # where every organ stays for the rest of the clip
GLOW_SIGMA = 6.0    # at 1536 wide: 3 sigma is 18px, which is all the room there
                    # is - the right circle's outer edge is x=1408 and the safe
                    # area ends at 1426
GLOW_ROW = 0.24     # how much of the bloom a row's own cue lights
GLOW_FIN = 0.50     # and the finale. Above this the halo stops being a rim and
                    # becomes a haze the organ sits in, which flattens the very
                    # thing it is meant to lift
BADGE_LIFT = 0.36   # the ball, as the surge's crest passes its column
BADGE_RISE = 0.05
BADGE_SETTLE = 0.26


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


# ------------------------------------------------------------------ the organ

def organs(layout, W, H, poster, clean, times, stagger=0.09, sigma=GLOW_SIGMA):
    """One entry per row: the organ's own pixels, cut to its own outline.

    **Found, not assumed.** The generator fills the right guide circle with
    whatever the row asked for, and how much of the disc that covers is not
    knowable in advance: measured over two posters and ten circles it runs from
    34% to 97%, so a fixed radius lights a halo of bare row colour on one row and
    clips the organ on the next. The shape is read the way `refine_art` reads the
    lifter - poster against the clean base at the same 45 levels the animator's
    own colour test uses, opened at 5x5 so jpeg speckle is not an edge and closed
    at 13x13 so a dark seam inside an organ does not split it in two.

    **And the disc is not the organ.** 5.0% of the wave - 20 672 px at 1536 -
    lies inside the guide circles, where the animator never paints: it is real
    liquid, and it is standing still. Lighting the disc would put a bright
    motionless crescent beside moving liquid, which is the speckles-that-stand-
    still failure `flow.md` already records. The difference test excludes it for
    free: where the organ does not cover, the poster still equals the base.
    """
    L = json.load(open(layout)) if isinstance(layout, str) else layout
    k = W / 1536.0
    d = np.abs(np.float32(poster) - np.float32(clean)).max(axis=2) > ORGAN_TH
    yy, xx = np.mgrid[0:H, 0:W]
    s = max(1.0, sigma * k)
    pad = int(round(3 * s)) + 2
    out = []
    for i, row in enumerate(L["rows"]):
        cx, cy, r = L["anchor_r"] * k, row["cy"] * k, row["r"] * k
        disc = np.hypot(xx - cx, yy - cy) < r
        m = ndimage.binary_opening(d & disc, np.ones((5, 5)))
        m = ndimage.binary_closing(m, np.ones((13, 13)))
        lab, n = ndimage.label(m)
        if n == 0:
            print(f"    r{i + 1}: nothing found in the right circle - the row is "
                  f"animated without an organ response")
            continue
        area = ndimage.sum(m, lab, range(1, n + 1))
        keep = lab == (int(np.argmax(area)) + 1)
        print(f"    r{i + 1}: organ {int(keep.sum()):6d} px, {n} cluster"
              f"{'s' if n > 1 else ''}, dominant {100 * area.max() / area.sum():.0f}%"
              f", {100 * keep.sum() / disc.sum():.0f}% of the disc")

        ys, xs = np.where(keep)
        y0, y1 = max(0, ys.min() - pad), min(H, ys.max() + pad + 1)
        x0, x1 = max(0, xs.min() - pad), min(W, xs.max() + pad + 1)
        a = keep[y0:y1, x0:x1].astype(np.float32)
        # One pixel of blur on the cut itself. The silhouette comes off a
        # threshold, so its edge is a staircase, and a staircase lit at 60% is a
        # row of bright steps at the size this occupies in a vertical video.
        a = ndimage.gaussian_filter(a, 0.8)
        plane = np.dstack([np.float32(poster[y0:y1, x0:x1]), a * 255.0])
        glow = np.dstack([np.full(a.shape + (3,), 255.0, np.float32),
                          ndimage.gaussian_filter(a, s) * 255.0])
        t0 = times[i] if i < len(times) else times[-1]
        out.append(dict(row=i, x0=x0, y0=y0, cx=cx, cy=cy, r=r,
                        plane=plane, glow=glow, px=int(keep.sum()),
                        t=t0 + stagger))          # the row answers on its own cue
    return out


class Plan(list):
    """The badges, with their rows' organs alongside.

    A list, because the engine and everything else in here iterates it as one;
    the organs ride along rather than becoming a second plan, so `cues`, `draw`
    and `finale` are handed one object and the seam stays three functions wide.
    """
    organs = ()


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
            out.append(dict(img=cache[p], cx=x, cy=by, d=d, row=i,
                            t=t0 + j * stagger, name=name))
            x += d + g
    for b in out:
        b["fade_at"] = seconds - fade if fade > 0 else None
        b["fade"] = fade
    return out


def pop_times(pl):
    """The instants a badge lands, for the sound to be cut against."""
    return sorted(b["t"] for b in pl)


# The engine asks for `cues`; this folder has always called them pop times. One
# name on the seam, one name in here, and no third list of the same numbers.
cues = pop_times


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


def _organ_alpha(o, secs):
    """How lit the organ is at `secs`: nothing, then its row's own answer decaying
    onto a small residue, then the finale's, decaying onto a larger one.

    The residues are the point. An organ that lights once and goes back to
    exactly what it was has not been taught to the viewer, and the finale would
    then be the first thing it ever does - which in the last second reads as a
    fault rather than a climax. It stays a little awake instead."""
    a = 0.0
    if secs >= o["t"]:
        s = secs - o["t"]
        f = max(0.0, 1.0 - max(0.0, s - ORGAN_RISE) / ORGAN_SETTLE) ** 2
        a = min(1.0, s / ORGAN_RISE) * (ORGAN_RESIDUE + (ORGAN_LIFT - ORGAN_RESIDUE) * f)
    ft = o.get("fin_t")
    if ft is not None and secs >= ft:
        s = secs - ft
        f = max(0.0, 1.0 - max(0.0, s - FIN_RISE) / FIN_SETTLE) ** 2
        a = max(a, min(1.0, s / FIN_RISE) * (FIN_RESIDUE + (FIN_LIFT - FIN_RESIDUE) * f))
    return a


def paint_organs(frame, organs, secs):
    """Light only: the plane is the poster's own pixels multiplied up, never moved
    and never scaled. Behind it is the clean base, not the poster, so a pixel of
    movement opens a hole - and the poster is jpeg, so resampling would ring on
    every edge of it."""
    for o in organs:
        a = _organ_alpha(o, secs)
        if a <= 0.004:
            continue
        # Screened towards white, not multiplied. A multiply is what a muscle
        # plane wants, because it is drawn and mid-toned; an organ is a
        # photograph, and half of them are bone or fat sitting at 230 where a
        # 1.45x multiply clips to white and takes the shape with it. Screening
        # lifts the body of the tissue and leaves its highlights alone: at a=0.45
        # a mid-tone 150 goes to 197 and a near-white 230 to 241.
        lit = o["plane"].copy()
        lit[:, :, :3] = 255.0 - (255.0 - lit[:, :, :3]) * (1.0 - a)
        _blend(frame, lit, 1.0, o["x0"], o["y0"])
        g = a * (GLOW_FIN if o.get("fin_t") is not None and secs >= o["fin_t"] else GLOW_ROW)
        if g > 0.01:
            _blend(frame, o["glow"], g, o["x0"], o["y0"])


def _scaled(b, side):
    """The badge at `side` px, resized once and kept.

    `b["img"]` never changes and `side` is an integer, so this asks LANCZOS for
    the same picture over and over: 192 frames x 15 badges, of which all but the
    handful during the pop are the badge at its settled size. The cache is per
    badge and keyed by side, so it holds one entry for the whole steady stretch
    and a dozen for the pop. Byte-identical output - same filter, same input,
    same size - which is the only reason it is allowed to exist.
    """
    hit = b.get("_scaled")
    if hit is None:
        hit = b["_scaled"] = {}
    out = hit.get(side)
    if out is None:
        src = b.get("_u8")
        if src is None:
            src = b["_u8"] = Image.fromarray(
                np.clip(b["img"], 0, 255).astype(np.uint8), "RGBA")
        out = hit[side] = np.array(
            src.resize((side, side), Image.LANCZOS)).astype(np.float32)
    return out


def paint(frame, pl, secs, ring=True):
    """Draw every badge that is alive at `secs` into `frame` (H x W x 3 float)."""
    paint_organs(frame, getattr(pl, "organs", ()), secs)
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
        _blend(frame, _scaled(b, side), alpha,
               int(round(b["cx"] - side / 2.0)), int(round(b["cy"] - side / 2.0)))

        # The surge passing this badge's own column. Without it the highlight is
        # nearly invisible: 22.7% of the wave is behind a bowl or an organ and
        # most of what is left is behind a badge, so the band showing through the
        # gaps is not the effect - the badges lighting as it reaches them is.
        ft = b.get("fin_t")
        if ft is None or secs < ft or b.get("white") is None:
            continue
        s = secs - ft
        f = max(0.0, 1.0 - max(0.0, s - BADGE_RISE) / BADGE_SETTLE) ** 2
        if f > 0.02:
            w = b["white"]
            _blend(frame, w, alpha * BADGE_LIFT * f,
                   int(round(b["cx"] - w.shape[1] / 2.0)),
                   int(round(b["cy"] - w.shape[0] / 2.0)))


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
    p.add_argument("--micro-times", default="1,2,3.2,4.4,5.6",
                   help="when each row's badges land, in seconds. Moved in from "
                        "1,2,4,5.5,7 to make room for the finale: at the old rhythm "
                        "the last pop settles at 7.60 of an 8s clip and there is no "
                        "room for anything after it. The room cannot be bought with "
                        "--seconds - the surface travels a whole number of ribbon "
                        "lengths, so 9s costs 92px/s and there is no flag that gives "
                        "it back")
    p.add_argument("--micro-organ", type=int, default=1,
                   help="1 lets each row's organ answer its own cue and the finale; "
                        "0 leaves the right circle as the poster drew it")
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
    pl = Plan(pl)
    ts = pop_times(pl)
    print(f"  {len(pl)} micronutrient badges land at "
          f"{', '.join(f'{t:.2f}' for t in ts)}s")
    if args.micro_cues:
        with open(args.micro_cues, "w") as fh:
            fh.write(",".join(f"{t:.3f}" for t in ts) + "\n")
    if args.micro_organ and args.base:
        # ctx["base"] is the poster; the clean base is the file the animator was
        # given, read again here at the render's own size. Both are needed: the
        # organ is exactly what one has and the other does not.
        cb = Image.open(args.base).convert("RGB")
        if cb.size != (ctx["W"], ctx["H"]):
            cb = cb.resize((ctx["W"], ctx["H"]), Image.LANCZOS)
        pl.organs = organs(ctx["layout"], ctx["W"], ctx["H"], ctx["base"],
                           np.asarray(cb).astype(np.float32), times,
                           stagger=args.micro_stagger)
        print(f"  {len(pl.organs)} organs answer their own row, "
              f"{sum(o['px'] for o in pl.organs)} px of poster lit")
    _RING[0] = bool(args.micro_ring)
    return pl


_RING = [True]


def finale(pl, t0, ctx):
    """Everything already in the plan, lit once more as the surge reaches it.

    Nothing new is planned and nothing new is drawn: the organ is the same plane
    its own row lit at its own cue, and the badge is the same ball. That is the
    whole argument for doing the row responses first - by the time the finale
    arrives the viewer has seen this exact gesture five times, and the last
    second is a summary rather than a surprise.

    `at(row, x)` is the engine's, because only it has the arc length the band
    actually travels: each badge answers as the crest passes its own column and
    each organ as it reaches its circle, so the poster reads as one gesture
    running diagonally down it. Without --surge there is no cascade to follow and
    everything answers together on the finale's own instant.
    """
    at = (ctx.get("surge") or {}).get("at")
    for b in pl:
        b["fin_t"] = float(at(b["row"], b["cx"])) if at else float(t0)
        side = max(2, int(round(b["d"] * SHADOW)))
        w = np.array(Image.fromarray(np.clip(b["img"], 0, 255).astype(np.uint8), "RGBA")
                     .resize((side, side), Image.LANCZOS)).astype(np.float32)
        # White with the ball's own alpha, resized once here rather than per
        # frame: a resize costs milliseconds and there are 192 frames of them.
        w[:, :, :3] = 255.0
        b["white"] = w
    for o in getattr(pl, "organs", ()):
        o["fin_t"] = float(at(o["row"], o["cx"])) if at else float(t0)
    ts = [o["fin_t"] for o in getattr(pl, "organs", ())]
    if ts:
        print(f"  organs light again at {', '.join(f'{t:.2f}' for t in ts)}s, "
              f"settled by {max(ts) + FIN_RISE + FIN_SETTLE:.2f}s")


def draw(frame, pl, secs):
    paint(frame, pl, secs, ring=_RING[0])
