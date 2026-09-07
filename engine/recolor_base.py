#!/usr/bin/env python3
"""
recolor_base.py - a new palette for the base layer, same geometry.

The prompt is not allowed to change the base layer, so a topic that wants other
colours needs another base layer rather than another instruction. Geometry is
untouched here, so ribbon_mask.png still fits: one mask covers every palette.

    python3 recolor_base.py --rows '#0E2A26,#E9F0DA' \
                            --waves '#8E1B34,#5A3320,#B01E3C,#D2461B,#D98C7A' \
                            -o base_bloodflow.png
"""
import argparse
import os
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage


# The three authored assets live beside this script, not in whatever directory it
# is run from. A variant folder calls ../engine/ without keeping a copy of them,
# and a copy is how the tools drifted into three different generations at once.
_HERE = Path(__file__).resolve().parent



def _work_path(args, suffix):
    """Where a derived file goes: beside --out unless --work says otherwise.

    The base image is the one file a person opens - it is attached to the prompt
    and nothing else - so INPUT holds it and only it. Its clean copy and its
    layout are working files that only the tools ever read, and they belong in
    work/ however the base is addressed.
    """
    stem = os.path.basename(args.out).rsplit(".", 1)[0]
    d = args.work if args.work else os.path.dirname(args.out)
    return os.path.join(d, stem + suffix)


def hexes(s):
    out = []
    for h in s.split(","):
        h = h.strip().lstrip("#")
        out.append(np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32))
    return out


def to_hsv(rgb):
    mx = rgb.max(axis=-1); mn = rgb.min(axis=-1)
    v = mx / 255.0
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0.0)
    return s, v


def paint(rgb, target, s_ref, v_ref, vibrance=1.0, contrast=1.0):
    """Put the wave on a new colour, keeping its gloss.

    Scaling brightness by a constant drags the specular highlight down with
    everything else and the wave comes out flat and chalky. A gamma curve moves
    the median onto the target while leaving white at white, so the shine
    survives and the shadows deepen instead of washing out.
    """
    import colorsys
    s, v = to_hsv(rgb)
    h_t, s_t, v_t = colorsys.rgb_to_hsv(*(target / 255.0))

    # Gamma on brightness only. A gamma on saturation drives it to 1 everywhere
    # for any vivid target, and the wave comes out as a flat vector shape with no
    # shading left in it. Saturation is scaled instead, which keeps its variation.
    gv = np.log(max(v_t, 1e-3)) / np.log(max(min(v_ref, 0.999), 1e-3))
    v2 = np.clip(np.power(np.clip(v, 0, 1), max(gv, 0.05)), 0, 1)
    s2 = np.clip(s * (s_t * vibrance / max(s_ref, 1e-3)), 0, 1)

    if contrast != 1.0:                       # push shadow and highlight apart
        v2 = np.clip(0.5 + (v2 - 0.5) * contrast, 0, 1)

    i6 = h_t * 6.0
    i = int(i6) % 6
    f = i6 - int(i6)
    p_ = v2 * (1 - s2); q = v2 * (1 - f * s2); t = v2 * (1 - (1 - f) * s2)
    r, g, b = {0: (v2, t, p_), 1: (q, v2, p_), 2: (p_, v2, t),
               3: (p_, q, v2), 4: (t, p_, v2), 5: (v2, p_, q)}[i]
    return np.stack([r, g, b], axis=-1) * 255.0


TITLE_FONT = "/Users/ivanmuktic/Library/Fonts/SF-Compact-Display-Black.otf"


def fit_font(path, text, target_w, start=200):
    """Largest size at which the line still fits the width we allow it."""
    size = start
    while size > 20:
        f = ImageFont.truetype(path, size)
        if f.getbbox(text)[2] - f.getbbox(text)[0] <= target_w:
            return f
        size -= 2
    return ImageFont.truetype(path, 20)


