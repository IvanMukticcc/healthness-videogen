#!/usr/bin/env python3
"""
micro_card.py - act two: what act one's five foods add up to.

Act one is the poster: five foods, five organs, the badges popping. The card
turns over and act two answers the question act one raises - if you ate these,
what did you actually get? The numbers are `micro_result.py`'s, which are the
app's; this file only puts them on glass.

    python3 micro_card.py --topic pressure --still preview.png
    python3 micro_card.py --topic pressure --behind ../work/pressure_silent.mp4 \\
        --seconds 7.0 -o act2.mp4 --cues pressure_act2.json

WHAT IS THE APP'S AND WHAT IS MINE

The ring is the app's `MicroSegmentedRing`, mirrored rather than approximated:
eighteen segments in `MicronutrientType.displayOrder` (the ten vitamins, then
the five minerals, then fibre, sugar and sodium), 3 degrees of gap, so 17
degrees of arc each, starting at twelve o'clock, butt caps. A segment's track is
its own colour at 0.18 - and at **0.08 when the nutrient is unknown**, which is
the app refusing to let "nobody measured this" look like "you got none of it".
A limit nutrient over its goal turns **red**, which is the only place the ring
says something is wrong.

The three family colours are `micro_icons.py`'s rather than the app's raw
tokens. They are the same three sampled off the same screen, and using them here
means the badge that pops on a row in act one and the arc that fills for it in
act two are the identical blue, green and orange.

WHAT THE NUMBER IS, AND THE LINE UNDER IT

The score is the app's: the mean of min(progress, 1) over the sixteen target
nutrients, minus 0.1 for every limit blown, floored at zero. It is computed over
all sixteen even though the card lists seven, because an average of what
happened to fit on screen is not the app's number any more.

Against a whole day's goals five foods score low - 17% for BLOOD PRESSURE, 36%
for AGE SLOWER, 44% for STRESS RELIEF - and that is honest rather than harsh:
the plate is a third of the day's potassium and none of its vitamin D. So the
score carries a line saying what it is a score of. The app does the same thing
with its own footnote about coverage; a number this size needs its denominator
in the same breath or it reads as a grade.
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw

import micro_result as mr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "engine"))
from glass import (                                                # noqa: E402
    BG, INK, SUB, TRACK, RED, S, FOOT_A, SAFE_X,
    behind_frames, frost, footer, font, ease, overshoot,
    rounded, pane, shadow, text, walk as _walk,
)

# MicronutrientType.displayOrder: grouped, and inside a group in the enum's own
# order. Ten, then five, then three.
ORDER = ([t for t in mr.TYPES if t[2] == mr.VIT]
         + [t for t in mr.TYPES if t[2] == mr.MIN]
         + [t for t in mr.TYPES if t[2] == mr.OTH])
GAP_DEG = 3.0
SEG_DEG = 360.0 / len(ORDER) - GAP_DEG          # 17 degrees

LOGICAL = (1080, 1920)

# English, because act one's captions are: BEETROOT|NITRATES and a Croatian card
# behind it would be two languages in eight seconds. The app's own screen says
# "Mikro rezultat"; --lang hr prints that instead, for a Croatian cut.
STRINGS = {
    "en": {"head": "MICRONUTRIENTS", "score": "MICRO SCORE",
           "under": "five foods, not a whole day",
           "vit": "VITAMINS", "min": "MINERALS", "oth": "FIBRE & THE REST"},
    "hr": {"head": "MIKRONUTRIJENTI", "score": "MIKRO REZULTAT",
           "under": "pet namirnica, ne cijeli dan",
           "vit": "VITAMINI", "min": "MINERALI", "oth": "VLAKNA I OSTALO"},
}


class Plan:
    """Act two's timeline. Every time in seconds from its first frame.

    A cue is when the thing is READ, not when it starts arriving: the rows fade
    over 0.3s, so a row cued at 0.55 is legible at about 0.85 and the sound goes
    with the second number. Macro learned this the expensive way - a pane that
    began fading 0.42s before its cue was on screen half a second early and the
    beat the user asked for measured 0.13.
    """

    def __init__(self, res, seconds=7.0, lang="en"):
        self.res, self.seconds, self.lang = res, seconds, lang
        self.rows = self.pick(res)
        # WHAT THE TURN HANDS OVER IS GLASS, NOT A CARD.
        #
        # This file used to draw the list pane at frame 0 and only slide it 26px,
        # on the reasoning that the flip had just delivered that card so nothing
        # on it should arrive twice. The user's answer is better: the turn should
        # not show the card at all. It delivers the frost, and the cards land on
        # it - so nothing arrives twice because nothing was there. Frame 0 is bare
        # frosted glass, and every card animates on, the first one included.
        self.title0 = 0.10
        self.card1, self.card_dur = 0.25, 0.26
        self.row0 = self.card1 + self.card_dur + 0.12
        self.rowgap, self.rowdur = 0.26, 0.28
        self.row_end = self.row0 + self.rowgap * (len(self.rows) - 1) + self.rowdur
        # Half a second after the last row settles the second card lands, and
        # then its arc fills. Each card does something as soon as it arrives.
        self.pane2 = self.row_end + 0.50
        self.ring0 = self.pane2 + self.card_dur + 0.10
        self.ring_dur = 1.30
        self.score0 = self.ring0 + 0.30          # the number counts with the arc
        self.under0 = self.ring0 + self.ring_dur + 0.20

    @staticmethod
    def pick(res):
        """Seven of eighteen: the three biggest vitamins, the three biggest
        minerals, and fibre - plus any limit that is blown, because a red arc
        with nothing naming it is a puzzle. The score stays over all sixteen."""
        ls = res["lines"]
        def top(group, n):
            got = [l for l in ls if l["group"] == group and l["kind"] == mr.TARGET]
            return sorted(got, key=lambda l: -l["pct"])[:n]
        rows = top(mr.VIT, 3) + top(mr.MIN, 3)
        rows += [l for l in ls if l["key"] == "fiber"]
        rows += [l for l in ls if l["kind"] == mr.LIMIT and l["pct"] > 1]
        return rows

    def cues(self):
        """What act two's sound lands on. Written to disk, never typed twice."""
        return {"rows": [self.row0 + self.rowgap * i for i in range(len(self.rows))],
                "cards": [self.card1, self.pane2],
                "ring": self.ring0, "ring_dur": self.ring_dur,
                "score": self.score0, "under": self.under0, "seconds": self.seconds}


