# Healthness Shorts

Vertical clips where something pours across a row into what it changes. Four
variants of the same idea, one engine underneath them.

## The two folders that matter

Every variant has the same three, and only two of them are yours:

    INPUT/     the base image for the topic, and nothing else. Take it from here
               and attach it to the prompt
    OUTPUT/    the finished clip, in a folder for the day. Take it from here too
    work/      everything else, including the poster that comes back

`INPUT/` holds `base_<topic>.png` and no other kind of file. Its clean copy and
its layout are working files that only the tools read, so `recolor_base.py
--work` leaves them in `work/` however the base is addressed. A folder with one
kind of thing in it needs no reading.

The prompt is not a file. It is written in the terminal for the topic at hand,
because it changes with every poster and a saved copy of it goes stale in an
afternoon - which is exactly what happened on 7 September, when a poster was
generated from a prompt three revisions old.

## The variants

    Foods/       a food, a wave, the organ it feeds. The original
    Micro/       the same, with the vitamins and minerals popping onto the rows
    Exercise/    a lift, a wave, the muscles it works, lighting on a body
    Biohacks/    a free habit, a wave, and a dial counting to what it moves

`Biohacks/` is the one that needs no generator: it draws both circles itself, so
a topic is a palette, a title and five rows of a table, and the clip comes out of
one command. The other three still take a poster back from an image model.

## The engine

    engine/      six tools, three authored wave assets, and the sound shelf

`engine/README.md` is the one to read before changing anything in there. The
short version: **a variant never keeps a copy of an engine file.** It calls
`../../engine/<tool>.py` from its `work/`, and keeps only what is its own - its
overlay module, its data, its palettes, its output.

    ./engine-status.sh

reports whether that is still true. It only reads.

## Where the reasoning is written down

Each variant's `work/flow.md` carries its loop and, under **what is already known
to break**, every mistake that cost an hour - the flat bowls, the captions at ten
different sizes, the liquid cut where it met the organ, the wave that climbed to
the right. None of them are obvious and all of them came back twice before being
written down.

`archive/` holds the checkpoints from before this was a git repository. Two of
them predate the levelling of the wave's tips and their bases only animate with
their own masks, which is why they are kept rather than deleted.
