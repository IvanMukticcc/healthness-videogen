# Longevity — the plan

Written at 00:30 on 9 September, before any code, because the brief is large and
the first thing a large brief needs is a shape somebody can argue with. Every
step below is a separate commit and a separate push. Nothing here is settled
until the folder that owns it has said so.

---

## What this is not

**Not a fifth category in the row.** The user said so outright, and the four
existing ones already share a spine so completely that a fifth instance of it
would be a Micro clip with different nouns:

    Foods       a food     ->  the organ it feeds
    Micro       a food     ->  the organ, with the nutrients named between them
    Exercise    a lifter   ->  a body, with the muscles lighting
    Biohacks    a habit    ->  a dial counting what it changes

Five rows. A wave per row. Cause on the left, effect on the right, the mechanism
named in between. Four variants, one sentence.

## The structural break

In all four children, **the five rows are five parallel facts**. Nothing connects
row 1 to row 5; you can shuffle them and lose nothing but a little rhythm.

In the father, **the five rows are one thing that runs.** Top to bottom is time.
The poster stops being a list and becomes a line.

That is the twist, and the mechanism for it already exists without having been
built for it: `--surge` runs the highlight down the rows with a 0.06 s stagger,
and the finale fires when it arrives. Built last night to make an ending; it is
actually a picture of something travelling through a life.

## The shape

**Five rows are five decades.** 30s, 40s, 50s, 60s, 70s+.

Each row names **the one lever that buys the most in that decade**, and each
lever comes from a different child category — so a Longevity clip is literally
made of the other four, which is what "father" has to mean if it means anything.

    left circle     the lever, in the child category's own visual language
    the wave        one life, running down the poster rather than across a row
    right circle    a dial counting - not an organ, a NUMBER
    the bar         what it is, in the app's own careful language

**The right circle counts.** Biohacks' `dial.py` already draws a dial that counts
to a value and locks. Here it counts years, or a percentage, or a risk figure -
and the finale is where all five have landed and the poster shows what they come
to together. The other four categories end with everything lit; this one ends
with everything **added up**.

## Why this one has a constraint the others never had

`fitcircle/Sources/Models/Fasting.swift` carries a comment that decides the tone
of this whole category:

> Phrased descriptively with "typically" / "commonly" — never as medical claims
> (see privacy policy §11 Health Disclaimer).

Foods can say "garlic, for the tonsils" and nobody is harmed. A longevity
category says numbers about how long people live, and the app it advertises has a
health disclaimer it must not contradict. So:

- **every row carries a source**, and a row whose source is a placeholder does
  not ship. Biohacks already built exactly this - `hacks.py` prints `NO` against
  an unsourced entry and `check.py` refuses it at the end. That machinery
  transfers whole.
- **the language is the app's**: typically, commonly, associated with. Never
  "adds 7 years". "Associated with" is not weaker copy, it is the copy that can
  be defended, and defensible is what makes a claim shareable rather than
  reportable.

This is the first category where being careful is part of the design instead of a
tax on it.

## What it adds that the children do not have

**Fasting.** The app ships six protocols - 13:11, 14:10, 16:8, 18:6, 20:4, OMAD
23:1 - and six metabolic stages with hour thresholds: anabolic 0-4, catabolic
4-12, fat burning 12-16, ketosis 16-24, autophagy 24-48, deep ketosis 48+. That
is a five-row structure that is *already* about time, already written in
compliant language, and already in the product. It is the strongest single topic
this repository has been handed and nobody has animated it.

**Supplements.** Sixteen in `Supplement.swift`, from D3 to creatine to
electrolytes, with units and micronutrient mappings - which means a supplement
row can name what it actually contains rather than gesturing.

## The steps

Each is a commit and a push. Ordered so that the earliest ones are useful even if
the later ones change.

    1   this plan                                              <- you are here
    2   longevity.py     the vocabulary: decades, levers, sources, dials
    3   fasting.json     six protocols and six stages, from the app, with sources
    4   the base         recolor_base with a palette that reads as time
    5   life_overlay     the wave as one line: the surge, slowed and made the point
    6   dial_overlay     the counting circle, generalised from Biohacks
    7   the master prompt + PROMPTING.md, written from the four we have
    8   check.py         sources, language, the claim audit
    9   render.sh        and a test clip from material already on disk
    10  flow.md, README.md, CLAUDE.md

## Open, and going to the other three tonight

- Biohacks is the only folder that has broken the format before. They are asked
  to attack the shape above before step 2 is written.
- Exercise draws the only human body here. A father category about a life may
  want it, and `bodymap.py` may or may not generalise past muscles.
- Micro has the most topics and the tightest prompt discipline. The master prompt
  is theirs to tear apart.
