# Vitamins — the loop

Act one is the poster: five bowls, the liquid running, the headline vitamin
lighting in each right circle, two more badges popping on each row. It stops
without a finale. The poster turns over, and act two says what the five foods
actually carried and what the micro score is.

This folder was split out of `Micro/` on 16 September 2026, so most of what is
known about generating one of these posters was learned there. **Read
`../../Organs/work/flow.md` "What is already known to break" before writing a
prompt** - it is the same base, the same bowls, the same caption bars and the
same wave, and about two thirds of its entries apply here word for word:

    droplets and --drops 0            the captions have a reserved place
    --reach 0                         no text is asked for at all
    speckles that stand still         the title is drawn into the base
    recolouring: gamma, not scaling   telling it where to put things fails
    artwork crowding the edges        the bowl comes out flat unless every row says so
    "a bowl" lets it choose ceramic   the safe area is one fourteenth
    the source wave climbs right      the wave cut where it meets the bowl
    a caption fitted on its own       a badge may not sit on a guide circle
    hue rotation throws contrast away a badge that fades out is a smudge
    ImageDraw replaces, composite     act one's title ghosts into act two's heading

**And about a third of them cannot happen here at all**, which is worth saying
rather than leaving to be discovered: every entry about asking a generator for an
organ is gone. An organ named on its own coming back as an object; naming a joint
and getting the bone; asking for a piece of tissue and getting a slab; two organs
in one circle being impossible; a structure thinner than a finger arriving
correct and unreadable; something magnified arriving with the circle around it.
Six regeneration causes, none of which exist in a prompt that asks for five bowls
and nothing else. ../../CLAUDE.md rule 10 - a body part named by its address
draws everything at that address - has no application in this folder.

## The loop

**1. Author the topic in `topics.json`.** Five foods, their captions, their
servings, and any vitamin the derivation will not get right. Nothing else in this
folder takes a food or a vitamin as an argument, so this is the only place a
topic is decided.

    ./vitamins.py <topic>              read it back as a table before going on

Check the table. `(derived)` means `engine/micro/nutrients.json` chose it - the
first entry of that food's row belonging to the vitamin family; `(authored)`
means you did. A food with no vitamin among its three fails loudly and names the
row, which is the case to write into `topics.json` rather than work around.

**Choose the five foods for their vitamins.** Obvious, and the demo topic is the
counter-example that proves it costs something: it reuses `AGE SLOWER`'s five,
which were chosen for an organ clip, and three of the five rows come out
`VITAMIN C`. Nothing is wrong with the clip; it just says one word three times.

**2. Build the base, then give the user the prompt.**

    ../.venv/bin/python ../../engine/recolor_base.py --work ...      the base
    ./make_prompt.py <topic>                                          the prompt

`make_prompt.py` fills `ImageSwap.txt` as it stands right now. Hand over the body
alone - `--body-only`, piped through `../../engine/clip.py prompt` - because the
header names the captions, and a header pasted into a prompt whose body forbids
text in three places once cost a poster with artwork 33 to 74px into caption bars
78px tall.

**3. The poster comes back.** `grab.py`, then:

    ../.venv/bin/python ../../engine/check_base.py <topic>_poster.jpeg \
        --base ../INPUT/base_<topic>.png

Under about two pixels of wave drift the authored mask still fits. Above that,
regenerate - the animation cannot correct a wave the generator has redrawn.

**Then look at the right-hand circles yourself.** `check_base.py` measures the
wave, not the emptiness, and this variant's one new failure mode is invisible to
it: a generator that put something in the right circle, or spread the bowl
towards it. The ball hides a disc of 1.06r and nothing outside that.

**3b. The captions**, both bars, from the same file everything else comes from:

    ../.venv/bin/python ../../engine/add_labels.py <topic>_poster.jpeg \
        -l base_<topic>_layout.json -o <topic>_labelled.png \
        --labels "$(./vitamins.py <topic> --labels)"

**4. Render.** One command, and it runs `render2.sh` itself:

    ./render.sh <topic>

    ACT1_ONLY=1 ./render.sh <topic>     act one alone, to audition it
    ./render2.sh <topic>                re-cut act two onto an act one already rendered

## What act one is, in numbers

Measured on the `demo` cut, 16 September:

    act one          5.4583 s     last badge 4.74s + settle 0.47 + gap 0.25
    the turn         0.5833 s     14 frames at 24fps, Macro's turn
    act two          5.618  s     micro_card decides it: last change + 1.0s
    the whole clip  11.659  s     278 frames, 1080x1934 throughout

**One resolution, and check it rather than assuming it.** Act one comes out at
the poster's aspect - 1080x1934 from a 1536x2752 base - and act two is rendered
at act one's size read back with ffprobe. A second act at a hardcoded 1080x1920
concatenates with `-c copy` into a file that changes size mid-stream: ffmpeg
decodes it, every frame extracts correctly, every check passes, and QuickTime
holds act two's first frame from the turn to the end.

    ffprobe -v error -select_streams v:0 -show_entries frame=width,height \
        -of default=nw=1:nk=1 clip.mp4 | paste - - | sort | uniq -c

More than one line is the bug. **`-show_entries stream=` cannot see this** - the
stream reports the first segment's dimensions and says nothing about the rest.

## What is already known to break, here

