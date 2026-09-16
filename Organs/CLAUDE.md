# Organs — food for vital organs, in one scene

Five foods on the left, the organ each one feeds on the right, the liquid running
between them and the micronutrients popping onto the row as it goes. Then the
finale: the surge runs down the poster, every organ lights again, the chord
lands. That is the whole clip and it ends where it ends.

    INPUT/     base_<topic>.png
    OUTPUT/    the old per-variant folder, kept as history - nothing writes to it
    work/      render.sh, make_prompt.py, ImageSwap.txt, meals.json,
               audit.py, flow.md, README.md, the posters

    cd work && ./render.sh <topic> <topic>_labelled.png 'auto:FOOD,FOOD,FOOD,FOOD,FOOD'

The finished clip goes to `../../OUTPUT/ORGANS/<topic>_organs.mp4` (`../CLAUDE.md`
rule 12), flat and dateless. `../../OUTPUT/DONE/ORGANS/` is what has gone out; the
user fills it by hand and nothing here writes to it.

`render.sh` does animation, pops and mux in one command, because the three have
to agree on when the badges land and typing the times twice is how a pop ends up
half a frame off its badge.

## This folder was Micro until 16 September 2026

The micro series split in two on the user's instruction. This half is the classic
one - one scene, organs on the right, the finale at the end. The other half is
`../Vitamins/`: the right circle holds the vitamin the food is known for instead
of an organ, act one has **no** finale, and the poster turns over into a second
act with the micro score on it.

Three consequences worth knowing before you go looking for something:

- **The two-act cut is not here.** `render2.sh`, `micro_card.py`, `micro_result.py`
  and the act-two grams went to `../Vitamins/work/`. A clip from this folder is
  eight seconds long and has one scene in it, which is the point.
- **The badge machinery is in the engine.** `micro_overlay.py`, `micro_audio.py`,
  `micro_icons.py` and `engine/micro/` - the 42 balls, the nine sources and
  `nutrients.json` - moved to `../../engine/` the same day, because two variants
  now read them and two copies of a badge set is precisely the arrangement
  `../CLAUDE.md` rule 1 exists to prevent. They are called by path, never copied
  back in. `../engine-status.sh` checks that, and it is on its list.
- **`../../OUTPUT/MICRO/` and `../../OUTPUT/DONE/MICRO/` are left alone.** The 28
  clips filed there were cut before the split, as two-act organ clips that belong
  to neither category cleanly. Rule 5: a shipped clip is not re-filed, re-cut or
  re-named because a later one is organised better. Do not tidy them.

## The seam

**`micro_overlay.py` plugs into the engine, it does not patch it.** Its
`add_arguments`, `build` and `draw` are what `../../engine/flowanim.py --overlay
micro_overlay` calls. There was once a `micro_patch.py` here that grafted the
badge layer onto a copy of the animator; the hook replaced it. Do not bring it
back, and do not copy an engine file into this folder.

**Yours to change: everything in `Organs/`, and nothing else.** Not `Vitamins/`,
which is the sibling category and has its own agent; not `Foods/`, `Exercise/`,
`Macro/`, `Biohacks/` or `Longevity/`. And **not `engine/`** - the animator, the
wave assets, the badge set and the tools are shared by all seven variants now,
and a change made from in here is a change made to six clips nobody asked you to
touch.

If this variant needs something the engine does not do, **say so and stop**: name
what is missing and what you would change. Do not edit `engine/`, do not copy a
tool in here to edit it, and do not patch around it. The seams meant for this are
`--overlay` with `build` and `draw`, and `refine_art` when the animator has
misread what is artwork. Both are in `engine/README.md`. See `../CLAUDE.md` rule 3.

`work/make_prompt.py` fills the current template for a topic. That is compatible
with rule 8: it reads `ImageSwap.txt` as it stands now rather than keeping a copy
of a prompt written yesterday. Its output is a working file - do not file it in
`INPUT/`.

`work/meals.json` carries what each topic is: its title, its captions, its badge
list and the five foods with their servings. The grams are there because the 28
clips in `OUTPUT/DONE/MICRO/` had a second act that used them, and rule 13 says
an authored list no command can give back is kept rather than dropped. Nothing in
this folder reads them today.
