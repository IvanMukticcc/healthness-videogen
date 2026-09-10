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
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/Library/Fonts"

# The goal is a PERSON, not a label. See profile.py: the app computes it from
# body and intent, and a clip measuring the same food against the EU reference
# intake would be advertising a product it disagrees with. The default profile
# is stated on screen and overridable from render.sh.
DEFAULT_PROFILE = dict(weight_kg=66, height_cm=172, age=30, sex="male",
                       activity="light", goal="mild_gain")

# The surface is the engine's. It was this file's until 10 September, when Micro
# became the second variant to lay a card over a poster - same promotion rule as
# flip.py, and the same reason: two generations of the same drawing code in one
# repository is what engine/ exists to prevent.
#
# Imported by name rather than used as `glass.pane(...)` so that the body of
# render() below did not have to change at all. A mechanical move should be
# provable byte-for-byte, and a diff that also rewrites two hundred call sites
# cannot be.
sys.path.insert(0, os.path.join(HERE, "..", "..", "engine"))
from glass import (                                                # noqa: E402
    BG, CARD, INK, SUB, TRACK, BLUE, GREEN, RED, ORANGE, S,
    BEHIND_W, BLUR, FROST, SAT, CARD_A, RIM_A, FOOT_A,
    behind_frames, frost, footer, font, ease, overshoot,
    rounded, pane, shadow, text, ring, bar, walk as _walk,
)

MACRO = {"carbs": BLUE, "protein": GREEN, "fat": RED}

class Plan:
    """The timeline. Every time in seconds from the first frame of act two."""

    def __init__(self, rows, tot, title="TODAY'S BOWL", seconds=7.5, who=None):
        self.rows, self.tot, self.title, self.seconds = rows, tot, title, seconds
        self.who = who or __import__("dailygoal").goals(**DEFAULT_PROFILE)
        n = len(rows)
        self.settle = 0.35                      # the card arriving out of the flip
        self.food0, self.foodgap = 0.55, 0.42
        self.food_end = self.food0 + self.foodgap * (n - 1) + 0.45
        # Half a second between the three things, which is what was asked for and
        # is also about as short as a beat can be and still read as one.
        self.ring0 = self.food_end + 0.5
        self.ring_dur = 1.35
        self.chip0 = self.ring0 + 0.5
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
    # The lead is 0.10, not 0.42. A pane that starts fading 0.42s before its cue
    # is ON SCREEN 0.42s before its cue, so the half-second the user asked for
    # between the food and the ring was being spent on the pane's own fade and
    # measured 0.13s. The cue is when the arc moves; the card only needs to be
    # there a moment before it, not most of a beat before it.
    ring_in = ease((t - (plan.ring0 - 0.10)) / 0.30)
    if ring_in > 0:
        shadow(img, ringbox, 30, alpha=int(15 * ring_in))
        pane(d, ringbox, 30, ring_in)
        cx, cy = LW / 2, ringtop + ring_h * 0.44
        rad, wid = min(214, ring_h * 0.31), 44
        p = ease((t - plan.ring0) / plan.ring_dur)
        frac = plan.tot["kcal"] / plan.who["kcal"] * p
        col = ORANGE if plan.tot["kcal"] > plan.who["kcal"] else GREEN
        ring(d, cx, cy, rad, wid, frac, col)
        shown = plan.tot["kcal"] * p
        text(d, (cx, cy - 34), f"{shown:,.0f}".replace(",", "."), f_big, INK, anchor="mm")
        text(d, (cx, cy + 66), f"/ {plan.who['kcal']:,.0f} kcal".replace(",", "."),
             f_of, SUB, anchor="mm")
        if t > plan.verdict:
            pct = 100 * plan.tot["kcal"] / plan.who["kcal"]
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
        val, ref = plan.tot[key], plan.who[key]
        k = ease(min(tt, 1.0))
        text(d, (x0 + 26, chiptop + 30), key.capitalize(), f_chip, SUB)
        text(d, (x0 + 26, chiptop + 78), f"{val * k:.0f}", f_cval, INK)
        wnum = d.textlength(f"{val * k:.0f}", font=f_cval) / S
        text(d, (x0 + 32 + wnum, chiptop + 100), f"/ {ref:.0f}g", f_cof, SUB)
        bar(d, (x0 + 26, chiptop + chip_h - 46, x0 + cw - 26, chiptop + chip_h - 34),
            val * k / ref, MACRO[key])

    # WHO THE GOAL BELONGS TO. This is load-bearing and not a caption.
    #
    # It replaced "reference intake, EU 1169/2011", which was defensible for a
    # reason that has now gone: 2000 kcal is a printed labelling constant and
    # belongs to nobody, so "40% of a day" was a fact about a packet. A goal
    # computed from 172 cm and 66 kg is a statement about a PERSON, and the only
    # thing standing between "34% of a day" and an implied recommendation to
    # whoever is watching is this line naming who it was computed for.
    #
    # So it does not get shortened for space, dropped to fit a longer meal, or
    # covered by anything. If act two's layout is ever tightened, tighten
    # something else. macro-c1's point, and it is the right one.
    text(d, (LW / 2, chiptop + chip_h + 22),
         f"{plan.who['who']} · {plan.who['activity']} · {plan.who['goal']}",
         f_note, SUB, anchor="ma")
    text(d, (LW / 2, chiptop + chip_h + 52),
         f"goal {plan.who['kcal']:.0f} kcal from BMR {plan.who['bmr']:.0f} "
         f"· Mifflin-St Jeor", f_note, SUB, anchor="ma")
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
    ap.add_argument("--sex", default=DEFAULT_PROFILE["sex"])
    ap.add_argument("--age", type=int, default=DEFAULT_PROFILE["age"])
    # --body-* rather than --height/--weight: this file already has --width and
    # --height for the frame, and argparse rejected the collision loudly, which
    # is the only reason it took one run instead of a confusing render.
    ap.add_argument("--body-height", type=float, default=DEFAULT_PROFILE["height_cm"])
    ap.add_argument("--body-weight", type=float, default=DEFAULT_PROFILE["weight_kg"])
    ap.add_argument("--activity", default=DEFAULT_PROFILE["activity"])
    ap.add_argument("--goal", default=DEFAULT_PROFILE["goal"])
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

    import dailygoal as prof
    who = prof.goals(a.body_weight, a.body_height, a.age, a.sex, a.activity, a.goal)
    rows, tot = foods.meal(foods.parse_meal(a.meal))
    plan = Plan(rows, tot, a.title, a.seconds, who)
    print(f"  goal: {who['who']} · {who['activity']} · {who['goal']} -> "
          f"{who['kcal']:.0f} kcal, C {who['carbs']:.0f} P {who['protein']:.0f} "
          f"F {who['fat']:.0f}")
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
          f"({100 * tot['kcal'] / who['kcal']:.0f}% of the day); "
          f"macros account for {e:.0f} kcal ({100 * e / tot['kcal'] - 100:+.1f}%)")


if __name__ == "__main__":
    main()
