# Healthness Shorts — house rules

**This is not the app repository.** The `CLAUDE.md` two levels up describes
`fitcircle/`, `fitcircle-android/` and the web page: `develop`, `scripts/run.sh`,
`parity.sh`, `push.sh`. None of it applies here. Nothing in this tree builds an
app, and there is no `scripts/` folder.

This is its own git repository — `healthness-videogen`, private, branch `main`.

**Started at the root rather than inside a variant?** Then the engine is yours
and so is deciding what belongs in it: read `MAINTAINER.md` after this. Started
inside `Foods/`, `Micro/`, `Exercise/` or `Biohacks/`? That folder is your whole
remit - see
rule 3 - and `MAINTAINER.md` is not addressed to you.

## The shape

    engine/                the seven tools, three authored wave assets, sfx/
    Foods/ Micro/ Exercise/ Biohacks/   four variants, three folders each:
    Longevity/             the father: five rows are one fast, not five topics
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

3. **Change only your own variant.** If you were started in `Foods/`, `Micro/`,
   `Exercise/` or `Biohacks/`, that folder is the whole of what you may edit.
   Not the other three - other people and other agents are in them at the same
   time. **And not
   `engine/`**, no matter how small or how obviously right the change looks.
   A variant is not the place from which the thing all four variants run gets
   changed.

   The rule reads like a restriction and works like a division of labour. Four
   engine-level things came out of one variant in a single day - the guide-circle
   wipe's assumption, three dead flags, a poster grabbed by the wrong variant,
   and a mechanism written from one observation - and its agent's report on the
   cost was that not one of them took longer than the message describing it.
   Every one was fixed at the root, once, for all four.

   When a variant needs something the engine does not do: **say so and stop.**
   Describe what is missing and what you would change. Do not edit `engine/`, do
   not copy a tool into your folder to edit it there, and do not work around it
   with a patch script. Almost always the answer is an overlay module in your own
   `work/`, and there are two seams for it: `build` and `draw` put something on
   top of the finished frames, and `refine_art` corrects what the animator thinks
   is artwork. `engine/README.md` describes both. When it is genuinely neither,
   the engine change is made from the root, by whoever is looking after all four.

4. **If you are working in `engine/`, you are changing all four variants.**
   Before committing, re-render one clip in each and compare it against what it
   produced before. A difference is fine when it is the fix arriving - say which
   fix, and how large the difference is, in pixels and clusters, not in
   adjectives. `./engine-status.sh` must still say every variant calls the engine
   and keeps no copy.

5. **Shipped is shipped.** A rule found halfway through a day applies to the
   clips made after it, never backwards. Nothing already in an `OUTPUT/<DD.MM>/`
   folder is rebuilt because a later clip does it better. Do not offer to.

6. **Every clip ships with sound.** The silent pass is an intermediate: keep it
   in `work/` or in `/tmp`, whichever your render script does - every variant's
   `render.sh` needs it on disk to probe its duration before muxing. What matters
   is that it **never lands in `OUTPUT/`**, where it is only something to mistake
   for the finished clip later.

   Nor does anything else. A check that *reads* a shipped clip writes its
   intermediates somewhere it names explicitly: on 8 September a comparison
   decoded two clips to wav with a loop that put one of them back beside its
   source, and a day folder held a stray `.wav` until the next listing caught
   it. A day folder holds finished clips and nothing at all besides.

7. **`INPUT/` holds base images and nothing else.** The base is the one file a
   person opens - it gets attached to the prompt. Its clean copy and its layout
   are working files: `recolor_base.py --work` keeps them in `work/`.

9. **A poster that came back wrong is regenerated, not reconstructed.** If the
   generator moved a wave, drew an organ half outside its circle, or invented
   something that is not on disk anywhere, ask for another poster.
   `check_base.py` says so and it is right: the animation cannot correct a wave
   the generator redrew.

   **Keep one archival copy of every shipped poster**, as
   `<topic>_poster.jpeg` beside the working files. It is the only artefact in
   this repository that no command can remake: a base comes back from
   `recolor_base.py`, a labelled poster from `add_labels.py`, a clip from
   `render.sh` - but an image model cannot be asked twice for the same picture,
   and the wave in a poster is the wave that clip's animation was measured
   against. Micro measured the exposure on 8 September: fourteen of its topics
   existed only as untracked files, and a lost `work/` would have ended them.

   The one thing that is allowed is putting **base** pixels back. The row
   stripe, the wave, the guide circle and the caption bars exist on disk at
   pixel-exact geometry, and copying a region of the base over a poster that
   scribbled on it is the same trade the whole design makes everywhere else:
   what must be identical is never regenerated. Restoring is fine.
   Reconstructing is not.

   **A base element that is gone is a regeneration, full stop** - stripes,
   waves, bars, logo. No deciding whether it can be worked around. The user set
   this on 8 September, after part 18 came back with artwork 15 to 64px into
   caption bars 78px tall, on all ten bars, against a historic worst of 7.
   Restoring the bars there would not have been putting base pixels back: what
   had spilled into them was the bowls and the organs, so the restored bar would
   have cut those shapes off with a hard horizontal edge. That is the boundary
   the allowance above already had and did not say - restoration is for a region
   with nothing that legitimately belongs over it. Where a case sits between the
   two, it is a regeneration, because deliberating is how a bad poster ships.

8. **The prompt is not a file.** It is written in the terminal for the topic at
   hand and handed over whole, ready to paste. A saved copy goes stale in an
   afternoon.

   What the rule forbids is a prompt **copied forward**: the poster that came
   back from a prompt three revisions old came back because a file was lying
   there and got pasted again. A prompt written down and never read back is a log
   entry, not a source, and Micro keeps one per topic for exactly that - to
   reprint after a regeneration, and to diff two passes of the same part. The
   invariant that makes it safe is greppable, so state it that way: *the
   generator writes `prompt_<topic>.txt` from `ImageSwap.txt`, and **nothing may
   read `prompt_<topic>.txt` back.*** Check that, not whether a file exists - and
   read it as a prohibition rather than as an observation, because an agent
   looking for "the prompt for superfoods15" will find that file before it finds
   `ImageSwap.txt`, and reading it would be the whole failure recreated in one
   step. The next topic is filled from the template, always.

   `../../engine/clip.py prompt` is the handover, and it is not one of those
   files: one buffer, overwritten by the next prompt, gone on reboot, refusing
   past 45 minutes.

## Before writing code here

Read the variant's `work/flow.md`. Its **what is already known to break** section
is every mistake that cost an hour, with the measurement that found it. They all
came back twice before being written down: the flat bowls, ten captions at ten
sizes, the liquid cut where it meets the organ, the wave that climbed to the
right. Do not rediscover them.
