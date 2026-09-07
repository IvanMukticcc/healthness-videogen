#!/usr/bin/env python3
"""
left_disc.py - the lifter's circle, in the colour of the wave that leaves it.

The food version puts the food in a bowl, and the bowl is why the row reads as
one thing pouring into another. This variant asked the generator for the same
circle and got three different answers in three days: an opaque white disc on a
dark row, a near-black one on a light row, and then - after the prompt said not
to draw a disc at all - a cut-out athlete standing on the row with nothing behind
him. A sentence the model interprets is the wrong place for a design element
that has to be identical on every row of every topic.

So the circle stops being something asked for. It is drawn into the base, in the
colour of that row's own wave, and the generator is told to put the athlete
inside it - the same trade as the guide marks, and as the waves themselves: what
must be identical is never regenerated.

The colour is read from the wave rather than named, so it follows the palette
automatically, and shaded a little darker so the wave's gloss still reads where
it crosses the disc. The liquid then leaves a circle of its own colour, which is
the bowl the whole design was copied from.

It goes into BOTH the base and its clean copy, and that matters: the animator
wipes whatever differs between the two, treating it as a guide mark. Identical
in both, the disc is design, and it survives.

    python3 left_disc.py --base ../INPUT/base_<topic>.png \
        -c base_<topic>_clean.png -l base_<topic>_layout.json
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ENGINE = Path(__file__).resolve().parent / ".." / ".." / "engine"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-b", "--base", required=True, help="base_<topic>.png, written in place")
    p.add_argument("-c", "--clean", required=True, help="its _clean copy, written in place")
    p.add_argument("-l", "--layout", required=True)
    p.add_argument("-m", "--mask", default=str(ENGINE / "ribbon_mask.png"))
    p.add_argument("--shade", type=float, default=0.85,
                   help="how much darker than the wave the disc sits. At 1.0 the "
                        "wave vanishes into it where the two overlap")
    p.add_argument("--feather", type=float, default=2.0)
    args = p.parse_args()

    base = np.asarray(Image.open(args.base).convert("RGB"), np.float32)
    clean = np.asarray(Image.open(args.clean).convert("RGB"), np.float32)
    mask = np.asarray(Image.open(args.mask).convert("L").resize(
        (base.shape[1], base.shape[0]), Image.LANCZOS)) > 128
    L = json.load(open(args.layout))
    H, W = base.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]

    for i, row in enumerate(L["rows"], 1):
        lo, hi = row["stripe"]
        band = np.zeros((H, W), bool)
        band[lo:hi] = True
        wave = mask & band
        if not wave.any():
            raise SystemExit(f"row {i}: no wave under the mask - wrong base?")
        # The wave's own colour, from the copy without the guide marks on it.
        col = np.median(clean[wave], axis=0) * args.shade

        cx, cy, r = float(L["anchor_l"]), float(row["cy"]), float(row["r"])
        a = np.clip((r - np.hypot(xx - cx, yy - cy)) / max(args.feather, 1e-3), 0, 1)[:, :, None]
        base = base * (1 - a) + col[None, None, :] * a
        clean = clean * (1 - a) + col[None, None, :] * a
        print(f"  r{i}: disc at ({cx:.0f}, {cy:.0f}) r={r:.0f} in "
              f"#{int(col[0]):02X}{int(col[1]):02X}{int(col[2]):02X}, "
              f"read from {int(wave.sum())} px of wave")

    Image.fromarray(np.clip(base, 0, 255).round().astype(np.uint8)).save(args.base)
    Image.fromarray(np.clip(clean, 0, 255).round().astype(np.uint8)).save(args.clean)
    print(f"wrote {args.base} and {args.clean}")


if __name__ == "__main__":
    main()
