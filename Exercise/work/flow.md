# Healthness Shorts — the exercise animation flow

When the user says **"nova tema"** or **"idemo dalje"**, run this loop.

The point of the whole design: **the parts that must be identical are never
regenerated.** An image model cannot redraw a wave the same way twice, so the
wave is never asked to. It cannot redraw a body the same way twice either, so
from this version on the body is not asked to. Only the athlete on the left, the
title and the palette change.

## Where things live

    ShortPrompt/
      engine/           the shared tools, the wave assets, sfx/ - never copied in
      Foods/ Micro/ Biohacks/   the other variants. Not ours to touch
      Exercise/         this one: lifts, bodies, muscles
        INPUT/            base_<topic>.png, and nothing else
        OUTPUT/           finished clips, one folder per day (`08.09/`)
        work/             everything else, including this file
          icons/            the badges, and the blank sphere they are cut from
          palettes/         a reference base, so a new one has something to sit beside

Run everything from inside `Exercise/work/`. It writes nothing outside itself
except the base, which goes to `../INPUT/`, and the finished clip, which goes to
`../OUTPUT/<DD.MM>/`. `icons/` is where the badges live and where
`muscle_icons.py` writes them - it wrote to `ASSETS/Muscle/` until 8 September
2026, which nothing had read since the three-folder layout landed.

## Files that carry the design

| file | what it is |
| --- | --- |
| `../../engine/base_layer.png` | the reference base, shared by every variant: five row stripes, five identical waves, logo. 1536×2752 |
| `../../engine/ribbon_mask.png` | where the waves are. Authored from `base_layer.png`, **geometry only** |
| `base_<topic>.png` | one per topic: `base_layer.png` recoloured. Same geometry, so the same mask fits |
| `../../engine/flowanim.py` | the animator |
| `../../engine/recolor_base.py` | makes a new palette |
| `../../engine/check_base.py` | did the generator leave the waves alone? |
| `../../engine/make_base.py` | rebuilds `base_layer.png` from a freshly generated wave poster. Rarely needed |
| `muscles.py` | the vocabulary: label, tier, colour, body regions. Everything else reads it |
| `bodymap.py` | the figure, front and back. `--sheet` for the catalogue |
| `body_overlay.py` | where the body sits in the row and how a muscle ignites |
| `muscle_icons.py` | builds the badges. `--all` for the catalogue, `--one 'Label:p\|s\|t'` for one |
| `muscle_overlay.py` | where the badges go and how they enter. Imported by `flowanim.py` |
| `muscle_audio.py` | the hit, the chord and the bed. All three synthesised - `../../engine/sfx/lift_bed_8s.m4a` is this file's own `--bed` output, and reproduces from it at waveform correlation 0.999983, so it is generated rather than licensed and could be rebuilt if it were ever lost |
| `exercises.json` | lift → the muscles it works, prime mover first |
| `../../engine/grab.py` | takes the newest 1536×2752 image out of Downloads and names it `<topic>_poster.jpeg` |
| `clean_poster.py` | puts the base back where the generator drew outside its brief |
| `left_disc.py` | fills the left circle with that row's wave colour, in the base and its clean copy |
| `render.sh` | animate, sound, mux. Refuses a poster with empty left circles |
| `PROMPTING.md` | why the prompt says what it says, and what each line cost |
| `audit.py` | what moves that should not |
| `../OUTPUT/<DD.MM>/` | the day's finished clips, sound already on them |

## The loop

**A clip in `OUTPUT/` came from a generated poster. Always.** Every variant here
follows the same four steps and this folder is not an exception to them:

    1. build base_<topic>.png       ../../engine/recolor_base.py, then left_disc.py
    2. write the prompt             ImageSwap.txt filled for the topic, handed
                                    over whole in the terminal - never a file,
                                    never a diff, never "change only row 3".
                                    PROMPTING.md is why it says what it says
    3. the user returns the image   grab.py, then check_base.py, then
                                    clean_poster.py
    4. caption it and render        add_labels.py, then ./render.sh with the
                                    labelled poster as the second argument

