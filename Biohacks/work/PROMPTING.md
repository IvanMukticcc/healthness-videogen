# Prompting the scene poster

`ImageSwap.txt` is what gets filled and pasted. This is why it says what it says.

Eight generations over one day, five of them sent back. Everything here was paid
for by one of those five, and every number is measured on a poster that exists.

---

## The one sentence

**The generator is being asked to paint five photographs around five things it
must not touch.** Everything hard about this prompt follows from that: the waves,
the title, the logo, the caption strips and the footer are all *already correct*
in the attached image, and an image model has no concept of "leave this alone" —
it has a concept of "this is what the picture looks like". So the prompt spends
most of its length describing what is already there, in the language of finished
artwork rather than of restriction.

---

## What it gets right without being asked

Worth knowing, because prompt length is not free and these cost nothing:

- **the wave's geometry.** Five generations, worst drift 1.0 px, usually 0.0.
  The instruction is still there because the one time it drifts, the video breaks
- **photographic quality.** "Cinematic, real camera, shallow depth of field" is
  enough; it has never come back as an illustration
- **the horizontal cut between bands.** Never once blended two rows

## What it gets wrong every time unless stopped

- **it fills marks rather than removing them.** The first scene poster came back
  with all twenty alignment marks intact, the photograph painted *around* them:
  std 0.8 inside a circle against std 47 in the picture beside it. The fix is
  three parts and all three are needed — name them as alignment marks, say the
  photograph is painted over them, then **list what may not be put there
  instead**: a plain disc, a white circle, a dark circle, a blurred patch, a
  glow. Micro records Google Flow reading "so that no part of either circle is
  still visible" and painting a bright disc over the circle. Covering a mark is
  not removing one.

- **it centres the subject.** "In the left third" produced a man standing
  squarely in the middle. `ITS CENTRE ABOUT ONE SIXTH OF THE IMAGE WIDTH IN FROM
  THE LEFT EDGE` produced him at the far left. A fraction it can measure beats a
  region it has to interpret.

- **it drifts the lightness.** Band 4 came back at luma 131 against a layout
  that says light. This is the one that silently ruins a poster, because
  `add_labels.py` picks white or near-black from the layout's flag *before*
  anyone has seen the photograph — so a band that goes dark does not dim its
  caption, it deletes it. Stated once at the top it drifts; the version that
  holds names the bands, says "as bright as an overexposed photograph", and puts
  `light` or `dark` in the row line as well.

- **it puts detail where the captions go.** `WALK DAILY` landed on a sunlit path
  of grass and stones: contrast 97 against background variation 72, where every
  other caption on that poster ran 122-250 against 5-50. The bottom fifth of
  every band needs its own paragraph, and each row line has to say what is along
  its bottom edge — a smooth table edge, an even paving tone, a plain floor.

## No negative prompt

There is no negative field in `ImageSwap.txt` any more and there should not be
one. The user reported the generator deleting things it had been told to keep,
the caption strips among them, and the negative list is what confuses it.

**This folder is where the mechanism is easiest to see, because its list was the
longest.** It opened `text, letters, numbers, caption, label, title, clock,
watermark, logo` — while the body of the same prompt says `THE TITLE AT THE TOP
AND THE LOGO AT THE BOTTOM ARE FINAL. Do not redraw, move or restyle either.`
Handed both, a model can read the negative field as permission to remove exactly
what the base drew and the body just protected. `logo`, bare, against *the logo
is final*.

It is the purest form of the mistake the first sentence of this file warns
about. A negative field is a list of nouns with all the context stripped off,
describing the same image as the body — and on the nouns they share, **the one
with less context wins**. The body says what a thing *is* and what happens to
it; the list says only that the word is unwelcome.

Nothing was lost by dropping it. Every case the list was carrying is already in
the body, stated as a consequence rather than as a word to suppress: `grey
circle, grey bar, faint circle left visible, plain disc, blurred patch` is the
paragraph about the alignment marks, which is also where this folder already
records that naming them was not enough — it took saying the photograph is
painted over them *and* listing what may not replace them.

If a failure the list was holding back comes back, that is a finding to report,
not a reason to restore the block.

---

## The join, which is the whole difference between good and finished

