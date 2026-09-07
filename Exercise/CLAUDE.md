# Exercise — a lift, a wave, the muscles it works

Five rows: a lifter on the left, the liquid, and a body on the right whose
muscles light one at a time as their badges land.

    INPUT/     base_<topic>.png
    OUTPUT/    <DD.MM>/<topic>_muscles.mp4
    work/      render.sh, muscle_overlay.py, body_overlay.py, bodymap.py,
               muscles.py, muscle_icons.py, muscle_audio.py, exercises.json,
               icons/, flow.md, README.md

    cd work && ./render.sh <topic> <topic>_labelled.png 'auto:LIFT,LIFT,LIFT,LIFT,LIFT'

**Two overlays, and the order matters.** `--overlay body_overlay,muscle_overlay`:
the body is drawn first, because it ends the wave where the organ ends it in the
food version, and a badge is never behind it. Both plug into the engine through
`add_arguments`, `build` and `draw` - neither patches it, and neither may be
turned back into a copy of `flowanim.py`.

The body is drawn at render time rather than baked into the poster, because a
muscle has to light on the frame its badge lands and a baked body cannot do
anything on a frame.

**Yours to change: everything in `Exercise/`, and nothing else.** Not `Foods/`, `Micro/`,
which other agents are in at the same time. Not `engine/` - the animator, the
wave assets and the tools are shared by all three variants, and a change made
from in here is a change made to two clips nobody asked you to touch.

If this variant needs something the engine does not do, **say so and stop**: name
what is missing and what you would change. Do not edit `engine/`, do not copy a
tool in here to edit it, and do not patch around it. The seams meant for this are
`--overlay` with `build` and `draw`, and `refine_art` when the animator has
misread what is artwork. Both are in `engine/README.md`. See `../CLAUDE.md` rule 3.