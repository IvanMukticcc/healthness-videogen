# Healthness Shorts — the exercise animation flow

When the user says **"nova tema"** or **"idemo dalje"**, run this loop.

The point of the whole design: **the parts that must be identical are never
regenerated.** An image model cannot redraw a wave the same way twice, so the
wave is never asked to. It cannot redraw a body the same way twice either, so
from this version on the body is not asked to. Only the athlete on the left, the
title and the palette change.

## Where things live

    ShortPrompt/
      OTHER/            the tools, the bases, the mask, the generated posters
      Micro/            the food version: bowls, organs, micronutrients
      Exercise/work/  this one: lifts, bodies, muscles. This file.
        ASSETS/Muscle/    the badges, and the blank sphere they are cut from
        ASSETS/           the bed, synthesised here
        OUTPUT/           finished videos, one folder per day (`07.09/`)
        work/             posters, scrap renders, cue files
        palettes/         a reference base, kept so a new one has something to sit beside
      ASSETS/           `Vitamini/` and `Minerali/` as generated, and the water beds

Run everything from inside `Exercise/work/`. It writes nothing outside itself.

## Files that carry the design

| file | what it is |
| --- | --- |
| `base_layer.png` | the reference base: five row stripes, five identical waves, logo. 1536×2752 |
| `ribbon_mask.png` | where the waves are. Authored from `base_layer.png`, **geometry only** |
| `base_<topic>.png` | one per topic: `base_layer.png` recoloured. Same geometry, so the same mask fits |
| `flowanim.py` | the animator |
| `recolor_base.py` | makes a new palette |
| `check_base.py` | did the generator leave the waves alone? |
| `make_base.py` | rebuilds `base_layer.png` from a freshly generated wave poster. Rarely needed |
| `muscles.py` | the vocabulary: label, tier, colour, body regions. Everything else reads it |
| `bodymap.py` | the figure, front and back. `--sheet` for the catalogue |
| `body_overlay.py` | where the body sits in the row and how a muscle ignites |
| `muscle_icons.py` | builds the badges. `--all` for the catalogue, `--one 'Label:p\|s\|t'` for one |
| `muscle_overlay.py` | where the badges go and how they enter. Imported by `flowanim.py` |
| `muscle_audio.py` | the hit, and the bed. Both synthesised |
| `exercises.json` | lift → the muscles it works, prime mover first |
| `../../engine/grab.py` | takes the newest 1536×2752 image out of Downloads and names it `<topic>.jpeg` |
| `clean_poster.py` | puts the base back where the generator drew outside its brief |
| `left_disc.py` | fills the left circle with that row's wave colour, in the base and its clean copy |
| `render.sh` | animate, sound, mux |
| `audit.py` | what moves that should not |
| `../OUTPUT/<DD.MM>/` | the day's finished clips, sound already on them |

## The loop

**1. Pick the topic and the palette.** Five lifts, a title, and a colour scheme
clearly different from the last few. Build the base:

```
.venv/bin/python recolor_base.py --rows '<dark>,<light>' \
  --waves '<c1>,<c2>,<c3>,<c4>,<c5>' --vibrance 1.05 --contrast 1.04 \
  --title '<TITLE>' --subtitle '<SUBTITLE>' -o work/base_<topic>.png
```

Rows 1, 3, 5 take the dark colour and 2, 4 the light one. Put the bright wave
colours on the dark rows.

**The waves may not be red, orange or amber.** The badges are those colours. The
allowed arc is lime, cyan, violet, fuchsia, teal, and `Prompts.txt` says what was
measured and what it cost. Six filled palettes are in there ready to paste.

Pick the five lifts so the bodies differ — five presses light the same chest five
times and the viewer has seen the whole clip by row two. Check before building:

```
.venv/bin/python -c "import muscle_overlay as m; print(m.resolve('auto:HIP THRUST'))"
```

**1b. Fill the left circle.** The lifter sits in a circle the way the food sits
in a bowl, and the circle is drawn rather than asked for:

```
../.venv/bin/python left_disc.py -b base_<topic>.png -c base_<topic>_clean.png \
    -l base_<topic>_layout.json
```

