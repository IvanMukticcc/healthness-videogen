# Longevity — the plan

Second version. The first one is in the history at `d841fff` and was wrong in its
axis; Biohacks took it apart within the hour and the argument that killed it is
recorded below, because it is the useful part.

---

## What survives from the first version

**The structural break.** All four existing variants share one spine — five rows,
a wave each, cause on the left, effect on the right, the mechanism named between
— and in all four **the five rows are five parallel facts**. Shuffle them and you
lose only rhythm.

The father makes the five rows **one thing that runs**. Top to bottom is time.
The poster stops being a list and becomes a line.

And the mechanism for it already exists without having been built for it:
`--surge` runs a highlight down the rows on a 0.06 s stagger and the finale fires
when it arrives. Built to give the clips an ending; it is a picture of something
travelling.

## What was wrong, and how we know

The first version made the five rows **five decades** — 30s through 70s — each
naming the lever that buys most in that decade.

It fails its own check. This category's whole safety argument is that every row
carries a source and an unsourced row does not ship, taken from Biohacks'
`hacks.py`. **"The one lever that buys most in your 40s" has no study behind it
and cannot have one:** cohort studies give effect sizes over a population, not
decade-indexed rankings. Every row would have been refused by the checker the
plan proposed to adopt. That is not a tooling gap, it is the concept saying it is
not sourceable.

Two more, from the same critique and both right:

- **Four rows out of five are addressed to somebody else.** A 35-year-old has one
  row. Every clip we make works because all five apply to the viewer today, in a
  format whose pull is in the first second and a half.
- **It is one poster, not a category.** The children have topics. What is the
  second decades clip? The axis is spent on the first.

## The axis: hours

`fitcircle/Sources/Models/Fasting.swift` ships six metabolic stages with hour
thresholds, and they are not five facts about fasting — they are **five points on
one fast**:

    anabolic       0-4 h    digesting the last meal
    catabolic      4-12 h   glycogen typically becomes the main fuel
    fat burning   12-16 h   fat stores typically become a primary source
    ketosis       16-24 h   ketones typically rise as a fuel
    autophagy     24-48 h   cellular clean-up is typically more active
    deep ketosis    48+ h   prolonged; consult a clinician

**Top to bottom is hours elapsed.** The wave is the fast.

- **one continuous process**, not a metaphor for one. The structural break the
  first version wanted, arrived at honestly
- **every row is the viewer's.** You pass through all of them. Nobody watches
  somebody else's row
- **it is a category, not a poster.** Six protocols in the app — 13:11, 14:10,
  16:8, 18:6, 20:4, OMAD 23:1 — are six clips from one shape, each reaching a
  different depth. 16:8 arrives at ketosis; OMAD reaches autophagy's door
- **sourced by construction.** Every stage in the app is already written as
  "typically" and "commonly", under a comment at `Fasting.swift:222` saying
  never as medical claims, see privacy policy §11. We are not translating claims
  into compliant language. **The compliant language is the source.**

## Why this is the father

Not because it is a clip about our categories — nobody outside this repository
cares about our taxonomy. Because **the fast is the day the other four hang off**.
Foods and Micro are the feeding window. Water, the walk and the light are the
fasting hours. Exercise sits where the protocol puts it. The father is the spine
the children were already attached to, and the poster is the first place that
spine has ever been drawn.

## The picture: photograph the outside, draw the inside

This is the second structural break and it is what stops the category being a
fifth instance of anything.

Nobody can photograph autophagy. Nobody can photograph glycogen running out.
Every child variant solves the "show the mechanism" problem by generating a
picture of it — a bowl, an organ, a lifter — and this one cannot, because at
hour 16 of a fast **there is nothing on the outside to see.** That is not a
limitation to work around. It is the subject.

So the poster is one fast seen two ways at once:

    the band       PHOTOGRAPHED. One room, five hours. The last plate cleared,
                   the evening, the dark, first light, the empty morning
                   kitchen. Continuous - the same place, the same window, time
                   moving through it. This is what the generator is for and it
                   is the only thing it is asked for
    the right      DRAWN. What is happening inside, which no camera can reach:
    circle         the stage, lit on a body. Identical on every clip because it
                   is authored, which is the rule the whole design rests on
    the left       DRAWN. The hour, on a dial that counts to it and locks
    circle

**Outside is a photograph because it is real and changes; inside is a drawing
because it is invisible and must not change.** Foods and Micro generate the
subject. Exercise generates the lifter and draws the body. Biohacks draws
everything, or photographs the whole band. This one splits the frame along what
a camera can actually see, and the split is the point being made.

It also gives the master prompt the one job image models are best at: **the same
place, five times, as the light changes.** Not five subjects that must agree with
each other - one subject that must agree with itself.

## The elements

    left circle    the hour. A dial that counts to it and locks
    the wave       one fast, running down the poster
    right circle   the stage: what the body is typically doing
    the bar        0-24 h across all five rows, one mark per stage boundary
    the caption    the app's own sentence, unedited

**A dial survives when it counts a unit the viewer already has a scale for.**
`16 H` needs nothing under it. `+7 YEARS` needs everything, which is why the
first version's counting circle would have been a claim wearing a number's
clothes. Biohacks' day bar transfers unchanged, relabelled 0-24 h.

**No summing finale.** The first version ended by adding the rows up. Effect
sizes across studies are not summable and the checker would refuse it — and it
was the one place this category could have put an invented number in front of a
health app's audience. On a fast there is nothing to invent: the total is hours
elapsed, which is arithmetic. The finale is the protocol's own end.

## The checker, generalised from `hacks.py` with two changes

1. **`source` needs a kind.** Biohacks' are all studies. A fasting stage's source
   is the app's own descriptive copy, which is not a study and must not be
   dressed as one. So `claim: measured | described`, and the checker **refuses
   any `described` row whose value carries a `%` or a `+`/`-` sign** — that is
   precisely how a descriptive stage becomes a medical claim by accident, and it
   is the one failure that could reach the app's disclaimer.
2. **`dir` collapses.** Everything on a fast is time. Colour by stage instead,
   which the design wants anyway.

## The steps

Each is a commit and a push.

    1   this plan                                              <- revised
    2   longevity.py    the vocabulary: stages, protocols, sources, claim kinds
    3   fasting.json    six stages and six protocols, from the app, with sources
    4   the base        a palette that reads as hours: night through to night
    5   hour_overlay    the dial that counts hours, from dial.py
    6   stage_overlay   the right circle, and the 0-24 h bar
    7   the master prompt, and PROMPTING.md written from the four we have
    8   check.py        sources, claim kinds, the % and +/- refusal
    9   render.sh, and a test clip from material already on disk
    10  flow.md, README.md, CLAUDE.md

## Who is doing what

- **Biohacks writes step 2.** `longevity.py` is the generalisation of their
  `hacks.py`, they know every way it fails, and they found the axis. Offered by
  them, taken.
- **Micro takes the master prompt apart** when it exists. Most topics, most
  rejections, tightest prompt discipline of the four.
- **Exercise on whether a body belongs here.** `bodymap.py` is the only human
  figure in the repository and a fast happens to one. It may not generalise past
  muscles and that is an answer too.
- **The root** owns the folder, the base, the overlays and the integration.
