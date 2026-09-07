#!/usr/bin/env python3
"""
make_base.py - build a reusable liquid base layer from a generated poster.

One wave is chosen, thickened where it runs too thin, and stamped into all five
rows, each recoloured to the colour that row already had. The five ribbons then
match to the pixel rather than to 92%, so a single authored mask serves every
row and every future poster.

    python3 make_base.py poster.jpeg -o base_layer.png -m ribbon_mask.png
"""
import argparse
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def row_background(arr):
    """Background of every scanline, as a ramp between the two margins."""
    H, W, _ = arr.shape
    m = max(2, int(W * 0.03))
    left = np.median(arr[:, 1:1 + m, :], axis=1)
    right = np.median(arr[:, W - 1 - m:W - 1, :], axis=1)
    t = (np.arange(W) / (W - 1))[None, :, None]
    return left[:, None, :] * (1 - t) + right[:, None, :] * t


def find_ribbons(arr, tol, min_area):
    bg = row_background(arr)
    diff = np.abs(arr - bg).max(axis=2)
    fg = ndimage.binary_closing(diff > tol, np.ones((5, 5)))
    lab, n = ndimage.label(fg)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl is None:
            continue
        comp = lab == i
        if comp.sum() < min_area:
            continue
        out.append(comp)
    out.sort(key=lambda c: np.where(c)[0].min())
    return out, bg, diff


def profile(comp, sigma=6.0):
    """Centre line and half thickness per column, over the ribbon's own span."""
    ys, xs = np.where(comp)
    x0, x1 = xs.min(), xs.max()
    cols = np.arange(x0, x1 + 1)
    top = np.zeros(len(cols)); bot = np.zeros(len(cols))
    for j, x in enumerate(cols):
        c = np.where(comp[:, x])[0]
        top[j], bot[j] = (c.min(), c.max()) if len(c) else (np.nan, np.nan)
    ok = ~np.isnan(top)
    top = np.interp(cols, cols[ok], top[ok]); bot = np.interp(cols, cols[ok], bot[ok])
    # A short box filter leaves per-column jitter in the traced edge, and that
    # jitter is what makes the finished wave look bumpy next to the original.
    sm = lambda v: ndimage.gaussian_filter1d(v, sigma, mode="nearest")
    return cols, sm(top), sm(bot)


def taper_tail(L, length, fade):
    """Thin the wave to a point at the organ end, and dissolve the last of it.

    A blunt tail has to be hidden by whatever organ the generator draws, and the
    organs vary in size and height, so some of it always shows above or below
    them. Trimming the wave instead risks a gap when an organ lands further
    right. A tail that narrows to a point and fades out reads as the leading edge
    of a pour and survives either placement.
    """
    t = np.zeros(L, np.float32); a = np.ones(L, np.float32)
    n = min(L - 2, max(8, length))
    r = np.linspace(1, 0, n)                            # 1 where the tail begins,
    t[-n:] = (r * r * (3 - 2 * r))                      # 0 at the very tip
    t[:-n] = 1.0
    k = min(L - 2, max(4, fade))
    a[-k:] = np.linspace(1.0, 0.0, k) ** 0.7
    return t, a


def thicken(cols, top, bot, floor_frac, tip_frac):
    """Raise the thinnest stretches to a floor, keeping a rounded tip.

    The generated wave tapers to three pixels at its end. Anything that thin
    tears the moment the silhouette is deformed, and it was the source of the
    stray fragments in the previous build.
    """
    L = len(cols)
    half = (bot - top) * 0.5
    centre = (top + bot) * 0.5
    span = half.max() * 2
    floor = np.full(L, floor_frac * span)
    tip = max(6, int(L * 0.035))
    floor[-tip:] = np.linspace(floor[-1], tip_frac * span, tip)
    nose = max(6, int(L * 0.02))
    floor[:nose] = np.linspace(tip_frac * span, floor[0], nose)
    # Smoothed after the floor and the taper, not before: taking a maximum against
    # a floor puts a corner wherever the two cross, and smoothing earlier cannot
    # remove a corner that does not exist yet.
    new_half = ndimage.gaussian_filter1d(np.maximum(half, floor), 9.0, mode="nearest")
    centre = ndimage.gaussian_filter1d(centre, 5.0, mode="nearest")
    return centre, half, new_half


def cross_section(arr, comp, K=256, sigma=6.0):
    """Read a ribbon into its own (across, along) grid, colours and all."""
    cols, top, bot = profile(comp, sigma)
    v = np.linspace(0, 1, K)[:, None]
    ys = top[None, :] + v * (bot - top)[None, :]
    xs = np.broadcast_to(cols[None, :].astype(float), ys.shape)
    tex = np.stack([ndimage.map_coordinates(arr[:, :, c], [ys, xs], order=3, mode="nearest")
                    for c in range(3)], axis=2)
    return cols, top, bot, tex


