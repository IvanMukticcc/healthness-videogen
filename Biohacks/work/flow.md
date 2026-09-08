# Healthness Shorts — the biohack flow

When the user says **"nova tema"** or **"idemo dalje"**, run this loop.

The point of the whole design, carried over: **the parts that must be identical
are never regenerated.** An image model cannot redraw a wave the same way twice,
so the wave is never asked to. It cannot redraw a dial the same way twice either,
and a dial that disagrees with itself between rows is five instruments instead of
one - so from this variant on, **neither circle is asked for at all.**

That is the structural difference. Foods and Micro get both circles from a
generator; Exercise gets the left one; this gets neither. What changes between
topics is the palette, the title, the five hacks and their numbers, and all four
of those are text in a file.

## The loop

**1. Pick five hacks and check they have sources.**

```
../../.venv/bin/python hacks.py
../../.venv/bin/python hacks.py 'cold finish' 'lights down'
```

The table prints `NO` against any entry whose `source` is a placeholder. Those do
not ship, and `check.py` refuses them at the end as well. **Write the source
before the number**, not after: a value invented first is a value the citation
gets bent to fit.

Pick them so the day reads left to right down the poster - `clock` orders them,
and the day bar draws its stops in the order the rows are given. A poster whose
clocks run 06:40, 22:30, 13:20, 07:05, 14:00 is five facts; in order it is a day.

**2. Pick the palette. Here the wave takes the colour of the hour.**

In the food version the wave takes the colour of its food. That rule does not
transfer - a hack is not a colour - so this one replaces it: **dawn amber,
morning ice, midday lime, afternoon coffee, night violet.** The eye reads the
poster top to bottom and the palette says what time it is before a single clock
has been read.

**And the palette is unrestricted**, which is this variant's alone. Exercise
fences its waves off from red, amber and orange because its badges are those
colours and a third of every row would be lost under an amber wave. Here the
badge is glass and the dial has its own disc, so nothing on the liquid has a hue
to collide with. Use it. Five topics that look alike is five topics nobody
scrolls back for.

```
../../.venv/bin/python ../../engine/recolor_base.py \
  --rows '#0E1A20,#E8EEF0' \
  --waves '#FFB020,#1B8FD6,#9BE04A,#B4471E,#A98CFF' \
  --vibrance 1.05 --contrast 1.04 \
  --title '5 FREE BIOHACKS' --subtitle 'ONE DAY, ZERO COST' \
  -o ../INPUT/base_<topic>.png --work .
```

Rows 1, 3, 5 take the dark colour and 2, 4 the light one. Put the bright wave
colours on the dark rows: the glyph is drawn in its own wave's colour, so a pale
wave on a pale row is a pale glyph on a pale disc, and `scene_overlay.wave_colour`
will have to drag it away from the hue to make it legible.

**3. Put the captions on.** Left is the hack, right is the metric, and the metric
must be the same words as `metric` in `hacks.json` - the dial draws the number and
the caption names it, and the two disagreeing is the one thing nothing catches.

```
../../.venv/bin/python ../../engine/add_labels.py ../INPUT/base_<topic>.png \
    -l base_<topic>_layout.json -o <topic>_labelled.png \
    --labels 'HACK|METRIC,HACK|METRIC,HACK|METRIC,HACK|METRIC,HACK|METRIC'
```

All ten are drawn at one size and the longest sets it. `CAFFEINE AT BED` at
fifteen characters took every caption down to 34px; `CAFFEINE LEFT` at thirteen
put them all back to 44. Keep them under fourteen.

**And do not let the left caption say what the chip says.** The `7000 steps`
entry was captioned `7000 STEPS` with a chip reading `7000 STEPS`, and the row
spent its whole 0.55 s saying one thing twice. The caption names the hack, the
chip prices it: `WALK MORE` and `7000 STEPS`.

**4. Render.** One command, because the picture and three sounds have to agree
about five instants and typing them twice drifts by a frame.

```
./render.sh <topic> 'auto:HACK,HACK,HACK,HACK,HACK'
```

Out comes `../OUTPUT/<DD.MM>/<topic>_biohack.mp4` with the bed, the chips, the
counters and the chord on it. `WIDTH=540 ./render.sh ...` while tuning: identical
timing, a third of the wait.

**5. Check before delivering.**

```
../../.venv/bin/python check.py <topic> --hacks 'auto:HACK,...'
```

