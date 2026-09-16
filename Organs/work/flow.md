# Healthness Shorts — the poster animation flow

When the user says **"nova tema"** or **"idemo dalje"**, run this loop.

The point of the whole design: the liquid is authored once and never
regenerated. An image model cannot redraw a wave the same way twice, so the wave
is never asked to. Only the food, the organs, the title and the palette change.

## Where things live

    ShortPrompt/
      engine/        the shared tools, the three authored wave assets, sfx/
        micro/       the 42 badge balls and nutrients.json, shared with Vitamins
      Organs/        this variant
        INPUT/       base_<topic>.png, and nothing else - it is the file a
                     person opens, to attach it to the prompt
        OUTPUT/      the old per-variant folder. History; nothing writes to it
        work/        everything else: this file, the posters as they come back,
                     the scrap renders, the cues
      OUTPUT/ORGANS/       the finished clips, flat and dateless
      OUTPUT/DONE/ORGANS/  what has gone out. The user fills it by hand
      Vitamins/      the other half of the micro series, split out 16 September
      Foods/ Exercise/ Biohacks/ Macro/ Longevity/   the rest. Not yours to edit
      archive/       checkpoints from before this was a repository

Run everything from inside `Organs/work/`: the engine is `../../engine/`, the
finished clips go to `../../OUTPUT/ORGANS/`, and the interpreter is
`../.venv/bin/python`. Half the paths in this file are wrong from anywhere else,
which is why `render.sh` cd's here before it does anything.
`../../engine-status.sh` checks that this folder is still calling the engine
rather than carrying a copy of it.

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
| `micro/nutrients.json` | food → the micronutrients it is known for |
| `micro/icons/` | the 42 badge balls |
| `render.sh` | animate, sound, mux |
| `meals.json` | what a topic is: title, captions, badge list, the five foods |
| `audit.py` | what moves that should not. Reads the cues and the finale off disk by itself; the verdict carries how many frame pairs it is based on |
| `../../OUTPUT/ORGANS/` | the finished clips, sound already on them |
| `../../engine/sfx/` | the beds, 8 s, normalised to -18 LUFS |

The four `micro_*` rows and `micro/` moved into `../../engine/` on 16 September,
when the series split into Organs and Vitamins: two categories reading one badge
set and one nutrient table is exactly the arrangement `../../CLAUDE.md` rule 1
exists to prevent. They are called by path like every other engine tool.

**`base_layer.png`, `ribbon_mask.png`, `flowanim.py`, `recolor_base.py`,
`check_base.py` and `make_base.py` are the engine's**, in `../../engine/`, and
are called from there by path - never copied in here, and never written bare as
though they sat in this folder (`../CLAUDE.md` rule 1). `ribbon_mask.png` and
`base_layer.png` resolve beside the script that uses them, so they need no flag.
`base_<topic>.png` is this variant's, in `../INPUT/`; so is everything below it
in the table.

## The loop

**1. Pick the topic and the palette.** Five foods, five organs, a title.

**Read `SERIES.md` first.** It is every food and every organ that has already
been on a poster, plus all twenty-three palettes measured off the bases. It
exists because the log stopped: `Prompts.txt` has the full prompt for every clip
up to BONE STRENGTH and nothing after it, so choosing part 21 on 9 September
meant reading the captions back out of twenty-three finished posters to find out
what was spent. That is an afternoon the table now costs a minute. **Add a row
to it when a clip ships** - that is the whole maintenance, and it is what was
skipped nine times.

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
../.venv/bin/python ../../engine/recolor_base.py --rows '<dark>,<light>' \
  --waves '<c1>,<c2>,<c3>,<c4>,<c5>' --vibrance 1.05 --contrast 1.04 \
  -o ../INPUT/base_<topic>.png --work .
