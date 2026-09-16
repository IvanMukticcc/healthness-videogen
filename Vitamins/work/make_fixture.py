#!/usr/bin/env python3
"""
make_fixture.py - an Organs poster with the organs taken out, for testing.

**This makes a TEST FIXTURE, not a poster.** Nothing it writes may ship. It
exists so the Vitamins path can be exercised end to end - empty right circle,
composited ball, no act-one finale, the turn, the card - without waiting on a
generation, and so that a change to any of those can be checked the same way
tomorrow.

    ./make_fixture.py ../../Organs/work/ageing_poster.jpeg demo

WHAT IT DOES, AND WHY THAT IS ALLOWED

It copies the right-hand region of every row out of the ANCHORED base and back
over the poster. ../../CLAUDE.md rule 9 draws the line exactly here: putting base
pixels back is fine and reconstructing is not, and the region it restores is one
with nothing in it that legitimately belongs over it - in a Vitamins poster the
right circle is empty by construction.

The anchored base rather than the clean copy, deliberately. A real Vitamins
poster comes back with its right circle *untouched*, guide mark and all, because
that is what the prompt asks for; `flowanim.py --anchored` then sees the poster
still equalling the anchored base there, concludes the generator covered nothing,
and puts the clean base back itself. Restoring from the clean copy would skip
that step and test a path no real poster takes.

WHY THE REGION IS WIDER THAN THE CIRCLE

Measured on the ageing poster, the organs run past the guide circle: 1389 to 4937
px between r and 1.35r, and another 172 to 639 out to 2r. A disc the size of the
mark would have left a rim of organ around a ball that only covers the mark.

1.9r was the first guess and it was not enough: 21 to 416 px survived on every
row, all of it between 1.90r and 3.00r, and on rows 4 and 5 it reached x=1535 -
the right edge of the poster, 128px outside the guide circle, where no ball will
ever cover it. 3.2r leaves **0 px on all five rows**, which is the number this
default is set from. The region is clipped to the row's own stripe and stops
above the caption bar, so a radius this wide still cannot reach the row above or
the reserved strip below.

The script prints what is still different afterwards, every time, because a
fixture nobody measured is a fixture that quietly tests the wrong thing - and
because the next poster fed to it will have its organs in different places.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image


def main():
    p = argparse.ArgumentParser()
    p.add_argument("poster", help="an Organs poster, organs and all")
    p.add_argument("topic", help="the Vitamins topic it becomes - base_<topic>.png "
                                 "and base_<topic>_layout.json must already be here")
    p.add_argument("--radius", type=float, default=3.2,
                   help="how far out to restore, in guide-circle radii. 3.2 is "
                        "measured, not chosen: see the docstring")
    p.add_argument("-o", "--out")
    a = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    anchored = os.path.join(here, "..", "INPUT", f"base_{a.topic}.png")
    layout = os.path.join(here, f"base_{a.topic}_layout.json")
    out = a.out or os.path.join(here, f"{a.topic}_fixture.png")
    for f in (a.poster, anchored, layout):
        if not os.path.exists(f):
            raise SystemExit(f"missing: {f}")

    L = json.load(open(layout))
    post = np.asarray(Image.open(a.poster).convert("RGB")).astype(np.uint8)
    base = np.asarray(Image.open(anchored).convert("RGB")).astype(np.uint8)
    if post.shape != base.shape:
        raise SystemExit(f"poster is {post.shape[1]}x{post.shape[0]} and the base "
                         f"is {base.shape[1]}x{base.shape[0]} - they must match")

    H, W = post.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    out_arr = post.copy()
    region = np.zeros((H, W), bool)
    for row in L["rows"]:
        cx, cy, r = L["anchor_r"], row["cy"], row["r"]
        disc = np.hypot(xx - cx, yy - cy) < r * a.radius
        # Clipped to this row: above the caption bar so the reserved strip is
        # left exactly as the poster has it, and inside the stripe so a wide
        # radius cannot reach into the row above.
        band = (yy >= row["stripe"][0]) & (yy < row["cap_top"])
        region |= disc & band
    out_arr[region] = base[region]
    Image.fromarray(out_arr).save(out)

    # WHAT IS LEFT. The verdict is not "done", it is how much of the generator's
    # right-hand artwork survived the restore - and where.
    d = np.abs(out_arr.astype(np.int16) - base.astype(np.int16)).max(axis=2) > 45
    print(f"  {os.path.basename(out)}: restored {int(region.sum())} px "
          f"from {os.path.basename(anchored)}")
    worst = 0
    for i, row in enumerate(L["rows"], 1):
        cx, cy, r = L["anchor_r"], row["cy"], row["r"]
        dist = np.hypot(xx - cx, yy - cy)
        band = (yy >= row["stripe"][0]) & (yy < row["cap_top"])
        inside = int((d & band & (dist < r * 1.06)).sum())     # under the ball
        around = int((d & band & (dist >= r * 1.06)
                      & (dist < r * 3.0)).sum())               # beside it, visible
        worst = max(worst, around)
        print(f"    r{i}: {inside:6d} px left under the ball, {around:5d} px beside it")
    print(f"  the ball covers a disc of 1.06r, so the second column is what a "
          f"viewer would see. Worst row: {worst} px.")


if __name__ == "__main__":
    main()
