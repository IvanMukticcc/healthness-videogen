# Healthness Shorts — the poster animation flow

When the user says **"nova tema"** or **"idemo dalje"**, run this loop.

The point of the whole design: the liquid is authored once and never
regenerated. An image model cannot redraw a wave the same way twice, so the wave
is never asked to. Only the food, the organs, the title and the palette change.

## Where things live

    ShortPrompt/
      engine/    the five tools and the three authored assets. Read its README
      OTHER/     this variant: the bases, the generated posters, the prompts, this file
      MikroVersion/ ExerciseVersion/   other variants, worked on by others
      ASSETS/    water SFX, both CC0
      OUTPUT/    finished videos, one folder per day (`07.09/`), sound on every one

Run everything from inside `OTHER/`, calling `../engine/<tool>.py`; `ASSETS` and
`OUTPUT` are one level up. **Never keep a copy of an engine file here** - that is
how the same five tools ended up at three different generations at once.
`../engine-status.sh` reports what each variant is actually running.

## Files that carry the design

| file | what it is |
| --- | --- |
| `../engine/base_layer.png` | the reference base: five row stripes, five identical waves, logo. 1536×2752 |
| `../engine/ribbon_mask.png` | where the waves are. Authored from `base_layer.png`, **geometry only** |
| `base_<topic>.png` | one per topic, made here: the base recoloured. Same geometry, so the same mask fits |
| `../engine/flowanim.py` | the animator |
| `../engine/recolor_base.py` | makes a new palette |
| `../engine/check_base.py` | did the generator leave the waves alone? |
| `../engine/make_base.py` | rebuilds the base layer from a freshly generated wave poster. Rarely needed |
| `../OUTPUT/<DD.MM>/` | the day's finished clips, `_sfx` only |
| `../ASSETS/` | water SFX, 8 s, normalised to -18 LUFS |

## The loop

**1. Pick the topic and the palette.** Five foods, five organs, a title.

**The wave takes the colour of its food.** Yoghurt runs white, beetroot magenta,
ginger amber, lentils brown, seaweed teal. This is the whole point of the row: a
food and the organ it feeds, joined by the food itself made liquid. A palette
chosen for how it looks - turquoise out of chia seeds, pink out of yoghurt -
breaks that in the one place the eye is looking, and the row becomes a colour
chart with an organ at the end of it.

**The two row background colours are the free choice**, and they are what makes
one topic look different from the last. Pick them to sit under the five food
colours: rows 1, 3, 5 take the dark one, rows 2 and 4 the light one, so a pale
food (yoghurt, garlic, oats) wants its row dark and a dark food (chocolate,
coffee, blueberries) wants its row light.

Build the base:

```
.venv/bin/python ../engine/recolor_base.py --rows '<dark>,<light>' \
  --waves '<c1>,<c2>,<c3>,<c4>,<c5>' --vibrance 1.05 --contrast 1.04 \
  -o base_<topic>.png
```

Rows 1, 3, 5 take the dark colour and 2, 4 the light one. Put the bright wave
colours on the dark rows. Check the printed "asked vs got" medians and look at
the result before handing it over.

**2. Give the user the prompt**, ready to paste, and tell them to attach
`base_<topic>.png`. The template is in `ImageSwap.txt`; the opening paragraph is
what does the work and goes in unchanged. Filled examples are in `Prompts.txt`.

**3. The user returns the generated poster.** Check it before spending time on it:

```
.venv/bin/python ../engine/check_base.py <poster> --base base_<topic>.png
```

`safe to animate` means the mask still fits. Anything else: ask for a
regeneration, do not try to animate around it.

**3b. Put the captions on**, into the bars the base reserved for them. All ten
are drawn at one size - the longest one sets it, so keep them short; a
seventeen-letter caption shrinks the other nine with it. `add_labels.py` prints
the size it settled on and which caption forced it:

```
.venv/bin/python ../engine/add_labels.py <poster> -l base_<topic>_layout.json \
    -o <poster>_labelled.png \
    --labels 'FOOD|ORGAN,FOOD|ORGAN,FOOD|ORGAN,FOOD|ORGAN,FOOD|ORGAN'
```

**4. Animate.** The silent pass is scrap - render it out of the way, not into
OUTPUT:

```
.venv/bin/python ../engine/flowanim.py <poster>_labelled.png --width 1080 --seconds 8 \
    --base base_<topic>_clean.png \
    --anchored base_<topic>.png --layout base_<topic>_layout.json \
    --drops 0 --reach 0 -o /tmp/<topic>.mp4
```