```

Rows 1, 3, 5 take the dark colour and 2, 4 the light one. Put the bright wave
colours on the dark rows. Check the printed "asked vs got" medians and look at
the result before handing it over.

**2. Give the user the prompt**, ready to paste, and tell them to attach
`base_<topic>.png`. **There is no negative prompt** - it was removed on
8 September because the generator was deleting what the base drew, the caption
bars among them, and a field listing `caption`, `title` and `changed logo` as
unwanted nouns is where that came from. The body forbids all of it in context
instead. `ImageSwap.txt` says why, at length, so nobody adds one back. The template is in `ImageSwap.txt`; the opening paragraph is
what does the work and goes in unchanged. Filled examples are in `Prompts.txt`.

Print it whole in the terminal - that is rule 8 and it does not change - and pipe
it through `clip.py` on the way, so it is on the clipboard as well:

```
python3 make_prompt.py <topic> ... --body-only \
    | ../../engine/clip.py prompt - --topic <topic>
../../engine/clip.py image <topic>     # the base, for the attach step
../../engine/clip.py prompt            # re-copy after pasting something else
```

**Clip the body, not the file.** `make_prompt.py` writes a header above the
prompt - title, palette, captions, badges, the note - and a list of commands
below it, and both are for the person. On 9 September the whole file went into
the generator instead of the body: the header says
`Captions: 'BUTTER BEANS|PELVIC FLOOR...'` inside a prompt whose body forbids
text in three separate places, and part 21 came back with every bowl and organ
drawn large, **33 to 74px into caption bars 78px tall on all five rows** - worse
than part 18, which set the previous record at 15 to 64. The same body pasted on
its own came back with all five bars at 0px. `--body-only` prints the body and
nothing else; the file is still written, and nothing reads it back.

The buffer is one entry in the system temp directory, overwritten by the next
prompt and refused after 45 minutes with rule 8 quoted back - the opposite of a
`prompt_<topic>.txt` still sitting here three revisions later. `clip.py image`
refuses anything that is not 1536x2752, which is `grab.py`'s safety net pointing
the other way: a base the mask does not fit costs a whole generation before
anyone finds out.

**3. The user returns the generated poster.** Check it before spending time on it:

```
../.venv/bin/python ../../engine/grab.py <topic>     # -> <topic>_poster.jpeg

../.venv/bin/python ../../engine/check_base.py <topic>_poster.jpeg \
    --base ../INPUT/base_<topic>.png
