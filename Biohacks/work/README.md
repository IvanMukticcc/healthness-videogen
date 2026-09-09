# Biohacks — the files, and what each one decides

`flow.md` is the loop. This is what the code is and why it is shaped that way.

## The idea in one row

    [ glyph ]  ~~~~~~  [ 10 MIN ]  ~~~~~~  [ +250% ]
      the hack          what it costs        what it moves
      its own wave's    glass, neutral       counts up, ring closing
      colour                                 colour says which direction

    ────●────────●────────●────────●────────●────    the day, filling

Left to right in the direction the liquid already runs: cause, cost, effect, in
a quarter of a second, five times, and then a bar underneath that says all five
belong to one day.

## The files

| file | what it decides |
| --- | --- |
| `hacks.json` | the vocabulary. Every number on screen, with the study it came from |
| `hacks.py` | how a hack is looked up, what its direction colour is, how its value is split into a countable part and its units |
| `glyphs.py` | a lucide icon at any size in any colour. Rasterised by `rsvg-convert`, cached in `icons/` |
| `dial.py` | the drawn parts: the disc, the rings, the number, and `blend`, the one primitive the three overlays share |
| `scene_overlay.py` | the left circle - where the glyph sits, what colour it takes and when |
| `dial_overlay.py` | the right circle - when the ring sweeps and the number counts. **Owns the finale's timing** |
| `day_overlay.py` | the chip on the liquid and the day bar under the poster - the two elements that are about the viewer rather than about a row |
| `biohack_audio.py` | the bed, the counter's tick train, and the assembly. Imports `engine/impact.py`; does not reproduce it |
| `check.py` | what must be true of the finished clip |
| `check_scene.py` | what must be true of a returned poster, before a render is spent on it |
| `render.sh` | all of it, once, so the picture and the sound cannot drift |
| `ImageSwap.txt` | the prompt template. Filled per topic and handed over whole - never a file the user opens |
| `PROMPTING.md` | what makes one of these prompts work, measured over eight generations |
| `Prompts.txt` | every topic that has shipped: its palette, its captions, its hacks, its scenes |

## Three overlays, and why three

One per **place**: left circle, right circle, everything else. The engine draws
them in the order they are named, and the order is that.

    --overlay scene_overlay,dial_overlay,day_overlay

`--hacks` and `--hack-times` are declared by `scene_overlay` alone and read by
all three. Declared twice, argparse refuses the parser outright - which is the
right failure, because two modules owning one flag is two modules that disagree
about it the first time either changes. They cannot be run separately; `render.sh`
always passes all three.

## What is generated and what is drawn

**The photograph is generated. Everything else is drawn.** A clip comes back from
the same round trip every other variant here makes - build the base, hand the
prompt over, take the image back, caption it, render - and what this variant adds
on top is drawn at render time and never asked for: the chip in the liquid, the
counting dial, the day bar, and the light that crosses the row.

That split is the reason the dial can count. An image model cannot draw the same
ring twice, so it is not asked to; five posters whose dials disagreed about where
a ring starts would be five instruments, and the comparison the clip is about
would not survive it. `PROMPTING.md` has the same argument from the other side -
what the generator is *good* at, and what it will quietly get wrong.

### The plate under the left captions

`engine/caption_glass.py`, between `add_labels.py` and `render.sh`, scene mode
only. `add_labels.py` picks its ink from the layout's light/dark flag - a
guarantee on a flat row, a guess on a photograph - so the left caption's
legibility is decided by whatever the generator happened to put under it. Across
this folder's first six posters the ink-to-background gap ran 83 to 243, and
**both rows under 95 were light rows, both row 4**: the same signature as the
black sled that cost Exercise `SLED PUSH`. The plate takes them to 116 and 120.

The right caption never had the problem - it sits on the dial's own disc, which
is opaque and a known colour - so `--side` stays at its `left` default, and so do
`--min-alpha 0.42` and `--target 95`. They were measured on Exercise's five
bands and they hold on all thirty rows here, which is the point: one tool
carrying two variants' worth of constants is the drift promoting it was meant to
end.

It writes `<topic>_glass_labelled.png` rather than back over `<topic>_labelled.png`,
because it is not idempotent - on a dark row its own rim reads as letters to the
next pass and the plate grows to its own edge, 46px tall to 70, with no error.
Keeping the two files apart makes the caption step re-runnable and preserves the
`(poster, labelled)` pair every caption measurement here is made from.

`check_scene.py --glass` verifies the result, and that is the only honest place
for the verdict: before the plate exists the answer depends on where the letters
land, and nothing knows that until `add_labels.py` has run. The left caption is
no longer a reason to send a poster back.

### The preview, which is not a clip

`./render.sh <topic> 'auto:...'` with no poster draws a lucide glyph in the left
circle instead of a photograph and writes `work/<topic>_preview.mp4`. It will not
write to `OUTPUT/`.

