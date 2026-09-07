#!/usr/bin/env python3
"""
bodymap.py - the figure on the right of every row, and the muscles that light on it.

It is drawn here rather than generated for exactly the reason the wave is drawn
once and never regenerated: a model cannot draw the same anatomy twice. Five rows
whose bodies disagree about where the lats are is five different bodies, and the
comparison the whole clip is about - this lift hits that, the next one hits this
- is gone. So the body is authored, in normalised coordinates, and every poster
gets the same one.

    x   0 is the spine, positive is the figure's left, +-0.29 at the hands
    y   0 is the crown, 1 is under the feet

Two views. `front` and `back` share a silhouette - from a hundred pixels away a
person's outline is the same either way - and differ only in which muscles are
drawn on it. That is also why the silhouette is authored once: two silhouettes
would have drifted apart the first time either was touched.

The figure is a ghost - white on the dark rows, near-black on the light ones -
so the only saturated thing in the circle is the muscle that is working. At the
size a row gives it, about 300px tall, that contrast is the entire read.

    python3 bodymap.py --sheet work/body_sheet.png     # every muscle, both views
    python3 bodymap.py --view back --lit Lats:p,Biceps:s -o work/back.png
"""
import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import muscles

SS = 4                    # supersample; a 300px figure drawn straight is ragged


# ------------------------------------------------------------------ curves

def spline(pts, n=18, tau=0.34):
    """Closed Catmull-Rom through the control points.

    Authoring a deltoid as a polygon takes forty points and still reads as a
    polygon. Eight points and a spline through them reads as a muscle, and eight
    points is something that can be moved by hand.

    `tau` is the tension. At the textbook 0.5 the curve overshoots every tight
    corner and a pectoral comes out as a pill - the first draft of this file was
    a figure made entirely of lozenges. 0.34 still rounds the shape and stops
    bulging past the points it was given.
    """
    P = np.asarray(pts, np.float64)
    m = len(P)
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    t2, t3 = t * t, t * t * t
    h00 = 2 * t3 - 3 * t2 + 1
    h10 = t3 - 2 * t2 + t
    h01 = -2 * t3 + 3 * t2
    h11 = t3 - t2
    out = []
    for i in range(m):
        p0, p1, p2, p3 = P[(i - 1) % m], P[i], P[(i + 1) % m], P[(i + 2) % m]
        out.append(h00 * p1 + h10 * (tau * (p2 - p0))
                   + h01 * p2 + h11 * (tau * (p3 - p1)))
    return np.concatenate(out)


# ------------------------------------------------------------------ the figure
#
# A lifter, not a person: shoulders at +-0.20 against a waist at +-0.088, and a
# head a little under scale. Drawn at true proportions the figure reads as a
# pictogram off a toilet door, and the V-taper is the one thing that says at a
# glance that this clip is about training.

TORSO = [
    (0.048, 0.142), (0.092, 0.156), (0.134, 0.184), (0.140, 0.226),
    (0.135, 0.258), (0.120, 0.302), (0.100, 0.340), (0.088, 0.378),
    (0.098, 0.418), (0.122, 0.448), (0.130, 0.478), (0.112, 0.506),
    (0.000, 0.520), (-0.112, 0.506), (-0.130, 0.478), (-0.122, 0.448),
    (-0.098, 0.418), (-0.088, 0.378), (-0.100, 0.340), (-0.120, 0.302),
    (-0.135, 0.258), (-0.140, 0.226), (-0.134, 0.184), (-0.092, 0.156),
    (-0.048, 0.142),
]

NECK = [(0.038, 0.094), (0.044, 0.150), (-0.044, 0.150), (-0.038, 0.094)]

# One arm and one leg, authored for the figure's left and mirrored. Authoring
# both sides by hand is how they stopped matching.
ARM = [
    (0.108, 0.166), (0.160, 0.170), (0.198, 0.196), (0.208, 0.240),
    (0.212, 0.300), (0.228, 0.380), (0.248, 0.444), (0.258, 0.510),
    (0.262, 0.556), (0.248, 0.608), (0.222, 0.610), (0.214, 0.552),
    (0.208, 0.508), (0.196, 0.442), (0.176, 0.380), (0.158, 0.300),
    (0.146, 0.244), (0.136, 0.198),
]