```

`safe to animate` means the mask still fits. Anything else: ask for a
regeneration, do not try to animate around it.

**Copy the poster before regenerating over it.** `grab.py` replaces
`<topic>_poster.jpeg`, and on 10 September that destroyed the better generation:
AGE SLOWER's first pass had four rows right and one wrong, the second pass had
three right, and the first no longer existed to ship. Nothing had shipped from
it, so nothing in `../CLAUDE.md` rule 9 was broken - and that was the wrong
reading of the rule, because what was at risk was not a clip but the only copy of
a generation. `cp <topic>_poster.jpeg <topic>2_poster.jpeg` before the next grab
costs a second and keeps both on the table; `render.sh` takes the poster path as
its second argument, so shipping from the copy needs no second base and no
rename.

**Check that the poster is a new poster.** On 10 September the same image was
grabbed three times under three filenames - `...143431`, `...143909`,
`...144659` - because what was being saved was the generation already in the
thread, not the one asked for after it. `check_base.py` printed the same five
wave differences each time (3.7, 9.3, 3.2, 9.9, 6.4) and every measured disc
matched to a tenth of a percent, which is the tell; the proof is one line:

    ../.venv/bin/python -c "import hashlib;from PIL import Image;\
        print(hashlib.md5(Image.open('<topic>_poster.jpeg').tobytes()).hexdigest()[:12])"

Identical pixels mean the regeneration has not happened yet. Say so and wait -
the clip built from it would be the clip the regeneration was meant to replace.

**A base element missing from the poster is a regeneration, full stop.** The row
stripes, the waves, the caption bars and the logo are the base's own; if one of
them comes back covered or painted out, ask for the poster again with the same
prompt and do not spend a minute deciding whether it can be worked around. Part
18 came back with the bowls drawn so large that artwork reached **15 to 64 px
into caption bars that are 78 px tall** - against 7 px on the two posters that
had ever intruded at all - and a 60 px caption drawn into that lands on glass and
tissue. Measure the depth per bar rather than eyeballing it: the artwork is
there, the bar is a base element, and the number says immediately which of the
two it is.

And do not reach for the restore. Rule 9 allows putting base pixels back, but
only over a region with nothing that legitimately belongs on top of it: on part
18 what had spilled into the bars was the bowls and the organs, so a restored bar
would have cut them off with a hard horizontal edge. That is amputation, not
restoration. Anything between the two cases is a regeneration, because
deliberating is how a bad poster ships.

The poster lands in `work/` and stays there, under the name git carries:
`.gitignore` ignores `*.jpeg` and un-ignores `*_poster.jpeg`, and `grab.py`
writes the second since 548f5f6. For one morning it wrote the first while the
rule said to carry the second, and every poster grabbed in that window was still
being thrown away - the name is load-bearing, not cosmetic. Every tool reads the jpeg directly - the labelled
poster built from `<topic>_poster.jpeg` is byte-identical to one built from a PNG
copy of it, checked on 9 September - so the conversion step that used to sit here
bought nothing but a lossless copy of a lossy original at twice the size.
`INPUT/` holds base images and nothing else (`../CLAUDE.md` rule 7) - until
8 September every generated prompt in this folder told the reader to put the
poster there, which is the one thing that folder forbids.

**3b. Put the captions on**, into the bars the base reserved for them. All ten
are drawn at one size - the longest one sets it, so keep them short; a
seventeen-letter caption shrinks the other nine with it. `add_labels.py` prints
the size it settled on and which caption forced it:

```
../.venv/bin/python ../../engine/add_labels.py <topic>_poster.png \
    -l base_<topic>_layout.json -o <topic>_labelled.png \
    --labels 'FOOD|ORGAN,FOOD|ORGAN,FOOD|ORGAN,FOOD|ORGAN,FOOD|ORGAN'
```

**4. Animate, sound it, ship it.** In this folder that is one command, because
the animator and the sound have to agree on when the badges land, and typing the
times twice is how a pop ends up half a frame off the badge it belongs to:

```
./render.sh <topic> <topic>_labelled.png 'auto:FOOD,FOOD,FOOD,FOOD,FOOD'
```

`auto:` reads `../../engine/micro/nutrients.json`. To choose the badges by hand, pass them instead -
`;` between rows, `,` inside one: `'K,Folate,Iron;Nitrates,Folate;...'`. Anything
after the third argument goes straight to `flowanim.py`.

Out comes `../../OUTPUT/ORGANS/<topic>_organs.mp4` with the water and the pops on
it. `work/<topic>_silent.mp4` is the scrap pass; `work/<topic>_cues.txt` is what
the sound was cut against. The folder is flat and dateless - `../../CLAUDE.md`
rule 12, because a day folder took its name from the clock and a session that ran
past midnight wrote into a new one while the evening's work looked abandoned.
**Only the finished cut goes there**: the clip is never published
without sound, so a mute mp4 in `OUTPUT/` is only something to mistake for the
finished one later - and neither does anything else land there. That includes
what a *check* writes: measuring the mix means decoding a shipped clip, and an
intermediate written beside its source rather than into a named scratch folder
leaves a stray `.wav` in a day folder. `../CLAUDE.md` rule 6, second half,
which is that incident.

The three steps it runs, if one is ever needed alone. **Run them from `work/`,
which is where `render.sh` cd's to before anything else** - the engine is two
folders up from here and the day's folder one up, and half of these paths are
wrong from anywhere else:

```
../.venv/bin/python ../../engine/flowanim.py <topic>_labelled.png \
    --width 1080 --seconds 8 --overlay micro_overlay \
    --base base_<topic>_clean.png --anchored ../INPUT/base_<topic>.png \
    --layout base_<topic>_layout.json --drops 0 --reach 0 \
    --micro 'auto:FOOD,...' --micro-cues <topic>_cues.txt \
    --micro-times 0.25,1.35,2.45,3.55,4.65 \
    --finale auto --finale-cue <topic>_finale.txt \
    --surge 0.30 --surge-dur 0.34 --surge-stagger 0.05 \
    -o <topic>_silent.mp4

