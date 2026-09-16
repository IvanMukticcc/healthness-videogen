# Vitamins — what the food carries, and what it adds up to

Five foods on the left, and on the right, instead of an organ, **the vitamin that
food is known for** - the app's own ball, blue, with the letter on it. The liquid
runs, the other micronutrients pop onto the row, and then act one simply stops:
no surge, no chord, nothing that announces an ending, because this clip is not
over. The poster turns over like a window and act two is on the back of it - how
much of which micronutrient the five foods actually carried, and the micro score.
Then the ending.

    INPUT/     base_<topic>.png
    work/      topics.json, vitamins.py, render.sh, render2.sh,
               vitamin_overlay.py, micro_card.py, micro_result.py,
               make_prompt.py, ImageSwap.txt, make_fixture.py, flow.md, README.md

    cd work && ./render.sh <topic>

One argument. Everything else - the five foods, their labels, their headline
vitamins, their badges, their servings - is derived from `topics.json` by
`vitamins.py`, and the derivation is the point (`../CLAUDE.md` rule 13).

The finished clip goes to `../../OUTPUT/VITAMINS/<topic>_vitamins.mp4`
(`../CLAUDE.md` rule 12), flat and dateless. `../../OUTPUT/DONE/VITAMINS/` is
what has gone out; the user fills it by hand and nothing here writes to it.

## This folder was half of Micro until 16 September 2026

The micro series split in two on the user's instruction. `../Organs/` is the
classic half - one scene, organs on the right, the finale at the end. This is the
other half, and the three differences are the whole of it:

|                    | Organs                  | Vitamins                          |
| ---                | ---                     | ---                               |
| the right circle   | the organ, generated    | the vitamin ball, composited      |
| the prompt         | asks for bowl AND organ | asks for the bowl and leaves the right circle empty |
| the ending         | finale at 5.4s, one act | no act-one finale; the turn, the card, then the end |

## The right circle is not generated, and that is deliberate

The prompt tells the generator to leave the right circle exactly as it arrives.
`vitamin_overlay.py` puts the ball on afterwards, out of `engine/micro/icons/`.

A generator asked for "the vitamin C in this food" draws pills one time, a bottle
the next and an orange the third, and it cannot draw the letter at all, because
the prompt forbids text in three places and has to. So the one element that has
to be exactly right is the one element not left to a roll of the dice - which is
the same trade the rest of this repository makes everywhere: **what must be
identical is never regenerated.**

Two things follow, and both are in `work/vitamin_overlay.py` with their reasons:

- the ball is never smaller than the guide circle, because the animator does not
  paint inside a circle and bare circle would be standing liquid beside moving
  liquid;
- the ball is on screen from frame 0 and *lights* on its row's cue, the same
  gesture and the same constants as an organ answering its row in the other
  category. The two are one series.

## The seam

**Two overlays, chained, and neither forks the animator.**
`../../engine/flowanim.py --overlay vitamin_overlay,micro_overlay` draws the ball
first and the badges on top. `vitamin_overlay.py` is this folder's own;
`micro_overlay.py` is the engine's and is shared with Organs.

Each declares its own flags and neither reads the other's - `--vitamin-times` and
`--micro-times` carry the same five instants, filled from one variable in
`render.sh`. That looks like duplication and is not: Biohacks let one overlay read
a flag another declared and its three overlays stopped being runnable separately
at all, throwing `AttributeError` from a module that had declared nothing wrong.

**Yours to change: everything in `Vitamins/`, and nothing else.** Not `Organs/`,
which is the sibling category and has its own agent; not `Foods/`, `Exercise/`,
`Macro/`, `Biohacks/` or `Longevity/`. And **not `engine/`** - `micro_overlay.py`,
`micro_audio.py`, `micro_icons.py` and the badge set in `engine/micro/` are shared
with Organs, so a change made from in here is a change made to that category's
clips too.

If this variant needs something the engine does not do, **say so and stop**: name
what is missing and what you would change. Do not edit `engine/`, do not copy a
tool in here to edit it, and do not patch around it. See `../CLAUDE.md` rule 3.

## topics.json is where a topic lives

`work/topics.json` is the authored half of every topic: the five foods as the
generator is asked for them, their captions, any vitamin somebody chose by hand,
and the serving act two weighs. `vitamins.py` derives the rest and `render.sh`
asks it - so a food, a vitamin or a badge is never typed at a command line, and
act two cannot disagree with the picture above it.

That is `../CLAUDE.md` rule 13, and the cost of not doing it is on record: Micro's
badge lists existed in exactly two places, `prompt_<topic>.txt` which rule 8
forbids reading back, and the pixels of the finished clips. They were recovered by
matching drawn discs against the icon set. **The test is whether a command can
produce it.** A base comes back from `recolor_base.py`, a clip from `render.sh`, a
caption string from `vitamins.py --labels` - a list somebody chose comes back from
nothing.

`make_prompt.py` fills `ImageSwap.txt` as it stands now, from `topics.json`. Its
output is a working file - do not file it in `INPUT/`, and nothing may read
`prompt_<topic>.txt` back (rule 8).
