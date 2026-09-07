# Micro/work — the same clip, with the micronutrients on it

A copy of the 7 September morning checkpoint with one thing added: the vitamins,
minerals and fibre a food actually carries pop onto its row while the liquid
runs. Everything about the liquid, the mask, the bases and the poster prompt is
the checkpoint's and is unchanged, so a command that rendered a clip there
renders the same clip here — `--micro` is what turns the badges on, and without
it nothing is different.

**Everything of this variant's own lives here, in `work/`.** The poster arrives
in `../INPUT/` and the finished clip leaves from `../OUTPUT/`. The badges are
in `icons/`, cut once from `icon-sources/`. The animator, the wave assets and
the sound are the engine's, two folders up, and are never copied in.

## The loop

One command does the three steps, because they have to agree on when the badges
land and typing the times twice is how a pop ends up half a frame off the badge
it belongs to:

```
./render.sh liver liver_labelled.png \
    'auto:LEAFY GREENS,BEETROOT,TURMERIC,BROCCOLI,COFFEE'
```

`auto:` looks each food up in `nutrients.json` and takes the two or three things
it is genuinely known for. To choose by hand, give the badges instead — `;`
between rows, `,` inside one:

```
./render.sh liver liver_labelled.png 'K,Folate,Iron;Nitrates,Folate;...'
```

Everything after the third argument goes to `flowanim.py` untouched, so
`--micro-d`, `--micro-times`, `--seconds` and the rest still work. Output lands
in `../OUTPUT/<DD.MM>/<topic>_micro.mp4`, sound already on it.

Steps 1 to 3b of `flow.md` are unchanged: palette, prompt, `check_base.py`,
`add_labels.py`. `render.sh` replaces steps 4 and 4b.

## The pieces

| file | what it is |
| --- | --- |
| `micro_icons.py` | builds the badges: recovers the sphere, sets the label, recolours |
| `micro_overlay.py` | where each badge goes and how it enters; imported by `flowanim.py` |
| `micro_audio.py` | the pop, synthesised, one note per row |
| `nutrients.json` | food → the micronutrients it is known for |
| `render.sh` | animate, sound, mux |
| `audit.py` | did anything move that should not? |
| `make_prompt.py` | fills `ImageSwap.txt` for a topic, so a prompt is never a stale copy |
| `icons/` | 38 badges, 512px, plus `_ball_orange.png`, the blank sphere |

## Staying level with the base generator

This folder is a copy of a checkpoint, and the base generator kept moving under
it: in one morning the prompt gained clear glass bowls and 3D organs,
`add_labels.py` started sizing all ten captions together, and `flowanim.py` grew
`--halo`. Nothing said so, and a poster was generated from a three-revision-old
prompt before anyone noticed.

`../../engine-status.sh` reports whether this folder is still calling the
engine rather than carrying a copy of it. The drift it used to watch for is
gone: there is one animator now, and `micro_overlay.py` plugs into it through
`--overlay` rather than being patched into a copy.

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
.venv/bin/python micro_icons.py --all                 # the catalogue
.venv/bin/python micro_icons.py --one 'Choline:o'     # something not in it
.venv/bin/python micro_icons.py --sheet               # look at the lot
```

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

## The sound

Synthesised, not sampled. A hit off a library arrives with a room on it, and
five of them in eight seconds sound like five different rooms.

**The synthesis is the engine's**, `engine/impact.py`, and it is Exercise's hit:

    click     1.2 ms of noise, differenced       the contact
    body      sine falling 1.0 -> 0.42 of f0     the landing
    sub       an octave under it, 90 ms          the weight behind it
    air       band-passed noise, 35 ms           the spray after it

`micro_audio.py` keeps what is Micro's own - reading the cues `flowanim.py`
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

`render.sh` mixes it over the water bed at fixed gains with a limiter rather
than `loudnorm`, which pumps the water down under every pop. `POP_GAIN` is 0.62,
Exercise's, so the two variants share the mix as well as the synthesis; measured
on the same picture the finished cut lands on **-18.0 LUFS, -1.3 dBTP** at either
0.60 or 0.62, so this is about the two clips being one sound and not about level.
Do not push it much further: the limiter sits at 0.82 and the hits are
transients, so a loud one pumps the water underneath it.

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

```
.venv/bin/python audit.py work/liver_silent.mp4 --cues work/liver_cues.txt
```

## Still open

- the thyroid base predates "the wave takes the colour of its food" and breaks
  it: brazil nuts run vermilion, eggs violet, yoghurt pink. Its clip is in
  `OUTPUT/07.09/` and stays there - shipped is shipped - but the base wants
  rebuilding before that topic is shot again
- the label-position check in `check_base.py` is unreliable and only prints a
  note; look at the poster before animating
- the generator draws a soft shadow around the waves although the prompt forbids
  it, and it sits still while the silhouette ripples
- `nutrients.json` holds about 130 foods. A food that is not in it stops the
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
