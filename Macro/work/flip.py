#!/usr/bin/env python3
"""flip.py - one card, two faces: act one turns over and act two is behind it.

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


def frame(face_a, face_b, angle, dolly=2.6, lift=0.06, backdrop=BACKDROP):
    """One frame of the turn. Under 90 degrees shows A, over it shows B."""
    W, H = face_a.size
    front = angle < 90.0
    src = face_a if front else face_b.transpose(Image.FLIP_LEFT_RIGHT)

    # the card lifts towards the viewer through the turn and settles back
    k = math.sin(math.radians(angle))
    scale = 1.0 - lift * k

    quad = project(W, H, angle, dolly, scale)
    out = Image.new("RGB", (W, H), backdrop)
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

    # light falls off as the face turns away, and comes back as it faces us
    shade = 0.36 + 0.64 * abs(math.cos(math.radians(angle)))
    if shade < 0.999:
        warped = Image.eval(warped, lambda v: int(v * shade))
    out.paste(warped, (0, 0), mask)
    return out


def turn(face_a, face_b, n, dolly=2.6, lift=0.06):
    """The whole turn as `n` frames, ease-in-out so it starts and ends at rest."""
    for i in range(n):
        u = (i + 1) / (n + 1)
        e = 0.5 - 0.5 * math.cos(math.pi * u)          # ease in and out
        yield frame(face_a, face_b, 180.0 * e, dolly, lift)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--frames", type=int, default=14)
    ap.add_argument("--dolly", type=float, default=2.6)
    ap.add_argument("--lift", type=float, default=0.06)
    ap.add_argument("--start", type=int, default=0, help="first frame number")
    args = ap.parse_args()

    A = Image.open(args.a).convert("RGB")
    B = Image.open(args.b).convert("RGB").resize(A.size, Image.LANCZOS)
    os.makedirs(args.out_dir, exist_ok=True)
    for i, im in enumerate(turn(A, B, args.frames, args.dolly, args.lift)):
        im.save(os.path.join(args.out_dir, f"f{args.start + i:05d}.png"))
    print(f"  {args.frames} frames of turn -> {args.out_dir}")


if __name__ == "__main__":
    main()