**4b. Lay the SFX on it, and only this file goes to OUTPUT.** Never a silent
version - the clip is never published without the water sound, so a mute mp4 in
the tree is only something to mistake for the finished one later:

```
ffmpeg -y -i /tmp/<topic>.mp4 -i ../ASSETS/flow_soft_8s.m4a \
       -shortest -c:v copy -c:a aac -b:a 192k ../OUTPUT/<DD.MM>/<topic>_sfx.mp4
```

`<DD.MM>` is the day's folder - `07.09`, made if it is not there yet. One folder
per day, holding the finished clips of that day and nothing else.

**5. Audit before delivering.** Sample a few frames and count what moves outside
the wave mask. It should be single digits. If type, bowls or organs move,
something is wrong — say so rather than shipping it.

## Shipped is shipped

A rule found halfway through a day applies to the videos made after it, never
backwards. Nothing in an `OUTPUT/<DD.MM>/` folder gets rebuilt because a later
clip does it better - not the wave colours, not the caption sizes, not the flat
bowls. The older clips are the record of how this got better, and they are worth
more as that than as five more minutes of polish. Do not offer to redo one.

The corollary is that a mistake is cheap: it costs the next poster, not the last
one. So decide, ship, and write the rule down.

## What is already known to break

These were all found by measurement, and each one cost an hour. Do not rediscover them.

- **Droplets.** Detecting loose droplets to fly them separately picks up letters:
  in the bottom rows a label sits four pixels under the wave, and its letters are
  as pale as a lemon wave. `--drops 0`. Bring droplets back only as an authored
  layer in the base, never by detection.
- **Reaching the organ.** The stretch warp that pushed the wave's tip to the
  organ moves the whole horizontal band, and in the bottom rows that band
  contains the label. It ate the "LY" of LYMPHATIC. `--reach 0`. The wave now
  reaches far enough on its own.
- **Liquid in front of the organ.** The mask runs the full length of the wave,
  including under the bowl and the organ. Painting there puts the liquid on top
  of them. `--base` fixes it: paint only where the poster still equals the base.
- **Speckles that stand still.** The `clean` mask must be opened and closed
  before use, or JPEG noise along the wave's edge leaves unpainted pixels sitting
  still while the wave moves under them.
- **Recolouring.** Gamma on brightness, plain scaling on saturation. Scaling
  brightness kills the specular highlight and everything goes chalky; gamma on
  saturation drives it to 1 and the wave turns into a flat vector shape.
- **Artwork crowding the edges.** The bowl and the organ get placed against the
  wave's two tips, so a wave reaching the edge of the poster drags them out there
  and a vertical feed crops them off. The wave is inset to 20%-79% of the width
  for this reason (`--span` in `make_base.py`), and the prompt states the safe
  area outright. On a new poster, added artwork should stay inside x 154-1382.
- **The captions have a reserved place.** With no text asked for, the generator
  fills the whole row with the bowl and the organ, and a caption added afterwards
  lands on top of them. So the base draws a faint bar under each circle and the
  prompt tells the model to keep it clear. `recolor_base.py` writes
  `base_<topic>_layout.json` with the circle and bar geometry; `add_labels.py`
  and `flowanim.py` both read it rather than working it out again, which is how
  the caption and its bar used to drift apart.
- **No text is asked for at all.** The title is drawn into the base and the row
  captions are added afterwards by `add_labels.py`. Asked for, the captions land
  above the bowl, beside it, or drift once a session has been prompted a few
  times - and a caption in the wrong place is not something the animation can
  correct. Both are typography at known positions, so neither needs a model.
- **The title is drawn into the base, not asked for.** Left to the generator it
  lands wherever it likes, usually inside the top tenth, where a phone's status
  bar and the feed's own crop cut it off. `recolor_base.py --title/--subtitle`
  puts it at 11%-19% of the height every time: clear of the top, clear of the
  first wave. The prompt tells the model the title is already there.
- **Telling the generator where to put things does not work.** It places the
  bowl and the organ where it likes, and once the wave was inset for the safe
  area they stopped meeting the liquid at all. So the base now carries two faint
  circles per row, drawn over the wave's two tips (`--anchors` in
  `recolor_base.py`), and the prompt tells the model to fill them. A mark it can
  see beats a sentence it has to interpret.