def segmented_ring(d, cx, cy, radius, width, values, frac=1.0, track_a=1.0):
    """The app's MicroSegmentedRing.

    `values` is one entry per nutrient in ORDER: None for unknown, otherwise
    (progress, colour, is_over_limit). `frac` sweeps the whole ring on, segment
    by segment, so the fill arrives the way the app animates it rather than all
    at once.
    """
    box = [(cx - radius) * S, (cy - radius) * S, (cx + radius) * S, (cy + radius) * S]
    n = len(values)
    for i, v in enumerate(values):
        start = i * (SEG_DEG + GAP_DEG) - 90
        colour = v[1] if v else (140, 140, 150)
        # Track. Unknown sits at 0.08, known at 0.18: "nobody measured this" may
        # not look like "you got none of it".
        a = (0.08 if v is None else 0.18) * track_a
        if a <= 0.005:
            continue
        d.arc(box, start, start + SEG_DEG,
              fill=tuple(colour) + (int(255 * a),), width=int(width * S))
    for i, v in enumerate(values):
        if not v:
            continue
        pct, colour, over = v
        if pct <= 0:
            continue
        # Each segment's own share of the sweep, so the ring fills clockwise.
        step = min(max(frac * n - i, 0.0), 1.0)
        if step <= 0:
            continue
        start = i * (SEG_DEG + GAP_DEG) - 90
        span = SEG_DEG * min(pct, 1.0) * step
        if span < 0.4:
            continue
        d.arc(box, start, start + span,
              fill=(RED if over else tuple(colour)) + (255,), width=int(width * S))


def fade(t, at, dur=0.30):
    return 0.0 if t < at else ease(min((t - at) / dur, 1.0))


def enter(t, at, dur=0.26):
    """A card arriving: 0 before `at`, then up to 1 with a small overshoot.

    `glass.overshoot` is the badges' own curve from act one, so both acts have
    the same hand - a thing that arrives goes slightly past its size and settles
    back rather than easing politely into place.
    """
    if t < at:
        return 0.0
    return overshoot(min((t - at) / dur, 1.0))


def grow(box, k, lo=0.94):
    """The box at `k` of its way in, scaled about its own centre."""
    sc = lo + (1.0 - lo) * k
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = (x1 - x0) * sc / 2, (y1 - y0) * sc / 2
    return (cx - w, cy - h, cx + w, cy + h)


