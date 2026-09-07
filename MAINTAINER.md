# If you were started at the root

You are not in a variant. The engine is yours, and so is everything that has to
be decided above one variant. Read `CLAUDE.md` first - the house rules bind you
too - then this.

## The job

1. **Keep the engine one engine.** Five tools, three authored wave assets, one
   copy. `./engine-status.sh` must say every variant calls it and keeps none.
   When it stops saying that, someone forked a tool; read the diff and put the
   difference where it belongs before it grows.

2. **Decide what is engine and what is variant.** The test that has held so far:

   - Does the miss happen in all three? Engine.
   - Is it about what *this* variant puts in its circles, or draws on top? The
     variant's own module, through `--overlay` (`build`/`draw`) or `refine_art`.
   - Is it a number another variant might want different? A flag, with the
     default that keeps today's behaviour.

   The bowl's rim travelling down the wave was the first kind: measured on Foods
   before touching anything, present in all three. The black singlet on a dark
   row is the second: it exists because Exercise puts a photograph in a circle,
   and `refine_art` was added rather than a guess in the animator.

3. **Answer the variants.** They are told to say what they need and stop. When
   one does, the work is yours: verify, decide, implement, and tell them it is
   done and that they need do nothing.

4. **Run the Foods variant.** The classic clips are made from `Foods/work/`; its
   `flow.md` is the loop. Being the maintainer does not exempt you from it.

## Verify before you believe

Both reports from variants so far were right about the cause and wrong about a
number, and both numbers would have been shipped if taken on trust.

- Micro proposed capping the artwork growth at 15-20% of a row's wave. Measured,
  the components that touch a seed run to 81% of a wave's area, so that cap would
  have rejected the fix it was meant to allow. What needed measuring was not the
  component's size but how much wave the growth newly claims: 6.5-8.3%. Cap 25%.
- Exercise proposed `binary_fill_holes` on the artwork mask. The argument is
  sound and it is in the engine now - bounded, because the mask contains both
  guide circles and all ten caption bars, and a poster bridging them would have
  had its wave filled and frozen without a word.

So: reproduce the claim on a poster of your own before acting on it, and measure
the constant rather than accepting one.

## Verify after you change

Rule 4, in full. Re-render one clip in each of the three variants and compare
against what it produced before:

    cd Foods/work    && ../.venv/bin/python ../../engine/flowanim.py <poster> ...
    cd Micro/work    && ./render.sh <topic> <topic>_labelled.png 'auto:...'
    cd Exercise/work && ./render.sh <topic> <topic>_labelled.png 'auto:...'

Identical to the frame is what a refactor should produce. A difference is fine
when it is a fix arriving - then say which fix, and how large, in pixels and
clusters. "Looks the same" is not a measurement.

## Commit your own changes only

`git add -A` once swept an engine edit made by the Exercise agent into a commit
of mine - the one titled *The engine is off limits from a variant, said plainly*.
The change turned out to be worth keeping, which is luck, not process. Stage the
files you touched, by name.

## What is open

- **Exercise's base is not finished.** Do not change it, and do not act on ideas
  that depend on it until its agent says otherwise. One such idea is parked:
  giving `recolor_base.py` a per-side `--anchors`, so a variant that draws its
  own right-hand artwork can have a base with no right guide circle at all - no
  mark, nothing for the generator to fill, no ring to clean up afterwards.
- **`refine_art` has no user yet.** It was added for Exercise's black-singlet
  case; if a second variant needs the same correction, that is the signal to
  promote it into the animator.
- **Exercise still carries its own copy of the strike synthesis.**
  `engine/impact.py` reproduces `muscle_audio.py`'s hits bit for bit; when its
  agent is free, that file should call the engine's and keep only its bed. Until
  then the two are identical and nothing is at risk, but it is a copy.
- **The prompt template is the third thing that exists in three copies.** After
  the tools and the badge synthesis, `ImageSwap.txt` is now forked across Foods,
  Micro and Exercise, and it drifts the same way: Micro measured three faults on
  part 11 and fixed its own copy, and Foods had every one of them. Ported by
  hand this time. The shared half - the circles, the bars, the safe area, the no
  text rule, the glass bowls - is most of the file; the variant half is the five
  rows. Worth splitting before it is fixed by hand a third time.
- **`check_base.py`'s label check is unreliable** and only prints a note. Look at
  the poster before animating.
- **The guide circles are never fully covered.** A faint halo survives behind
  most organs in the still poster. The video paints it out from the clean base;
  the poster carries it, which matters if a still is ever published.
- **`Micro/work/make_prompt.py`** tells the user to put the returned poster in
  `INPUT/`, which rule 7 forbids. Flagged to its agent; it is their file.

## Where the record is

`git log` is the history, and the commit messages carry the reasoning and the
measurements. `archive/` holds the checkpoint folders from before this was a
repository; the two oldest predate the levelling of the wave's tips and their
bases only animate with their own masks.
