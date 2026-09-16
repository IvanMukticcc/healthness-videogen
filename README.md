# Healthness Shorts

Vertical clips where something pours along a wave into what it changes. Seven
variants of the same idea, one engine underneath them.

> **Arriving from outside the project?** The clips are not the interesting part.
> This is a repository worked on by several agents at once — one at the root
> holding the engine, one inside each variant — and what is written down here is
> how they are kept from standing on each other.
>
> Three files carry that, and they are the ones to read:
>
> | | |
> |---|---|
> | [`CLAUDE.md`](CLAUDE.md) | the rules binding every agent. A variant never copies an engine tool; a variant needing what the engine lacks **says so and stops**; shipped is shipped. Each rule carries the date and the incident that produced it. |
> | [`MAINTAINER.md`](MAINTAINER.md) | the root agent's job, and the part worth reading first — **"Verify before you believe."** Every variant report so far has been right about the cause and wrong about the number. Three shapes of that failure, with the measurements that caught each one. |
> | [`engine-status.sh`](engine-status.sh) | drift detection. Per file, per variant: *calls the engine · same · stale · diverged*, and it dates a stale copy to the commit it came from. It discovers variants rather than listing them, after a hardcoded list quietly skipped the fifth one. |
>
> The engine is 14 Python tools in [`engine/`](engine). Everything else here is
> artwork, audio and output.

## The two folders that matter

Every variant has the same two:

    INPUT/     the base image for the topic, and nothing else. Take it from here
               and attach it to the prompt
    work/      everything else, including the poster that comes back

The finished clip does not come out of the variant any more. It goes to
`OUTPUT/<CATEGORY>/` at the root of this repository, flat and dateless, and
`OUTPUT/DONE/<CATEGORY>/` is where the user files it once it has been published.
A variant's own `OUTPUT/` folder, where one still exists, is history.

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
    Organs/      the same, with the vitamins and minerals popping onto the rows
    Vitamins/    the headline vitamin in the right circle instead of the organ,
                 and the poster turns over into a second act with the score on it
    Exercise/    a lift, a wave, the muscles it works, lighting on a body
    Macro/       a meal, and what it adds up to on the back of the card
    Biohacks/    five habits, a day bar, chips and dials
    Longevity/   five rows are one fast, not five topics

`Organs/` and `Vitamins/` were one folder called `Micro/` until 16 September
2026. They are the same clip with two differences: what is in the right circle,
and whether the poster turns over.

## The engine

    engine/      eight tools, three authored wave assets, the sound shelf, and
                 micro/ - the badge balls and nutrients.json, read by both halves
                 of the micro series

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
