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

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/Library/Fonts"

# EU Regulation 1169/2011, Annex XIII. Reference intakes for an average adult.
REFERENCE = {"kcal": 2000.0, "carbs": 260.0, "protein": 50.0, "fat": 70.0}
REF_NOTE = "reference intake, EU 1169/2011"

BG = (242, 242, 247)
CARD = (255, 255, 255)

# GLASS. Act two is not a screen that replaces the poster - it is a pane laid
# over it, and the liquid keeps moving underneath. Act one is a seamless loop,
# so continuing it behind the glass costs one decode and no extra render: frame
# (act1_frames + flip_frames + i) mod act1_frames is exactly where the wave
# would have been if it had never stopped.
#
# The backdrop is decoded at BEHIND_W and blown back up. It is about to be
# blurred past any detail that width could have carried, and 192 frames of
# 1080x1920 in memory is 1.2 GB against 74 MB at 270.
BEHIND_W = 270
BLUR = 7.5              # at BEHIND_W; ~30 at 1080
FROST = 0.34            # how far the blurred poster is pulled towards white
SAT = 1.75              # put back the colour the whitening takes out
CARD_A = 186            # the panes themselves, out of 255
RIM_A = 120             # and the hairline that makes a pane an edge
FOOT_A = 0.55           # the wordmark band, over the frost rather than instead of it
# 0.34 and 0.55 are where this stops being free. Below about 0.30 the panes lose
# the ground they need and the secondary text starts competing with whatever the
# wave is doing behind it; below about 0.45 on the band the wordmark itself goes
# grey, and the mark is the one thing in the frame that has to survive every
# setting. Measured on the band rather than judged: see flow.md.
INK = (0, 0, 0, 255)
SUB = (72, 72, 78, 205)          # darker than the app's grey: it sits on glass,
                                 # not on an opaque card, and 142 disappears

# THE TRACK IS LIGHT BECAUSE THE GLASS IS THIN. At FROST 0.62 it was
# (120, 120, 128, 42) and read as an empty ring - but 84% of what you were
# looking at was the pale pane behind it, not the track. At 0.34 the ground
# under the ring runs 111 to 238 and the track went with it: measured on
# breakfast's held frame, the darkest track fell to 112.7 against a value arc of
# 111.3. A separation of 1.3 levels where it had been 51.7, with only hue still
# telling the empty part of the ring from the full part.
#
# Alpha alone cannot fix that, which is the obvious move and the wrong one:
# (120, 120, 128) at 255 lands at 122.7, still 11.4 from the arc, because the
# track colour is itself nearly as dark as the green. The track has to be LIGHT
# and it has to hold. (228, 228, 236) at 120 measures darkest 167.6, separation
# 56.3 - just past the 51.7 it had before - and keeps 66.8 levels of spread
# around the circumference, so it still moves with the wave rather than sitting
# on the glass as a painted band.
TRACK = (228, 228, 236, 120)
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


def _walk(i, start, lo, hi):
    """Frame index `i` steps into a walk from `start`, bouncing within [lo, hi]."""
    if hi <= lo:
        return max(0, lo)
    span = hi - lo
    pos = (start - lo + i) % (2 * span)
    return lo + (pos if pos <= span else 2 * span - pos)


def behind_frames(path, width=BEHIND_W):
    """Every frame of act one, small. Decoded once, kept for the whole render."""
    import subprocess
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                         "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
                        capture_output=True, text=True).stdout.strip().split(",")
    sw, sh = int(pr[0]), int(pr[1])
    h = round(width * sh / sw / 2) * 2
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={width}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    n = len(raw) // (width * h * 3)
    return [Image.frombytes("RGB", (width, h), raw[i * width * h * 3:(i + 1) * width * h * 3])
            for i in range(n)], (width, h)


