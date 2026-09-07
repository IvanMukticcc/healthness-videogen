#!/usr/bin/env python3
"""
check_base.py - has the generator left the waves alone?

The pipeline rests on one assumption: the liquid in a new poster sits exactly
where base_layer.png put it. Image models do not guarantee that, so this
measures it per row before any time is spent animating.

It compares against the base layer directly rather than detecting the wave
again. Re-detecting fails precisely where it matters: a dark green wave on a
dark navy row barely clears any threshold, and the check then reports drift that
is not there.

    python3 check_base.py new_poster.png
"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage


# The three authored assets live beside this script, not in whatever directory it
# is run from. A variant folder calls ../engine/ without keeping a copy of them,
# and a copy is how the tools drifted into three different generations at once.
_HERE = Path(__file__).resolve().parent


def align(a, b):
    """Best (dx, dy) that lines b up with a, by phase correlation on edges."""
    ga = ndimage.gaussian_gradient_magnitude(a, 1.5)
    gb = ndimage.gaussian_gradient_magnitude(b, 1.5)
    ga -= ga.mean(); gb -= gb.mean()
    win = np.outer(np.hanning(ga.shape[0]), np.hanning(ga.shape[1]))
    F = np.fft.rfft2(ga * win) * np.conj(np.fft.rfft2(gb * win))
    F /= np.maximum(np.abs(F), 1e-9)
    c = np.fft.irfft2(F, s=ga.shape)
    dy, dx = np.unravel_index(int(np.argmax(c)), c.shape)
    if dy > ga.shape[0] // 2: dy -= ga.shape[0]
    if dx > ga.shape[1] // 2: dx -= ga.shape[1]
    return float(dx), float(dy)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("poster")
    p.add_argument("-b", "--base", default=str(_HERE / "base_layer.png"))
    p.add_argument("-m", "--mask", default=str(_HERE / "ribbon_mask.png"))
    p.add_argument("--drift", type=float, default=2.0, help="pixels of drift still considered a fit")
    p.add_argument("--diff", type=float, default=14.0, help="allowed mean difference on the wave")
    args = p.parse_args()

    ref = np.array(Image.open(args.mask).convert("L")) > 127
    H, W = ref.shape
    base = np.array(Image.open(args.base).convert("RGB").resize((W, H), Image.LANCZOS)).astype(np.float32)
    img = Image.open(args.poster).convert("RGB")
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS)
    new = np.array(img).astype(np.float32)

    lab, n = ndimage.label(ref)
    order = sorted(range(1, n + 1), key=lambda i: np.where(lab == i)[0].min())
    print(f"{args.poster}  vs  {args.base}   ({W}x{H})")
    worst_d = worst_e = 0.0
    for k, i in enumerate(order, 1):
        band = lab == i
        ys, xs = np.where(band)
        # Only the middle stretch: the bowl and the organ are meant to cover the
        # two ends, so a difference there is the new artwork, not a moved wave.
        x0 = max(int(xs.min()), int(W * 0.30)); x1 = min(int(xs.max()), int(W * 0.75))
        y0, y1 = max(0, ys.min() - 12), min(H, ys.max() + 12)
        A = base[y0:y1, x0:x1].mean(axis=2)
        B = new[y0:y1, x0:x1].mean(axis=2)
        dx, dy = align(A, B)
        sub = band[y0:y1, x0:x1]
        err = float(np.abs(A - B)[sub].mean()) if sub.any() else 0.0
        worst_d = max(worst_d, float(np.hypot(dx, dy))); worst_e = max(worst_e, err)
        # A moved wave and a repainted one are not the same failure. Only the
        # first breaks the mask; the animator reads the wave's appearance from the
        # poster, so repainting is fine and used to raise a false alarm here.
        moved = abs(dx) > args.drift or abs(dy) > args.drift
        flag = "MOVED - regenerate" if moved else ("repainted, fine" if err > args.diff else "ok")
        print(f"  row {k}: shift {dx:+5.1f}, {dy:+5.1f} px   mean difference on the wave {err:5.1f}   -> {flag}")

    print("\nlabels:")
    bad = check_labels(new, base, ref.astype(np.float32))

    print()
    if bad:
        # Reported, not enforced. This test still misses short captions and trips
        # over the subtitle, and a check that cries wolf is worse than none. Look
        # at the poster: the labels belong under the bowl and under the organ.
        print(f"  ({bad} flagged - unreliable, check the poster by eye)")
    if worst_d <= args.drift:
        note = "" if worst_e <= args.diff else f", repainted by {worst_e:.0f} levels which the animator handles"
        print(f"waves are where the mask expects them (worst shift {worst_d:.1f} px{note}) - safe to animate")
    else:
        print(f"waves have MOVED (worst shift {worst_d:.1f} px) - regenerate;")
        print("the animation cannot correct a wave the generator put somewhere else")


def check_labels(new, base, mask, anchor_l=330, anchor_r_x=1190):
    """Is every label below the thing it names?

    The generator sometimes puts the food label above the bowl instead of under
    it. Nothing else in this pipeline looks at type, so it went out in a finished
    video before anyone noticed. Cheap to test: the label must sit lower than the
    circle it belongs to.
    """
    H, W, _ = new.shape
    m = max(2, int(W * 0.03))
    left = np.median(new[:, 1:1 + m, :], axis=1); right = np.median(new[:, W - 1 - m:W - 1, :], axis=1)
    t = (np.arange(W) / (W - 1))[None, :, None]
    bg = (left[:, None, :] * (1 - t) + right[:, None, :] * t).mean(axis=2)
    lum = new.mean(axis=2)
    ink = (np.abs(lum - bg) > 70) & ((lum > 205) | (lum < 75))
    ink &= ~ndimage.binary_dilation(mask > 0.3, np.ones((15, 15)))
    ink = ndimage.binary_opening(ink, np.ones((2, 2)))
    # Type only. A white ceramic bowl is as bright as a label, and the title is
    # brighter still; both were being read as the row's caption. A letter stroke
    # cannot contain a 21x21 square, a bowl can.
    ink &= ~ndimage.binary_opening(ink, np.ones((21, 21)))

    # Row stripes, so the search cannot wander into the neighbour's label - which
    # is what it did, and it then reported four perfectly good labels as wrong.
    marg = new[:, 4:16, :].mean(axis=1)
    ch = np.abs(np.diff(marg, axis=0)).max(axis=1)
    edges = [0] + [int(y) + 1 for y in np.where(ch > 25)[0]] + [H]
    edges = [e for i2, e in enumerate(edges) if i2 == 0 or e - edges[i2 - 1] > 60]

    lab, n = ndimage.label(mask > 0.5)
    order = sorted(range(1, n + 1), key=lambda i: np.where(lab == i)[0].min())
    bad = 0
    for k, i in enumerate(order, 1):
        ys, xs = np.where(lab == i)
        y_lo = next((e for e in reversed(edges) if e <= ys.min()), 0)
        y_hi = next((e for e in edges if e >= ys.max()), H)
        for name, cx in (("food", anchor_l), ("organ", anchor_r_x)):
            col = xs[np.argmin(np.abs(xs - cx))]
            cy = ys[xs == col].mean()
            zone = np.zeros((H, W), bool)
            # Near its own circle, not anywhere in the stripe: the title lives in
            # the first stripe too and would otherwise be taken for row 1's label.
            zone[max(y_lo, int(cy) - 300):min(y_hi, int(cy) + 300),
                 max(0, cx - 230):min(W, cx + 230)] = True
            words = ink & zone
            words = ndimage.binary_closing(words, np.ones((6, 40)))
            l2, n2 = ndimage.label(words)
            # A caption is wide and short. Berries in a bowl and stray highlights
            # are neither, and they were being mistaken for the label.
            best, area = None, 0
            for j, sl2 in enumerate(ndimage.find_objects(l2), start=1):
                if sl2 is None:
                    continue
                w2 = sl2[1].stop - sl2[1].start; h2 = sl2[0].stop - sl2[0].start
                if w2 < 110 or h2 > 95 or w2 < h2 * 1.8:
                    continue
                a = int((l2 == j).sum())
                if a > area:
                    best, area = j, a
            if best is None or area < 900:
                print(f"  row {k} {name:5}: no label found")
                bad += 1
                continue
            ly = np.where(l2 == best)[0].mean()
            ok = ly > cy
            if not ok:
                bad += 1
            print(f"  row {k} {name:5}: label at y={ly:6.0f}, circle centre y={cy:6.0f}"
                  f"   -> {'below, ok' if ok else 'ABOVE - wrong side'}")
    return bad


if __name__ == "__main__":
    main()