LEG = [
    (0.132, 0.478), (0.138, 0.520), (0.130, 0.580), (0.112, 0.640),
    (0.088, 0.690), (0.094, 0.740), (0.090, 0.786), (0.070, 0.848),
    (0.048, 0.898), (0.072, 0.944), (0.028, 0.956), (0.014, 0.940),
    (0.018, 0.900), (0.030, 0.848), (0.042, 0.786), (0.038, 0.740),
    (0.036, 0.690), (0.028, 0.600), (0.018, 0.508),
]

HEAD = (0.000, 0.050, 0.044, 0.056)          # cx, cy, rx, ry

# The muscles. Every one is authored on the figure's left and mirrored, except
# `abs`, which crosses the centre line and would grow a seam down it.
#
# A muscle with an entry in both views is drawn twice, differently: what shows of
# the triceps from the front is the outer edge of the upper arm, not the head of
# the muscle, and drawing the back's shape on the front view puts a bicep-sized
# triceps where the biceps is. An empty list means it does not show from that
# side at all - the badge still lands and still sounds, only the body stays dark.
MIRRORED = True

FRONT = {
    "neck":        [(0.006, 0.100), (0.032, 0.104), (0.038, 0.142), (0.008, 0.145)],
    "traps":       [(0.038, 0.130), (0.098, 0.150), (0.152, 0.192),
                    (0.136, 0.208), (0.086, 0.182), (0.042, 0.162)],
    "chest":       [(0.020, 0.196), (0.086, 0.184), (0.126, 0.198),
                    (0.136, 0.226), (0.120, 0.256), (0.076, 0.272),
                    (0.030, 0.266), (0.018, 0.230)],
    "front_delt":  [(0.116, 0.172), (0.166, 0.174), (0.194, 0.206),
                    (0.192, 0.246), (0.164, 0.260), (0.130, 0.238),
                    (0.118, 0.200)],
    "side_delt":   [(0.166, 0.176), (0.198, 0.202), (0.202, 0.252),
                    (0.178, 0.266), (0.162, 0.228), (0.162, 0.192)],
    "lats":        [(0.112, 0.262), (0.132, 0.272), (0.124, 0.330),
                    (0.102, 0.352), (0.098, 0.300)],
    "serratus":    [(0.084, 0.268), (0.116, 0.276), (0.110, 0.318),
                    (0.086, 0.310)],
    "biceps":      [(0.152, 0.278), (0.192, 0.286), (0.204, 0.336),
                    (0.200, 0.384), (0.168, 0.380), (0.154, 0.324)],
    "triceps":     [(0.194, 0.278), (0.210, 0.302), (0.220, 0.356),
                    (0.210, 0.376), (0.200, 0.340), (0.196, 0.302)],
    "forearm":     [(0.180, 0.388), (0.218, 0.394), (0.244, 0.468),
                    (0.250, 0.516), (0.234, 0.532), (0.210, 0.474),
                    (0.188, 0.430)],
    "abs":         [(0.000, 0.274), (0.050, 0.288), (0.054, 0.350),
                    (0.044, 0.412), (0.000, 0.446), (-0.044, 0.412),
                    (-0.054, 0.350), (-0.050, 0.288)],
    "obliques":    [(0.058, 0.298), (0.100, 0.312), (0.094, 0.376),
                    (0.074, 0.424), (0.052, 0.396), (0.054, 0.340)],
    "hip_flexors": [(0.016, 0.436), (0.076, 0.446), (0.094, 0.482),
                    (0.034, 0.492), (0.012, 0.466)],
    "quads":       [(0.046, 0.510), (0.124, 0.502), (0.118, 0.578),
                    (0.096, 0.664), (0.056, 0.670), (0.038, 0.590)],
    "adductors":   [(0.016, 0.508), (0.048, 0.512), (0.042, 0.598),
                    (0.024, 0.634), (0.012, 0.570)],
    "calves":      [(0.038, 0.712), (0.090, 0.716), (0.086, 0.792),
                    (0.060, 0.848), (0.040, 0.790)],
    # The gluteus medius, which really is visible from the front at the outer
    # hip. Without it every squat, lunge and leg press lands a GLUTES badge over
    # a body where nothing happens - and a dead beat in a row of three is worse
    # than no badge at all.
    "glutes":      [(0.096, 0.426), (0.128, 0.448), (0.130, 0.492),
                    (0.106, 0.502), (0.092, 0.464)],
    "hamstrings":  [],
    "erectors":    [],
    "rhomboids":   [],
    "rear_delt":   [(0.116, 0.176), (0.132, 0.196), (0.134, 0.238),
                    (0.120, 0.234)],
}

