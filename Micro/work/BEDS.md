# Water beds — where the four came from

The engine's `flow_soft_8s.m4a` is what `render.sh` uses unless told otherwise,
and it was rejected on 8 September for sounding like a tap running in a flat
rather than water outdoors. That is measurable, which is how these four were
chosen rather than guessed.

**Basis: the finished 8 s beds, the whole 8.0 s, mono sum, Welch average of
8192-sample Hann frames at 50% overlap, share of total energy, top band
stopping at 8 kHz with a separate column above it.** The first
version of this table measured the *source recordings* - and only their first 40
seconds - while naming the beds in its rows, which are a chosen window with a
high-pass on two of them. Right in direction, wrong in width, and it took someone
re-measuring to catch it. Name the basis or the table is decoration.

| bed | centroid | <80 Hz | 300 Hz-2 kHz | 2-8 kHz | >8 kHz |
| --- | --- | --- | --- | --- | --- |
| `flow_soft_8s.m4a` (in use) | 2838 Hz | 5.0% | 58.1% | **27.2%** | 9.1% |
| `flow_river_8s.m4a` | **1193 Hz** | 1.1% | 74.3% | 15.7% | 0.3% |
| `flow_brook_8s.m4a` | 1826 Hz | 1.3% | 75.7% | 16.3% | 3.6% |
| `flow_stones_8s.m4a` | 1931 Hz | 4.9% | 65.5% | 19.8% | 5.6% |
| `flow_shore_8s.m4a` | **388 Hz** | 17.3% | 33.9% | 2.4% | 0.1% |

A tap in a sink is close, narrow and bright: energy above 2 kHz and nothing
underneath it. A watercourse recorded outdoors has body in the low mids and less
hiss on top.

**And what survives a phone**, which is where these are actually heard.
Fourth-order high-pass at 500 Hz, where a phone speaker gives up:

| bed | RMS | LUFS |
| --- | --- | --- |
| `flow_soft` | -0.6 dB | -0.3 |
| `flow_brook` | -1.3 | -0.8 |
| `flow_stones` | -1.9 | -1.0 |
| `flow_river` | -2.0 | -1.4 |
| `flow_shore` | **-8.5** | **-6.8** |

RMS ungated over the whole 8 s; LUFS is `ebur128`'s integrated figure, which is
EBU-gated. On a bed with a swell the gate matters.

Two meters because they disagree: LUFS is K-weighted and discounts the bottom
octaves, so `flow_stream` reads -1.0 by LUFS and -5.5 by RMS. `flow_shore` loses
6.8 to 8.5 dB either way - it is surf, and half of it lives between 80 and 300 Hz.
It is the one to pick on a phone rather than on a desktop.

**Not every warm-looking file is water.** Two candidates measured 90% and 97%
below 80 Hz in their sources, which reads as body until you high-pass at 70 Hz:
one lost 8.6 dB and the other 11.7, and what was left underneath was another thin
trickle. That was wind and handling noise, not a river. Both were dropped.
`flow_river` and `flow_shore` carry a 60 Hz high-pass for the same reason.

## And the fifth, which is the one in use

`flow_soft_warm_8s.m4a` - the original `flow_soft` with a -10 dB shelf from 2 kHz.
Asked for on 8 September: damp the one already there rather than swap it. 2-8 kHz
falls from 27.2% to 8.2%, above 8 kHz from 9.1% to 1.8%, centroid from 2838 Hz to
1403. A second shelf followed on the same evening - `flow_soft_warmer_8s.m4a`, the
same cut at -14 dB - because the first was right in kind and not quite far
enough. 2-8 kHz runs 27.2% -> 8.1% -> 4.8% across the three, the centroid 2838 ->
1404 -> 1157 Hz. `render.sh` defaults to the second, with `BED_GAIN` down from
1.0 to 0.8.

**The second shelf needed no compensation, which is the finding below arriving in
reverse.** The first shelf raised the water 0.95 dB K-weighted; the second raised
it 0.05, because the band the meter emphasises was already gone. So the tone
changed and the level did not: -19.0 LUFS of water before, -18.9 after, same clip,
same gain, only the bed swapped.

**Those are two changes and they pull opposite ways.** Measured separately on the
water-only window at the head of a finished clip, 0-0.90 s, ungated:

| | RMS | K-weighted |
| --- | --- | --- |
| the shelf alone, both beds at gain 1.0 | **+1.97 dB** | **+0.95** |
| the gain alone, 1.0 to 0.8, warm bed both sides | -1.88 | -1.89 |
| net, which is what ships | +0.09 | **-0.94** |

Damping a bed and re-normalising it makes it *louder*: `loudnorm` targets a
K-weighted figure, K-weighting carries a +4 dB shelf above 1.5 kHz, so cutting
10 dB off the top means the file must come up to hold -18 LUFS - and it comes up
about twice as much in raw energy as in perceived energy. The gain reduction is
what actually made the water quieter; the shelf is what stopped it hissing.

Badges and the finale are unmoved to within 0.2 dB, so what changed is the
balance and not the mix. And the three figures for the same pair of beds - +0.20
gated over 8 s, +0.43 ungated over 8 s, +1.00 over the first 0.9 s - are the
reason this file names its span as well as its meter.

## The four

| file | what it is | character |
| --- | --- | --- |
| `flow_river_8s.m4a` | a shallow river over a stony bed | steady, warmest, the least like a tap |
| `flow_brook_8s.m4a` | a rivulet through a meadow, Molln, Austria | lighter and closer, still outdoors |
| `flow_stones_8s.m4a` | a brook over stones, Krumme Steyerling | brighter, more movement in it |
| `flow_shore_8s.m4a` | surf on a shore | swell rather than flow, a different thing entirely |

## Sources, all clear for commercial use

CC0 or public domain only, the same rule the engine's `sfx/LICENCES.md` sets: CC
BY and CC BY-SA candidates were skipped on purpose, and several good recordings
were passed over for that reason alone.

| file | source on Wikimedia Commons | licence |
| --- | --- | --- |
| `flow_river_8s.m4a` | `Shallow small river with stony riverbed.ogg` | Public domain |
| `flow_brook_8s.m4a` | `2024-07-26 Molln (Oberösterreich) Rinnsal plätschert bei der Wiese im Wasserschutzgebiet Bräugrabenstraße.wav` | CC0 |
| `flow_stones_8s.m4a` | `2024-07-26 Molln (Oberösterreich) Bachlauf plätschert (Krumme Steyerling bei Piesslingerstraße).wav` | CC0 |
| `flow_shore_8s.m4a` | `Waves.ogg` | Public domain |

## How they were cut

Eight seconds, the length of a clip, so nothing loops. The eight were not taken
from the start: each recording was scanned in half-second hops for the window
whose loudness sits closest to the file's median, with the least variation inside
it and no peak far above it - a gust, a footstep or a clunk shows up as one of
those three. `flow_shore` was scored the opposite way, for one full swell rather
than a flat stretch, because surf that does not move is just noise.

Then `loudnorm=I=-18:TP=-1.5:LRA=11` and 150 ms fades at both ends, matching the
engine's beds. **`flow_shore` needed two passes**: single-pass loudnorm undershot
by 2.7 dB on something that dynamic, so its measured values were fed back in.
All four land at -18.0 to -18.1 LUFS, and every one peaks lower in the finished
mix than the current bed does (-2.1 to -2.6 dBFS against -1.5).

## Using one

`render.sh` takes the bed from `$BED`, so nothing needs editing to try one:

```
BED=../../engine/sfx/flow_river_8s.m4a ./render.sh <topic> <topic>_labelled.png 'auto:...'
```

`preview_bed_<name>.mp4` in this folder is each one under a finished clip, mixed
through the same chain `render.sh` uses, duck included. They are working files:
they do not go to `OUTPUT/`.

**They are on the shelf, not in here.** All four went into `engine/sfx/` on
8 September on the user's instruction, with their source recordings and their
entries in `sfx/LICENCES.md`, which is the fuller record - this file is the
reasoning behind the choice. A bed is not Micro's own the way `micro_overlay.py`
is: every variant pours water, so a bed belongs where all of them can reach it.

Nothing points at them yet. `render.sh` still defaults to `flow_soft_8s.m4a`, so
no clip anywhere changed when they landed - Micro's last cut re-renders to a
byte-identical audio track. Changing that default is a one-line edit to this
variant's own `render.sh`, and it waits until one of them is picked.
