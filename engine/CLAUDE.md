# You are in the engine

Everything here is used by **all four variants**. A change to `flowanim.py`
changes the food clips, the micronutrient clips, the exercise clips and the
biohack clips at once.
That is the point of the folder, and it is also the risk.

## Before you change anything

- Is this an engine improvement, or one variant's behaviour? If a variant needs
  it and the others do not, it is an overlay module in that variant's `work/`,
  not a flag here. The seam is `--overlay`, documented in `README.md`.
- The three wave assets are authored, not derived. `base_layer.png`,
  `ribbon_mask.png` and `ribbon_rgba.png` are what `make_base.py` built once from
  `source_wave_poster.jpeg`, and the mask fits the base to the pixel. Change the
  geometry and **every `base_<topic>.png` in every variant has to be rebuilt**,
  because the mask no longer fits. That is the one change that is never cheap.

## If you are writing a tool here

**Do not name it after a standard library module.** Python puts a script's own
directory first on `sys.path`, so a file here is on the import path of every tool
here - and a variant calling `../../engine/flowanim.py` gets `engine/` searched
before the stdlib. `copy.py` lived for half an hour and broke `check_base`,
`flowanim`, `recolor_base` and `add_labels` in all four variants at once: scipy
imports numpy, numpy's f2py calls `copy.deepcopy` at import time, and it got the
new file. `grab.py` survived only because it never imports scipy. Check the name
against `sys.stdlib_module_names` before you write the file, not after.

One more gotcha, because it cost a rewrite and it will not show up in your own
testing. **`sys.stdin.isatty()` is false in every script, pipeline and agent
subprocess** - which is to say, in exactly the context an engine tool runs in,
and never in the context you tried it in by hand. `copy.py`'s first version read
stdin when `not sys.stdin.isatty()`, so a bare `copy.py prompt` tried to read a
prompt nobody was sending and failed instead of doing its job. Take stdin when it
is asked for by name, never when it seems to be there.

## After you change anything

Re-render one clip in each of the four variants and compare against what it
produced before:

    cd ../Foods/work    && ../.venv/bin/python ../../engine/flowanim.py ...
    cd ../Micro/work    && ./render.sh <topic> <topic>_labelled.png 'auto:...'
    cd ../Exercise/work && ./render.sh <topic> <topic>_labelled.png 'auto:...'
    cd ../Biohacks/work && ./render.sh <topic> 'auto:HACK,HACK,HACK,HACK,HACK'

Identical to the frame is the expected result for a refactor. A difference is
fine when it is a fix arriving - then say which fix, and how large the difference
is, in pixels and clusters, not in adjectives.

    ../engine-status.sh

must still say every variant calls the engine and keeps no copy.

## The comments say bowl and organ

They describe the mechanism through the case it was built for: a bowl of food on
the left of each row, the organ it feeds on the right, both filling a guide
circle drawn over the wave's two tips. In `Exercise` the same two circles hold a
lifter and a body. The mechanism is the circles; the nouns are the food version's.