The wave begins with a blunt cut about one sixth of the way in. In the food
version a bowl sits there and hides it. Here nothing does unless the prompt puts
something there, and an exposed cut is the single thing that makes the poster
look like a graphic dropped onto a photograph.

**The rule that works: every row puts a light source or a coloured mass at the
far left and lets it carry rightwards.** Not an object beside the wave — a thing
the wave can come *out* of.

    sun in a window          gold light floods right
    coffee poured            the stream falls and carries
    water down a shoulder    sheets off to the right
    breath, mid-exhale       a plume travelling right
    a lamp behind two hands  the flare spills between them
    glowing peppers          the red carries off the plate
    a window behind a desk   daylight streaks past the shoulder
    a dusk sky in a window   the rose spills into the room

`longer` row 5 measured the difference. "A man standing up, seen from the side"
put him *beside* the wave and the join read 27. Moving the lamp behind his hands
took it to 83 — the flare is what covers the cut.

**And the wave's colour has to exist in the scene**, which is a constraint on the
palette, not on the prompt. `sugar` shipped first with teal for standing at a
desk, magenta for walking and violet for dinner — three colours with no source in
any photograph the topic could have, so the prompt could only ask for the join in
general terms. Rebuilt so every wave comes out of something real, the same prompt
shape passed on the first generation.

---

## What the checks are for

Run both before spending a render. Between them they catch everything above.

    ../../.venv/bin/python ../../engine/check_base.py <topic>.jpeg --base ../INPUT/base_<topic>.png
    ../../.venv/bin/python check_scene.py <topic>

`check_base.py` answers the only question that can break the video — did the
waves move — and, since 8 September, whether the poster came from this base at
all. `check_scene.py` answers the five that decide whether the picture is any
good: the left mark, the lightness, the right third, the captions, the footer.

**Two things they cannot tell you.** The title check finds a foreign *base*, not
a foreign *topic*: two posters sharing a title both pass. And the join is printed
without a verdict, because the number tracks how bright the scene is rather than
whether the seam is covered — `sleep` row 5, the best-integrated band on that
poster, reads 34, and the exposed cut it was meant to catch read 27. Look at the
band.

---

## Two topics may share a hack. They may not share its photograph.

`day` and `sleep` have three hacks in common, `day` and `firsthour` two. That is
not a problem - a hack is a fact and it belongs wherever it is true. The
photograph is not: five images repeated across two clips makes a feed look like
one clip posted twice.

So before writing scenes, check what has already been shot for those hacks and
frame them differently. `day` did it this way: morning light became a doorway
facing the sun rather than a bedroom window; the cold row moved from a dark
shower to a bright bathroom, changing bands as well as scenes; the walk went
from an open park to a shaded path lit through leaves; the coffee was pushed
away rather than poured, which is also what "last" coffee actually looks like;
and the dimming moved from a bedside lamp to a wall switch.

Cheap to do at writing time and impossible to fix afterwards.

## Sending one back

Cheap, and cheaper than a render. Say the number, name the row, give the whole
prompt again with that row rewritten — never a diff, never "change only row 5".
The person pasting it is holding one thing, not two.

Since `engine/clip.py`, re-handing a corrected prompt costs exactly what the
first one cost: pipe it through at handover and it is on the clipboard as well
as on the screen. The last practical argument for a diff — that a hundred and
fifty lines are tedious to select twice — is gone.

A reject costs a generation. A poster that passes and should not have costs a
render, a look, a rewrite and *then* a generation. The five that were sent back
were all sent back on a number.

---

## The shape of a row line

Every one that has worked has the same four parts in the same order:

    Row 4 (light — THIS MUST BE THE BRIGHTEST BAND ON THE IMAGE):
      ^ which band, and its lightness restated

    the interior of a sauna at the far left built from pale, almost white
    bleached cedar, flooded with flat bright daylight
      ^ the subject, placed, and the tone said again inside the sentence

    a basket of hot stones at the far left with a small red glow ... a thin
    wisp of steam rises off them and drifts right
      ^ the thing that carries rightwards, which is the join

    a smooth unbroken pale bench runs across the bottom of the band and the
    right half is empty pale wall
      ^ what is along the bottom edge and in the right third

Repetition across the paragraph and the row line is not sloppiness. The food
version records the same finding about camera angle: stated once at the top it
holds for a row or two and the rest drift.
