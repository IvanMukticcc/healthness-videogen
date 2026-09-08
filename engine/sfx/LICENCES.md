# Water SFX

All from Wikimedia Commons, and all either CC0 or public domain, so no
attribution is required and they are clear for commercial use. CC BY and CC BY-SA
candidates were skipped on purpose - several good recordings among them - because
share-alike terms do not sit well with a commercial feed.

`lift_bed_8s.m4a` is in neither table: it is synthesised by
`Exercise/work/muscle_audio.py --bed`, nothing was downloaded to make it, and it
has no licence to record. This file covers the recordings only.

| file | source | licence |
| --- | --- | --- |
| `water_trickle.wav` | 363120 fractalstudios water-trickle | CC0 |
| `stream_close.wav` | 433589 jackthemurray stream-river-water-up-close | CC0 |
| `river_stony.ogg` | `Shallow small river with stony riverbed.ogg` | Public domain |
| `brook_meadow.wav` | `2024-07-26 Molln (Oberösterreich) Rinnsal plätschert bei der Wiese im Wasserschutzgebiet Bräugrabenstraße.wav` | CC0 |
| `brook_stones.wav` | `2024-07-26 Molln (Oberösterreich) Bachlauf plätschert (Krumme Steyerling bei Piesslingerstraße).wav` | CC0 |
| `shore_waves.ogg` | `Waves.ogg` | Public domain |

## Ready to use

| file | cut from | character |
| --- | --- | --- |
| `flow_soft_8s.m4a` | `water_trickle.wav` | soft trickle, the quieter of the two |
| `flow_stream_8s.m4a` | `stream_close.wav` | a stream up close, wider and airier |
| `flow_river_8s.m4a` | `river_stony.ogg` | a shallow river over stones: steady, and the warmest here |
| `flow_brook_8s.m4a` | `brook_meadow.wav` | a rivulet through a meadow, lighter and closer |
| `flow_stones_8s.m4a` | `brook_stones.wav` | a brook over stones, brighter, more movement |
| `flow_shore_8s.m4a` | `shore_waves.ogg` | surf on a shore: swell rather than flow |
| `flow_soft_warm_8s.m4a` | `flow_soft_8s.m4a` | the same trickle with its top taken off |
| `flow_soft_warmer_8s.m4a` | `flow_soft_8s.m4a` | and once more, asked for after a clip shipped on the first |

The last five were added on 8 September, on the user's instruction, after
`flow_soft_8s.m4a` was rejected for sounding like a tap running indoors rather
than water outdoors. That is measurable and it is why these and not others.

**Basis: the finished 8 s beds, not their source recordings; the whole 8.0 s,
mono sum, Welch average of 8192-sample Hann frames at 50% overlap, share of total
energy; the top band stops at 8 kHz and there is a separate column above it, so
"above 2 kHz" here is two columns and not one.** The first version of this table
gave figures taken from the source recordings - and from only their first 40
seconds - while naming the beds in its rows. The beds are a chosen window with a
high-pass on two of them, so they were never the same measurement.

| bed | centroid | <80 Hz | 80-300 | 300 Hz-2 kHz | 2-8 kHz | >8 kHz |
| --- | --- | --- | --- | --- | --- | --- |
| `flow_soft_8s` | 2838 Hz | 5.0% | 0.5% | 58.1% | **27.2%** | 9.1% |
| `flow_stream_8s` | 612 Hz | 64.1% | 4.6% | 21.6% | 8.9% | 0.7% |
| `flow_river_8s` | **1193 Hz** | 1.1% | 8.6% | 74.3% | 15.7% | 0.3% |
| `flow_brook_8s` | 1826 Hz | 1.3% | 3.2% | 75.7% | 16.3% | 3.6% |
| `flow_stones_8s` | 1931 Hz | 4.9% | 4.2% | 65.5% | 19.8% | 5.6% |
| `flow_shore_8s` | **388 Hz** | 17.3% | 46.3% | 33.9% | 2.4% | 0.1% |
| `flow_soft_warm_8s` | 1404 Hz | 10.4% | 1.1% | 78.5% | 8.1% | 1.8% |
| `flow_soft_warmer_8s` | 1156 Hz | 12.5% | 1.3% | 80.5% | 4.8% | 0.9% |

A tap in a sink is close, narrow and bright - a lot above 2 kHz and nothing
underneath. `flow_soft` puts 27.2% of its energy in 2-8 kHz and another 9.1%
above that. Water recorded outdoors has body in the low mids and less hiss on top.