`render.sh` will not write to `OUTPUT/` unless the file it is handed carries an
athlete in every left circle. A labelled **base** is a file that plausibly exists
in here - the six recipes in `Prompts.txt` were captioning the base until
8 September 2026 - and handed one, every other check passes, because the waves it
carries are the base's own. The left circles are the only thing a generation
adds: 29 to 74 off the base on a real poster, 0.0 on all five rows of a labelled
base.

**1. Pick the topic and the palette.** Five lifts, a title, and a colour scheme
clearly different from the last few. Build the base:

```
../.venv/bin/python ../../engine/recolor_base.py --rows '<dark>,<light>' \
  --waves '<c1>,<c2>,<c3>,<c4>,<c5>' --vibrance 1.05 --contrast 1.04 \
  --title '<TITLE>' --subtitle '<SUBTITLE>' \
  -o ../INPUT/base_<topic>.png --work .
```

`--work .` is what keeps the two working files here: the base itself is the one
file a person opens, so it goes to `../INPUT/` alone, and its clean copy and its
layout stay in `work/` beside everything else (`../CLAUDE.md` rule 7).

Rows 1, 3, 5 take the dark colour and 2, 4 the light one. Put the bright wave
colours on the dark rows.

**The waves may not be red, orange or amber.** The badges are those colours. The
allowed arc is lime, cyan, violet, fuchsia, teal, and `Prompts.txt` says what was
measured and what it cost. Six filled palettes are in there ready to paste.

Pick the five lifts so the bodies differ — five presses light the same chest five
times and the viewer has seen the whole clip by row two. Check before building:

```
../.venv/bin/python -c "import muscle_overlay as m; print(m.resolve('auto:HIP THRUST'))"
```

**1b. Fill the left circle.** The lifter sits in a circle the way the food sits
in a bowl, and the circle is drawn rather than asked for:

```
../.venv/bin/python left_disc.py -b ../INPUT/base_<topic>.png \
    -c base_<topic>_clean.png -l base_<topic>_layout.json
```

It reads each row's own wave colour and puts the disc down in both files —
identical in the two, so the animator reads it as design rather than as a guide
mark to wipe. Both files are written in place, and nothing needs moving: the base
is already in `../INPUT/`, which holds base images and nothing else.

**2. Give the user the prompt**, whole and ready to paste, and put the base on
the clipboard for them in the same breath:

```
osascript -e 'set the clipboard to (read (POSIX file "'"$PWD"'/../INPUT/base_<topic>.png") as «class PNGf»)'
```

It lands as a PNG - `osascript -e 'clipboard info'` says `«class PNGf», 763267`
against a 763 KB file - so it pastes straight into the generator with ⌘V and
nobody has to find the folder. `open ../INPUT` is the fallback if the clipboard
is wanted for something else.

Tell them to attach `base_<topic>.png`. The template is in `ImageSwap.txt`; the opening
paragraph is what does the work and goes in unchanged. Filled examples are in
`Prompts.txt`. **`PROMPTING.md` is why it says what it says** - read it before
changing a word of the template, because every line in it was paid for by a
poster that came back wrong.

Sending one back is cheap and cheaper than a render: say the number, name the
row, and hand over the whole prompt again with that paragraph rewritten. Never a
diff. A reject costs one generation; a poster that passes and should not costs a
render, a look, a rewrite and then a generation anyway.

The generator now fills **only the left circle**. Say so; it is the one thing
about this version that a prompt copied from the food version gets wrong.

**3. The user returns the generated poster.** It does not have to be moved by hand — `../.venv/bin/python ../../engine/grab.py <topic>` takes the newest file in Downloads whose size is exactly 1536×2752 and renames it `<topic>_poster.jpeg` here. The size is the safety net: a screenshot or a photo is not that, and the generator's own filename changes every time. The `_poster` in the name is not decoration: the repository ignores `*.jpeg` wholesale and un-ignores `*_poster.jpeg`, and a poster is the only artefact here that no command can remake - the base, the labels and the clip all come back from a script, and an image model cannot be asked twice for the same picture. Then check it before spending time on it:

