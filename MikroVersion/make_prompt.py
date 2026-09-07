#!/usr/bin/env python3
"""
make_prompt.py - fill the live template, never a copy of it.

The thyroid poster was generated from a prompt that had been typed out by hand
from a template three revisions old: it was missing the clear glass bowls and the
3D organs the base generator had added that morning. Nothing said so, because a
prompt written into a file is a copy the moment the template moves.

So the prompt is not written any more, it is filled. The body comes from the
`=== THE PROMPT ===` block of ImageSwap.txt as it stands right now, and only the
five rows are substituted. Update the template and every topic re-rendered from
it is current.

    python3 make_prompt.py hair \\
        --title 'HAIR & NAILS' --subtitle 'FOODS THAT REBUILD THEM' \\
        --row 'whole eggs with cracked yolks | a hair follicle inside living skin' \\
        ... five of them ... \\
        --captions 'EGGS|STRONG STRANDS,...' \\
        --badges 'Biotin,Protein,Selenium;...' \\
        --palette 'rows #331821 / #F7EDE8, waves #FFC233, ...' \\
        --note 'why this topic'
"""
import argparse
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "ImageSwap.txt")


HEAPED = "the food heaped above the rim"


def body(rows):
    t = open(TEMPLATE).read()
    a = t.index("=== THE PROMPT ===")
    a = t.index("\n", a) + 1
    b = t.index("=== END OF PROMPT ===")
    s = t[a:b].strip("\n")
    lines = s.split("\n")
    for i, (food, organ, rim) in enumerate(rows, 1):
        for j, ln in enumerate(lines):
            if f"<FOOD {i}>" not in ln:
                continue
            # A liquid cannot be heaped. The template's tail is written for solid
            # food, so a broth or a honey row supplies its own rim clause and it
            # is swapped in here rather than left to contradict itself.
            if rim:
                ln = ln.replace(HEAPED, rim)
            lines[j] = ln.replace(f"<FOOD {i}>", food).replace(f"<ORGAN {i}>", organ)
    s = "\n".join(lines)
    left = re.findall(r"<[A-Z]+ \d>", s)
    if left:
        raise SystemExit(f"template still holds {sorted(set(left))} - "
                         f"give one --row per placeholder")
    return s


def negative():
    t = open(TEMPLATE).read()
    a = t.index("NEGATIVE PROMPT")
    a = t.index("\n\n", a) + 2
    b = t.index("\n\n", a)
    return t[a:b].strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("topic")
    p.add_argument("--title", required=True)
    p.add_argument("--subtitle", required=True)
    p.add_argument("--row", action="append", required=True,
                   help="'FOOD | ORGAN', five of them, top row first. A liquid adds "
                        "a third field, the clause that replaces 'the food heaped "
                        "above the rim': 'honey | throat | filling the bowl to just "
                        "under the rim'")
    p.add_argument("--captions", required=True)
    p.add_argument("--badges", required=True)
    p.add_argument("--palette", default="")
    p.add_argument("--note", default="")
    p.add_argument("-o", "--out")
    args = p.parse_args()

    rows = []
    for r in args.row:
        parts = [x.strip() for x in r.split("|")]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise SystemExit(f"--row needs 'FOOD | ORGAN': {r}")
        rows.append((parts[0], parts[1], parts[2] if len(parts) > 2 else ""))

    t = args.topic
    out = args.out or os.path.join(HERE, "INPUT", f"prompt_{t}.txt")
    head = f"{args.title} — attach base_{t}.png (the one WITH the faint circles)"
    text = f"""{head}
{'=' * len(head)}

Generate at 1536 x 2752. Put the returned poster back as INPUT/{t}_poster.png.

Filled from ImageSwap.txt by make_prompt.py, so it is the template as it stands,
not a copy of an older one.

Title:    '{args.title}'
Subtitle: '{args.subtitle}'
{('Palette:  ' + args.palette) if args.palette else ''}

Captions (go on afterwards, not in the prompt):
  '{args.captions}'

Badges:
  '{args.badges}'
{(chr(10) + args.note) if args.note else ''}

=== THE PROMPT ===

{body(rows)}

=== END OF PROMPT ===


NEGATIVE PROMPT, if the tool offers a separate field:

{negative()}


WHEN THE POSTER COMES BACK

    .venv/bin/python check_base.py INPUT/{t}_poster.png --base INPUT/base_{t}.png

    .venv/bin/python add_labels.py INPUT/{t}_poster.png \\
        -l INPUT/base_{t}_layout.json -o INPUT/{t}_labelled.png \\
        --labels '{args.captions}'

    ./render.sh {t} INPUT/{t}_labelled.png \\
        '{args.badges}'
"""
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        fh.write(text)
    print(f"  {len(rows)} rows filled from {os.path.basename(TEMPLATE)} -> {out}")


if __name__ == "__main__":
    main()