**A warm-looking measurement is not always water.** Two other candidates read 90%
and 97% below 80 Hz in their sources, which looks like body until you high-pass
at 70 Hz: one lost 8.6 dB and the other 11.7, and underneath was another thin
trickle. That was wind and handling noise, and both were dropped. `flow_river`
and `flow_shore` carry a 60 Hz high-pass for the same reason.

`flow_soft_warm_8s.m4a` and `flow_soft_warmer_8s.m4a` are not recordings of
their own: both are `flow_soft_8s.m4a` with a high shelf from 2 kHz, -10 dB and
-14 dB, made when the user asked for the bed in use to be damped rather than
replaced, and then damped once more. Across the three, 2-8 kHz runs 27.2% -> 8.1%
-> 4.8% and the centroid 2838 -> 1404 -> 1157 Hz. Micro renders with the second;
no other variant uses either. The first stays because `superfoods14` shipped on
it, and a shipped clip's bed is not a file to overwrite.

**The second shelf needed no gain compensation and the first did.** Cutting the
top and re-normalising raises a bed - see the entry in `engine/README.md` - but
the first shelf raised the water 0.95 dB K-weighted and the second only 0.05,
because the band K-weighting emphasises had already been taken out. So the water
sits where it did: -19.0 LUFS before and -18.9 after, in the same finished clip
with only the bed swapped.

## What survives a phone

A phone speaker gives up somewhere around 500 Hz, so a bed's low end is a promise
it cannot keep in a feed. Fourth-order high-pass at 500 Hz, the loss measured two
ways because the two disagree and the disagreement is the point:

| bed | RMS | LUFS |
| --- | --- | --- |
| `flow_soft_8s` | -0.6 dB | -0.3 |
| `flow_soft_warm_8s` | -1.2 | -0.6 |
| `flow_soft_warmer_8s` | -1.4 | -0.7 |
| `flow_brook_8s` | -1.3 | -0.8 |
| `flow_stones_8s` | -1.9 | -1.0 |
| `flow_river_8s` | -2.0 | -1.4 |
| `flow_stream_8s` | **-5.5** | -1.0 |
| `flow_shore_8s` | **-8.5** | **-6.8** |

RMS here is an ungated mean over the whole 8 s; the LUFS column is ffmpeg's
`ebur128` integrated figure, which is EBU-gated and therefore drops the quiet
stretches. On a bed with an authored swell that is a real difference and not
noise, and it is why a second measurement elsewhere read 0.3 to 1.2 dB less loss
on the same files. LUFS is also K-weighted and has already discounted the bottom
octaves, so a bass-heavy bed looks like it survives one that it does not:
`flow_stream` reads -1.0 by LUFS and -5.5 by RMS. Name the meter, the span and
the gating, or the figure means nothing.

`flow_shore` is the one to be careful with either way. It is surf, 46.3% of it
between 80 and 300 Hz, and it loses 6.8 to 8.5 dB on the speaker most people hear
it through - the same trap as the 40-inch tam-tam among the finale candidates,
most impressive in headphones and weakest of the nine on a phone. Three of the
four field recordings survive a phone; that one is chosen on a desktop and
regretted in a feed.

Nothing points at the four field recordings yet - every variant's `render.sh`
still resolves its own bed, and a variant tries one with
`BED=../../engine/sfx/flow_river_8s.m4a ./render.sh ...`.

Eight seconds, the length of the videos, so nothing needs looping. Normalised to
−18 LUFS with a true peak of −1.5 dB, which leaves headroom under a voiceover,
and 150 ms fades at both ends so there is no click.

## Putting one on a video

```
ffmpeg -i OUTPUT/sleep.mp4 -i ASSETS/flow_soft_8s.m4a \
       -shortest -c:v copy -c:a aac -b:a 192k OUTPUT/sleep_sfx.mp4
```

Quieter, to sit under a voiceover:

```
ffmpeg -i OUTPUT/sleep.mp4 -i ASSETS/flow_soft_8s.m4a \
       -filter:a "volume=0.5" -shortest -c:v copy OUTPUT/sleep_sfx.mp4
```

To cut a different eight seconds from a source, change the `-ss` offset:

```
ffmpeg -y -ss 20 -i ASSETS/stream_close.wav -t 8 \
  -af "loudnorm=I=-18:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.15,afade=t=out:st=7.85:d=0.15" \
  -c:a aac -b:a 192k ASSETS/flow_stream_8s.m4a
```
