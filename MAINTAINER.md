# If you were started at the root

You are not in a variant. The engine is yours, and so is everything that has to
be decided above one variant. Read `CLAUDE.md` first - the house rules bind you
too - then this.

## The job

1. **Keep the engine one engine.** Seven tools, three authored wave assets, one
   copy. `./engine-status.sh` must say every variant calls it and keeps none.
   When it stops saying that, someone forked a tool; read the diff and put the
   difference where it belongs before it grows.

2. **Decide what is engine and what is variant.** The test that has held so far:

   - Does the miss happen in all four? Engine.
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

Every report from a variant so far has been right about the cause and wrong
about the number, and every one of those numbers would have shipped if taken on
trust. That is not a fact about variants. It is a fact about sample size, and
Exercise named it better than this file had: **each of us was confident in
proportion to our sample rather than to the population.** Biohacks inferred a
threshold from one poster in each direction; Exercise inferred a range from
three; the root claimed no stale `work/` prefix existed anywhere on the strength
of a grep that could not match the form it took. Three readings are enough to be
right about a cause and never enough to be right about a constant.

So the question to ask of any number arriving from anywhere, including from here:
how many did they look at, and how many are there?

- Micro proposed capping the artwork growth at 15-20% of a row's wave. Measured,
  the components that touch a seed run to 81% of a wave's area, so that cap would
  have rejected the fix it was meant to allow. What needed measuring was not the
  component's size but how much wave the growth newly claims: 6.5-8.3%. Cap 25%.
- Exercise proposed `binary_fill_holes` on the artwork mask. The argument is
  sound and it is in the engine now - bounded, because the mask contains both
  guide circles and all ten caption bars, and a poster bridging them would have
  had its wave filled and frozen without a word.

- Exercise proposed the title band as the discriminator for a poster grabbed by
  the wrong variant, measured on three posters at 1.9-2.5 against 72-88, and
  concluded any threshold from 10 to 60 would do. Over 37 posters and 1332
  mismatched pairs: own base 0.0-3.2, closest mismatch 2.41, which is *below* the
  worst legitimate match. No threshold separates every pair, and the ten it
  cannot separate share a title - so the check finds a foreign base and not a
  foreign topic. The cause was right, the tool is in the engine, and the
  constant they gave would have hidden its one real limitation.

So: reproduce the claim on a poster of your own before acting on it, and measure
the constant rather than accepting one. Widen the sample until it stops moving -
that is what turned 1.9-vs-72 into an overlap, and it took the whole corpus
rather than a bigger handful.

**And measure the mechanism, not only the number.** Biohacks put a wrongly-taken
poster back by moving it, saw that it kept its place in the newest-first
ordering, and wrote down "put it back by moving, do not copy". The observation
was true. The reason was not: `shutil.copy2` and `cp -p` preserve the stamp
exactly as `mv` does, and what restamps is a bare `cp`. The axis is whether the
method preserves mtime, not copy against move.

That is worse than having no reason at all, in their words, because **a reason
generalises and an observation does not** - somebody reading it would reach for a
bare `cp` on a different file believing they were on the safe side of the rule.
It cost thirty seconds to check afterwards.

Three shapes, then, from one week: right cause and wrong constant, from too small
a sample; right number and wrong subject, from measuring the source recordings
instead of the finished beds; and right observation with the wrong mechanism
under it. The third is the quiet one, because nothing about it looks like a
number that could be wrong.

Which gives the tell to watch for, and it is theirs: **the claims that get
measured here are the ones that announce themselves as measurable.** Pixel
counts, decibels, thresholds - anything with a unit gets checked, because it
looks like the sort of thing that has a right answer. "Move preserves the
timestamp" reads as a fact about a library rather than as a claim, and it was
thirty seconds away from being one. So the question is not only *is this
measured* but *did this even look like something to measure* - because the ones
that do not are the ones that go a day.

## Verify after you change

