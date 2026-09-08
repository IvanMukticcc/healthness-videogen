# The engine

Six tools and three authored assets. Everything that makes a Healthness Shorts
poster move is here, and **nowhere else**.

    make_base.py        rebuilds base_layer.png, ribbon_mask.png and ribbon_rgba.png
                        from source_wave_poster.jpeg. Deterministic: same source and
                        same flags reproduce all three byte for byte
    recolor_base.py     a palette and a title -> base_<topic>.png, its _clean copy
                        and its _layout.json
    grab.py             the poster the generator handed back, out of Downloads and
                        into <topic>.jpeg beside the caller. The size is the whole
                        safety net: nothing that is not 1536x2752 is renamed
    check_base.py       did the generator leave the waves alone?
    add_labels.py       the row captions, all ten at one size
    flowanim.py         the animator

    base_layer.png      five row stripes, five identical waves, the logo. 1536x2752
    ribbon_mask.png     where the waves are. Authored from base_layer.png, geometry only
    ribbon_rgba.png     the wave on its own, with the tail's fade in alpha
    source_wave_poster.jpeg   the generated poster all three were built from

## The one rule

**A variant folder does not keep a copy of any file in here.** It calls
`../engine/<tool>.py` with its own python, and keeps only what is its own: its
overlays, its prompt, its palettes, its output.

This is not tidiness. Copies were how the same tools ended up at three
different generations at once: on 7 September 2026 Micro was running
`add_labels.py` from the checkpoint of the 7th, `make_base.py` from the one after
it and `check_base.py` from the 6th, while Exercise had quietly changed
all five. Neither had the two fixes made that morning, so in both of them the
liquid still broke where it met the organ.

`../engine-status.sh` reports what each variant is running. It only reads.

When a variant genuinely needs different behaviour, that behaviour goes in the
variant, as its own module and its own flags - the way `micro_overlay.py` and
`muscle_overlay.py` already do it. A fork of a tool is the thing to avoid.

## Paths

The three assets resolve beside this directory, not beside the caller, so
`../engine/recolor_base.py` from any folder finds them without a flag. Everything
a topic owns - `base_<topic>.png`, the poster, the captions, the video - is
passed in explicitly and is written where the caller stands.

## What the geometry guarantees

    waves span x 229-1289 of 1536       = 15% to 84% of the width
    row stripes start at 412, 825, 1238, 1649, 2063, each 413 tall
    wave rows y 491-702, 904-1115, 1317-1527, 1729-1940, 2142-2353
    both tips within ~1px of their circle centre, 25px clear of the caption bar
    one traversal of the wave per 8 s   ~95 px/s

Change any of that and every `base_<topic>.png` in every variant has to be
rebuilt, because `ribbon_mask.png` no longer fits. That is the one change that is
never cheap.

Two things the geometry does **not** guarantee, both found by Biohacks and worth
knowing before a fifth variant rediscovers them.

**The guide-circle wipe assumes the generator painted over the mark.** With
`--anchored`, a pixel that still matches the anchored base where the anchored
base carries a mark is taken as "the generator did not cover this circle", and
the clean base is put back (`flowanim.py`, `left = (d_anc < anchor_tol) & mark`).
That is certain from the code, and it is exactly right for a poster whose whole
job was to fill those circles. It inverts the moment a variant stops asking for
that: a generator that paints a full-bleed photograph *around* the circles leaves
them matching the anchored base perfectly, so the wipe fires on every one of them
and restores flat row colour into the middle of the picture. Reported measured at
2-3 levels of difference inside the circles against a standard deviation of 47 in
the photograph beside them. `--anchor-r 0` turns it off and is the right answer;
nothing in here needs changing. Know which assumption your poster is under.

**The liquid's silhouette moves outside the authored mask.** `--swell` lets the
edge breathe past `ribbon_mask.png` and the resize to render width moves the
boundary again, so a check that asks "what moved that should not" has to dilate
the mask before using it as an alibi. Measured on a 540-wide render with the
variant's own elements excluded: 86px of edge motion within 2px of the mask, 94
at 2-4, 89 at 4-6, 43 at 6-8, and past 8px what is left is x264 ringing. On a
flat row stripe none of it reads; on a bright photograph it does, which is why it
took a photographic variant to surface. Not reproduced from this side - the
poster is not on disk here - so it is one variant's number on one render, and the
shape of it is what to trust rather than the digits.

## The overlay seam

