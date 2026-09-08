#!/usr/bin/env python3
"""
check.py - what has to be true before a clip is delivered.

Both other variants ship an `audit.py` that counts what moves outside the wave
mask in the gaps between badges. That test does not transfer here, and pretending
it did would have made it useless: this variant deliberately moves things outside
the mask all the time - five dials, five chips and a day bar that never stops -
so the honest version has to know where its own furniture is.

So it asks four questions instead, and the last two are the ones that actually
catch things:

  1. SOURCES     every hack on the poster has a study behind it in hacks.json,
                 and none of them is the placeholder. A number nobody can chase
                 does not go on a health brand's feed
  2. SETTLED     nothing outside the liquid is still moving on the last frames.
                 The last frame is the one a feed freezes on, and a clip caught
                 mid-sweep looks broken on every lap. The liquid itself never
                 stops - it is a seamless loop of flowing water and stopping it
                 would be the fault, not the fix
  3. STRAY       nothing moves outside the wave and outside this variant's own
                 elements. Type creeping, a poster artefact being advected, a
                 chip drawn where nothing planned one - all of it lands here.

                 **Judged on the largest cluster, not on the total.** x264 at
                 crf 16 rings along every high-contrast edge, and the ringing
                 comes and goes as the bitrate is reallocated around whatever
                 else is moving - measured here, the title's own edges change by
                 30 levels over frames 19-24, which is exactly while row 1's
                 shock ring is expanding two hundred pixels below it. That is
                 261 px of "movement" in 50 clusters of five pixels each, and no
                 tolerance separates it from motion because it is a real level
                 change. Its shape does: ringing is a scatter of one and two
                 pixel fragments along an edge, and a thing that has actually
                 moved is one blob. The exercise variant records the same finding
                 as 128 px on its reference cut
  4. LOOP        the audio joins end to end, because a click every eight seconds
                 is a click for as long as anybody watches

    python3 check.py day
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import dial
import day_overlay
import hacks


def frames(path, every=1):
    """The clip as float arrays, decoded once."""
    meta = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,nb_frames,r_frame_rate", "-of", "json", path],
        capture_output=True, text=True).stdout)["streams"][0]
    W, H = int(meta["width"]), int(meta["height"])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path,
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    n = len(raw) // (W * H)
    a = np.frombuffer(raw, np.uint8)[:n * W * H].reshape(n, H, W).astype(np.int16)
    num, den = (int(v) for v in meta["r_frame_rate"].split("/"))
    return a[::every], W, H, num / den


def own_regions(topic, W, H, hackspec, times):
    """Everything this variant draws that is not liquid, as one mask.

    Built from the same plan the render used rather than from a rectangle drawn
    by eye - if the chip moves, this moves with it, and a test that has to be
    kept in step by hand is a test that stops being true on a Tuesday.
    """
    layout = f"base_{topic}_layout.json"
    L = json.load(open(layout))
    k = W / 1536.0
    yy, xx = np.mgrid[0:H, 0:W]
    m = np.zeros((H, W), bool)

    pad = 22 * k                                   # the bloom, and the shock ring
    for row in L["rows"]:
        for cx in (L["anchor_l"], L["anchor_r"]):
            m |= np.hypot(xx - cx * k, yy - row["cy"] * k) < row["r"] * k + pad

    rows = hacks.resolve(hackspec)
    for c in day_overlay.chips(rows, layout, W, H, times, curves=None):
        # The shock ring reaches 1.30 of the chip's height and is drawn on a
        # canvas rounded out from there, so 1.35 was one pixel short of it and
        # this test spent its first run reporting the chip's own ring as a stray.
        r = c["h"] * 1.55
        m |= ((np.abs(xx - c["cx"]) < c["w"] / 2 + r) &
              (np.abs(yy - c["cy"]) < c["h"] / 2 + r))

    db = day_overlay.daybar(rows, W, H, times, 8.0)
    m |= ((yy > db["y"] + db["lab_dy"] - 40 * k) & (yy < db["y"] + 40 * k) &
          (xx > db["x0"] - 40 * k) & (xx < db["x1"] + 40 * k))
    return m


def main():
    p = argparse.ArgumentParser()
    p.add_argument("topic")
    p.add_argument("--clip", help="default ../OUTPUT/<today>/<topic>_biohack.mp4")
    p.add_argument("--hacks", help="the same spec render.sh was given")
    p.add_argument("--times", default="0.7,1.85,3.0,4.15,5.3")
    p.add_argument("--tol", type=int, default=8, help="levels of change that count")
    p.add_argument("--settle", type=float, default=0.5,
                   help="how much of the tail must be still, in seconds")
    p.add_argument("--cluster", type=int, default=40,
                   help="largest connected cluster allowed, for both the settled "
                        "test and the stray one. Ringing runs to 28 px on the "
                        "reference cut at 540 and 16 at 1080; anything that has "
                        "actually moved is thousands, and is one blob")
    a = p.parse_args()

    clip = a.clip or f"{a.topic}_silent.mp4"
    if not os.path.exists(clip):
        sys.exit(f"no {clip} - run ./render.sh first")
    bad = 0

    # ---- 1. sources
    spec = a.hacks
    if not spec:
        sys.exit("--hacks is the same spec render.sh was given; it is what says "
                 "which studies to check")
    rows = hacks.resolve(spec)
    print("sources")
    for h in rows:
        ok = "Placeholder" not in h["source"] and len(h["source"]) > 40
        print(f"  {'ok ' if ok else 'NO '}{h['name']:<20} {h['value']:>7}  "
              f"{h['source'][:64]}...")
        bad += not ok

    # ---- the picture
    fr, W, H, fps = frames(clip)
    d = np.abs(np.diff(fr.astype(np.int16), axis=0)).max(axis=0)
    mask = np.asarray(Image.open("../../engine/ribbon_mask.png").convert("L")
                      .resize((W, H), Image.LANCZOS)).astype(np.float32) / 255.0 > 0.5
    # Grown by four pixels before it is used as an alibi. The authored mask is
    # where the liquid *is*; the animator's --swell lets its silhouette breathe a
    # little past that, and the resize down to the render width moves the
    # boundary again. Undilated, this test reported 2370 px in 79 clusters, every
    # one of them a two-pixel fringe along a wave edge, and a test that cries
    # wolf on its own geometry is a test nobody runs twice.
    mask = ndimage.binary_dilation(mask, np.ones((9, 9)))
    times = [float(t) for t in a.times.split(",")]
    mine = own_regions(a.topic, W, H, spec, times)

    # ---- 2. settled  (after the mask: the liquid is exempt)
    n = int(round(a.settle * fps))
    tail = np.abs(np.diff(fr[-n - 1:].astype(np.int16), axis=0)).max(axis=0)
    tail = np.where(mask, 0, tail)                 # the liquid is meant to move
    moved = int((tail > a.tol).sum())
    lab, k = ndimage.label(tail > a.tol)
    # By cluster, not by total, and for a reason that was measured rather than
    # argued: the same clip checked at 540 reports 3 px in 3 clusters and at 1080
    # reports 196 px in 106 - 1.8 px each, which is x264 ringing along type that
    # got sharper, not something that started moving. A total makes the test
    # resolution-dependent and a per-megapixel total makes it arithmetic nobody
    # will believe. A cluster does not scale: ringing is one to five pixels at
    # any width, and a dial or a chip still moving is thousands.
    tails = ndimage.sum(tail > a.tol, lab, range(1, k + 1)) if k else np.zeros(0)
    tbig = int(tails.max()) if k else 0
    print(f"\nsettled  last {a.settle:.2f}s ({n} frames)")
    print(f"  {'ok ' if tbig <= a.cluster else 'NO '}largest cluster {tbig} px "
          f"(limit {a.cluster}); {moved} px in {k} clusters still moving on the "
          f"frames a feed freezes on")
    bad += tbig > a.cluster

    # ---- 3. stray
    stray = (d > a.tol) & ~mask & ~mine
    s = int(stray.sum())
    lab, k = ndimage.label(stray)
    sizes = ndimage.sum(stray, lab, range(1, k + 1)) if k else np.zeros(0)
    big = int(sizes.max()) if k else 0
    print(f"\nstray  outside the liquid and outside this variant's own elements")
    print(f"  {'ok ' if big <= a.cluster else 'NO '}largest cluster {big} px "
          f"(limit {a.cluster}); {s} px in {k} clusters altogether")
    for i in np.argsort(sizes)[::-1][:4]:
        ys, xs = np.where(lab == i + 1)
        print(f"     {int(sizes[i]):5d} px at x {xs.min()}-{xs.max()} "
              f"y {ys.min()}-{ys.max()}")
    bad += big > a.cluster

    # ---- 4. loop
    out = a.clip or f"../OUTPUT/{__import__('time').strftime('%d.%m')}/{a.topic}_biohack.mp4"
    print("\nloop")
    if os.path.exists(out) and out.endswith(".mp4"):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-f", "f32le",
                              "-ac", "1", "-ar", "48000", "-"],
                             capture_output=True).stdout
        x = np.frombuffer(raw, np.float32)
        if len(x):
            join = float(abs(x[0] - x[-1]))
            head = float(np.abs(x[:240]).max())
            print(f"  {'ok ' if join < 0.05 else 'NO '}audio joins end to end, "
                  f"|x[0]-x[-1]| = {join:.4f}  (first 5 ms peak {head:.3f})")
            bad += join >= 0.05
    else:
        print("  -- no finished cut to read; run ./render.sh")

    print(f"\n{'CLEAN' if not bad else str(bad) + ' PROBLEM(S)'} - "
          f"{clip} at {W}x{H}, {len(fr)} frames, {fps:.0f}fps")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