```
../.venv/bin/python ../../engine/check_base.py <poster> --base ../INPUT/base_<topic>.png
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
    -l base_<topic>_layout.json -o <topic>_clean.png            # circle mode
../.venv/bin/python clean_poster.py <poster> --base ../INPUT/base_<topic>.png \
    -l base_<topic>_layout.json --bars 0 --radius 138 \
    -o <topic>_clean.png                                        # scene mode
```

**Both flags in the scene-mode line are load-bearing.** `--bars 0` leaves the
generator's caption bars alone, because on a photograph the captions go on glass
and a restored bar would be a second bar under the pane. And the default
`--radius` of 340 is a circle-mode number - it is sized for the stroked ring the
generator used to draw and for the caption bar's far corners, neither of which
exists here. On POWER GOES FIRST it took **69657 px** out of row 4, carving a
pale disc the size of a dinner plate out of the sprint lane's turf and putting
the guide circle and both bars back inside it, with a hard round edge across the
track. That is the wrong side of rule 9's line: the turf legitimately belongs
there, so it is not a region to restore. At 138 the restore is exactly the guide
circle, which the body's own disc covers at render time, and the other four rows
go from 2540-3700 px to 1974-2317 - the same repair, without the hole.

The caption bars matter as much as the ring: `add_labels.py` takes its ink from
whether the row is light or dark, which is right for the bar the base drew and
wrong for a photo lying over it — and the discs come back inverted against their
rows, so every left caption would be drawn in the one colour the thing under it
shares.

**3b. Put the captions on**, into the bars the base reserved for them. The right
caption names the muscle **group**, not a muscle — the body beside it is already
saying which muscles, in colour, one at a time:

```
../.venv/bin/python ../../engine/add_labels.py <topic>_clean.png \
    -l base_<topic>_layout.json -o <topic>_labelled.png \
    --labels 'LIFT|GROUP,LIFT|GROUP,LIFT|GROUP,LIFT|GROUP,LIFT|GROUP'
```

The input is the **cleaned** poster, never the base: the base has no athletes on
it, and labelling it would throw the generator's work away at the last step.

Watch the size it prints. Every caption is set at one size and the longest label
picks it, so a single long one shrinks all ten: `CONCENTRATION CURL` gave 30px
where `SUITCASE CARRY` gives 40. If one label is much longer than the rest,
shorten that one rather than accepting the size it forces.

**3c. On a photographic poster, put the captions on glass.** On a coloured row
`add_labels.py` is safe: it takes its ink from the row's light/dark flag and the
row is one flat colour. On a photograph that guarantee is gone - the flag still
says light, and what actually lies under the caption is whatever the picture put
there. On NO GYM REQUIRED row 4 that was the black sled, so `SLED PUSH` was drawn
in near-black on it and disappeared: 36 luminance between the ink and its
background, against 231 on the row above.

```
../.venv/bin/python ../../engine/caption_glass.py <topic>_clean.png \
    <topic>_labelled.png \
    -l base_<topic>_layout.json -o <topic>_glass.png
```

**It writes a third file, and it now refuses to do anything else.** The pair it
is given has to differ by ink alone, so writing over either one destroys the
input the next run needs; the engine checks for that and stops (this file asked
for `-o <topic>_labelled.png` until 9 September 2026, which the tool no longer
accepts). `<topic>_glass.png` is then the poster `render.sh` is handed - not the
labelled one.

It runs **after** `add_labels.py`, not before, because the width of a pane is the
width of its words and only the tool that drew them knows that. Given the poster
before and after labelling it solves `labelled = a*ink + (1-a)*clean` for the
ink's coverage, which gives both the box to fit and a way to lay the words back
down without the halo that copying drawn pixels would carry.

Each pane is the lightest one that still separates its ink by 95 luminance, so
the four captions that already read barely change and the one over the sled is
lifted: 36 to 95 there, 112 to 139 and 144 to 166 on the two middling rows, 231
and 198 left alone. One fixed strength cannot do that - at the setting that
rescues the sled the other four are heavier than they need to be, and at the
setting that suits them the sled stays unreadable.

Circle mode does not want this. There the base draws the caption bars itself and
the ink is guaranteed against them; a pane on top would be a second bar.

