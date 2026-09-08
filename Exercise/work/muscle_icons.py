#!/usr/bin/env python3
"""
muscle_icons.py - the muscle badges, all cut from one sphere.

The nine vitamin balls the sphere was recovered from were generated one at a time
for the food version, so no
two share a glyph size and vitamin C is not even a sphere - it came back as a
shield with the checkerboard still baked into its fringe. A row of badges that
disagree about how big a letter is reads as clip art. So the sphere is authored
once here and every badge is that same sphere with a label on it.

The sphere is not drawn from scratch: it is recovered from the eight real vitamin
balls, which is why it still has their gloss, their rim and their four specular
dots.

    median of the eight        the glyphs disagree, the ball does not
    grey closing               a disc-shaped max/min pass with a footprint wider
                               than a letter stroke removes every dark stroke and
                               leaves the bright ball, which gives the glyph mask
    multigrid diffusion        fills the masked letters back in from the ball
                               around them, coarse to fine so it actually settles

The colours are the three tiers in muscles.py - red prime mover, orange
synergist, blue stabiliser - and they are the same three the muscle takes on the
body. That is deliberate and load-bearing: a red ball lands saying CHEST and the
chest goes red in the same frame, and the viewer connects the two without being
told. The sphere's luminance is gradient-mapped onto each, which is the only way
to land on an exact colour: rotating the hue of a bright orange ball into red
gives a scarlet that is not #FF453A.

A muscle needs one badge per tier it is ever used at, so the files are named
`CHEST_p.png`, `CHEST_s.png`, `CHEST_t.png`. The same muscle really is a
different badge in a different row - the chest is what a bench press is for and
what a dip borrows.

The letters are white with a soft shadow of themselves under them, because hue
contrast - which is all the original orange balls had - is the first thing a
badge loses at the size it occupies in a vertical video.

    ../.venv/bin/python muscle_icons.py --all             # every muscle at every tier
    ../.venv/bin/python muscle_icons.py --one 'Soleus:s'  # one off-catalogue badge
    ../.venv/bin/python muscle_icons.py --sheet           # contact sheet of what exists

--rebuild does not run from here and is not meant to: the eight source balls are
the food version's and are not in this variant. The sphere it recovered is
committed as icons/_ball.png and every badge is cut from that.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

import muscles

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_BALLS = os.path.join(HERE, "..", "ASSETS", "Vitamini")   # read only, never written
# The badges live in icons/, which is the directory muscle_overlay.py reads. They
# were in ASSETS/Muscle/ until the three-folder layout landed, and this file was
# not moved with them: --one and --all wrote badges into a folder nothing loads,
# and --one crashed before it got there, because the missing _ball.png sent it to
# rebuild the sphere from vitamin balls that are not in this variant. Two files
# disagreeing about where the badges live is the same drift the engine exists to
# prevent, one folder down.
OUT = os.path.join(HERE, "icons")
TEMPLATE = os.path.join(OUT, "_ball.png")
FONT = "/Users/ivanmuktic/Library/Fonts/SF-Pro-Display-Heavy.otf"

# The eight vitamin balls that came back as spheres, in the folder next door.
# They are the only thing this reads from outside itself, and only with --rebuild:
# the recovered sphere is committed here, so a fresh clone does not need them.
SOURCE = ["A", "B12", "B2", "B6", "D", "E", "FOLATE", "K"]
SIZE = 1024

# The three tiers, from muscles.py rather than restated here - the body reads the
# same table, and a badge whose red is not the body's red breaks the one link the
# clip is built on.
FAMILY = muscles.TIER

# Where the sphere's own brightness lands on the tier colour. A hue rotation
# cannot do this: the template is a *bright* orange ball, and rotating it towards
# red gives a scarlet nowhere near #FF453A. Mapping its luminance onto a ramp
# built from the target puts the ball on the exact colour and keeps the gloss,
# the rim and the specular dots exactly where they were.
RAMP = [
    (0.00, ("mix", 0.50, (0, 0, 0))),      # rim
    (0.42, ("as-is", 0.0, None)),          # the family colour itself
    (0.72, ("mix", 0.42, (255, 255, 255))),
    (0.90, ("mix", 0.80, (255, 255, 255))),
    (1.00, ("mix", 1.00, (255, 255, 255))),  # specular
]

# White letters, with their own soft shadow underneath. The fitted law that made
# the original orange balls work was almost pure hue contrast, and hue contrast
# is the first thing a phone-sized badge loses. White holds on all three.
INK = (255, 255, 255)
INK_SHADOW = 0.42        # how far the letter darkens the ball beneath it

# The catalogue is not written out here: it is every muscle in muscles.py at
# every tier, because a table of exercises is free to ask for any of them and a
# missing badge stops a render. 28 muscles times 3 tiers is 84 small files.
def catalogue():
    return [(f"{k}_{t}", muscles.label(k), t)
            for k in sorted(muscles.MUSCLES) for t in ("p", "s", "t")]


# ---------------------------------------------------------------- the sphere

def _grey_closing(a, k):
    """Separable close. A disc footprint of this size is minutes; two 1-D passes
    each way is the same answer here, because the thing being removed is a letter
    stroke and a square kernel wider than the stroke removes it just as well."""
    for ax in (0, 1):
        a = ndimage.maximum_filter1d(a, k, axis=ax, mode="nearest")
    for ax in (0, 1):
        a = ndimage.minimum_filter1d(a, k, axis=ax, mode="nearest")
    return a


def _relax(v, m, iters):
    k = np.array([[0., 1, 0], [1, 0, 1], [0, 1, 0]], np.float32) / 4.0
    for _ in range(iters):
        v = np.where(m, ndimage.convolve(v, k, mode="nearest"), v)
    return v


def _inpaint(img, mask, levels=6):
    """Laplace fill, coarse to fine. Plain Jacobi at full resolution needs about
    (hole diameter)^2 sweeps to settle - the letters are 400px across, so it
    stops halfway and leaves a ghost of the glyph. Solving on a 32px picture
    first and carrying that down costs nothing and actually converges."""
    out = img.copy()
    for ch in range(img.shape[2]):
        pyr, v, m = [], out[:, :, ch].copy(), mask
        for _ in range(levels):
            pyr.append((v, m))
            v, m = v[::2, ::2], m[::2, ::2]
        v, m = pyr[-1]
        v = _relax(v.copy(), m, 600)
        for L in range(len(pyr) - 2, -1, -1):
            v0, m0 = pyr[L]
            up = np.array(Image.fromarray(v.astype(np.float32))
                          .resize((v0.shape[1], v0.shape[0]), Image.BILINEAR))
            cur = v0.copy()
            cur[m0] = up[m0]
            v = _relax(cur, m0, 300)
        out[:, :, ch] = v
    return out


def build_template(verbose=True):
    """Recover the blank sphere from the eight lettered ones."""
    stack = []
    for n in SOURCE:
        p = os.path.join(SRC_BALLS, f"vit_{n}.png")
        im = Image.open(p).convert("RGBA")
        a = np.array(im)[:, :, 3]
        ys, xs = np.nonzero(a > 10)
        im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        stack.append(np.array(im.resize((SIZE, SIZE), Image.LANCZOS)).astype(np.float32))
    st = np.stack(stack)

    med = np.median(st[:, :, :, :3], axis=0)
    dev = np.abs(st[:, :, :, :3] - med[None]).max(axis=3)
    glyph = np.stack([ndimage.binary_dilation(dev[i] > 18, np.ones((5, 5)))
                      for i in range(len(SOURCE))])
    w = (~glyph).astype(np.float32)[:, :, :, None]
    ball = (st[:, :, :, :3] * w).sum(axis=0) / np.maximum(w.sum(axis=0), 1e-6)

    c = (SIZE - 1) / 2.0
    R = SIZE / 2.0
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    rr = np.hypot(xx - c, yy - c)

    # Fill the void outside the ball with its nearest edge pixel, or the closing
    # erodes the transparent background inward and eats the rim.
    inside = rr < R * 0.985
    idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
    img = ball[idx[0], idx[1]]

    lum = img.mean(axis=2)
    dark = (_grey_closing(lum, 221) - lum) > 4.0
    dark = ndimage.binary_closing(dark, np.ones((9, 9)))
    dark = ndimage.binary_dilation(dark, np.ones((21, 21))) & (rr < R * 0.93)

    out = np.clip(_inpaint(img, dark), 0, 255)
    alpha = np.clip((R * 0.995 - rr) + 0.5, 0, 1) * 255
    rgba = np.dstack([out, alpha]).astype(np.uint8)
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(rgba).save(TEMPLATE)
    if verbose:
        print(f"  sphere recovered from {len(SOURCE)} balls, "
              f"{dark.sum()} px of letter filled back in -> {TEMPLATE}")
    return rgba


def template():
    if not os.path.exists(TEMPLATE):
        return build_template()
    return np.array(Image.open(TEMPLATE).convert("RGBA"))


# ---------------------------------------------------------------- the label

CAP = 0.46          # a single letter, as tall as the originals drew it
WIDE = 0.88         # the widest a line may run across the ball
CONDENSE = 0.86     # long words are squeezed rather than shrunk


def split_label(text):
    """Two lines if the word offers a place to break and one line would be tiny.
    'Beta-carotene' set on one line is 40% of the cap height it gets on two, and
    at badge size that is the difference between a word and a smudge."""
    if len(text) <= 8:
        return [text]
    for sep, keep in ((" ", ""), ("-", "-")):
        if sep in text[1:-1]:
            i = text.rfind(sep, 1, len(text) - 1)
            if 2 < i < len(text) - 2:
                return [text[:i] + keep, text[i + 1:]]
    return [text]


def _ink(lines, D):
    """The text as a D x D alpha plane, fitted to the ball."""
    long = max(len(s) for s in lines) > 6
    cond = CONDENSE if long else 1.0
    S = 3                     # supersample; PIL alone leaves the stems ragged
    lo, hi = 8, int(D * CAP * 1.4)
    gap = 0.10                # between the two lines, as a fraction of cap
    while hi - lo > 1:
        size = (lo + hi) // 2
        f = ImageFont.truetype(FONT, size)
        w = max(f.getbbox(s)[2] - f.getbbox(s)[0] for s in lines) * cond
        h = sum(f.getbbox(s)[3] - f.getbbox(s)[1] for s in lines) + gap * size * (len(lines) - 1)
        if w <= D * WIDE and h <= D * CAP * (1.0 if len(lines) == 1 else 1.55):
            lo = size
        else:
            hi = size
    f = ImageFont.truetype(FONT, lo * S)
    pad = D * S
    im = Image.new("L", (pad * 2, pad * 2), 0)
    d = ImageDraw.Draw(im)
    step = lo * S * (1.0 + gap)
    y = pad - step * (len(lines) - 1) / 2.0
    for s in lines:
        d.text((pad, y), s, font=f, fill=255, anchor="mm")
        y += step
    a = np.array(im)
    ys, xs = np.nonzero(a > 0)
    im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    im = im.resize((max(1, int(round(im.width * cond / S))), max(1, im.height // S)),
                   Image.LANCZOS)
    ink = np.zeros((D, D), np.float32)
    x0 = int(round(D / 2 - im.width / 2))
    y0 = int(round(D * 0.489 - im.height / 2))          # the originals sit 1% high
    if x0 < 0 or y0 < 0 or x0 + im.width > D or y0 + im.height > D:
        raise SystemExit(f"label {lines} does not fit the ball")
    ink[y0:y0 + im.height, x0:x0 + im.width] = np.array(im).astype(np.float32) / 255.0
    return ink


def draw_label(rgba, text, fam=None):
    """White letters, with a soft shadow of themselves underneath.

    The shadow is what makes white work everywhere on the ball: the top-left
    specular is white too, and a letter crossing it would otherwise disappear
    into it. Darkening the ball under the ink first gives the letter an edge no
    matter what it lands on."""
    D = rgba.shape[0]
    ink = _ink(split_label(text), D)
    out = rgba.astype(np.float32).copy()
    ball = out[:, :, :3]

    sh = Image.fromarray((ink * 255).astype(np.uint8), "L")
    sh = sh.filter(ImageFilter.GaussianBlur(D * 0.016))
    sh = np.roll(np.array(sh).astype(np.float32) / 255.0, int(round(D * 0.011)), axis=0)
    ball *= (1.0 - INK_SHADOW * np.clip(sh - ink, 0, 1)[:, :, None])

    out[:, :, :3] = ball * (1 - ink[:, :, None]) + np.float32(INK) * ink[:, :, None]
    return out


# ---------------------------------------------------------------- colour

def _mix(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def recolour(rgba, fam, lo=None, hi=None):
    """Gradient-map the sphere's luminance onto the family colour.

    Luminance, not value: the orange template's red channel is pinned near 255
    from the rim to the core, so V is almost flat across it and mapping on V
    gives a ball with no shading at all. Luminance runs 137 at the rim to 255 on
    the specular, which is the shading the sphere actually has."""
    target = FAMILY[fam]
    a = rgba.astype(np.float32)
    lum = a[:, :, 0] * 0.299 + a[:, :, 1] * 0.587 + a[:, :, 2] * 0.114
    inside = a[:, :, 3] > 200
    if lo is None:
        lo, hi = np.percentile(lum[inside], [1.0, 99.9])
    t = np.clip((lum - lo) / max(hi - lo, 1e-6), 0, 1)

    stops = [(pos, _mix(target, col, amt) if kind == "mix" else target)
             for pos, (kind, amt, col) in RAMP]
    xs = np.array([p for p, _ in stops], np.float32)
    ys = np.array([c for _, c in stops], np.float32)
    out = a.copy()
    for ch in range(3):
        out[:, :, ch] = np.interp(t, xs, ys[:, ch])
    return out


# ---------------------------------------------------------------- build

def make(name, label, fam, tpl, size=512):
    # Ball first, letter second: the letter is white and must not be mapped
    # along with the sphere it sits on.
    a = draw_label(recolour(tpl, fam), label)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    if size != im.width:
        im = im.resize((size, size), Image.LANCZOS)
    p = os.path.join(OUT, f"{name}.png")
    im.save(p)
    return p


def sheet(path):
    files = sorted(f for f in os.listdir(OUT) if f.endswith(".png") and not f.startswith("_"))
    cell, cols = 170, 12
    rows = (len(files) + cols - 1) // cols
    im = Image.new("RGB", (cols * cell, rows * cell), (18, 34, 56))
    for i, f in enumerate(files):
        b = Image.open(os.path.join(OUT, f)).convert("RGBA")
        b.thumbnail((cell - 12, cell - 12))
        im.paste(b, ((i % cols) * cell + 6, (i // cols) * cell + 6), b)
    im.save(path)
    print(f"  {len(files)} badges -> {path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--all", action="store_true", help="build the whole catalogue")
    p.add_argument("--one", action="append", default=[],
                   help="'Label:tier' where tier is p, s or t")
    p.add_argument("--rebuild", action="store_true", help="re-derive the sphere first")
    p.add_argument("--size", type=int, default=512)
    p.add_argument("--sheet", nargs="?", const=os.path.join(HERE, "muscle_sheet.png"))
    args = p.parse_args()

    os.makedirs(OUT, exist_ok=True)
    if (args.rebuild or not os.path.exists(TEMPLATE)) and not os.path.isdir(SRC_BALLS):
        sys.exit(f"no sphere at {TEMPLATE}, and it cannot be rebuilt here: the eight "
                 f"source balls are the food version's and are not in this variant. "
                 f"Restore icons/_ball.png rather than re-deriving it.")
    if args.rebuild or not os.path.exists(TEMPLATE):
        build_template()
    tpl = template()

    todo = catalogue() if args.all else []
    for spec in args.one:
        label, fam = spec.rsplit(":", 1)
        todo.append((f"{muscles.key(label)}_{fam}", label, fam))
    for name, label, fam in todo:
        make(name, label, fam, tpl, args.size)
    if todo:
        print(f"  {len(todo)} badges written to {OUT}")
    if args.sheet:
        sheet(args.sheet)
    if not todo and not args.sheet:
        p.print_help()


if __name__ == "__main__":
    main()