Four questions: every number has a study, nothing outside the liquid is still
moving on the last frames, nothing moves that this folder did not plan, and the
audio joins end to end. Both are judged on the **largest connected cluster**, and
the reference cuts at 1080 report a largest settled cluster of 32 px, a largest
stray cluster of 16 px, and a loop join of 0.045.

## The rhythm, and why it is not the house rhythm

The other two ship `1,2,3.2,4.4,5.6`. This ships `0.7,1.85,3.0,4.15,5.3`, and
both ends moved for a reason.

**It starts earlier** because a feed decides in about 1.5 s. At a first cue of
1.0 the first number was not on screen until 1.28, and the seventeen frames
before it were liquid and five empty rings. The rings now read `0%` from frame 0
- an instrument at rest rather than a hole - and the first count starts at 0.88.

**It is even, 1.15 s apart**, where theirs accelerates. Theirs is a list being
counted off; this is a day passing, and a day has a beat.

**It ends where it has to.** A row here is a glyph, a chip and then half a second
of a dial counting - 0.55 s longer than a badge landing - so `cues` reports the
dial's **settle**, not its start, and the finale lands after it:

    last row fires        5.30
    chip lands            5.38
    dial counts           5.48 - 5.98
    finale                6.48       (--finale-lead 0.50, not the engine's 0.60:
    surge over 5 rows     6.48-7.02   the lead exists to clear what the last cue
    dials settled         7.22        started, and the count is already over)
    still hold            7.22-8.00

**The room is not bought with `--seconds`.** The surface travels a whole number
of ribbon lengths, which is what makes the loop seamless, so the speed is
`ribbon / seconds` and nothing else: 8 s is 92 px/s, 9 s is 82, and there is no
value between them.

## What is already known to break

Each of these was found by measurement and cost an hour. Do not rediscover them.

### Carried from the other variants, still true

- **Droplets.** `--drops 0`. Detecting loose droplets picks up letters.
- **Reaching.** `--reach 0`. The stretch warp moves the whole horizontal band,
  and in the bottom rows that band contains the caption.
- **Liquid in front of the artwork.** `--base` paints only where the poster still
  equals the base.
- **Speckles that stand still.** The clean mask is opened and closed before use.
- **A caption fitted on its own is a caption of its own size.** One size for all
  ten, from the longest string. The same rule is applied here to the dial numbers
  and to the chips, and for the same reason.
- **An element that fades out is a smudge for half a second**, and that is the
  frame a feed freezes on. Nothing here fades: the glyphs keep their colour, the
  chips stay up, the dials hold their number, and the loop cuts.
- **`alimiter` undoes its own limit.** `level=disabled`.
- **A transverse wave through something that stays put is a flag, not a flow.**
  `--snake 0`, `--swell` low.

### New here

- **A white glyph on a light row is not a dim glyph, it is no glyph.** The first
  cut drew every disc a touch *lighter* than its row and every glyph white. On
  rows 2 and 4 - the light ones - the left circle vanished completely and the
  dial's number with it. Discs are now darker than their row in both directions
  and the ink follows `dial.ink(light)`, which has one branch because of it.

- **A green snowflake is a colour system losing an argument with an object.**
  The second cut coloured each glyph by its hack's *direction* - the green, blue
  or amber its dial draws - on the exercise variant's sound argument that a
  colour arriving at both ends of a row is what joins them. It gave a green
  snowflake and a blue coffee cup, and the object wins every time. The glyph
  takes **its own wave's colour** instead, read from the picture with
  `scene_overlay.wave_colour`; the dial keeps the direction colours, because a
  ring has no opinion about what green means.

- **A wave colour is not automatically legible on its own disc.** The disc is the
  row's colour shifted 18-22 levels; the coffee wave lands 14 levels off a light
  disc and disappears into it. `wave_colour` walks the colour up or down, hue
  intact, until it clears `LUMA_GAP` (60). Every other row on the shipped palette
  clears it unaided.

- **The count and the ring must be on the same ease.** Counted linearly against a
  ring eased on `easeOutCubic`, the number is ahead of the arc through the whole
  of the middle and the two read as two animations in one circle. Both are on
  `1-(1-p)^3`, and so are the ticks - `biohack_audio.counter` lays them at the
  times the *value* passes each of sixteen equal steps, not at equal times.

- **`--finale auto` must be given the dial's settle, not its start.** `cues`
  returns `t + count`. Returning `t` puts the finale on top of a number still
  counting, and two things arriving at once is one thing nobody sees.

