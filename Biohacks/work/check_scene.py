#!/usr/bin/env python3
"""
check_scene.py - is a scene-mode poster good enough to spend a render on?

`engine/check_base.py` answers the only question that can break the video: did
the waves move. This answers the five that decide whether the picture is any
good, and it answers them in numbers so that sending one back is a measurement
rather than an opinion.

    0. IS IT OURS  does this poster even come from this topic's base? The title
                  is drawn into the base and the prompt forbids touching it, so
                  |poster - base| over the title band is near zero for a poster
                  of ours and enormous for anyone else's.

                  This is first because it is the check that invalidates all the
                  others, and because nothing else catches it: `grab.py` takes
                  the newest 1536x2752 file in Downloads and cannot know which
                  variant it belongs to, and every variant is built on the same
                  base geometry - so an Exercise poster passed check_base.py's
                  wave test AND all four checks below. Measured: 4.0 mean for
                  ours, 86.4 for the one that was not.

    1. MARKS      is the LEFT circle painted over, or did the generator paint the
                  photograph around it and leave it standing? A flat disc has
                  almost no variance; a photograph has a lot, and that one number
                  separates them cleanly.

                  The right circle is not tested and does not matter: the dial
                  covers it at 0.97 alpha whatever is underneath. The first
                  version of this tested both, took the worse of the two, and
                  sent back a poster whose left circles were all correct
    2. LIGHTNESS  does each band still read the way the layout says it does?
                  add_labels.py picks white or near-black ink from that flag
                  before it has seen the photograph, so a band that flipped
                  loses its caption entirely
    3. THE JOIN   is the wave's blunt left cut hidden? This is the defect that
                  shows, and it is measured where it happens: |poster - base| in
                  the 70px just right of the wave's start, on the wave's own rows.
                  Something drawn there - a splash, a shoulder, a plume of breath
                  - reads 49-210. A cut left standing in the open reads 26.

                  This replaces two attempts to measure where the SUBJECT is, and
                  both failed on the same band. Share-of-the-left-third passed a
                  man standing squarely in the middle at 35% against a 34% floor.
                  The centroid of the band's detail then flagged a band whose man
                  WAS at the far left, because his dark trousers are a large flat
                  area and the lamp and laptop behind him are not: detail
                  measures where a picture is busy, not where its subject is.
                  What the design actually needs is not the subject at x=16% - it
                  is the seam covered, and that is one number away
    4. RIGHT      is the right third quiet? Anything drawn there survives past
                  the dial's disc and nudges the wave's tip
    5. FOOTER     is the strip under the last band empty? The day bar goes there
                  and has nothing to hide behind

    python3 check_scene.py firsthour
"""
import argparse
import json
import sys

import numpy as np
from PIL import Image

# A flat disc left standing measures std 0.8-8; a photograph painted over the
# mark measures 24-79. Both ends measured on the two firsthour posters, so the
# line between them is drawn where there is nothing near it.
OURS_DIFF = 25.0            # mean |poster - base| over the title band. Ours
                            # measures 4.0, another variant's poster 86.4
TITLE = (191, 392)          # where recolor_base.py draws the title, at 1536
MARK_STD = 15.0
LIGHT_LUMA = 150.0          # over this a band reads light, under it dark
JOIN_DIFF = 40.0            # levels between poster and base at the wave's start.
                            # Measured over five bands that merge well: 49, 100,
                            # 146, 210. One that does not: 26


