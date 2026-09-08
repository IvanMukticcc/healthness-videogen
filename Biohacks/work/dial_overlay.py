#!/usr/bin/env python3
"""
dial_overlay.py - the right circle: where the dial sits, and when it counts.

`dial.py` draws it; this decides when. The split is the same one `bodymap.py` and
`body_overlay.py` make next door, and for the same reason: what a thing looks
like and what it does on a given frame are two questions, and answering them in
one file is how a drawing routine ends up with a clock in it.

The sequence, per row, is the whole grammar of this variant:

    t0          the glyph lights           the hack
    t0 + 0.08   the chip lands             what it costs you
    t0 + 0.18   the ring sweeps, the       what it changes
                number counts, 0.50s

Left to right, cause to effect, in the direction the liquid is already running.
It is the same quarter-second three times over, and by the third row the viewer
is reading the dial before the ring has finished - which is exactly when a format
starts working.

**This overlay owns the finale's timing**, because the dial is the last thing to
move in a row. `cues` reports when a dial has settled, not when it started, so
`--finale auto` cannot land on top of a number still counting.
"""
import json

import numpy as np

import dial
import hacks

LEAD = 0.18         # after the row's cue, the dial starts
COUNT = 0.50        # and how long it takes. Under 0.35 the digits are a blur and
                    # the count reads as a glitch; over 0.7 the row outstays the
                    # rhythm and the finale has nowhere to go
FIN_FLASH = 0.07
FIN_SETTLE = 0.20
FIN_LIFT = 0.55     # the ring going white as the surge passes its column
FIN_GLOW = 0.60
IDLE = 0.34         # how present the resting zero is before the row fires


def plan(rows, layout, W, H, times, fps, base=None, lead=LEAD, count=COUNT, dy=0.0):
    L = json.load(open(layout)) if isinstance(layout, str) else layout
    k = W / 1536.0
    n = max(2, int(round(count * fps)))
    r0 = L["rows"][0]["r"] * k

    font = dial.fit_number([h["value"] for h in rows],
                           2 * (r0 * dial.R_RING - r0 * dial.W_RING / 2 - r0 * dial.PAD))
    widest = max((h["value"] for h in rows), key=len)
    print(f"  every dial at {font.size}px, the size '{widest}' fits in; "
          f"the count is {n} frames")

    out = []
    for i, (h, row) in enumerate(zip(rows, L["rows"])):
        r = row["r"] * k
        cx, cy = L["anchor_r"] * k, row["cy"] * k + dy * k
        bg = (30, 34, 42)
        if base is not None:
            a, b = int(row["stripe"][0] * k), int(row["stripe"][1] * k)
            bg = tuple(np.median(base[a + 8:b - 8, 4:20].reshape(-1, 3), axis=0))
        d = dial.build(h, r, bg, bool(row["light"]), font, n, k=k)
        d.update(row=i, cx=cx, cy=cy, r=r, n=n, count=count,
                 t=(times[i] if i < len(times) else times[-1]) + lead,
                 name=h["name"], dir=h["dir"])
        out.append(d)
    return out


def paint(frame, pl, secs):
    for d in pl:
        D = d["D"]
        x0, y0 = int(round(d["cx"] - D / 2.0)), int(round(d["cy"] - D / 2.0))
        dial.blend(frame, d["disc"], 1.0, x0, y0)
        dial.blend(frame, d["track"], 1.0, x0, y0)

        s = secs - d["t"]
        if s < 0:
            # The dial reads zero before it reads anything else. An empty ring is
            # a hole; a ring with 0% in it is an instrument, and the count that
            # follows is then a needle moving rather than a number appearing.
            # It also puts five numbers on the frame a feed uses as the cover.
            dial.blend(frame, d["nums"][0], IDLE, x0, y0)
            continue
        p = min(1.0, s / d["count"])
        e = 1.0 - (1.0 - p) ** 3                       # the same ease dial.py counts on
        dial.blend(frame, d["arcs"][int(round(e * (len(d["arcs"]) - 1)))], 1.0, x0, y0)
        dial.blend(frame, d["nums"][min(len(d["nums"]) - 1,
                                        int(round(p * (d["n"] - 1))))], 1.0, x0, y0)

        # The finale. The ring goes white as the surge's crest passes this
        # column, and nothing else moves: the number has already been counted and
        # counting it a second time would say the measurement had changed. The
        # ring is the part that may be lit twice, because a ring is a state.
        ft = d.get("fin_t")
        if ft is None or secs < ft:
            continue
        s = secs - ft
        f = max(0.0, 1.0 - max(0.0, s - FIN_FLASH) / FIN_SETTLE) ** 2
        if f > 0.02:
            dial.blend(frame, d["lit"], FIN_LIFT * f, x0, y0)
            dial.blend(frame, d["glow"], FIN_GLOW * f, x0, y0)


# ---------------------------------------------------------------------------
# The seam into engine/flowanim.py --overlay dial_overlay
# ---------------------------------------------------------------------------

def add_arguments(p):
    # --hacks and --hack-times belong to scene_overlay, which is listed first.
    # Declared twice, argparse refuses the parser outright, and that is the right
    # behaviour: two modules owning one flag is two modules that disagree about
    # it the first time one of them changes.
    p.add_argument("--dial-lead", type=float, default=LEAD,
                   help="how long after the row's cue the dial starts counting")
    p.add_argument("--dial-count", type=float, default=COUNT,
                   help="how long the count takes")
    p.add_argument("--dial-dy", type=float, default=0.0)
    p.add_argument("--dial-cues", help="write the instants the dials settle here, "
                                       "for the SFX - the tick train is cut against "
                                       "them and typing them twice drifts by a frame")


def build(args, ctx):
    if not args.hacks:
        return None
    times = [float(t) for t in args.hack_times.split(",")]
    pl = plan(hacks.resolve(args.hacks), ctx["layout"], ctx["W"], ctx["H"], times,
              ctx["fps"], base=ctx["base"], lead=args.dial_lead,
              count=args.dial_count, dy=args.dial_dy)
    for d in pl:
        print(f"    r{d['row'] + 1}: {d['metric']:<18} counts to {d['value']:>7} "
              f"({d['dir']}) over {d['t']:.2f}-{d['t'] + d['count']:.2f}s")
    if args.dial_cues:
        with open(args.dial_cues, "w") as fh:
            fh.write(",".join(f"{d['t']:.3f}:{d['count']:.3f}" for d in pl) + "\n")
    return pl


def cues(pl):
    """When each dial has **settled**, not when it started.

    `--finale auto` takes the last cue any overlay reports and adds the lead. A
    dial reporting its start would put the finale on top of a number still
    counting, and two things arriving at once is one thing nobody sees.
    """
    return sorted(d["t"] + d["count"] for d in pl)


def finale(pl, t0, ctx):
    at = (ctx.get("surge") or {}).get("at")
    for d in pl:
        d["fin_t"] = float(at(d["row"], d["cx"])) if at else float(t0)
    ts = ", ".join(f"{d['fin_t']:.2f}" for d in pl)
    print(f"  dials light again at {ts}s, "
          f"settled by {max(d['fin_t'] for d in pl) + FIN_FLASH + FIN_SETTLE:.2f}s")


def draw(frame, pl, secs):
    paint(frame, pl, secs)
