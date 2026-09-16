# Organs/work — food for vital organs, with the micronutrients on it

Five foods, the organ each one feeds, and the vitamins, minerals and fibre a food
actually carries popping onto its row while the liquid runs. One scene, and it
ends with the finale: the surge runs down the poster, every organ lights again,
the chord lands.

This folder was `Micro/work` until 16 September 2026. The series split in two and
the two-act cut went to `../../Vitamins/`, taking `render2.sh`, `micro_card.py`
and `micro_result.py` with it; the badge machinery went to the engine, because
both halves read it. What is left here is this category's own.

**Everything of this variant's own lives here, in `work/`.** The poster arrives
in `../INPUT/` and the finished clip leaves for `../../OUTPUT/ORGANS/`. The
animator, the wave assets, the badge set and the sound are the engine's, two
folders up, and are never copied in.

## The loop

One command does the three steps, because they have to agree on when the badges
land and typing the times twice is how a pop ends up half a frame off the badge
it belongs to:

```
./render.sh liver liver_labelled.png \
    'auto:LEAFY GREENS,BEETROOT,TURMERIC,BROCCOLI,COFFEE'
```

`auto:` looks each food up in `../../engine/micro/nutrients.json` and takes the two or three things
it is genuinely known for. To choose by hand, give the badges instead — `;`
between rows, `,` inside one:

```
./render.sh liver liver_labelled.png 'K,Folate,Iron;Nitrates,Folate;...'
```

Everything after the third argument goes to `flowanim.py` untouched, so
`--micro-d`, `--micro-times`, `--seconds` and the rest still work. Output lands
in `../../OUTPUT/ORGANS/<topic>_organs.mp4`, sound already on it - flat and
dateless, per ../../CLAUDE.md rule 12. `../../OUTPUT/DONE/ORGANS/` is what has
gone out and nothing here writes to it.

Steps 1 to 3b of `flow.md` are unchanged: palette, prompt, `check_base.py`,
`add_labels.py`. `render.sh` replaces steps 4 and 4b.

## The pieces

Here:

| file | what it is |
| --- | --- |
| `render.sh` | animate, sound, mux |
| `audit.py` | did anything move that should not? Reads its own cues and finale off disk |
| `make_prompt.py` | fills `ImageSwap.txt` for a topic, so a prompt is never a stale copy |
| `meals.json` | what a topic is: title, captions, badge list, the five foods and their servings |
| `SERIES.md` | every food and organ already used, and all 23 palettes - read before picking a topic |

In the engine since 16 September, shared with `../../Vitamins/` and called by
path, never copied in (../../CLAUDE.md rule 1):

| file | what it is |
| --- | --- |
| `../../engine/micro_icons.py` | builds the badges: recovers the sphere, sets the label, recolours |
| `../../engine/micro_overlay.py` | where each badge goes and how it enters; imported by `flowanim.py` |
| `../../engine/micro_audio.py` | the pop, synthesised, one note per row |
| `../../engine/micro/nutrients.json` | food → the micronutrients it is known for |
| `../../engine/micro/icons/` | 42 badges, 512px, plus `_ball_orange.png`, the blank sphere |
| `../../engine/micro/icon-sources/` | the nine generated vitamin balls the sphere was recovered from |

## Staying level with the base generator

This folder is a copy of a checkpoint, and the base generator kept moving under
it: in one morning the prompt gained clear glass bowls and 3D organs,
`add_labels.py` started sizing all ten captions together, and `flowanim.py` grew
`--halo`. Nothing said so, and a poster was generated from a three-revision-old
prompt before anyone noticed.

`../../engine-status.sh` reports whether this folder is still calling the
engine rather than carrying a copy of it. The drift it used to watch for is
gone: there is one animator now, and `micro_overlay.py` plugs into it through
`--overlay` rather than being patched into a copy. Since the split it watches the
badge machinery too - `micro_overlay.py`, `micro_audio.py` and `micro_icons.py`
are on its list, because two categories reading one badge set is exactly the
arrangement that drifted into three generations in a morning the last time it was
three copies.

    same           the geometry and the shared tools. A difference here is drift
    MERGE          flowanim.py and the four docs - ours plus theirs