def luma(a):
    return float(np.dot(a.reshape(-1, 3).mean(axis=0), (0.299, 0.587, 0.114)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("topic")
    p.add_argument("--poster")
    p.add_argument("--layout")
    p.add_argument("--base")
    a = p.parse_args()
    poster = a.poster or f"{a.topic}.jpeg"
    layout = a.layout or f"base_{a.topic}_layout.json"
    basef = a.base or f"../INPUT/base_{a.topic}.png"

    img = np.asarray(Image.open(poster).convert("RGB")).astype(np.float32)
    base = np.asarray(Image.open(basef).convert("RGB")).astype(np.float32)
    H, W, _ = img.shape
    L = json.load(open(layout))
    k = W / 1536.0
    yy, xx = np.mgrid[0:H, 0:W]
    bad = []

    ty0, ty1 = int(TITLE[0] * k), int(TITLE[1] * k)
    ours = float(np.abs(img[ty0:ty1] - base[ty0:ty1]).max(axis=2).mean())
    print(f"{poster}  {W}x{H}")
    if ours >= OURS_DIFF:
        print(f"\n  THIS IS NOT A POSTER OF base_{a.topic}.png. The title band is "
              f"{ours:.0f} levels from the base (ours measures ~4).\n"
              f"  grab.py takes the newest 1536x2752 file in Downloads and cannot "
              f"know whose it is,\n  and every variant shares this base geometry - "
              f"so the wave check passes on someone\n  else's poster. Put it back "
              f"where it came from and grab again.")
        sys.exit(1)
    print(f"  from our base (title band {ours:.1f} levels off, limit {OURS_DIFF:.0f})\n")
    print("  band  left mark      lightness          the join     right third")
    for i, row in enumerate(L["rows"]):
        y0, y1 = int(row["stripe"][0] * k), int(row["stripe"][1] * k)
        band = img[y0:y1]
        cy, r = row["cy"] * k, row["r"] * k

        m = np.hypot(xx - L["anchor_l"] * k, yy - cy) < r * 0.6
        std = float(img[m].std(axis=0).mean())
        marks_ok = std >= MARK_STD

        lu = luma(band)
        want_light = bool(row["light"])
        light_ok = (lu >= LIGHT_LUMA) == want_light

        # Where the picture's detail is. A subject on the left puts it there; the
        # empty half of a bright kitchen puts almost none anywhere.
        det = np.abs(np.diff(band.mean(axis=2), axis=1))
        tot = float(det.sum())
        third = det.shape[1] // 3
        share = float(det[:, :third].sum() / tot) if tot else 0.0
        right = float(det[:, 2 * third:].sum() / tot) if tot else 0.0
        right_ok = right <= share

        # The wave starts at x 229 of 1536. Look at the 70 px just right of that,
        # over the wave's own band, and ask how far the poster has moved from the
        # base there. Nothing drawn = nothing moved = the cut is in the open.
        jx0, jx1 = int(229 * k), int(300 * k)
        jy0, jy1 = int((row["cy"] - 60) * k), int((row["cy"] + 60) * k)
        join = float(np.abs(img[jy0:jy1, jx0:jx1]
                            - base[jy0:jy1, jx0:jx1]).max(axis=2).mean())
        join_ok = join >= JOIN_DIFF

        for ok, why in ((marks_ok, f"r{i+1} left circle still standing (std "
                                   f"{std:.1f}, want >{MARK_STD:.0f}) - the "
                                   f"photograph was painted around it, not over it"),
                        (light_ok, f"r{i+1} is {'light' if lu >= LIGHT_LUMA else 'dark'} "
                                   f"(luma {lu:.0f}) and the layout says "
                                   f"{'light' if want_light else 'dark'} - the caption "
                                   f"will be drawn in the wrong ink"),
                        (join_ok, f"r{i+1} the wave's left cut is in the open "
                                  f"(only {join:.0f} levels of anything drawn over "
                                  f"it, want {JOIN_DIFF:.0f}) - the subject has to "
                                  f"overlap the start of the liquid, not sit beside it"),
                        (right_ok, f"r{i+1} right third is busier than the left "
                                   f"({100*right:.0f}% against {100*share:.0f}%)")):
            if not ok:
                bad.append(why)

        print(f"   {i+1}    {std:5.1f} {'ok ' if marks_ok else 'NO '}   "
              f"{lu:5.1f} {'light' if lu >= LIGHT_LUMA else 'dark ':<5} "
              f"{'ok ' if light_ok else 'NO '}   "
              f"{join:5.0f} {'ok ' if join_ok else 'NO '}   "
              f"{100*right:4.0f}% {'ok ' if right_ok else 'NO '}")

    # the footer, where the day bar goes
    f0, f1 = int(2476 * k), int(2585 * k)
    foot = img[f0:f1]
    fd = float(np.abs(np.diff(foot.mean(axis=2), axis=1)).mean())
    foot_ok = fd < 1.5
    print(f"\n  footer strip y {f0}-{f1}: detail {fd:.2f} "
          f"{'ok - empty, the day bar can go there' if foot_ok else 'NO - something is drawn there'}")
    if not foot_ok:
        bad.append("the strip under the last band is not empty")

    if bad:
        print(f"\nSEND IT BACK - {len(bad)} thing(s) to fix:")
        for w in bad:
            print(f"  - {w}")
    else:
        print("\nGOOD ENOUGH TO RENDER")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