It reads each row's own wave colour and puts the disc down in both files —
identical in the two, so the animator reads it as design rather than as a guide
mark to wipe. Then move `base_<topic>.png` to `../INPUT/`, which holds base
images and nothing else.

**2. Give the user the prompt**, ready to paste, and tell them to attach
`base_<topic>.png`. The template is in `ImageSwap.txt`; the opening paragraph is
what does the work and goes in unchanged. Filled examples are in `Prompts.txt`.

The generator now fills **only the left circle**. Say so; it is the one thing
about this version that a prompt copied from the food version gets wrong.

**3. The user returns the generated poster.** It does not have to be moved by hand — `../.venv/bin/python ../../engine/grab.py <topic>` takes the newest file in Downloads whose size is exactly 1536×2752 and renames it `<topic>.jpeg` here. The size is the safety net: a screenshot or a photo is not that, and the generator's own filename changes every time. Then check it before spending time on it:

```
.venv/bin/python check_base.py <poster> --base work/base_<topic>.png
```

`safe to animate` means the mask still fits. Anything else: ask for a
regeneration, do not try to animate around it.

Then look at the right circles by eye. The wave check does not cover them.
Anything the generator drew *inside* one is covered by the body's disc; anything
straddling its *edge* survives, and also nudges the wave's tip. `ImageSwap.txt`
has the measurement.

**3a. Take back what is not the generator's.** It draws in the right circle
whatever the prompt says — on PULL DAY it rubbed out the guide mark and the
caption bar and drew a stroked ring of radius 200 around a circle of 138 — and
its athlete arrives on an opaque disc that hangs over the top third of the left
caption bar. All of that is base content, on disk, at pixel-exact geometry, so it
is restored rather than regenerated (`../CLAUDE.md` rule 9):

```
../.venv/bin/python clean_poster.py <poster> --base ../INPUT/base_<topic>.png \
    -l base_<topic>_layout.json -o <topic>_clean.png
```

The caption bars matter as much as the ring: `add_labels.py` takes its ink from
whether the row is light or dark, which is right for the bar the base drew and
wrong for a photo lying over it — and the discs come back inverted against their
rows, so every left caption would be drawn in the one colour the thing under it
shares.

**3b. Put the captions on**, into the bars the base reserved for them. The right
caption names the muscle **group**, not a muscle — the body beside it is already
saying which muscles, in colour, one at a time:

```
.venv/bin/python add_labels.py <poster> -l work/base_<topic>_layout.json \
    -o work/<topic>_labelled.png \
    --labels 'LIFT|GROUP,LIFT|GROUP,LIFT|GROUP,LIFT|GROUP,LIFT|GROUP'
```

**4. Animate, sound it, ship it.** One command, because the animator and the
sound have to agree on when the badges land — and that instant is also when the
muscle lights:

```
./render.sh <topic> work/<topic>_labelled.png 'auto:LIFT,LIFT,LIFT,LIFT,LIFT'
```

`auto:` reads `exercises.json`. To choose the muscles by hand, pass them instead —
`;` between rows, `,` inside one, `:p`/`:s`/`:t` to override a tier:
`'Chest:p,Triceps:s;Lats:p,Biceps:s;...'`. Anything after the third argument goes
straight to `flowanim.py`.

Out comes `../OUTPUT/<DD.MM>/<topic>_muscles.mp4` with the bed and the hits on it.
`work/<topic>_silent.mp4` is the scrap pass; `work/<topic>_cues.txt` is what the
sound was cut against.

Watch the render's output for a line like

    r3: Glutes does not show from the front - its badge lands over an unlit body

That is a dead beat: the badge lands and the hit sounds over a body where nothing
happens. Either reorder the row so the view flips, or swap the muscle.

The three steps it runs, if one is ever needed alone:

```
.venv/bin/python flowanim.py work/<topic>_labelled.png --width 1080 --seconds 8 \
    --mask ribbon_mask.png --base work/base_<topic>_clean.png \
    --anchored work/base_<topic>.png --layout work/base_<topic>_layout.json \
    --drops 0 --reach 0 --muscles 'auto:LIFT,...' \
    --muscle-cues work/<topic>_cues.txt -o work/<topic>_silent.mp4

.venv/bin/python muscle_audio.py --cues-file work/<topic>_cues.txt \
    --seconds 8 -o work/<topic>_hits.wav

ffmpeg -y -i work/<topic>_silent.mp4 -i ../../engine/sfx/lift_bed_8s.m4a -i work/<topic>_hits.wav \
  -filter_complex "[1:a]volume=1.0[w];[2:a]volume=0.62[p];\
[w][p]amix=inputs=2:duration=first:normalize=0[m];\
[m]alimiter=limit=0.82:level=disabled[a]" \
  -map 0:v -map "[a]" -shortest -c:v copy -c:a aac -b:a 192k \
  ../OUTPUT/<DD.MM>/<topic>_muscles.mp4
```

Without `--muscles` the animator renders the liquid and nothing else.

`<DD.MM>` is the day's folder — `07.09`, made if it is not there yet. **Only the
finished cut goes there.** The silent pass stays in `work/`: the clip is never
published without sound, so a mute mp4 in `OUTPUT/` is only something to mistake
for the finished one later.

**5. Audit before delivering.**

```
.venv/bin/python audit.py work/<topic>_silent.mp4 --cues work/<topic>_cues.txt
```

Single digits is clean. On the reference cut it reports 128 px, and that is x264
ringing on the boundary between a near-black row and a white one, not motion —
see `README.md`. If type or the athlete moves, something is wrong; say so rather
than shipping it.

## What is already known to break

Everything below was found by measurement, and each one cost an hour. Do not
rediscover them.

### Carried from the food version, still true

- **Droplets.** Detecting loose droplets to fly them separately picks up letters.
  `--drops 0`. Bring droplets back only as an authored layer in the base.
- **Reaching.** The stretch warp that pushed the wave's tip along moves the whole
  horizontal band, and in the bottom rows that band contains the label. It ate
  the "LY" of LYMPHATIC. `--reach 0`.
- **Liquid in front of the artwork.** The mask runs the full length of the wave.
  Painting there puts the liquid on top of whatever fills the circles. `--base`
  fixes it: paint only where the poster still equals the base.
- **Speckles that stand still.** The `clean` mask must be opened and closed
  before use, or JPEG noise along the wave's edge leaves unpainted pixels sitting
  still while the wave moves under them.
- **Recolouring.** Gamma on brightness, plain scaling on saturation. Scaling
  brightness kills the specular highlight; gamma on saturation drives it to 1 and
  the wave turns into a flat vector shape.
- **Artwork crowding the edges.** The wave is inset to 20%–79% of the width so
  what gets placed against its tips is not dragged off a vertical crop. Added
  artwork should stay inside x 154–1382.
- **The captions have a reserved place.** With no text asked for, the generator
  fills the whole row and a caption added afterwards lands on top. The base draws
  a faint bar under each circle and the prompt tells the model to keep it clear.
- **No text is asked for at all.** The title is drawn into the base; the row
  captions are added by `add_labels.py`. Both are typography at known positions,
  so neither needs a model.
- **Telling the generator where to put things does not work.** It places things
  where it likes. The base carries faint circles and the prompt tells the model
  to fill them. A mark it can see beats a sentence it has to interpret.
- **The safe area is one fourteenth of the width, not one tenth.** The guide
  circles reach x 112, and a tenth of 1536 is 154 — so a tenth tells the model to
  keep the athlete out of the very circle it is told to fill, and it follows the
  sentence over the mark.
- **A badge is not allowed to sit on a guide circle.** The athlete fills one and
  the body the other. The badges are laid out in the gap between the two and
  shrink to fit rather than overflowing.
- **A transverse wave through a body that stays put is a flag, not a flow.** Keep
  `--snake` at 0 and `--swell` low.
- **A badge that fades out is a smudge for half a second**, and that is the frame
  a feed freezes on. `--muscle-fade 0`, which is the default.
- **Hue rotation cannot hit a given colour**, and throws contrast away on the
  way. Gradient-map the sphere's luminance onto the target, then draw the letter
  on top in white.