- **The thin ring at the disc's edge is worth 14 px of number.** The first dial
  was a fat gauge at `r*0.78` and 11.5% width, which left the number 178 px and
  42 px of type in the finished 1080 video. At `r*0.94` and 7.5% it gets 236 and
  56. The circle is fixed by the base at 275 px across, so every pixel the ring
  takes is a pixel off the only thing anybody reads.

- **An empty ring is a hole; a ring reading zero is an instrument.** The dials
  now draw `nums[0]` at 0.34 alpha before their row fires, which also puts five
  numbers on the frame a feed uses as the cover.

- **This variant's audit is not the other two's.** `audit.py` next door counts
  what moves outside the wave mask between badges, and here five dials, five
  chips and a day bar move out there on purpose. `check.py` builds the mask of
  its own furniture from the same plan the render used, and **judges the rest on
  the largest connected cluster rather than on the total**: x264 at crf 16 rings
  along the title's edges by 30 levels while row 1's shock ring expands 200 px
  below it, which no tolerance separates from motion. Its shape does - ringing is
  single-pixel columns on letter stems, and a thing that has moved is one blob.

- **A total makes a movement test resolution-dependent.** The same clip measured
  3 px in 3 clusters at 540 wide and 196 px in 106 clusters at 1080 - 1.8 px per
  cluster, which is type that got sharper, not something that started moving. The
  first version of `check.py` had a pixel budget and would have failed every
  full-resolution render it was ever pointed at. A cluster does not scale.

- **Two rows with the same glyph is one row the viewer stops reading.**
  `walk after lunch` and `7000 steps` were both filed as `footprints`, which is
  the right icon for either of them read on its own and a repeat on a poster that
  holds both. `scene_overlay.build` now names it on stderr rather than fixing it:
  which of the two should move is a decision about the topic, not about the code.

- **A chip's shock ring reaches further than the chip.** `own_regions` allowed
  `h * 1.35` where the ring is drawn to `h * 1.30` on a canvas rounded out from
  there, and the test spent its first run reporting the chip's own ring as a
  stray, at y 122-123 - one pixel outside its own declared region. 1.55.

- **The mask has to be dilated before it is used as an alibi.** `--swell` lets the
  liquid's silhouette breathe past the authored mask and the resize to render
  width moves the boundary again. Undilated, `check.py` reported 2 370 px in 79
  clusters, every one a two-pixel fringe along a wave edge.

- **The bed is written here, not into `engine/sfx/`.** The shelf there is shared
  and this bed is this variant's. A third file in a shared folder that only one
  caller ever reads is the beginning of the same drift every other copy in this
  repository started as. `biohack_audio.py --bed` rebuilds it.

- **The bed loops by construction, so it must not be faded.** Every component is
  a whole number of cycles over the clip and the join measures 0.00000. The
  engine's water beds carry 150 ms fades because they were cut out of longer
  takes; a fade here would be the bed ducking on every lap of the loop. 12 ms of
  guard at each end, and no more.

- **`--bed-gain 0.48` is not a taste.** It lands the bed on -18.4 LUFS, which is
  where both engine beds are normalised, so every mix number in `render.sh`
  means the same thing here as it does next door.

- **The chip is 0.62, not Micro's 0.85.** A row here is a chip, sixteen ticks and
  a lock. At 0.85 the chip masked the first four ticks of its own counter, which
  is the half of the sound that is new.

- **One chip, not three badges.** Measured at 1536 over the 415 720 px of the
  wave mask: 22.7% of the liquid is inside a guide circle and never painted,
  Micro's three 210 px badges cover another 54.7% and leave **22.6% visible** -
  which is the 22.3% `engine/README.md` arrives at from the other direction. One
  313x118 chip covers 23.6% and leaves **53.7%**. That is what makes `--surge`
  read here: next door the finale highlight has almost no wave left to run along.

## Invariants worth re-checking if something looks off

```
waves span x 229-1289 of 1536       = 15% to 84% of the width
row stripes start at 412, 825, 1238, 1649, 2063, each 413 tall
wave rows y 491-702, 904-1115, 1317-1527, 1729-1940, 2142-2353
guide circles r 137, x 250 and x 1270; caption bars 380x78 under them
the day bar's clear strip is y 2476-2585; the logo starts at 2586
one traversal of the wave per 8 s   ~92 px/s
dial ring at r*0.94, width r*0.075; the number gets 236 px at 1536
the glyph's colour == its own wave's; the ring's == its direction's
```