It lives in the engine now rather than here (58d7e5c). The fault is not this
variant's: `add_labels.py` takes its ink from the layout's light/dark flag, which
is a guarantee on a flat row and a guess on a photograph, so every variant with a
scene mode inherits it. Biohacks measured the same signature on their own posters
- thinnest ink-to-background gap 86 against 153-243 elsewhere, four of the five
thinnest on light rows, which is our sled at 36 in milder form - and asked for the
tool rather than copying it. The tuning is still ours: `--min-alpha 0.42` and
`--target 95` were measured on five Exercise bands, and if another folder's
measurement argues for different numbers that is one conversation, not two sets
of constants.

**4. Animate, sound it, ship it.** One command, because the animator and the
sound have to agree on when the badges land — and that instant is also when the
muscle lights:

```
./render.sh <topic> <topic>_labelled.png 'auto:LIFT,LIFT,LIFT,LIFT,LIFT'
```

`auto:` reads `exercises.json`. To choose the muscles by hand, pass them instead —
`;` between rows, `,` inside one, `:p`/`:s`/`:t` to override a tier:
`'Chest:p,Triceps:s;Lats:p,Biceps:s;...'`. Anything after the third argument goes
straight to `flowanim.py`.

Out comes `../OUTPUT/<DD.MM>/<topic>_muscles.mp4` with the bed and the hits on it.
`<topic>_silent.mp4` is the scrap pass; `<topic>_cues.txt` is what the
sound was cut against.

Watch the render's output for a line like

    r3: Glutes does not show from the front - its badge lands over an unlit body

That is a dead beat: the badge lands and the hit sounds over a body where nothing
happens. Either reorder the row so the view flips, or swap the muscle.

The three steps it runs, if one is ever needed alone. Run them from `work/`, and
keep them in step with `render.sh` - a stale copy here is how a fixed fault comes
back, which is exactly what the two-input mix below used to do to the finale:

```
../.venv/bin/python ../../engine/flowanim.py <topic>_labelled.png \
    --width 1080 --seconds 8 \
    --overlay body_overlay,muscle_overlay \
    --base base_<topic>_clean.png --anchored ../INPUT/base_<topic>.png \
    --layout base_<topic>_layout.json \
    --drops 0 --reach 0 --anchor-tol 6 \
    --muscles 'auto:LIFT,...' --muscle-times 1,2,3.2,4.4,5.6 \
    --muscle-cues <topic>_cues.txt \
    --finale auto --surge 0.30 --finale-cue <topic>_finale.txt \
    -o <topic>_silent.mp4

../.venv/bin/python muscle_audio.py --cues-file <topic>_cues.txt \
    --finale-cue <topic>_finale.txt --finale-out <topic>_chord.wav \
    --seconds 8 -o <topic>_hits.wav

# the duck window is read from the finale's own instant: FIN-0.28 to FIN+1.12
FIN=$(cat <topic>_finale.txt)
DUCK="volume='1-0.28*clip(min((t-$(awk -v t=$FIN 'BEGIN{print t-0.28}'))/0.20,\
($(awk -v t=$FIN 'BEGIN{print t+1.12}')-t)/0.35),0,1)':eval=frame"

ffmpeg -y -i <topic>_silent.mp4 -i ../../engine/sfx/lift_bed_8s.m4a \
  -i <topic>_hits.wav -i <topic>_chord.wav \
  -filter_complex "[1:a]volume=1.0,${DUCK}[w];[2:a]volume=0.62[p];\
[3:a]volume=1.0[f];\
[w][p][f]amix=inputs=3:duration=first:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[a]" \
  -map 0:v -map "[a]" -shortest -c:v copy -c:a aac -b:a 192k -movflags +faststart \
  ../OUTPUT/<DD.MM>/<topic>_muscles.mp4
```

The chord is a fourth input at unity and not a fourth thing in the hits file:
one track takes one gain, and 0.62 is the badges' number, not its.

Without `--muscles` the animator renders the liquid and nothing else.

`<DD.MM>` is the day's folder — `07.09`, made if it is not there yet. **Only the
finished cut goes there.** The silent pass stays in `work/`: the clip is never
published without sound, so a mute mp4 in `OUTPUT/` is only something to mistake
for the finished one later.