def frost(im, size):
    """One act-one frame turned into the pane you read through.

    Blur, then pull towards white, then put the saturation back. The order
    matters: whitening a blurred frame washes the liquid out to a grey ghost,
    and the colour is the only thing telling you what is behind the glass.
    """
    b = im.filter(ImageFilter.GaussianBlur(BLUR))
    b = Image.blend(b, Image.new("RGB", b.size, (255, 255, 255)), FROST)
    b = ImageEnhance.Color(b).enhance(SAT)
    return b.resize(size, Image.LANCZOS)


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


def rounded(d, box, r, fill, outline=None, width=0):
    d.rounded_rectangle([c * S for c in box], radius=r * S, fill=fill,
                        outline=outline, width=int(width * S))


def pane(d, box, r, a=1.0):
    """A sheet of glass: translucent white with a hairline lit edge.

    The hairline is not decoration. A pane at 168 alpha over a frosted poster
    has almost the same value as the frost around it, so without an edge the
    card has no boundary and the list looks like text floating on a smear. One
    pixel of brighter white is the whole difference between a pane and a stain.
    """
    if a <= 0.01:
        return
    rounded(d, box, r, (255, 255, 255, int(CARD_A * a)),
            outline=(255, 255, 255, int(RIM_A * a)), width=1.5)


def shadow(img, box, r, blur=18, alpha=15, dy=6):
    """A soft drop under each pane, painted into the RGBA layer it sits on."""
    lay = Image.new("L", img.size, 0)
    ImageDraw.Draw(lay).rounded_rectangle(
        [(box[0]) * S, (box[1] + dy) * S, (box[2]) * S, (box[3] + dy) * S],
        radius=r * S, fill=alpha)
    lay = lay.filter(ImageFilter.GaussianBlur(blur * S / 3))
    img.paste(Image.new("RGBA", img.size, (0, 0, 0, 255)), (0, 0), lay)


def text(d, xy, s, f, fill, anchor="la"):
    d.text((xy[0] * S, xy[1] * S), s, font=f, fill=fill, anchor=anchor)


def ring(d, cx, cy, radius, width, frac, colour, track=TRACK):
    """The calorie ring: a track, an arc from twelve o'clock, and round caps.

    THE CAP SITS ON THE STROKE'S CENTRELINE, NOT ON `radius`. PIL draws an arc's
    width INWARD from the bounding box, so a stroke of `width` on a box of
    `radius` has its centreline at `radius - width/2`. Placing the cap at
    `radius` puts it half a stroke too far out, and a cap of `width * 0.62`
    against a stroke of `width` is a fifth too wide on top of that. Both errors
    push the same way, which is why it read as a blob sliding off the end of the
    arc rather than as a rounded end.

    A round cap is a disc of exactly half the stroke width, centred on the
    centreline, at BOTH ends. The one at the start matters as much: without it
    twelve o'clock is a square edge, and a ring with one rounded end and one
    square one looks like a mistake even to someone who cannot say what is wrong.
    """
    import math
    box = [(cx - radius) * S, (cy - radius) * S, (cx + radius) * S, (cy + radius) * S]
    d.ellipse(box, outline=track, width=int(width * S))
    if frac <= 0:
        return
    sweep = 360.0 * min(frac, 1.0)
    d.arc(box, -90, -90 + sweep, fill=colour, width=int(width * S))

    rmid = radius - width / 2.0          # the centreline PIL actually strokes
    rr = width / 2.0                     # a cap is half the stroke, exactly
    for ang in (-90.0, -90.0 + sweep):
        a = math.radians(ang)
        hx, hy = cx + rmid * math.cos(a), cy + rmid * math.sin(a)
        d.ellipse([(hx - rr) * S, (hy - rr) * S, (hx + rr) * S, (hy + rr) * S],
                  fill=colour)


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


