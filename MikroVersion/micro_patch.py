#!/usr/bin/env python3
"""
micro_patch.py - the badge layer, applied to the engine rather than forked from it.

The badges need three things inside `flowanim.py`: its arguments, one planning
step once the geometry is known, and one draw at the end of every frame. There is
no hook for that, and the frame loop is local to `main()`, so it cannot be
reached from outside.

The obvious answer is to keep a copy of `flowanim.py` here with the badge lines
in it, and that answer is wrong. It is what `engine/` was just created to end:
`OTHER`, `MikroVersion` and `ExerciseVersion` each held a copy, they drifted
apart in a morning, and a poster was generated from a three-revision-old prompt
because nobody could see it happen.

So this is a derivation, not a copy. It reads `../engine/flowanim.py` as it
stands, inserts three blocks at three anchors, and writes the result to
`work/flowanim_micro.py`, which is scrap and is rebuilt on every render. If the
engine moves, the derivation moves with it. If an anchor disappears, this stops
with the anchor that is missing rather than producing something that half works.

The right long-term fix is one hook in the engine - a callable the frame loop
invokes once per frame - and then this file becomes four lines. Until the engine
offers it, this keeps the badge layer in one place without holding a second copy
of a fifty-kilobyte file that somebody else is editing.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "engine", "flowanim.py")
OUT = os.path.join(HERE, "work", "flowanim_micro.py")

ARGS = '''    # --- micronutrient badges (MikroVersion) -------------------------------
    # Off unless --micro is given, so every engine command line still renders
    # exactly the video it used to.
    p.add_argument("--micro", help="badges per row: 'A,C;Iron,Zinc;...' (';' between "
                                   "rows), or 'auto:FOOD,FOOD,...' to look each food "
                                   "up in nutrients.json")
    p.add_argument("--micro-times", default="1,2,4,5.5,7",
                   help="when each row's badges land, in seconds")
    p.add_argument("--micro-d", type=float, default=210.0,
                   help="badge diameter at 1536 wide")
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
    p.add_argument("--micro-dir", default=micro_overlay.MICRO_DIR)
    p.add_argument("--micro-cues", help="write the landing times here, for the SFX")
    # -----------------------------------------------------------------------
'''

PLAN = '''    mplan = []
    if args.micro:
        if not args.layout:
            sys.exit("--micro needs --layout: the badges sit on the row the layout describes")
        rows = micro_overlay.resolve(args.micro)
        times = [float(t) for t in args.micro_times.split(",")]
        curves = None
        if args.micro_follow:
            # The wave's own centre line, read off the geometry that is about to
            # be animated - so the badges sit in the liquid however the poster
            # drew it, instead of on a row centre the wave may not pass through.
            LJ = json.load(open(args.layout))
            k = W / 1536.0
            curves = []
            for row in LJ["rows"]:
                cy = row["cy"] * k
                g = min(geo, key=lambda g: abs(0.5 * (g["top"].mean() + g["bot"].mean()) - cy))
                # top/bot are stored in the ribbon's own column range, so the
                # index is x - x0, not x.
                mid = 0.5 * (g["top"] + g["bot"])
                x0 = g["x0"]
                curves.append(lambda x, mid=mid, x0=x0:
                              float(mid[int(np.clip(round(x) - x0, 0, len(mid) - 1))]))
        mplan = micro_overlay.plan(rows, args.layout, W, H, times, curves=curves,
                                   diameter=args.micro_d, gap=args.micro_gap,
                                   stagger=args.micro_stagger, dy=args.micro_dy,
                                   micro_dir=args.micro_dir, seconds=args.seconds,
                                   fade=args.micro_fade)
        cues = micro_overlay.pop_times(mplan)
        print(f"  {len(mplan)} micronutrient badges land at "
              f"{', '.join(f'{t:.2f}' for t in cues)}s")
        if args.micro_cues:
            with open(args.micro_cues, "w") as fh:
                fh.write(",".join(f"{t:.3f}" for t in cues) + "\\n")

'''

DRAW = '''        # Last, and outside the protect pass: the badges are drawn on top of the
        # finished frame, so nothing in the liquid pipeline has to know they exist.
        if mplan:
            micro_overlay.paint(out, mplan, f / args.fps, ring=bool(args.micro_ring))
'''

IMPORT = '''
# MikroVersion: the badge layer lives beside this file's source, not in the engine.
sys.path.insert(0, {here!r})
import micro_overlay
'''


def cut(s, anchor, block, where="before"):
    if anchor not in s:
        raise SystemExit(f"micro_patch: the engine no longer has this anchor:\\n  {anchor}\\n"
                         f"read ../engine/flowanim.py and move the insertion point")
    return s.replace(anchor, block + anchor if where == "before" else anchor + block, 1)


def main():
    src = open(ENGINE).read()
    src = cut(src, "\ndef autocrop(", IMPORT.format(here=HERE))
    src = cut(src, '    p.add_argument("--layout", help="the _layout.json the base wrote")', ARGS)
    src = cut(src, '    cmd = ["ffmpeg", "-y", "-loglevel", "error",', PLAN)
    src = cut(src, "        out[protect] = base[protect]\n", DRAW, where="after")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        fh.write(src)
    print(f"  badge layer applied to {os.path.relpath(ENGINE, HERE)} -> "
          f"{os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
