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
  --rows '<dark>,<light>' \
  --waves '<c1>,<c2>,<c3>,<c4>,<c5>' \
  --vibrance 1.05 --contrast 1.04 \
  --title '<THE TITLE>' \
  -o ../INPUT/base_<topic>.png --work .
```

The wave colours are the foods', top to bottom.

**`--rows` IS A DECISION PER TOPIC, NOT A DEFAULT.** This line used to read
`--rows '#12262B,#EDF0EE'` with the colours written in, and sixteen topics in a
row used that pair because it was sitting there looking like part of the command.
The user asked twice why every Macro clip had the same background; Micro varies
per topic and it is most of why its clips read as different videos rather than
one video with the food swapped. A topic chooses its rows the way it chooses its
waves — from what it is — and `<dark>,<light>` is written as a hole here so it
cannot be used without choosing.

The constraint is one thing only: **the dark row stays dark**, because the title
is white on it. Everything else is taste. That same constraint is why a Macro
palette cannot fail `glass.ghost(base, 72, 130)` — the band act two draws its
heading in sits above act one's title on flat row colour, so a dark row keeps the
heading off live colour automatically. Measured across the riskiest candidates:
band 5.1-6.7 against ordinary 29.6-76.6, all passing.

A palette per topic, adjust on taste:

| | dark | light | |
| --- | --- | --- | --- |
| breakfast | `#2E1F0E` | `#F6F0E2` | oat and honey |
| curry | `#35200A` | `#F7EFDC` | turmeric |
| dinner | `#14203A` | `#EFEFE8` | night blue |
| fishsupper | `#102A33` | `#E9F1F2` | sea slate |
| lunch | `#1E2A14` | `#F1F2E6` | olive |
| lunchbox | `#33261A` | `#F4EEE2` | kraft |
| mezze | `#3A1E14` | `#F7EEE4` | terracotta |
| omelette | `#2A2210` | `#F8F2E0` | butter |
| pasta | `#2E120F` | `#F5EFE6` | tomato |
| roast | `#241A14` | `#F3EDE2` | charred — the first one shipped |
| ryeplate | `#2A241A` | `#F3EFE4` | rye |
| salad | `#16281C` | `#EEF3E9` | leaf |
| sandwich | `#2D2317` | `#F6F0E4` | sourdough |
| smoothie | `#2A1030` | `#F5EDF2` | berry |
| snack | `#241A10` | `#F4EDE0` | cocoa |
| stirfry | `#1E1A10` | `#F2EFE2` | soy |
| tunabowl | `#122630` | `#EDF2F0` | ocean |

`breakfast` was made with waves
`#F2EFE6,#4C3F8F,#D9A02B,#C8A46A,#B8763F` and the title
`WHAT IS IN YOUR BREAKFAST`, on the old shared pair — as were the fifteen after
it. Only `roast` shipped with its own.

**Re-basing an existing topic costs a generation.** The row colours are in the
poster's pixels, so changing them means a new base AND a new poster from the
generator — it is not a re-render. Sixteen topics is sixteen handovers of the
user's time, and that number goes to them before the queue starts, not after.

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

**The caption cannot disagree with the database, and nothing stops it disagreeing
with the BOWL.** `foods.py --labels` guarantees the word and the numbers come from
the same row of `foods.json`, which is the failure it was built for. It knows
nothing about which bowl is in which row of the poster.

That order is decided twice, in two places, by hand: once when the base is built
(`--waves`, top to bottom) and written into the prompt as Row 1 to Row 5, and
again when the label string is typed. On `sushi` those two disagreed - the base
and the prompt had sesame on row 4 and cucumber on row 5, the label string had
them the other way round - and the clip rendered with a bowl of sesame seeds
captioned CUCUMBER WITH PEEL. Every check passed: waves 0.0px, bars 0.00%,
captions sourced, totals correct. Nothing in the pipeline compares a caption to
the picture above it.

**So the five foods are ONE ordered list, written once and used for all three
things** - the `--waves` order, the prompt's Row 1..5, and the `--labels` string.
Not retyped per step. If it is ever retyped, read it back against the poster
before rendering, because the render will not.


**The goal is a person, and the footer naming them is load-bearing.**
`dailygoal.py` computes the day's goal the way the app does - Mifflin-St Jeor for
adults, Schofield under 18, times the activity factor, times the fitness-goal
factor - and the macro goals from `User.dailyCarbsGoal` and its siblings. It
replaced the EU reference intake, which was defensible for a reason that has now
gone: 2000 kcal is a printed labelling constant belonging to nobody, so "40% of a
day" was a fact about a packet. A goal from 172 cm and 66 kg is a statement about
a person, and the line naming who it was computed for is the only thing between
that and an implied recommendation. **It does not get shortened for space.**

`./dailygoal.py --verify` checks the constants against `BodyEnergy.swift` and
`OnboardingState.swift` rather than trusting the transcription.

