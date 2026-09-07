# Micro — the same clip, with the micronutrients on it

The food poster with the vitamins, minerals and fibre a food actually carries
popping onto its row while the liquid runs.

    INPUT/     base_<topic>.png
    OUTPUT/    <DD.MM>/<topic>_micro.mp4
    work/      render.sh, micro_overlay.py, micro_icons.py, micro_audio.py,
               nutrients.json, icons/, icon-sources/, flow.md, README.md

    cd work && ./render.sh <topic> <topic>_labelled.png 'auto:FOOD,FOOD,FOOD,FOOD,FOOD'

`render.sh` does animation, pops and mux in one command, because the three have
to agree on when the badges land and typing the times twice is how a pop ends up
half a frame off its badge.

**`micro_overlay.py` plugs into the engine, it does not patch it.** Its
`add_arguments`, `build` and `draw` are what `../../engine/flowanim.py --overlay
micro_overlay` calls. There was once a `micro_patch.py` here that grafted the
badge layer onto a copy of the animator; the hook replaced it. Do not bring it
back, and do not copy an engine file into this folder.

Yours to change: everything in `Micro/`. Not yours: `engine/`, `Foods/`,
`Exercise/`. See `../CLAUDE.md`.

`work/make_prompt.py` fills the current template for a topic. That is compatible
with rule 8: it reads `ImageSwap.txt` as it stands now rather than keeping a copy
of a prompt written yesterday. Its output is a working file - do not file it in
`INPUT/`.
