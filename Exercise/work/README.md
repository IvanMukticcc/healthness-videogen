# Exercise/work — the same clip, about lifting

The food version ran a row as *bowl → liquid → organ*, with the micronutrients
popping onto the liquid. This one runs it as **lift → liquid → body**, with the
muscles popping onto the liquid and lighting up on the body as they land.

Everything about the liquid, the mask, the base geometry and the frozen wave
layer is the 7 September checkpoint's and is unchanged, so the animation is the
same animation. What changed is what stands at the two ends of every row and
what the badges say.

**This folder holds everything but the engine.** `INPUT/` for the base, `OUTPUT/`
for the clips, `work/` for the rest, with the badges in `work/icons/`. `.venv` is
a symlink one level up. The six shared tools are called from `../../engine/` and
never copied in (`../CLAUDE.md` rule 1); the badge sphere they were cut from is
committed as `work/icons/_ball.png`, so nothing outside is needed to render a
clip - `--rebuild` is not runnable from here and does not need to be.

## The one idea

**The body is drawn, not generated.** That is the whole difference, and it is
the same rule the wave already lives by: an image model cannot draw the same
thing twice, so it is never asked to.

Five rows whose bodies disagree about where the lats are is five different
bodies, and the comparison the clip exists to make — *this lift hits that, the
next one hits this* — does not survive it.

Having the body be ours buys the thing the badges alone cannot do: **the muscle
lights on the frame its badge lands, in the same colour.** A red ball arrives
saying CHEST and the chest goes red in the same frame. That link is why the
tier colours live in one file that both the badge builder and the body map read
(`muscles.py`); a badge whose red is not the body's red is two unrelated
animations playing at once.

## The loop

One command does the three steps, because they have to agree on when a badge
lands — that instant is also when the muscle lights and when the hit sounds:

```
./render.sh push push_labelled.png \
    'auto:BENCH PRESS,OVERHEAD PRESS,CHEST DIP,LATERAL RAISE,TRICEPS PUSHDOWN'
```

`auto:` looks each lift up in `exercises.json` and takes the muscles it actually
works, prime mover first. To choose by hand, give the muscles instead — `;`
between rows, `,` inside one, and `:p`, `:s` or `:t` to override a tier:

```
./render.sh push push_labelled.png 'Chest:p,Triceps:s,Front Delts:s;Lats:p,...'
```

Everything after the third argument goes to `flowanim.py` untouched, so
`--muscle-d`, `--muscle-times`, `--body-scale`, `--seconds` and the rest still
work. Output lands in `../OUTPUT/<DD.MM>/<topic>_muscles.mp4`, sound already on it.

Steps 1 to 3b of `flow.md` are unchanged: palette, prompt, `check_base.py`,
`add_labels.py`. `render.sh` replaces steps 4 and 4b.

## The pieces

| file | what it is |
| --- | --- |
| `muscles.py` | the vocabulary: label, tier, colour, which body regions |
| `bodymap.py` | the figure, front and back, and the muscles that light on it |
| `body_overlay.py` | where the body goes in the row and how a muscle ignites |
| `muscle_icons.py` | builds the badges: recovers the sphere, sets the label, recolours |
| `muscle_overlay.py` | where each badge goes and how it enters; imported by `flowanim.py` |
| `muscle_audio.py` | the hit, and the bed, both synthesised |
| `exercises.json` | 130 lifts → the muscles each one works |
| `render.sh` | animate, sound, mux |
| `audit.py` | did anything move that should not? |
| `icons/` | 84 badges, 512px, plus `_ball.png`, the blank sphere |
| `../../engine/sfx/lift_bed_8s.m4a` | the bed, synthesised, seamless, −18.4 LUFS |

## The vocabulary

28 muscles, three tiers. A row is a list of `(muscle, tier)` and everything
downstream reads that one pair: the badge file, the colour on the body, the note
of the hit.

    p   primary mover     #FF453A     the muscle the set is for
    s   synergist         #FF9F0A     helping, and it knows it the next morning
    t   stabiliser        #0A84FF     holding the shape while the other two work

`exercises.json` writes the tier explicitly (`"bench press": ["Chest:p",
"Triceps:s", "Front Delts:s"]`) because the same muscle is a different tier in a
different row — the chest is what a bench press is *for* and what a dip
*borrows*. A muscle named without a tier takes its usual one.

## The badges

