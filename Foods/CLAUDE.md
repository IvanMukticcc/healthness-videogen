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

Yours to change: everything in `Foods/`. Not yours: `engine/`, `Micro/`,
`Exercise/`. See `../CLAUDE.md` for why.

The prompt template is `work/ImageSwap.txt` and the filled ones are in
`work/Prompts.txt` - but the prompt handed to the user is always written out
whole in the terminal, ready to paste, never as a diff against an earlier one.
