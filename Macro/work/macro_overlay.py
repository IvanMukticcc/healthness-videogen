#!/usr/bin/env python3
"""macro_overlay.py - act one: what each food is made of, and what it costs.

Micro's rows carry a vitamin per bowl. Macro's carry the same three facts for
every food - carbohydrate, protein, fat - and the calories they add up to. That
is the whole difference and it changes one thing structurally: **three badges a
row instead of one, and a number in the right-hand circle instead of an organ.**

WHY THE BADGES ARE DRAWN AND NOT SPRITED

Micro keeps an `icons/` folder because a vitamin is a picture: there is no way
to derive the letter K's badge from the word. A macro badge is a colour and a
number, both of which come out of `foods.py`, so a folder of pre-rendered PNGs
would be a cache of something already known - and a cache that goes stale
silently the first time a food's figures are corrected upstream. They are drawn
at build time, from the database, every render.

The colours are the app's, not this folder's: carbs blue, protein green, fat
red, exactly as `DailyIntakeDetailView.swift` passes them to `MacroChip`. A
viewer who sees blue in the clip and blue in the app is being told those are the
same thing, which they are.

THE RIGHT CIRCLE

Foods puts an organ there; Micro puts an organ there. Macro puts the calories,
because the row's argument is arithmetic rather than anatomy - these three
numbers, this many calories - and the circle is where a row's conclusion goes.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import foods

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/Library/Fonts"

POP = 0.42              # nothing to settled, as Micro's badges
RISE = 0.10
STAGGER = 0.085         # inside a row: the three land as one event with three parts
SS = 2                  # badges are drawn at 2x and landed at 1x

BLUE = (0, 122, 255)
GREEN = (52, 199, 89)
RED = (255, 59, 48)
ORDER = (("carbs", BLUE, "CARBS"), ("protein", GREEN, "PROTEIN"), ("fat", RED, "FAT"))


def _font(weight, size):
    return ImageFont.truetype(f"{FONTS}/SF-Pro-Display-{weight}.otf", int(size))


def _disc(d, colour, value, label, shadow=0.34):
    """One macro badge as an RGBA sprite: a coloured disc, a number, a word."""
    n = int(d * SS)
    pad = int(n * 0.16)
    im = Image.new("RGBA", (n + pad * 2, n + pad * 2), (0, 0, 0, 0))

    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).ellipse([pad, pad + n * 0.05, pad + n, pad + n * 1.05],
                               fill=int(255 * shadow))
    sh = sh.filter(ImageFilter.GaussianBlur(n * 0.055))
    im.paste(Image.new("RGBA", im.size, (0, 0, 0, 255)), (0, 0), sh)

    dr = ImageDraw.Draw(im)
    dr.ellipse([pad, pad, pad + n, pad + n], fill=colour + (255,))
    # a soft top-light, so the disc reads as a ball rather than a sticker
    gl = Image.new("L", im.size, 0)
    ImageDraw.Draw(gl).ellipse([pad + n * 0.16, pad + n * 0.08,
                                pad + n * 0.84, pad + n * 0.52], fill=54)
    im.paste(Image.new("RGBA", im.size, (255, 255, 255, 255)),
             (0, 0), gl.filter(ImageFilter.GaussianBlur(n * 0.06)))

    cx, cy = pad + n / 2, pad + n / 2
    txt = f"{value:.1f}".rstrip("0").rstrip(".") if value < 100 else f"{value:.0f}"
    dr.text((cx, cy - n * 0.07), txt, font=_font("Bold", n * 0.34),
            fill=(255, 255, 255, 255), anchor="mm")
    dr.text((cx, cy + n * 0.17), "g", font=_font("Semibold", n * 0.15),
            fill=(255, 255, 255, 210), anchor="mm")
    dr.text((cx, cy + n * 0.33), label, font=_font("Semibold", n * 0.115),
            fill=(255, 255, 255, 225), anchor="mm")
    return np.asarray(im.resize((im.width // SS, im.height // SS), Image.LANCZOS),
                      dtype=np.float32) / 255.0


# Atwater's factors, the arithmetic every nutrition label on earth is built on:
# a gram of carbohydrate or protein carries 4 kcal, a gram of fat 9.
ATWATER = {"carbs": 4.0, "protein": 4.0, "fat": 9.0}


def _plate(d):
    """The empty ring, drawn from the first frame. It is furniture, not an event.

    THE WAVE HAS TO END IN SOMETHING. Foods and Micro put an organ in the right
    circle and the generator draws it, so the liquid's tapered tip is behind a
    solid object from frame zero and is never once seen ending. Macro took that
    circle for itself and then only started drawing in it at the row's cue, which
    left five naked tips tapering into flat colour for the first second of the
    clip - and left the poster itself looking unfinished, because a still has no
    cue to wait for.

    So the plate and the empty track arrive with the poster and only the coloured
    arcs and the number pop. An empty ring is not a placeholder either: it is a
    ring at zero, which is what the app draws before you have eaten anything.
    """
    n = int(d * SS)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    # Fully opaque, not 235. At 92% the liquid's tip showed through as a dark
    # wedge just inside the left edge - the tip was hidden and its shadow was
    # not, which is the same fault one step quieter.
    dr.ellipse([0, 0, n, n], fill=(18, 38, 43, 255))
    pad = n * 0.085
    dr.ellipse([pad, pad, n - pad, n - pad], outline=(255, 255, 255, 38),
               width=int(n * 0.085))
    return np.asarray(im.resize((n // SS, n // SS), Image.LANCZOS),
                      dtype=np.float32) / 255.0


def _kcal(d, f):
    """The right-hand circle: the calories, and where in the food they come from.

    Not a bar against a maximum. A per-100 g calorie figure has no reference
    intake to be a fraction OF - inventing a scale ("out of 600") would put an
    unsourced denominator in the one place a row concludes.

    So the ring is a composition rather than a progress: the three macros'
    share of THIS food's energy, in the same three colours as the badges beside
    it. Almonds come back four-fifths red, honey all but entirely blue, and the
    reading is instant and needs no legend. The number in the middle is the
    kcal, which is a fact, and the split is arithmetic on the same row's facts.

    It is also act two's ring, five times and smaller, which is the point: the
    thing turning over at the end is the thing you have been looking at.
    """
    n = int(d * SS)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    cx = cy = n / 2

    energy = {k: f[k] * v for k, v in ATWATER.items()}
    total = sum(energy.values()) or 1.0
    pad = n * 0.085
    wid = n * 0.085
    box = [pad, pad, n - pad, n - pad]
    a0 = -90.0
    for key, colour, _ in ORDER:
        sweep = 360.0 * energy[key] / total
        if sweep <= 0.4:
            a0 += sweep
            continue
        dr.arc(box, a0, a0 + sweep, fill=colour + (255,), width=int(wid))
        a0 += sweep

    dr.text((cx, cy - n * 0.09), f"{f['calories']:.0f}", font=_font("Black", n * 0.30),
            fill=(255, 255, 255, 255), anchor="mm")
    dr.text((cx, cy + n * 0.12), "KCAL", font=_font("Bold", n * 0.125),
            fill=(255, 255, 255, 235), anchor="mm")
    dr.text((cx, cy + n * 0.245), "PER 100 G", font=_font("Semibold", n * 0.078),
            fill=(255, 255, 255, 175), anchor="mm")
    return np.asarray(im.resize((n // SS, n // SS), Image.LANCZOS),
                      dtype=np.float32) / 255.0


def add_arguments(p):
    p.add_argument("--macro", help="the five foods, comma separated, by their "
                                   "name in the app's database")
    p.add_argument("--macro-times", default="1,2,3.2,4.4,5.6",
                   help="when each row's three badges begin landing")
    p.add_argument("--macro-cues", help="write the landing instants here, for the audio")
    p.add_argument("--macro-d", type=float, default=196.0, help="badge diameter at 1536 wide")
    p.add_argument("--macro-gap", type=float, default=20.0)
    p.add_argument("--macro-stagger", type=float, default=STAGGER)
    p.add_argument("--macro-kcal", default="1", help="0 to leave the right circle alone")


def build(args, ctx):
    if not args.macro:
        return None
    names = [n.strip() for n in args.macro.split(",") if n.strip()]
    W, H = ctx["W"], ctx["H"]
    k = W / 1536.0
    L = ctx["layout"]
    if isinstance(L, str):
        L = json.load(open(L))
    curves = ctx.get("curves") or []
    times = [float(x) for x in args.macro_times.split(",")]

    out = []
    for i, (name, row) in enumerate(zip(names, L["rows"])):
        f = foods.refuse_unsourced(foods.find(name))
        t0 = times[i] if i < len(times) else times[-1]
        d = args.macro_d * k
        g = args.macro_gap * k
        x_lo = (L["anchor_l"] + row["r"]) * k + 16 * k
        x_hi = (L["anchor_r"] - row["r"]) * k - 16 * k
        room = x_hi - x_lo
        if 3 * d + 2 * g > room:
            d = (room - 2 * g) / 3
        span = 3 * d + 2 * g
        x = (x_lo + x_hi) / 2.0 - span / 2.0 + d / 2.0
        for j, (key, colour, label) in enumerate(ORDER):
            by = row["cy"] * k
            if i < len(curves) and curves[i] is not None:
                lo = row["stripe"][0] * k + d * 0.5 + 6 * k
                hi = row["cap_top"] * k - d * 0.5 - 6 * k
                by = float(np.clip(curves[i](x), lo, hi))
            out.append(dict(img=_disc(d, colour, f[key], label), cx=x, cy=by, d=d,
                            row=i, t=t0 + j * args.macro_stagger, kind="macro"))
            x += d + g
        if args.macro_kcal != "0":
            rd = row["r"] * 2 * k * 0.92
            rx, ry = L["anchor_r"] * k, row["cy"] * k
            out.append(dict(img=_plate(rd), cx=rx, cy=ry, d=rd, row=i,
                            t=0.0, kind="plate", still=True))
            out.append(dict(img=_kcal(rd, f), cx=rx, cy=ry, d=rd, row=i,
                            t=t0 + 2 * args.macro_stagger + 0.06, kind="kcal"))

    if args.macro_cues:
        with open(args.macro_cues, "w") as fh:
            fh.write(",".join(f"{b['t']:.3f}" for b in sorted(
                (b for b in out if b["kind"] == "macro"), key=lambda b: b["t"])))
    return out


def cues(plan):
    """The engine asks for these; the audio reads the file, never the argument."""
    return sorted(b["t"] for b in plan if b["kind"] == "macro")


def _ease(p):
    """easeOutBack, the same curve Micro's badges land on."""
    c1, c3 = 2.2, 3.2
    q = p - 1.0
    return 1.0 + c3 * q * q * q + c1 * q * q