Rule 4, in full. Re-render one clip in each of the four variants and compare
against what it produced before:

    cd Foods/work    && ../.venv/bin/python ../../engine/flowanim.py <poster> ...
    cd Micro/work    && ./render.sh <topic> <topic>_labelled.png 'auto:...'
    cd Exercise/work && ./render.sh <topic> <topic>_labelled.png 'auto:...'
    cd Biohacks/work && ./render.sh <topic> 'auto:HACK,HACK,HACK,HACK,HACK'

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
- **The prompt template has now been fixed by hand a fourth time.** On
  9 September the negative-prompt block came out of every one of them, because a
  separate negative field contradicts the body of the prompt: every variant's
  list contained `text, letters, caption, label, title` and three of them
  `logo`, while the body says the title and the logo are *already in the image
  and must stay*. A generator handed both reads the negative field as permission
  to remove what the base drew - the reserved caption bars, the title - which is
  what the user reported seeing. One edit per variant, plus Micro's
  `make_prompt.py`, which lifts the block out of its own `ImageSwap.txt` and
  emits it into all nineteen generated prompts, so removing the block from the
  template alone would make `negative()` raise on the next topic.

  The entry below said "worth splitting before it is fixed by hand a third
  time". It has now been four, the cost is measurable - four templates, one
  generator, nineteen files - and the prediction was right. Splitting it is
  still the answer and still nobody's current task.

  Micro's number for it, having done its own share: 21 files. Nineteen were
  generated artefacts that had to be touched only because they are what the user
  actually pastes - and they are also why the fault survived, since fixing the
  template alone would have left nineteen live copies of the bad prompt in the
  folder. So the test for whatever the split turns into is theirs: **changing one
  sentence changes one file, and every generated prompt is a view rather than a
  copy.**

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
- **The finale is half built.** The engine decides *when* it is (`--finale`,
  `cues`/`finale` on the seam) and runs the light through the liquid
  (`--surge`); what lights up inside the circles is each variant's and neither
  has written it yet. Two things go with it, both variant work: the row cues
  move from `1,2,4,5.5,7` to `1,2,3.2,4.4,5.6`, because the shipped rhythm
  leaves 0.35s between the last thing moving and the last frame; and the badges
  have to light as the highlight passes them, because only 22.3% of the liquid
  is visible once the overlays have drawn - 22.7% of the wave is behind a bowl
  or an organ and 71.1% of the rest is behind a badge. `ctx["surge"]["at"]`
  answers when the crest reaches any column, so neither variant has to guess it.
  Until they are written, `--surge` shows properly only in Foods, where nothing
  covers the wave.
- **Biohacks is the fourth variant, and two decisions of its own are settled.**
  Its bed stays in `Biohacks/work/` rather than on the shelf in `engine/sfx/`,
  and the reason first written here was wrong: it said the shelf holds assets
  that were downloaded and licensed while this one is derived. Checked - the
  lift bed is derived too, synthesised by `Exercise/work/muscle_audio.py --bed`,
  and it is not in `LICENCES.md` because nothing was downloaded to make it. So
  the shelf already holds one generated bed and a variant holds another, and the
  line between them is where each happened to end up rather than a principle.
  Left as it is, deliberately, because moving either costs a re-render for a
  tidiness nobody is paying for - but it is an inconsistency and not a rule, and
  the next variant that generates a bed can point at either precedent. Decide it
  then, once, for all of them. Its `--finale-gain 1.00` against
  the engine's 0.316 is also deliberate and measured: a row there is a chip,
  sixteen ticks and a lock, so the chord has to arrive over a brighter and
  busier texture than a badge thudding leaves.

  It is also the variant that answers a question the other three could not. The
  surge was built and then found to be nearly invisible where three 210px badges
  cover the wave; one 313x118 chip leaves 53.7% of the liquid open, and there
  the highlight carries the finale on its own. Verified from this side at 22.0%
  covered and 55.2% visible, in five clusters. That is the first report from a
  variant whose number held.

- **Micro's organs have no grammar yet.** Exercise's body reacts to every badge
  from the first second, so a finale there is a summary of something the viewer
  has been taught. Micro's organs do not move at all for eight seconds, so a
  finale would be the first thing an organ ever does - and a first time in the
  last second reads as a fault, not a climax. The small per-badge response comes
  before the finale, not after it.

## When the user sends a variant into engine/

It happened on the 9th: the user asked Micro for new water, Micro said the shelf
was not its to write to, and the user told it directly to put the files there.
It did, and then told the root rather than leaving it to be found in
`git status`. Both halves of that are right. Rule 3 binds agents, not the person
whose repository it is, and an instruction from them is not a variant reaching
over the line. What the rule is still owed is the notice, so that whoever is
holding the engine is not the last to know.

Verify it anyway, the same as any other report. That one checked out: every
pre-existing asset byte-identical to HEAD, nothing in any variant pointing at
the new files, and the four bed defaults untouched - so the change could not
move a clip anywhere, which is rule 4 in the only form available to an agent
that cannot render in three of the four folders.

## A fix in code, and the same command stale in prose

Found by Exercise the evening the finale routing was fixed, and it is the
maintainer's to sweep because it only shows across folders. Both variants that
keep a "the steps it runs, if one is ever needed alone" block in `flow.md` had
one that no longer matched `render.sh`. Anyone following the prose would have
rebuilt the fault the code had just been cleared of.