def main():
    p = argparse.ArgumentParser()
    p.add_argument("poster")
    p.add_argument("-o", "--out", default="base_layer.png")
    p.add_argument("-m", "--mask", default="ribbon_mask.png")
    p.add_argument("-l", "--layer", default="ribbon_rgba.png")
    p.add_argument("--tol", type=int, default=36)
    p.add_argument("--min-area", type=int, default=20000)
    p.add_argument("--floor", type=float, default=0.12, help="thinnest allowed, share of the wave's own height")
    p.add_argument("--tip", type=float, default=0.06, help="how far the rounded ends taper")
    p.add_argument("--sharpen", type=float, default=0.18, help="unsharp amount after downsampling")
    p.add_argument("--rows-top", type=float, default=0.150)
    p.add_argument("--rows-bottom", type=float, default=0.900)
    p.add_argument("--wave-pos", type=float, default=None,
                   help="place the wave by its bounding box, as a fraction of the band. "
                        "Left unset the tips are placed on the circle centres instead, "
                        "which is what the layout actually wants")
    p.add_argument("--level", type=float, default=1.0,
                   help="straighten the tip-to-tip rise: 1 puts both ends at the same height, 0 leaves the source's slope")
    p.add_argument("--tip-drop", type=float, default=0.0,
                   help="pixels to sink the tips below the circle centre")
    p.add_argument("--gap", type=int, default=20, help="the row gap recolor_base.py uses; only read here to find the circle centre")
    p.add_argument("--caption-h", type=int, default=78, help="likewise, the caption bar height")
    p.add_argument("--logo-y", type=float, default=0.955)
    p.add_argument("--ss", type=int, default=2, help="supersampling factor")
    p.add_argument("--smooth", type=float, default=0.9, help="blur the source to kill JPEG blocking")
    p.add_argument("--span", default="0.15,0.84",
                   help="where the wave starts and ends, as fractions of the width")
    p.add_argument("--taper", type=int, default=260, help="length over which the tail narrows to a point")
    p.add_argument("--fade", type=int, default=150, help="length over which the tip dissolves")
    p.add_argument("--source", type=int, default=0, help="which row to copy (0 = pick the fullest)")
    args = p.parse_args()

    img = Image.open(args.poster).convert("RGB")
    W0, H0 = img.size
    if args.ss > 1:
        # Everything below resamples the wave twice, and resampling at output
        # size is what leaves stair-stepped edges. Doing it at double size and
        # shrinking at the end averages those away instead.
        img = img.resize((W0 * args.ss, H0 * args.ss), Image.LANCZOS)
    arr = np.array(img).astype(np.float32)
    if args.smooth > 0:
        # The source is a JPEG, so its smooth gradients carry 8x8 block edges.
        # They survive every resampling step below and show up as stepping when
        # the base is zoomed. A gentle blur removes them well under the level
        # where the gloss detail starts to go.
        arr = np.stack([ndimage.gaussian_filter(arr[:, :, c], args.smooth) for c in range(3)], axis=2)
    H, W, _ = arr.shape
    comps, bg, diff = find_ribbons(arr, args.tol, args.min_area)
    print(f"poster {W}x{H}  |  {len(comps)} ribbons found")
    if len(comps) < 2:
        raise SystemExit("need the five ribbons to work from")

    areas = [int(c.sum()) for c in comps]
    pick = args.source - 1 if args.source else int(np.argmax(areas))
    print(f"  areas {areas}  ->  copying row {pick + 1}")

    src = comps[pick]
    cols, top, bot = profile(src, 6.0 * args.ss)
    # Pull the wave in from the edges. The bowl and the organ are placed against
    # its two tips, so a wave that runs to the edge of the poster drags them out
    # there with it - and a vertical feed crops the sides, taking the organ and
    # half the label with them.
    if args.span:
        a, b = [float(v) for v in args.span.split(",")]
        was = (int(np.where(src)[1].min()), int(np.where(src)[1].max()))
        newcols = np.arange(int(a * W), int(b * W) + 1)
        u_old = np.linspace(0, 1, len(cols)); u_new = np.linspace(0, 1, len(newcols))
        top = np.interp(u_new, u_old, top); bot = np.interp(u_new, u_old, bot)
        cols = newcols
        print(f"  wave placed from {a*100:.0f}% to {b*100:.0f}% of the width "
              f"(x {cols[0]}-{cols[-1]}), was x {was[0]}-{was[1]}")
    centre, half, new_half = thicken(cols, top, bot, args.floor, args.tip)
    if args.level:
        # The source wave climbs from left to right. Placed by either tip, the
        # other one lands 100px off the circle it is supposed to run into - it
        # met the organ at the top of its circle rather than in the middle, and
        # read as the liquid stopping short of it. Take the tip-to-tip slope out
        # and the S is symmetric: both ends arrive at the same height, so both
        # can sit on a circle centre at once. Only the trend is removed, so the
        # curve of the wave itself is untouched.
        ramp = np.linspace(centre[0], centre[-1], len(centre))
        rise = centre[-1] - centre[0]
        centre = centre - (ramp - ramp.mean()) * args.level
        print(f"  tip-to-tip rise {rise:+.0f}px levelled by {args.level:.0%} "
              f"-> tips now {centre[-1] - centre[0]:+.0f}px apart")
    new_half = ndimage.gaussian_filter1d(new_half, 4.0 * args.ss, mode="nearest")
    tprof, aprof = taper_tail(len(cols), args.taper, args.fade)
    new_half = new_half * (0.06 + 0.94 * tprof)
    print(f"  thinnest part of the wave: {half.min() * 2:.0f}px  ->  {new_half.min() * 2:.0f}px at the tip, "
          f"{np.median(new_half) * 2:.0f}px median")
    print(f"  tail narrows over {args.taper}px and fades over the last {args.fade}px")

    out = arr.copy()
    mask_out = np.zeros((H, W), np.float32)
    # The wave is also kept as its own layer: full-strength colour plus the fade
    # in alpha. Baking the fade into the pixels means a recolour has to divide it
    # back out, and where the alpha is small that cannot be recovered - which is
    # what leaves a muddy tip in the old topic's colour.
    rgba = np.zeros((H, W, 4), np.float32)
    K = 256

    # Repaint every stripe flat before drawing anything. Erasing the old wave and
    # patching the hole cannot win: the background carries a gradient and a
    # texture, and whatever is reconstructed leaves either a ghost of the old
    # outline or a rectangular patch where the fill misses. A stripe filled with
    # one colour has nothing left to give either away, and a flat row is what the
    # animator's background model assumes anyway.
    liquid = np.zeros((H, W), bool)
    for c in comps:
        liquid |= c
    liquid = ndimage.binary_dilation(liquid, np.ones((41 * args.ss, 41 * args.ss)))

    # The bands are laid out afresh rather than inherited from the source poster.
    # There they sat where the generator happened to put them, leaving 500px idle
    # under the last wave while every row was still too short to hold a bowl and
    # a caption underneath it. Spread evenly between the title and the logo, each
    # row gains what that idle space was wasting.
    marg = arr[:, 4 * args.ss:16 * args.ss, :].mean(axis=1)
    ch = np.abs(np.diff(marg, axis=0)).max(axis=1)
    old_edges = [0] + [int(y) + 1 for y in np.where(ch > 25)[0]] + [H]
    old_edges = [e for i, e in enumerate(old_edges) if i == 0 or e - old_edges[i - 1] > 60 * args.ss]

    tones = []
    for k in range(len(old_edges) - 1):
        a0, b0 = old_edges[k], old_edges[k + 1]
        band = np.zeros((H, W), bool); band[a0:b0] = True
        sel_bg = band & ~liquid
        if sel_bg.sum() > 500:
            tones.append(np.median(arr[sel_bg], axis=0))
    tones = sorted(tones, key=lambda t: t.mean())
    dark, light = tones[0], tones[-1]

    # the logo is the only artwork outside the waves, and it travels with them
    strong = (~liquid) & (np.abs(arr - dark).max(axis=2) > 80) & (np.abs(arr - light).max(axis=2) > 80)
    joined = ndimage.binary_closing(strong, np.ones((8 * args.ss, 40 * args.ss)))
    lab_k, n_k = ndimage.label(joined)
    keep = np.zeros_like(strong)
    for j in range(1, n_k + 1):
        blob = lab_k == j
        if blob.sum() > 2000 * args.ss * args.ss:
            keep |= blob & strong
    logo_px = arr[keep].copy()
    ky, kx = np.where(keep)

    top_y = int(H * args.rows_top); bot_y = int(H * args.rows_bottom)
    band_h = (bot_y - top_y) / 5.0
    bands = [(int(top_y + i * band_h), int(top_y + (i + 1) * band_h)) for i in range(5)]
    out[:] = dark
    for i, (a0, b0) in enumerate(bands):
        out[a0:b0] = dark if i % 2 == 0 else light
    shift = 0
    if keep.sum():
        shift = int(H * args.logo_y) - int(ky.mean())
        out[np.clip(ky + shift, 0, H - 1), kx] = logo_px
    print(f"  five bands of {band_h:.0f}px between y {top_y} and {bot_y}; "
          f"logo moved {shift}px to y {int(H * args.logo_y)}")

    for i, comp in enumerate(comps):
        # Each row keeps its own colour and shading; only the geometry is
        # conformed. Rotating one row's pixels onto another row's hue loses the
        # colour the generator actually chose - the dark green came back lime.
        _, _, _, tex = cross_section(arr, comp, K, 6.0 * args.ss)

        ys_, xs_ = np.where(comp)
        a0, b0 = bands[i]
        if args.wave_pos is None:
            # Straight onto the circle centre. recolor_base.py lays the row out as
            # gap, circle, gap, caption, gap, so the centre follows from the band
            # height and those two numbers - and deriving it here from the same
            # three is what keeps the tip and the circle from drifting apart.
            r_row = ((b0 - a0) - (args.caption_h + 3 * args.gap) * args.ss) / 2.0
            aim = a0 + args.gap * args.ss + r_row + args.tip_drop * args.ss
        else:
            aim = a0 + (b0 - a0) * args.wave_pos
        dy = aim - (0.5 * (centre[0] + centre[-1]) if args.wave_pos is None
                    else (top.min() + bot.max()) * 0.5)
        cen = centre + dy
        lo = cen - new_half; hi_ = cen + new_half
        y0 = max(0, int(lo.min()) - 3); y1 = min(H, int(hi_.max()) + 4)
        Yb = np.arange(y0, y1)[:, None]
        vv = (Yb - lo[None, :]) / np.maximum(hi_ - lo, 1)[None, :]
        inside = (vv >= 0) & (vv <= 1)
        # Inset from the very edge of the cross-section. The smoothed profile can
        # sit a pixel outside the real ribbon, so its first and last rows hold the
        # old background - and painting those as the wave's edge draws a black rim.
        kk = (0.06 + 0.88 * np.clip(vv, 0, 1)) * (K - 1)
        jj = np.broadcast_to(np.linspace(0, tex.shape[1] - 1, len(cols))[None, :], vv.shape)
        paint = np.stack([ndimage.map_coordinates(tex[:, :, ch], [kk, jj], order=3, mode="nearest")
                          for ch in range(3)], axis=2)

        a_ = np.array(Image.fromarray((inside.astype(np.float32) * 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255.0
        a_ = a_ * aprof[None, :]
        tile = out[y0:y1, cols[0]:cols[-1] + 1, :]
        out[y0:y1, cols[0]:cols[-1] + 1, :] = tile * (1 - a_[:, :, None]) + paint * a_[:, :, None]
        mask_out[y0:y1, cols[0]:cols[-1] + 1] = np.maximum(mask_out[y0:y1, cols[0]:cols[-1] + 1], a_)
        sub = rgba[y0:y1, cols[0]:cols[-1] + 1]
        hit = a_ > sub[:, :, 3]
        sub[:, :, :3] = np.where(hit[:, :, None], paint, sub[:, :, :3])
        sub[:, :, 3] = np.maximum(sub[:, :, 3], a_)
        print(f"    row {i + 1}: own colour {tuple(int(c) for c in np.median(arr[comp], axis=0))}, canonical shape")

    oimg = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    mimg = Image.fromarray((mask_out * 255).astype(np.uint8))
    if args.ss > 1:
        oimg = oimg.resize((W0, H0), Image.LANCZOS)
        mimg = mimg.resize((W0, H0), Image.LANCZOS)
    if args.sharpen > 0:
        oimg = oimg.filter(ImageFilter.UnsharpMask(radius=1.2, percent=int(args.sharpen * 100), threshold=2))
    o = np.array(oimg).astype(np.float32)
    rng = np.random.default_rng(3)
    o = o + rng.uniform(-0.5, 0.5, o.shape)              # break up 8-bit banding
    Image.fromarray(np.clip(o, 0, 255).round().astype(np.uint8)).save(args.out)
    mimg.save(args.mask)
    rimg = Image.fromarray(np.concatenate(
        [np.clip(rgba[:, :, :3], 0, 255), np.clip(rgba[:, :, 3:] * 255, 0, 255)], axis=2).astype(np.uint8))
    if args.ss > 1:
        rimg = rimg.resize((W0, H0), Image.LANCZOS)
    rimg.save(args.layer)
    print(f"wrote {args.layer} (the wave on its own, with the fade in alpha)")
    print(f"wrote {args.out} and {args.mask}")


if __name__ == "__main__":
    main()
