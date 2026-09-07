# Foods — a food, a wave, the organ it feeds

The original variant. Five rows: a bowl of food on the left, the liquid it pours,
the organ it feeds on the right.

    INPUT/     base_<topic>.png - what you hand the user to attach to the prompt
    OUTPUT/    <DD.MM>/<topic>_sfx.mp4
    work/      bases' clean copies and layouts, the posters that come back,
               the labelled posters, flow.md, Prompts.txt, ImageSwap.txt

**`work/flow.md` is the loop.** Read it before doing anything: the palette, the
prompt, `check_base.py`, `add_labels.py`, the animation, the sound, the audit.
Its **what is already known to break** section is not background reading.

**Yours to change: everything in `Foods/`, and nothing else.** Not `Micro/`, `Exercise/`,
which other agents are in at the same time. Not `engine/` - the animator, the
wave assets and the tools are shared by all three variants, and a change made
from in here is a change made to two clips nobody asked you to touch.

If this variant needs something the engine does not do, **say so and stop**: name
what is missing and what you would change. Do not edit `engine/`, do not copy a
tool in here to edit it, and do not patch around it. The seams meant for this are
`--overlay` with `build` and `draw`, and `refine_art` when the animator has
misread what is artwork. Both are in `engine/README.md`. See `../CLAUDE.md` rule 3.

The prompt template is `work/ImageSwap.txt` and the filled ones are in
`work/Prompts.txt` - but the prompt handed to the user is always written out
whole in the terminal, ready to paste, never as a diff against an earlier one.