`make_prompt.py` removes the commonest way this bites. A prompt written into a
file is a copy the moment the template moves, so prompts are not written any
more, they are filled: the body comes out of `ImageSwap.txt` as it stands and
only the five rows are substituted.

## The badges

Nine vitamin balls came back from the generator one at a time, so no two agreed
on how big a letter is, and vitamin C came back as a shield with the
checkerboard still in its fringe. A row of badges that disagree reads as clip
art, so the sphere is authored once and every badge is that sphere with a label.

The sphere is not drawn from scratch — it is **recovered from the eight real
ones**, which is why it still has their gloss, their rim and their four specular
dots. Median of the eight, then a grey closing whose footprint is wider than a
letter stroke to find what the letters cover, then a coarse-to-fine Laplace fill
to put the ball back underneath them. Plain Jacobi at full resolution does not
converge on a 400px hole and leaves a ghost of the letter; the pyramid does.

The colours are **the app's own**, sampled off its Micronutrients screen:

    vitamins  #3E85F6       minerals  #69C66C       fibre and the rest  #EF9749

The sphere's luminance is gradient-mapped onto each. That is the only way to
land on an exact colour — rotating the hue of a bright orange ball towards green
gives a lime, not #69C66C. Luminance and not value, because the template's red
channel is pinned near 255 from rim to core, so V is nearly flat across it and a
map on V produces a ball with no shading at all.

The letters are **white**, with a soft shadow of themselves underneath. The
fitted law the original balls used was almost pure hue contrast — 46° of
yellow-orange against 26° of red-orange — and hue contrast is the first thing a
badge loses at the size it occupies in a vertical video. The shadow is what lets
white work everywhere: the specular is white too, and a letter crossing it would
otherwise vanish into it.

`--rebuild` re-derives the sphere; nothing else needs it.

```
../.venv/bin/python ../../engine/micro_icons.py --all                 # the catalogue
../.venv/bin/python ../../engine/micro_icons.py --one 'Choline:o'     # something not in it
../.venv/bin/python ../../engine/micro_icons.py --sheet               # look at the lot
```

## What a render spends its time on

`paint()` runs 192 times and draws every badge that is alive, and until
9 September it asked LANCZOS for the same picture on every one of them: the
badge's pixels never change and its size is an integer, so all but the handful of
frames during the pop were the same resize computed again. `_scaled()` keeps
them, keyed by badge and side - one entry for the whole settled stretch, about a
dozen for the pop.

Measured on two topics at 1080, whole clip: **63 s -> 46 s** on superfoods18 and
**56 s -> 50 s** on superfoods7, and in both cases the rawvideo hash of all 192
frames is identical before and after. That is the only reason it was allowed to
ship - a cache that changed a pixel would be a different clip, however fast.

## How they enter

Back-eased pop from zero, through about 15% over-scale, down onto 1.0 in 0.42 s,
with a thin ring thrown off at the landing. A badge that fades in is furniture; a
badge that overshoots is an event.

They sit **on the wave's own centre line**, read off the geometry `flowanim.py` is
about to animate, so a row of them rides the S instead of cutting across it. The
line is clamped to the row, because the wave is free to ripple and the badge is
not free to climb into the row above or sit on the caption.

Defaults: 210px across at 1536 wide, 0.09 s between the badges of a row, landing
at **1, 2, 4, 5.5 and 7 s**, and **staying up to the end**. `--micro-fade` can
fade them out, but the default is 0: a badge fading out passes through a stretch
where it is a soft coloured smudge with a ghost of a word in it, and that is
exactly the frame a feed freezes on.

## The finale

The clip counts: a badge lands, a note climbs a degree, and after five rows the
ear is waiting for something. From 8 September it arrives. The engine decides
**when** - `--finale auto` takes the last cue and adds 0.60s - and everything
that lights up is this folder's.

