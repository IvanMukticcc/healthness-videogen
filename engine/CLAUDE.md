# You are in the engine

Everything here is used by **all seven variants**. A change to `flowanim.py`
changes the food clips, the organ clips, the vitamin clips, the exercise clips,
the macro clips, the biohack clips and the fasting clips at once.
That is the point of the folder, and it is also the risk.

Some of it is used by fewer, and that is still not a variant's to change.
`micro_overlay.py`, `micro_audio.py`, `micro_icons.py` and `micro/` are read by
`Organs/` and `Vitamins/` only - the two halves of the micro series, split on
16 September 2026. They are here rather than in either folder because two copies
of a badge set is the arrangement rule 1 exists to prevent, and a change to them
is a change to both categories' clips.

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

Re-render one clip in each variant and compare against what it produced before.
These are invocations that ran on 16 September 2026, not sketches:

    cd ../Foods/work     && ./render.sh heart heart_labelled.png
    cd ../Organs/work    && ./render.sh liver liver_labelled.png \
                              'auto:LEAFY GREENS,BEETROOT,TURMERIC,BROCCOLI,COFFEE'
    cd ../Vitamins/work  && ./render.sh demo
    cd ../Exercise/work  && ./render.sh bigfive bigfive_labelled.png \
                              'auto:BENCH PRESS,PULL-UP,BACK SQUAT,LATERAL RAISE,DEADLIFT'
    cd ../Biohacks/work  && ./render.sh calm \
                              'auto:MORNING LIGHT,COLD FINISH,WALK AFTER LUNCH,LIGHTS DOWN,NOSE BREATHING' \
                              calm_labelled.png
    cd ../Macro/work     && ./render.sh breakfast breakfast_labelled.png \
                              'Greek yogurt,Blueberries,Honey,Oats,Almonds' \
                              '200 Greek yogurt,80 Blueberries,20 Honey,60 Oats,15 Almonds'
    cd ../Longevity/work && ./render.sh hour168 16_8 hour168_labelled.png

`WIDTH=540` makes each about 26s instead of 66s and changes no timing. Two of
them ignore an `OUT=` you give them and write into their own `../OUTPUT/$DAY/`
- Exercise and Biohacks - so check for a day folder you did not mean to make.

Identical to the frame is the expected result for a refactor. A difference is
fine when it is a fix arriving - then say which fix, and how large the difference
is, in pixels and clusters, not in adjectives.

    ../engine-status.sh

must still say every variant calls the engine and keeps no copy.

**A tool added here is not covered until it is on that script's `FILES` list.**
The list is typed by hand, which is the property that let Longevity go unchecked
for a day, and the three `micro_*` tools were added to it the same commit that
moved them in.

## The comments say bowl and organ

They describe the mechanism through the case it was built for: a bowl of food on
the left of each row, the organ it feeds on the right, both filling a guide
circle drawn over the wave's two tips. In `Exercise` the same two circles hold a
lifter and a body; in `Vitamins` the right one holds a badge ball this repository
draws itself and the generator never touches. The mechanism is the circles; the
nouns are the food version's.