**5. Audit before delivering.**

```
../.venv/bin/python audit.py <topic>_silent.mp4 --cues <topic>_cues.txt
```

Single digits is clean. On the reference cut it reports 128 px, and that is x264
ringing on the boundary between a near-black row and a white one, not motion —
see `README.md`. If type or the athlete moves, something is wrong; say so rather
than shipping it.

**It finds its own timings, and it says which it read.** Given
`<topic>_silent.mp4` it reads `<topic>_cues.txt` and `<topic>_finale.txt` from
beside the video; `--cues` and `--finale` still override, for re-checking an
older clip by hand. If it finds neither it says so in place of the filenames,
because a clean over a window containing every badge is not a clean.

**The finale used to be inside the last window, and that is fixed.** It is not a
badge cue - it has its own file so the sound does not strike it as a sixth hit -
so the windows knew nothing about it and the stretch after the last badge ran to
the end of the clip with the loudest moving thing in the video inside it. Every
Exercise audit on 9 September 2026 reported 46000 to 49000 px and `look at it`
for clips that were correct, with the offending sample at t=6.91, dead in the
surge. The same cut now:

    before   4 windows, 12 pairs   46680 px   look at it
    after    5 windows, 14 pairs       0 px   clean

The alarm was the visible half. The hazard was the other one: three samples
across a window is a thin search, and had the rhythm placed them either side of
the surge the same window would have printed `clean` while containing it. So the
count of frame pairs is printed beside the verdict - `clean` over fourteen pairs
and `clean` over three are not the same sentence.

The fifth window is new and it is the one worth having: 7.28-7.55, after the
finale settles, sampled at any length down to 0.15s because the last frame is the
one a feed freezes on. It reads 0 px, which is the first direct confirmation of
the settle this file has been claiming since the finale landed.

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

- **The finale has to be paid for in the rhythm, not in seconds.** At
  `1,2,4,5.5,7` the last badge lands at 7.18 of an 8s clip and there is nowhere
  to put an arrival. `render.sh` now runs `1,2,3.2,4.4,5.6`: last badge 5.78,
  finale 6.38, and the clip is still and settled from 7.25s to the last frame -
  measured at 540 wide, 178 px in 3 clusters on the last moving frame and 0 px,
  0 clusters after it. A longer clip is not the alternative: the surface travels
  a whole number of ribbon lengths, so 8s is 92px/s and 9s is 82, with nothing
  in between.
- **The finale is not the landing flash again.** The landing lifts a muscle
  towards white, which is right for one region arriving on a dark body. At the
  finale every region lights at once, and lifting them all towards white is
  exactly the merge this file already warns about - glutes beside hamstrings as
  one red mass. So `body_overlay.finale` multiplies instead: every pixel keeps
  its ratio to the darker rim around it. Measured over the five bodies, 99% of
  the rim pixels survive the peak (9413 against 9465 settled).
- **A badge does not pop twice.** `muscle_overlay.finale` slides a specular band
  across each ball as the surge passes its column. A second pop reads as a
  second landing, and a second landing wants a second hit under it - which the
  sound cannot give, because the finale is one chord, not five more strikes.
- **The finale is not a badge cue.** It goes in `<topic>_finale.txt`, its own
  file, and `muscle_audio.py` reads it through `--finale-cue`. Written into
  `<topic>_cues.txt` it would be sounded as a sixth badge on a frame where
  nothing lands.
