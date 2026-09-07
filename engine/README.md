# The engine

Five tools and three authored assets. Everything that makes a Healthness Shorts
poster move is here, and **nowhere else**.

    make_base.py        rebuilds base_layer.png, ribbon_mask.png and ribbon_rgba.png
                        from source_wave_poster.jpeg. Deterministic: same source and
                        same flags reproduce all three byte for byte
    recolor_base.py     a palette and a title -> base_<topic>.png, its _clean copy
                        and its _layout.json
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

This is not tidiness. Copies were how the same five tools ended up at three
different generations at once: on 7 September 2026 MikroVersion was running
`add_labels.py` from the checkpoint of the 7th, `make_base.py` from the one after
it and `check_base.py` from the 6th, while ExerciseVersion had quietly changed
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