- **`alimiter` undoes its own limit.** `level=disabled`.
- **The wave's centre line is stored in the ribbon's own column range.**
  `geo["top"]` is indexed by `x - x0`, not by `x`.

### New here

- **The circle is drawn, not asked for.** Three days, three answers: an opaque
  white disc on a dark row, a near-black one on a light row, and then — after the
  prompt said not to draw a disc — a cut-out athlete standing on the row with
  nothing behind him. A design element that has to be identical on every row of
  every topic does not belong in a sentence the model interprets. `left_disc.py`
  puts it in the base, in the row's own wave colour at 0.85 shade so the wave's
  gloss still reads where it crosses, and the prompt only has to say the athlete
  stands inside it. The liquid then leaves a circle of its own colour, which is
  what the bowl does in the food version.

- **The lifter is bigger than the mark, and the animator cannot see all of him.**
  The generator fills the left circle with an opaque photo disc of radius about
  180 against the circle's 138, inverted against its row. Artwork is found by
  difference from the base or by detail, and a black singlet on a near-black row
  has neither: the liquid was painted across his chest and pale crescents of his
  disc were sampled into the wave's texture and carried downstream. 8497 px of
  him moved. `body_overlay.refine_art` walks out from the circle's centre along
  every angle to the furthest pixel that still differs from the base and keeps
  everything nearer — the shape is found, not described, so a smaller athlete
  yields a smaller silhouette. `--lifter-r 0` turns it off; the radius is only
  where looking stops.
- **The guide-circle wipe paints the wave onto the lifter.** Inside a circle the
  clean base *is* the wave, and the wipe puts it back wherever the poster still
  looks like the guide mark. A dark singlet is within the animator's default 20
  levels of the row behind it, so it came back cyan — and then, once `refine_art`
  called him artwork, it stayed cyan and stopped moving, which is worse. Both
  circles are covered here by construction, so `render.sh` passes
  `--anchor-tol 6`: 256454 px still get wiped, 18889 of them no longer taken off
  the athletes.
- **The waves may not be red, orange or amber.** The synergist tier is the
  commonest in the table, so an amber wave loses about a third of every row. See
  `Prompts.txt` for the arc that was measured and what it replaced.
- **`--body-scale` is against the radius, not the diameter.** Read as a diameter
  it is 4.4r and the arms hang a quarter of the poster out either side.
- **A muscle that does not show from the chosen view is a dead beat.** The badge
  lands and the hit sounds over an unlit body. `view_for` picks the side that
  shows more of the row before it asks which way the row faces — on direction
  alone, 18 of the 130 lifts had one; on coverage first, 6 do. `bodymap.py` also
  carries a gluteus medius on the front view, because without it every squat,
  lunge and leg press does it. The planner prints a line naming the remaining
  six when they come up.
- **Two lit muscles on the same tier merge.** Glutes beside hamstrings, both
  primary, is one red mass with no anatomy left in it. Every lit region carries a
  darker rim of its own colour.
- **Catmull-Rom at the textbook tension of 0.5 overshoots every tight corner**
  and a pectoral comes out as a lozenge. 0.34.
- **Noise cut in the time domain does not loop.** The bed is built by shaping a
  spectrum and transforming back, so sample n−1 joins sample 0. Otherwise it is a
  click every eight seconds for as long as anyone watches.
- **The right circle is an invitation.** An empty marked circle is exactly what
  the generator fills, so the prompt calls it *finished artwork* rather than
  *empty*, and lists what not to put there. The disc underneath covers anything
  inside it; anything straddling the edge is a regeneration.

## Invariants worth re-checking if something looks off

```
waves span x 229-1289 of 1536       = 15% to 84% of the width
row stripes start at 412, 825, 1238, 1649, 2063, each 413 tall
wave rows y 491-702, 904-1115, 1317-1527, 1729-1940, 2142-2353
both tips within ~1px of their circle centre, 25px clear of the caption bar
one traversal of the wave per 8 s   ≈ 95 px/s, the speed the user settled on
the figure is 2.20r tall in a 1.00r circle - head and feet run just past the disc
badge tier colours == body tier colours, both from muscles.py
```

Ask the user to generate at 1536×2752. Smaller posters are upscaled before
animating and lose sharpness.