- **The finale's level is the engine's, not this folder's.** It was tempting to
  set it here and it was wrong twice over. The sound itself changed under us on
  8 September 2026 - `impact.finale` is now an FM bell, chosen by the user out of
  nine candidates in a finished clip, and its own default gain is 0.316 - so the
  1.00 this file used to pass, measured against the old chord, became +10 dB over
  the level the sound was picked at: on the hits track the chord alone reached
  0.0 dBFS before the mix even started. And the sound is shared with the other
  variants, so a number set in `muscle_audio.py` is a second loudness for one
  sound, which is the drift `engine/impact.py` exists to prevent. `--finale-gain`
  is therefore an override that is not passed: unset, the engine's own gain
  stands.

  Measured here anyway, because an Exercise row is three hits and Micro's is one,
  and the difference is real. Hits track alone, cardio: the chord is -22.3 dB
  mean / -10.0 peak against row 5's -18.4 / -2.9, so it answers the row from
  3.9 dB under it (4.6 under row 4). In the finished mix, where the bed and the
  row's own tail are in the window too, that reads as 2.9 dB under row 5 - and
  Micro measures 2.4 dB on `energy` and 2.5 dB on `superfoods12`. Three variants
  within half a decibel, on rows of one hit and rows of three, is the argument
  for one value in the engine rather than a gain per folder: level with the row
  costs +3.3 dB here (gain 0.46) and about the same there (0.398). Affordable
  either way - the mixed file peaks at -3.11 dB at 0.316 and at 0.46 alike,
  1.4 dB clear of the limiter's -1.72 ceiling, so nothing is limited. Headroom
  was never what was wrong with 1.00; being a second loudness for a shared sound
  was. **That number is reported to the root, not applied here.**

  The user settled it at 0.398 in the engine (d1fba5d, 8 September 2026), +2.0 dB
  over the audition and the value that is level with a Micro row, on the grounds
  that a cadence sitting slightly under is a smaller fault than one sitting over.
  Measured here afterwards on the same cardio cut: the chord is 1.9 dB under
  row 5 on the hits track (2.6 under row 4) and 2.8 dB under in the finished mix,
  and the mix peak is still -3.11 dB, set by a badge rather than by the chord.
  So an Exercise finale does arrive under the row it answers, by about a third of
  what it did. If that ever reads as under rather than measures as it, the seam is
  the same one: report the number and the cut, do not put a gain back in here.

- **One track gets one gain, so the finale needs its own.** `muscle_audio.py`
  summed the chord into `<topic>_hits.wav` and `render.sh` then multiplied that
  whole track by `HIT_GAIN`, 0.62 - a number measured for badge hits. So the
  0.398 the engine returns arrived at 0.247, **4.15 dB under the level the user
  picked it at**, and every measurement above was taken through that loss without
  knowing it. It is also why the finished-mix window looked so unresponsive: the
  chord in it was 4 dB quieter than intended before the window even diluted it.
  No engine number could have fixed this - it was the routing, not the level, and
  a local gain here would have hidden it and left two variants at two chord
  levels for the third time.

  The chord now comes out in `<topic>_chord.wav` (`--finale-out`) and the mix
  takes it as a fourth input at `FINALE_GAIN=1.0`. Measured on the cardio cut,
  before -> after:

      sfx track at mix weights   1.9 dB UNDER row 5  ->  2.2 dB OVER it
                                 2.6 under row 4     ->  1.6 over
      finished mix               2.8 under row 5     ->  1.7 under
      file peak                  -3.11 dB either way, set by a badge, limiter idle
      integrated                 -18.1 -> -17.9 LUFS, true peak -2.7 both

  Read by peak rather than by mean the chord is still about 1 dB under the
  badges: it sustains where they spike, and the two meters disagree by design.
  Whether 2 dB over by mean is right for a three-hit row is a question for a
  finished cut nobody has heard yet - the numbers go to the root, the gain does
  not come back in here.

