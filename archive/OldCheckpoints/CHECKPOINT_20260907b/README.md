# Checkpoint — 7 September 2026, morning

Supersedes `CHECKPOINT_20260907`, taken at 00:13 the same night. That one's bases
and posters still animate with its own mask; this one moves the waves inside the
row, so the two are not interchangeable. Anything made before this checkpoint —
`base_gut`, `base_vital1`-`5`, and the posters generated on them — belongs to the
older mask and must be animated from that folder.

## What changed from the night before

- **Both tips of the wave now sit on a circle centre.** The source wave climbs
  104px from left to right. The placement put its left tip on the circle centre,
  so the right tip arrived 102px high: the liquid met the organ at the top of its
  circle instead of running into the middle of it, and read as stopping short.
  Lowering the wave only trades one end for the other. `make_base.py --level 1`
  removes the tip-to-tip slope and leaves the curve of the wave alone, so the S
  is symmetric and both ends arrive at the same height.
- **The wave's place in the row is derived, not tuned.** `--wave-pos 0.3425` is
  no longer the default. The placement reads the same gap and caption height
  `recolor_base.py` lays the row out with, so the tip and the circle it aims at
  cannot drift apart. `--wave-pos` still overrides it; `--tip-drop` sinks both
  tips a few pixels below centre.
- **The prompt is the user's tested one, verbatim** — `ImageSwap.txt` had drifted
  from what actually works. Two things it was getting wrong:
  - **the bowls came out flat.** Asked for "a bowl of carrots" the generator
    draws it straight down: a disc of food with no rim and no side, which next to
    a glossy 3D wave reads as a sticker. The camera angle is now stated twice —
    once for all five bowls, then again inside every row — and made checkable: an
    elliptical rim, a visible side wall, the food heaped above the rim.
  - **the safe area is one fourteenth of the width, not one tenth.** The guide
    circles reach x 112, and a tenth of 1536 is 154 — so a tenth told the model to
    keep the bowl out of the very circle it was told to fill, and it followed the
    sentence over the mark.
- **Finished clips go to `../OUTPUT/<DD.MM>/`, and only the `_sfx` cut.** The
  video is never published without the water sound, so a silent mp4 in the tree
  is only something to mistake for the finished one later. The silent pass is
  rendered to `/tmp`.

## Verified on this state

    both tips vs their circle centre   within 1.3px in all five rows
    wave inside the circle band        y 491-702 vs circle 432-707 (row 1)
    clear of the caption bar           25px in every row
    poster returned by the generator   wave shift 0.0px in all five rows
    moving outside the waves           161px in 89 clusters, largest 19px
    moving in the title                16px, one column
    moving on the captions             0

The strays are H.264 ringing along contrast edges, all of them one pixel wide.
The count is taken with 15px of slack around the mask, because the silhouette
ripples: the wave legitimately moves a little outside the shape it was authored in.

## Still open

- the label-position check in `check_base.py` is unreliable and only prints a
  note; look at the poster before animating
- the generator draws a soft shadow around the waves although the prompt forbids
  it, and it sits still while the silhouette ripples

## The loop

    .venv/bin/python recolor_base.py --rows '<dark>,<light>' \
        --waves '<c1>,<c2>,<c3>,<c4>,<c5>' \
        --title '<TITLE>' --subtitle '<SUBTITLE>' --title-top 0.03 \
        -o base_<topic>.png

    # attach base_<topic>.png to the prompt in ImageSwap.txt, in a fresh chat

    .venv/bin/python check_base.py <poster> --base base_<topic>.png
    .venv/bin/python add_labels.py <poster> -l base_<topic>_layout.json \
        -o <topic>_labelled.png --labels 'FOOD|ORGAN,...'
    .venv/bin/python flowanim.py <topic>_labelled.png --width 1080 --seconds 8 \
        --mask ribbon_mask.png --base base_<topic>_clean.png \
        --anchored base_<topic>.png --layout base_<topic>_layout.json \
        --drops 0 --reach 0 -o /tmp/<topic>.mp4
    ffmpeg -y -i /tmp/<topic>.mp4 -i ../ASSETS/flow_soft_8s.m4a \
        -shortest -c:v copy -c:a aac -b:a 192k ../OUTPUT/<DD.MM>/<topic>_sfx.mp4

Rebuilding the base layer itself, if ever needed:

    .venv/bin/python make_base.py source_wave_poster.jpeg --taper 190 --fade 80 \
        -o base_layer.png -m ribbon_mask.png -l ribbon_rgba.png

It is deterministic: run on the same source with the same flags it reproduces
`base_layer.png`, `ribbon_mask.png` and `ribbon_rgba.png` bit for bit. That is
what made it safe to move the waves at all.

## Shipped from this state

    OUTPUT/07.09/liver_sfx.mp4      LIVER RESET - FOODS YOUR LIVER LOVES