def _blend(dst, src, alpha, x0, y0):
    """Composite one sprite INTO dst, in place.

    In place is not a style choice. `flowanim.py` calls `m.draw(out, pl, t)` and
    throws the return value away - the frame it writes to ffmpeg is the array it
    handed in. An overlay that builds a new array and returns it is correct in
    every respect except the one that matters, and it fails silently: the render
    succeeds, the timings are written, the cues file is right, and the badges are
    simply absent. That is how the first five renders of this variant came out.
    """
    h, w = src.shape[:2]
    Hh, Ww = dst.shape[:2]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    ww = min(w - sx0, Ww - dx0)
    hh = min(h - sy0, Hh - dy0)
    if ww <= 0 or hh <= 0:
        return
    s = src[sy0:sy0 + hh, sx0:sx0 + ww]
    a = s[:, :, 3:4] * alpha
    region = dst[dy0:dy0 + hh, dx0:dx0 + ww].astype(np.float32)
    dst[dy0:dy0 + hh, dx0:dx0 + ww] = np.clip(
        region * (1 - a) + s[:, :, :3] * 255.0 * a, 0, 255).astype(np.uint8)


def draw(frame, plan, t):
    """Draws into `frame`. Returns it too, but the engine does not read that."""
    if not plan:
        return frame
    for b in plan:
        if b.get("still"):
            scale, alpha = 1.0, 1.0
        else:
            p = (t - b["t"]) / POP
            if p <= 0:
                continue
            scale = _ease(min(p, 1.0)) if p < 1.0 else 1.0
            alpha = min(1.0, (t - b["t"]) / RISE) if p < 1.0 else 1.0
        img = b["img"]
        want = max(2, int(round(img.shape[1] * scale)))
        if want != img.shape[1]:
            im = Image.fromarray((img * 255).astype(np.uint8), "RGBA")
            hh = max(2, int(round(img.shape[0] * scale)))
            img = np.asarray(im.resize((want, hh), Image.BILINEAR),
                             dtype=np.float32) / 255.0
        x0 = int(round(b["cx"] - img.shape[1] / 2))
        y0 = int(round(b["cy"] - img.shape[0] / 2))
        _blend(frame, img, alpha, x0, y0)
    return frame