BACK = {
    "neck":        [(0.006, 0.100), (0.032, 0.104), (0.038, 0.140), (0.008, 0.143)],
    "traps":       [(0.000, 0.128), (0.104, 0.154), (0.154, 0.194),
                    (0.114, 0.232), (0.054, 0.274), (0.000, 0.290)],
    "rhomboids":   [(0.010, 0.236), (0.076, 0.226), (0.092, 0.278),
                    (0.012, 0.290)],
    "lats":        [(0.024, 0.268), (0.104, 0.254), (0.134, 0.268),
                    (0.130, 0.312), (0.096, 0.362), (0.054, 0.394),
                    (0.026, 0.384)],
    "erectors":    [(0.006, 0.330), (0.060, 0.324), (0.076, 0.396),
                    (0.060, 0.442), (0.008, 0.448)],
    "rear_delt":   [(0.118, 0.174), (0.168, 0.178), (0.196, 0.210),
                    (0.192, 0.250), (0.162, 0.262), (0.130, 0.232)],
    "side_delt":   [(0.174, 0.182), (0.200, 0.208), (0.200, 0.252),
                    (0.182, 0.264), (0.172, 0.222)],
    "front_delt":  [(0.176, 0.184), (0.196, 0.208), (0.194, 0.244),
                    (0.178, 0.250)],
    "triceps":     [(0.154, 0.274), (0.196, 0.282), (0.212, 0.340),
                    (0.206, 0.384), (0.172, 0.380), (0.156, 0.320)],
    "biceps":      [(0.152, 0.282), (0.166, 0.302), (0.170, 0.354),
                    (0.160, 0.370), (0.152, 0.328)],
    "forearm":     [(0.180, 0.388), (0.218, 0.394), (0.244, 0.468),
                    (0.250, 0.516), (0.234, 0.532), (0.210, 0.474),
                    (0.188, 0.430)],
    "obliques":    [(0.076, 0.318), (0.106, 0.330), (0.098, 0.386),
                    (0.076, 0.424), (0.062, 0.386)],
    "serratus":    [(0.090, 0.276), (0.120, 0.286), (0.114, 0.322),
                    (0.092, 0.316)],
    "glutes":      [(0.008, 0.436), (0.098, 0.430), (0.128, 0.468),
                    (0.114, 0.518), (0.050, 0.532), (0.010, 0.510)],
    "hamstrings":  [(0.028, 0.546), (0.122, 0.536), (0.112, 0.618),
                    (0.090, 0.672), (0.046, 0.676), (0.030, 0.612)],
    "adductors":   [(0.016, 0.508), (0.048, 0.512), (0.042, 0.598),
                    (0.024, 0.634), (0.012, 0.570)],
    "calves":      [(0.036, 0.706), (0.094, 0.710), (0.090, 0.790),
                    (0.064, 0.852), (0.038, 0.792)],
    "chest":       [],
    "abs":         [],
    "hip_flexors": [],
    "quads":       [],
}

# Drawn in this order, so an overlap always resolves the same way. Deep muscles
# first, the ones that sit on top of them last.
ORDER = ["neck", "traps", "rhomboids", "erectors", "lats", "serratus", "chest",
         "obliques", "abs", "hip_flexors", "glutes", "adductors", "quads",
         "hamstrings", "calves", "side_delt", "rear_delt", "front_delt",
         "biceps", "triceps", "forearm"]


# ------------------------------------------------------------------ drawing

