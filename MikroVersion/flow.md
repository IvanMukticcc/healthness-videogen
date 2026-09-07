# Healthness Shorts — the poster animation flow

When the user says **"nova tema"** or **"idemo dalje"**, run this loop.

The point of the whole design: the liquid is authored once and never
regenerated. An image model cannot redraw a wave the same way twice, so the wave
is never asked to. Only the food, the organs, the title and the palette change.

## Where things live

    ShortPrompt/
      OTHER/         the tools, the bases, the mask, the generated posters
      CHECKPOINT_*/  the base generator's own history. The newest is upstream
      MikroVersion/  the same, plus the micronutrient badges. This file.
        INPUT/         the base handed to the generator, the poster it returns
        ASSETS/Micro/  the badges, and the blank sphere they are cut from
        ASSETS/        the water beds, copied in so the folder stands alone
        OUTPUT/        finished videos, one folder per day (`07.09/`)
        work/          scrap renders and cue files
      ASSETS/        water SFX, both CC0; `Vitamini/` and `Minerali/` as generated
      OUTPUT/        `OTHER/`'s finished videos

Run everything from inside `MikroVersion/`. It writes nothing outside itself; it
reads `../ASSETS/Vitamini` once, to recover the sphere, and `./sync.sh` to see
what the newest checkpoint has changed since this copy was taken.

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
| `micro_icons.py` | builds the badges. `--all` for the catalogue, `--one 'Label:v\|m\|o'` for one |
| `micro_overlay.py` | where the badges go and how they enter. Imported by `flowanim.py` |
| `micro_audio.py` | the pop, synthesised. One note per row, climbing |
| `nutrients.json` | food → the micronutrients it is known for |
| `render.sh` | animate, sound, mux |
| `audit.py` | what moves that should not |
| `sync.sh` | what the newest checkpoint changed that this folder has not taken |
| `OUTPUT/<DD.MM>/` | the day's finished clips, sound already on them |
| `ASSETS/` | the water beds, 8 s, normalised to -18 LUFS |

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
.venv/bin/python recolor_base.py --rows '<dark>,<light>' \
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
.venv/bin/python check_base.py <poster> --base base_<topic>.png
```

`safe to animate` means the mask still fits. Anything else: ask for a
regeneration, do not try to animate around it.

**3b. Put the captions on**, into the bars the base reserved for them. All ten
are drawn at one size - the longest one sets it, so keep them short; a
seventeen-letter caption shrinks the other nine with it. `add_labels.py` prints
the size it settled on and which caption forced it:

```
.venv/bin/python add_labels.py <poster> -l base_<topic>_layout.json \
    -o <poster>_labelled.png \
    --labels 'FOOD|ORGAN,FOOD|ORGAN,FOOD|ORGAN,FOOD|ORGAN,FOOD|ORGAN'
```

**4. Animate, sound it, ship it.** In this folder that is one command, because
the animator and the sound have to agree on when the badges land, and typing the
times twice is how a pop ends up half a frame off the badge it belongs to:

```
./render.sh <topic> INPUT/<topic>_labelled.png 'auto:FOOD,FOOD,FOOD,FOOD,FOOD'
```

`auto:` reads `nutrients.json`. To choose the badges by hand, pass them instead -
`;` between rows, `,` inside one: `'K,Folate,Iron;Nitrates,Folate;...'`. Anything
after the third argument goes straight to `flowanim.py`.

Out comes `OUTPUT/<DD.MM>/<topic>_micro.mp4` with the water and the pops on it.
`work/<topic>_silent.mp4` is the scrap pass; `work/<topic>_cues.txt` is what the
sound was cut against. `<DD.MM>` is the day's folder - `07.09`, made if it is not
there yet. **Only the finished cut goes there**: the clip is never published
without sound, so a mute mp4 in `OUTPUT/` is only something to mistake for the
finished one later.

The three steps it runs, if one is ever needed alone:

```
.venv/bin/python flowanim.py INPUT/<topic>_labelled.png --width 1080 --seconds 8 \
    --mask ribbon_mask.png --base INPUT/base_<topic>_clean.png \
    --anchored INPUT/base_<topic>.png --layout INPUT/base_<topic>_layout.json \
    --drops 0 --reach 0 --micro 'auto:FOOD,...' \
    --micro-cues work/<topic>_cues.txt -o work/<topic>_silent.mp4

.venv/bin/python micro_audio.py --cues-file work/<topic>_cues.txt \
    --seconds 8 -o work/<topic>_pops.wav

ffmpeg -y -i work/<topic>_silent.mp4 -i ASSETS/flow_soft_8s.m4a -i work/<topic>_pops.wav \
  -filter_complex "[1:a]volume=1.0[w];[2:a]volume=0.6[p];\
[w][p]amix=inputs=2:duration=first:normalize=0[m];\
[m]alimiter=limit=0.82:level=disabled[a]" \
  -map 0:v -map "[a]" -shortest -c:v copy -c:a aac -b:a 192k \
  OUTPUT/<DD.MM>/<topic>_micro.mp4
```

Without `--micro` the animator renders exactly the clip it rendered before the
badges existed, so an old command line is still good.

**5. Audit before delivering.** `audit.py` counts what moves outside the wave
mask, in the windows between one badge finishing and the next one landing - the
only stretches where the liquid is the only thing entitled to move:

```
.venv/bin/python audit.py work/<topic>_silent.mp4 --cues work/<topic>_cues.txt
```

It should be single digits. If type, bowls or organs move, something is wrong —
say so rather than shipping it.

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
- **A badge is not allowed to sit on a guide circle.** The bowl fills one and the
  organ the other, and a badge over either covers the thing the row is about. The
  badges are laid out in the gap between the two circles and shrink to fit it.
- **Hue rotation cannot hit a given colour, and throws contrast away on the way.**
  The badges are the app's blue, green and orange, so the sphere's luminance is
  gradient-mapped onto each rather than rotated - rotating the bright orange
  template towards green lands on a lime. Rotating ball and letter together also
  kills the letter: 46° against 26° reads on orange, 100° against 80° does not.
  Map the ball, then draw the letter on top in white.
- **A badge that fades out is a smudge for half a second**, and that is the frame
  a feed freezes on. `--micro-fade 0`, which is the default: they stay up and the
  loop cuts.
- **Telling the generator to cover a mark is not telling it to remove one.**
  Google Flow read "so that no part of either circle is still visible" and painted
  a bright disc over the circle, then stood the bowl on that. Measured, that plate
  sits 140-155 levels off the base, so no threshold catches it without eating the
  bowl, and four ways of removing it afterwards - flatness, radial peel, colour
  blend, connectivity - all left either a pale ring around the food or white
  wedges cut into it. It is a prompt problem, and the prompt now names the circles
  as alignment marks and forbids the replacement by name. Not to be confused with
  the feathered ring `--halo` seals, which is a few pixels wide and is real.
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