A variant that wants to draw on top of the finished frames does not fork the
animator. It writes a module with three functions and names it:

    ../../engine/flowanim.py poster.png --overlay micro_overlay ...

    add_arguments(parser)   its own flags, added before the final parse
    build(args, ctx)        whatever it needs to draw with, or None to do nothing
    draw(frame, plan, t)    on the finished frame, t in seconds

`ctx` carries `W`, `H`, `fps`, `seconds`, `frames`, `layout`, `geo`, `base`,
`mask`, and `curves` - one function per row giving the wave's own centre line at
any x, which is what an overlay needs to sit *in* the liquid rather than on a row
centre the wave crosses twice and sits on nowhere.

Modules are imported from the directory the command was run in, so a variant's
`work/` folder is where they live. Several can be named, comma separated, and
they draw in that order: `--overlay body_overlay,muscle_overlay` puts the body
down first so a badge is never behind it.

## sfx/

The sound shelf, shared. `flow_soft_8s.m4a` under the food clips,
`lift_bed_8s.m4a` under the exercise ones, both normalised to about -18 LUFS.
They did not arrive the same way: the water beds are cut from CC0 recordings and
`LICENCES.md` has their sources, while the lift bed is **synthesised**, by
`Exercise/work/muscle_audio.py --bed`, and is in no licence file because nothing
was downloaded to make it.

**A bed has no level. It has a level at an instant.** Measured here on the assets
themselves, momentary R128 every half second across the clip: `lift_bed` spans
1.5 LU and is quietest at 8.0s, `flow_soft` spans 2.8 LU and is quietest at 7.0s.
The first is authored that way - its swell is placed so the loop seam falls where
it is quietest - and in a finished mix the spread is wider still, because the
duck's release lands on top of it. So a figure quoted for "the bed" means
nothing without the second it was taken at. Badge rows and the chord are events
at fixed times and a window identifies them; a bed is a continuous shape and it
does not.

### refine_art, the other half of the seam

`draw` runs at the end of every frame. There is one earlier point a variant may
also want, and it is the only other one: **what counts as artwork.**

    refine_art(art, ctx) -> art

`art` is the boolean mask of everything the liquid must not be painted over - the
bowls, the organs, the guide circles, the caption bars. The animator finds it by
difference from the base and by local detail, and both tests can miss. A white
bowl on a pale stripe is nearly the colour the base already had there; a black
singlet on a near-black row has neither colour nor texture to give it away. When
they miss, the liquid is painted across the front of something it should have run
behind, and pale fragments of it are sampled into the wave's texture and travel
downstream.

What the miss looks like depends on what a variant puts in its circles, so the
mask is handed over rather than guessed at harder in here. `ctx` carries `W`,
`H`, `layout`, `mask`, `base`, `poster` and `args`. Return the mask you want -
usually the one you were given with something added.

A variant may define `refine_art` without defining `build` and `draw`, and the
other way round.

### cues and finale, the third half of the seam

    cues(plan) -> [seconds]
    finale(plan, t0, ctx)

Both optional, both about one instant: the end.

The clip counts. A badge lands, a muscle lights, a note climbs one degree of a
pentatonic, and five rows later the ear is waiting for something that never
arrives - the last cue lands at 7.18s of an 8s clip and the remaining 0.82s
carries nothing new. `--finale` is that arrival, and the whole of what the engine
does about it is decide **when**. What lights up is the variant's, because what
is in the circles is the variant's.

`--finale auto` collects `cues(plan)` from every overlay that has it, takes the
last one and adds `--finale-lead` (0.60s: enough to clear the 0.42s pop that cue
started and the 0.47s flash on the body, so the finale begins on ground nothing
else is still moving on). `--finale <number>` sets it outright, for a variant
with no cues at all. Then `finale(plan, t0, ctx)` hands the instant to every
overlay that wants it, and `--finale-cue <file>` writes it for the SFX step. One
number, computed once, in the same file-passing way `--micro-cues` already
works - typed twice it drifts by a frame and reads as a sync fault.

**There is no room for it at the shipped rhythm.** `1,2,4,5.5,7` leaves 0.35s
between the last thing moving and the last frame. The finale needs about 1.8s
after the last row's cue - 0.65 for the row to settle, 0.8 for the finale, and
0.4 of hold, because the last frame is the one a feed freezes on. So the rows
move earlier: `1,2,3.2,4.4,5.6` puts the last badge at 5.78, the finale at 6.38
and leaves 0.8s of settled hold.