**Two places the arithmetic will not close, and they are not the same place.**

  1. *The food data.* Atwater 4/4/9 against the app's own calorie field, per
     clip - breakfast +2.8%, lunch -0.1%. The database disagreeing with itself
     by rounding and by each food's source. `foods.py --meal` prints it.
  2. *The goal.* `dailyProteinGoal` is **grams per kilogram of bodyweight** and
     never touches the calorie goal, so the three macro goals do not sum to the
     calorie goal by construction - about 93% at a typical profile. Nothing to do
     with Atwater or with food data.

Same symptom, different causes. A clip that quietly reconciled either one would
be advertising an app that disagrees with it.

**Act one is shown to its last movement, not to its length.** It is still
rendered at eight seconds - the loop, the wave speed and the backdrop all depend
on that - but the clip cuts `BEAT` after the last thing that moves. The trim
point comes from the engine's own printed surge window (`surge +30% over 5 rows,
5.67-6.21s`), not re-derived here.

Measured on the 10.09 clip before the change: outside the ribbon the step is
0.0006-0.008 from 6.29s to 7.96s, and inside it the finale surge peaks at 6.67
and is back to the flow baseline by 6.92. So the clip held a finished poster for
**1.08 seconds** before the turn began. With the tightened rhythm as well, act one
now runs 6.33s instead of 8.0 and the whole clip is 14.42s instead of 16.08.

**The rhythm starts at 0.5s.** `MACRO_TIMES` is `0.5,1.6,2.7,3.8,4.9` - 1.1
apart, which is Micro's spacing and the one with the most clips behind it. The
first second used to be five bare rings and a poster, which is the only second a
vertical feed reliably gets.

**The backdrop bounces instead of running out.** Trimming what is shown does not
shorten what is rendered, so frames past the cut are still available - but act
two is longer than what remains, so the walk ping-pongs between `--behind-lo`
(the finale frame) and the last frame. Every frame from the finale on carries all
fifteen badges, so bouncing there cannot reproduce the content blink. A bounce
reverses the liquid's direction, which on an un-blurred surface would be the most
visible artefact in animation; here it is the same 0.011 mean per step that makes
the backdrop nearly free. `render.sh` prints the window and the reversal count,
and warns under 24 frames.

**The limiter engages here, and it had never had to anywhere else.** Micro's
`render.sh` says its mix "peaks 0.15 dB under the 0.82 ceiling" and "the limiter
is still not engaged" - true, and it means the ceiling has never been tested.
With this rhythm the mix hits it: 36 samples over 0.82 before limiting. The
limiter holds exactly - verified by writing the same graph to `pcm_f32le` with
and without it, 1.0787 against 0.8200 - so the ceiling works, and now somebody
has checked.

**Measure audio in its native channel layout.** The ceiling was briefly dropped
to 0.74 here to buy headroom against an AAC overshoot that turned out not to
exist. `ffmpeg -map 0:a -f f32le -ac 1` on these clips reports a peak 2.0 dB
higher than the same bytes decoded natively - the mix is mono sources fanned out
to stereo, so the two channels are identical, and rematrixing a fully correlated
pair raises it. On the shipped clip: 0.7323 and -23.6 dB native, 0.9212 and
-20.8 dB through `-ac 1`. Every audio number in this folder is a native-layout
number. These clips are also 96 kHz, so a `-ar 48000` in a measurement is a
resample nobody asked for.

**The ring pane fades in.** It used to appear on one frame, which measured 20.8
mean - the largest step in act two after the card landing, and the same order as
the backdrop blink that was treated as a bug. The list pane is there from the
start and the chips fade, so it was the only element arriving by cut. 6.3 now,
spread over two frames.

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
is the only thing telling you what is behind the glass. `SAT` 1.75 keeps the
badges reading blue, green and red through the pane. It was set against `FROST`
0.62 and holds at 0.34, where more of act one comes through rather than less -
the paragraph below is what that extra light cost.

**A value on glass is a value against a moving ground, and the track was not.**
`FROST` 0.34 let act one through and took the calorie ring's empty track with it.
`TRACK` was `(120, 120, 128, 42)` - 42 of 255, so 84% of what read as a grey
track was the pale pane behind it rather than the track. Thin the pane and the
ground under the ring runs 111 to 238 as the rows pass behind it, and the track
goes with it: measured on breakfast's held frame, the darkest track fell to 112.7
against a value arc of 111.3. A separation of 1.3 levels where it had been 51.7,
with only hue left to say which part of the ring was full.

Raising the alpha is the obvious fix and it does not work. `(120, 120, 128)` at
255 lands at 122.7, still 11.4 from the arc, because the track colour is itself
nearly as dark as the green. It is `(228, 228, 236, 120)` now: measured darkest
167.0, separation 55.7, and 66.7 levels of spread around the circumference, so it
still moves with the wave instead of sitting on the glass as a painted band. The
same constant is the macro bars' track and they had the same fault - the red fill
ran into a dark grey track at the bottom of the card.

The general form, because it will happen again: **anything drawn at low alpha
over the glass is not a colour, it is a tint on whatever act one is doing.** It
is safe only while the ground stays still. Every time `FROST` moves, every low
alpha in `meal.py` has to be re-measured against the arc or the fill it is meant
to be distinguishable from.

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
