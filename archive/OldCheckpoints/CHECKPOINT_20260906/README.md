# Checkpoint — 6 September 2026

Last confirmed on the SUPERFOODS series, two posters through the loop with the
title drawn into the base: 0 pixels moving outside the waves, 0 in the title
band, rows within 6% of each other on the first one.

The state after Gut Health went through the whole loop cleanly. This overwrites
the earlier save from the same day on purpose: that one still had the guide
circles bleeding through and a check that demanded a regeneration every time the
generator touched up a wave. Nothing there is worth going back to.

## What is here

    flowanim.py      the animator
    make_base.py     builds base_layer.png + ribbon_mask.png + ribbon_rgba.png
    recolor_base.py  a new palette, and the guide circles
    check_base.py    has the generator left the waves where the mask expects them

    base_layer.png   the reference base, 1536x2752
    ribbon_mask.png  where the waves are, geometry only
    ribbon_rgba.png  the waves on their own, with the fade in alpha
    palettes/        the topic bases made so far, with and without circles

    flow.md          the loop, and everything already known to break
    ImageSwap.txt    the prompt template
    Prompts.txt      filled examples

## Restoring

    cp CHECKPOINT_20260906/*.py CHECKPOINT_20260906/*.png \
       CHECKPOINT_20260906/*.txt CHECKPOINT_20260906/flow.md OTHER/

Rebuilding the base from the original wave poster, if ever needed:

    cd OTHER
    .venv/bin/python make_base.py source_wave_poster.jpeg --taper 190 --fade 80 \
        -o base_layer.png -m ribbon_mask.png -l ribbon_rgba.png

## The settings that matter

    wave inset      20% to 79% of the width   (--span)
    tail            narrows over 190px, fades over the last 80px
    guide circles   r=150px at x=330 and x=1190, both at the wave's vertical
                    centre so the bowl and the organ line up. Placing each one on
                    the centreline of its own column puts them 100px apart, and
                    the higher one gets clipped by the stripe above. From the
                    centre, r=150 still reaches the left tip by 15px and the
                    right by 85, so both ends stay covered.
    supersampling   2x, cubic resampling, dither on write
    animation       --drops 0 --reach 0, one traversal per 8 s, ~78-99 px/s

## The title lives in the base

`recolor_base.py --title 'SUPERFOODS' --subtitle 'FOR VITAL ORGANS'` draws it in
with SF Compact Display Black, centred in the gap between the top of the poster
and the top of the first guide circle, with a floor at 5% of the height. It lands
at about 8%-16%.

Asked for in the prompt instead, it goes wherever the model likes, usually inside
the top tenth - where a phone's status bar and the feed's own crop take it. The
prompt now tells the model the title is already there. For a series with a fixed
heading this also means it is identical to the pixel on every poster.

    --title-top 0.03   lower floor, the title sits higher
    --title-top 0.08   higher floor, the title sits lower

## Two bases per topic

    base_<topic>.png         with the circles - attach this to the prompt
    base_<topic>_clean.png   without them - this one goes to flowanim.py

## What this state gets right that earlier ones did not

- the guide circles are painted out before animating, so no translucent second
  shape shows under the liquid
- a repainted wave and a moved wave are told apart; only a moved one is a reason
  to regenerate, and the generator repaints almost every time
- the wave's appearance is read from the poster, not the base, so the
  generator's own gloss survives into the video
- stripes are filled flat, so no ghost of an older wave outline and no patch
- the outline is smoothed after the thickness floor and the taper, not before

- nothing is painted inside the guide circles. The bowl and the organ always sit
  on them, so the liquid under them is hidden anyway, and working the covered
  part out from colour kept failing - a white bowl over a cream wave came out
  with blocks of paint across its face.

- the generator draws its own circular plate behind each organ, because the
  prompt tells it to fill the circle. That is its artwork, not a leftover guide
  circle, and `--anchor-tol` must stay low enough not to erase it. It looks fine
  and it guarantees the liquid ends on something.

## Still open

- the label-position check in `check_base.py` is not reliable: white bowls read
  as type, the subtitle trips it, and short captions are missed. It prints a
  note and nothing more. Look at the poster before animating - labels belong
  under the bowl and under the organ.
- the generator draws a soft shadow around the waves although the prompt forbids
  it. It sits still while the silhouette ripples.
