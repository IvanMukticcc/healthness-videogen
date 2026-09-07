# Healthness Shorts — the poster animation flow

When the user says **"nova tema"** or **"idemo dalje"**, run this loop.

The point of the whole design: the liquid is authored once and never
regenerated. An image model cannot redraw a wave the same way twice, so the wave
is never asked to. Only the food, the organs, the title and the palette change.

## Where things live

    ShortPrompt/
      OTHER/     the tools, the bases, the mask, the generated posters, this file
      ASSETS/    water SFX, both CC0
      OUTPUT/    finished videos

Run everything from inside `OTHER/`; `ASSETS` and `OUTPUT` are one level up.

## Files that carry the design

| file | what it is |
| --- | --- |
| `base_layer.png` | the reference base: five row stripes, five identical waves, logo. 1536×2752 |
| `ribbon_mask.png` | where the waves are. Authored from `base_layer.png`, **geometry only** |
| `base_<topic>.png` | one per topic: `base_layer.png` recoloured. Same geometry, so the same mask fits |
| `flowanim.py` | the animator |
| `recolor_base.py` | makes a new palette |
| `check_base.py` | did the generator leave the waves alone? |
| `make_base.py` | rebuilds `base_layer.png` from a freshly generated wave poster. Rarely needed |
| `../OUTPUT/` | finished videos go here |
| `../ASSETS/` | water SFX, 8 s, normalised to -18 LUFS |

## The loop

**1. Pick the topic and the palette.** Five foods, five organs, a title, and a
colour scheme that is clearly different from the last few. Build the base:

```
.venv/bin/python recolor_base.py --rows '<dark>,<light>' \
  --waves '<c1>,<c2>,<c3>,<c4>,<c5>' --vibrance 1.05 --contrast 1.04 \
  -o base_<topic>.png
```

Rows 1, 3, 5 take the dark colour and 2, 4 the light one. Put the bright wave
colours on the dark rows. Check the printed "asked vs got" medians and look at
the result before handing it over.

**2. Give the user the prompt**, ready to paste, and tell them to attach
`base_<topic>.png`. The template is in `ImageSwap.txt`; the opening paragraph is
what does the work and goes in unchanged. Filled examples are in `Prompts.txt`.

**3. The user returns the generated poster.** Check it before spending time on it:

```
.venv/bin/python check_base.py <poster> --base base_<topic>.png
```

`safe to animate` means the mask still fits. Anything else: ask for a
regeneration, do not try to animate around it.

**4. Animate into OUTPUT:**

```
.venv/bin/python flowanim.py <poster> --width 1080 --seconds 8 \
    --mask ribbon_mask.png --base base_<topic>.png --drops 0 --reach 0 \
    -o ../OUTPUT/<topic>.mp4
```

**4b. Lay the SFX on it.** Every finished video gets water sound:

```
ffmpeg -y -i ../OUTPUT/<topic>.mp4 -i ../ASSETS/flow_soft_8s.m4a \
       -shortest -c:v copy -c:a aac -b:a 192k ../OUTPUT/<topic>_sfx.mp4
```

**5. Audit before delivering.** Sample a few frames and count what moves outside
the wave mask. It should be single digits. If type, bowls or organs move,
something is wrong — say so rather than shipping it.

## What is already known to break

These were all found by measurement, and each one cost an hour. Do not rediscover them.

- **Droplets.** Detecting loose droplets to fly them separately picks up letters:
  in the bottom rows a label sits four pixels under the wave, and its letters are
  as pale as a lemon wave. `--drops 0`. Bring droplets back only as an authored
  layer in the base, never by detection.
- **Reaching the organ.** The stretch warp that pushed the wave's tip to the
  organ moves the whole horizontal band, and in the bottom rows that band
  contains the label. It ate the "LY" of LYMPHATIC. `--reach 0`. The wave now
  reaches far enough on its own.
- **Liquid in front of the organ.** The mask runs the full length of the wave,
  including under the bowl and the organ. Painting there puts the liquid on top
  of them. `--base` fixes it: paint only where the poster still equals the base.
- **Speckles that stand still.** The `clean` mask must be opened and closed
  before use, or JPEG noise along the wave's edge leaves unpainted pixels sitting
  still while the wave moves under them.
- **Recolouring.** Gamma on brightness, plain scaling on saturation. Scaling
  brightness kills the specular highlight and everything goes chalky; gamma on
  saturation drives it to 1 and the wave turns into a flat vector shape.
- **Artwork crowding the edges.** The bowl and the organ get placed against the
  wave's two tips, so a wave reaching the edge of the poster drags them out there
  and a vertical feed crops them off. The wave is inset to 20%-79% of the width
  for this reason (`--span` in `make_base.py`), and the prompt states the safe
  area outright. On a new poster, added artwork should stay inside x 154-1382.
- **The title is drawn into the base, not asked for.** Left to the generator it
  lands wherever it likes, usually inside the top tenth, where a phone's status
  bar and the feed's own crop cut it off. `recolor_base.py --title/--subtitle`
  puts it at 11%-19% of the height every time: clear of the top, clear of the
  first wave. The prompt tells the model the title is already there.
- **Telling the generator where to put things does not work.** It places the
  bowl and the organ where it likes, and once the wave was inset for the safe
  area they stopped meeting the liquid at all. So the base now carries two faint
  circles per row, drawn over the wave's two tips (`--anchors` in
  `recolor_base.py`), and the prompt tells the model to fill them. A mark it can
  see beats a sentence it has to interpret.
- **A transverse wave through a body that stays put is a flag, not a flow.**
  Keep `--snake` at 0 and `--swell` low; the flow reads through the surface
  advection, not through the silhouette swinging.

## Invariants worth re-checking if something looks off

```
waves span x 307-1213 of 1536       = 20% to 79% of the width
row stripes start at 0, 865, 1220, 1595, 1952
wave rows y 563-798, 931-1166, 1295-1530, 1658-1893, 2020-2255
one traversal of the wave per 8 s   ≈ 95 px/s, the speed the user settled on
```

Ask the user to generate at 1536×2752. Smaller posters are upscaled before
animating and lose sharpness.
