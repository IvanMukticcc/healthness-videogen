#!/usr/bin/env python3
"""
audit.py - does anything move that should not?

The old check was to diff two frames and count the moving pixels that fall
outside the wave mask. With badges on the clip that check fires on every one of
them, and a number that is always wrong is a number nobody reads.

So the frames are chosen instead of filtered. The cues file says when each badge
lands; a badge is finished 0.52 s later (0.42 s of pop, and the ring is gone by
0.34 s). Any gap between one badge finishing and the next one starting is a
window where the only thing in the picture that is allowed to move is the
liquid - and inside such a window the original invariant holds exactly as it did
before the badges existed.

    python3 audit.py work/liver_silent.mp4

The spec comes off disk by default. render.sh already wrote <topic>_cues.txt and
<topic>_finale.txt, the topic is in the video's own filename, and the flags are
now the override for re-checking an old clip by hand rather than the only way to
get the check right. Measured on cholesterol_silent.mp4 on 9 September, the three
ways this used to be invoked:

    --cues and --finale    4 windows, 12 frame pairs      0 px   clean
    --cues only            5 windows, 15 pairs        60176 px   look at it
    neither                1 window,   3 pairs            0 px   clean

Omitting the spec does not widen the search, it thins it to a quarter - three
pairs at 0.05, 3.96 and 7.87, and 7.87 is after the finale has stopped moving.
The same word, clean, off a quarter of the looking, with nothing in the output
that told them apart. Hence both changes here: the default reads the files, and
the verdict carries the number of pairs it is based on.
"""
import argparse
import os
import re
import subprocess

import numpy as np
from PIL import Image
from scipy import ndimage

SETTLED = 0.52          # pop 0.42 + a little; the ring dies at 0.34
FINALE_SPAN = 1.00      # surge 0.34 + four rows of 0.05 stagger + the organ's
                        # 0.08 rise and 0.24 fall, rounded up. Measured on the
                        # first cut: nothing outside the wave moves after
                        # t_fin + 0.82


def frame(path, t, W, H):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path,
         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.int16)


def windows(cues, seconds, fade, need=0.45, finale=None, span=FINALE_SPAN):
    """Stretches where nothing is landing and nothing is fading.

    The finale is a hole cut in the last one. Everything else in this file is
    about catching motion nobody asked for; the finale is motion asked for by
    name - five organs lighting and a highlight running the length of every wave
    - and a window that contains it reports tens of thousands of pixels of
    exactly what was ordered. So it is excluded, and what remains after it is
    audited as usual: measured, that stretch is 0 px, which is the real check.
    A settled finale leaves the last frame alone.
    """
    out, prev = [], 0.0
    for t in list(cues) + [seconds + 99]:
        a, b = prev, min(t, seconds - fade)
        for lo, hi in _cut(a, b, finale, span):
            if hi - lo >= need:
                out.append((lo + 0.05, hi - 0.05))
        prev = max(prev, t + SETTLED)
    return out