S=$(ffprobe -v error -show_entries format=duration -of csv=p=0 <topic>_silent.mp4)

../.venv/bin/python ../../engine/micro_audio.py --cues-file <topic>_cues.txt \
    --finale-file <topic>_finale.txt --finale-out <topic>_riser.wav \
    --seconds "$S" -o <topic>_pops.wav

T=$(cat <topic>_finale.txt)
D0=$(awk -v t="$T" 'BEGIN{printf "%.2f", t - 0.28}')
D1=$(awk -v t="$T" 'BEGIN{printf "%.2f", t + 1.12}')
ffmpeg -y -loglevel error -i <topic>_silent.mp4 \
  -i ../../engine/sfx/flow_soft_warmer_8s.m4a \
  -i <topic>_pops.wav -i <topic>_riser.wav \
  -filter_complex \
"[1:a]volume=0.30,volume='1-0.28*clip(min((t-${D0})/0.20,(${D1}-t)/0.35),0,1)':eval=frame[w];\
[2:a]volume=0.85[p];[3:a]volume=1.0[f];\
[w][p][f]amix=inputs=3:duration=first:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[a]" \
  -map 0:v -map "[a]" -shortest -c:v copy -c:a aac -b:a 192k \
  -movflags +faststart ../../OUTPUT/ORGANS/<topic>_organs.mp4