def _place(pts, W, H, top, height, mirror=False):
    """Normalised figure coordinates to pixels on a W x H canvas."""
    s = -1.0 if mirror else 1.0
    return [(W * 0.5 + s * x * height, top + y * height) for x, y in pts]


def _fill(draw, pts, W, H, top, height, colour, mirror_both=True):
    """One region, both sides. A region that crosses the centre line is drawn
    once - mirroring it would leave a seam down the sternum."""
    if not pts:
        return
    crosses = min(x for x, _ in pts) < -0.004
    sides = [False] if crosses or not mirror_both else [False, True]
    for m in sides:
        draw.polygon([tuple(p) for p in spline(_place(pts, W, H, top, height, m))],
                     fill=colour)


def _figure_mask(W, H, top, height):
    """The silhouette, as an alpha plane. Every muscle is clipped to it, which is
    what keeps a deltoid from spilling off the arm it was authored on."""
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    cx, cy, rx, ry = HEAD
    d.ellipse((W * 0.5 + (cx - rx) * height, top + (cy - ry) * height,
               W * 0.5 + (cx + rx) * height, top + (cy + ry) * height), fill=255)
    for pts in (NECK, TORSO):
        d.polygon([tuple(p) for p in spline(_place(pts, W, H, top, height))], fill=255)
    for part in (ARM, LEG):
        for m in (False, True):
            d.polygon([tuple(p) for p in spline(_place(part, W, H, top, height, m))],
                      fill=255)
    return im


def layers(view, size, tiers=None, light=False, height=None, top=None):
    """The body, and one RGBA plane per muscle that can light on it.

    Returned separately because they animate separately: the body is composited
    once and never changes, and a muscle plane is faded up on the frame its badge
    lands. Merging them would mean recompositing the whole figure every frame for
    the sake of one region.
    """
    tiers = tiers or {}
    W = H = int(size)
    h = float(height if height is not None else H * 0.94)
    t = float(top if top is not None else (H - h) * 0.5)
    Wq, Hq, hq, tq = W * SS, H * SS, h * SS, t * SS

    sil = _figure_mask(Wq, Hq, tq, hq)
    silf = np.array(sil).astype(np.float32) / 255.0

    ink = (255, 255, 255) if not light else (13, 19, 30)
    # Deliberately faint. The figure is a map, not a portrait: whatever is
    # working has to be the loudest thing in the circle, and at the size a row
    # gives the body that is a contrast question, not a size one. The first cut
    # drew the ghost at 0.20 and the lit muscle read as a detail on a statue.
    body_a, seam_a, line_a, edge_a = ((0.15, 0.22, 0.38, 0.60) if not light
                                      else (0.13, 0.20, 0.35, 0.54))

    # The unlit anatomy, in two parts. The fills say where the muscle is; the
    # lines between them are what makes it read as anatomy rather than as a
    # bruise. Filled alone, the chest, the serratus and the obliques run into one
    # another and the whole flank becomes a single pale smear - at three hundred
    # pixels the divisions are the only thing carrying the shape.
    defs = FRONT if view == "front" else BACK
    fill = Image.new("L", (Wq, Hq), 0)
    df = ImageDraw.Draw(fill)
    line = np.zeros((Hq, Wq), np.float32)
    er_k = 2 * max(1, int(SS * 0.9)) + 1
    for name in ORDER:
        pts = defs.get(name)
        if not pts:
            continue
        _fill(df, pts, Wq, Hq, tq, hq, 255)
        one = Image.new("L", (Wq, Hq), 0)
        _fill(ImageDraw.Draw(one), pts, Wq, Hq, tq, hq, 255)
        oa = np.array(one).astype(np.float32) / 255.0
        line = np.maximum(line, np.clip(
            oa - np.array(one.filter(ImageFilter.MinFilter(er_k))).astype(np.float32) / 255.0,
            0, 1))
    fillf = np.array(fill).astype(np.float32) / 255.0 * silf
    line *= silf

    rgb = np.zeros((Hq, Wq, 3), np.float32) + np.float32(ink)
    a = silf * body_a + fillf * (seam_a - body_a)
    a = np.maximum(a, line * line_a)

    # A rim, so a white ghost on a pale wave still has an outline. Drawn as the
    # silhouette minus an eroded copy of itself rather than as a stroke: PIL
    # strokes a spline as a chain of round caps and the joins show.
    er = np.array(sil.filter(ImageFilter.MinFilter(2 * max(1, int(SS * 1.3)) + 1))
                  ).astype(np.float32) / 255.0
    a = np.maximum(a, np.clip(silf - er, 0, 1) * edge_a)

    body = np.dstack([rgb, a * 255.0])
    body = np.array(Image.fromarray(np.clip(body, 0, 255).astype(np.uint8), "RGBA")
                    .resize((W, H), Image.LANCZOS)).astype(np.float32)

    out = {}
    for k, tier in tiers.items():
        m = Image.new("L", (Wq, Hq), 0)
        dm = ImageDraw.Draw(m)
        drew = False
        for name in muscles.regions(k):
            pts = defs.get(name)
            if pts:
                _fill(dm, pts, Wq, Hq, tq, hq, 255)
                drew = True
        if not drew:
            continue          # nothing of it shows from this side; the badge still lands
        mf = np.array(m).astype(np.float32) / 255.0 * silf
        col = np.float32(muscles.TIER[tier])
        # A darker rim inside the lit muscle. Two neighbours on the same tier are
        # the same red, and glutes lighting next to hamstrings without it is one
        # red mass across the back of the legs with no anatomy left in it. The
        # rim also lifts the muscle off whatever colour the wave is behind it.
        rim = np.clip(mf - np.array(m.filter(ImageFilter.MinFilter(er_k))
                                    ).astype(np.float32) / 255.0, 0, 1)
        rgbm = np.zeros((Hq, Wq, 3), np.float32) + col
        rgbm *= (1.0 - 0.58 * rim)[:, :, None]
        plane = np.dstack([rgbm, mf * 255.0])
        out[k] = np.array(Image.fromarray(np.clip(plane, 0, 255).astype(np.uint8), "RGBA")
                          .resize((W, H), Image.LANCZOS)).astype(np.float32)
    return body, out


