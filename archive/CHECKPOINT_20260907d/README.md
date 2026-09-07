# Checkpoint — 7 September 2026, after the blood sugar poster

**Geometry and tools are unchanged since `CHECKPOINT_20260907b`.** `base_layer.png`,
`ribbon_mask.png` and `ribbon_rgba.png` are byte for byte the same files, and so
is every `.py`. The only thing that moved between `c` and here is `ImageSwap.txt`
— and it is what this checkpoint exists to record, because it is the first state
whose prompt reliably produces the look the posters were meant to have.

Read b's README for the tip-levelling that made the liquid run into the middle of
each circle. Everything there still holds.

## What changed from c

Two prompt-only fixes, both found by putting the liver and lungs posters side by
side.

- **The bowls are asked for as clear glass, in every row.** "A bowl of walnuts"
  leaves the material to the model: the same wording gave liver clear glass and
  lungs opaque ceramic in five different colours. Glass is the one that sits next
  to a liquid without competing with it.
- **The organs are asked for as 3D renders, in every row.** Left alone the
  generator reaches for the textbook — a flat anatomical diagram, a cross-section
  drawing — which beside a rendered bowl and a glossy wave looks pasted in from
  another document. They are now asked for with real volume, a visible near side
  and the bowl's own lighting.

Both follow the rule the camera angle taught: **say it in the paragraph above the
rows and again inside every row.** Stated once at the top it holds for a row or
two and then drifts.

The blood sugar poster is the first generated on this prompt and needed no
regeneration: five glass bowls, five three-dimensional organs.

## Shipped

    OUTPUT/07.09/liver_sfx.mp4        LIVER RESET  - FOODS YOUR LIVER LOVES
    OUTPUT/07.09/lungs_sfx.mp4        BREATHE EASY - FOODS FOR HEALTHY LUNGS
    OUTPUT/07.09/bloodsugar_sfx.mp4   BLOOD SUGAR  - FOODS THAT KEEP IT STEADY

## Measured on the three clips

                             liver        lungs        blood sugar
    wave shift on the poster  0.0px all    0.0px all    0.0px all
    moving inside the waves   160 236 px   166 604 px   164 110 px
    moving outside them       161, max 19  81, max 9    173, max 20
    moving in the title       16           23           36
    moving on the captions    0            53           134

Four frames each, difference threshold 12, 15px of slack around the mask because
the silhouette ripples. The blood sugar clip has the highest counts of the three,
so its six largest clusters were opened: every one is a single pixel wide, a
vertical line along a contrast edge. H.264 ringing, not movement.

## Still open

- the label-position check in `check_base.py` is unreliable and only prints a
  note; look at the poster before animating
- the generator draws a soft shadow around the waves although the prompt forbids
  it, and it sits still while the silhouette ripples
- the guide circles are never fully covered; a faint halo survives behind most
  organs. The animator paints them out from the `_clean` base, so it costs
  nothing in the video — but the still poster carries it
