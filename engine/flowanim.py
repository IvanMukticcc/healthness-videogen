#!/usr/bin/env python3
"""
flowanim.py - deterministic liquid-flow animation for the Healthness posters.

No generative model. It finds the coloured ribbons in a still poster, then
slides a soft sheen along them at a constant speed. Everything else is copied
frame for frame, so text, bowls and organs cannot glitch: they are literally
the same pixels in every frame.

    python3 flowanim.py poster.png -o flow.mp4
    python3 flowanim.py poster.png --mask-only      # check the mask first

Tune with --x0/--x1 (where the ribbons live, as a fraction of width) and
--amp (how strong the sheen is).
"""
import argparse
from pathlib import Path
import importlib, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


# The mask lives beside this script. --base and --anchored stay explicit: those
# are the topic's own files and belong to whichever folder is calling.
_HERE = Path(__file__).resolve().parent


def wave_centre_curves(geo, layout, W):
    """One function per row giving the wave's own centre line at any x.

    An overlay that wants to sit *in* the liquid - a badge, a marker - needs the
    line the wave actually follows, not the row's centre, which the wave crosses
    twice and sits on nowhere. Both variants worked this out for themselves, in
    the same fifteen lines, from geometry that only this file has. So it lives
    here and is handed over.
    """
    L = json.load(open(layout))
    k = W / 1536.0
    curves = []
    for row in L["rows"]:
        cy = row["cy"] * k
        g = min(geo, key=lambda g: abs(0.5 * (g["top"].mean() + g["bot"].mean()) - cy))
        # top and bot are stored over the ribbon's own column range, so the index
        # is x - x0 and not x.
        mid, x0 = 0.5 * (g["top"] + g["bot"]), g["x0"]
        curves.append(lambda x, mid=mid, x0=x0:
                      float(mid[int(np.clip(round(x) - x0, 0, len(mid) - 1))]))
    return curves


def load_overlays(spec):
    """Import the overlay modules named on the command line, from the caller.

    This is the seam that keeps one animator. Micro and Exercise
    each had their own fork of this file - 77 and 152 lines apart - and the whole
    of both differences was: import a module, add its flags, build a plan, draw it
    on the finished frame. So the animator now does those four things for any
    module that offers three functions, and neither variant needs a copy.

        add_arguments(parser)   optional, its own flags
        build(args, ctx)        returns whatever it wants to draw with, or None
        draw(frame, plan, t)    on the finished frame, t in seconds

    Modules are imported from the directory the command was run in, which is the
    variant's own folder.
    """
    if not spec:
        return []
    sys.path.insert(0, os.getcwd())
    mods = []
    for name in spec.split(","):
        name = name.strip()
        if name:
            mods.append(importlib.import_module(name))
    return mods


def autocrop(img, thresh=24):
    """Trim a uniform dark border (screenshot padding, rounded corners)."""
    a = np.array(img.convert("RGB")).astype(np.int16)
    lum = a.max(axis=2)
    rows = np.where(lum.max(axis=1) > thresh)[0]
    cols = np.where(lum.max(axis=0) > thresh)[0]
    if len(rows) == 0 or len(cols) == 0:
        return img
    return img.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))


def ribbon_mask(arr, x0, x1, y0, y1, tol, min_span, feather, debug=None):
    """White where the liquid ribbons are, black everywhere else.

    Thresholding alone cannot separate a shaded photoreal ribbon from its row
    background - the darker half of the ribbon and the background overlap. So
    instead: mark everything that is not background, label the connected blobs,
    and keep only the blobs long enough to be a ribbon. Labels break into short
    per-letter blobs and drop out on their own, whatever colour they are.
    """
    H, W, _ = arr.shape
    a = arr.astype(np.int16)

    # Background colour of each scanline, sampled from the left and right margins,
    # which are always empty poster background.
    # The cream rows are not flat: they ramp left to right by ~70 levels, far more
    # than any sane tolerance. A single median per scanline therefore misreads half
    # the row as ink, so the background is modelled as a ramp between the two margins.
    m = max(2, int(W * 0.03))
    left = np.median(a[:, 1:1 + m, :], axis=1)
    right = np.median(a[:, W - 1 - m:W - 1, :], axis=1)
    t = (np.arange(W) / (W - 1))[None, :, None]
    bg = left[:, None, :] * (1 - t) + right[:, None, :] * t

    diff = np.abs(a - bg).max(axis=2)

    xs = np.arange(W)[None, :]
    ys = np.arange(H)[:, None]
    window = (xs >= int(x0 * W)) & (xs <= int(x1 * W)) \
             & (ys >= int(y0 * H)) & (ys <= int(y1 * H))

    fg = (diff > tol) & window
    fg = ndimage.binary_closing(fg, np.ones((5, 5)))     # bridge JPEG speckle
    fg = ndimage.binary_opening(fg, np.ones((9, 9)))     # sever label letters touching a ribbon

    lab, n = ndimage.label(fg)
    keep = np.zeros_like(fg)
    span_px = min_span * W
    kept = []
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        if sl is None:
            continue
        w = sl[1].stop - sl[1].start
        h = sl[0].stop - sl[0].start
        if w >= span_px and w > h:                       # long and horizontal: a ribbon
            keep |= (lab == i)
            kept.append((w, h))
    if debug is not None:
        debug.update(components=n, kept=len(kept), shapes=sorted(kept, reverse=True)[:8])

    mimg = Image.fromarray((keep * 255).astype(np.uint8))
    if feather > 0:
        mimg = mimg.filter(ImageFilter.GaussianBlur(feather))
    return np.array(mimg).astype(np.float32) / 255.0, diff



def flow_coord(keep, smooth=41):
    """Arc length along each ribbon, as a coordinate for every pixel it covers.

    A sheen driven by x alone reads as a highlight sweeping across glass: the
    bands sit vertically and cut the ribbon at an angle. Here each ribbon gets
    its own centreline; bands then run perpendicular to the local flow and the
    phase advances with arc length, so the streaks travel *along* the curve.
    """
    H, W = keep.shape
    u = np.zeros((H, W), np.float32)
    lab, n = ndimage.label(keep)
    Y, X = np.mgrid[0:H, 0:W]
    for i in range(1, n + 1):
        comp = lab == i
        cnt = comp.sum(axis=0).astype(np.float32)
        cols = np.where(cnt > 0)[0]
        if len(cols) < 8:
            continue
        yc = np.zeros(W, np.float32)
        yc[cols] = (comp * np.arange(H)[:, None]).sum(axis=0)[cols] / cnt[cols]
        yc[:cols[0]], yc[cols[-1] + 1:] = yc[cols[0]], yc[cols[-1]]
        k = np.ones(smooth) / smooth                      # smooth the centreline
        yc = np.convolve(yc, k, mode="same")
        yc[:smooth], yc[-smooth:] = yc[smooth], yc[-smooth]
        slope = np.gradient(yc)
        arc = np.cumsum(np.sqrt(1.0 + slope ** 2))        # constant speed along the curve
        u[comp] = (arc[X] + slope[X] * (Y - yc[X]))[comp].astype(np.float32)
    return u