The sphere is the food version's, and it is not drawn from scratch: it was
**recovered from the eight real vitamin balls**, which is why it still has their
gloss, their rim and their four specular dots. Median of the eight, a grey
closing wider than a letter stroke to find what the glyphs cover, then a
coarse-to-fine Laplace fill to put the ball back underneath them.

What changed is the colour and the catalogue. The three tier colours are
gradient-mapped onto the sphere's luminance — the only way to land on an exact
colour, since rotating a bright orange ball's hue towards red gives a scarlet
that is not `#FF453A`. The letters stay white with a soft shadow of themselves
underneath.

Every muscle exists at every tier, so the files are `CHEST_p.png`, `CHEST_s.png`,
`CHEST_t.png` — 28 × 3 = 84.

```
../.venv/bin/python muscle_icons.py --all                # the catalogue
../.venv/bin/python muscle_icons.py --one 'Soleus:s'     # something not in it
../.venv/bin/python muscle_icons.py --sheet              # look at the lot
```

## The body

Authored in normalised coordinates in `bodymap.py`: `x` 0 at the spine and ±0.29
at the hands, `y` 0 at the crown and 1 under the feet. Two views sharing one
silhouette — from a hundred pixels away a person's outline is the same either
way, and two silhouettes would have drifted apart the first time either was
touched.

A muscle with an entry in both views is drawn **differently in each**: what shows
of the triceps from the front is the outer edge of the upper arm, not the head of
the muscle. An empty entry means it does not show from that side at all; the
badge still lands and still sounds, and the planner says so on stdout rather than
letting a dead beat pass unnoticed.

Which way a row faces is decided by what it lights, not by hand, and by two
questions in this order.

**How much of the row can each side actually show?** A jump rope is Calves,
Quads, Forearms; all three read from the front and only the calves from behind,
so it is a front view whatever the calves would prefer. Deciding on direction
alone put a dead beat in **18 of the 130 lifts**; asking about coverage first
takes it to **6**, and those six are genuine — a lunge cannot show its hamstrings
while showing its quads.

**Then, only on a tie, which way does the row face?** The first muscle counts
triple, because it is the one the lift is *for* — so a pull-up is Lats, Biceps,
Forearms and shows the back, even though two of those three read from the front.

The figure is a **ghost**: white on the dark rows, near-black on the light ones,
at 0.15 alpha. Deliberately faint. Whatever is working has to be the loudest
thing in the circle, and at the size a row gives the body that is a contrast
question rather than a size one — the first cut drew it at 0.20 and the lit
muscle read as a detail on a statue.

```
../.venv/bin/python bodymap.py --sheet                          # every muscle, both views
../.venv/bin/python bodymap.py --view back --lit Lats:p,Biceps:s -o back.png
```

## How they enter

**The badge**: back-eased pop from zero, through about 15% over-scale, down onto
1.0 in 0.42 s, with a thin ring thrown off at the landing. A badge that fades in
is furniture; a badge that overshoots is an event.

They sit on the wave's own centre line, read off the geometry `flowanim.py` is
about to animate, clamped to the row.

**The muscle**: on the same cue, white-hot for 0.13 s and then down onto the tier
colour over 0.34 s, with a bloom that settles to a low steady glow. The flash is
squared, so most of the white is gone before the badge has finished its overshoot
and the two read as one event rather than two.

Defaults: 210px badges at 1536 wide, 0.09 s between the badges of a row, landing
at **1, 2, 4, 5.5 and 7 s**, and staying up to the end. The body is there from
the first frame — a figure that fades in with its first badge leaves the right
third of the poster empty for a second, and a feed's first frame is the whole
audition.

## The sound

Synthesised, not sampled. The food version's bed is running water, which is the
right sound for a clip about what you drink and the wrong one for a clip about
what you lift, so both the hits and the bed are built here.

    click     1.2 ms of noise, differenced        the plate touching down
    body      sine falling 1.0 → 0.35 of f0       the weight arriving
    sub       sine an octave below, 90 ms         what it weighs
    air       band-passed noise, 35 ms            the room, briefly

The sub is the difference between a bubble and a weight. The note climbs: row 1
on the root at 420 Hz, rows 2–5 up a major pentatonic, two semitones per badge
inside a row. Five identical thuds read as a machine; five rising ones read as a
set being counted off, and a viewer waits for the next one.

