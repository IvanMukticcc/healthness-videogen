# Healthness Shorts

Vertical clips where a food pours into the organ it feeds. Three variants of the
same idea, one engine underneath them.

## The two folders that matter

Every variant has the same three, and only two of them are yours:

    INPUT/     the poster the image generator hands back. Drop it here
    OUTPUT/    the finished clip, in a folder for the day. Take it from here
    work/      everything else

The prompt is not a file. It is written in the terminal for the topic at hand,
because it changes with every poster and a saved copy of it goes stale in an
afternoon - which is exactly what happened on 7 September, when a poster was
generated from a prompt three revisions old.

## The variants

    Foods/       a food, a wave, the organ it feeds. The original
    Micro/       the same, with the vitamins and minerals popping onto the rows
    Exercise/    a lift, a wave, the muscles it works, lighting on a body

## The engine

    engine/      five tools, three authored wave assets, and the sound shelf

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
