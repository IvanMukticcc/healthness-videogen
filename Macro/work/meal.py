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

# The goal is a PERSON, not a label. See dailygoal.py: the app computes it from
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
    BEHIND_W, BLUR, FROST, SAT, CARD_A, RIM_A, FOOT_A, SAFE_X,
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
                "land": self.land,
                "chips": [self.chip0 + self.chipgap * i for i in range(3)]}

    @property
    def land(self):
        """When the LAST THING ON SCREEN has finished arriving.

        Not `verdict`, which is when the "% of a day" line starts fading up, and
        not `verdict + 0.4`, which is when its alpha stops being recomputed. An
        ease-out spends its last quarter moving less than a level of 255, so the
        line looks finished well before the maths does: measured on its own band
        it goes 37 -> 146 at the cue and is still at 228 by the time it settles,
        0.29s later, with nothing after that.

        Solved rather than measured, so it holds if the fade length changes:
        alpha is `255 * ease(x)` and its last distinguishable step is at
        `ease(x) >= 254.5/255`, which for the cubic is x = 0.874.

        WHY THE RING NUMBER DOES NOT DECIDE THIS. It has the same crawl - the
        score is `round(v * ease(x))`, so a 444 kcal ring reaches its last digit
        at x = 0.896 and a 799 one later still - but it finishes before the
        verdict line even starts, because `verdict` is 0.25s past the end of the
        ring's own fill. In this variant the last word on screen is always the
        verdict, and it is always 0.874 of a fixed 0.4s fade after its cue.
        """
        return self.verdict + 0.4 * 0.874


# The layout is authored once, at this size, and delivered at whatever size is
# asked for. Every constant below - padding, row height, font size, ring radius -
# is a number of pixels at 1080x1920, so scaling them individually would mean
# thirty places to get right and one place to get wrong. A preview at 540 drew
# 1080-sized text on a 540-wide card and the food names ran through their own
# calorie figures; that is the whole reason this is a resize and not a scale.
LOGICAL = (1080, 1920)


def arrive(t, cue, dur=0.34):
    """A card coming in: `(scale, alpha)`, or None before its cue.

    EVERY CARD IN ACT TWO ARRIVES, INCLUDING THE FIRST. The turn hands over bare
    frosted glass and the cards land on it one at a time - that sequence is the
    whole shape of the act, and a card that is simply present at frame 0 is not
    early, it is missing from the sequence.

    The entrance is act one's badge feel: `overshoot` for the size so it goes a
    little past and settles, `ease` for the alpha so it is never a hard cut. Same
    curve for all three, because three cards that arrive differently read as
    three unrelated events rather than as one list being built.
    """
    tt = (t - cue) / dur
    if tt <= 0:
        return None
    return overshoot(min(tt, 1.0)), ease(min(tt, 1.0))