```

**This block was run command for command on 16 September 2026 and its output
compared against `render.sh`'s**: the cue file byte-identical, and the finished
mp4 byte-identical to `../../OUTPUT/ORGANS/liver_organs.mp4`. That is the only
version of "the prose matches the script" worth writing down, and this block has
needed it twice - the second time because the bed changed to `flow_soft_warmer`,
the bed gain to 0.30 and the rhythm to `0.25,1.35,...` while these lines still
said `flow_soft_8s`, `volume=1.0` and `1,2,3.2,4.4,5.6`. Anyone following the
stale version would have rebuilt a clip the mix had already been fixed out of.


Three things in there are load-bearing, and each was wrong in this block until
8 September, when the fallback quietly stopped producing what `render.sh`
produces:

**The animator and the mask are the engine's, by path.** `flowanim.py` and
`ribbon_mask.png` written bare read as files in this folder, which is the layout
that ended on 7 September and what rule 1 exists to stop anyone relearning. The
mask needs no flag at all: it resolves beside the script it belongs to.

**The bed is ducked, and the duck is written against the instant in
`<topic>_finale.txt`.** Without those two `awk` lines the water never steps back
under the chord. That is not a subtlety of taste: the clip the user auditioned
the finale in had the chord at unity through a 0.28 duck, so a mix without it is
not the ending that was approved.

**The riser is a fourth input at 1.0, not part of the pops.** The badge gain
belongs to badges: summed into `<topic>_pops.wav` the chord got `volume=0.85`
with them and reached the mix 1.4 dB under the level `impact.finale` returns -
and Exercise's 0.62 put the same chord 4.2 dB under. One number in the engine
arriving as three levels is what `engine/impact.py` exists to prevent.

Without `--micro` the animator renders exactly the clip it rendered before the
badges existed, so an old command line is still good.

**4b. What the finale is.** From 8 September the clip ends on one: the five
organs light again as the engine's highlight reaches each of them, the badges
light as it passes their columns, and a riser answers the count the five rows
have been keeping. `render.sh` passes it - `--finale auto --surge 0.30` - and
nothing has to be typed twice, because the instant is computed once in
`flowanim.py`, published to the overlay, and written to `<topic>_finale.txt` for
the sound.

The rhythm moved to make room: `--micro-times 1,2,3.2,4.4,5.6`. At the shipped
`1,2,4,5.5,7` the last pop settles at 7.60 of an 8s clip and there is nothing
0.35s can hold. **The room is not bought with `--seconds`:** the surface travels
a whole number of ribbon lengths, which is what makes the loop seamless, so 9
seconds costs 92px/s -> 82 and no flag gives it back.

**5. Audit before delivering.** `audit.py` counts what moves outside the wave
mask, in the windows between one badge finishing and the next one landing - the
only stretches where the liquid is the only thing entitled to move:

```
../.venv/bin/python audit.py ../../OUTPUT/ORGANS/<topic>_organs.mp4
```

**The spec comes off disk now, so the bare command is the strict check.** It
reads `<topic>_cues.txt` and `<topic>_finale.txt`, which `render.sh` has already
written, and says so in its first line; the flags remain for re-checking an old
clip by hand. Before 9 September the spec was the typist's job and leaving it out
failed the wrong way: measured on `cholesterol_silent.mp4`, both flags gave 4
windows and **12 frame pairs**, `--cues` alone gave 5 windows and a false 60 176
px, and neither gave **one window and three pairs** - and printed the same word,
`clean`, off a quarter of the looking. Three samples at 0.05, 3.96 and 7.87, and
7.87 is after the finale has stopped moving.

So the verdict now carries its own denominator - `clean, 12 frame pairs over 4
windows`. A number that cannot be compared with the same number a week later is
not a check, and `clean` on its own could not be.

It should be single digits. If type, bowls or organs move, something is wrong —
say so rather than shipping it.

## Shipped is shipped

A rule found halfway through a day applies to the videos made after it, never
backwards. Nothing in an `../OUTPUT/<DD.MM>/` folder gets rebuilt because a later
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
- **The liquid you see between an organ's branches is not the animation's.** The
  wave is painted into the base along the whole row and the generator draws the
  organ over it, so an organ that is mostly holes shows the base's wave between
  its parts. Measured on the lungs clip: those pixels change by **0** between
  3.0s and 3.5s while 7 069 px of wave to the left of the organ change.
  On 9 September this was attacked from the overlay - `seal_gaps` put the row
  colour back over the organ's closed silhouette minus itself - and **it was
  reverted the same morning.** Two versions, two failures: excluding the ribbon
  left the leak it existed to fix, and including the ribbon cut a black bite out
  of the wave at the junction in **every** row, which is worse than the leak.
  The junction is the problem: the wave's tip and the organ's edge interleave
  there at a few pixels' scale, and no mask drawn from the organ's silhouette
  separates them cleanly. If this is tried again it belongs at generation time -
  an organ drawn solid where it crosses the wave - not at paint time.
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
- **And naming a joint asks for the bone.** Part 14 said "the jaw joint just in
  front of the ear, where the lower jaw meets the skull", which is where it lives
  and still came back as a bare skull with the joint picked out in red - a prop
  among four soft organs, and it cost a regeneration. A joint is bone by
  definition, so the sentence cannot save it: ask for the soft tissue that does
  the work instead. "The chewing muscle just in front of the ear that clenches,
  under the skin of a living face, with no bone showing" keeps the same row and
  the same food, because what magnesium relaxes is the muscle, not the hinge.
  **And that sentence stopped working on 10 September.** STRESS RELIEF pasted it
  verbatim and got a whole flayed head - a face with the skin off, filling 72% of
  its guide circle, the same prop among four soft organs the part 14 skull was.
  The address is what does it: "just in front of the ear, under the skin of a
  living face" names a face, and a face is what gets drawn. So drop the address
  as well as the joint and ask for the muscle as an object - "a single skeletal
  muscle lifted out on its own, its fibres running the length of it and tapering
  to a pale tendon at each end, with no bone, no skin and no head anywhere in the
  image" came back a clean spindle at 38% of the disc on the next pass. The rule
  that survives both is the one two entries down: ask for a thing that could be
  lifted out of a body in one piece, and say nothing about where it lived.
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
- **Name a part of an organ and the organ is what arrives.** Asked for the aorta,
  part 17 drew a whole heart with the aorta on it. The bile duct brought the
  gallbladder (16), the coronary arteries and the portal vein brought the heart
  and the liver, the islets brought the pancreas and the meniscus brought the
  knee (19). Every one is anatomically right and every one puts an organ the
  series has already used back on the poster - so the caption says CORONARY while
  the picture says heart. It is the same shape as the joint and the magnification:
  a part has no outline of its own until the thing it belongs to is drawn around
  it. Treat the parent organ as spent when you choose the row, or accept that the
  row is a second view of it, and pick foods and captions knowing that.
- **Asking for a piece of tissue asks for a slab of it.** "A piece of skin torn
  at its edges so that it ends in an irregular outline" is `flow.md`'s own fix for
  part 15's lens bubble, and on AGE SLOWER it produced a **rectangular tile** with
  hard vertical sides - twice, the second time against a sentence that said "no
  straight edges and no square corners anywhere on it". The tooth in the same clip
  did the same thing: "one tooth in the gum" came back as a **cut block of jaw**,
  and so did "with no jaw, no block of bone and nothing cut square". Both are the
  section rule from further down, arriving as a box instead of as a frame: a piece
  of a sheet-like organ has no outline of its own, so the generator supplies the
  cut. The measurement is the organ's own bounding box - **how much of it the
  artwork fills**. Four cut-out organs on that poster filled 43-60% of theirs; the
  tile filled 85% and the skin block 76%, against ~100% for a true rectangle. Over
  about 70% and it is a slab, whatever the sentence asked for. What works is an
  organ with a boundary of its own: the tooth row became a heart and arrived right
  on the first pass, at 61% of its disc and 54% of its box.
- **Two entries about act two moved to `../../Vitamins/work/flow.md`** on
  16 September, when the two-act cut left this folder: `ImageDraw` replacing
  pixels rather than compositing them, and act one's title ghosting into exactly
  where act two puts its heading. Both were found here, on these posters, and
  both now bite only where there is a card to draw - so they live where the card
  is. The palette numbers in the second one are this corpus's: pressure 74.3
  against 16.8, metabolism 81.1 against 19.6, ageing 91.9.
- **A structure thinner than a finger comes back correct and unreadable.** The
  vagus nerve, asked for as "a pale cord with fine branches coming off it, lifted
  clear of the tissue around it", arrived exactly as described and covered
  **2 965 px, 5.0% of its guide circle** - against 51 to 78% for the adrenal, the
  stomach, the heart and the brain on the same poster. Nothing was wrong with it
  except that at arm's length the row reads as a bowl and a wave running into
  empty background. `flowanim.py` prints this number per row when it lights the
  organs, and the poster can be measured for it before any of that: artwork
  inside the right-hand circle, as a percentage of the circle. Under about 30% is
  a row with no organ in it, and the fix is a thicker organ, not a bigger prompt.
- **Two organs cannot be had at all, and the sentence is not the problem.** The
  spleen came back as a kidney twice on 10 September - bean shape, concave hilum,
  artery, vein and ureter - the second time against a sentence that named all
  four and forbade them. "A short length of small intestine" came back once
  correctly and once as the whole abdominal package, colon frame and caecum and
  appendix included, against a sentence forbidding those three by name. Both are
  the parent-organ rule above, but with a twist that matters for what you do
  next: **the parent is what has the outline, and the child has none.** A spleen
  next to the generator's kidney and a length of jejunum next to the generator's
  gut package are not underspecified, they are outgunned, and a third sentence is
  not the difference. Swap the row. Iron's fifth story moved from the spleen to
  the thyroid, whose silhouette nothing else shares, and its fourth from the
  small intestine to the stomach, which comes back standalone every time - and
  both new organs arrived right on the first pass. Four generations for one clip,
  three of them spent describing instead of swapping.
  STRESS RELIEF added a third case and the same answer: "the lining of the gut,
  its velvety inner surface facing the viewer, a short piece torn at its edges"
  came back as the whole colon frame, which also hung **523 px of itself 21 px
  into a caption bar 78 px tall** - so the row failed twice over, the wrong organ
  and a base element covered. The row moved to the stomach, which is now three
  for three.
- **18px in the audit is the subtitle, not artwork.** `iron` reported 18 px
  outside the wave: a **1px wide, 22px tall line at poster x 867, y 341-362**,
  which is inside the subtitle, plus two single pixels. bones2 measured the same
  thing at 1x16px, x 997, y 341-363. It is the encoder quantising type's
  antialiased edge between two frames. Anything in the title block at that height
  with a width of one pixel is this, and it does not need looking at twice - but
  do locate it rather than shipping on the word `clean`, which is what the
  threshold prints for anything under 400.
  **It is not only the title block.** METABOLISM reported 17 px in one frame pair
  and both clusters were captions: **1 px wide, 16 px tall at poster x 253,
  y 751-772**, which is inside row 1's caption bar, and a single pixel at x 226,
  y 1998 inside row 4's. Same signature, different type - so the test is the
  *width*, one pixel, and not where it sits. `audit.py` does not print positions;
  this locates them, and it writes nothing (`../CLAUDE.md` rule 6):

      ../.venv/bin/python -c "
      import numpy as np, sys; sys.path.insert(0,'.'); import audit
      from PIL import Image; from scipy import ndimage
      W,H=1080,1934
      m=Image.open('../../engine/ribbon_mask.png').convert('L').resize((W,H),Image.LANCZOS)
      allowed=ndimage.binary_dilation(np.array(m)>128,np.ones((31,31)))
      f0=audit.frame('<clip>',0.05,W,H); f1=audit.frame('<clip>',0.05+1/12,W,H)
      stray=(np.abs(f0-f1).max(axis=2)>10)&~allowed
      lab,n=ndimage.label(stray)
      [print(int((lab==k).sum()),'px  x',np.where(lab==k)[1].min(),np.where(lab==k)[0].min())
       for k in range(1,n+1)]"

- **Ask for a thing that could be lifted out of a body in one piece.** This is
  the rule the two failures below are both special cases of, and part 17 is the
  test that it holds: five organs written as whole objects with their own
  boundary - a cut length of vessel with the cells inside it, the aorta arching
  off a heart, one tooth in the gum, a cluster of alveoli hanging like a bunch of
  grapes, a lymph vessel with its valves - came back with **no roundel in any row**
  (radius spread 22.6-41.9% against a 12% threshold), nothing on a caption bar and
  nothing outside the safe area, first pass. A section, a magnification and a
  joint all name something that has no outline of its own, so the generator
  supplies one: a frame, a lens bubble, a bone.
- **Asking for something magnified asks for the circle around it.** Part 15 wanted
  the gut's villi and the skin's pigment cells, both written as "magnified". Both
  came back as photographs inside a hard circular frame - radius spread 4.8% and
  0.4% around their own centroid, where a piece of tissue measures 25-40% - even
  though the prompt forbids an organ in a circle in three separate sentences. The
  word is the cause: every textbook draws a magnified structure inside a lens
  bubble, so asking for one asks for the bubble. Ask for **a piece of the tissue,
  torn at its edges so it ends in an irregular outline**, and drop "magnified"
  entirely. Measure it rather than looking: fit a circle to the artwork's own
  boundary, because a roundel slightly smaller than the guide mark passes any test
  written against the mark's radius.
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