**The organ answers its own row first.** This is the whole of why the finale
works here rather than reading as a fault. Exercise's body reacts to every badge
from the first second, so its finale summarises something the viewer has been
taught; Micro's organs sat still for eight seconds, and a first movement in the
last second is a glitch, not a climax. So each organ lifts on its own row's cue,
0.07s up and 0.38s down onto a residue it keeps - and the finale is that same
gesture with the volume up, on ground the viewer already knows.

**The organ is found, not assumed.** It is poster pixels: the shape comes off
the poster against the clean base at 45 levels, opened 5x5 so jpeg speckle is
not an edge and closed 13x13 so a dark seam inside an organ does not split it.
Measured over two posters and ten circles it is always one dominant blob at
99-100% of what is found, but its coverage of the disc runs **41% to 62%** on
one poster alone - so a fixed radius would light a ring of bare row colour on one
row and clip the organ on the next. And the disc is not the organ: 5.0% of the
wave lies inside the guide circles where the animator never paints, and lighting
it would put a bright motionless crescent beside moving liquid, which is the
speckles-that-stand-still failure `flow.md` already records. The difference test
excludes it for free - where the organ does not cover, the poster still equals
the base.

**Light only, never geometry.** Nothing is scaled and nothing is moved: behind
the organ is the clean base rather than the poster, so a pixel of movement opens
a hole, and the poster is jpeg, so a resample rings on every edge. The lift is a
**screen** towards white, not a multiply - half these organs are bone or fat
sitting at 230, where a 1.45x multiply clips to flat white and takes the shape
with it. The bloom has 18px to work in: the right circle's outer edge is x=1408
of 1536 and the safe area ends at 1426, so the blur is sigma 6.

Everything is precomputed in `finale(pl, t0, ctx)` and only alpha varies per
frame - a gaussian per frame is minutes over 192 of them. The arrival times come
from `ctx["surge"]["at"](row, x)`: each badge answers as the crest passes its own
column and each organ as it reaches its circle, so the poster reads as one
gesture running diagonally down it rather than five unrelated flashes.

Measured on the INFLAMMATION cut at 1080:

    organ silhouettes        11 977 - 18 095 px, one cluster each, 41-62% of the disc
    a row's own answer        4 242 px in 1 cluster, bottom 705 against a bar at 727
    the finale, settled      19 950 px in 5 clusters - five organs, one each
    reach                    x 1397 of 1426, and clear of every caption bar
    still moving at 7.15s    0 px outside the wave, 0.85s before the last frame
    audit                    0 px, windows with the finale's own stretch cut out

## The sound

Synthesised, not sampled. A hit off a library arrives with a room on it, and
five of them in eight seconds sound like five different rooms.

**The synthesis is the engine's**, `engine/impact.py`, and it is Exercise's hit:

    click     1.2 ms of noise, differenced       the contact
    body      sine falling 1.0 -> 0.42 of f0     the landing
    sub       an octave under it, 90 ms          the weight behind it
    air       band-passed noise, 35 ms           the spray after it

`../../engine/micro_audio.py` keeps what is the series' own - reading the cues `flowanim.py`
wrote, grouping them back into rows, writing the wav - and calls
`impact.build(..., root=420.0)` for the sound itself. It is not copied in.

Until 7 September this folder had its own: no sub, a 760 Hz root, the pitch
falling by 2.4 in 45 ms rather than by three in 30. Measured, that was **-20.6
LUFS at -1.7 dBFS** against Exercise's **-19.4 at -0.5** - and level was the
smaller half of it. A badge landing on a row is the same event as a muscle
lighting up, and it read as a bubble in one variant and an impact in the other.
On the same cues the engine's build now measures -19.4 LUFS, -0.5 dBFS, to the
decimal what Exercise gets.

The note climbs: row 1 on the root, rows 2-5 up a major pentatonic, two
semitones per badge inside a row - `impact.SCALE` and `impact.STEP`, shared
rather than kept twice. Five identical thuds read as a machine; five rising ones
read as a list being counted off, and a viewer waits for the next one.

