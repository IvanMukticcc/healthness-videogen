#!/usr/bin/env python3
"""
day_overlay.py - what a hack costs, and the day it sits in.

Two things, and they are one idea. Every other element in this repository is
inside a row. These two are the first that are not: the chip says what the row
costs *you*, and the day bar underneath says the five rows are not a list of five
things but five moments of one day.

THE CHIP. One per row, glass, in the middle of the liquid, saying `10 MIN` or
`2 MIN`. It is the only number in the clip that is about the viewer rather than
about the body, and it is the one that decides whether the video is saved: a
protocol you cannot afford is a fact, and a protocol that costs two minutes is a
plan.

Glass rather than coloured, which is not a style choice. Next door the badges are
red, amber and blue, so the wave palette there is fenced off to lime, cyan,
violet, fuchsia and teal - a third of every row would be lost under an amber
wave. A chip that takes its darkness from whatever is behind it collides with
nothing, so **this variant's wave palette is unrestricted**, which is the one
freedom the other two do not have.

And there is one of it, not three. Measured on the shipped layout at 1536, over
the 415 720 pixels of the wave mask: 22.7% of the liquid is inside a guide circle
and never painted at all, Micro's three 210px badges cover another 54.7%, and
**22.6% of the wave is visible** in a finished micronutrient clip - which is the
22.3% `engine/README.md` arrived at from the other direction. One 313x118 chip
covers 23.6%, and **53.7% is visible here**.

That is not tidiness, it is what makes `--surge` work. The engine's finale
highlight runs the length of every wave, and next door it is nearly invisible
because there is almost no wave left to run along - `engine/README.md` says so
and gives the badges lighting as the effect instead. Here the band is the effect,
and that is measured rather than hoped: rendering the same clip with and without
`--surge` and taking the mean brightness of the 53.8% of the liquid a viewer can
actually see,

    6.50s   +0.00      the two clips are the same picture
    6.58s   +2.33      the band enters row 1
    6.75s   +5.00      peak
    6.92s   +1.02
    7.00s   -0.50      gone

against a run-to-run difference of 0.01 levels (1 sd) over everything before the
finale. Five levels of mean lift across twenty-seven thousand pixels, 355x the
noise floor, in a third of a second.

Do not try to measure this per pixel by diffing two renders. x264 at crf 16 has
lookahead: changing what happens at 6.5s changes how frames at 2s are
reconstructed, and a per-pixel diff of the two files reports 47 693 px of
"difference" before the finale has begun. A spatial mean over a fixed region
averages that away, which is why the noise floor above is 0.01 and not 40 000.

THE DAY BAR. A track under the last row with five stops on it and a head that
moves the whole time. It does three things no per-row element can:

  - it moves from frame 0, so the clip is never still. The first row does not
    fire until 0.70s and a feed decides in about 1.5, so those first seventeen
    frames are the whole of the audition
  - its head reaches each stop exactly as that row fires, so it is a countdown
    to the next event rather than a record of the last
  - it fills, and a bar that is 4/5 full is a reason to stay for the fifth

The stops are evenly spaced and carry their clock times as labels. True
chronological spacing was tried and thrown away: 06:40 and 07:05 are 25 minutes
apart in a seventeen-hour day, which is nine pixels, and two stops nine pixels
apart read as a printing fault rather than as a fact about mornings. The clocks
under them carry the chronology exactly, which is all it was ever for.
"""
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import dial
import hacks

FONT = dial.FONT
SS = dial.SS

# ---- the chip
POP = 0.40          # nothing to settled
RISE = 0.09         # of that, still fading up
RING = 0.32         # the shock ring thrown off at the landing
CH_H = 118.0        # chip height at 1536. The wave is 94 tall, so a chip a
                    # little taller than the liquid reads as sitting on it
CH_PAD = 46.0       # left and right of the text
CH_FILL = 0.74      # how opaque the glass is. Below 0.6 the wave's gloss shows
                    # through the digits and the number stops being crisp; above
                    # 0.85 it is a black box and the liquid appears to be cut

