# Biohacks — a free habit, a wave, and the number it moves

Five rows. On the left the hack, on the right a dial that **counts** to what it
changes, a glass chip in the liquid saying what it costs you in minutes, and
under all five a bar filling across one day.

    INPUT/     base_<topic>.png
    OUTPUT/    <DD.MM>/<topic>_biohack.mp4
    work/      render.sh, hacks.py, hacks.json, glyphs.py, dial.py,
               scene_overlay.py, dial_overlay.py, day_overlay.py,
               biohack_audio.py, check.py, icons/, icon-sources/,
               flow.md, README.md, ImageSwap.txt

    cd work && ./render.sh <topic> 'auto:HACK,...' <topic>_labelled.png

## What is different here, and why it is not decoration

**A clip comes from a generated poster, like everywhere else here.** Build the
base, hand the prompt over whole, take the image back, caption it, render. What
this variant adds is that it can also draw both circles itself - a lucide glyph
on the left, a dial on the right - and that is a **preview**: it writes to
`work/<topic>_preview.mp4`, never to `OUTPUT/`, and it exists so a topic can be
seen laid out and timed before a generation is spent on it. Three previews were
delivered as clips on 8 September, which is what the split is for.

**The right circle counts.** Micro's organs do not move for eight seconds and
`MAINTAINER.md` says so; Exercise's body lights. Here the circle holds a
measurement and it counts up to it - 0, 43, 96, 168, 250 - with a ring closing at
the same rate and sixteen ticks under it. A number arriving is a fact; a number
counting is an event, and it is the one gesture on a phone that cannot be taken
in at a glance.

**The message is a day, not a list.** Foods says what to eat, Micro says what is
in it, Exercise says what it works - three catalogues of things. This says: here
is one day of your life, five moments in it, all of them free, and here is what
each one measurably moves. That is `fitcircle/docs/CORE_STORY.md` - *health, as a
rhythm* - as eight seconds of video.

**Every number carries its study.** `hacks.json` holds the value and the citation
in the same entry, `hacks.resolve` refuses a hack whose `source` is missing, and
`check.py` refuses the placeholder. This is a health brand. A number nobody can
chase costs more than the view it buys.

## Three overlays, one per place

`--overlay scene_overlay,dial_overlay,day_overlay`: the left circle, the right
circle, then everything that is in neither. They draw in that order, so the chip
is never behind anything.

`--hacks` and `--hack-times` are declared by `scene_overlay` alone and read by
all three. Declared twice, argparse refuses the parser outright, and that is
right: two modules owning one flag is two modules that disagree about it the
first time either one changes.

None of the three patches the engine. `add_arguments`, `build`, `draw`, `cues`
and `finale` are the whole of what `flowanim.py` knows about this folder.

**Yours to change: everything in `Biohacks/`, and nothing else.** Not `Foods/`,
`Micro/` or `Exercise/`, which other agents are in at the same time. Not
`engine/` — the animator, the wave assets and the tools are shared by all
variants, and a change made from in here is a change made to clips nobody asked
you to touch.

If this variant needs something the engine does not do, **say so and stop**: name
what is missing and what you would change. Do not edit `engine/`, do not copy a
tool in here to edit it, and do not patch around it. The seams meant for this are
`--overlay` with `build` and `draw`, and `refine_art` when the animator has
misread what is artwork. Both are in `engine/README.md`. See `../CLAUDE.md` rule 3.

Nothing here is a copy of an engine file. `biohack_audio.py` **imports**
`engine/impact.py` rather than reproducing it - which is the mistake
`MAINTAINER.md` currently records against `Exercise/work/muscle_audio.py`.
