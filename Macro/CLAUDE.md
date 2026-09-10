# Macro — what a food is made of, and what it becomes

Five foods. Each row carries three badges — carbohydrate, protein, fat, per
100 g — and a ring on the right holding the calories. Then **the card turns over**
and the five become one meal, read out in the app's own face.

    INPUT/     base_<topic>.png - what you hand the user to attach to the prompt
    OUTPUT/    <DD.MM>/<topic>_macro.mp4
    work/      foods.py, macro_overlay.py, meal.py, flip.py, macro_audio.py,
               render.sh, ImageSwap.txt, flow.md, the bases and the posters

    ./render.sh <topic> <poster> '<five foods>' '<the meal>'      a clip
    ./render.sh <topic> '' '<five foods>' '<the meal>'            a preview

**Read `work/flow.md` first.** It is the loop and it carries what is already
known to break.

## The three things that are not like the other variants

1. **The clip has two acts and does not loop.** Every other variant ships eight
   seconds that join back to their own first frame. This ships about sixteen and
   ends on a held frame, because act two answers a question act one asks and an
   answer that loops back into the question is a worse clip, not a longer one.

2. **The right-hand circle belongs to this folder, not to the generator.** The
   prompt tells it to leave the circle exactly as it is; `flowanim.py --anchored`
   then restores clean base over the untouched mark, and the ring is drawn on the
   flat row colour. `engine/README.md` documents that wipe as a hazard for
   photographic variants. Here it is the mechanism.

   Verified on the first two real posters, 10 September: inside the right
   circles the generator moved 0.01-0.11% of pixels at a mean deviation of
   2.35-4.71, which is jpeg ringing on the mark's own edge and not artwork, and
   the wipe painted out 261536 px. Both caption bars came back untouched on both
   posters too - 0.00% of pixels moved in all ten, against a historic worst
   elsewhere of 7px of artwork into a 78px bar. Macro is the only variant using
   both bars, so that one had never been tested against a real bowl.

3. **Every number is the app's own.** `foods.py` reads
   `fitcircle/Resources/en.lproj/foods.json` and caches it as `macros.json`. A
   clip advertises the app, so a viewer who looks a food up afterwards has to see
   the figure the clip showed them.

## The rules this folder has and the others do not

**No USDA id, no row.** 1983 of the app's 2272 foods carry an `fdcId`; the other
289 are `dataSource: "estimate"`. An estimate is one row among thousands in an
app. At 1080×1920 it is the only thing on screen. `foods.refuse_unsourced`
turns it down.

**An ambiguous food name is refused, never resolved.** `Oat` matches Oats,
Oatmeal and Oat milk — 379, 76 and 46 kcal. Picking the first is a wrong number
with nothing to notice it by.

**The totals are summed from the portions, never carried beside them.** Somebody
will add five numbers on a phone and has to get the sixth.

**The reference intake is the labelling yardstick, not a goal.** EU 1169/2011
Annex XIII — 2000 kcal, C 260 g, P 50 g, F 70 g — is printed on every packet of
food in Europe, is not advice, and is named on screen. The app shows a user's own
goal; a clip has no user, and a goal on screen would be a goal for nobody or an
implied recommendation.

**Nothing on a per-100 g figure gets a denominator.** The right-hand ring is a
composition — the three macros' share of that food's energy on Atwater's 4/4/9 —
and not a bar against a maximum, because there is no sourced maximum for calorie
density and inventing one puts an unsourced number where a row concludes.

## Yours to change: everything in `Macro/`, and nothing else

Not `Foods/`, `Micro/`, `Exercise/`, `Biohacks/` or `Longevity/`. **Not
`engine/`** — the animator, the wave assets and the tools are shared by all six
variants now, and a change made from in here is a change made to five clips
nobody asked you to touch.

If this variant needs something the engine does not do, **say so and stop**. The
seams are `--overlay` with `build`/`draw`/`cues`, and `refine_art`. See
`../CLAUDE.md` rule 3.

**`flip.py` is deliberately not in the engine.** One variant flips. If a second
one ever wants to, that is when it moves — the way `grab.py` and
`caption_glass.py` got there, after a second user appeared and not before.

## What is unfinished

- the glass is tuned against one poster. `FROST` 0.34, `FOOT_A` 0.55 and
  `TRACK`'s alpha were all measured on breakfast, whose rows alternate dark navy
  and near-white. The ground under act two's cards is whatever act one is doing
  behind them, so a topic whose base is mostly light or mostly dark moves every
  one of those numbers at once. The ring track's separation from the value arc
  was 51.7 levels, fell to 2.0 when the frost thinned, and is 55.7 now - measure
  it on the next topic rather than assuming it travelled. Act one's glass badges
  are the same exposure one surface over: their fill is a tint on the wave AND on
  the row colour the wave does not cover, so each macro's luminance now varies
  12-22 levels across the five rows where flat fills varied 3-6. Hue survives and
  white type is safe at a worst separation of 105, but a base with a lighter
  palette than breakfast's alternating navy and near-white widens all of it
- `check.py` does not exist here. Longevity's is the model: spec off disk, the
  sample count printed beside the verdict, and failing toward alarm
- act two's `--seconds` is fixed at 7.5 and its timeline scales inside that; a
  meal of eight foods has not been tried
