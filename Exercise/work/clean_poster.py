#!/usr/bin/env python3
"""
clean_poster.py - take back the parts of the poster that were never the
generator's: the right circle, and the ten caption bars.

The prompt calls the right circle finished artwork, lists what not to put there,
and tells the model to keep the bars clear. It draws in both anyway. On PULL DAY
it rubbed out the guide circle and the caption bar under it and drew a stroked
ring of its own, radius about 200 against the circle's 138 - and the body's disc
covers 138, so a ring outside it survives into the video as a hoop around every
body. On the left it filled its circle with a photo disc half again as wide as
the mark, which then hung over the top third of the caption bar.

Regenerating is the documented answer to artwork that straddles the circle's
edge, and it stays the right answer when the generator has drawn something that
cannot be reconstructed. This is not that case. Every pixel this touches is base
content by design - the row stripe, the tail of the wave, the guide circle, the
caption bar - and the base is on disk at pixel-exact geometry (check_base
reports 0.0 px of drift). So the region is copied back rather than asked for
again, which is the trade the whole design makes everywhere else: what must be
identical is never regenerated.

The bars matter as much as the ring, and less obviously. add_labels.py picks its
ink from whether the ROW is light or dark - white on the dark rows, near-black
on the light ones - which is right for a bar the base drew and wrong for a photo
lying over it. Here the discs are inverted against their rows, so every left
caption would have been drawn in the one colour the thing underneath it shares:
white on a white disc, black on a black one. Restoring the bars first makes the
rule true again rather than teaching it exceptions.

Only the row's own stripe is touched, so a generous circle radius cannot reach
the row above or below, and the athlete is only ever clipped where it lies in
its own caption bar.

    ../.venv/bin/python clean_poster.py poster.jpeg --base ../INPUT/base_pull.png \
        -l base_pull_layout.json -o pull_clean.png
"""
import argparse
import json
import numpy as np
from PIL import Image


def restore(out, pos, base, a):
    """Blend the base back in under a soft mask, and say how much was covering it."""
    changed = int(((np.abs(pos - base).max(axis=-1) > 30) & (a > 0.5)).sum())
    return out * (1 - a[:, :, None]) + base * a[:, :, None], changed


def main():
    p = argparse.ArgumentParser()
    p.add_argument("poster")
    p.add_argument("-b", "--base", required=True, help="base_<topic>.png, circles and all")
    p.add_argument("-l", "--layout", required=True)
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--radius", type=float, default=340.0,
                   help="how far from the right circle's centre to restore. The "
                        "ring the generator drew reaches 215; the caption bar's "
                        "far corners are 303 away")
    p.add_argument("--caption-w", type=int, default=380, help="as recolor_base drew them")
    p.add_argument("--bars", type=int, default=1,
                   help="0 leaves the caption bars as the generator left them")
    p.add_argument("--feather", type=float, default=3.0,
                   help="soft edge on the restored patch, so the seam is not a "
                        "shape of its own where jpeg noise meets clean png")
    args = p.parse_args()

    pos = np.asarray(Image.open(args.poster).convert("RGB"), np.float32)
    base = np.asarray(Image.open(args.base).convert("RGB"), np.float32)
    if pos.shape != base.shape:
        raise SystemExit(f"poster is {pos.shape[1]}x{pos.shape[0]}, base is "
                         f"{base.shape[1]}x{base.shape[0]} - resize before cleaning")
    L = json.load(open(args.layout))
    H, W = pos.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    f = max(args.feather, 1e-3)

    out = pos.copy()
    for i, row in enumerate(L["rows"], 1):
        cx, cy = float(L["anchor_r"]), float(row["cy"])
        lo, hi = row["stripe"]
        in_row = (yy >= lo) & (yy < hi)

        a = np.clip((args.radius - np.hypot(xx - cx, yy - cy)) / f, 0, 1)
        a[~in_row] = 0.0                       # never past the row's own stripe
        out, n = restore(out, pos, base, a)
        print(f"  r{i}: right circle, r<{args.radius:.0f} inside y {lo}-{hi}"
              f"   ({n} px the generator had changed)")

        if not args.bars:
            continue
        # The same rounded slab recolor_base drew: a capsule of height cap_h.
        hw, hh = args.caption_w / 2.0, row["cap_h"] / 2.0
        ccy = row["cap_top"] + hh
        for side, bx in (("left", float(L["anchor_l"])), ("right", float(L["anchor_r"]))):
            dx = np.clip(np.abs(xx - bx) - (hw - hh), 0, None)
            b = np.clip((hh - np.hypot(dx, yy - ccy)) / f, 0, 1)
            b[~in_row] = 0.0
            out, n = restore(out, pos, base, b)
            if n:
                print(f"      {side} caption bar: {n} px taken back")

    Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8)).save(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
