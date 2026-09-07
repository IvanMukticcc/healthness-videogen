# Checkpoint — 7 September 2026, end of the day's six clips

**The base layer, the mask and the prompt are unchanged since
`CHECKPOINT_20260907d`** — `base_layer.png`, `ribbon_mask.png`, `ribbon_rgba.png`
and `ImageSwap.txt` are the same files, byte for byte, as are `check_base.py`,
`make_base.py` and `recolor_base.py`. Two tools moved: `add_labels.py` and
`flowanim.py`. Everything else here is what those two changes were learnt from.

Read `OldCheckpoints/CHECKPOINT_20260907b/README.md` for the tip-levelling and
`CHECKPOINT_20260907d/README.md` for the glass bowls and the 3D organs. Both
still hold. The two checkpoints from before the waves were levelled - 20260906
and 20260907 - are in `OldCheckpoints/` too, and their bases only animate with
their own masks.

## What changed from d

**Colour is not a palette any more.** The wave takes the colour of the food that
pours it - yoghurt white, beetroot magenta, honey amber. Picked for how they look
instead, the rows stop meaning anything: the blood sugar poster ran turquoise out
of chia seeds and pink out of yoghurt, and it was the one thing the eye was
looking at. Only the two row background colours are a free choice, and they are
what makes one topic look different from the last. Pale foods go on the dark
rows, dark foods on the light ones - which is a layout constraint on the food
list, not an afterthought.

**Every caption is one size.** `add_labels.py` used to fit each caption on its
own, so ten labels came out at ten sizes - 'OATS' at 60px beside 'SLOWER
ABSORPTION' at 38 - and the poster read as ten decisions instead of one label
style. The size is now found once, from the longest string, and printed along
with which caption forced it. The cost is that one long caption shrinks the other
nine, which is the reason to write short ones:

    yesterday's superfoods    42px   longest 'PUMPKIN SEEDS'
    blood sugar               32px   longest 'SLOWER ABSORPTION'
    heart                     46px   longest 'POMEGRANATE'
    superfoods 5              60px   longest 'PINEAPPLE'

**The liquid is no longer cut where it meets the bowl and the organ.** The
generator covers the guide circle with its artwork and leaves a feathered ring a
few pixels wide where its patch fades into the mark. That ring matches neither
the anchored base nor anything paintable, and inside a circle nothing is
repainted - so it stood there as a dark band straight across a wave that was
moving on both sides of it. `flowanim.py --halo` decides what is covered inside a
circle by size rather than by an exact match: an opening at `--halo-edge` drops
anything thinner than an edge, and what it drops gets the clean base put back.

15px, because the circle's own alpha ramp in `recolor_base.py` is 14. Over that
ramp the anchored base is part tint and part wave while the poster is all wave,
so the difference clears `anchor_tol` on its own and the ring reads as covered.
Anything up to the width of that ramp is edge.

**And the seal may only touch the ribbon's own footprint.** An opening cannot
tell a feathered edge from thin artwork: the first version of this fix took the
gallbladder's bile duct off with the ring, because a duct is exactly as thin as
an edge. Scoped to the mask it seals 4 200px instead of 14 200, and the ducts,
vessels and stalks that hang off an organ survive.

## Shipped

    OUTPUT/07.09/liver_sfx.mp4         LIVER RESET   - FOODS YOUR LIVER LOVES
    OUTPUT/07.09/lungs_sfx.mp4         BREATHE EASY  - FOODS FOR HEALTHY LUNGS
    OUTPUT/07.09/bloodsugar_sfx.mp4    BLOOD SUGAR   - FOODS THAT KEEP IT STEADY
    OUTPUT/07.09/heart_sfx.mp4         HEART HEALTH  - FOODS THAT KEEP IT STRONG
    OUTPUT/07.09/superfoods_5_sfx.mp4  SUPERFOODS FOR VITAL ORGANS, part 5
    OUTPUT/07.09/superfoods_6_sfx.mp4  SUPERFOODS FOR VITAL ORGANS, part 6

Only part 6 was rendered with the seal; the first five carry the cut and keep it.
A rule found halfway through a day applies to what comes after it - the older
clips are the record of how this got better. See "Shipped is shipped" in flow.md.

## The series so far

Parts 1-6 have spent thirty foods and thirty organs, and none may repeat.
`Prompts.txt` lists them; parts 5 and 6 are written out in full there.

## Measured on the six

                        shift   inside     outside          title  captions
    liver               0.0px   160 236    161, max 19       16      0
    lungs               0.0px   166 604     81, max  9       23     53
    blood sugar         0.0px   164 110    173, max 20       36    134
    heart               0.0px   169 143    121, max 17       32     86
    superfoods 5        1.0px   158 994    130, max 21       21    106
    superfoods 6        0.0px   165 725    154, max 17       21    120

Four frames each, difference threshold 12, 15px of slack around the mask because
the silhouette ripples. Every surviving cluster is one pixel wide - H.264 ringing
along contrast edges, not movement.

## Still open

- the label-position check in `check_base.py` is unreliable and only prints a
  note; look at the poster before animating
- the guide circles are never fully covered; a faint halo survives behind most
  organs in the still poster. The video paints it out, the poster carries it
- part 6's throat came back as a thyroid in a neck, and the thyroid was already
  spent in part 2. Ask for the larynx by name if the pair ever comes up again