**And it is not bought with seconds.** The surface travels a whole number of
ribbon lengths over the clip - that is what makes the loop seamless - so the
speed is `ribbon / seconds` and nothing else. Measured: 8s gives 92px/s, 9s
gives 82, 10s gives 74, 12s gives 61. There is no `--speed` that returns 92px/s
at 9 seconds; the next available value is 165, at two traversals. The clip is
8 seconds.

## --surge

The light that runs the length of every wave at the finale. It is light and
nothing else: the loop is that whole number of traversals, so the one thing a
finale may not do is push the liquid faster.

    --surge 0.30 --surge-dur 0.42 --surge-stagger 0.06 --surge-width 0.10

A band travelling each ribbon's own arc length, so it runs *with* the curve
instead of cutting across it - the same coordinate the streaks use. One row at a
time, 0.06s apart, top to bottom: simultaneous reads as a flash frame, and a
cascade this short still reads as one gesture while giving the eye a direction.

It never touches the artwork (`clean`, like every other paint pass) and it is
gone `--surge-clear` pixels before it reaches a guide circle. That second one is
measured: **22.7% of the wave lies inside a circle and is never painted at all**,
so a highlight that simply stopped at the circle's edge would draw ten hard
edges, one at every bowl and every organ. Verified over the whole window at
1080 wide: 0 px changed outside the wave mask, 0 px changed inside a circle.

**How much of it shows is decided by the variant, not by here.** Of the wave,
22.7% is behind a bowl or an organ and is never painted at all. What covers the
rest is the overlay's business, and the two answers so far are a long way apart.
Micro's and Exercise's three 210px badges take another 54.7% - a badge is 210px
across and the wave is 94 - and leave **22.3% of the liquid visible**. Biohacks'
single 313x118 chip takes 23.6% and leaves **53.7%**; measured again from this
side on its finished render, 22.0% and 55.2%, in five clusters, which are the
five chips.

So in the badge variants the band glinting through the gaps is not the effect,
and the effect is the badges lighting as it passes them. In the chip variant the
highlight carries on its own: the same clip rendered with and without it differs
by +5.00 levels of mean brightness over the visible liquid at the crest, against
0.01 of run-to-run noise.

Either way the variant has to know when the crest reaches a given column, so the
engine publishes it rather than leaving three overlays to work it out
separately:

    ctx["finale"]        the instant
    ctx["surge"]["at"]   at(row, x) -> seconds, when the crest passes column x
                         of that row. Rows are numbered top to bottom, the order
                         the layout lists them in

For the Micro layout at 6.38s that reads: row 1's bowl at 6.46, its three badges
at 6.53, 6.59, 6.65, its organ at 6.72; row 5's organ at 6.96. Half a second,
diagonally across the poster.

## impact.py

The sound a badge makes when it lands, synthesised: a click, a body whose pitch
falls by a factor of three in 30 ms, a sub an octave below that carries the
weight, and 35 ms of air. The note climbs one pentatonic degree per row and two
semitones per badge inside a row, so five of them read as a list being counted
rather than as a machine.

    import impact
    track = impact.build(cues, seconds, per_row, root=420.0)

It is here because the variants make the same sound. Micro had its own, thinner
one - no sub, root at 760 - and the two drifted the way every other copy in this
repository drifted. A variant that wants a different sound passes a different
`root`; one that wants a genuinely different instrument writes its own and says
why in the file. Biohacks does both: its counter's lock is its own, built on the
same inharmonic 1.41 ratio the chord below is, so its finale is a chord of a
sound its clip has already taught the ear five times.

    track = impact.finale(t0, seconds, root=420.0)

The other sound in there: the chord the climbing rows resolve onto, laid at the
finale's instant. Two-operator FM with the modulator at 1.41x the carrier -
which is how a bell is made, and why it is not an organ - seven voices on the
pentatonic an octave over the root, opening upward 12ms per degree, with one
sine an octave *below* the root underneath. On a phone that sine is felt rather
than heard, and it is the difference between a chime and an arrival.

It was chosen off nine candidates auditioned in a finished clip, six of them
real recordings: crotales playing these exact five notes, a tuned Thai gong on
the root, a 40-inch tam-tam, cymbal rolls, all from the Iowa MIS collection and
all free of restrictions. The synthesis won. One measurement from that audition
is worth keeping whatever wins next time: **a phone speaker is gone below about
500Hz.** Through a fourth-order high pass there, the 40-inch tam-tam loses 7.6dB
of itself and the gongs lose 3.0 - the biggest sounds in the collection are the
most impressive of the nine in headphones and the weakest of them in a feed.
This one loses 0.8.

