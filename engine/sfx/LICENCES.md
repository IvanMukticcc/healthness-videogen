# Water SFX

Both from Wikimedia Commons and both CC0, so no attribution is required and they
are clear for commercial use. CC BY and CC BY-SA candidates were skipped on
purpose: share-alike terms do not sit well with a commercial feed.

| file | source | licence |
| --- | --- | --- |
| `water_trickle.wav` | 363120 fractalstudios water-trickle | CC0 |
| `stream_close.wav` | 433589 jackthemurray stream-river-water-up-close | CC0 |

## Ready to use

| file | cut from | character |
| --- | --- | --- |
| `flow_soft_8s.m4a` | `water_trickle.wav` | soft trickle, the quieter of the two |
| `flow_stream_8s.m4a` | `stream_close.wav` | a stream up close, wider and airier |

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