- **The bowl comes out flat unless every row says otherwise.** Asked for "a bowl
  of carrots" the generator draws it straight down: a disc of food with no rim
  and no side, which next to a glossy 3D wave reads as a sticker. The fix is the
  camera angle stated twice - once for all five bowls, then again inside each row
  - and made checkable: an elliptical rim, a visible side wall, the food heaped
  above the rim. Stated once at the top it holds for a row or two and then drifts.
- **"A bowl" lets the generator choose the material.** The same wording gave the
  liver poster clear glass bowls and the lungs one opaque ceramic in five
  different colours. Glass is the one that reads beside the liquid, so the row
  says "a clear glass bowl of ...", exactly where it says the camera angle.
- **The organs come back flat unless asked for as renders.** Left alone the
  generator reaches for the textbook - an anatomical diagram, a cross-section
  drawing - which next to a 3D bowl and a glossy wave looks pasted in from another
  document. Ask for volume, a visible near side and the bowl's lighting, in the
  paragraph above the rows and again in each row.
- **The safe area is one fourteenth of the width, not one tenth.** The guide
  circles reach x 112, and a tenth of 1536 is 154. Told to keep everything a
  tenth from the edge, the model keeps the bowl out of the very circle it was
  told to fill - it follows the sentence over the mark. A fourteenth is 110, just
  clear of the circles.
- **The source wave climbs to the right.** Tip to tip it rose 104px, and the
  placement put the left tip on its circle centre, so the right one arrived 102px
  high - it met the organ at the top of its circle instead of in the middle, and
  read as the liquid stopping short of it. Translating the wave down only trades
  one end for the other. `make_base.py --level 1` takes the tip-to-tip slope out
  and leaves the curve alone, so both ends arrive at the same height and both sit
  on a circle centre; `--wave-pos` is then unnecessary, since the placement is
  derived from the same gap and caption height recolor_base.py lays the row out
  with. `--tip-drop` sinks both tips a few pixels below centre if wanted.
- **The wave was cut where it met the bowl and the organ.** Not a join problem:
  the generator covers the guide circle with its artwork and leaves a feathered
  ring a few pixels wide at the edge, where its patch fades into the mark. That
  ring matches neither the anchored base nor anything paintable, and inside a
  circle nothing is repainted - so it stood there as a dark band straight across
  a wave that was moving on both sides of it. `flowanim.py --halo` now decides
  what is covered inside a circle by size rather than by an exact match: an
  opening at `--halo-edge` (15px, the width of the circle's own alpha ramp)
  drops anything thinner than an edge, and what it drops gets the clean base put
  back. Set `--halo 0` to see the old behaviour.
- **The seal may only touch the ribbon's own footprint.** An opening cannot tell a
  feathered edge from thin artwork: the first version of the fix took the
  gallbladder's bile duct off with the ring, because a duct is exactly as thin as
  an edge. It exists so the liquid runs unbroken into the bowl and the organ, so
  it has no business anywhere the liquid does not go. Scoped to the mask it seals
  4 200px instead of 14 200, and the ducts, vessels and stalks that hang off an
  organ survive.
- **An organ named on its own comes back as an object.** "A row of healthy human
  teeth with gums" produced a full denture, sitting on the poster like a prop
  among four pieces of anatomy. Say where it lives - in the gum, on the kidney,
  under the skin - and it is drawn as part of a body.
- **A caption fitted on its own is a caption of its own size.** Ten labels fitted
  one by one came out at ten sizes - 'OATS' at 60px beside 'SLOWER ABSORPTION' at
  38 - and the poster read as ten decisions instead of one label style. One size
  for all ten, found from the longest string. The cost is that a long caption
  shrinks every other one, so write short ones.
- **A transverse wave through a body that stays put is a flag, not a flow.**
  Keep `--snake` at 0 and `--swell` low; the flow reads through the surface
  advection, not through the silhouette swinging.

## Invariants worth re-checking if something looks off

```
waves span x 229-1289 of 1536       = 15% to 84% of the width
row stripes start at 412, 825, 1238, 1649, 2063, each 413 tall
wave rows y 491-702, 904-1115, 1317-1527, 1729-1940, 2142-2353
both tips within ~1px of their circle centre, 25px clear of the caption bar
one traversal of the wave per 8 s   ≈ 95 px/s, the speed the user settled on
```

Ask the user to generate at 1536×2752. Smaller posters are upscaled before
animating and lose sharpness.
