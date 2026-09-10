#!/usr/bin/env python3
"""meal.py - act two: the poster's five foods become one meal, in the app's own face.

Act one is a poster: photographed food, liquid, a number per row. Act two is the
product. It is drawn, not generated, for the same reason Longevity draws its
dials - nobody can photograph a progress ring, and a generator asked for one
returns something that looks like the app without being it, which is worse than
not showing it at all.

WHAT THE NUMBERS ARE MEASURED AGAINST, AND WHY IT IS NOT A GOAL

The app shows current against the user's own goal. A clip has no user, so a goal
on screen would be a goal for nobody - or worse, an implied recommendation, which
is the one thing this repository's health rules refuse everywhere else.

The reference intakes are the way out and they are the same thing every packet of
food in Europe already carries: EU Regulation 1169/2011, Annex XIII - 2000 kcal,
carbohydrate 260 g, protein 50 g, fat 70 g. They are not advice, they are the
labelling yardstick, and they are printed on screen as such. That gives the ring
and the three bars exactly the app's shape - a value, a reference, a proportion -
with nothing invented.

THE ONE ARITHMETIC A VIEWER CAN CHECK

The totals are summed from the portions in `foods.meal`, never carried
alongside them. Somebody will add four numbers on a phone; they have to get the
fifth.
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/Library/Fonts"

# EU Regulation 1169/2011, Annex XIII. Reference intakes for an average adult.
REFERENCE = {"kcal": 2000.0, "carbs": 260.0, "protein": 50.0, "fat": 70.0}
REF_NOTE = "reference intake, EU 1169/2011"

BG = (242, 242, 247)
CARD = (255, 255, 255)
INK = (0, 0, 0)
SUB = (142, 142, 147)
TRACK = (229, 229, 234)
BLUE = (0, 122, 255)
GREEN = (52, 199, 89)
RED = (255, 59, 48)
ORANGE = (255, 149, 0)
MACRO = {"carbs": BLUE, "protein": GREEN, "fat": RED}

S = 2                                   # supersample: draw at 2x, land at 1x

# The poster's own footer, pixel for pixel. Act two is drawn and act one is
# photographed, so the one thing that must be identical between them is the
# thing that is identical everywhere else in this repository: the wordmark. It
# is not redrawn in a similar font - it is the bottom of engine/base_layer.png,
# below the last row stripe (which ends at 2063+413=2476 of 2752), scaled.
BASE_LAYER = os.path.join(HERE, "..", "..", "engine", "base_layer.png")
_footer = None


def footer(W):
    """The dark band with the Healthness mark, cached at the width asked for."""
    global _footer
    if _footer is None or _footer.width != W:
        b = Image.open(BASE_LAYER).convert("RGB")
        strip = b.crop((0, 2476, b.width, b.height))
        h = round(strip.height * W / b.width)
        _footer = strip.resize((W, h), Image.LANCZOS)
    return _footer


def font(weight, size):
    return ImageFont.truetype(f"{FONTS}/SF-Pro-Display-{weight}.otf", int(size * S))


def ease(x):
    """Ease-out cubic. Everything that arrives, arrives on this."""
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def overshoot(x, amount=0.12):
    """A pop that goes slightly past and settles - the badge feel from act one."""
    x = max(0.0, min(1.0, x))
    e = ease(x)
    return e + amount * (1 - e) * (x ** 0.5) * (1 - x) * 4


def rounded(d, box, r, fill):
    d.rounded_rectangle([c * S for c in box], radius=r * S, fill=fill)


def shadow(img, box, r, blur=18, alpha=18, dy=6):
    """The app's cards sit on a very soft shadow; without it they float."""
    lay = Image.new("L", img.size, 0)
    ImageDraw.Draw(lay).rounded_rectangle(
        [(box[0]) * S, (box[1] + dy) * S, (box[2]) * S, (box[3] + dy) * S],
        radius=r * S, fill=alpha)
    lay = lay.filter(ImageFilter.GaussianBlur(blur * S / 3))
    img.paste(Image.new("RGB", img.size, (0, 0, 0)), (0, 0), lay)


def text(d, xy, s, f, fill, anchor="la"):
    d.text((xy[0] * S, xy[1] * S), s, font=f, fill=fill, anchor=anchor)