def grown(box, k, floor=0.94):
    """`box` scaled about its own centre - 94% at k=0, full size at k=1."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    f = floor + (1.0 - floor) * k
    return (cx + (x0 - cx) * f, cy + (y0 - cy) * f,
            cx + (x1 - cx) * f, cy + (y1 - cy) * f)


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
    # FRAME 0 IS BARE GLASS AND NOTHING IS ON IT.
    #
    # This is what the turn reveals: an empty frosted surface. Two attempts got
    # it wrong in opposite directions and both were mine. Handing the face over
    # with nothing and then fading the whole card in on top of it made the card
    # arrive twice. Making the panes furniture so they were there from frame 0
    # cured that and cost the sequence - three empty cards delivered at once,
    # which is the thing that made the act read as a list being built.
    #
    # The answer is neither: the glass is empty, and then the cards LAND on it,
    # one at a time, each one animating in and each one doing something the
    # moment it settles. The first card arrives like the other two, because a
    # first card that is simply already there is not first, it is absent.
    if plan.settle > 0 and t <= 0:
        return deliver()

    # ---- the column, measured from both ends ------------------------------
    # The footer is fixed at the bottom and the title at the top; everything
    # between is sized from what is left, so a five-food meal does not run into
    # the wordmark and a three-food one does not leave a hole where the fourth
    # row would have been.
    # SAFE_X, not 54. Act one has kept one fourteenth of the width clear since
    # the first prompt because that strip is what a vertical feed crops; act two
    # was authored at half that and the clips went out with Instagram's action
    # rail sitting on the Fat chip and the ring's right shoulder. The engine's
    # comment carries why 96 rather than the ~215 it would take to clear the rail
    # outright: that is a 43% narrower card, and the rail is asymmetric, so a
    # card that dodged it would read off-centre for everyone who never taps.
    pad, top = SAFE_X, 160
    rowh = 96
    n = len(plan.rows)
    listbox = (pad, top, LW - pad, top + 34 + rowh * n)
    # CARD ONE arrives at `settle`, a quarter second after the turn, and carries
    # the heading with it - the title is this card's, not the act's, and a
    # heading hanging over an empty surface before the first card lands is the
    # same "already there" fault one element smaller.
    c1 = arrive(t, plan.settle)
    if c1 is None:
        return deliver()
    k1, a1 = c1
    text(d, (LW / 2, 96), plan.title, f_title, INK[:3] + (int(255 * a1),), anchor="ma")
    shadow(img, grown(listbox, k1), 30, alpha=int(15 * a1))
    pane(d, grown(listbox, k1), 30, a1)
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
    # THE RING CARD ARRIVES. IT IS NOT FURNITURE, AND THIS WAS MY MISTAKE.
    #
    # The flip turns ONE card towards the viewer, and it is the list above. That
    # card must not arrive twice, because the turn already delivered it. This one
    # is below it and was never on the face, so nothing about it arrives twice
    # and it has no claim to being there from frame 0.
    #
    # Drawing it unconditionally put all three panes on screen empty at the turn
    # and destroyed the thing the user liked most - the cards coming in one at a
    # time. The rule generalised one step too far: "the flip already delivered
    # that card" is about the face, not about every pane in the act.
    #
    # The fade stays, and so does its 0.10 lead: this pane used to arrive by cut,
    # a 20.8 level step mid-act, and a pane that starts fading 0.42s before its
    # cue is ON SCREEN 0.42s before it, which is how the half-second between the
    # food and the ring got spent on the pane's own fade.
    c2 = arrive(t, plan.ring0)
    if c2 is not None:
        k2, ring_in = c2
        shadow(img, grown(ringbox, k2), 30, alpha=int(15 * ring_in))
        pane(d, grown(ringbox, k2), 30, ring_in)
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
    last_chip = 0.0
    cw = (LW - pad * 2 - 24) / 3
    for i, key in enumerate(("carbs", "protein", "fat")):
        tt = (t - (plan.chip0 + plan.chipgap * i)) / plan.chip_dur
        c3 = arrive(t, plan.chip0 + plan.chipgap * i)
        if c3 is None:                  # three chips, three cues, one at a time
            continue
        k3, a3 = c3
        last_chip = a3 if i == 2 else last_chip
        x0 = pad + i * (cw + 12)
        box = (x0, chiptop, x0 + cw, chiptop + chip_h)
        shadow(img, grown(box, k3), 26, blur=14, alpha=int(12 * a3))
        pane(d, grown(box, k3), 26, a3)
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
    # IT ARRIVES WITH THE CHIPS, because it is about the chips. These two lines
    # were drawn unconditionally, so they appeared the instant card one landed -
    # at full opacity, in one frame, under empty glass, about three seconds
    # before the three bars whose reference they name. A footnote that turns up
    # before the thing it annotates is not early, it is unexplained.
    #
    # No frame-difference check would have found this. Small grey type is under
    # the floor: on a held frame the codec alone moves a few hundred pixels by
    # four or five levels, so a threshold low enough to see the note is
    # measuring x264. It was found by asking the code when it draws.
    if last_chip > 0:
        nc = SUB[:3] + (int(SUB[3] * last_chip),)
        text(d, (LW / 2, chiptop + chip_h + 22),
             f"{plan.who['who']} · {plan.who['activity']} · {plan.who['goal']}",
             f_note, nc, anchor="ma")
        text(d, (LW / 2, chiptop + chip_h + 52),
             f"goal {plan.who['kcal']:.0f} kcal from BMR {plan.who['bmr']:.0f} "
             f"· Mifflin-St Jeor", f_note, nc, anchor="ma")
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
