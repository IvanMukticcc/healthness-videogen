#!/usr/bin/env python3
"""glass.py - the surface a second act is drawn on.

Extracted from `Macro/work/meal.py` on 10 September 2026, when Micro became the
second variant to turn a poster over and read something off the back of it. Same
promotion rule as `flip.py` an hour earlier: a thing moves here when a second
user appears, and not in anticipation of one.

WHAT IT IS

A pane of frosted glass laid over act one, with act one still moving underneath.
Not a screen that replaces the poster - the liquid keeps flowing behind it, which
is the only thing joining two acts that otherwise have nothing in common, one
being a photograph and the other being an app.

    behind_frames(clip)   act one's frames, decoded small
    frost(frame, size)     one of them turned into the pane you read through
    walk(i, start, lo, hi) which frame sits under act two's frame i
    pane(d, box, r)        a translucent card with a lit edge
    shadow / bar / text / font / ease / overshoot / rounded
    footer(W)              the poster's own wordmark band

THREE THINGS THAT ARE NOT OBVIOUS AND COST A DAY EACH

**Blur, THEN pull towards white, THEN restore saturation.** The other order
washes the liquid out to a grey ghost, and the colour is the only thing telling
you what is behind the glass.

**A pane needs a lit edge or it is a stain.** At `CARD_A` over a frosted poster a
card has almost the same value as the frost around it; without a hairline of
brighter white it has no boundary and a list of text floats on a smear.

**Anything drawn at low alpha over this is not a colour, it is a tint on whatever
act one is doing** - and act one is doing something different on every row. A
constant that looks right against one poster's rows can vanish against another's.
`MAINTAINER.md` carries the case: a ring track at 42 alpha collapsed from 51.7
levels of separation to 2.0 when the frost changed, and no alpha could fix it
because 84% of what read as "a grey track" was the pane behind it.

The backdrop is decoded at `BEHIND_W` and blown back up. It is about to be
blurred past any detail that width could carry, and 192 frames of 1080x1920 in
memory is 1.2 GB against 74 MB at 270.
"""
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/Library/Fonts"

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
# TUNED AGAINST ONE PALETTE, AND IT SHOWS. 0.34 was measured on Macro's
# breakfast base, whose rows alternate dark navy and near-white; navy goes to
# grey under the whitening and takes its white title with it. Micro's pressure
# base is green and white, a mid-tone that survives, so at 0.34 act one's title
# reads straight through and collides with act two's, which sits in the same
# place. Pass `amount=` per variant and check it with `title_survival()`.
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

S = 2                                   # supersample: draw at 2x, land at 1x
# The poster's own footer, pixel for pixel. Act two is drawn and act one is
# photographed, so the one thing that must be identical between them is the
# thing that is identical everywhere else in this repository: the wordmark. It
# is not redrawn in a similar font - it is the bottom of engine/base_layer.png,
# below the last row stripe (which ends at 2063+413=2476 of 2752), scaled.
BASE_LAYER = os.path.join(HERE, "base_layer.png")
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


def walk(i, start, lo, hi):
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


def title_survival(base_png, size=(1080, 1920), **kw):
    """How much of a poster's own title still reads through the glass.

    The criterion, and it is comparative rather than absolute: **the title band
    must not be livelier than an ordinary band of the same poster.** If it is,
    act one's heading is competing with act two's, which sits in the same place.

    Measured on the two posters that set the range:

        Macro breakfast, white on navy   title 42.6   ordinary band 81.2   passes
        Micro pressure,  white on green  title 73.6   ordinary band 14.5   fails

    Navy goes to grey under the whitening and takes its white type with it. A
    mid-tone green does not, so the type stays. Nothing is wrong with either
    poster; `FROST` was tuned against the first one.
    """
    import numpy as np
    im = Image.open(base_png).convert("RGB")
    small = im.resize((BEHIND_W, round(BEHIND_W * im.height / im.width)), Image.LANCZOS)
    f = np.asarray(frost(small, size, **kw)).astype(float)
    lum = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
    h = size[1]
    title = lum[int(h * 0.073):int(h * 0.130), :]
    other = lum[int(h * 0.156):int(h * 0.188), :]
    return float(title.max() - title.min()), float(other.max() - other.min())


def frost(im, size, amount=None, sat=None, blur=None):
    """One act-one frame turned into the pane you read through.

    Blur, then pull towards white, then put the saturation back. The order
    matters: whitening a blurred frame washes the liquid out to a grey ghost,
    and the colour is the only thing telling you what is behind the glass.
    """
    b = im.filter(ImageFilter.GaussianBlur(BLUR if blur is None else blur))
    b = Image.blend(b, Image.new("RGB", b.size, (255, 255, 255)),
                    FROST if amount is None else amount)
    b = ImageEnhance.Color(b).enhance(SAT if sat is None else sat)
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


def ring(d, cx, cy, radius, width, frac, colour, track=TRACK,
         on=(255, 255, 255, CARD_A)):
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
    d.ellipse(box, outline=track if on is None else over(track, on),
              width=int(width * S))
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


def over(top, bottom):
    """Source-over of two RGBA tuples, because ImageDraw does not do it.

    **ImageDraw REPLACES pixels; it does not composite them.** A track drawn at
    alpha 120 onto a pane already at 186 leaves 120 - so the track becomes a
    MORE transparent window in the card and shows more of act one through it
    than the card around it does. It reads as "the glass is a bit uneven"
    rather than as a bug, which is why it survived in Macro from the day the
    panes went translucent until micro-bb hit it head-on drawing a header
    ground and measured the ghost getting worse: 14.4 to 18.9 levels.

    Verified rather than assumed: pane 186, track 120 drawn over it, resulting
    alpha 120. Composited, 218.

    So anything meant to sit ON a pane is composited against that pane here and
    drawn once, at the right colour and the right alpha.
    """
    ta = top[3] / 255.0
    ba = bottom[3] / 255.0
    a = ta + ba * (1 - ta)
    if a <= 0:
        return (0, 0, 0, 0)
    rgb = tuple(int(round((top[i] * ta + bottom[i] * ba * (1 - ta)) / a)) for i in range(3))
    return rgb + (int(round(a * 255)),)


def bar(d, box, frac, colour, on=(255, 255, 255, CARD_A)):
    x0, y0, x1, y1 = box
    h = y1 - y0
    # `on` is the surface this sits on, so the track can be composited against
    # it and drawn once. Pass on=None where it is over something opaque.
    rounded(d, box, h / 2, TRACK if on is None else over(TRACK, on))
    w = (x1 - x0) * max(0.0, min(1.0, frac))
    if w > h * 0.4:
        rounded(d, (x0, y0, x0 + w, y1), h / 2, colour)


