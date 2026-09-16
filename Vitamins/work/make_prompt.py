#!/usr/bin/env python3
"""
make_prompt.py - fill the live template, never a copy of it.

A poster was once generated from a prompt typed out by hand from a template three
revisions old: it was missing the clear glass bowls the base generator had added
that morning. Nothing said so, because a prompt written into a file is a copy the
moment the template moves.

So the prompt is not written any more, it is filled. The body comes from the
`=== THE PROMPT ===` block of ImageSwap.txt as it stands right now, and only the
five foods are substituted. Update the template and every topic re-rendered from
it is current.

    ./make_prompt.py demo
    ./make_prompt.py demo --body-only | ../../engine/clip.py prompt - --topic demo

THE ROWS COME FROM topics.json, NOT FROM THE COMMAND LINE.

Organs' version of this file takes the five rows as `--row` arguments, and that
is how a topic's foods came to exist in exactly two places: the generated prompt,
which ../../CLAUDE.md rule 8 forbids reading back, and the pixels of the finished
clips. ../../CLAUDE.md rule 13 is the answer and `topics.json` is where it lives -
so here the topic is named and everything else is looked up. `--row` is still
accepted for a one-off that is not a topic yet.

This is not rule 8 loosened. `prompt_<topic>.txt` is still written and still
never read back; what changed is that the INPUT the prompt is built from is a
file a program may read.
"""
import argparse
import json
import os
import re
import sys

import vitamins as V

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "ImageSwap.txt")

HEAPED = "the food heaped above the rim"


def body(rows):
    """`rows` is a list of (food, rim_clause). There is no second noun: the right
    circle is left empty and the ball goes on afterwards."""
    t = open(TEMPLATE).read()
    a = t.index("=== THE PROMPT ===")
    a = t.index("\n", a) + 1
    b = t.index("=== END OF PROMPT ===")
    s = t[a:b].strip("\n")
    lines = s.split("\n")
    for i, (food, rim) in enumerate(rows, 1):
        for j, ln in enumerate(lines):
            if f"<FOOD {i}>" not in ln:
                continue
            # A liquid cannot be heaped. The template's tail is written for solid
            # food, so a broth or a tea row supplies its own rim clause and it is
            # swapped in here rather than left to contradict itself.
            if rim:
                ln = ln.replace(HEAPED, rim)
            lines[j] = ln.replace(f"<FOOD {i}>", food)
    s = "\n".join(lines)
    left = re.findall(r"<[A-Z]+ \d>", s)
    if left:
        raise SystemExit(f"template still holds {sorted(set(left))} - "
                         f"give one row per placeholder")
    return s


def main():
    p = argparse.ArgumentParser()
    p.add_argument("topic")
    p.add_argument("--row", action="append", default=[],
                   help="'FOOD' or 'FOOD | rim clause', five of them, top row "
                        "first. Overrides topics.json for a one-off")
    p.add_argument("--title")
    p.add_argument("--subtitle")
    p.add_argument("--note", default="")
    p.add_argument("-o", "--out")
    # The header of this file - title, captions, vitamins, the note - is for the
    # person, not for the generator. Pasted whole into it once, it cost a poster:
    # the header names the captions inside a prompt whose body forbids text in
    # three places, and everything came back 33 to 74px into caption bars 78px
    # tall. So the handover is the body alone, and this flag is what pipes it.
    p.add_argument("--body-only", action="store_true",
                   help="print the prompt body to stdout - what is pasted into "
                        "the generator, without this file's header or its tail. "
                        "The file is still written.")
    args = p.parse_args()

    t = args.topic
    if args.row:
        rows = []
        for r in args.row:
            parts = [x.strip() for x in r.split("|")]
            if not parts[0]:
                raise SystemExit(f"--row needs a food: {r}")
            rows.append((parts[0], parts[1] if len(parts) > 1 else ""))
        title = args.title or t.upper()
        subtitle = args.subtitle or ""
        labels = vits = "(not in topics.json - add it before rendering)"
    else:
        e, trows = V.load(t)
        nuts = V.nutrients(trows)
        heads = V.headlines(trows, nuts)
        rows = [(r["food"], r.get("rim", "")) for r in trows]
        title = args.title or e["title"]
        subtitle = args.subtitle or e["subtitle"]
        labels = ",".join(f"{r['label']}|{V.caption(h)}"
                          for r, h in zip(trows, heads))
        vits = ",".join(heads)

    # INPUT/ holds base images and nothing else (../../CLAUDE.md rule 7): the base
    # is the one file a person opens, to attach it. A filled prompt is a working
    # file and stays here, next to the template it was filled from.
    out = args.out or os.path.join(HERE, f"prompt_{t}.txt")
    head = f"{title} — attach base_{t}.png (the one WITH the faint circles)"
    text = f"""{head}
{'=' * len(head)}

Generate at 1536 x 2752. The poster comes back into work/, not into INPUT/:
INPUT/ holds base images and nothing else (../../CLAUDE.md rule 7), and the base
is the file you just attached. grab.py takes the newest one out of Downloads.

Filled from ImageSwap.txt by make_prompt.py, so it is the template as it stands,
not a copy of an older one. The five foods are topics.json's.

Title:    '{title}'
Subtitle: '{subtitle}'

THE RIGHT CIRCLES STAY EMPTY. The vitamin balls are composited afterwards by
vitamin_overlay.py out of engine/micro/icons/ - the generator is not asked for
them and must not draw anything there.

Captions (go on afterwards, not in the prompt):
  '{labels}'

Vitamins (the right circles, and the right caption bars):
  '{vits}'
{(chr(10) + args.note) if args.note else ''}

=== THE PROMPT ===

{body(rows)}

=== END OF PROMPT ===



WHEN THE POSTER COMES BACK, every command from work/

    ../.venv/bin/python ../../engine/grab.py {t}

    ../.venv/bin/python ../../engine/check_base.py {t}_poster.jpeg \\
        --base ../INPUT/base_{t}.png

    ../.venv/bin/python ../../engine/add_labels.py {t}_poster.jpeg \\
        -l base_{t}_layout.json -o {t}_labelled.png \\
        --labels "$(./vitamins.py {t} --labels)"

    ./render.sh {t}              act one, the turn and the card, in one command

Nothing above retypes a food, a vitamin or a badge: render.sh asks vitamins.py
for all three, and vitamins.py reads topics.json.
"""
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        fh.write(text)
    note = f"  {len(rows)} rows filled from {os.path.basename(TEMPLATE)} -> {out}"
    if args.body_only:
        # Not read back out of `out` - rule 8 forbids that, and the point of this
        # flag is the same point: what reaches the generator comes from the
        # template, never from a file lying about.
        sys.stdout.write(body(rows) + "\n")
        print(note, file=sys.stderr)
    else:
        print(note)


if __name__ == "__main__":
    main()
