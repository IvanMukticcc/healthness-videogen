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

                  This was first because it was the check that invalidated all
                  the others: `grab.py` takes the newest 1536x2752 file in
                  Downloads and cannot know which variant it belongs to, and
                  every variant is built on the same base geometry - so an
                  Exercise poster passed check_base.py's wave test AND all four
                  checks below.

                  **`engine/check_base.py` does this now** (`--title-tol`, 8 by
                  default, refusing before every other test), so this is a
                  second line of defence rather than the only one. It is kept
                  because it runs on the poster this folder is about to label
                  and render, and a check that costs one subtraction is not
                  worth removing to save it.

                  **And it finds a foreign BASE, not a foreign topic.** Two
                  posters gave 4.0 for ours against 86.4 for a stranger's, and
                  that separation is an artefact of a sample of two. The root
                  widened it to 37 posters and 1332 mismatched pairs: own base
                  runs 0.0-3.2 and the best mismatch is 2.41, which is *below*
                  the worst legitimate match - so no threshold separates the ten
                  pairs that share a title. `liver` and `lungs` exist in two
                  variants each, and Micro's superfoods run is one title across
                  many topics. Had the poster that started this happened to
                  share a title with the one it was meant to be, everything here
                  would have passed it.

                  Nothing in this folder collides today - `5 FREE BIOHACKS`,
                  `YOUR FIRST HOUR`, `BLOOD SUGAR` are ours alone across 49
                  bases - but that is a fact about today's titles, not a
                  property of the test. **If this variant ever runs a series
                  under one title**, the way Micro's superfoods run does, this
                  goes quiet: SUPERFOODS 7 against the SUPERFOODS 12 base
                  measures 5.4 and passes. Give each topic its own title, or
                  accept that the old hazard - last topic's poster animated with
                  this topic's base - is open again.

    IF YOU EVER PUT ONE BACK, MOVE IT, DO NOT COPY IT. `shutil.move` preserves
                  mtime, so a returned poster keeps its original timestamp and
                  sinks back into `grab.py`'s newest-first ordering instead of
                  surfacing at the front of it. That is why the session this was
                  taken from still found the right file on its next grab. Nobody
                  designed it and everybody now depends on it: restoring by
                  copying would stamp it now and put it at the head of the queue.

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
    3. THE JOIN   printed, never judged. |poster - base| just right of the
                  wave's start - the seam that shows if the subject does not
                  cover it. Useful to watch across posters of one topic; not a
                  pass or a fail, because it does not measure what it looks
                  like it measures.

                  It is dominated by how BRIGHT the scene and the wave are, not
                  by whether the cut is covered. `sleep` row 5 - a violet wave
                  emerging from behind a dimmed lamp, the best-integrated band
                  on the poster - reads 34. `firsthour` row 5 before it was
                  fixed, the wave's blunt end standing in open dark office air,
                  read 27. Seven apart, on opposite sides of the only thing the
                  test is for. And the success it seemed to have - that same
                  band going 27 to 83 when the lamp moved behind the man's hands
                  - is confounded: a lamp flare is bright, so the number rose
                  because the scene got brighter, not because the seam got
                  covered.

                  Left in because a large drop between two posters of one topic
                  still says something. Not left in as a verdict: a number that
                  fires on brightness while claiming to measure coverage is
                  worse than no number, because it makes a rejection feel
                  objective when it is not, and it already sent back a poster
                  that was right.

                  Two earlier attempts to measure the SUBJECT's position failed
                  the same way and are worth knowing about before a third is
                  written. Share-of-the-left-third passed a man standing
                  squarely in the middle at 35% against a 34% floor. The
                  centroid of the band's detail then flagged a band whose man
                  WAS at the far left, because his dark trousers are a large
                  flat area and the lamp and laptop behind him are not - detail
                  measures where a picture is busy, not where its subject is.

                  Three instruments, three failures, one lesson: where the
                  subject sits and whether it covers the seam are things the eye
                  reads instantly and pixel statistics read badly. LOOK AT THE
                  BAND. The four checks around this one are all things the eye
                  reads badly, which is why they are the ones that judge
    4. RIGHT      is the right third quiet? Anything drawn there survives past
                  the dial's disc and nudges the wave's tip
    5. CAPTIONS   can the ten captions be read? add_labels.py picks its ink from
                  the layout's light flag - 28 on a light band, 255 on a dark one
                  - so the ink is known exactly and the only question is what is
                  behind it. Two numbers, both direct rather than proxies: how
                  far the background's mean luminance is from the ink, and how
                  busy the background is.

                  A caption fails only when it misses BOTH, which took a second
                  pass to get right. `longer` row 2 put WALK DAILY on a sunlit
                  path of grass and stones: contrast 97 against variation 72,
                  and it was the one caption on that poster that could not be
                  read. But the noise number alone also rejected `sleep`'s
                  MORNING LIGHT at 169/70 and `firsthour`'s LONG EXHALES at
                  123/74, both perfectly legible. Enough contrast survives a
                  busy background and a quiet background carries weak contrast;
                  it is the pair that kills.

    6. FOOTER     is the strip under the last band empty? The day bar goes there
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
OURS_DIFF = 8.0             # mean |poster - base| over the title band, measured
                            # the same way engine/check_base.py --title-tol
                            # measures it, so the two files mean one thing by 8.
                            #
                            # 25 was the first guess and it was too generous, in
                            # a way worth keeping. Over 37 posters and 1332
                            # mismatched pairs: own base 0.0-3.2, a foreign base
                            # with a different title 38-88. So there is a wide
                            # empty gap and almost any number in it works - which
                            # is what made 25 feel safe - but 8 sits just above
                            # the legitimate ceiling instead of in the middle of
                            # the gap, and margin above 3.2 is the only margin
                            # that does anything. Nothing lives between 3.2 and
                            # 38 to be traded away for it.
                            #
                            # There is no value that separates every pair. The
                            # closest mismatch in the repository is 2.41, BELOW
                            # the worst legitimate match. See the header.
