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
`lift_bed_8s.m4a` under the exercise ones, both normalised to -18 LUFS, both CC0
with the sources in `LICENCES.md`.

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

## impact.py

The sound a badge makes when it lands, synthesised: a click, a body whose pitch
falls by a factor of three in 30 ms, a sub an octave below that carries the
weight, and 35 ms of air. The note climbs one pentatonic degree per row and two
semitones per badge inside a row, so five of them read as a list being counted
rather than as a machine.

    import impact
    track = impact.build(cues, seconds, per_row, root=420.0)

It is here because both variants make the same sound. Micro had its own, thinner
one - no sub, root at 760 - and the two drifted the way every other copy in this
repository drifted. A variant that wants a different sound passes a different
`root`; one that wants a genuinely different instrument writes its own and says
why in the file.
