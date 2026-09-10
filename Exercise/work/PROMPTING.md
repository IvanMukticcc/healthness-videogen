# Prompting the lift poster

`ImageSwap.txt` is what gets filled and pasted. This is why it says what it says.

Six posters for four topics on 8 September 2026, one sent back on a number.
Everything here was paid for by one of those, or by a poster earlier in this
folder's history that `flow.md` still records, and every number is measured on a
poster that exists.

---

## The one sentence

There are two modes now and the sentence changes between them. **In scene mode
the generator is being asked to paint five rooms around five things it must not
touch.** In circle mode - the first thirteen topics - **it is being asked for one
photograph per row, standing in a circle that is already drawn.**

In circle mode, what it is *not* asked for is the load-bearing half: not the
circle - the base draws that, in the row's own wave colour, at 0.85 shade,
identical on every row of every topic - not the body on the right, not the wave,
not the title, not the caption bars. One athlete, cropped by a disc he did not
bring. In scene mode the same list holds minus the disc, and the row itself
becomes the thing being asked for.

Everything hard about this prompt follows from that, in both modes. An image
model has no concept of *leave this alone*; it has a concept of *this is what the
picture looks like*. So most of the prompt's length describes what is already
correct in the attached image, in the language of finished artwork rather than of
prohibition.

The sections between here and **Scene mode** were measured in circle mode. Most
of them carry over - the lightness rule, the named-row colour rule, naming a
checkable instant rather than a dynamic pose - and where one does not, it says so.

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

    ../.venv/bin/python ../../engine/check_base.py <topic>_poster.jpeg --base ../INPUT/base_<topic>.png
    ../.venv/bin/python clean_poster.py <topic>_poster.jpeg --base ../INPUT/base_<topic>.png \
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

## Scene mode, and what it cost to get right

The user asked for it on 8 September after seeing the two variants side by side:
the athlete in the room he trains in, not on a coloured coin, and the liquid
merging with the picture rather than lying on it. Two generations, and the second
shipped.

**What the first one got wrong, and what fixed it.**

- **it added a second logo.** 6764 px of one above the title, where the base
  already carries one at the foot. The old wording said the logo was final, which
  it read as "do not change the one that is there". What holds is naming the
  count: *there is exactly one logo in this image and it is at the very bottom;
  do not add a second one at the top, in a corner, or on a wall inside a
  photograph.* 0 px the next time
- **it made a wave translucent.** Row 2 came back with the room showing through
  it - lovely, and inert: the animator will not paint over what differs from the
  base, so **9.1% of that wave ever moved** against 20-51% on the rows it left
  alone. The paragraph that fixed it says the wave is opaque, that nothing behind
  it shows through, and that where something in the room crosses it, that object
  is what covers it. All five waves came back at 3.0-5.6 mean difference and the
  liquid ran 15-49%
- **it drew a different exercise.** Row 5 asked for a kneeling cable crunch and
  came back as battle ropes - a better photograph, the wrong lift, and the caption
  and three badges above it would all have been lying. Naming the lift is not
  enough; what worked was naming the apparatus, the position and then the
  exclusions: *this is a kneeling cable crunch on a cable machine - not battle
  ropes, not a rope slam, and there is no thick heavy rope anywhere in the
  picture*

**What POWER GOES FIRST got wrong on 9 September, and what the template says
now.** Three faults in one generation, and the first of them made the poster
unusable before any of ours were looked at.

- **it re-framed the canvas.** The image came back at a different aspect ratio,
  cropped: the title read POWER GOES FIRS with the last letters outside the
  frame and the logo was gone altogether. Nothing on a poster like that is at
  base geometry, so `check_base.py` refuses it and there is nothing to repair -
  the whole picture has moved. The old opening said *use the attached image as
  the base*, which the model can satisfy while re-rendering it at its own size.
  What it says now names the size and what proves it: same 1536 x 2752, same
  crop on all four sides, and *if any part of the title or the logo is missing
  or cut off at an edge, the image is wrong*
- **band 2 came back with no wave at all**, and bands 4 and 5 came back with
  waves redrawn as flat ribbons running the wrong way - starting at the right
  and hanging to the LEFT of the athlete. The opening paragraph forbids moving
  and redrawing a wave; it never said how many there are. The new paragraph
  counts them band by band and states the direction: each one begins about a
  sixth in and runs right, and no part of a wave lies left of the athlete
- **the athletes were not on the mark.** Measured by eye off the returned
  poster, their centres sat at roughly 0.30, 0.50, 0.22, 0.62 and 0.66 of the
  width against the 0.163 the left circle marks - three of the five at or right
  of centre, and two of those mirrored, athlete right and liquid left.

  **This is the circle-mode lesson arriving in scene mode.** `flow.md` records
  it as *telling the generator where to put things does not work; a mark it can
  see beats a sentence it has to interpret* - and scene mode is the one mode
  that tells the model to paint the mark out. Having removed the only thing that
  pinned the figure down, the prompt was left holding the sentence, which is
  exactly the arrangement that failed three days running before `left_disc.py`
  existed.

  The template no longer asks for the left circle to be erased. It is covered
  *because the athlete is standing on it*, and the paragraph says so, with a
  falsifiable test beside it - *if you can see his whole body in the middle of
  the image, the band is wrong* - and the direction stated, because a mirrored
  band satisfies every other sentence in the prompt. The right circle and the
  bars are still covered by the room alone.

  If this comes back a second time the answer is probably not more prose. It is
  that scene mode needs its own mark - something in the base at that spot which
  a photograph can plausibly be painted over, the way `left_disc.py` gave circle
  mode a disc. That is an engine question, not one for this folder.