def _cut(a, b, finale, span):
    """(a, b) minus the finale's own stretch."""
    if finale is None:
        return [(a, b)]
    f0, f1 = finale - 0.05, finale + span
    if f1 <= a or f0 >= b:
        return [(a, b)]
    return [(x, y) for x, y in ((a, min(b, f0)), (max(a, f1), b)) if y > x]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    # The mask is the engine's, like the animator that used it: a copy here is
    # how the same asset ended up at two generations at once.
    p.add_argument("--mask", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "..", "..", "engine", "ribbon_mask.png"))
    p.add_argument("--cues", help="the file flowanim.py --micro-cues wrote")
    p.add_argument("--finale", help="the file flowanim.py --finale-cue wrote, or the "
                                    "instant itself: its own stretch is cut out of the "
                                    "windows rather than reported as a fault")
    p.add_argument("--finale-span", type=float, default=FINALE_SPAN,
                   help="how long the finale is allowed to be moving for")
    p.add_argument("--fade", type=float, default=0.4)
    p.add_argument("--slack", type=int, default=15,
                   help="px of grace around the mask; the silhouette does ripple")
    p.add_argument("--tol", type=int, default=10, help="what counts as a changed pixel")
    args = p.parse_args()

    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height",
                            "-show_entries", "format=duration",
                            "-of", "csv=p=0", args.video],
                           capture_output=True, text=True, check=True).stdout.split()
    W, H = (int(v) for v in probe[0].split(",")[:2])
    seconds = float(probe[1])

    m = Image.open(args.mask).convert("L").resize((W, H), Image.LANCZOS)
    mask = np.array(m) > 128
    allowed = ndimage.binary_dilation(mask, np.ones((args.slack * 2 + 1,) * 2))

    # The topic is in the filename - cholesterol_micro.mp4, superfoods21_silent.mp4 -
    # and render.sh wrote the two files beside this script.
    topic = re.sub(r"_(micro|silent)$", "",
                   os.path.splitext(os.path.basename(args.video))[0])
    here = os.path.dirname(os.path.abspath(__file__))

    def beside(kind):
        f = os.path.join(here, f"{topic}_{kind}.txt")
        return f if os.path.exists(f) else None

    cues_src, cues_from = (args.cues, "--cues") if args.cues else (beside("cues"), "disk")
    fin_src, fin_from = (args.finale, "--finale") if args.finale else (beside("finale"), "disk")

    cues = []
    if cues_src:
        cues = sorted(float(c) for c in open(cues_src).read().strip().split(","))
    fin = None
    if fin_src:
        fin = float(open(fin_src).read().strip()
                    if os.path.exists(fin_src) else fin_src)

    if cues_from == "disk" and fin_from == "disk" and cues_src and fin_src:
        print(f"  cues and finale from {topic}_*.txt, what render.sh was given")
    if not cues:
        print(f"  NO CUES for '{topic}'. One window over the whole clip and three "
              f"frame pairs - the weakest form of this check, not the strict one. "
              f"Pass --cues, or run it where {topic}_cues.txt is.")
    wins = windows(cues, seconds, args.fade if cues else 0.0,
                   finale=fin, span=args.finale_span)
    if not wins:
        raise SystemExit("no quiet window - the badges never stop landing")
    if fin is not None:
        print(f"  finale at {fin:.2f}s: {fin - 0.05:.2f}-{fin + args.finale_span:.2f}s "
              f"is cut out of the windows, everything after it is not")

    print(f"{args.video}  {W}x{H}  {seconds:.2f}s")
    print(f"  {len(wins)} quiet windows: " +
          ", ".join(f"{a:.2f}-{b:.2f}" for a, b in wins))
    worst = 0
    pairs = 0
    step = 1.0 / 12                       # two frames apart at 24fps
    for a, b in wins:
        for t in np.linspace(a, max(a, b - step), 3):
            f0 = frame(args.video, t, W, H)
            f1 = frame(args.video, t + step, W, H)
            d = np.abs(f0 - f1).max(axis=2) > args.tol
            stray = d & ~allowed
            lab, n = ndimage.label(stray)
            if n:
                sz = ndimage.sum(stray, lab, range(1, n + 1))
                big = int(sz.max())
            else:
                big = 0
            worst = max(worst, int(stray.sum()))
            pairs += 1
            print(f"  t={t:5.2f}  moving {int(d.sum()):7d} px, "
                  f"{int(stray.sum()):5d} outside the wave in {n} clusters, largest {big}")
    # The pair count is the verdict's denominator. "clean (12 pairs)" and
    # "clean (3 pairs)" are the same word off four times the looking, and
    # without the number nothing in this output separates them - which is the
    # whole reason the thin invocation was able to pass for the strict one.
    print(f"  worst frame: {worst} px outside the wave "
          f"({'clean' if worst < 400 else 'look at it'}, {pairs} frame pairs "
          f"over {len(wins)} window{'s' if len(wins) != 1 else ''})")


if __name__ == "__main__":
    main()
