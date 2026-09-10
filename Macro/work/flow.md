# Macro — the loop

Six steps, and only two of them are yours to think about.

| | |
| --- | --- |
| `../../engine/recolor_base.py` | a new palette, same geometry |
| `../../engine/check_base.py` | did the generator leave the waves alone? |
| `../../engine/add_labels.py` | the captions, into the bars the base reserved |
| `../../engine/clip.py` | `prompt` hands the prompt over, `image` copies the base |
| `foods.py` | the app's database: look up, refuse, build a meal, write the labels |
| `macro_overlay.py` | act one's badges and the calorie ring. Imported by `flowanim.py` |
| `meal.py` | act two, drawn in the app's face |
| `flip.py` | the turn between them |
| `macro_audio.py` | pops, ticks, the sweep and the bell |
| `render.sh` | all of it, in one command |

**The engine's tools are called by path and never copied in here**
(`../../CLAUDE.md` rule 1). `ribbon_mask.png` and `base_layer.png` resolve beside
the script that uses them, so they need no flag.

## 1. The base

Derived, so it is not in git — the command is, and this is it:

```
../.venv/bin/python ../../engine/recolor_base.py \
  --rows '#12262B,#EDF0EE' \
  --waves '<c1>,<c2>,<c3>,<c4>,<c5>' \
  --vibrance 1.05 --contrast 1.04 \
  --title '<THE TITLE>' \
  -o ../INPUT/base_<topic>.png --work .
```

`breakfast` was made with waves
`#F2EFE6,#4C3F8F,#D9A02B,#C8A46A,#B8763F` and the title
`WHAT IS IN YOUR BREAKFAST`. The wave colours are the foods', top to bottom.

## 2. The prompt

`ImageSwap.txt` is the template. Fill the five rows, write it out whole in the
terminal, hand it over with `../../engine/clip.py prompt`. Never paste a saved
copy forward (`../../CLAUDE.md` rule 8).

The user attaches `../INPUT/base_<topic>.png`; `clip.py image <topic>` puts it
on the clipboard.

## 3. Back from the generator

```
../.venv/bin/python ../../engine/check_base.py <topic>_poster.png \
    --base ../INPUT/base_<topic>.png
../.venv/bin/python foods.py --labels '<the five foods>'
../.venv/bin/python ../../engine/add_labels.py <topic>_poster.png \
    -l base_<topic>_layout.json -o <topic>_labelled.png --labels '<that output>'
```

Keep `<topic>_poster.jpeg` beside the working files. It is the one artefact no
command can remake (`../../CLAUDE.md` rule 9).

## 4. The clip

```
./render.sh <topic> <topic>_labelled.png \
    'Greek yogurt,Blueberries,Honey,Oats,Almonds' \
    '200 Greek yogurt,80 Blueberries,20 Honey,60 Oats,15 Almonds'
```

`WIDTH=540` while tuning. Everything after the fourth argument goes to
`flowanim.py` untouched.

## What is already known to break

**Act two is glass, and the glass is free because act one loops.** The second
act is not a screen that replaces the poster - it is a pane laid over it, and
the liquid keeps moving underneath. `flowanim.py` guarantees the surface travels
a whole number of ribbon lengths, so act one's frame N is act one's frame 0:
continuing it behind act two costs one decode and no second render. Act two's
first frame sits over act one's frame `act1_frames + flip_frames`, and the wave
carries on as though it had never stopped.

**It is clamped at the last frame, never wrapped, and the distinction is the
whole of it: act one loops in LIQUID, not in content.** The surface travels the
ribbon exactly once, so the wave joins seamlessly - but the badges accumulate
across the eight seconds and never reset, so frame 0 has five bare rings where
frame 191 has fifteen badges, five filled arcs and the finale. Frame 0 against
frame 191 is mean 14.27 with 14.19% of the frame different. A modulo therefore
put frame 0 under act two's second-to-last frame and every coloured bloom behind
the frost blinked out at 15.96s of a 16 second clip: 5.30% of the frame over 20
levels, against neighbouring steps of 0.004 to 0.012. Two hundred times the
normal step, on the held ending, where nothing else moves at all. Holding the
last frame costs a two-frame freeze of a backdrop already moving 0.011 mean per
step under heavy blur - invisible, where the blink was the only thing visible.

