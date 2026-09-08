# Prompting the lift poster

`ImageSwap.txt` is what gets filled and pasted. This is why it says what it says.

Six posters for four topics on 8 September 2026, one sent back on a number.
Everything here was paid for by one of those, or by a poster earlier in this
folder's history that `flow.md` still records, and every number is measured on a
poster that exists.

---

## The one sentence

**The generator is being asked for one photograph per row, standing in a circle
that is already drawn.** Not the circle - the base draws that, in the row's own
wave colour, at 0.85 shade, identical on every row of every topic. Not the body
on the right, not the wave, not the title, not the caption bars. One athlete,
cropped by a disc he did not bring.

Everything hard about this prompt follows from that. An image model has no
concept of *leave this alone*; it has a concept of *this is what the picture
looks like*. So most of the prompt's length describes what is already correct in
the attached image, in the language of finished artwork rather than of
prohibition - and the one thing it does ask for is described as fitting a mark
rather than as being placed somewhere.

---

## What it gets right without being asked

Prompt length is not free, and these cost nothing:

- **the waves' geometry.** Six posters, worst drift 1.4 px, 0.0 on five of them.
  The instruction stays because the one time it drifts the mask no longer fits
  and the video breaks
- **the right circle.** 0 px drawn inside it on all four topics. That is the
  `FINISHED ARTWORK` wording plus the list of what not to put there, and
  `flow.md` records what it was like before: on PULL DAY the generator rubbed out
  the guide mark and the caption bar and drew a stroked ring of radius 200 around
  a circle of 138
- **no text.** Not one word added on any poster this day, with the rule split in
  two - the title, then everything else
- **photographic cut-outs.** Never once came back as an illustration or a render

## What it gets wrong every time unless stopped

- **the athlete is bigger than the mark.** He arrives at roughly twice the
  circle: an opaque photo disc of radius about 180 against the circle's 138 in
  the early posters, and on KETTLEBELL row 4 a figure whose legs ran well past
  the caption bar. That is not cosmetic. `clean_poster.py` restores the bar,
  because `add_labels.py` takes its ink from whether the ROW is light or dark and
  that is wrong over a photograph - and restoring it across a pair of shins cut
  them off and left both shoes floating underneath, 3533 px taken back and two
  orphans that read as debris rather than as occlusion. The sentence that fixes
  it is in the prompt now: *sized to the circle and cropped by it, does not stand
  through it, no part of him appears below the circle or beyond it on any side.*
  It took that row from 3533 px to 279. **It is not free** - see the hard part
  below

- **it repaints a wave it was told not to touch.** KETTLEBELL came back with both
  light rows washed out, wave and disc together: row 4's contrast against its own
  stripe fell from 138.6 to 27.0, row 2's from 115.9 to 49.2. The opening
  paragraph already said *do not restyle them, do not change their colour* and
  that was not enough. What worked, first try, was naming the rows: **the waves
  on the second and fourth rows are dark green and sit on a light background,
  that contrast is deliberate, do not tint them towards the background, do not
  harmonise the image.** The regeneration kept 100, 99, 100, 99 and 101% of each
  wave's contrast. A general rule it can nod at; a named row it either obeys or
  visibly does not

- **it brings its own circle if the base does not draw one.** Three days, three
  answers: an opaque white disc on a dark row, a near-black one on a light row,
  and then - after the prompt said not to draw a disc - a cut-out athlete
  standing on the row with nothing behind him. A design element identical on
  every row of every topic does not belong in a sentence a model interprets, so
  `left_disc.py` draws it and the prompt only says the athlete stands inside it

- **it obeys a sentence over a mark.** The safe area is one FOURTEENTH of the
  width, not one tenth. The guide circles reach x 112 and a tenth of 1536 is 154,
  so a tenth tells the model to keep the athlete out of the very circle it is
  told to fill - and it does exactly that. Even at a fourteenth it overruns:
  CARDIO reached x 102 and 107, WEEK ONE row 4 reached x 62, all with a hand or a
  trailing foot

---

## The hard part: the disc, and what stands in it

Biohacks has a join to cover, where the wave's blunt cut is exposed and something
in the photograph has to hide it. Here `left_disc.py` covers that cut by
construction, so this variant's hard part is the opposite one: **the athlete has
to fit a circle he is being cropped by, and both directions of missing cost
something.**