def ring(d, cx, cy, radius, width, frac, colour, track=TRACK):
    """The calorie ring: a track, an arc from twelve o'clock, and a round cap."""
    box = [(cx - radius) * S, (cy - radius) * S, (cx + radius) * S, (cy + radius) * S]
    d.ellipse(box, outline=track, width=int(width * S))
    if frac <= 0:
        return
    sweep = 360.0 * min(frac, 1.0)
    d.arc(box, -90, -90 + sweep, fill=colour, width=int(width * S))
    # the leading dot, exactly as the app draws its cap
    import math
    a = math.radians(-90 + sweep)
    hx, hy = cx + radius * math.cos(a), cy + radius * math.sin(a)
    rr = width * 0.62
    d.ellipse([(hx - rr) * S, (hy - rr) * S, (hx + rr) * S, (hy + rr) * S], fill=colour)


def bar(d, box, frac, colour):
    x0, y0, x1, y1 = box
    h = y1 - y0
    rounded(d, box, h / 2, TRACK)
    w = (x1 - x0) * max(0.0, min(1.0, frac))
    if w > h * 0.4:
        rounded(d, (x0, y0, x0 + w, y1), h / 2, colour)


class Plan:
    """The timeline. Every time in seconds from the first frame of act two."""

    def __init__(self, rows, tot, title="TODAY'S BOWL", seconds=7.5):
        self.rows, self.tot, self.title, self.seconds = rows, tot, title, seconds
        n = len(rows)
        self.settle = 0.35                      # the card arriving out of the flip
        self.food0, self.foodgap = 0.55, 0.42
        self.food_end = self.food0 + self.foodgap * (n - 1) + 0.45
        self.ring0 = self.food_end + 0.15
        self.ring_dur = 1.35
        self.chip0 = self.ring0 + 0.55
        self.chipgap = 0.16
        self.chip_dur = 0.75
        self.verdict = self.ring0 + self.ring_dur + 0.25

    def cues(self):
        """What act two's audio has to land on. Written to disk, never typed twice."""
        c = [self.food0 + self.foodgap * i for i in range(len(self.rows))]
        return {"foods": c, "ring": self.ring0, "verdict": self.verdict,
                "chips": [self.chip0 + self.chipgap * i for i in range(3)]}


# The layout is authored once, at this size, and delivered at whatever size is
# asked for. Every constant below - padding, row height, font size, ring radius -
# is a number of pixels at 1080x1920, so scaling them individually would mean
# thirty places to get right and one place to get wrong. A preview at 540 drew
# 1080-sized text on a 540-wide card and the food names ran through their own
# calorie figures; that is the whole reason this is a resize and not a scale.
LOGICAL = (1080, 1920)