It earns its place: a topic can be seen laid out, timed and sounded in about a
minute, which is where a caption that is too long, two rows sharing a glyph or a
rhythm that runs past the finale all show up - before a generation is spent on
any of it. It was briefly mistaken for the shipping path and three previews
reached `OUTPUT/` on 8 September, which is why the two now go to different
places.

The cost is that a glyph is not a photograph. For the topics where that matters -
where the left circle should be a real sunrise through a real window - the prompt
is in `ImageSwap.txt` and `--scene poster` leaves the circle alone.

## The dial, in the detail that matters

The circle is 275 px across at 1536 and the base fixes it, so every pixel the
ring takes is a pixel off the number. The first version was a fat gauge in the
middle at `r*0.78` and 11.5% width, and it left the number 178 px - 42 px of
type in the finished 1080 video. The shipped ring is at `r*0.94` and 7.5%, which
leaves 236 px and 56 px of type.

The count and the ring are on the same ease, `1-(1-p)^3`, and so are the ticks
under them: `biohack_audio.counter` inverts that ease and lays sixteen clicks at
the times the *value* passes each of sixteen equal steps. Laid evenly they are a
metronome running under a number that is slowing down, and they separate audibly
in the last tenth of a second - which is exactly where the eye is.

`nums` is pre-rendered, one sprite per frame of the count. Twelve frames, five
dials, sixty sprites; rendering the text per frame would be 192 draws a dial for
a result that is twelve distinct pictures.

## The two colour systems, and why they do not fight

**The ring takes its direction's colour** - green when something rises that
should rise, blue when something falls that should fall, amber when a clock
moves. Three states, learned in two rows without being told.

**The glyph takes its own wave's colour**, read out of the picture. The second
cut coloured the glyph by direction too, on the exercise variant's good argument
that a colour arriving at both ends of a row is what joins them. It produced a
green snowflake and a blue coffee cup, and an object always wins an argument with
a colour system. A ring has no opinion about what green means; a snowflake does.

The consequence is that **the wave palette here is unrestricted**. Exercise
fences its waves off from red, amber and orange because its badges are those
colours and a third of every row would be lost under an amber wave. Here the chip
is glass and the dial has its own disc, so nothing on the liquid has a hue to
collide with. `flow.md` proposes using that freedom for time of day: dawn amber,
morning ice, midday lime, afternoon coffee, night violet.

## The day bar

The only element in this repository that is not inside a row. It lives in the
clear strip the base leaves between the last caption and the logo, y 2476-2585 at
1536, and it does three things nothing per-row can:

- **it moves from frame 0.** The first row does not fire until 0.70 s and a feed
  decides in about 1.5, so those seventeen frames are the whole audition
- **its head arrives at each stop exactly as that row fires.** The map from time
  to position is piecewise linear through the cues, so the bar is always pointing
  at what is about to happen rather than recording what just did
- **it fills**, and four fifths of a bar is a reason to stay for the fifth

Stops are evenly spaced with their clocks as labels. True chronological spacing
was tried and thrown out: 06:40 and 07:05 are nine pixels apart in a
seventeen-hour day, and two stops nine pixels apart read as a printing fault. The
clocks carry the chronology exactly, which is all it was ever for.

`NAME@HH:MM` in the spec moves a hack's clock for one topic. The table's clock is
where a hack usually falls in a day, which is the wrong answer the moment a topic
is not a whole day - cyclic sighing is filed at 17:30 and belongs at 07:20 in a
morning protocol.

## The sound

Three layers, and only the middle one is written here.

- **the chip** is `engine/impact.strike` at root 520 rather than the 420 the other
  two share. A glass capsule, not a bowl or a barbell. Imported, not copied
- **the counter** is this folder's: sixteen clicks on the count's own ease and a
  short FM lock at the end, on the same inharmonic 1.41 ratio the engine's chord
  is built from - so the finale is a chord of a sound the ear has been taught
  five times
- **the bed** is a low pad that breathes twice, built in the frequency domain so
  the last sample joins the first. It measures 0.00000 at the join and -18.4
  LUFS, which is where both engine beds are normalised. It lives here, not in
  `engine/sfx/`: a file in a shared folder that only one caller reads is where
  every other copy in this repository started

Measured on the reference cut: -16.7 LUFS integrated, -1.6 dBTP, and the limiter
engages on 9 samples of 384 000. Micro's shipped clips measure -17.6 and -1.2.

## icon-sources/

`lucide-static`, ISC, 2 077 icons, downloaded once. ISC asks for nothing: no
attribution in the artwork, no share-alike, commercial use fine. The tarball is
not kept - the unpacked `package/` is what `glyphs.py` reads, and `icons/` is the
cache, keyed by name, size and colour.

    python3 glyphs.py --sheet          # every icon hacks.json names
    python3 glyphs.py moon sunrise --size 260