**The riser** is `impact.finale`, laid on the instant `flowanim.py` wrote, and it
is added to the same wav but never to the cues: `micro_audio.py` regroups cues
into rows by the gaps between them, so a finale appended to that list would open
a sixth row - `SCALE[5 % 5]` is the root again - and the cadence that answers the
count would be sounded as one more badge landing.

**Its level is the engine's, and this file passes none.** It used to force
`--finale-gain 0.80`, measured against the chord `impact.finale` made before
176c632. The finale is a synthesised FM bell now, chosen by the user out of nine
candidates - six of them real recordings - and its own default is 0.316, the
level it was auditioned at. Forcing 0.80 over that is **+8.1 dB**, measured on
the energy cut's own cues: in the finished mix the finale's half second goes
from -23.3 dB mean and -5.1 peak to -18.0 and -4.1. The mix peaks at -2.24 dB
either way, half a decibel under the 0.82 ceiling, so the objection is not
headroom - it is that 0.80 is not the level the sound was picked at, and that
Exercise had tuned the same shared sound to 1.00 while this file said 0.80,
which is the drift `engine/impact.py` exists to prevent. So nothing is passed;
`--finale-gain` stays as an override and forwards only when it is given.

**What the default measures here.** The first version of this paragraph
measured 0.316 and found the finale 2.4 dB under a badge row - the cadence that
answers the count arriving quieter than the badges it answers. Exercise found 2.9
dB under on its cardio cut and the root 2.5 dB on superfoods12: three cuts, one
direction. The user ruled, and `impact.finale`'s default is **0.398** since
d1fba5d, +2.00 dB on the same waveform. Re-measured here it was still 1.4 to 2.5
dB under, which turned out to be the second half of the same fault: the riser was
summed into `<topic>_pops.wav` and `render.sh` then put `volume=${POP_GAIN}` over
that whole file, so the chord arrived at 0.85 of what `impact.finale` returns -
**1.41 dB under the level it was auditioned at**, and 4.15 dB under in Exercise,
which uses 0.62. A badge gain was being applied to something that is not a badge.

It is its own input at unity now, and this is the same energy cut through the
same chain, before and after:

    riser summed into the pops    finale -22.2 dB, rows -19.7 to -20.8
    riser at unity, its own input finale -21.4 dB, rows -19.8 to -20.9
    against the quietest row      -1.9 dB before, **-0.5 dB after**
    clip peak                     -2.24 dB either way, 0.5 dB under the 0.82
                                  ceiling; the limiter still never engages

-0.5 against a row is what the level was picked for, and it is what the clip now
delivers. Nothing about the sound changed to get there - only what was multiplying
it on the way to the mix.

**Every figure above is a mean over half a second, and the meter has to be said
each time.** A chord sustains and a badge spikes, so the two disagree by
construction: on the same finished cut the finale is 0.5 to 1.7 dB under the rows
by mean and 2.7 under to 0.2 over by peak. Neither is the wrong answer; quoting
one without saying which is how a level argument runs all evening. Exercise's cut
splits the same way, 2.2 dB over by mean and 1.0 under by peak, and the rule is
now in `engine/README.md`.

The bed still steps back 2.9 dB under the finale and comes straight back,
written against the same instant so the two cannot drift:
`1-0.28*clip(min((t-(T-0.28))/0.20,((T+1.12)-t)/0.35),0,1)`.

`render.sh` mixes it over the water bed at fixed gains with a limiter rather
than `loudnorm`, which pumps the water down under every pop. `POP_GAIN` is
**0.85**, up from Exercise's 0.62: the badges are what the eye is following and
the hit was sitting under the water. The two variants still share the synthesis;
this one number is deliberately not shared.

Measured on the part 12 cut, at 0.85 against 0.62:

    pops, RMS at the cue        +1.8 dB
    pops over the water bed     +6.8 dB, against +5.4
    bed level between the hits   0.00 dB, unchanged - the limiter never engages
    mix peak                    0.15 dB UNDER the 0.82 ceiling
    finished cut                -17.6 LUFS, -1.2 dBTP (was -18.0, -1.3)

