# Checkpoint — 7 September 2026

The layout rebuilt so every row is identical. Supersedes CHECKPOINT_20260906,
which is kept because its bases and posters still work with its own mask — this
one moves the waves, so the two are not interchangeable.

## What changed from the 6th

- **The rows are laid out here, not inherited from the source poster.** Five
  equal bands between the title and the logo. Each is 826px at 2x, where before
  they were ~710px with 500px sitting idle under the last wave.
- **One gap governs everything.** A row is band, gap, circle, gap, caption, gap.
  Given the band height, that fixes the radius and the circle's position, and
  `make_base --wave-pos` puts the wave so its left tip lands on the circle's
  centre. Measured: every gap 20px, every circle centre within 1.5px of the tip,
  every right tip 100-102px inside its circle.
- **A caption bar under each circle.** Without a marked place for text the
  generator fills the whole row and a caption added afterwards lands on top of
  the bowl. The prompt tells it to keep the bars clear.
- **The geometry is written to `base_<topic>_layout.json`** and read by
  `add_labels.py` and `flowanim.py`. Each used to work it out again, and the
  caption and its bar drifted apart.
- **The waves span 15%-84% of the width**, circles 6.5%-92.4%, matching the safe
  area the user measured on a phone.

## The loop

    .venv/bin/python recolor_base.py --rows '<dark>,<light>' \
        --waves '<c1>,<c2>,<c3>,<c4>,<c5>' \
        --title 'SUPERFOODS' --subtitle 'FOR VITAL ORGANS' --title-top 0.03 \
        -o base_<topic>.png

    # attach base_<topic>.png to the prompt in ImageSwap.txt, in a fresh chat

    .venv/bin/python check_base.py <poster> --base base_<topic>.png
    .venv/bin/python add_labels.py <poster> -l base_<topic>_layout.json \
        -o <poster>_labelled.png --labels 'FOOD|ORGAN,...'
    .venv/bin/python flowanim.py <poster>_labelled.png --width 1080 --seconds 8 \
        --mask ribbon_mask.png --base base_<topic>_clean.png \
        --anchored base_<topic>.png --layout base_<topic>_layout.json \
        --drops 0 --reach 0 -o ../OUTPUT/<topic>.mp4
    ffmpeg -y -i ../OUTPUT/<topic>.mp4 -i ../ASSETS/flow_soft_8s.m4a \
        -shortest -c:v copy -c:a aac -b:a 192k ../OUTPUT/<topic>_sfx.mp4

Rebuilding the base from the original waves, if ever needed:

    .venv/bin/python make_base.py source_wave_poster.jpeg --taper 190 --fade 80 \
        -o base_layer.png -m ribbon_mask.png -l ribbon_rgba.png

## Verified on this state

    every gap                     20.0px in all five rows
    circle centre vs left tip     within 1.5px
    right tip inside its circle   100-102px of a 138px radius
    pixels moving outside waves   29 of 157058
    pixels moving in the title    0
    pixels moving on captions     9

## Three ordering bugs fixed here, all invisible until a frame was opened

- the guide marks were cleared from `arr` after `base` had already been derived
  from it, so they survived into every frame
- the clean copy of the base was taken before the title was drawn, so the
  animator treated the heading as a difference and wiped it
- closing the leftover-mark mask with a 7x7 kernel bridged the gaps between
  letter strokes and ate the captions; the strict test is now re-applied after

## Still open

- the label-position check in `check_base.py` is unreliable and only prints a
  note; look at the poster before animating
- the generator draws a soft shadow around the waves although the prompt forbids
  it, and it sits still while the silhouette ripples
