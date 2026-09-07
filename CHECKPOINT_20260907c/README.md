# Checkpoint — 7 September 2026, after the lungs poster

**The geometry is untouched since `CHECKPOINT_20260907b`** — `base_layer.png`,
`ribbon_mask.png` and `ribbon_rgba.png` are the same files, byte for byte, so
bases and posters made against b animate here and the other way round. What this
one adds is two finished topics and the day's working practice.

Read b's README for the tip-levelling and the prompt rewrite that made this state
possible. Everything there still holds.

## What this checkpoint records

- **Two clips shipped**, both through the loop without a regeneration:

      OUTPUT/07.09/liver_sfx.mp4   LIVER RESET  - FOODS YOUR LIVER LOVES
      OUTPUT/07.09/lungs_sfx.mp4   BREATHE EASY - FOODS FOR HEALTHY LUNGS

- **The levelled tips held on real posters.** Both came back with a wave shift of
  0.0px in all five rows. The generator left the liquid alone, which is what the
  whole design rests on.
- **Sound is not optional, and the day's folder is where clips live.** The silent
  pass is rendered to `/tmp`; only the `_sfx` cut is written, into
  `../OUTPUT/<DD.MM>/`. A mute mp4 in the tree is only something to mistake for
  the finished one later.
- **`palettes/` holds both topics' bases**, each with its `_clean` copy and its
  `_layout.json`.

## Measured on the two clips

              liver                       lungs
    wave shift on the poster    0.0px all five rows        0.0px all five rows
    moving inside the waves     160 236 px                 166 604 px
    moving outside them         161 px, largest 19         81 px, largest 9
    moving in the title         16 px                      23 px
    moving on the captions      0                          53 px

Counted over four frames with a difference threshold of 12, allowing 15px of
slack around the mask because the silhouette ripples - the wave legitimately
moves a little outside the shape it was authored in. What is left is H.264
ringing along contrast edges, every cluster one pixel wide.

## Known from these two, fixed after this checkpoint

- **"a bowl" lets the model choose the material.** The liver poster came back
  with clear glass bowls, the lungs one with opaque ceramic in five different
  colours - same prompt, different roll. Glass is the one that reads next to the
  liquid, so it is now stated in the row like the camera angle is.
- **The organs came back flat.** Textbook diagrams and cross-section drawings
  beside a 3D bowl and a glossy wave. They are now asked for as renders with
  volume and the bowl's lighting.

Both are prompt-only; nothing in the tools or the base changed for them.

## Still open

- the label-position check in `check_base.py` is unreliable and only prints a
  note; look at the poster before animating
- the generator draws a soft shadow around the waves although the prompt forbids
  it, and it sits still while the silhouette ripples