def over(img, fn):
    """Draw one element ON TOP of what is already there, rather than instead of it.

    `ImageDraw` does not composite: drawing white at alpha 166 over a pane at 186
    REPLACES those pixels with 166, so a header sheet meant to hide act one's
    title made that band more transparent than the card around it - measured, the
    ghost went from 14.4 levels to 18.9 when the sheet was added. Every element
    here that carries alpha and sits over the pane has the same fault: the bar
    tracks at 120 and the ring's own tracks at 46 were cutting windows in the
    card and showing more of the poster, not less.

    So each of them is drawn into its own transparent layer and composited. The
    layers are grouped - all the tracks in one, all the fills in another - rather
    than one per shape, because each is a full-size RGBA allocation and there are
    168 frames of them.
    """
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(lay))
    img.alpha_composite(lay)


def render(plan, t, W=1080, H=1920, behind=None):
    """One frame of act two.

    THE COLUMN IS MEASURED FROM BOTH ENDS, NOT LAID OUT FROM THE TOP.

    The number of rows varies - seven, plus a row for any limit the plate blew -
    so a fixed ring position leaves a hole under a short list and collides with a
    long one. The title is pinned at the top and the wordmark band at the bottom;
    the list pane takes exactly what its rows need, and the ring pane takes what
    is left, with a floor so a long list can never squeeze it into a stripe. The
    ring is then centred IN ITS OWN BOX rather than at a fixed y, which is what
    makes both cases look deliberate rather than lucky.
    """
    LW, LH = LOGICAL
    size = (LW * S, LH * S)
    base = frost(behind, size) if behind is not None else Image.new("RGB", size, BG)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    st = STRINGS[plan.lang]
    res = plan.res

    f_title = font("Bold", 50)
    f_head = font("Semibold", 28)
    f_grp = font("Semibold", 26)
    f_row = font("Semibold", 40)
    f_val = font("Regular", 34)
    f_big = font("Bold", 150)
    f_lbl = font("Semibold", 34)
    f_note = font("Regular", 28)

    # SAFE_X, not 54. Act one has kept one fourteenth of the width clear since
    # the first prompt was written; act two was authored at 54 on 1080, which is
    # half that, and on a phone Instagram's action rail sat on the outer edge of
    # every card. It is the engine's number because both variants had it wrong.
    x0, x1 = SAFE_X, LW - SAFE_X
    ta = fade(t, plan.title0, 0.28)
    k1 = enter(t, plan.card1, plan.card_dur)          # the list card arriving
    rise = 0.0

    fb = footer(LW)
    foot_top = LH - fb.height

    # The title sits ON THE FROST, above the card, and it has to sit ABOVE act
    # one's own title band: the poster's heading occupies video y 143-274 and
    # measures 74 levels through the glass, against 17 for a quiet band. Above
    # y 140 the poster has nothing but margin - measured at 0.0 - so that is
    # where act two's heading goes, and the card starts at 140 so the ghost band
    # is behind a pane rather than on bare frost.
    # ANCHOR "ma": the y is the TOP of the text, not its middle - which is what
    # Macro does, and the reason its heading looked right on a phone while this
    # one did not. Centred at 92 a 52px title starts at y 66, thirty pixels
    # higher than Macro's 96, and that put it level with Instagram's own back
    # chevron and camera button: the title sat between two pieces of their UI.
    #
    # Lower is not free. `glass.ghost` on the nine bases says the band 72-130 is
    # the last one that reads clean - 31 to 72 levels against ordinary bands of
    # 28 to 77 - and every step down is worse, because act one's own title lives
    # at 143-274 and a 30px blur carries it upward. 96 with a 50px face lands at
    # 96-146, and the card starts right under it so the strip covers the rest.
    if ta > 0.01:
        text(d, (LW / 2, 96 + (1 - ta) * 14), res["title"], f_title,
             INK[:3] + (int(255 * ta),), anchor="ma")

    # The list pane: header strip, then the rows, growing with however many
    # there are.
    head_h = 96
    rowh, grph = 82, 40
    groups = []
    for row in plan.rows:
        if not groups or groups[-1] != row["group"]:
            groups.append(row["group"])
    list_h = head_h + grph * len(groups) + rowh * len(plan.rows) + 26
    list_top = 168
    list_bot = list_top + list_h
    lbox = grow((x0, list_top, x1, list_bot), min(k1, 1.15))
    a1 = min(k1, 1.0)
    if a1 > 0.01:
        shadow(img, lbox, 40, alpha=int(15 * a1))
        over(img, lambda dd: pane(dd, lbox, 40, a=a1))

    # The strip behind MICRONUTRIENTS and the kcal figure is the one part of the
    # card that has to be opaque, and for the reason the whole header was before
    # the title moved out: act one's title lands exactly here. At 0.90 compound
    # a 74-level ghost measures 4. Everywhere else the poster is meant to show
    # through - that is what the glass is for.
    if a1 > 0.01:
        sx0, sy0, sx1, _ = lbox
        def strip(dd, b=(sx0, sy0, sx1, sy0 + head_h * (lbox[3] - lbox[1]) / list_h),
                  aa=a1):
            rounded(dd, b, 40, (255, 255, 255, int(180 * aa)))
            rounded(dd, (b[0], b[3] - 40, b[2], b[3]), 0, (255, 255, 255, int(180 * aa)))
            dd.line([(b[0] * S, b[3] * S), (b[2] * S, b[3] * S)],
                    fill=(255, 255, 255, int(210 * aa)), width=int(1.5 * S))
        over(img, strip)

    # The words on the card wait for the card to land rather than riding its
    # scale: type scaled by 6% and back reads as a focus pull, not as an entrance.
    ha = fade(t, plan.card1 + plan.card_dur * 0.8, 0.20)
    if ha > 0.01:
        text(d, (x0 + 44, list_top + 32), st["head"], f_head,
             SUB[:3] + (int(SUB[3] * ha),))
        text(d, (x1 - 44, list_top + 32), f"{res['calories']} kcal", f_head,
             SUB[:3] + (int(SUB[3] * ha),), anchor="ra")

    y = list_top + head_h + 18
    last_group = None
    for i, row in enumerate(plan.rows):
        a = fade(t, plan.row0 + plan.rowgap * i, plan.rowdur)
        if row["group"] != last_group:
            last_group = row["group"]
            if a > 0.01:
                label = {mr.VIT: st["vit"], mr.MIN: st["min"],
                         mr.OTH: st["oth"]}[last_group]
                text(d, (x0 + 44, y), label, f_grp, SUB[:3] + (int(SUB[3] * a),))
            y += grph
        if a <= 0.01:
            y += rowh
            continue
        over_limit = row["kind"] == mr.LIMIT and row["pct"] > 1
        colour = RED if over_limit else tuple(int(row["colour"][k:k + 2], 16)
                                              for k in (1, 3, 5))
        text(d, (x0 + 44, y), row["label"], f_row, INK[:3] + (int(255 * a),))
        amount = f"{row['amount']:.0f}" if row["amount"] >= 10 else f"{row['amount']:.1f}"
        text(d, (x1 - 44, y + 6), f"{amount} {row['unit']} \u00b7 {row['pct'] * 100:.0f}%",
             f_val, colour + (int(255 * a),), anchor="ra")
        bw = x1 - x0 - 88
        w = bw * min(row["pct"], 1.0) * a
        over(img, lambda dd, yb=y, aa=a, ww=w, cc=colour: (
            rounded(dd, (x0 + 44, yb + 46, x1 - 44, yb + 56), 5,
                    TRACK[:3] + (int(TRACK[3] * aa),)),
            ww > 10 and rounded(dd, (x0 + 44, yb + 46, x0 + 44 + ww, yb + 56), 5,
                                cc + (int(255 * aa),))))
        y += rowh

    # The ring pane takes what is left between the list and the wordmark band.
    # The floor is what stops a long list turning it into a stripe: past that it
    # overflows visibly, which is a bug you can see rather than one you cannot.
    # The note lives INSIDE this pane, under the ring, so no height is reserved
    # for it outside: reserving it twice left 134px of bare frost between the
    # card and the wordmark, which reads as the layout having run out rather
    # than as space.
    gap = 30
    ring_top = list_bot + gap
    ring_h = max(520, foot_top - gap * 2 - ring_top)
    ring_bot = ring_top + ring_h

    # It fades AND rises the last 18px, which is what makes it read as arriving
    # rather than as being switched on. The shadow fades with it: a soft drop
    # under a pane that is not there yet is a grey smudge on the frost.
    k2 = enter(t, plan.pane2, plan.card_dur)
    p2 = min(k2, 1.0)
    rbox = grow((x0, ring_top, x1, ring_bot), min(k2, 1.15))
    if p2 > 0.01:
        shadow(img, rbox, 40, alpha=int(15 * p2))
        over(img, lambda dd: pane(dd, rbox, 40, a=p2))

    cx = LW / 2
    cy = (rbox[1] + rbox[3]) / 2 - ring_h * 0.06
    radius = min(200, ring_h * 0.30)
    width = max(20, radius * 0.14)

    sweep = ease(min(max((t - plan.ring0) / plan.ring_dur, 0.0), 1.0))
    track_a = fade(t, plan.pane2 + plan.card_dur * 0.8, 0.30) * (1 if p2 > 0.01 else 0)
    if track_a > 0.01:
        vals = []
        for key, _lbl, grp, _u, kind in ORDER:
            have = res_progress(res, key)
            if have is None:
                vals.append(None)
            else:
                colour = tuple(int(mr.COLOUR[grp][k:k + 2], 16) for k in (1, 3, 5))
                vals.append((have, colour, kind == mr.LIMIT and have > 1))
        over(img, lambda dd: segmented_ring(dd, cx, cy, radius, width, vals,
                                            sweep, track_a))

    score = res["score"]
    a = fade(t, plan.score0, 0.45)
    if a > 0.01 and score is not None:
        shown = score * ease(min(max((t - plan.score0) / plan.ring_dur, 0.0), 1.0))
        text(d, (cx, cy - 10), f"{shown * 100:.0f}%", f_big,
             INK[:3] + (int(255 * a),), anchor="mm")
        text(d, (cx, cy + 86), st["score"], f_lbl, SUB[:3] + (int(SUB[3] * a),),
             anchor="mm")

    a = fade(t, plan.under0, 0.40)
    if a > 0.01:
        text(d, (cx, rbox[3] - 46), st["under"], f_note,
             SUB[:3] + (int(SUB[3] * a),), anchor="mm")

    out = Image.alpha_composite(base.convert("RGBA"), img).convert("RGB")
    out = out.resize(LOGICAL, Image.LANCZOS)
    strip_img = out.crop((0, foot_top, LW, LH))
    out.paste(Image.blend(strip_img, fb, FOOT_A), (0, foot_top))
    return out if (W, H) == LOGICAL else out.resize((W, H), Image.LANCZOS)


