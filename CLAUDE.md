# Healthness Shorts — house rules

**This is not the app repository.** The `CLAUDE.md` two levels up describes
`fitcircle/`, `fitcircle-android/` and the web page: `develop`, `scripts/run.sh`,
`parity.sh`, `push.sh`. None of it applies here. Nothing in this tree builds an
app, and there is no `scripts/` folder.

This is its own git repository — `healthness-videogen`, private, branch `main`.

## The shape

    engine/                the five tools, three authored wave assets, sfx/
    Foods/ Micro/ Exercise/    three variants, three folders each:
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

3. **Work only in your own variant.** Do not edit a sibling variant's folder.
   Other people and other agents are in them at the same time.

4. **Changing anything in `engine/` changes all three variants.** Before
   committing such a change, re-render one clip in each and compare it against
   what it produced before. A difference is fine when it is the fix arriving -
   say which fix, and how large the difference is.

5. **Shipped is shipped.** A rule found halfway through a day applies to the
   clips made after it, never backwards. Nothing already in an `OUTPUT/<DD.MM>/`
   folder is rebuilt because a later clip does it better. Do not offer to.

6. **Every clip ships with sound.** The silent pass is an intermediate and is
   rendered to `/tmp`. Only the `_sfx` cut is written into `OUTPUT/`.

7. **`INPUT/` holds base images and nothing else.** The base is the one file a
   person opens - it gets attached to the prompt. Its clean copy and its layout
   are working files: `recolor_base.py --work` keeps them in `work/`.

8. **The prompt is not a file.** It is written in the terminal for the topic at
   hand and handed over whole, ready to paste. A saved copy goes stale in an
   afternoon.

## Before writing code here

Read the variant's `work/flow.md`. Its **what is already known to break** section
is every mistake that cost an hour, with the measurement that found it. They all
came back twice before being written down: the flat bowls, ten captions at ten
sizes, the liquid cut where it meets the organ, the wave that climbed to the
right. Do not rediscover them.