# ---- the day bar
BAR_Y = 2530.0      # the track's centre, at 1536. The clear strip under the last
BAR_H = 14.0        # row runs y 2476-2585 and the logo starts at 2586
BAR_X0 = 250.0      # the two guide-circle columns, so the bar is on the poster's
BAR_X1 = 1270.0     # own grid rather than on a margin of its own
STOP_R = 15.0
LAB_DY = -44.0      # the clock, above the track: below it is the logo
LAB_SIZE = 30


def _rounded(w, h, rgb, alpha, radius=None):
    """A rounded-rectangle plate, anti-aliased the way the rings are."""
    W, H = int(round(w)), int(round(h))
    r = (H / 2.0) if radius is None else radius
    im = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(im).rounded_rectangle((0, 0, W * SS - 1, H * SS - 1),
                                         radius=r * SS, fill=255)
    m = np.array(im.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255.0 * alpha
    return np.dstack([np.broadcast_to(np.float32(rgb), (H, W, 3)), m * 255.0]).copy()


def _outline(w, h, rgb, alpha, width, radius=None):
    W, H = int(round(w)), int(round(h))
    r = (H / 2.0) if radius is None else radius
    im = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(im).rounded_rectangle((0, 0, W * SS - 1, H * SS - 1),
                                         radius=r * SS, outline=255,
                                         width=max(1, int(round(width * SS))))
    m = np.array(im.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255.0 * alpha
    return np.dstack([np.broadcast_to(np.float32(rgb), (H, W, 3)), m * 255.0]).copy()


def _label(text, font, rgb, pad=6):
    b = font.getbbox(text)
    W, H = (b[2] - b[0]) + pad * 2, (b[3] - b[1]) + pad * 2
    im = Image.new("L", (W * SS, H * SS), 0)
    f = ImageFont.truetype(FONT, int(round(font.size * SS)))
    bb = f.getbbox(text)
    ImageDraw.Draw(im).text((pad * SS - bb[0], pad * SS - bb[1]), text, font=f, fill=255)
    m = np.array(im.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255.0
    return np.dstack([np.broadcast_to(np.float32(rgb), (H, W, 3)), m * 255.0]).copy()


def fit_chip(texts, avail, start=110):
    """One size for every chip, from the widest - the house rule, and the same
    argument as `add_labels.fit_all`: five sizes read as five decisions."""
    size = start
    while size > 16:
        f = ImageFont.truetype(FONT, size)
        if all(f.getbbox(t)[2] - f.getbbox(t)[0] <= avail for t in texts):
            return f
        size -= 2
    return ImageFont.truetype(FONT, 16)


# ------------------------------------------------------------------ the chip

def chips(rows, layout, W, H, times, curves=None, lead=0.08, h_px=CH_H,
          gap=26.0, stagger=0.09):
    """One entry per chip. A row may declare more than one and they lay out side
    by side, centred in the gap between the guide circles.

    **One is the shipped default, and the measurement is the argument.** Over the
    415 720 px of the wave mask at 1536, one 313x118 chip covers 23.6% of the
    liquid and leaves 53.7% of it visible; a second takes the cover to about 30%.
    A second chip earns its place when it says something the first cannot - a
    dose and the window it works in - and never when it is filling space.
    """
    L = json.load(open(layout)) if isinstance(layout, str) else layout
    k = W / 1536.0
    x_lo = (L["anchor_l"] + L["rows"][0]["r"]) * k + 20 * k
    x_hi = (L["anchor_r"] - L["rows"][0]["r"]) * k - 20 * k
    texts = [t for h in rows for t in h["chips"]]
    most = max(len(h["chips"]) for h in rows)
    font = fit_chip(texts, (x_hi - x_lo) * 0.62 / most, start=int(round(72 * k)))
    print(f"  {len(texts)} chips over {len(rows)} rows, every one at "
          f"{font.size}px - the size '{max(texts, key=len)}' fits in")

    ch = h_px * k
    g = gap * k
    out = []
    for i, (h, row) in enumerate(zip(rows, L["rows"])):
        widths = [(font.getbbox(t)[2] - font.getbbox(t)[0]) + 2 * CH_PAD * k
                  for t in h["chips"]]
        span = sum(widths) + g * (len(widths) - 1)
        room = x_hi - x_lo
        if span > room:                            # shrink to fit, never overflow
            widths = [w * (room - g * (len(widths) - 1)) / sum(widths) for w in widths]
            span = sum(widths) + g * (len(widths) - 1)
        x = (x_lo + x_hi) / 2.0 - span / 2.0
        for j, (text, cw) in enumerate(zip(h["chips"], widths)):
            cx = x + cw / 2.0
            x += cw + g
            cy = row["cy"] * k
            if curves is not None and i < len(curves) and curves[i] is not None:
                # On the liquid's own centre line, not the row's - the wave
                # crosses the row centre twice and sits on it nowhere, so a chip
                # placed there floats off the thing it is meant to be riding.
                lo = row["stripe"][0] * k + ch * 0.5 + 8 * k
                hi = row["cap_top"] * k - ch * 0.5 - 8 * k
                cy = float(np.clip(curves[i](cx), lo, hi))
            out.append(_one(text, cx, cy, cw, ch, font, i, k,
                            (times[i] if i < len(times) else times[-1])
                            + lead + j * stagger))
    return out


def _one(text, cx, cy, cw, ch, font, row, k, t):
    """Glass: a dark plate, a light rim, and a highlight along the top third.

    The rim is what makes it read as a surface rather than a hole - the app this
    is for is built in iOS 26's liquid glass and this is the same material, drawn
    rather than blurred, because there is nothing behind it to sample on a frame
    that has not been composited yet.
    """
    return dict(row=row, cx=cx, cy=cy, w=cw, h=ch, text=text, t=t,
                plate=_rounded(cw, ch, (10, 16, 20), CH_FILL),
                rim=_outline(cw, ch, (255, 255, 255), 0.30, 2.4 * k),
                gloss=_rounded(cw - 8 * k, ch * 0.42, (255, 255, 255), 0.10),
                lab=_label(text, font, (255, 255, 255)))


def _ease(p):
    """easeOutBack: starts at exactly 0, overshoots about 15%, settles on 1.
    A chip that fades in is furniture; a chip that overshoots is an event."""
    c1, c3 = 2.2, 3.2
    q = p - 1.0
    return 1.0 + c3 * q * q * q + c1 * q * q


def _chip_ring(frame, c, p):
    r0, r1 = c["h"] * 0.55, c["h"] * 1.30
    r = r0 + (r1 - r0) * (1 - (1 - p) ** 2)
    a = (1.0 - p) ** 1.6 * 0.42
    if a < 0.01:
        return
    w = max(1.0, c["h"] * 0.05 * (1 - p) + 1.0)
    W = int(c["w"] + 2 * r + 4)
    Hh = int(c["h"] + 2 * r + 4)
    im = Image.new("L", (W, Hh), 0)
    ImageDraw.Draw(im).rounded_rectangle(
        ((W - c["w"]) / 2 - r, (Hh - c["h"]) / 2 - r,
         (W + c["w"]) / 2 + r, (Hh + c["h"]) / 2 + r),
        radius=c["h"] / 2 + r, outline=255, width=int(round(w)))
    m = np.array(im).astype(np.float32) / 255.0 * a
    src = np.dstack([np.full((Hh, W, 3), 255.0, np.float32), m * 255.0])
    dial.blend(frame, src, 1.0, int(round(c["cx"] - W / 2)), int(round(c["cy"] - Hh / 2)))


def paint_chips(frame, cs, secs, ring=True):
    for c in cs:
        s = secs - c["t"]
        if s < 0:
            continue
        alpha = min(1.0, s / RISE) if RISE > 0 else 1.0
        scale = _ease(min(1.0, s / POP))
        if scale <= 0.01 or alpha <= 0.002:
            continue
        if ring and s < RING:
            _chip_ring(frame, c, s / RING)
        for layer, dy in ((c["plate"], 0.0), (c["gloss"], -c["h"] * 0.24),
                          (c["rim"], 0.0), (c["lab"], 0.0)):
            h0, w0 = layer.shape[:2]
            if abs(scale - 1.0) > 0.004:
                w1, h1 = max(2, int(round(w0 * scale))), max(2, int(round(h0 * scale)))
                im = Image.fromarray(np.clip(layer, 0, 255).astype(np.uint8), "RGBA") \
                          .resize((w1, h1), Image.LANCZOS)
                layer = np.array(im).astype(np.float32)
                h0, w0 = h1, w1
            dial.blend(frame, layer, alpha,
                       int(round(c["cx"] - w0 / 2.0)),
                       int(round(c["cy"] + dy * scale - h0 / 2.0)))


# ------------------------------------------------------------------ the day bar

def daybar(rows, W, H, times, seconds, finale_hint=None, y=BAR_Y):
    """The track, its five stops, and the piecewise map from time to head.

    The head is not a linear function of the clip. It is bent so that it arrives
    at stop i exactly at row i's cue: between the cues it is a straight run, and
    the effect is that the bar is always pointing at whatever is about to happen.
    A head that simply crossed at constant speed would be behind the rows for the
    first half and ahead of them for the second, and would read as a decoration
    that happens to be moving.
    """
    k = W / 1536.0
    x0, x1 = BAR_X0 * k, BAR_X1 * k
    y = y * k
    h = BAR_H * k
    n = len(rows)
    xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]

    font = ImageFont.truetype(FONT, max(12, int(round(LAB_SIZE * k))))
    end = finale_hint if finale_hint else seconds
    # (t, p) knots. 0 at the start, each stop at its row's cue, the end of the
    # track at the finale - so the bar completes on the instant the clip resolves
    # rather than a beat after it.
    knots = [(0.0, 0.0)] + [(times[i], (xs[i] - x0) / (x1 - x0)) for i in range(n)] \
            + [(end, 1.0)]
    return dict(x0=x0, x1=x1, y=y, h=h, xs=xs, knots=knots,
                track=_rounded(x1 - x0, h, (255, 255, 255), 0.16),
                stops=[dict(row=i, x=xs[i], t=times[i], clock=rows[i]["clock"],
                            colour=hacks.colour(rows[i]),
                            lab=_label(rows[i]["clock"], font, (255, 255, 255)))
                       for i in range(n)],
                r=STOP_R * k, lab_dy=LAB_DY * k, k=k)


def _head(db, secs):
    ks = db["knots"]
    if secs <= ks[0][0]:
        return 0.0
    for (t0, p0), (t1, p1) in zip(ks, ks[1:]):
        if secs <= t1:
            u = (secs - t0) / max(1e-6, t1 - t0)
            return p0 + (p1 - p0) * u
    return 1.0


def paint_daybar(frame, db, secs, fin=None):
    x0, x1, y, h, r = db["x0"], db["x1"], db["y"], db["h"], db["r"]
    dial.blend(frame, db["track"], 1.0, int(round(x0)), int(round(y - h / 2)))

    p = _head(db, secs)
    fw = (x1 - x0) * p
    if fw > 2:
        fill = _rounded(fw, h, (255, 255, 255), 0.90)
        dial.blend(frame, fill, 1.0, int(round(x0)), int(round(y - h / 2)))

    for s in db["stops"]:
        lit = secs >= s["t"]
        col = s["colour"] if lit else (255, 255, 255)
        a = 1.0 if lit else 0.30
        rr = r * (1.0 + 0.55 * max(0.0, 1.0 - (secs - s["t"]) / 0.28) ** 2) if lit else r
        D = int(round(rr * 2)) + 2
        im = Image.new("L", (D * SS, D * SS), 0)
        ImageDraw.Draw(im).ellipse((SS, SS, D * SS - SS, D * SS - SS), fill=255)
        m = np.array(im.resize((D, D), Image.LANCZOS)).astype(np.float32) / 255.0 * a
        src = np.dstack([np.broadcast_to(np.float32(col), (D, D, 3)), m * 255.0]).copy()
        dial.blend(frame, src, 1.0, int(round(s["x"] - D / 2)), int(round(y - D / 2)))

        lab = s["lab"]
        dial.blend(frame, lab, 1.0 if lit else 0.34,
                   int(round(s["x"] - lab.shape[1] / 2)),
                   int(round(y + db["lab_dy"] - lab.shape[0] / 2)))


# ---------------------------------------------------------------------------
# The seam into engine/flowanim.py --overlay day_overlay
# ---------------------------------------------------------------------------

class Plan(list):
    """The chips, with the day bar riding along, so the seam stays three
    functions wide rather than becoming two plans the engine has to know about."""
    bar = None


def add_arguments(p):
    p.add_argument("--chip-lead", type=float, default=0.08,
                   help="after the glyph, before the dial - the row reads left to "
                        "right in the direction the liquid runs")
    p.add_argument("--chip-h", type=float, default=CH_H,
                   help="chip height at 1536; the wave is 94 tall")
    p.add_argument("--chip-ring", type=int, default=1)
    p.add_argument("--chip-follow", type=int, default=1,
                   help="1 sits the chip on the wave's own centre line, 0 on the row's")
    p.add_argument("--daybar", type=int, default=1,
                   help="0 drops the day bar and the clip becomes five unrelated rows")
    p.add_argument("--daybar-y", type=float, default=BAR_Y,
                   help="the track's centre at 1536. 2530 is the middle of the "
                        "clear strip the base leaves between the last caption bar "
                        "(ends 2456) and the logo (starts 2586), and it is the only "
                        "band wide enough. It is also 92%% of the way down the "
                        "poster, which is where a feed draws its own caption - the "
                        "same zone row 5's captions and the logo have always been "
                        "in, so this is no worse than what ships, but it is where "
                        "to look first if a platform starts covering it")
    p.add_argument("--chip-cues", help="write the landing times here, for the SFX")


def build(args, ctx):
    if not args.hacks:
        return None
    rows = hacks.resolve(args.hacks)
    times = [float(t) for t in args.hack_times.split(",")]
    cs = chips(rows, ctx["layout"], ctx["W"], ctx["H"], times,
               curves=ctx["curves"] if args.chip_follow else None,
               lead=args.chip_lead, h_px=args.chip_h)
    pl = Plan(cs)
    ts = ", ".join(f"{c['t']:.2f}" for c in pl)
    print(f"  {len(pl)} chips land at {ts}s")
    if args.chip_cues:
        with open(args.chip_cues, "w") as fh:
            fh.write(",".join(f"{c['t']:.3f}" for c in pl) + "\n")
    if args.daybar:
        # The finale is not known yet - it is computed from the cues after every
        # build has run. The bar is told the clip's length now and corrected in
        # `finale`, which is the one place the real instant exists.
        pl.bar = daybar(rows, ctx["W"], ctx["H"], times, ctx["seconds"],
                        y=args.daybar_y)
        print(f"  day bar {pl.bar['x0']:.0f}-{pl.bar['x1']:.0f} at y {pl.bar['y']:.0f}, "
              f"stops at {', '.join(s['clock'] for s in pl.bar['stops'])}")
    _RING[0] = bool(args.chip_ring)
    return pl


_RING = [True]


def cues(pl):
    return sorted(c["t"] for c in pl)


def finale(pl, t0, ctx):
    """The bar completes on the finale, not on the last frame.

    Told the clip's length at build time it would still be creeping while the
    chord rings and the surge runs, and the one thing a resolution may not do is
    arrive while something else is still travelling.
    """
    if pl.bar is not None:
        ks = pl.bar["knots"]
        pl.bar["knots"] = ks[:-1] + [(float(t0), 1.0)]
    for c in pl:
        c["fin_t"] = float(t0)


def draw(frame, pl, secs):
    paint_chips(frame, pl, secs, ring=_RING[0])
    if pl.bar is not None:
        paint_daybar(frame, pl.bar, secs)
