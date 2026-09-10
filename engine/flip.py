#!/usr/bin/env python3
"""flip.py - one card, two faces: the first act turns over and the second is behind it.

Lived in `Macro/work/` until 10 September 2026, when Micro became the second
variant to turn a card over. That is the promotion rule this repository runs on
and it is written into `Macro/CLAUDE.md`: one variant flips, and if a second one
ever does, that is when it moves - the way `grab.py` and `caption_glass.py` got
here, after a second user appeared and not before. Nothing about it changed on
the way; a variant that wants a different turn passes different arguments.

A cut between the poster and the app screen would be two videos in a row. The
turn is what makes them one object - the thing you were looking at is the thing
holding the answer, and it was holding it the whole time.

HOW IT IS DONE, AND WHY NOT WITH A SCALE

The cheap version squeezes the frame horizontally to nothing and expands the
other one back. It reads as a shutter, not a card, because a real card turning
gets NEARER on one side and FURTHER on the other, and the eye reads that
perspective long before it reads the width.

So the four corners are rotated in three dimensions about the vertical axis and
projected through a pinhole at `--dolly` card-widths away, and the source face is
mapped onto the resulting quad with a homography. The near edge grows past the
card's own width; the far edge shrinks. At 90 degrees the card is edge-on and
one pixel wide, which is exactly the frame where the faces swap.

Three things that are not the geometry and matter as much:

  - THE BACK FACE IS MIRRORED. Act two is drawn on the back of the card, so
    before it is projected it is flipped left-to-right; the projection flips it
    back. Skip this and the turn is correct and the screen is inside out
  - LIGHT. A face turning away from the viewer loses light. Shading by the
    cosine of the angle is what stops it looking like a printed texture on a
    rotating rectangle
  - THE BACKDROP. Something has to be behind a card that is edge-on. It is the
    poster's own dark ground, so the turn happens inside the brand rather than
    over black

    ./flip.py a.png b.png --out-dir frames/ --frames 14
"""
import argparse
import math
import os

import numpy as np
from PIL import Image, ImageDraw

BACKDROP = (16, 31, 38)             # the base's dark ground, sampled from base_layer.png


def _coeffs(src, dst):
    """Homography for PIL, which maps OUTPUT pixels back to INPUT pixels."""
    m = []
    for (sx, sy), (dx, dy) in zip(src, dst):
        m.append([dx, dy, 1, 0, 0, 0, -sx * dx, -sx * dy])
        m.append([0, 0, 0, dx, dy, 1, -sy * dx, -sy * dy])
    A = np.array(m, dtype=float)
    b = np.array(src, dtype=float).reshape(8)
    return np.linalg.solve(A, b)


def project(W, H, angle, dolly=2.6, scale=1.0):
    """The card's four corners after turning `angle` degrees about its own spine."""
    a = math.radians(angle)
    f = dolly * W
    out = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = sx * W / 2 * scale, sy * H / 2 * scale
        xr, zr = x * math.cos(a), -x * math.sin(a)
        s = f / (f + zr)
        out.append((W / 2 + xr * s, H / 2 + y * s))
    return out


def frame(face_a, face_b, angle, dolly=2.6, lift=0.06, backdrop=BACKDROP,
          back_alpha=0.90, rim=True):
    """One frame of the turn. Under 90 degrees shows A, over it shows B.

    `backdrop` is a colour or an image. Given act one's live frames it is the
    scene the card is turning IN rather than a void it is turning over, and the
    card can then be glass: the back face goes down at `back_alpha` so the
    poster carries on moving through the pane.

    The front face stays opaque on purpose. It IS act one's last frame, so at
    zero degrees it lies exactly on the backdrop and the card is invisible -
    then it shears away from the live scene underneath as the turn starts, which
    reads as the surface peeling off rather than a new object appearing.
    """
    W, H = face_a.size
    front = angle < 90.0
    src = face_a if front else face_b.transpose(Image.FLIP_LEFT_RIGHT)

    # the card lifts towards the viewer through the turn and settles back
    k = math.sin(math.radians(angle))
    scale = 1.0 - lift * k

    quad = project(W, H, angle, dolly, scale)
    out = (backdrop.copy() if isinstance(backdrop, Image.Image)
           else Image.new("RGB", (W, H), backdrop))
    corners = [(0, 0), (W, 0), (W, H), (0, H)]

    # An edge-on card has no area to draw into; a degenerate homography is a
    # crash, so the frames within a degree of side-on are simply the backdrop.
    width = max(p[0] for p in quad) - min(p[0] for p in quad)
    if width < 2.0:
        return out

    warped = src.transform((W, H), Image.PERSPECTIVE, _coeffs(corners, quad),
                           Image.BICUBIC)
    # the mask is the quad, not the frame: outside it the backdrop shows through
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(quad, fill=255)
    a = 1.0 if front else back_alpha
    if a < 0.999:
        mask = Image.eval(mask, lambda v: int(v * a))

    # light falls off as the face turns away, and comes back as it faces us
    shade = 0.36 + 0.64 * abs(math.cos(math.radians(angle)))
    if shade < 0.999:
        warped = Image.eval(warped, lambda v: int(v * shade))
    out.paste(warped, (0, 0), mask)
    if rim:
        # A pane of glass is only visible at its edge. Without this the card
        # reads as a printed picture being rotated; with it, it is a sheet.
        edge = Image.new("L", (W, H), 0)
        ImageDraw.Draw(edge).polygon(quad, outline=int(150 * math.sin(
            math.radians(angle)) ** 0.5), width=max(2, W // 360))
        out.paste(Image.new("RGB", (W, H), (255, 255, 255)), (0, 0), edge)
    return out


def turn(face_a, face_b, n, dolly=2.6, lift=0.06, backdrops=None, back_alpha=0.90):
    """The whole turn as `n` frames, ease-in-out so it starts and ends at rest."""
    for i in range(n):
        u = (i + 1) / (n + 1)
        e = 0.5 - 0.5 * math.cos(math.pi * u)          # ease in and out
        bd = backdrops[i % len(backdrops)] if backdrops else BACKDROP
        yield frame(face_a, face_b, 180.0 * e, dolly, lift, bd, back_alpha)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--frames", type=int, default=14)
    ap.add_argument("--dolly", type=float, default=2.6)
    ap.add_argument("--lift", type=float, default=0.06)
    ap.add_argument("--start", type=int, default=0, help="first frame number")
    ap.add_argument("--backdrop-dir", help="act one's frames, in order, to turn in front of")
    ap.add_argument("--back-alpha", type=float, default=0.90)
    args = ap.parse_args()

    A = Image.open(args.a).convert("RGB")
    B = Image.open(args.b).convert("RGB").resize(A.size, Image.LANCZOS)
    bds = None
    if args.backdrop_dir:
        names = sorted(os.listdir(args.backdrop_dir))
        bds = [Image.open(os.path.join(args.backdrop_dir, n)).convert("RGB").resize(A.size)
               for n in names if n.lower().endswith(".png")]
        print(f"  turning in front of {len(bds)} live frames of act one")
    os.makedirs(args.out_dir, exist_ok=True)
    for i, im in enumerate(turn(A, B, args.frames, args.dolly, args.lift,
                                bds, args.back_alpha)):
        im.save(os.path.join(args.out_dir, f"f{args.start + i:05d}.png"))
    print(f"  {args.frames} frames of turn -> {args.out_dir}")


if __name__ == "__main__":
    main()