**STRONGER AT SEVENTY cost five generations, and four of them were mine.** The
scene prompt above was Biohacks' with our rows in it. Over one morning it stopped
being that, one reasonable-looking paragraph at a time: a canvas lock, a
five-waves count, an opaque-waves rule, a no-second-logo rule, a safe-area rule,
a mock-up ban, an inset ban, a subject paragraph describing a man in his sixties,
and finally a rewrite of the two paragraphs that place the athlete - the marks
paragraph and the far-left paragraph - into a direct order, *put the athlete in
the left circle*. Every one of them answered a real failure. Together they moved
the athlete to the middle of the band and kept him there for four generations.

Two mechanisms, and they are worth separating.

- **The order contradicted the paragraph above it.** *Put the athlete in the left
  circle* sits two paragraphs under *the photograph is painted over all four
  marks, as if they had never existed*. A model handed both has to decide whether
  the circle is a place or a thing to erase. Biohacks never says *in the circle*:
  it says the subject is at the far left, its centre about one sixth of the width
  in, **where the faint circle is now** - a coordinate, with the mark as evidence
  for it rather than as the instruction. The circle-mode wording that this was
  reaching for works because there the circle is a filled disc that survives into
  the finished poster. In scene mode it does not survive, and an instruction to
  stand in something that will not exist is not an instruction.
- **A row that describes a body composes around that body.** Ours had become
  paragraphs of biomechanics - the weight over the leading foot, the thigh at
  ninety degrees, the trailing foot just clear - and a generator handed a person
  in that much detail frames the person. Biohacks' rows spend their words on the
  room and its light and place the subject with three words, *at the far left*.
  Restoring that shape put the men on the mark in all five bands, first try,
  after four failures.

The user called it before the measurement did: *malo mozda pretjeruzes*, beside
the DESK poster, which passed everything with a shorter prompt. **Prompt length
is not free, and a paragraph that fixed something is not thereby permanent.** The
test for keeping one is whether the failure it answers comes back without it, and
the only way to know is to take it out. All eight came out; only the rewritten
right-third paragraph went back in, for a second athlete drawn on the right, and
that one was a rewrite rather than an addition.

What survived the cut and why it is safe to have dropped the rest: Biohacks has
never needed any of them. If one of those failures returns, restore that single
paragraph and not the set.

Three things came the other way, from their prompt into ours, and all three earned
their place immediately: **the bottom fifth quiet edge to edge** rather than our
lower-left quarter, which is the strip both captions actually sit in; **a lighting
brief in every row header** - `(dark - one light, deep shadow everywhere else)`,
`(light - THIS MUST BE ONE OF THE TWO BRIGHTEST BANDS)`; and **a per-row sentence
naming the quiet strip and what is not on it**, which is the same trick as naming
the rows for the wave colours - a general rule it can nod at, against a named
place it either obeys or visibly does not.

**And two things that are ours rather than the prompt's.** A photographic row has
no row colour to take, so the disc under the body goes on glass - near-black with
a bright rim - and the figure is drawn for a dark ground on every row, because
left on the row's own flag it came out charcoal on charcoal. `render.sh` decides
which mode a poster is by measuring it: the left margin of each stripe differs
from the base by 1.1-2.3 on a circle poster and 26-114 on a photograph.

**The palette stops being free.** Biohacks records that a wave whose colour has
no source in the photograph cannot be joined to it. Ours already may not be red,
orange or amber because the badges are - which leaves magenta, violet, cyan, teal
and lime, all of which exist as gym light. So the topic, the palette and the five
rooms are now chosen together, not in that order and then patched.

---

## Why there is no negative prompt

There was one until 8 September and it was doing harm. It listed `text, letters,
caption, label, title` and `changed logo` beside a body that says the title is
already in the image, that the logo is final, and that the bars under the circles
are reserved for text added later and must be kept clear. The user's report is
that the generator sometimes deletes what it was told to keep, the caption bars
among them.

**A negative field and a body that describe the same image are two prompts, and
on the nouns they share the one with less context wins.** "The title is already
drawn, do not add another" and the bare noun "title" are not the same
instruction. The body says what a thing is and where it is; the list says only
its name, and a name is as easy to read as *remove this* as *do not add this*.

Nothing was lost by dropping it. Every prohibition in that list is in the body
already and in context - `DO NOT CHANGE THE ATTACHED IMAGE`, `ADD NO TEXT OF ANY
KIND`, `THE RIGHT CIRCLE IS ALREADY FINISHED ARTWORK`, and the sentence that
names what may not be put in the right circle covers the anatomy diagram and the
muscle chart the list used to carry. If some failure turns out to have been held
back only by that list, that is a finding to report, not a reason to restore the
block.

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