def striations(H, seed_cols=64):
    """Two smooth phase offsets across the ribbon thickness.

    Without these the bands are clean stripes marching in lockstep, which reads
    as a wipe. Offsetting the phase per scanline breaks them into filaments that
    slide past each other, the way the inside of a pour does.
    """
    rng = np.random.default_rng(7)
    out = []
    for _ in range(2):
        anchors = rng.random(seed_cols)
        y = np.interp(np.linspace(0, seed_cols - 1, H), np.arange(seed_cols), anchors)
        out.append(y.astype(np.float32)[:, None])
    return out



def flatten_along_flow(arr, mask, span):
    """Blur the ribbon lengthwise, inside its own edges.

    The poster bakes a long specular highlight into each ribbon. Left in place it
    stays nailed down while the streaks travel over it, and the eye reads the
    moving part as a light crossing still liquid rather than as the liquid moving.
    Smearing detail along the flow leaves the cross-section shading - so the
    ribbon still looks round - but removes the landmark that says "not moving".
    Normalised so the blur cannot drag background in over the edges.
    """
    m = mask[:, :, None]
    num = ndimage.uniform_filter1d(arr * m, size=span, axis=1, mode="nearest")
    den = ndimage.uniform_filter1d(m, size=span, axis=1, mode="nearest")
    # Outside the ribbons den is 0 and the quotient is meaningless: keep the poster.
    return np.where(den > 1e-2, num / np.maximum(den, 1e-3), arr)