def res_progress(res, key):
    for l in res["lines"]:
        if l["key"] == key:
            return l["pct"]
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--topic", required=True)
    p.add_argument("--lang", default="en", choices=["en", "hr"])
    p.add_argument("--seconds", type=float, default=7.0)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--width", type=int, default=1080)
    p.add_argument("--height", type=int, default=1920)
    p.add_argument("--age", type=int, default=30)
    p.add_argument("--gender", default="none", choices=["male", "female", "none"])
    p.add_argument("--behind", help="act one, for the frosted backdrop")
    p.add_argument("--behind-offset", type=int, default=0)
    p.add_argument("--behind-lo", type=int, default=0)
    p.add_argument("--still", help="write one frame at --at and stop")
    p.add_argument("--at", type=float, default=6.0)
    p.add_argument("--cues", help="where to write act two's timeline")
    p.add_argument("--first-frame", help="png of frame 0, for the flip's face B")
    p.add_argument("-o", "--out")
    a = p.parse_args()

    res = mr.result(a.topic, a.age, a.gender)
    plan = Plan(res, a.seconds, a.lang)
    if a.cues:
        with open(a.cues, "w") as fh:
            json.dump(plan.cues(), fh, indent=1)
        print(f"  act two's cues -> {a.cues}")

    bg, _ = behind_frames(a.behind) if a.behind else (None, None)

    def behind_at(i):
        if not bg:
            return None
        return bg[_walk(i, a.behind_offset, a.behind_lo, len(bg) - 1)]

    if a.still:
        im = render(plan, a.at, a.width, a.height, behind_at(0))
        im.save(a.still)
        print(f"  {a.topic} at {a.at:.2f}s -> {a.still}   score "
              f"{'-' if res['score'] is None else f'{res['score'] * 100:.0f}%'}")
        return

    if not a.out:
        raise SystemExit("--out or --still")
    n = int(round(a.seconds * a.fps))
    import subprocess
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{a.width}x{a.height}", "-framerate", str(a.fps), "-i", "-",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
         a.out], stdin=subprocess.PIPE)
    for i in range(n):
        im = render(plan, i / a.fps, a.width, a.height, behind_at(i))
        if i == 0 and a.first_frame:
            im.save(a.first_frame)
        ff.stdin.write(im.tobytes())
    ff.stdin.close()
    ff.wait()
    print(f"  act two: {n} frames, {a.seconds:.2f}s -> {a.out}")


if __name__ == "__main__":
    main()