def render(view, lit=None, size=512, light=False, **kw):
    """The finished picture, for looking at. The animator uses `layers`."""
    lit = lit or {}
    body, planes = layers(view, size, lit, light=light, **kw)
    im = Image.fromarray(np.clip(body, 0, 255).astype(np.uint8), "RGBA")
    for k in lit:
        if k in planes:
            im.alpha_composite(Image.fromarray(
                np.clip(planes[k], 0, 255).astype(np.uint8), "RGBA"))
    return im


# ------------------------------------------------------------------ cli

def sheet(path, size=190):
    names = [k for k in muscles.MUSCLES if k != "FULLBODY"]
    cols = 8
    rows = (len(names) * 2 + cols - 1) // cols
    cell = size + 22
    im = Image.new("RGB", (cols * cell, rows * cell), (16, 24, 38))
    d = ImageDraw.Draw(im)
    i = 0
    for k in names:
        for view in ("front", "back"):
            b = render(view, {k: muscles.MUSCLES[k][1]}, size)
            im.paste(b, ((i % cols) * cell + 11, (i // cols) * cell + 11), b)
            d.text(((i % cols) * cell + 14, (i // cols) * cell + 2),
                   f"{muscles.label(k)} {view[0]}", fill=(150, 165, 190))
            i += 1
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    im.save(path)
    print(f"  {i} figures -> {path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--view", choices=["front", "back"], default="front")
    p.add_argument("--lit", default="", help="'Chest:p,Triceps:s'")
    p.add_argument("--size", type=int, default=512)
    p.add_argument("--light", action="store_true", help="a light row: draw the ghost dark")
    p.add_argument("--sheet", nargs="?", const="work/body_sheet.png")
    p.add_argument("-o", "--out")
    a = p.parse_args()

    if a.sheet:
        sheet(a.sheet)
        return
    lit = dict(muscles.parse(s) for s in a.lit.split(",") if s.strip())
    if a.lit and not a.view:
        a.view = muscles.view_for(list(lit.items()))
    im = render(a.view, lit, a.size, light=a.light)
    out = a.out or "work/body.png"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    im.save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