- **A dark wave on a light row can come back washed out, and `check_base.py`
  will pass it.** On KETTLEBELL, 8 September 2026, the generator repainted both
  light rows: row 2's wave went from (28,200,89) to (192,239,122) and row 4's
  from (14,160,68) to (218,240,168), the left discs with them. Measured as how
  far the wave stands off its own row stripe, row 2 lost 58% of its contrast and
  row 4 lost 81% - 138.6 down to 27.0. The geometry never moved, so the wave
  check says *safe to animate*, and it is right: that check measures whether the
  mask still fits. Restyling is a different fault and nothing measures it.

  It animates. Averaged over eight windows the pale rows flow as much as any
  other - row 2 at 10356 moving px against WEEK ONE's 11924 - so this is a
  design fault rather than a broken clip, and the user shipped it. What the
  poster cannot do is be repaired: the wave right of x 450 is clear of the
  athlete and could be restored from the base exactly, but the same repaint hit
  the left disc, and the athlete stands *inside* that disc. A restored wave
  beside a pale disc is a row contradicting itself, so the choice is the poster
  as it came or another generation.

  **Naming the rows in the prompt fixed it, first try.** One paragraph - the
  waves on rows 2 and 4 are dark green on a light background, that contrast is
  deliberate, do not lighten them or tint them towards the background, do not
  harmonise the image, and the filled circle keeps its colour too - and the
  regeneration kept 100, 99, 100, 99 and 101% of each wave's contrast against
  its row. The generic "do not restyle them" in the opening paragraph had not
  been enough on its own; the rows had to be named. Suspected trigger, still one
  data point: deep green against a near-white row. MACHINES ONLY carried #7422FF
  on a light row untouched, so it is not simply dark-on-light.

  What the pale version looked like is worth keeping, because it is how this
  fault announces itself: not a uniformly pale row but **two greens in one row**,
  a deep moving band with a hard edge against a pale static one. The animator
  reads the liquid's colour from the base and refuses to paint over what it
  scores as artwork, so a repainted wave puts those two rules against each
  other - the base-coloured liquid it does paint slides through the generator's
  paint, ending always at the right circle's edge and wandering at the other end.
  On the pale row 2 only 6.9% of the repainted pixels ever moved, against 8.5% on
  an untouched row at the same instant.

- **An athlete drawn far larger than the disc gets his legs cut off by the
  caption bar.** `clean_poster.py` restores the bar because `add_labels.py`
  picks its ink from whether the ROW is light or dark, which is wrong over a
  photograph - that part is right and stays. But on KETTLEBELL row 4 the
  generator drew the athlete at roughly twice the disc, legs running well past
  the bar, and taking the bar back cut her shins and left both shoes floating
  under it: 3533 px restored, and the two orphans read as debris rather than as
  something standing behind the bar. It has been harmless until now because what
  crossed the bar was a foot or a skipping rope, small enough to read as
  occlusion.

  `--bars 0` leaves the generator's bar and avoids the cut, at the price the bar
  restoration was built to avoid. The cheap fix is upstream and it works: "the
  athlete is sized to the circle and cropped by it: he does not stand through it,
  and no part of him - no foot, no shoe, no hand, no kettlebell - appears below
  the circle or beyond it on any side" took the overhang on that row from 3533 px
  to 279. It is not free either. The athletes come back visibly smaller in their
  discs, because the sentence that keeps the feet out also keeps the whole figure
  in, so use it when a poster has already overhung rather than by default.