Exercise found and fixed its own. Micro's is still stale in three ways as of the
9th: the bed goes in at `volume=1.0` with no duck, so the water never steps back
under the finale - the shape its own agent argued should be preserved because it
is the shape the chosen level was chosen through; the cwd is inconsistent, with
`INPUT/` and `work/` written from the variant root while `../../engine/sfx/` is
only right from `work/`; and `flowanim.py` and `ribbon_mask.png` are named as
though they were local files, which is the layout rule 1 exists to stop people
relearning. Flagged to its agent; it is their file.

Foods and Biohacks carry no such block, so there is nothing to sweep there.

The general shape: when a fix lands in a script, grep the prose for the same
command. `grep -rn "amix=inputs" --include='*.md'` is what found these.

And it is worse than a fix leaving prose behind, which is what it looked like at
first. Micro swept its own file after being told and found four more commands in
the same block naming engine tools as local files, an interpreter path that
resolved from the variant root rather than from `work/` so that none of them
would have started, a step telling the reader to write a labelled poster into
`INPUT/` against rule 7, and a "where things live" section still describing
`OTHER/` and `CHECKPOINT_*/`. The block had also stopped tracking the script
days before it stopped tracking the mix: no `--overlay`, no `--micro-times`, no
finale. **Prose drifts continuously and silently, not at the moment of a fix**,
so the sweep is worth running when nothing in particular has happened.

The standard for calling one fixed is Micro's: run the block by hand, command
for command, and diff its output against the shipped clip. Theirs came out at
correlation 1.000000 with a byte-identical cue file, which is the only version
of "the prose now matches" that is worth reporting.

**And the class is wider than prose.** Exercise ran every documented command in
its folder rather than stopping at the block it had tripped over, and the grep
would have found none of what that turned up: a badge builder writing to
`work/ASSETS/Muscle/` while the overlay had read `work/icons/` since the
three-folder layout landed, `--sheet` defaults resolving to `work/work/…`, and
six prompt recipes running `add_labels.py` on the *base* rather than on the
returned poster - following one would have captioned an empty base and thrown
the generator's five athletes away at the last step. Stale prose and stale
sibling paths in tools nobody has run lately are the same fault; only the first
is greppable. What finds the second is running the commands.

**And running a command is not the whole of it either.** A command can run and
still be wrong. Micro's `README.md` carried an `audit.py` example that predated
the finale, so without `--finale` it counts the ending's own movement as motion
that should not be there: it reports 76 816 px on a clip that measures 4 with the
flag. It executes, it prints, and it is believed. A command that cries wolf is
worse than one that does not run. So the check has three levels - grep the prose,
run the command, and read the number it prints knowing what it should say.

Swept across the four on 9 September, and two things I wrote here that day were
wrong. Both were caught by the variant they were written about, and both are
worth keeping as method rather than as apology.

*"Nothing carries a stale `work/` prefix any more"* was false when written. The
grep looked for the literal - `default=`, `="work/`, `'work/` - and a path built
by segments walks straight past it. At that very commit `micro_icons.py:349` and
`muscle_icons.py:341` both held `os.path.join(HERE, "work", …)`, where `HERE` is
already `work/`, so `--sheet` would have made `work/work/` on first use. **Grep
finds strings, not paths.** That is the whole argument for running the command.

*"The nine vitamin balls are recoverable from `e0020f1^`, where the three-folder
move deleted them"* was also false, and the evidence was two commands above it in
my own terminal: the move brought them in as `Micro/work/icon-sources/`, nine
files, `vit_A.png` through `vit_K.png`. Only `SRC_BALLS` was left pointing where
they used to be. One path, no restore. Micro then proved the flag had always
worked: `--rebuild` re-derives the sphere from those nine byte-identically to the
`_ball_orange.png` every shipped badge was cut from.

What is actually true after all of it: Foods had one bare engine tool name in
`ImageSwap.txt`, fixed here. Micro's builder wrote to `work/ASSETS/Micro` while
the overlay read `work/icons`; repointed, and `--all` then rebuilt all 40 badges
byte-identically to the ones in every shipped clip. Its `make_prompt.py` had
written the rule-7 violation into **twelve** generated prompts rather than the
two the grep found - the generator, not the files, was the fault. And the
poster's real route, `<topic>.jpeg` from `grab.py` converted to a lossless
`<topic>_poster.png`, was in no document at all, so one step grabbed a jpeg and
the next silently expected a png. Biohacks writes and reads `work/icons` in one
place and is clean.

## Where the record is

`git log` is the history, and the commit messages carry the reasoning and the
measurements. `archive/` holds the checkpoint folders from before this was a
repository; the two oldest predate the levelling of the wave's tips and their
bases only animate with their own masks.