- **The animator does not paint inside a guide circle**, and in this variant the
  right one is empty. 5.0% of the wave lies inside the circles and it is real
  liquid standing still, which is fine under an organ and not fine under nothing.
  The ball is therefore never smaller than the mark: the circle is r 137.5 at
  1536 and `--vitamin-d` defaults to 290 rather than 275, the extra 15px being
  the antialiased rim rather than a margin anybody chose. `vitamin_overlay.build`
  refuses anything under 275 rather than letting it render.

- **An organ spills well past its guide circle**, which matters whenever an
  Organs poster is being turned into a fixture. Measured on `ageing`: 1389 to
  4937 px between r and 1.35r on the five rows, and another 172 to 639 out to 2r.
  A restore of 1.9r left 21 to 416 px on every row, all of it between 1.90r and
  3.00r, and on rows 4 and 5 it reached x=1535 - the right edge of the poster,
  128px outside the circle, where no ball will ever cover it. 3.2r leaves 0 px on
  all five. `make_fixture.py` prints the residue every time for that reason.

- **The two overlays must not read each other's flags.** `vitamin_overlay`
  declares `--vitamin-times` and `micro_overlay` declares `--micro-times`, both
  defaulting to the same five instants, and `render.sh` fills them from one
  variable. It looks like duplication. The alternative is on record: Biohacks let
  one overlay read a flag another declared, and its three overlays stopped being
  runnable separately at all - `AttributeError: 'Namespace' object has no
  attribute 'dial_lead'`, thrown from a module that had declared nothing wrong.

- **`--micro-organ 0` is not an optimisation.** `micro_overlay` finds the right
  circle's artwork by difference from the clean base and lights it. Here there is
  none by construction, so left at 1 it prints "nothing found in the right
  circle" five times and does nothing. Off, it does not look.

- **The headline vitamin leaves the row's badges, and that is a choice.** Two
  badges per row here, ten in the clip, against Organs' three and fifteen. The
  ball on the right has already said that word and popping it again 300px to the
  left is the same word twice in one second. `vitamins.py --keep-all` puts it
  back if the choice is ever revisited.

- **Act one may not carry a finale, and `render2.sh` refuses if it does.** The
  surge glow is baked into act one's picture, so cutting at 5.46s would show the
  beginning of an ending and then cut away from it. `render.sh` passes
  `--finale off` and deletes `<topic>_finale.txt` first, so the file's presence
  afterwards can only mean something rendered it - and the refusal is loud.

- **The cut is measured from the last badge being ON SCREEN, not from its cue.**
  The two are 0.47s apart: a badge cued at 4.74 is still arriving until about
  5.21. Cutting at cue + gap would start the turn while the thing the viewer is
  watching is still moving.

- **`ImageDraw` replaces pixels, it does not composite them.** Act two draws a
  header sheet over the glass pane to hide what is behind it. Drawn white at
  alpha 166 over a pane at 186 it made that band *more* transparent, not less -
  measured on the same patch, the ghost went **14.4 -> 18.9 levels** when the
  sheet meant to kill it was added. Every element with alpha over the pane had
  the same fault and none of them looked obviously wrong: the row bars at 120
  and the ring's own tracks at 46 were cutting windows in the card and showing
  more of the poster through them. Each one now goes through `micro_card.over()`
  - its own transparent layer, then `img.alpha_composite(lay)` - and the sheet
  measures **4.3 levels**, under the frost's own quiet bands. If a translucent
  thing over another translucent thing looks weaker than it should, this is why.
- **Act one's title ghosts into exactly where act two puts its heading.** The
  poster's title sits at y 203-390, which is video y 143-274, and act two's
  header block lands at 196-298. Through a pane passing 27% it was legible:
  a viewer could read BLOOD PRESSURE / FOODS THAT BRING IT DOWN under act two's
  own BLOOD PRESSURE. `engine/glass.title_survival()` measures it - the title
  band's contrast against an ordinary band of the same poster - and every Micro
  palette fails it: pressure 74.3 against 16.8, metabolism 81.1 against 19.6,
  ageing 91.9. Macro passes on navy alone, which greys out and takes its white
  type with it.

  **Two fixes that do not work, both measured before the one that does.** More
  frost is a linear blend, so it scales the title band and the quiet band
  together and the ratio is invariant: 0.34 -> 0.62 takes 74.3 to 42.0 and 16.8
  to 8.6. Cropping the title band out of the backdrop trades one set of words
  for another - the poster's caption bars move up into the same place and
  BEETROOT | NITRATES ghosts instead. What works is giving the header its own
  ground: a sheet at 0.90 compound alpha, which puts any poster's title under 5
  levels regardless of its palette, including the plum that cropping made worse.

- **A frame-difference check has a floor, and act two's closing note lives under
  it.** On a held frame at 270 wide, x264 alone moves 100-280 pixels by 4-5 levels
  every frame; anything quieter is indistinguishable from the encoder, and
  dropping the threshold finds the encoder rather than the picture. The last
  *event* comes from the thing that draws it - `micro_card.py`'s plan - never
  from differencing frames.

## Invariants worth re-checking if something looks off

- `./vitamins.py <topic>` agrees with the captions burnt into the labelled poster
- the right circle in the finished clip is a ball and nothing else is visible
  around it
- `ffprobe ... frame=width,height | uniq -c` prints exactly one line
- `<topic>_finale.txt` does not exist
- the clip ends about a second after the score reaches its final integer