def render(plan, t, W=1080, H=1920):
    LW, LH = LOGICAL
    img = Image.new("RGB", (LW * S, LH * S), BG)
    d = ImageDraw.Draw(img)

    f_title = font("Bold", 40)
    f_food = font("Semibold", 42)
    f_gram = font("Regular", 34)
    f_kcal = font("Semibold", 36)
    f_big = font("Bold", 132)
    f_of = font("Regular", 40)
    f_chip = font("Semibold", 30)
    f_cval = font("Bold", 54)
    f_cof = font("Regular", 28)
    f_note = font("Regular", 24)
    f_verd = font("Bold", 44)

    if plan.settle > 0 and t <= 0:
        return img.resize((W, H), Image.LANCZOS)

    text(d, (LW / 2, 96), plan.title, f_title, INK, anchor="ma")

    # ---- the column, measured from both ends ------------------------------
    # The footer is fixed at the bottom and the title at the top; everything
    # between is sized from what is left, so a five-food meal does not run into
    # the wordmark and a three-food one does not leave a hole where the fourth
    # row would have been.
    fb = footer(LW)
    foot_top = LH - fb.height
    pad, top = 54, 160
    rowh = 96
    n = len(plan.rows)
    listbox = (pad, top, LW - pad, top + 34 + rowh * n)
    shadow(img, listbox, 30)
    rounded(d, listbox, 30, CARD)
    for i, r in enumerate(plan.rows):
        tt = (t - (plan.food0 + plan.foodgap * i)) / 0.40
        if tt <= 0:
            continue
        k = overshoot(tt)
        y = top + 20 + rowh * i + rowh / 2 + (1 - k) * 26
        alpha = min(1.0, tt * 1.6)
        ink = tuple(int(BG[j] + (INK[j] - BG[j]) * alpha) for j in range(3))
        sub = tuple(int(BG[j] + (SUB[j] - BG[j]) * alpha) for j in range(3))
        text(d, (pad + 34, y), f"{r['grams']:.0f} g", f_gram, sub, anchor="lm")
        text(d, (pad + 150, y), r["name"], f_food, ink, anchor="lm")
        text(d, (LW - pad - 34, y), f"{r['kcal']:.0f} kcal", f_kcal, sub, anchor="rm")

    # ---- the ring, taking whatever the list left it -----------------------
    note_h, chip_h, gap = 76, 210, 30
    ringtop = listbox[3] + gap
    ring_h = max(560, foot_top - note_h - chip_h - gap * 3 - ringtop)
    ringbox = (pad, ringtop, LW - pad, ringtop + ring_h)
    if t > plan.ring0 - 0.3:
        shadow(img, ringbox, 30)
        rounded(d, ringbox, 30, CARD)
        cx, cy = LW / 2, ringtop + ring_h * 0.44
        rad, wid = min(214, ring_h * 0.31), 44
        p = ease((t - plan.ring0) / plan.ring_dur)
        frac = plan.tot["kcal"] / REFERENCE["kcal"] * p
        col = ORANGE if plan.tot["kcal"] > REFERENCE["kcal"] else GREEN
        ring(d, cx, cy, rad, wid, frac, col)
        shown = plan.tot["kcal"] * p
        text(d, (cx, cy - 34), f"{shown:,.0f}".replace(",", "."), f_big, INK, anchor="mm")
        text(d, (cx, cy + 66), f"/ {REFERENCE['kcal']:,.0f} kcal".replace(",", "."),
             f_of, SUB, anchor="mm")
        if t > plan.verdict:
            pct = 100 * plan.tot["kcal"] / REFERENCE["kcal"]
            v = ease((t - plan.verdict) / 0.4)
            vc = tuple(int(CARD[j] + (col[j] - CARD[j]) * v) for j in range(3))
            text(d, (cx, ringbox[3] - 62), f"{pct:.0f}% of a day", f_verd, vc, anchor="mm")

    # ---- the three chips --------------------------------------------------
    chiptop = ringbox[3] + gap
    cw = (LW - pad * 2 - 24) / 3
    for i, key in enumerate(("carbs", "protein", "fat")):
        tt = (t - (plan.chip0 + plan.chipgap * i)) / plan.chip_dur
        if tt <= 0:
            continue
        x0 = pad + i * (cw + 12)
        box = (x0, chiptop, x0 + cw, chiptop + chip_h)
        shadow(img, box, 26, blur=14, alpha=14)
        rounded(d, box, 26, CARD)
        val, ref = plan.tot[key], REFERENCE[key]
        k = ease(min(tt, 1.0))
        text(d, (x0 + 26, chiptop + 30), key.capitalize(), f_chip, SUB)
        text(d, (x0 + 26, chiptop + 78), f"{val * k:.0f}", f_cval, INK)
        wnum = d.textlength(f"{val * k:.0f}", font=f_cval) / S
        text(d, (x0 + 32 + wnum, chiptop + 100), f"/ {ref:.0f}g", f_cof, SUB)
        bar(d, (x0 + 26, chiptop + chip_h - 46, x0 + cw - 26, chiptop + chip_h - 34),
            val * k / ref, MACRO[key])

    text(d, (LW / 2, chiptop + chip_h + 26), REF_NOTE, f_note, SUB, anchor="ma")
    out = img.resize(LOGICAL, Image.LANCZOS)
    out.paste(fb, (0, foot_top))
    return out if (W, H) == LOGICAL else out.resize((W, H), Image.LANCZOS)


def main():
    import argparse
    import json
    import subprocess

    import foods

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--meal", required=True,
                    help="'200 Greek yogurt,80 Blueberries,20 Honey,60 Oats'")
    ap.add_argument("--title", default="TODAY'S BOWL")
    ap.add_argument("--seconds", type=float, default=7.5)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--cues", help="write the timeline here, for the audio to read")
    ap.add_argument("--first-frame", help="also save frame 0 here, for the flip")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()

    rows, tot = foods.meal(foods.parse_meal(a.meal))
    plan = Plan(rows, tot, a.title, a.seconds)
    if a.cues:
        json.dump(plan.cues(), open(a.cues, "w"), indent=1)

    n = int(round(a.seconds * a.fps))
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{a.width}x{a.height}", "-r", str(a.fps), "-i", "-",
         "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
    for i in range(n):
        im = render(plan, i / a.fps, a.width, a.height)
        if i == 0 and a.first_frame:
            im.save(a.first_frame)
        ff.stdin.write(im.tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg failed")
    e = tot["carbs"] * 4 + tot["protein"] * 4 + tot["fat"] * 9
    print(f"  act two: {n} frames, {len(rows)} foods, {tot['kcal']:.0f} kcal "
          f"({100 * tot['kcal'] / REFERENCE['kcal']:.0f}% of the reference intake); "
          f"macros account for {e:.0f} kcal ({100 * e / tot['kcal'] - 100:+.1f}%)")


if __name__ == "__main__":
    main()
