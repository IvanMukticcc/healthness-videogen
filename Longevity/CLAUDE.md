# Longevity — the father category

Five rows, one fast. **Top to bottom is hours elapsed**, not five topics: the
poster is a line rather than a list, and that is the whole difference between
this folder and the four it unifies.

    INPUT/     base_<topic>.png - what you hand the user to attach to the prompt
    OUTPUT/    <DD.MM>/<topic>_longevity.mp4
    work/      PLAN.md, EVIDENCE.md, longevity.py, fasting.py, fasting.json,
               fast_overlay.py, render.sh, ImageSwap.txt, the bases and posters

    ./render.sh <topic> <protocol> <poster>     a clip
    ./render.sh <topic> <protocol>              a preview, never into OUTPUT/

**Read `work/PLAN.md` first.** It carries the three structural breaks and why
each one exists, and every one of them was argued for and half of them were
argued down. `work/EVIDENCE.md` is the second thing to read and it is not
optional: this is the only category here whose subject can hurt somebody.

## The four things that are not like the other variants

1. **The rows are one thing that runs.** Elsewhere five rows are five parallel
   facts and you can shuffle them. Here they are five points on one fast.

2. **Rows go dim.** A 16:8 lights four and leaves autophagy dark. The gap is the
   content — it is what a longer protocol buys, shown rather than argued — and a
   dim row is not a claim. It says the fast stops before here, which is the
   opposite of claiming the stage. **The caption under a dim row must not add a
   verdict the app declined to give.**

3. **The rows do not alternate.** `--rows` gets the same colour twice, because a
   poster whose argument is that top to bottom is time cannot read as a
   checkerboard. The five waves carry the whole gradient instead.

4. **Photograph the outside, draw the inside.** Nobody can photograph autophagy.
   The generator gets the room and the light and nothing else; the hour and the
   stage are authored here and identical on every clip.

## The rule this folder has and the others do not

**Every row carries a source, and an unsourced row does not ship.** The stage
summaries are the app's own words, copied verbatim from
`fitcircle/Sources/Models/Fasting.swift`, which is written under a comment saying
never as medical claims, see privacy policy §11. **Do not paraphrase them.** The
compliant phrasing *is* the source; a paraphrase is a new claim with nothing
behind it, and this is the one place in the repository where copying text is the
careful option rather than the lazy one.

`longevity.py` refuses a `described` row whose value has grown a `%` or a sign.
That is how a descriptive stage becomes a medical claim by accident.

## Yours to change: everything in `Longevity/`, and nothing else

Not `Foods/`, `Micro/`, `Exercise/` or `Biohacks/`, which other agents are in at
the same time. Not `engine/` — the animator, the wave assets and the tools are
shared by all five variants, and a change made from in here is a change made to
four clips nobody asked you to touch.

If this variant needs something the engine does not do, **say so and stop**. The
seams are `--overlay` with `build`/`draw`/`cues`/`finale`, and `refine_art`. See
`../CLAUDE.md` rule 3.

## What is unfinished

- the hour sits left-of-centre in its ring
- the 0–24 h bar is written in `fast_overlay.bar()` and never drawn
- **an unreached row keeps a full-strength caption**, because `add_labels` draws
  captions into the poster and the overlay cannot dim what is already pixels.
  The row says the fast stops before here and its caption says AUTOPHAGY as
  loudly as the lit ones. This is the one that matters
- no clip has been made from a real generated poster yet; the first was rendered
  from the base itself