TITLE = (191, 392)          # where recolor_base.py draws the title, in a 2752
                            # tall poster. Scaled by HEIGHT, the way
                            # engine/check_base.py:92 scales it, not by the width
                            # factor everything else in this file uses. On a
                            # 1536x2752 poster the two are identical and this
                            # could never bite - which is exactly how a copy of a
                            # shared test waits: differing from the original in
                            # the one place the difference is invisible. Exercise
                            # found the same line in their own copy.
MARK_STD = 15.0
LIGHT_LUMA = 150.0          # over this a band reads light, under it dark
CAP_CONTRAST = 110.0        # ink to background mean, and how busy the background
CAP_NOISE = 65.0            # is. A caption fails only when it misses BOTH.
                            # Measured over three scene posters: the one that
                            # could not be read ran 97 against variation 72,
                            # while MORNING LIGHT reads fine at 169 against 70
                            # and LONG EXHALES at 123 against 74. Either number
                            # alone rejects captions that are perfectly legible
# No JOIN threshold. See the header: the number is printed and not judged,
# because it tracks the scene's brightness rather than the seam's coverage.


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

    ty0, ty1 = int(H * TITLE[0] / 2752), int(H * TITLE[1] / 2752)
    # Mean across channels, not max, because that is what
    # engine/check_base.py --title-tol measures and both files carry the number
    # 8. On the same poster max-across-channels reads 3.77 and mean reads 2.57,
    # so an 8 defined the first way is a 5.4 defined the second - two tools
    # measuring "the same thing" to the same threshold and disagreeing by half
    # of it. Same definition, same number, or the number has to change name.
    ours = float(np.abs(img[ty0:ty1] - base[ty0:ty1]).mean())
    print(f"{poster}  {W}x{H}")
    if ours >= OURS_DIFF:
        print(f"\n  THIS IS NOT A POSTER OF base_{a.topic}.png. The title band is "
              f"{ours:.1f} levels from the base (ours measures 0.0-3.2).\n"
              f"\n  It is almost certainly ANOTHER VARIANT'S, and there is nothing "
              f"wrong with it.\n  Do not regenerate it. Put it back in ~/Downloads "
              f"under its own name so whoever\n  it belongs to can still grab it, "
              f"then grab again once ours has arrived.\n"
              f"\n  Why nothing else caught it: grab.py takes the newest 1536x2752 "
              f"file in\n  Downloads and cannot know whose it is - that size "
              f"identifies a poster, not a\n  variant, and every variant generates "
              f"at exactly it. And every variant shares\n  this base geometry, so "
              f"check_base.py's wave test passes across variants by\n  construction. "
              f"`grab.py --keep` copies instead of moving and avoids the whole class.")
        sys.exit(1)
    print(f"  from our base (title band {ours:.1f} levels off, limit {OURS_DIFF:.0f})\n")
    print("  band  left mark      lightness         join(fyi)     right third")
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


        for ok, why in ((marks_ok, f"r{i+1} left circle still standing (std "
                                   f"{std:.1f}, want >{MARK_STD:.0f}) - the "
                                   f"photograph was painted around it, not over it"),
                        (light_ok, f"r{i+1} is {'light' if lu >= LIGHT_LUMA else 'dark'} "
                                   f"(luma {lu:.0f}) and the layout says "
                                   f"{'light' if want_light else 'dark'} - the caption "
                                   f"will be drawn in the wrong ink"),
                        (right_ok, f"r{i+1} right third is busier than the left "
                                   f"({100*right:.0f}% against {100*share:.0f}%)")):
            if not ok:
                bad.append(why)

        print(f"   {i+1}    {std:5.1f} {'ok ' if marks_ok else 'NO '}   "
              f"{lu:5.1f} {'light' if lu >= LIGHT_LUMA else 'dark ':<5} "
              f"{'ok ' if light_ok else 'NO '}   "
              f"{join:5.0f}      "
              f"{100*right:4.0f}% {'ok ' if right_ok else 'NO '}")

    # the captions, whose ink was chosen before anyone saw the photograph
    print()
    for i, row in enumerate(L["rows"]):
        c0 = int(row["cap_top"] * k)
        c1 = int((row["cap_top"] + row["cap_h"]) * k)
        ink = 28.0 if row["light"] else 255.0
        for side, cx in (("left ", L["anchor_l"]), ("right", L["anchor_r"])):
            m = (np.abs(xx - cx * k) < 190 * k) & (yy > c0) & (yy < c1)
            b = 0.299 * img[m][:, 0] + 0.587 * img[m][:, 1] + 0.114 * img[m][:, 2]
            con, noise = abs(float(b.mean()) - ink), float(b.std())
            # Both together, never either alone. High contrast survives a busy
            # background: sleep's MORNING LIGHT reads at 169 against variation
            # 70 and firsthour's LONG EXHALES at 123 against 74, and both are
            # perfectly legible. It is the pair that kills - 97 against 72.
            ok = con >= CAP_CONTRAST or noise <= CAP_NOISE
            if not ok:
                bad.append(f"r{i+1} {side.strip()} caption is not readable - "
                           f"contrast {con:.0f} (want {CAP_CONTRAST:.0f}) against a "
                           f"background varying by {noise:.0f} (want under "
                           f"{CAP_NOISE:.0f}). The bottom fifth of that band has to "
                           f"be quiet; the ink was chosen before the photograph "
                           f"existed. Contrast alone is fine at any noise, and a "
                           f"quiet background is fine at any contrast - it is the "
                           f"pair that kills")
                print(f"  caption r{i+1} {side}  contrast {con:5.0f}  noise {noise:5.0f}  NO")
            else:
                print(f"  caption r{i+1} {side}  contrast {con:5.0f}  noise {noise:5.0f}  ok")

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