The bed is a low fifth with a slow swell, built in the frequency domain so it is
exactly periodic over the clip. Cut noise in the time domain instead and the
eighth second does not join the first, which on a feed that loops is a click
every eight seconds forever.

`render.sh` mixes at fixed gains with a limiter rather than `loudnorm`, which
pumps the bed down under every hit.

## Verified on this state

    both tips vs their circle centre     within 1.3px in all five rows   (checkpoint)
    wave inside the circle band          y 491-702 vs circle 432-707     (checkpoint)
    moving outside the waves             128 px worst, and it is codec ringing
    badges land at                       1.00 2.00 4.00 5.50 7.00 + 0.09 stagger
    bed                                  -18.4 LUFS, seam step 0.00009
    finished cut                         -17.9 LUFS, -2.8 dBTP
    130 lifts in exercises.json          every muscle in the vocabulary,
                                         every badge file present
    dead beats across all 130 lifts      6, all of them unavoidable
    the disc over a hostile poster       3-13 levels of residual inside the circle

`audit.py` picks the frames rather than filtering them: a badge and the muscle it
lit are both finished 0.52 s after landing, so the gaps between one finishing and
the next starting are windows where the only thing allowed to move is the liquid.

```
../.venv/bin/python audit.py push_silent.mp4 --cues push_cues.txt
```

The 128 px it reports on this cut is **not motion**. It is a 64 × 2 px sliver on
the boundary between a near-black row and a white one — x264 ringing against a
110-level step, diffing 9 to 11 levels against a tolerance of 10. Raising the
tolerance would hide it and would also hide real things, so it is left visible
and written down here instead.

## Still open

- the label-position check in `check_base.py` is unreliable and only prints a
  note; look at the poster before animating
- `exercises.json` holds 130 lifts. One that is not in it stops the render with
  the name it could not find, rather than guessing
- the body is ~211px tall in the finished clip, which is what the row geometry
  allows. It reads as a map — *the back lit up* — rather than as anatomy. Making
  it meaningfully bigger means moving the caption bars, which means a new
  `base_layer.png`
- the athlete on the left is still generated, and is the only part of the clip
  that can come back wrong. The right half no longer can
- `bodymap.py` has one figure. A second, heavier or lighter, would let a topic
  pick one — but the five rows must always share it

## What is known to break

Everything in `flow.md` still applies, and `PROMPTING.md` holds the half of it
that is about the prompt rather than the animation: why the template says what it
says, what the generator gets right unasked, what it gets wrong every time, and
what each of those cost in generations. Read it before changing a word of
`ImageSwap.txt`. Added or changed by this folder:

- **The waves may not be red, orange or amber.** The badges are red, orange and
  blue, and the synergist is the commonest tier in the table, so an amber wave
  loses roughly a third of every row. The first cut of PULL DAY was amber and
  the word *Biceps* was readable only from the shadow under the ball. The
  allowed arc — lime, cyan, violet, fuchsia, teal — was picked by rendering all
  five with a red, an orange and a blue badge on each. See `Prompts.txt`.
- **`scale` is against the radius, not the diameter.** `body_overlay.plan`
  takes the figure's height as a multiple of the guide circle's *radius*. Read
  as a diameter it is 4.4r and the arms hang a quarter of the poster out either
  side.
- **A muscle that does not show from a view is a dead beat.** The badge lands
  and the hit sounds over a body where nothing happens. Two things hold it down:
  `view_for` picks the side that shows *more of the row* before it asks which way
  the row faces, and `bodymap.py` carries a gluteus medius on the front view —
  without it every squat, lunge and leg press lands a GLUTES badge onto nothing.
  Six of the 130 lifts still have one, and the planner prints a line naming it.
- **Two lit muscles on the same tier merge.** Glutes beside hamstrings, both
  primary, is one red mass across the back of the legs with no anatomy left in
  it. Every lit region carries a darker rim of its own colour.
- **Catmull-Rom at the textbook tension overshoots.** At 0.5 every tight corner
  bulges and a pectoral comes out as a lozenge — the first draft of the figure
  was made entirely of pills. 0.34.
- **Time-domain noise does not loop.** The bed's noise is built by shaping a
  spectrum and transforming back, so sample n−1 joins sample 0.
- **`alimiter` undoes its own limit.** `level` defaults to true and auto-levels
  the output back to 0 dB. `level=disabled`.
