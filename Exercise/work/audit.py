#!/usr/bin/env python3
"""
audit.py - does anything move that should not?

The old check was to diff two frames and count the moving pixels that fall
outside the wave mask. With badges on the clip that check fires on every one of
them, and a number that is always wrong is a number nobody reads.

So the frames are chosen instead of filtered. The cues file says when each badge
lands; a badge is finished 0.52 s later, and so is the muscle it lit - 0.42 s of
pop, the ring gone by 0.34 s, the body's flash settled by 0.47 s. Any gap between
one landing finishing and the next one starting is a window where the only thing
in the picture that is allowed to move is the liquid, and inside such a window
the original invariant holds exactly as it did before any of this existed.

The bodies themselves never move, so they need no window: they are outside the
mask and perfectly still, which is what the check is looking for.

    ../.venv/bin/python audit.py push_silent.mp4 --cues push_cues.txt
"""
import argparse
import pathlib
import subprocess

import numpy as np
from PIL import Image
from scipy import ndimage

SETTLED = 0.52          # pop 0.42 + a little; the ring dies at 0.34,
                        # the body's flash at 0.13 + 0.34


def frame(path, t, W, H):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path,
         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.int16)


def windows(cues, seconds, fade, need=0.45):
    """Stretches where nothing is landing and nothing is fading."""
    out, prev = [], 0.0
    for t in list(cues) + [seconds + 99]:
        a, b = prev, min(t, seconds - fade)
        if b - a >= need:
            out.append((a + 0.05, b - 0.05))
        prev = max(prev, t + SETTLED)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--mask",
                   default=str(pathlib.Path(__file__).resolve().parent
                               / ".." / ".." / "engine" / "ribbon_mask.png"),
                   help="the authored mask, which lives in the engine rather than here")
    p.add_argument("--cues", help="the file flowanim.py --muscle-cues wrote")
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

    cues = []
    if args.cues:
        cues = sorted(float(c) for c in open(args.cues).read().strip().split(","))
    wins = windows(cues, seconds, args.fade if cues else 0.0)
    if not wins:
        raise SystemExit("no quiet window - the badges never stop landing")

    print(f"{args.video}  {W}x{H}  {seconds:.2f}s")
    print(f"  {len(wins)} quiet windows: " +
          ", ".join(f"{a:.2f}-{b:.2f}" for a, b in wins))
    worst = 0
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
            print(f"  t={t:5.2f}  moving {int(d.sum()):7d} px, "
                  f"{int(stray.sum()):5d} outside the wave in {n} clusters, largest {big}")
    print(f"  worst frame: {worst} px outside the wave "
          f"({'clean' if worst < 400 else 'look at it'})")


if __name__ == "__main__":
    main()
