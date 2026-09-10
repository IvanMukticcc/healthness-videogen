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