- **Every geometric check passes another variant's poster.** `grab.py` takes the
  newest 1536×2752 file out of Downloads and cannot know who generated it. On
  8 September 2026 Biohacks grabbed an Exercise poster by accident, and nothing
  caught it: all four variants are built on the same base, so the waves are in
  the same places and `check_base.py` reported four rows ok and one repainted.
  Both tools were right about what they measure and both were looking at the
  wrong picture.

  What does not cross variants is the title, because `recolor_base.py` draws it
  into the base and every prompt forbids touching it. Measured over three topics
  here: against its own base a poster reads 1.9-2.6 mean difference in the title
  band, against another topic's 72-88. `check_base.py` carries the test now
  (28fc3be, `--title-tol 8`) and runs before anything of ours, and the accident
  that started it refuses at 85.4. `clean_poster.py` keeps a second copy of it,
  at the engine's tolerance rather than one of its own.

  Two things about it are worth more than the check. **Thirty times apart on
  three posters was not the general case**: over 37 posters and 1332 mismatched
  pairs the root measured own-base up to 3.2 and the closest mismatch at 2.41, so
  no threshold separates every pair and 8 is near the top of what is safe. Three
  readings were enough to be right about the cause and not enough to be right
  about the number, which is the third time a variant has managed exactly that.

  And **it finds a foreign base, not a foreign topic.** Two topics sharing a
  title read alike - Micro measures 5.4 between SUPERFOODS 7 and SUPERFOODS 12 -
  so the older hazard, last topic's poster cleaned against this topic's base, is
  not closed by it. Every Exercise title so far is unique, which is luck and not
  protection: reuse one and this check goes quiet.

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
- **The ragged edge along the wave is not a scene-mode fault; a flat row hides
  it, and most of the metric that found it was measuring the anchors.** Reported
  on 9 September 2026 as a deformed coloured fringe around the liquid, seen here
  and in Biohacks and not in Micro. Two rounds of measurement, and the second
  corrected the first.

  **What holds.** A flat row hides it. Measured on `desk` against `legs` - a
  photograph and a flat row from the same engine on the same day, five frames
  before the first badge lands - the flat row froze *more* of its rim and showed
  nothing at all. A frozen rim pixel holds a blend of the wave's colour and
  whatever was behind it: against a flat row that blend lies between the row
  colour and the wave colour and cannot be seen, against a photograph it is a
  blend with an arbitrary pixel. **A variant that shows nothing is not a
  control.**

  **What did not hold: the number.** The root found the tips. Both of a ribbon's
  ends are pinned within ~1px of their circle centre by the geometry contract -
  the surface scrolls through them and the ends do not move, and an end that
  moved would be the bug. They are the outer eighths of the ribbon's span, a
  quarter of the rim, and they are **100.0% frozen by construction**, in both
  modes:

      rim, inside definition    whole    tips     travel zone
      desk   (scene)            32.5%   100.0%      10.3%
      legs   (circle)           31.2%   100.0%       8.6%

  So any whole-rim figure has a floor around 25% before a pixel misbehaves.
  **Split the rim at the outer eighths or the number means nothing.**

  The tip floor does *not* explain the circle-vs-scene gap, and this file said it
  did for about an hour. The root proposed that reconciliation and I copied it in
  without checking whether it could apply: the 16.8% and 22.9% were measured at
  x 360-800, which had already excluded both tips, so tip geometry could not have
  been the explanation for anything about them. The root has since retracted it
  (c705fbc). Two numbers that disagree are not reconciled by inventing a
  difference between them - the question is how each was measured, and here the
  answer was a different band and a different x range.

  Two rims exist and they are not the same population. Mask-minus-erosion is the
  4px band *inside* the silhouette; dilation-minus-mask is the 4px band *outside*
  it, which is where the animator's deliberate 9x9 overshoot peters out and is
  structurally static in its own right - it reads 25.1% and 25.4% in the travel
  zone against the inside band's 10.3% and 8.6%. Quote the inside one.

  **Jpeg is part of it and not the whole of it.** `flowanim.py` run on
  `base_legs_clean.png` gives a clip at our exact geometry from an authored PNG
  with no jpeg at any point in its history - not a re-save, the file
  `recolor_base.py` wrote - and no generated content at all:

      PNG base, no jpeg ever      travel   6.1%
      legs, from a jpeg poster    travel   8.6%
      desk, from a jpeg poster    travel  10.3%

  So jpeg is worth 2.5 to 4.2 points here, a third to two fifths of the residue,
  and 6.1% survives without it. The root ran the same control at Longevity
  geometry and got **3.6%** from their own authored PNG - two variants, no jpeg
  in either, same rim, same split, same window, and the floor differs by nearly a
  factor of two. Whether that is the topic or the ribbon is open and is written
  down as open at the root; do not resolve it by assumption from in here.

  One number is stranger and is worth a look if the fringe ever matters visually:
  on the OUTSIDE band, in the travel zone, ours reads 25.1% and 25.4% against
  Longevity's 5.9%. That is the largest gap anywhere in this investigation and it
  is on the band this folder originally quoted. It is not simply edge ringing either: across the
  five rows of one clip, wave-to-row contrast 114-151 against frozen 6.4-12.7%,
  and the second-highest-contrast row is the least frozen of the five.

  Two things it is not: `refine_art`, which scene mode disables outright with
  `--lifter-r 0` and which returns unchanged on its first line; and the hard
  `inside` boolean, because the render's 10-90% edge transition measures 2.63px
  against the poster's 1.06px - already wider, so anti-aliasing widens what is
  not narrow. **The remaining fault is in the engine and is not ours**; the
  numbers went to the root on 9 September and `flowanim.py` was not touched from
  here.

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