def ribbon_geometry(keep, arr, gap_tol=12, pad=10, taper_right=True, bgsrc=None):
    """Per ribbon: edges, the background hidden underneath, and arc length.

    Everything is stored in the ribbon's own column range. Smoothing the edges
    across the full poster width instead pulls them towards zero at both ends,
    because the columns outside the ribbon carry no edge at all - that collapses
    the silhouette into rectangles and sends the background sampler into the
    neighbouring row.
    """
    H, W = keep.shape
    out = []
    lab, n = ndimage.label(keep)
    for i in range(1, n + 1):
        comp = lab == i
        cnt = comp.sum(axis=0)
        cols = np.where(cnt > 0)[0]
        if len(cols) < 40:
            continue

        # The opening that cleaned the mask also ate ~4px off every edge. Erasing
        # to the eroded edge wipes a rim of real ribbon that the redraw never puts
        # back, which shows as a bright fringe along the whole silhouette. Edges
        # come from a dilated copy; the run count stays on the original, so the
        # splash fingers are not welded shut by the dilation.
        # Speckle inside a ribbon shows up as slits a dozen pixels tall. Closed
        # holes are filled outright; the gap threshold below covers the rest.
        comp = ndimage.binary_fill_holes(comp)
        grown = ndimage.binary_dilation(comp, np.ones((9, 9)))
        top = np.full(W, -1); bot = np.full(W, -1); runs = np.zeros(W, int)
        for x in cols:
            ys = np.where(comp[:, x])[0]
            gs = np.where(grown[:, x])[0]
            top[x], bot[x] = gs[0], gs[-1]
            # Only a real gap splits the body. Counting every one-pixel hole as a
            # split shatters a ribbon that has speckle in it, and then almost none
            # of it qualifies as body and almost none of it moves.
            runs[x] = 1 + int((np.diff(ys) > gap_tol).sum())

        # Body = columns that are a single span. The splash crown is several spans
        # with gaps; deforming those would weld the fingers into one blob.
        idx = np.where((runs == 1) & (cnt > 0))[0]
        if len(idx) < 40:
            continue
        run = max(np.split(idx, np.where(np.diff(idx) > 1)[0] + 1), key=len)
        x0, x1 = int(run[0]), int(run[-1])
        xs = np.arange(x0, x1 + 1)
        L = len(xs)
        if L < 40:
            continue

        k = 9
        ker = np.ones(k) / k
        smooth = lambda v: np.convolve(np.pad(v, k // 2, mode="edge"), ker, mode="valid")
        t_s = smooth(top[xs].astype(np.float64))
        b_s = smooth(bot[xs].astype(np.float64))

        yc = 0.5 * (t_s + b_s)
        slope = np.gradient(yc)
        arc = np.cumsum(np.sqrt(1.0 + slope ** 2))

        # background colour per column, taken just outside the ribbon
        # Sampled well clear of the ribbon: the mask edge is feathered, so a few
        # pixels out is still half ribbon and repainting with it leaves a pale ghost.
        # Sampled from the base layer when there is one. In the finished poster
        # the bowl overlaps the start of the wave, so the pixels above it are
        # glass, and repainting with those leaves a pale smear under the pour.
        # The base layer has nothing there but the row's own background.
        bsrc = arr if bgsrc is None else bgsrc
        bgc = np.zeros((L, 3), np.float32)
        for j in range(L):
            hi = int(top[xs[j]]) - 14
            if hi - 12 >= 0:
                bgc[j] = np.median(bsrc[hi - 12:hi, xs[j], :], axis=0)
            else:
                lo = int(bot[xs[j]]) + 14
                bgc[j] = np.median(bsrc[lo:lo + 12, xs[j], :], axis=0)
        kb = np.ones(21) / 21                              # the row gradient is smooth
        for ch in range(3):
            bgc[:, ch] = np.convolve(np.pad(bgc[:, ch], 10, mode="edge"), kb, mode="valid")

        ramp = max(8, int(L * 0.05))
        taper = np.ones(L, np.float32)
        taper[:ramp] = np.linspace(0, 1, ramp)
        if taper_right:
            taper[-ramp:] = np.linspace(1, 0, ramp)

        out.append(dict(x0=x0, x1=x1, xs=xs, top=t_s, bot=b_s,
                        arc=arc, bg=bgc, taper=taper))
    return out



def ribbon_texture(arr, geo, K=96, smooth=0.10, edge=0.04):
    """Resample each ribbon into its own grid and split form from surface.

    Transport needs somewhere for the material to come from. Crossfading two
    copies half a cycle apart does not provide it: the weighted centre of the
    shift stays put, so the result throbs instead of travelling. Here the ribbon
    is split into its rounded form, which stays, and its surface detail, which
    circulates along the length. The detail is faded out at both ends before it
    wraps, so the wrap joins zero to zero and never shows.
    """
    for g in geo:
        xs, top, bot = g["xs"], g["top"], g["bot"]
        L = len(xs)
        vv = np.linspace(0, 1, K)[:, None]
        ys = top[None, :] + vv * (bot - top)[None, :]
        xsr = np.broadcast_to(xs[None, :].astype(float), ys.shape)
        tex = np.stack([ndimage.map_coordinates(arr[:, :, c], [ys, xsr], order=1, mode="nearest")
                        for c in range(3)], axis=2)

        span = max(3, int(L * smooth) | 1)
        base = ndimage.uniform_filter1d(tex, size=span, axis=1, mode="nearest")
        det = tex - base

        n = max(2, int(L * edge))
        w = np.ones(L, np.float32)
        ramp = np.linspace(0, 1, n); ramp = ramp * ramp * (3 - 2 * ramp)
        w[:n] = ramp; w[-n:] = ramp[::-1]
        g["base"], g["det"] = base, det * w[None, :, None]
    return geo



def find_droplets(arr, diff, mask, geo, tol, protect=None, lo=12, hi=2500, span=44,
                  tail_span=130,
                  margin=45, fill_min=0.55, aspect=(0.55, 1.8), hue_tol=80):
    """Lift the loose droplets out of the poster so they can be flown separately.

    They are too small to survive the ribbon filter, so nothing has been touching
    them: the stream moves and they hang in the air. Each one is cut out with a
    soft edge, the hole is filled with the background it was sitting on, and the
    patch is handed back to be drawn wherever it should be at a given moment.
    """
    H, W, _ = arr.shape
    solid = diff > tol
    near = ndimage.binary_dilation(mask > 0.4, np.ones((5, 5)))
    drops = []
    for g in geo:
        r = g.get("reach")
        xlo, xhi = int(g["xs"][0]), int(r["organ_x"] - 4) if r else int(g["xs"][-1] + 60)
        y0 = max(0, int(g["top"].min()) - margin); y1 = min(H, int(g["bot"].max()) + margin)
        # This ribbon's own colour, not the median of all five mixed together:
        # a global reference sits between crimson, white and green and belongs to
        # none of them, so whole rows lose every droplet they have.
        own = np.zeros(mask.shape, bool); own[y0:y1] = mask[y0:y1] > 0.6
        ink = arr[own]
        ribbon_rgb = np.median(ink, axis=0) if len(ink) else np.zeros(3)
        region = np.zeros_like(solid)
        region[y0:y1, xlo:xhi] = solid[y0:y1, xlo:xhi] & ~near[y0:y1, xlo:xhi]
        # The splash tips past the end of the body are part of the ribbon, so the
        # droplet pass skips them and the deformation cannot reach them either:
        # they sit there for the whole clip, neither moving nor leaving. Cut them
        # off at the body's last column and let them fly like everything else.
        # The crown's thin fingers are eaten by the opening that cleans the ribbon
        # mask, so the deformation never sees them and the droplet pass skips them
        # for being next to the ribbon. They are exactly the pixels that have paint
        # but no mask: take those, and let them fly.
        tail = np.zeros_like(solid)
        t0 = max(int(g["xs"][0]), int(g["xs"][-1]) - 90)
        tail[y0:y1, t0:xhi] = (solid & ~(mask > 0.5))[y0:y1, t0:xhi]
        region |= tail

        lab, n = ndimage.label(region)
        for i, sl in enumerate(ndimage.find_objects(lab), start=1):
            if sl is None:
                continue
            h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            comp = lab[sl] == i
            limit = tail_span if sl[1].start >= int(g["xs"][-1]) - 90 else span
            if not (lo <= comp.sum() <= hi) or max(h, w) > limit:
                continue
            # In two of the five rows the label sits four pixels under the ribbon,
            # so no margin can keep letters out. A droplet is a fat round blob in
            # the liquid's own colour; a letter is thin, lopsided, and white or
            # black. All three have to hold, because each one alone lets some
            # letter through - and a letter cut out of a label and flown across
            # the poster is the worst artefact this tool can produce.
            # Never lift type, whatever shape or colour it has. In the bottom row
            # the label sits inside the search band and its letters are as pale as
            # the lemon ribbon, so they pass both the shape and the colour test.
            if protect is not None and (protect[sl] & comp).any():
                continue
            is_tail = sl[1].start >= int(g["xs"][-1]) - 90
            if not is_tail:
                if comp.sum() / float(w * h) < fill_min:
                    continue
                if not (aspect[0] <= w / float(h) <= aspect[1]):
                    continue
            elif comp.sum() / float(w * h) < 0.35:
                continue
            med = np.median(arr[sl][comp], axis=0)
            if np.abs(med - ribbon_rgb).max() > hue_tol:
                continue
            py0, py1 = max(0, sl[0].start - 8), min(H, sl[0].stop + 8)
            px0, px1 = max(0, sl[1].start - 8), min(W, sl[1].stop + 8)
            sub = np.zeros((py1 - py0, px1 - px0), bool)
            sub[sl[0].start - py0:sl[0].stop - py0, sl[1].start - px0:sl[1].stop - px0] = comp
            # Wide enough to swallow the droplet's own soft edge and shadow: a
            # tight mask leaves a faint ring behind at the spot it flew from.
            alpha = np.array(Image.fromarray((ndimage.binary_dilation(sub, np.ones((7, 7))) * 255)
                                             .astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)),
                             dtype=np.float32) / 255.0
            # Erase wide, draw tight. The wide matte is needed to lift the drop and
            # its baked shadow off the poster; carrying that same matte to the new
            # position would paste the shadow, and a square of the old background
            # with it, onto clean ground.
            draw = np.array(Image.fromarray((sub * 255).astype(np.uint8))
                            .filter(ImageFilter.GaussianBlur(0.7)), dtype=np.float32) / 255.0
            draw = np.clip((draw - 0.35) / 0.5, 0, 1)
            ring = ndimage.binary_dilation(sub, np.ones((15, 15))) & ~ndimage.binary_dilation(sub, np.ones((11, 11)))
            patch = arr[py0:py1, px0:px1, :].copy()
            bg = np.median(patch[ring], axis=0) if ring.sum() > 4 else patch[0, 0]
            drops.append(dict(y0=py0, x0=px0, a=alpha[:, :, None], d=draw[:, :, None], px=patch,
                              bg=bg.astype(np.float32), organ=xhi))
    return drops
    return drops


def erase_droplets(arr, drops):
    for d in drops:
        h, w = d["a"].shape[:2]
        tile = arr[d["y0"]:d["y0"] + h, d["x0"]:d["x0"] + w, :]
        arr[d["y0"]:d["y0"] + h, d["x0"]:d["x0"] + w, :] = tile * (1 - d["a"]) + d["bg"] * d["a"]
    return arr


def plan_droplets(drops, lane):
    """Put every droplet on the same run-up to the organ, at staggered phases.

    Left where the poster put them, most sit within a few dozen pixels of the
    organ: there is no room to travel, and a shared fade makes the whole set
    blink at once. Sharing one lane and differing only in phase turns them into
    a stream where some are always setting off while others are arriving.
    """
    for d in drops:
        start = d["organ"] - lane
        d["start"] = start
        d["lane"] = lane
        d["phase"] = float(((d["x0"] - start) / lane) % 1.0)
    return drops


def draw_droplets(out, drops, phase):
    """Droplets ride the same current: one clock, so they stay in step."""
    H, W, _ = out.shape
    for d in drops:
        u = (phase + d["phase"]) % 1.0
        h, w = d["a"].shape[:2]
        x = int(round(d["start"] + u * d["lane"]))
        if x < 0 or x + w > W:
            continue
        f = min(1.0, u / 0.12) * min(1.0, (1.0 - u) / 0.22)
        if f <= 0.02:
            continue
        a = d["d"] * f
        tile = out[d["y0"]:d["y0"] + h, x:x + w, :]
        out[d["y0"]:d["y0"] + h, x:x + w, :] = tile * (1 - a) + d["px"] * a



def protected_pixels(arr, mask, geo=None, lum_gap=70, bright=210, dark=70, grow=3):
    """Everything that is ink or artwork rather than liquid, and must never move.

    In the bottom rows the label sits inside the ribbon's own vertical span, so
    no band margin can keep the stretch off the text - the two genuinely overlap.
    Marking the type itself and restoring it after every frame is the only thing
    that holds in all five rows regardless of how the layout falls.
    """
    H, W, _ = arr.shape
    m = max(2, int(W * 0.03))
    left = np.median(arr[:, 1:1 + m, :], axis=1)
    right = np.median(arr[:, W - 1 - m:W - 1, :], axis=1)
    t = (np.arange(W) / (W - 1))[None, :, None]
    bg = left[:, None, :] * (1 - t) + right[:, None, :] * t

    lum = arr.mean(axis=2); bgl = bg.mean(axis=2)
    ink = (np.abs(lum - bgl) > lum_gap) & ((lum > bright) | (lum < dark))
    ink &= ~ndimage.binary_dilation(mask > 0.3, np.ones((15, 15)))

    # Brightness alone also flags the pale ribbons - garlic and lemon are as light
    # as the type - and pinning their edges freezes patches of liquid in some rows
    # and none in others. Type is thin: a letter stroke cannot contain a 21x21
    # square, a sheet of milk or an organ's glow can. Keep only what is thin.
    ink &= ~ndimage.binary_opening(ink, np.ones((21, 21)))

    # The pale splash slivers past the end of a ribbon are thin and bright too,
    # so the same test calls them type and freezes them. Carve out the corridor
    # they live in - the ribbon's own height, from its end to the organ. Labels
    # sit well below that line, so they keep their protection.
    if geo:
        for g in geo:
            r = g.get("reach")
            if not r:
                continue
            y0 = max(0, int(g["top"][-1]) - 35); y1 = min(H, int(g["bot"][-1]) + 35)
            x0 = max(0, int(g["xs"][-1]) - 90); x1 = min(W, int(r["organ_x"]))
            ink[y0:y1, x0:x1] = False
    return ndimage.binary_dilation(ink, np.ones((grow, grow)))


def render_wave(arr, geo, n1, n2, lam1, lam2, c1, c2, t, amp, swell, snake, pad, advect, clean=None):
    """One frame: repaint the background, then draw each ribbon deformed.

    advect is the distance the surface has travelled, as a share of the
    ribbon's length; whole numbers over the clip keep the loop seamless.
    """
    """One frame: repaint the row background, then draw each ribbon deformed."""
    H, W, _ = arr.shape
    out = arr.copy()
    TAU = 2 * np.pi
    for g in geo:
        xs, top, bot = g["xs"], g["top"], g["bot"]
        arc, taper, bgc = g["arc"], g["taper"], g["bg"]
        half = np.maximum((bot - top) * 0.5, 1.0)

        ph = TAU * (arc / lam1 - c1 * t)
        bulge = swell * half * taper * np.sin(ph)          # thickness travels
        shift = snake * half * taper * np.sin(ph - 0.9)    # and the axis sways
        topd, botd = top - bulge + shift, bot + bulge + shift

        ylo = max(0, int(np.floor(min(topd.min(), top.min()))) - pad - 2)
        yhi = min(H, int(np.ceil(max(botd.max(), bot.max()))) + pad + 2)
        Y = np.arange(ylo, yhi)[:, None]
        tile = out[ylo:yhi, xs[0]:xs[-1] + 1, :]

        # erase the old ribbon with the row background it was covering
        erase = (Y >= (top - pad)[None, :]) & (Y <= (bot + pad)[None, :])
        # Only where the poster still equals the base layer. Where a bowl or an
        # organ has been laid over the wave neither source is right: the poster
        # has glass there and the base has bare background, and repainting with
        # either one draws a smear or an outline across the join.
        if clean is not None:
            erase &= clean[ylo:yhi, xs[0]:xs[-1] + 1]
        tile[erase] = np.broadcast_to(bgc[None, :, :], tile.shape)[erase]

        span = np.maximum(botd - topd, 1.0)
        v = (Y - topd[None, :]) / span[None, :]            # 0..1 across the ribbon
        inside = (v >= 0) & (v <= 1)
        # The mask runs the whole length of the wave, including the stretches the
        # bowl and the organ are drawn over. Painting there puts the liquid in
        # front of them; the poster shows what is on top, so paint only where it
        # still shows liquid.
        if clean is not None:
            inside &= clean[ylo:yhi, xs[0]:xs[-1] + 1]
        vc = np.clip(v, 0, 1)

        # The form is read where it is; the surface is read from further
        # upstream, so the liquid's own detail travels towards the organ.
        L = len(xs)
        K = g["base"].shape[0]
        jj = np.broadcast_to(np.arange(L, dtype=np.float64)[None, :], v.shape)
        kk = vc * (K - 1)
        jsrc = np.mod(jj - advect * L, L)

        acc = np.empty(tile.shape, np.float64)
        for ch in range(3):
            form = ndimage.map_coordinates(g["base"][:, :, ch], [kk, jj], order=1, mode="nearest")
            surf = ndimage.map_coordinates(g["det"][:, :, ch], [kk, jsrc], order=1, mode="grid-wrap")
            acc[:, :, ch] = form + surf
        tile[:, :, :] = np.where(inside[:, :, None], acc, tile)

        # streaks in the ribbon's own frame, so they travel with the body
        uu = np.broadcast_to(arc[None, :], v.shape)
        band = (0.55 * np.sin(TAU * (uu / lam1 + n1[ylo:yhi] - c1 * t))
                + 0.45 * np.sin(TAU * (uu / lam2 + n2[ylo:yhi] - c2 * t)))
        edge = np.clip(1.0 - np.abs(v - 0.5) * 2.0, 0, 1) ** 0.5
        shade = (1.0 + amp * band * edge)[:, :, None]
        tile[:] = np.where(inside[:, :, None], np.clip(tile * shade, 0, 255), tile)
        out[ylo:yhi, xs[0]:xs[-1] + 1, :] = tile
    return out



def ribbon_reach(arr, diff, geo, tol, anchor=0.55, cover=0.25, look=30):
    """Plan how far each ribbon has to stretch to touch the organ beside it.

    Growing a fresh tube out of the tip reads as a second, separate stream: the
    old end just sits there while something new crawls out from behind it. So
    nothing is added - the ribbon itself is stretched, and its real tip, splash
    crown and droplets are carried along by that stretch.
    """
    H, W, _ = arr.shape
    for g in geo:
        xs, top, bot = g["xs"], g["top"], g["bot"]
        y0 = max(0, int(top.min()) - 40); y1 = min(H, int(bot.max()) + 40)
        cov = (diff[y0:y1, :] > tol).mean(axis=0)

        # The scattered droplets past the ribbon read as thin coverage; the organ
        # is a solid block, so require a real column before calling it the organ.
        ox = next((x for x in range(int(xs[-1]) + look, W - 4) if cov[x] > cover), None)
        if ox is None:
            g["reach"] = None
            continue
        # Centre taken across the whole organ, not its first few columns: on a
        # shape like the thyroid those columns are one lobe and the tube aims low.
        sub = diff[y0:y1, ox:min(W, ox + 170)] > tol
        wts = sub.sum(axis=1).astype(float)
        ocy = float((wts * np.arange(len(wts))).sum() / max(wts.sum(), 1) + y0)

        # Where the poster's own liquid actually ends: the body, its splash crown
        # and the droplets past it. That tip is what has to travel.
        # The tip is the end of the solid body, not the last stray droplet: the
        # droplets already fly almost to the organ, so measuring from them leaves
        # nothing to travel while the stream itself still stops a hundred px short.
        tip = int(xs[-1])
        target = ox - 10
        if target - tip < 6:
            g["reach"] = None
            continue
        g["reach"] = dict(y0=y0, y1=y1, tip=tip, organ_x=ox,
                          anchor=int(xs[0] + (tip - xs[0]) * anchor),
                          dist=float(target - tip))
    return geo


def render_reach(out, arr, solid, g, front):
    """Stretch one ribbon's band so its own tip advances towards the organ."""
    r = g["reach"]
    if r is None or front <= 0:
        return
    H, W, _ = out.shape
    y0, y1 = r["y0"], r["y1"]
    d_max = r["dist"] * front

    # Displacement grows from nothing at the anchor to the full distance at the
    # tip, and holds past it. Spread over a few hundred pixels the local stretch
    # stays under ~15%, so the liquid elongates instead of visibly smearing.
    x = np.arange(W, dtype=np.float64)
    w = np.clip((x - r["anchor"]) / max(r["tip"] - r["anchor"], 1), 0, 1)
    w = w * w * (3 - 2 * w)
    d = d_max * w

    # The organ and its glow must not move. Switching from warped to untouched at
    # a single column leaves a vertical seam through the glow and slices the tip
    # off flat, so the two are crossfaded over the run-up to the organ instead.
    # Kept tight and hard against the organ. A wide fade means the liquid's tip
    # lands inside a zone that is mostly the untouched poster, and the untouched
    # poster does not move - which is exactly the bit that sits there forever.
    fade = np.clip((x - (r["organ_x"] - 8)) / 12.0, 0, 1)
    fade = fade * fade * (3 - 2 * fade)
    band = out[y0:y1]
    Y = np.broadcast_to(np.arange(y1 - y0)[:, None], band.shape[:2])
    xsrc = np.broadcast_to((x - d)[None, :], band.shape[:2])
    for ch in range(3):
        warped = ndimage.map_coordinates(band[:, :, ch], [Y, xsrc], order=1, mode="nearest")
        band[:, :, ch] = warped * (1 - fade)[None, :] + band[:, :, ch] * fade[None, :]
    out[y0:y1] = band


def main():
    p = argparse.ArgumentParser()
    p.add_argument("poster")
    p.add_argument("-o", "--out", default="flow.mp4")
    p.add_argument("--seconds", type=float, default=8.0)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--speed", type=float, default=0.045, help="flow speed, fraction of width per second")
    p.add_argument("--lam", type=float, default=0.060, help="streak spacing, fraction of width")
    p.add_argument("--amp", type=float, default=0.05, help="streak contrast")
    p.add_argument("--sheen", type=float, default=0.07, help="broad highlight on top")
    p.add_argument("--flatten", type=float, default=0.0, help="how much baked-in detail to smear away")
    p.add_argument("--flatten-span", type=float, default=0.05, help="smear length, fraction of width")
    p.add_argument("--x0", type=float, default=0.31, help="ribbon start, fraction of width")
    p.add_argument("--x1", type=float, default=0.78, help="ribbon end, fraction of width")
    p.add_argument("--y0", type=float, default=0.10, help="below the header, fraction of height")
    p.add_argument("--y1", type=float, default=0.92, help="above the footer, fraction of height")
    p.add_argument("--tol", type=int, default=36, help="how far from the row background counts as ink")
    p.add_argument("--min-span", type=float, default=0.18, help="a ribbon is at least this wide")
    p.add_argument("--feather", type=float, default=2.5)
    p.add_argument("--width", type=int, default=0, help="resize poster to this width first")
    p.add_argument("--mode", choices=["wave", "glow"], default="wave",
                   help="wave moves the silhouette, glow only lights the inside")
    p.add_argument("--drops", type=int, default=1, help="1 flies the loose droplets, 0 leaves them")
    p.add_argument("--droplane", type=float, default=0.20,
                   help="how long a run-up the droplets get, fraction of width")
    p.add_argument("--edge", type=float, default=0.04,
                   help="how much of each ribbon end is faded before the surface wraps")
    p.add_argument("--advect", type=float, default=1.0,
                   help="how much of the surface motion to apply; 0 freezes it")
    p.add_argument("--swell", type=float, default=0.07, help="how far the edge travels")
    p.add_argument("--snake", type=float, default=0.0, help="sideways sway of the axis")
    p.add_argument("--anchor", type=float, default=0.55,
                   help="where along the ribbon the stretch starts")
    p.add_argument("--reach", type=float, default=2.5,
                   help="seconds for the liquid to travel to the organ; 0 disables")
    p.add_argument("--gap", type=int, default=20, help="vertical hole that still counts as body")
    p.add_argument("--pad", type=int, default=3)
    p.add_argument("--autocrop", action="store_true")
    p.add_argument("--mask", default=str(_HERE / "ribbon_mask.png"),
                   help="use this mask file instead of detecting the ribbons")
    p.add_argument("--base", help="base layer without the guide circles")
    p.add_argument("--anchored", help="the base with the circles, so leftovers can be removed")
    p.add_argument("--art-cap", type=float, default=0.25,
                   help="how much of a row's wave the artwork search may claim by "
                        "connectivity before it is treated as a repainted wave")
    p.add_argument("--halo", type=int, default=1,
                   help="seal the feathered ring the generator leaves inside the circles")
    p.add_argument("--halo-edge", type=float, default=15,
                   help="anything thinner than this, in poster pixels, is a feathered edge and not artwork")
    p.add_argument("--anchor-tol", type=float, default=20,
                   help="how different from the anchored base still counts as leftover circle")
    p.add_argument("--layout", help="the _layout.json the base wrote")
    p.add_argument("--caption-w", type=float, default=380)
    p.add_argument("--anchor-r", type=float, default=150, help="guide circle radius at 1536 wide; 0 disables")
    p.add_argument("--anchor-l", type=float, default=250)
    p.add_argument("--anchor-r-x", dest="anchor_r_x", type=float, default=1270)
    p.add_argument("--save-mask", help="write the detected mask here for reuse")
    p.add_argument("--mask-only", action="store_true")
    p.add_argument("--overlay", help="comma-separated modules in the calling folder that "
                                     "draw on top of each finished frame")
    # Two passes: the overlay has to be imported before it can add its own flags,
    # and it is named by one of the flags.
    overlays = load_overlays(p.parse_known_args()[0].overlay)
    for m in overlays:
        if hasattr(m, "add_arguments"):
            m.add_arguments(p)
    args = p.parse_args()

    img = Image.open(args.poster).convert("RGB")
    if args.autocrop:
        img = autocrop(img)
    if args.width:
        w0, h0 = img.size
        img = img.resize((args.width, round(h0 * args.width / w0)), Image.LANCZOS)
    W, H = img.size
    if W % 2 or H % 2:                          # h264 needs even dimensions
        img = img.crop((0, 0, W - (W % 2), H - (H % 2)))
        W, H = img.size
    arr = np.array(img).astype(np.float32)

    dbg = {}
    if args.mask:
        # An authored mask is pure geometry. The ribbon's colour, the row colours
        # and the food may all change from poster to poster; where the liquid is
        # does not, so the same file serves every one of them.
        mi = Image.open(args.mask).convert("L")
        if mi.size != (W, H):
            mi = mi.resize((W, H), Image.LANCZOS)
        mask = np.array(mi).astype(np.float32) / 255.0
        m2 = max(2, int(W * 0.03))
        left = np.median(arr[:, 1:1 + m2, :], axis=1); right = np.median(arr[:, W - m2 - 1:W - 1, :], axis=1)
        tt = (np.arange(W) / (W - 1))[None, :, None]
        diff = np.abs(arr - (left[:, None, :] * (1 - tt) + right[:, None, :] * tt)).max(axis=2)
        dbg.update(components=0, kept=int((mask > 0.5).any()), shapes=[])
        print(f"  mask loaded from {args.mask}")
    else:
        mask, diff = ribbon_mask(arr, args.x0, args.x1, args.y0, args.y1,
                                 args.tol, args.min_span, args.feather, dbg)
    if args.save_mask:
        Image.fromarray((mask * 255).astype(np.uint8)).save(args.save_mask)
        print(f"  mask written to {args.save_mask}")
    cover = mask.mean()
    print(f"poster {W}x{H}  |  {dbg['kept']} ribbons kept of {dbg['components']} blobs"
          f"  |  mask covers {cover*100:.1f}% of the frame")
    print(f"  kept w x h: {dbg['shapes']}")
    if cover < 0.005:
        print("  mask looks empty - lower --tol or --min-span", file=sys.stderr)
    if cover > 0.20:
        print("  mask looks greedy - raise --tol/--min-span or narrow --x0/--x1", file=sys.stderr)

    if args.mask_only:
        out = args.out.rsplit(".", 1)[0] + "_mask.png"
        Image.fromarray((mask * 255).astype(np.uint8)).save(out)
        print("wrote", out)
        return

    u = flow_coord(mask > 0.5)
    span = max(3, int(args.flatten_span * W) | 1)
    # Before base is derived from arr, not after: the guide marks have to be
    # gone from the array the whole render starts from, or they survive into
    # every frame no matter what is painted later.
    if args.anchored:
        # Wipe whatever is left of the guide circles before anything else looks at
        # the poster. Where the poster still equals the anchored base, the
        # generator did not cover that circle, and the clean base says what should
        # have been there.
        ai = Image.open(args.anchored).convert("RGB")
        if ai.size != (W, H):
            ai = ai.resize((W, H), Image.LANCZOS)
        anc = np.array(ai).astype(np.float32)
        bi = Image.open(args.base).convert("RGB")
        if bi.size != (W, H):
            bi = bi.resize((W, H), Image.LANCZOS)
        cb = np.array(bi).astype(np.float32)
        # 20 was too tight: the generator lays a faint tone over the circle while
        # covering it, which lifts the difference just past the threshold and the
        # ring stays visible behind the organ. An organ or a bowl differs by well
        # over a hundred, so there is room.
        d_anc = np.abs(arr - anc).max(axis=2)
        mark = np.abs(anc - cb).max(axis=2) > 3
        left = (d_anc < args.anchor_tol) & mark
        # Closing bridges the gaps between letter strokes and then the caption
        # itself gets painted out, so the strict test is applied again afterwards:
        # a pixel that differs from the anchored base is something drawn on top.
        left = ndimage.binary_closing(left, np.ones((7, 7)))
        left &= d_anc < args.anchor_tol
        arr[left] = cb[left]
        print(f"  {int(left.sum())} px of guide circle painted out")

        # Inside a circle the test above is all or nothing: a pixel either still
        # holds the untouched guide mark, and the clean base is put back, or it is
        # kept as the generator drew it. What the generator actually leaves is a
        # third thing - a feathered ring a few pixels wide where its patch fades
        # into the mark. That ring is neither restored nor animated, so it stays
        # as a dark cut straight across the wave, at every bowl and every organ.
        #
        # So inside a circle, what counts as covered is decided by size rather
        # than by an exact match. A bowl or an organ is a hundred pixels across
        # and survives an opening; an edge is a dozen and does not. What the
        # opening drops gets the clean base put back, which is what the design
        # says belongs there anyway.
        #
        # 15px, because the circle's own alpha ramp in recolor_base.py is 14: over
        # that ramp the anchored base is part tint and part wave while the poster
        # is all wave, so the difference clears anchor_tol on its own and the ring
        # reads as covered. Anything up to the width of that ramp is edge.
        if args.halo:
            circ = np.zeros((H, W), bool)
            if args.layout:
                Lg = json.load(open(args.layout))
                kk = W / 1536.0
                yy_, xx_ = np.mgrid[0:H, 0:W]
                for row in Lg["rows"]:
                    for cx0 in (Lg["anchor_l"], Lg["anchor_r"]):
                        circ |= np.hypot(xx_ - cx0 * kk, yy_ - row["cy"] * kk) < row["r"] * kk + 14 * kk
            if circ.any():
                k = max(3, int(round(args.halo_edge * W / 1536.0)) | 1)
                covered = ndimage.binary_opening(d_anc >= args.anchor_tol, np.ones((k, k)))
                covered = ndimage.binary_closing(covered, np.ones((k, k)))
                # Only along the ribbon's own footprint. An opening cannot tell a
                # feathered edge from thin artwork, and the first version took the
                # gallbladder's bile duct off with the ring. The seal exists so the
                # liquid runs unbroken into the bowl and the organ, so it has no
                # business anywhere the liquid does not go: outside the ribbon, a
                # duct, a vessel or a stalk is left alone.
                near = ndimage.binary_dilation(mask > 0.02, np.ones((9, 9)))
                ring = circ & mark & near & ~covered & ~left
                arr[ring] = cb[ring]
                print(f"  {int(ring.sum())} px of feathered edge sealed with the clean base")

    base = arr * (1 - args.flatten) + flatten_along_flow(arr, mask, span) * args.flatten
    bgsrc = None
    clean = None
    if args.base:
        bi = Image.open(args.base).convert("RGB")
        if bi.size != (W, H):
            bi = bi.resize((W, H), Image.LANCZOS)
        bgsrc = np.array(bi).astype(np.float32)
        # Cleaned before use. A raw threshold also fires on JPEG noise and
        # resampling error along the wave's own edge, and those pixels then get
        # left unpainted: they stand still in a speckled fringe while the wave
        # moves under them. Opening removes the specks, closing seals the
        # artwork's interior, and a small dilation covers its soft edge.
        # What counts as added artwork, and what is merely the generator having
        # repainted the wave. It does repaint them - glossier, more contrast - and
        # a plain difference test then calls a third of the liquid "artwork" and
        # leaves it standing still. A blob that lies inside the wave is the wave;
        # a blob that lies outside it is a bowl or an organ.
        diff_b = np.abs(arr - bgsrc).max(axis=2)
        # Colour difference alone misses a white bowl on a pale stripe - it is
        # nearly the colour the base already had there, so nothing flags it and
        # the liquid gets painted across its front. Detail finds it instead: the
        # bowl has a rim and contents, the flat stripe underneath has neither.
        gp = ndimage.gaussian_gradient_magnitude(arr.mean(axis=2), 2.0)
        gb = ndimage.gaussian_gradient_magnitude(bgsrc.mean(axis=2), 2.0)
        drawn = (gp > 6.0) & (gb < 3.0)
        cand = ndimage.binary_opening((diff_b >= 45) | drawn, np.ones((5, 5)))
        cand = ndimage.binary_closing(cand, np.ones((13, 13)))
        inside = ndimage.binary_dilation(mask > 0.4, np.ones((9, 9)))

        # Seed the search outside the wave. A bowl touches the liquid it pours,
        # so bowl and wave merge into one blob - and since the wave is the larger
        # part, the whole thing passes as "the wave was repainted" and the bowl
        # gets painted over: the liquid appears to run across its front. Taking
        # only what lies clear of the wave as the seed, then growing it back over
        # the overlap, keeps the two apart.
        seed = cand & ~inside
        lab_a, n_a = ndimage.label(seed)
        art = np.zeros_like(cand)
        for j in range(1, n_a + 1):
            blob = lab_a == j
            if blob.sum() > 800:
                art |= blob
        # Growing the seed back over the overlap by a fixed 41x41 reaches the
        # glass along the ribbon's two edges and stops short of its middle - the
        # centre of the band is ~74px from the nearest seed at 1080 wide. So a
        # slice of bowl rim lying across the middle of the wave is left unmarked,
        # is read as liquid surface, and the advection carries it downstream: it
        # surfaces about 0.2s in and travels at the wave's own speed. Measured on
        # two posters and ten rows, that slice is 6.5% to 8.3% of the row's wave.
        #
        # Connectivity inside cand reaches all of it, because the rim is one blob
        # with the bowl. What connectivity risks is the case the fixed dilation
        # was defending against: a poster whose wave the generator repainted,
        # where the whole ribbon is in cand and one component would swallow it.
        # So the growth is taken per row and only if it claims less than art-cap
        # of that row's wave - 6.5-8.3% against a cap of 25% is not a close call,
        # and a repainted wave is not a small one.
        fixed = ndimage.binary_dilation(art, np.ones((41, 41))) & cand
        grown = ndimage.binary_propagation(art, mask=cand)
        wave_px = mask > 0.4
        art = fixed | (grown & ~wave_px)
        lab_w, n_w = ndimage.label(wave_px)
        for j in range(1, n_w + 1):
            w = lab_w == j
            add = (grown & w & ~fixed).sum()
            if add <= args.art_cap * w.sum():
                art |= grown & w
            else:
                print(f"    row {j}: connectivity would claim {100 * add / w.sum():.0f}% of "
                      f"the wave, over the {100 * args.art_cap:.0f}% cap - kept the fixed growth")
        art = ndimage.binary_dilation(art, np.ones((5, 5)))
        # Artwork is solid, so a hole inside it is still artwork. Everything
        # above finds artwork by how far it is from the base or by how much
        # detail it carries, and a black singlet on a near-black row has
        # neither: on PULL DAY the athlete's disc was found, his skin was found,
        # and the liquid was then painted across his chest, because that patch
        # differed from the row by less than the threshold and was as flat as the
        # stripe it sat on. It is enclosed by the artwork around it, though, and
        # that is enough to know what it is - the same argument as the white bowl
        # on a pale stripe, which detail caught and colour did not.
        # Bounded, because binary_fill_holes fills any enclosed region and the
        # mask already contains both guide circles and all ten caption bars: if a
        # poster's artwork ever bridged the two circles of a row, the wave
        # between them would be an enclosed hole and would be filled - frozen,
        # silently. A hole worth filling is a patch inside one piece of artwork,
        # so it is smaller than a guide circle; the cap is the same fraction of a
        # row's wave that the growth above uses.
        holes = ndimage.binary_fill_holes(art) & ~art
        lab_h, n_h = ndimage.label(holes)
        if n_h:
            cap = args.art_cap * float(np.median([(lab_w == j).sum() for j in range(1, n_w + 1)]))
            for j in range(1, n_h + 1):
                h = lab_h == j
                if h.sum() <= cap:
                    art |= h

        # The bowl and the organ always sit on the guide circles - that is what
        # the circles are for. Where one covers the wave, the liquid underneath is
        # hidden anyway, and trying to work out the covered part from colour keeps
        # failing: a white bowl over a cream wave leaves blocks of paint across
        # its face. Simply never paint inside a circle.
        if args.layout:
            # Straight from the file the base wrote. The circles and the caption
            # bars are places the poster reserves for artwork and type, and
            # nothing painted belongs in either.
            L = json.load(open(args.layout))
            k = W / 1536.0
            yy, xx = np.mgrid[0:H, 0:W]
            for row in L["rows"]:
                cy, r = row["cy"] * k, row["r"] * k
                cap0, cap1 = row["cap_top"] * k, (row["cap_top"] + row["cap_h"]) * k
                for cx0 in (L["anchor_l"], L["anchor_r"]):
                    cx = cx0 * k
                    art |= np.hypot(xx - cx, yy - cy) < r + 12 * k
                    hw = args.caption_w * k / 2 + 12 * k
                    art |= ((np.abs(xx - cx) < hw) & (yy > cap0 - 12 * k) & (yy < cap1 + 12 * k))
        # The last word on what counts as artwork belongs to the variant, if it
        # wants it. What the two tests above find is a difference from the base or
        # a patch of detail, and both can miss: a white bowl on a pale stripe was
        # one case, a black singlet on a near-black row is the other, and the
        # liquid then paints across the front of something it should have run
        # behind. What the miss looks like, and what fixes it, is particular to
        # what a variant puts in its circles - so the mask is offered to the
        # overlay modules rather than guessed at harder here.
        for m in overlays:
            if hasattr(m, "refine_art"):
                art = m.refine_art(art, dict(W=W, H=H, layout=args.layout, mask=mask,
                                             base=bgsrc, poster=arr, args=args))
        clean = ~art
        print(f"  background read from {args.base}"
              f"  ({100 - clean.mean() * 100:.0f}% of the frame is new artwork)")
    geo = ribbon_geometry(mask > 0.5, base, args.gap, taper_right=args.reach <= 0, bgsrc=bgsrc)
    if args.reach > 0:
        geo = ribbon_reach(base, diff, geo, args.tol, args.anchor)
        solid = ndimage.binary_opening(diff > args.tol, np.ones((3, 3)))
        solid = ndimage.binary_closing(solid, np.ones((3, 3)))
        hit = sum(1 for g in geo if g.get('reach'))
        print(f"  {hit} ribbons reach an organ")
    print(f"  {len(geo)} ribbons with a movable silhouette")
    frames = int(round(args.seconds * args.fps))

    # One speed for everything. Rounding the cycle count separately for the
    # surface, the ripples and the droplets gave each its own rounded speed, and
    # they visibly disagreed. So the loop constraint is paid in wavelength: the
    # counts stay whole, the wavelengths bend to fit, and every part of the
    # picture moves at the same number of pixels per second.
    L_ref = float(np.mean([len(g["xs"]) for g in geo]))
    trav = max(1, round(args.speed * W * args.seconds / L_ref))
    speed = L_ref * trav / args.seconds
    dist = speed * args.seconds

    c1 = max(1, round(dist / (args.lam * W)))
    lam1 = dist / c1
    c2 = max(1, round(dist / (args.lam * W * 0.38)))
    lam2 = dist / c2
    cs = max(1, round(dist / (args.lam * W * 3.0)))
    print(f"  everything moves at {speed:.0f}px/s  |  ripples {lam1:.0f}px x{c1}, {lam2:.0f}px x{c2}")

    protect = protected_pixels(base, mask, geo)
    drops = find_droplets(base, diff, mask, geo, args.tol, protect) if args.drops else []
    if drops:
        drop_cycles = max(1, round(dist / (args.droplane * W)))
        lane = dist / drop_cycles
        drops = plan_droplets(drops, lane)
        print(f"  {len(drops)} droplets on a {lane:.0f}px run-up at "
              f"{lane * drop_cycles / args.seconds:.0f}px/s")
        base = erase_droplets(base, drops)
    print(f"  {protect.sum()} pixels of type and artwork pinned in place")
    # Read the wave's own appearance from the base layer: under the bowl the
    # poster holds glass and egg, and advecting that would carry them downstream.
    # The poster's own waves are what should be animated; the base only fills in
    # where a bowl or an organ sits on top of one.
    texsrc = base if bgsrc is None else np.where(clean[:, :, None], base, bgsrc)
    geo = ribbon_texture(texsrc, geo, edge=args.edge)
    trav = max(1, round(speed * args.seconds / max(np.mean([g['arc'][-1]-g['arc'][0] for g in geo]), 1)))
    print(f"  surface travels the ribbon {trav}x over the clip")
    for j, g in enumerate(geo, 1):
        L = g["x1"] - g["x0"]
        print(f"    r{j}: x {g['x0']}-{g['x1']} (len {L})  arc {g['arc'][-1]-g['arc'][0]:.0f}"
              f"  half-thickness mean {np.mean((g['bot']-g['top'])*0.5):.1f}"
              f"  waves across it {(g['arc'][-1]-g['arc'][0])/lam1:.2f}")
    n1, n2 = striations(H)
    mask3 = mask[:, :, None]

    plans = []
    if overlays:
        ctx = dict(W=W, H=H, fps=args.fps, seconds=args.seconds, frames=frames,
                   layout=args.layout, geo=geo, base=base, mask=mask,
                   curves=wave_centre_curves(geo, args.layout, W) if args.layout else None)
        for m in overlays:
            pl = m.build(args, ctx)
            if pl:
                plans.append((m, pl))

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(args.fps),
           "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", args.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    TAU = 2 * np.pi
    for f in range(frames):
        t = f / frames
        if args.mode == "wave":
            out = render_wave(base, geo, n1, n2, lam1, lam2, c1, c2, t,
                              args.amp, args.swell, args.snake, args.pad,
                              args.advect * trav * t, clean)
            if args.reach > 0:
                secs = f / args.fps
                p = min(1.0, secs / args.reach)
                front = p * p * (3 - 2 * p)              # ease in and out of the arrival
                for g in geo:
                    render_reach(out, base, solid, g, front)
        else:
            band = (0.55 * np.sin(TAU * (u / lam1 + n1 - c1 * t))
                    + 0.45 * np.sin(TAU * (u / lam2 + n2 - c2 * t)))
            sheen = np.sin(TAU * (u / (lam1 * 3.0) - cs * t))
            factor = (1.0 + args.amp * band + args.sheen * sheen)[:, :, None]
            out = base * (1.0 - mask3) + np.clip(base * factor, 0, 255) * mask3
        if drops:
            draw_droplets(out, drops, (drop_cycles * t) % 1.0)
        out[protect] = base[protect]
        # Last, and outside the protect pass: an overlay draws on the finished
        # frame, so nothing in the liquid pipeline has to know it exists.
        for m, pl in plans:
            m.draw(out, pl, f / args.fps)
        ff.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())

    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit("ffmpeg failed")
    print(f"wrote {args.out}  ({frames} frames, {args.seconds}s @ {args.fps}fps, seamless loop)")


if __name__ == "__main__":
    main()