**1.00 is where it stops being free.** There the mix peaks 0.85 dB over the
ceiling, the limiter starts flattening the click, and the hit gets duller as it
gets louder - the transient is the whole sound. Anything above 0.85 wants
re-measuring rather than guessing: the test is the bed level in the 250-550 ms
after each hit, which is where pumping shows up first.

## Verified on this state

    both tips vs their circle centre   within 1.3px in all five rows   (checkpoint)
    wave inside the circle band        y 491-702 vs circle 432-707     (checkpoint)
    moving outside the waves           0 px, in every quiet window, both topics
    ball body vs the app colour        within 3-8%, all three families
    badges land at                     1.00 2.00 4.00 5.50 7.00 + 0.09 stagger
    finished cut                       -18.1 LUFS, -1.3 dBTP

`audit.py` picks the frames rather than filtering them: a badge is finished
0.52 s after it lands, so the gaps between one finishing and the next starting
are windows where the only thing allowed to move is the liquid, and the original
invariant holds there exactly as it did before the badges existed.

`--finale` is not optional since 8 September: it cuts the finale's own stretch
out of the windows. Without it the organs lighting at the end are counted as
things that moved, and the run reports tens of thousands of pixels on a clip
that is clean - 76 816 on the superfoods13 cut, against 4 with the flag.

Which is why neither flag is typed any more. Both files are on disk, `render.sh`
wrote them, and the topic is in the video's filename, so the bare command is the
strict one:

```
../.venv/bin/python audit.py ../../OUTPUT/ORGANS/cholesterol_organs.mp4
```

The flags still override, for an old clip whose files have moved. What changed on
9 September is which way the sloppy invocation fails. It does not cry wolf - it
goes quiet: with no spec at all the run collapses to **one window and three frame
pairs** against twelve, the three land at 0.05, 3.96 and 7.87 where nothing is
happening, and it prints `clean` in the same words as the strict run. So the
verdict now ends `clean, 12 frame pairs over 4 windows`, and a run with no cues
file says so in a line of its own before it starts.

## Still open

- the thyroid base predates "the wave takes the colour of its food" and breaks
  it: brazil nuts run vermilion, eggs violet, yoghurt pink. Its clip is in
  `OUTPUT/07.09/` and stays there - shipped is shipped - but the base wants
  rebuilding before that topic is shot again
- the label-position check in `check_base.py` is unreliable and only prints a
  note; look at the poster before animating
- the generator draws a soft shadow around the waves although the prompt forbids
  it, and it sits still while the silhouette ripples
- `../../engine/micro/nutrients.json` holds 137 foods. A food that is not in it stops the
  render with the name it could not find, rather than guessing
- a blue badge on a blue wave (lungs, row 2) separates on the shadow and the
  ball's own shading alone. It holds, but it is the thinnest case in the set

## What is known to break

Everything in `flow.md` still applies. Added by this folder:

- **Hue rotation cannot hit a given colour.** Rotating the bright orange
  template towards the app's green lands on a lime; rotating ball and letter
  together also keeps the hue *difference* and throws the contrast away, since
  46° against 26° reads on orange and 100° against 80° does not. Gradient-map the
  luminance onto the target, then draw the letter on top in white.
- **A badge that fades out is a smudge for half a second.** Alpha through 0.3 on
  a 1.3x shadow canvas is a soft coloured blob with a ghost of a word in it. They
  stay up; the loop cuts.
- **`alimiter` undoes its own limit.** `level` defaults to true and auto-levels
  the output back to 0 dB, so the first mix measured -0.1 dBTP with the limiter
  apparently on. `level=disabled`.
- **The old motion audit fires on every badge.** Choose the frames instead of
  filtering the pixels; see `audit.py`.
- **The wave's centre line is stored in the ribbon's own column range.**
  `geo["top"]` is indexed by `x - x0`, not by `x`. Indexed by `x` it raises on
  the first row and would silently place badges wrongly if the array were longer.
