# Healthness Shorts — house rules

**This is not the app repository.** The `CLAUDE.md` two levels up describes
`fitcircle/`, `fitcircle-android/` and the web page: `develop`, `scripts/run.sh`,
`parity.sh`, `push.sh`. None of it applies here. Nothing in this tree builds an
app, and there is no `scripts/` folder.

This is its own git repository — `healthness-videogen`, private, branch `main`.

**Started at the root rather than inside a variant?** Then the engine is yours
and so is deciding what belongs in it: read `MAINTAINER.md` after this. Started
inside `Foods/`, `Micro/`, `Exercise/` or `Biohacks/`? That folder is your whole
remit - see rule 3 - and `MAINTAINER.md` is not addressed to you.

## The shape

    engine/                the six tools, three authored wave assets, sfx/
    Foods/ Micro/ Exercise/ Biohacks/    four variants, three folders each:
        INPUT/             base_<topic>.png, and nothing else
        OUTPUT/            finished clips, a folder per day
        work/              everything else
    archive/               checkpoints from before this was a repository

## The rules that are not negotiable

1. **Never copy an engine file into a variant.** Not `flowanim.py`, not
   `recolor_base.py`, not `ribbon_mask.png`. Call `../../engine/<tool>.py` from
   the variant's `work/`. On 7 September 2026 all three folders held copies and
   they drifted to three different generations in a single morning; a poster was
   generated from a prompt three revisions old before anyone noticed. That is
   what `engine/` exists to prevent. `./engine-status.sh` checks it.

2. **A variant that needs different behaviour writes an overlay, not a fork.**
   `engine/flowanim.py --overlay <module>` calls three functions in a module of
   yours - `add_arguments`, `build`, `draw`. See `engine/README.md`.

3. **Change only your own variant.** If you were started in a variant folder -
   `Foods/`, `Micro/`, `Exercise/`, `Biohacks/`, or whichever exists by the time
   you read this - that folder is the whole of what you may edit. Not the others:
   other people and other agents are in them at the same time. **And not
   `engine/`**, no matter how small or how obviously right the change looks.
   A variant is not the place from which the thing every variant runs gets
   changed.

   When a variant needs something the engine does not do: **say so and stop.**
   Describe what is missing and what you would change. Do not edit `engine/`, do
   not copy a tool into your folder to edit it there, and do not work around it
   with a patch script. Almost always the answer is an overlay module in your own
   `work/`, and there are two seams for it: `build` and `draw` put something on
   top of the finished frames, and `refine_art` corrects what the animator thinks
   is artwork. `engine/README.md` describes both. When it is genuinely neither,
   the engine change is made from the root, by whoever is looking after them all.

4. **If you are working in `engine/`, you are changing every variant.**
   Before committing, re-render one clip in each and compare it against what it
   produced before. A difference is fine when it is the fix arriving - say which
   fix, and how large the difference is, in pixels and clusters, not in
   adjectives. `./engine-status.sh` must still say every variant calls the engine
   and keeps no copy.

5. **Shipped is shipped.** A rule found halfway through a day applies to the
   clips made after it, never backwards. Nothing already in an `OUTPUT/<DD.MM>/`
   folder is rebuilt because a later clip does it better. Do not offer to.

6. **Every clip ships with sound.** The silent pass is an intermediate: keep it
   in `work/` or in `/tmp`, whichever your render script does - both variants'
   `render.sh` need it on disk to probe its duration before muxing. What matters
   is that it **never lands in `OUTPUT/`**, where it is only something to mistake
   for the finished clip later.

7. **`INPUT/` holds base images and nothing else.** The base is the one file a
   person opens - it gets attached to the prompt. Its clean copy and its layout
   are working files: `recolor_base.py --work` keeps them in `work/`.

9. **A poster that came back wrong is regenerated, not reconstructed.** If the
   generator moved a wave, drew an organ half outside its circle, or invented
   something that is not on disk anywhere, ask for another poster.
   `check_base.py` says so and it is right: the animation cannot correct a wave
   the generator redrew.

   The one thing that is allowed is putting **base** pixels back. The row
   stripe, the wave, the guide circle and the caption bars exist on disk at
   pixel-exact geometry, and copying a region of the base over a poster that
   scribbled on it is the same trade the whole design makes everywhere else:
   what must be identical is never regenerated. Restoring is fine.
   Reconstructing is not.

8. **The prompt is not a file.** It is written in the terminal for the topic at
   hand and handed over whole, ready to paste. A saved copy goes stale in an
   afternoon.

## Before writing code here

Read the variant's `work/flow.md`. Its **what is already known to break** section
is every mistake that cost an hour, with the measurement that found it. They all
came back twice before being written down: the flat bowls, ten captions at ten
sizes, the liquid cut where it meets the organ, the wave that climbed to the
right. Do not rediscover them.