Too big and the caption bar cuts him - measured above, 3533 px and a pair of
orphan shoes. Too small and the row goes quiet: after the containment sentence
was added, KETTLEBELL's left circles differ from the base by 29 to 48 where the
other three topics run 46 to 74. That is the athlete shrinking inside his disc,
and it is the price of the sentence. **Use it on a topic that has already
overhung, not by default.**

Then there is the kit, which is the same problem wearing different clothes. The
prompt asks for plain dark training kit because it cuts out cleanly against no
background - and a black singlet on a near-black row is invisible to the
animator's artwork test, which finds artwork by difference from the base or by
detail and has neither here. 8497 px of an athlete were painted across with
liquid before `body_overlay.refine_art` walked his silhouette out from the
circle's centre, and `render.sh` passes `--anchor-tol 6` because the guide-circle
wipe was taking 18889 px off athletes at the engine's default of 20. The prompt
cannot fix that and should not try; it is named here so nobody "helpfully" asks
for a lighter kit and breaks the cut-outs to solve a problem the overlay already
solved.

---

## What the checks are for

Run both before spending a render.

    ../.venv/bin/python ../../engine/check_base.py <topic>.jpeg --base ../INPUT/base_<topic>.png
    ../.venv/bin/python clean_poster.py <topic>.jpeg --base ../INPUT/base_<topic>.png \
        -l base_<topic>_layout.json -o <topic>_clean.png

`check_base.py` answers the only question that can break the video - did the
waves move - and, since 8 September, whether the poster came from this base at
all. `clean_poster.py` asks that second question again at the engine's tolerance
and then takes back what was never the generator's: the right circle and the ten
caption bars. `render.sh` asks a third, before it will write to `OUTPUT/`:
are there athletes in the left circles at all.

**Three things they cannot tell you.**

The title check finds a foreign **base**, not a foreign **topic**. Two posters
sharing a title both pass - Micro measures 5.4 between SUPERFOODS 7 and the
SUPERFOODS 12 base. Every Exercise title is unique today, which is luck rather
than protection.

**A restyled wave passes.** KETTLEBELL's two washed-out rows were reported *safe
to animate*, correctly: that check measures whether the mask still fits, and
geometrically nothing had moved. Nothing measures colour. What it looks like in
the finished clip is not a pale row but **two greens in one row** - the animator
reads the liquid's colour from the base and refuses to paint over what it scores
as artwork, so base-coloured liquid slides through the generator's static paint
with a hard edge between them. Look at the light rows.

**Nothing measures whether the athlete fits his disc.** Both failures above - the
severed shins and the shrunken figure - passed every check in the folder.

---

## Sending one back

Cheap, and cheaper than a render. **Say the number, name the row, and give the
whole prompt again** with the paragraph that failed rewritten - never a diff,
never "change only row 4". The person pasting is holding one thing, not two, and
house rule 8 is that the prompt is not a file: it is written in the terminal for
the topic at hand and handed over whole.

A reject costs one generation. A poster that passes and should not costs a
render, a look, a rewrite and *then* a generation anyway. KETTLEBELL was sent
back on 138.6 down to 27.0 and came back right the first time.

---

## The shape of a row line

Every one that has worked has the same four parts in the same order:

    Row 4: an athlete performing a one-arm kettlebell clean,
      ^ which row, and the lift named as a lift rather than described

    seen from a low three-quarter angle,
      ^ the camera, restated in every row. Said only at the top it holds for a
        row or two and the rest drift; said only in the rows it reads as
        decoration. Both, every time

    caught at the catch with the bell landed in the rack position against the
    chest and forearm, the elbow tight to the ribs,
      ^ a checkable instant, not a dynamic pose. "The hardest point of the rep"
        is a phrase it can nod at; the bottom of a squat is a thing it either
        draws or does not

    the shoulders and upper back under visible tension, the kettlebell fully in
    frame.
      ^ what has to show, and what identifies the lift. The right caption names
        the muscle group, so the photograph has to earn it

---

## What was not taken from Biohacks

Their `PROMPTING.md` is the shape this file follows, and four things in it are
theirs alone. **The join rule** - a light source or coloured mass at the far left
that the wave comes out of - solves an exposed cut that `left_disc.py` covers
here. **"Neither circle is asked for"**: this variant asks for one. **The
colour-of-the-hour palette**: our palette is decided by the badges, which are
red, orange and blue, so the waves are lime, cyan, violet, fuchsia or teal and
never red, orange or amber - `Prompts.txt` records what was measured and what an
amber wave cost. And **scene mode**, which is a different picture entirely.