**The frost and the wordmark band have a floor, and it is the mark.** `FROST`
0.34 and `FOOT_A` 0.55. Below about 0.30 the panes lose the ground they need and
the secondary text starts competing with the wave behind it; below about 0.45 on
the band the wordmark goes grey. Measured at the shipped values rather than
judged: the mark reads 195 against a ground of 62, a separation of 133.

The backdrop is decoded at 270 wide and blown back up. It is about to be blurred
past any detail that width could have carried, and 192 frames of 1080x1920 in
memory is 1.2 GB against 74 MB at 270.

Blur, THEN pull towards white, THEN put the saturation back - in that order.
Whitening a blurred frame washes the liquid out to a grey ghost, and the colour
is the only thing telling you what is behind the glass. `FROST` 0.62 and `SAT`
1.75 keep the badges reading blue, green and red through the pane while act one's
title, white on dark, dissolves completely.

**A pane needs a lit edge or it is a stain.** At 168 alpha over a frosted poster
a card has almost the same value as the frost around it, and without a hairline
of brighter white it has no boundary - the list looks like text floating on a
smear. One pixel is the whole difference.

**Fading on glass is an alpha fade, not a fade towards the background colour.**
Text arriving on an opaque card can interpolate towards `BG`. There is no `BG`
here: the poster is moving behind it. Interpolating towards a colour that is not
there tints the text as it arrives.

**The wave has to end in something, from the first frame.** Foods and Micro put
an organ in the right circle and the generator draws it, so the liquid's tapered
tip is behind a solid object from frame zero and is never once seen ending. This
folder took that circle for itself and then only started drawing in it at the
row's cue - five naked tips tapering into flat colour for the first second, and
a labelled poster that looks unfinished because a still has no cue to wait for.
The plate and the empty track are furniture now and arrive with the poster; only
the coloured arcs and the number pop. An empty ring is not a placeholder, it is
a ring at zero, which is what the app draws before you have eaten anything.

The plate is **opaque**, not 92%: at 235 alpha the tip was hidden and its shadow
was not, which is the same fault one step quieter. And it is deliberately
smaller than the guide mark it sits on - the mark is removed by
`flowanim.py --anchored`, not covered. Verified on the worst case, the generator
handing the base back untouched: 420562 px of guide circle painted out, and the
outer band of the mark clear of the wave comes back within 3 levels of flat row
colour.

**An overlay must draw INTO the frame it is given.** `flowanim.py` calls
`m.draw(out, pl, t)` and throws the return value away — the array it hands in is
the array it writes to ffmpeg. A `draw` that builds a new frame and returns it
is correct in every other respect and fails in total silence: the render
succeeds, the cue file is written, the timings are right, and no badge appears.
Five renders came out that way before anyone looked at a frame instead of at the
exit code.

**`amix duration=first` with `-shortest` measures the water bed.** The bed is an
8 second file and act one is 8 seconds, so `first` means "eight seconds",
`-shortest` then trims the *video* to it, and a sixteen second clip is written
eight seconds long with nothing on stderr. It reads exactly like the concat
having failed. It is `duration=longest` and `apad`.

**Act two is authored at 1080×1920 and resized, not scaled.** Every constant in
`meal.render` — padding, row height, font size, ring radius — is a pixel count at
that size. A preview at 540 drew 1080-sized text on a 540-wide card and every
food name ran through its own calorie figure. Thirty constants to scale is one
constant to forget.

**An apostrophe in a `${VAR:-default}` is not worth the quoting.** `TODAY'S BOWL`
inside a bash default expansion came out as `TODAY\'S BOWL` on screen, and the
obvious fix (`'"'"'`) ends the parameter expansion and breaks the script. It is
its own variable now.

**The right circle has to be left alone by name, and told why.** A generator told
only to leave a region alone treats it as a region it has no instruction about,
and decorates it. `ImageSwap.txt` says what will happen to the work — it will be
covered and wasted — and that is the sentence that makes it stick.