`gain` is 0.398, which is 2dB over the 0.316 the chord was auditioned at, and
that 2dB was not a taste. Three variants measured the same thing independently
and none of them was asked to: at the audition level the cadence arrived 2.4dB
under a Micro badge row, 2.9dB under an Exercise one in the mix and 3.9dB on its
hits track alone, and 0.5dB over the water - the quietest of the three things in
its own half second. A sound that answers a count cannot be that. At 0.398 it
lands level with the row it closes. On the sfx track alone, where neither window
carries the bed, that is 0.5dB under a Micro row and 1.9dB under Exercise's
heavier three-hit ones; in the finished mixes, 0.7 and 2.8.

**Measure a level, never derive one.** Every figure above was taken at its own
gain. A mix window is half a second of bed and badge tails with the chord
somewhere inside it, and it does not move with the chord: +2.00dB of chord moves
that window 1.1dB on Micro and 0.3dB on Exercise, while on the sfx track, where
the chord is the only thing in the window, it moves the full 2.0. Two figures in
here were wrong before this was understood, both derived by adding dB to a
measurement taken elsewhere, and both were caught by the variant they were
written about. The sfx track is the instrument; the mix is the outcome.

Name the meter too, not only the basis. A chord sustains and a badge spikes, so
mean and peak disagree about them by construction and go on disagreeing: on a
corrected Exercise cut the chord measures 2.2dB **over** row 5 by mean over half
a second and 1.0dB **under** it by peak, on the same track in the same window.
Neither is wrong. A level quoted with no meter on it is half a number.

**And the level it returns is the level it has to arrive at.** All three variants
once summed the finale into the same wav as their badge hits and then scaled that
wav by their own pop gain in the mix - 0.85 in Micro, 0.62 in Exercise, 0.80 in
Biohacks. The chord is not a badge and has no business riding the badge gain:
measured, that delivered it **1.41dB under the chosen level in Micro and 4.15dB
under in Exercise**, so one number in this file arrived as three - the drift it
is here to prevent, one layer further down than anyone was looking for it. It
took two variants each reporting "still under the row" and neither being able to
reproduce the other's figure before anyone thought to ask which signal path was
being measured.

Micro and Exercise now give it its own input at unity. Biohacks passes an
explicit 1.00 and is right in outcome for a different reason: it chose that
number by ear on a finished cut with its own 0.80 already in the mix, which is
the general lesson - **the level that counts is the one measurable at the end.**

Where it lands, on the first Exercise cut rendered through the corrected routing,
measured three ways in the same windows of the same finished file:

    momentary, 400ms K-weighted    chord +0.7, +0.2, +0.4 LU over rows 1, 4, 5
    RMS mean, half-second          1.7 to 2.1 dB under them
    sample peak                    1.4 to 2.0 dB under them

Three meters, one window, three answers spanning 3dB - and **only one of them is
a loudness model.** Momentary R128 is the one that says what a listener gets, and
it says the cadence lands level with the rows it answers, marginally on the loud
side, which is where a cadence belongs. The other two are measuring a chord that
sustains against badges that spike, and K-weighting discounts the low sine under
the chord that unweighted RMS was mostly counting. Reproduced from this side on
the shipped file, independently K-weighted: -17.1, -16.6, -16.8 for the rows
against -16.4 for the chord, the same three differences to the decimal.

So quote momentary for this, and treat a level argument settled on unweighted RMS
as unsettled. Micro measures 0.5dB under its quietest row by mean in the mix and
has not been put through the same three yet.

The limiter is idle at either level; the mix peak is set by a badge, not by the
chord.

It is one number here rather than one per variant, deliberately. The level a
shared sound arrives at is part of the sound, and tuned separately in two
folders it becomes two sounds - which is what this file exists to stop. A
variant whose texture genuinely differs passes its own `gain` and says why in
its file, the way it would pass its own `root`.

`lead` puts a riser in front, and is 0 because that is how the chord was picked.
It is the only sound in the clip that says something is *about* to happen -
everything else is heard after the thing has already landed - so it is kept, off.

The tail is cut to what is left of the clip and faded, because a chord still
ringing on the last sample is a click on every lap of the loop.
