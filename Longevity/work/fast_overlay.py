#!/usr/bin/env python3
"""
fast_overlay.py - the hour on the left, the stage on the right, the fast between.

One module rather than three, because unlike the other variants these elements
are not independent: the hour, the stage and the bar are three views of the same
number, and a row is either reached or it is not. Splitting them would mean
passing `reached` around between modules that would each have to agree about it.

    ../../engine/flowanim.py <poster> --overlay fast_overlay --protocol 16_8 ...

WHAT IS DIFFERENT HERE, AND WHY

**Rows go dim.** Every other variant draws five rows of equal weight, because
their five rows are five facts. Here the rows are five points on one fast and the
fast stops somewhere: a 16:8 lights four and leaves autophagy dark. The dim row
is the content - it is what a longer protocol buys, shown rather than argued -
and it is not a claim. It says the fast stops before here, which is the opposite
of claiming the stage.

**Nothing counts up to a number that needs a scale.** The dial counts hours, and
an hour is a unit the viewer already has a scale for: `16 H` needs nothing under
it. That rule is Biohacks', from the folder this dial is generalised out of, and
it is why the first version of this category - which counted years gained - was a
claim wearing a number's clothes.

**The stage is drawn, never generated.** What happens at hour 16 is invisible, so
there is no photograph of it and no prompt for it. The generator gets the room and
the light; the body's inside is authored here and identical on every clip, which
is the rule the whole design rests on.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import longevity

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/Users/ivanmuktic/Library/Fonts/SF-Compact-Display-Black.otf"

SS = 4                  # supersample the ring; an arc at 1x has a staircase on it
R_RING = 0.94           # ring radius as a fraction of the guide circle
W_RING = 0.075
SWEEP = 0.55            # seconds for the dial to travel to its hour
LOCK = 0.16             # and the flash when it arrives
DIM = 0.34              # what an unreached row keeps: visible, clearly not lit
BAR_H = 0.010           # the 0-24 h bar, as a fraction of the poster height


def _font(px):
    try:
        return ImageFont.truetype(FONT, px)
    except OSError:
        return ImageFont.load_default()


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


def _rgba(im):
    return np.array(im.convert("RGBA")).astype(np.float32)


def dial(r, hour, colour, reached):
    """The left circle: a ring that fills to the hour, with the hour inside it.

    Twenty-four hours is the whole ring. The sweep is therefore honest about
    proportion without anybody drawing a scale - hour 4 is a sixth of the way
    round, and the eye reads that before it reads the number.
    """
    D = int(r * 2)
    big = D * SS
    im = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = big * 0.03
    box = (pad, pad, big - pad, big - pad)
    track = (255, 255, 255, 34) if reached else (255, 255, 255, 20)
    d.ellipse(box, outline=track, width=int(big * W_RING))
    if hour > 0:
        end = -90 + 360.0 * min(hour, 24) / 24.0
        d.arc(box, -90, end, fill=colour + (255 if reached else 90,),
              width=int(big * W_RING))
    im = im.resize((D, D), Image.LANCZOS)

    txt = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    t = ImageDraw.Draw(txt)
    label = f"{int(hour)} H"
    f = _font(int(D * 0.30))
    w = t.textbbox((0, 0), label, font=f)
    t.text(((D - (w[2] - w[0])) / 2 - w[0], (D - (w[3] - w[1])) / 2 - w[1]),
           label, font=f, fill=(255, 255, 255, 255 if reached else 130))
    out = _rgba(im)
    _blend_into(out, _rgba(txt))
    return out


def _blend_into(dst_rgba, src_rgba):
    a = src_rgba[:, :, 3:4] / 255.0
    dst_rgba[:, :, :3] = dst_rgba[:, :, :3] * (1 - a) + src_rgba[:, :, :3] * a
    dst_rgba[:, :, 3:4] = np.clip(dst_rgba[:, :, 3:4] + src_rgba[:, :, 3:4], 0, 255)


def stage_mark(r, stage_id, colour, reached):
    """The right circle: what is happening inside, drawn because no camera reaches it.

    Deliberately a diagram and not an illustration of an organ. The subject is a
    process rather than a place - glycogen falling, fat mobilising, ketones
    rising, cells recycling - and an organ would say the wrong thing about where
    it happens.
    """
    D = int(r * 2)
    big = D * SS
    im = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = colour + (255,)
    cx = cy = big / 2
    R = big * 0.34
    a = 255 if reached else 110

    if stage_id == "anabolic":                      # full: a solid disc, fed
        d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=colour + (a,))
    elif stage_id == "catabolic":                   # draining: a disc part-emptied
        d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=colour + (a,),
                  width=int(big * 0.028))
        d.pieslice((cx - R, cy - R, cx + R, cy + R), 90, 300, fill=colour + (a,))
    elif stage_id == "fat_burning":                 # droplets leaving
        for k, (dx, dy, rr) in enumerate(((-0.42, 0.10, 0.20), (0.06, -0.30, 0.26),
                                          (0.40, 0.26, 0.16))):
            d.ellipse((cx + dx * big / 2 - rr * big / 2, cy + dy * big / 2 - rr * big / 2,
                       cx + dx * big / 2 + rr * big / 2, cy + dy * big / 2 + rr * big / 2),
                      fill=colour + (a if k == 1 else int(a * 0.75),))
    elif stage_id == "ketosis":                     # rising: three marks climbing
        for k in range(3):
            h = big * (0.16 + 0.13 * k)
            x = cx + (k - 1) * big * 0.20
            d.rounded_rectangle((x - big * 0.045, cy + big * 0.20 - h,
                                 x + big * 0.045, cy + big * 0.20),
                                radius=big * 0.045, fill=colour + (a,))
    else:                                           # autophagy: a ring taking itself in
        d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=colour + (a,),
                  width=int(big * 0.030))
        for ang in range(0, 360, 45):
            t = np.radians(ang)
            d.line((cx + np.cos(t) * R * 0.42, cy + np.sin(t) * R * 0.42,
                    cx + np.cos(t) * R * 0.86, cy + np.sin(t) * R * 0.86),
                   fill=colour + (int(a * 0.8),), width=int(big * 0.022))
    return _rgba(im.resize((D, D), Image.LANCZOS))


def bar(W, H, rows, k):
    """One 0-24 h bar under the last row: where each stage begins, and how far
    this protocol gets. The only element that is about all five rows at once."""
    h = max(3, int(H * BAR_H))
    im = Image.new("RGBA", (W, h * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, x1 = int(W * 0.10), int(W * 0.90)
    d.rounded_rectangle((x0, h, x1, h * 2), radius=h / 2, fill=(255, 255, 255, 40))
    return _rgba(im), x0, x1, h


# ---------------------------------------------------------------------------
# the seam
# ---------------------------------------------------------------------------

def add_arguments(p):
    p.add_argument("--protocol", help="13_11 | 14_10 | 16_8 | 18_6 | 20_4 | 23_1")
    p.add_argument("--fast-times", default="1,2,3.2,4.4,5.6",
                   help="when each row's dial starts its sweep")
    p.add_argument("--fast-cues", help="write the lock instants here, for the SFX")


def build(args, ctx):
    if not args.protocol:
        return None
    if not ctx["layout"]:
        sys.exit("--protocol needs --layout")
    L = json.load(open(ctx["layout"])) if isinstance(ctx["layout"], str) else ctx["layout"]
    W, H = ctx["W"], ctx["H"]
    k = W / 1536.0
    proto, rows = longevity.rows_for(args.protocol)
    times = [float(t) for t in args.fast_times.split(",")]

    plan = []
    for i, (row, lay) in enumerate(zip(rows, L["rows"])):
        r = lay["r"] * k
        # longevity.STAGE_COLOUR gives tuples; a hex string is accepted too so a
        # palette can be overridden from a file without touching this.
        col = row["colour"]
        c = (tuple(int(col.lstrip("#")[j:j + 2], 16) for j in (0, 2, 4))
             if isinstance(col, str) else tuple(int(v) for v in col[:3]))
        plan.append(dict(
            t=times[i] if i < len(times) else times[-1],
            reached=row["reached"], hour=row["hour"],
            cxl=L["anchor_l"] * k, cxr=L["anchor_r"] * k, cy=lay["cy"] * k, r=r,
            dial=dial(r, row["hour"], c, row["reached"]),
            mark=stage_mark(r, row["stage"], c, row["reached"]),
        ))
    # An unreached row's CAPTION is the last thing that still shouts. add_labels
    # burns it into the poster, so the overlay cannot dim what is already pixels
    # - but it can put the clean base back over it, which is the trade this whole
    # design makes everywhere else: what must be identical is never regenerated.
    # Without this the row says "the fast stops before here" and its caption says
    # AUTOPHAGY as loudly as the lit ones, which is a claim made by typography.
    if getattr(args, "base", None):
        clean = np.array(Image.open(args.base).convert("RGB").resize((W, H),
                                                                     Image.LANCZOS)
                         ).astype(np.float32)
        cw = args.caption_w * k / 2 + 10 * k
        for p_, lay in zip(plan, L["rows"]):
            if p_["reached"]:
                continue
            y0, y1 = int(lay["cap_top"] * k) - 4, int((lay["cap_top"] + lay["cap_h"]) * k) + 4
            spans = []
            for cx0 in (L["anchor_l"], L["anchor_r"]):
                x0 = max(0, int(cx0 * k - cw)); x1 = min(W, int(cx0 * k + cw))
                spans.append((y0, y1, x0, x1, clean[y0:y1, x0:x1].copy()))
            p_["caption_patch"] = spans

    lit = sum(1 for r in rows if r["reached"])
    print(f"  {proto['name']}: {lit} of {len(rows)} rows reached, "
          f"dials sweep at {', '.join(f'{p[chr(116)]:.1f}' for p in plan)}s")
    if args.fast_cues:
        with open(args.fast_cues, "w") as fh:
            fh.write(",".join(f"{p['t'] + SWEEP:.3f}" for p in plan if p["reached"]) + "\n")
    return plan


def draw(frame, plan, secs):
    for p in plan:
        s = secs - p["t"]
        if s < 0:
            continue
        # An unreached row still appears - it is the content - but it never
        # sweeps and never locks. It is there from its own instant, dim.
        a = DIM if not p["reached"] else min(1.0, s / 0.12)
        if p["reached"] and s < SWEEP:
            a = min(1.0, s / 0.12)
        for img, cx in ((p["dial"], p["cxl"]), (p["mark"], p["cxr"])):
            _blend(frame, img, a,
                   int(round(cx - img.shape[1] / 2)), int(round(p["cy"] - img.shape[0] / 2)))
        # and the caption comes down to the same weight as the row it belongs to
        for y0, y1, x0, x1, patch in p.get("caption_patch", ()):
            r = frame[y0:y1, x0:x1]
            r *= DIM
            r += patch * (1.0 - DIM)


def cues(plan):
    """The instants a dial locks - only the reached ones make a sound."""
    return sorted(p["t"] + SWEEP for p in plan if p["reached"])


def finale(plan, t0, ctx):
    for p in plan:
        p["finale"] = t0