def render(plan, t, W=1080, H=1920, behind=None):
    """One frame. `behind` is an act-one frame; without one the pane is opaque grey."""
    LW, LH = LOGICAL
    size = (LW * S, LH * S)
    base = frost(behind, size) if behind is not None else Image.new("RGB", size, BG)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
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

    def deliver():
        out = Image.alpha_composite(base.convert("RGBA"), img).convert("RGB")
        out = out.resize(LOGICAL, Image.LANCZOS)
        # The glass runs the whole height, the wordmark band included. Pasted
        # opaque it ended the pane on a hard horizontal edge just above the logo,
        # which read as a strip stuck on rather than as the bottom of the same
        # sheet. Blended at FOOT_A the poster still moves through it and the mark
        # stays white on dark, which is the one thing that has to survive.
        strip = out.crop((0, foot_top, LOGICAL[0], LOGICAL[1]))
        out.paste(Image.blend(strip, fb, FOOT_A), (0, foot_top))
        return out if (W, H) == LOGICAL else out.resize((W, H), Image.LANCZOS)

    fb = footer(LW)
    foot_top = LH - fb.height
    if plan.settle > 0 and t <= 0:
        return deliver()

    text(d, (LW / 2, 96), plan.title, f_title, INK, anchor="ma")

    # ---- the column, measured from both ends ------------------------------
    # The footer is fixed at the bottom and the title at the top; everything
    # between is sized from what is left, so a five-food meal does not run into
    # the wordmark and a three-food one does not leave a hole where the fourth
    # row would have been.
    pad, top = 54, 160
    rowh = 96
    n = len(plan.rows)
    listbox = (pad, top, LW - pad, top + 34 + rowh * n)
    shadow(img, listbox, 30)
    pane(d, listbox, 30)
    for i, r in enumerate(plan.rows):
        tt = (t - (plan.food0 + plan.foodgap * i)) / 0.40
        if tt <= 0:
            continue
        k = overshoot(tt)
        y = top + 20 + rowh * i + rowh / 2 + (1 - k) * 26
        # Fading towards BG is what you do on an opaque card. On glass there is
        # no known colour to fade towards - the poster is moving behind it - so
        # the fade is in the alpha channel, which is what it always meant.
        alpha = min(1.0, tt * 1.6)
        ink = INK[:3] + (int(INK[3] * alpha),)
        sub = SUB[:3] + (int(SUB[3] * alpha),)
        text(d, (pad + 34, y), f"{r['grams']:.0f} g", f_gram, sub, anchor="lm")
        text(d, (pad + 150, y), r["name"], f_food, ink, anchor="lm")
        text(d, (LW - pad - 34, y), f"{r['kcal']:.0f} kcal", f_kcal, sub, anchor="rm")

    # ---- the ring, taking whatever the list left it -----------------------
    note_h, chip_h, gap = 76, 210, 30
    ringtop = listbox[3] + gap
    ring_h = max(560, foot_top - note_h - chip_h - gap * 3 - ringtop)
    ringbox = (pad, ringtop, LW - pad, ringtop + ring_h)
    # The ring pane FADES IN. It used to appear on one frame, which measured as a
    # 20.8 level step in the middle of the act - the same order as the backdrop
    # blink that was treated as a bug, and the largest thing in act two after the
    # card landing. The list pane is there from the start and the chips fade, so
    # this was the only element in the frame arriving by cut.
    ring_in = ease((t - (plan.ring0 - 0.42)) / 0.34)
    if ring_in > 0:
        shadow(img, ringbox, 30, alpha=int(15 * ring_in))
        pane(d, ringbox, 30, ring_in)
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
            vc = col + (int(255 * v),)
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
        shadow(img, box, 26, blur=14, alpha=12)
        pane(d, box, 26)
        val, ref = plan.tot[key], REFERENCE[key]
        k = ease(min(tt, 1.0))
        text(d, (x0 + 26, chiptop + 30), key.capitalize(), f_chip, SUB)
        text(d, (x0 + 26, chiptop + 78), f"{val * k:.0f}", f_cval, INK)
        wnum = d.textlength(f"{val * k:.0f}", font=f_cval) / S
        text(d, (x0 + 32 + wnum, chiptop + 100), f"/ {ref:.0f}g", f_cof, SUB)
        bar(d, (x0 + 26, chiptop + chip_h - 46, x0 + cw - 26, chiptop + chip_h - 34),
            val * k / ref, MACRO[key])

    text(d, (LW / 2, chiptop + chip_h + 26), REF_NOTE, f_note, SUB, anchor="ma")
    return deliver()


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
    ap.add_argument("--behind", help="act one's clip, seen through the glass")
    ap.add_argument("--behind-lo", type=int, default=0,
                    help="the earliest act-one frame the backdrop may use. Every "
                         "frame from the finale on carries all fifteen badges, so "
                         "a window starting there cannot step in content")
    ap.add_argument("--behind-offset", type=int, default=0,
                    help="which act-one frame sits under act two's first. Act one "
                         "loops seamlessly, so this is (act1 frames + flip frames) "
                         "and the liquid carries on as if it had never stopped")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()

    rows, tot = foods.meal(foods.parse_meal(a.meal))
    plan = Plan(rows, tot, a.title, a.seconds)
    if a.cues:
        json.dump(plan.cues(), open(a.cues, "w"), indent=1)

    n = int(round(a.seconds * a.fps))

    bg, bgsize = (None, None)
    if a.behind:
        bg, bgsize = behind_frames(a.behind)
        lo, hi = a.behind_lo, len(bg) - 1
        span = max(1, hi - lo)
        bounces = (n + (a.behind_offset - lo)) // span
        print(f"  behind the glass: {len(bg)} frames of act one at "
              f"{bgsize[0]}x{bgsize[1]}, from {a.behind_offset}, bouncing in "
              f"[{lo}, {hi}] - {span} frames, {bounces} reversals over the act")
        if span < 24:
            print(f"    WINDOW IS {span} FRAMES. Under about a second the backdrop "
                  f"stops reading as the liquid carrying on and starts reading as "
                  f"a texture wobbling. Trim act one less, or lower --behind-lo.")

    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{a.width}x{a.height}", "-r", str(a.fps), "-i", "-",
         "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
    for i in range(n):
        # PING-PONGED INSIDE A WINDOW, not wrapped and no longer merely clamped.
        #
        # Act one is still rendered at its full length; only the part of it that
        # is SHOWN gets trimmed, so frames past the trim are still on hand as
        # backdrop. Even so, act two is longer than what is left, so the walk
        # bounces between `--behind-lo` and the last frame.
        #
        # WHY IT MAY NOT WRAP. Act one loops in LIQUID - flowanim guarantees the
        # surface travels the ribbon exactly once - but it does not loop in
        # CONTENT: the badges accumulate over the eight seconds and never reset,
        # so frame 0 has five bare rings where frame 191 has fifteen badges, five
        # filled arcs and the finale. Measured, frame 0 against frame 191: mean
        # 14.27, 14.19% of the frame different.
        #
        # 14 + 180 overshoots 192 by two, so a modulo put act one's frame 0 under
        # act two's second-to-last frame and every coloured bloom behind the
        # frost blinked out at 15.96s of a 16 second clip - 5.30% of the frame
        # over 20 levels, against neighbouring steps of 0.004 to 0.012. Two
        # hundred times the normal step, on the held ending, where nothing else
        # is moving at all.
        #
        # Holding the last frame instead costs a two-frame freeze of a backdrop
        # that is already moving about 0.011 mean per step under heavy blur at
        # 270 wide. The freeze is invisible; the blink was the only thing moving.
        # WHY IT MAY BOUNCE. A bounce reverses the liquid's direction, which on
        # an un-blurred surface is the most visible artefact in animation. Here
        # it is the same 0.011 mean per step that makes the moving backdrop
        # nearly free in the first place - one measurement, two uses, and the
        # second is why the reversal cannot be seen.
        b = bg[_walk(i, a.behind_offset, a.behind_lo, len(bg) - 1)] if bg else None
        im = render(plan, i / a.fps, a.width, a.height, behind=b)
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
