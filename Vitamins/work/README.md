# Vitamins/work

What is in here and what it is for. `flow.md` is the loop and the mistakes;
`../CLAUDE.md` is the rules. This file is the map.

## Authored

    topics.json          a topic: five foods, captions, servings, any vitamin
                         chosen by hand. The ONLY place a topic is decided
    ImageSwap.txt        the prompt template. The right circle stays empty

## Derived from those, by command

    vitamins.py          topics.json -> the vitamin spec, the badge spec, the
                         caption string, the prompt rows. Nothing retypes them
    make_prompt.py       fills ImageSwap.txt for a topic -> prompt_<topic>.txt
                         (written, never read back - ../../CLAUDE.md rule 8)

## Rendering

    render.sh            one argument. Act one, then render2.sh. This is the one
    render2.sh           the turn and the card onto an act one already rendered
    vitamin_overlay.py   the ball in the right circle. This variant's own seam
    micro_card.py        act two: the list, the ring, the score, the note
    micro_result.py      the app's own micronutrient maths, ported

## Testing

    make_fixture.py      an Organs poster with the organs taken out, so the whole
                         path can be run without waiting on a generation.
                         Writes <topic>_fixture.png. NOT a poster; nothing it
                         makes may ship

## In the engine, called by path, never copied in

    ../../engine/flowanim.py        the animator
    ../../engine/micro_overlay.py   the badges. Shared with Organs
    ../../engine/micro_audio.py     the pops, the act-two ticks, the chord
    ../../engine/micro_icons.py     builds the balls
    ../../engine/micro/icons/       42 badge balls, shared with Organs
    ../../engine/micro/nutrients.json   food -> what it is known for
    ../../engine/glass.py           the frosted card act two is drawn on
    ../../engine/flip.py            the turn
    ../../engine/add_labels.py      the captions into the reserved bars
    ../../engine/check_base.py      how far the generator moved the wave

`../../engine-status.sh` reports whether that is still true. It only reads.

## The demo topic

`demo` is the format test and not a topic to ship. Its picture is Organs'
`ageing` poster with the organs restored out of the right circles, so every step
of this variant can be exercised end to end without a generation:

    ./make_fixture.py ../../Organs/work/ageing_poster.jpeg demo
    ../.venv/bin/python ../../engine/add_labels.py demo_fixture.png \
        -l base_demo_layout.json -o demo_labelled.png \
        --labels "$(./vitamins.py demo --labels)"
    ./render.sh demo

Its base carries `AGE SLOWER`'s title, because the base is a copy of that topic's
and a title is drawn into the base by `recolor_base.py`. A real topic gets its own
base and its own title. `topics.json`'s `title` is act two's heading and is the
one thing about `demo` that reads correctly.

Every command above runs from this folder.