def draw_title(img, title, subtitle, top, bottom, width_frac=0.72, gap=16):
    """Put the title into the base itself, at a fixed height.

    Asked for in the prompt, the title lands wherever the generator feels like -
    often within the top tenth, where a phone's status bar and the feed's own
    crop take it away. Drawn here it is in the same place every time, below the
    safe line, and the generator has nothing to place at all.
    """
    W, H = img.size
    d = ImageDraw.Draw(img)
    avail = int(W * width_frac)
    ft = fit_font(TITLE_FONT, title, avail)
    fs = fit_font(TITLE_FONT, subtitle, avail, start=110)
    bt = ft.getbbox(title); bs = fs.getbbox(subtitle)
    ht = bt[3] - bt[1]; hs = bs[3] - bs[1]
    block = ht + gap + hs
    y = top + max(0, (bottom - top - block) // 2)
    d.text(((W - (bt[2] - bt[0])) // 2 - bt[0], y - bt[1]), title, font=ft, fill=(255, 255, 255))
    d.text(((W - (bs[2] - bs[0])) // 2 - bs[0], y + ht + gap - bs[1]), subtitle, font=fs, fill=(255, 255, 255))
    return ht, hs, y, y + block


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-b", "--base", default=str(_HERE / "base_layer.png"))
    p.add_argument("-m", "--mask", default=str(_HERE / "ribbon_mask.png"))
    p.add_argument("-l", "--layer", default=str(_HERE / "ribbon_rgba.png"))
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--work", default=None,
                   help="where the two working files go. The base itself is the only "
                        "thing a person ever opens, so it goes to INPUT on its own and "
                        "its clean copy and its layout stay behind in work/")
    p.add_argument("--rows", required=True, help="two colours: dark rows, light rows")
    p.add_argument("--waves", required=True, help="five colours, top to bottom")
    p.add_argument("--title", help="drawn into the base at a fixed height")
    p.add_argument("--subtitle", default="")
    p.add_argument("--title-top", type=float, default=0.05,
                   help="floor for the title block, fraction of height - a phone status bar sits above this")
    p.add_argument("--anchors", type=int, default=1, help="draw the circles the generator aims at")
    p.add_argument("--anchor-r", type=int, default=150, help="largest circle radius; shrinks to fit the row")
    p.add_argument("--caption-h", type=int, default=78)
    p.add_argument("--caption-w", type=int, default=380)
    p.add_argument("--caption-gap", type=int, default=16)
    p.add_argument("--gap", type=int, default=20, help="the one gap: band to circle to caption to band")
    p.add_argument("--anchor-l", type=int, default=250)
    p.add_argument("--anchor-r-x", dest="anchor_r_x", type=int, default=1270)
    p.add_argument("--vibrance", type=float, default=1.15, help="saturation push")
    p.add_argument("--contrast", type=float, default=1.12, help="shadow-to-highlight spread")
    args = p.parse_args()

    arr = np.array(Image.open(args.base).convert("RGB")).astype(np.float32)
    H, W, _ = arr.shape
    mask = np.array(Image.open(args.mask).convert("L").resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    # Down to the faintest part of the tail. Cutting at 0.15 leaves the tip
    # holding the colour of whatever topic came before.
    liquid = mask > 0.02

    rows = hexes(args.rows); waves = hexes(args.waves)
    if len(rows) != 2 or len(waves) != 5:
        raise SystemExit("need two row colours and five wave colours")

    # row stripes, from the left margin where nothing is ever drawn
    marg = arr[:, 4:16, :].mean(axis=1)
    ch = np.abs(np.diff(marg, axis=0)).max(axis=1)
    edges = [0] + [int(y) + 1 for y in np.where(ch > 25)[0]] + [H]
    edges = [e for i, e in enumerate(edges) if i == 0 or e - edges[i - 1] > 60]
    print(f"row stripes at {edges}")

    out = arr.copy()
    old_bg = np.zeros((H, W, 3), np.float32)      # what each stripe used to be
    # backgrounds first, everywhere the liquid is not
    for k in range(len(edges) - 1):
        a, b = edges[k], edges[k + 1]
        band = np.zeros((H, W), bool); band[a:b] = True
        bgpix = band & ~ndimage.binary_dilation(liquid, np.ones((9, 9)))
        if bgpix.sum() < 100:
            continue
        med = np.median(arr[bgpix], axis=0)
        old_bg[band] = med
        target = rows[0] if med.mean() < 128 else rows[1]
        # keep the stripe's own texture and gradient by moving the deviations across
        out[band] = np.clip(arr[band] - med + target, 0, 255)
        print(f"  stripe {k + 1}: {tuple(int(v) for v in med)} -> {tuple(int(v) for v in target)}")

    # then the waves, each on its own new colour
    lab, n = ndimage.label(liquid)
    order = sorted(range(1, n + 1), key=lambda i: np.where(lab == i)[0].min())
    layer = np.array(Image.open(args.layer).convert("RGBA").resize((W, H), Image.LANCZOS)).astype(np.float32)
    for k, i in enumerate(order[:5]):
        sel = lab == i
        a = (layer[:, :, 3][sel] / 255.0)[:, None]
        # Lift the wave off the colour it was composited onto. The tail fades into
        # the old stripe, so its pixels are part wave and part old background;
        # recolouring that mixture leaves a muddy tip in the previous topic's hue.
        pure = layer[:, :, :3][sel]          # already un-composited, nothing to undo
        s_, v_ = to_hsv(pure)
        core = mask[sel] > 0.6
        ref_s = float(np.median(s_[core])) if core.sum() > 50 else float(np.median(s_))
        ref_v = float(np.median(v_[core])) if core.sum() > 50 else float(np.median(v_))
        painted = paint(pure, waves[k], ref_s, ref_v, args.vibrance, args.contrast)
        out[sel] = out[sel] * (1 - a) + painted * a
        got = np.median(painted, axis=0)
        print(f"  wave {k + 1}: asked {tuple(int(x) for x in waves[k])}, "
              f"got median {tuple(int(x) for x in got)}")

    rng = np.random.default_rng(3)
    out = out + rng.uniform(-0.5, 0.5, out.shape)        # the gamma curve above
    # The title goes on before the clean copy is taken. Taken first, the clean
    # base has no title, and the animator - which restores from it wherever the
    # poster still matches the anchored base - then wipes the heading out.
    img_out = Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8))
    if args.title:
        # Centred in the empty space above the first row rather than pinned to a
        # band. The space runs from the top of the poster to the top of the first
        # guide circle, which is where the bowl and the organ begin.
        first = min(np.where(lab == i)[0].min() for i in order[:5])
        last = max(np.where(lab == i)[0].max() for i in order[:5])
        circ_top = int((np.where(lab == order[0])[0].min() + np.where(lab == order[0])[0].max()) / 2
                       - args.anchor_r)
        top = int(H * args.title_top)
        ht, hs, y0t, y1t = draw_title(img_out, args.title, args.subtitle, top, circ_top)
        print(f"  title drawn at y {y0t}-{y1t} ({y0t/H*100:.1f}%-{y1t/H*100:.1f}% of height), "
              f"centred in the gap above the circles (which start at y {circ_top})")

    out = np.array(img_out).astype(np.float32)

    clean_out = out.copy()          # the same base without the guide circles
    layout = {"anchor_l": args.anchor_l, "anchor_r": args.anchor_r_x, "rows": []}
    if args.anchors:
        # A circle for the bowl and a bar for the caption. Without a marked place
        # for the text the generator fills the whole row with the bowl, and a
        # caption added afterwards lands on top of it. Same trick as the circles:
        # the model leaves alone what it can see.
        yy, xx = np.mgrid[0:H, 0:W]
        cap_h, cap_gap, top_pad = args.caption_h, args.caption_gap, 12

        # Every gap the same, by construction. The row is a band of known height:
        # gap, circle, gap, caption, gap. Solving that gives the radius and where
        # the circle sits, and make_base places the wave so its left tip lands on
        # the circle's centre. Nudging any of the three by hand is what left the
        # last row 122px taller than the rest with the caption adrift.
        inner = [edges[i + 1] - edges[i] for i in range(1, len(edges) - 2)]
        band_h = float(np.median(inner)) if inner else (H / 6.0)
        g = float(args.gap)
        r_all = (band_h - cap_h - 3 * g) / 2.0

        for k, i in enumerate(order[:5]):
            sel = lab == i
            ys, xs_ = np.where(sel)
            lo = next((e for e in reversed(edges) if e <= ys.min()), 0)
            if lo == 0:
                lo = int(next(e for e in edges if e > ys.min()) - band_h)
            hi = lo + band_h
            cy = lo + g + r_all
            cap_top = int(cy + r_all + g)
            r = r_all

            bgm = np.median(out[np.zeros((H, W), bool) | (np.arange(H)[:, None] >= lo) &
                                (np.arange(H)[:, None] < hi) & ~ndimage.binary_dilation(sel, np.ones((9, 9)))], axis=0)
            shift = 26 if bgm.mean() < 128 else -22
            tint = np.clip(bgm + shift, 0, 255)[None, None, :]

            row = {"cy": cy, "r": r, "cap_top": cap_top, "cap_h": cap_h,
                   "stripe": [int(lo), int(hi)], "light": bool(bgm.mean() >= 128)}
            layout["rows"].append(row)

            for cx in (args.anchor_l, args.anchor_r_x):
                d = np.hypot(xx - cx, yy - cy)
                al = np.clip((r - d) / 14.0, 0, 1)[:, :, None]
                out = out * (1 - al) + tint * al
                # the caption bar: a rounded slab under the circle
                hw, hh = args.caption_w / 2.0, cap_h / 2.0
                ccy = cap_top + hh
                dx = np.clip(np.abs(xx - cx) - (hw - hh), 0, None)
                db = np.hypot(dx, yy - ccy)
                ab = np.clip((hh - db) / 10.0, 0, 1)[:, :, None]
                out = out * (1 - ab) + tint * ab
        print(f"  circles r={layout['rows'][0]['r']:.0f} at x={args.anchor_l} and x={args.anchor_r_x}, "
              f"caption bars {args.caption_w}x{cap_h}")

    rng = np.random.default_rng(3)
    dith = lambda a: np.clip(a + rng.uniform(-0.5, 0.5, a.shape), 0, 255).round().astype(np.uint8)
    Image.fromarray(dith(out)).save(args.out)
    print(f"wrote {args.out}")
    if args.anchors:
        # The circles are a message to the generator, not part of the design. It
        # never covers them completely, and what is left reads as a translucent
        # second shape lying under the liquid. The animator needs this copy to
        # paint them out.
        clean_path = _work_path(args, "_clean.png")
        Image.fromarray(dith(clean_out)).save(clean_path)
        print(f"wrote {clean_path} (no circles - this is the one flowanim.py wants)")
    lay = _work_path(args, "_layout.json")
    json.dump(layout, open(lay, "w"), indent=1)
    print(f"wrote {lay} (the geometry, so the other tools do not have to guess)")


if __name__ == "__main__":
    main()
