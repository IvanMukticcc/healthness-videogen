#!/usr/bin/env python3
"""
vitamins.py - everything a Vitamins render needs, derived from topics.json.

`topics.json` is the authored half of a topic: five foods, their labels, their
servings, and any vitamin somebody chose by hand. This file is the derived half,
and it exists so that no part of a render is typed twice. The caption string, the
badge spec, the vitamin spec and the prompt rows all come out of one file, so a
topic cannot disagree with itself.

    ./vitamins.py demo --vitamins    C,C,D,K,C
    ./vitamins.py demo --badges      K,Fiber;Fiber,Polyphenols;...
    ./vitamins.py demo --labels      KIWI|VITAMIN C,BLACKBERRIES|VITAMIN C,...
    ./vitamins.py demo --rows        the --row arguments for make_prompt.py
    ./vitamins.py demo               the table, for a person

WHICH VITAMIN IS THE HEADLINE

`engine/micro/nutrients.json` already says what each food is known for, in the
order the badges should pop. The headline is the first entry of that row which
belongs to the vitamin family - the family is `micro_icons.py`'s, the same three
colours the badges are cut in, so the ball on the right and the badges in the
middle are the same blue.

Not every food has one. Dark chocolate is Polyphenols, Magnesium, Iron; garlic
gets there on its third entry. When the derivation finds nothing this **fails and
names the row** rather than picking something: a vitamins clip whose right circle
was filled by a fallback is a clip making a claim nobody made. Write the answer
into the row's `vitamin` in topics.json and it is recorded, which is the whole of
../../CLAUDE.md rule 13.

WHY THE HEADLINE LEAVES THE ROW'S BADGES

It is already the biggest thing on the row. Popping it again 300px to the left is
the same word twice in one second, so by default the row's badges are what is
LEFT after the headline is taken out - two per row instead of three. `--keep-all`
puts it back. This is the one place Vitamins deliberately reads differently from
Organs, where all three pop because nothing on that row has said them yet.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "..", "engine")
sys.path.insert(0, ENGINE)

import micro_icons                                            # noqa: E402
import micro_overlay                                          # noqa: E402

TOPICS = os.path.join(HERE, "topics.json")

# name as nutrients.json writes it -> the family micro_icons cut its ball in.
# 'v' is a vitamin; 'm' a mineral; 'o' fibre, protein, omega-3 and the rest.
FAMILY = {name: fam for name, _, fam in micro_icons.CATALOGUE}


def key(name):
    """nutrients.json's spelling -> the badge filename, which is what FAMILY and
    engine/micro/icons/ are both keyed by. 'Beta-carotene' -> 'BETACAROTENE'."""
    return name.upper().replace(" ", "").replace("-", "")


def caption(vit):
    """The right caption bar. 'C' -> VITAMIN C, 'B12' -> VITAMIN B12, but
    'Folate' -> FOLATE: nobody says "vitamin folate", and the bar is 380px wide
    with no room for a word that is wrong anyway."""
    k = key(vit)
    lettered = len(k) <= 3 and k[0].isalpha() and (len(k) == 1 or k[1:].isdigit())
    return f"VITAMIN {k}" if lettered else k


def load(topic, path=TOPICS):
    with open(path) as fh:
        t = json.load(fh)
    if topic not in t:
        have = ", ".join(sorted(k for k in t if not k.startswith("_")))
        raise SystemExit(f"{topic} is not in {os.path.basename(path)} - have: {have}")
    e = t[topic]
    rows = e["rows"]
    if len(rows) != 5:
        raise SystemExit(f"{topic} has {len(rows)} rows - the base has five")
    return e, rows


def nutrients(rows):
    """Each row's nutrients, in nutrients.json's own pop order."""
    return micro_overlay.resolve("auto:" + ",".join(r["label"] for r in rows))


def headlines(rows, nuts):
    """The vitamin in the right circle, one per row. Authored where it is
    authored, derived where it is not, and a failure that names the row where it
    is neither."""
    out, missing = [], []
    for i, (r, ns) in enumerate(zip(rows, nuts), 1):
        v = r.get("vitamin")
        if v:
            if key(v) not in FAMILY:
                raise SystemExit(f"row {i}: '{v}' is not a badge micro_icons knows - "
                                 f"build it with micro_icons.py --one '{v}:v'")
            out.append(v)
            continue
        hit = next((n for n in ns if FAMILY.get(key(n)) == "v"), None)
        if hit is None:
            missing.append(f"  row {i} {r['label']}: {', '.join(ns)} - no vitamin among them")
        out.append(hit)
    if missing:
        raise SystemExit(
            "no vitamin can be derived for these rows:\n" + "\n".join(missing) +
            "\n\nPut the one you mean in that row's \"vitamin\" in topics.json. "
            "It is a choice, so it is recorded rather than guessed (rule 13).")
    return out


def badges(nuts, heads, keep_all=False):
    """What still pops on the row: everything except the headline."""
    out = []
    for ns, h in zip(nuts, heads):
        out.append(list(ns) if keep_all else [n for n in ns if key(n) != key(h)])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("topic")
    p.add_argument("--vitamins", action="store_true",
                   help="the right circles, for flowanim --vitamin")
    p.add_argument("--badges", action="store_true",
                   help="the badges that still pop, for flowanim --micro")
    p.add_argument("--labels", action="store_true",
                   help="the caption pairs, for add_labels.py --labels")
    p.add_argument("--rows", action="store_true",
                   help="the --row arguments for make_prompt.py, one per line")
    p.add_argument("--title", action="store_true")
    p.add_argument("--subtitle", action="store_true")
    p.add_argument("--keep-all", action="store_true",
                   help="leave the headline vitamin in the row's badges too")
    p.add_argument("--topics", default=TOPICS)
    a = p.parse_args()

    e, rows = load(a.topic, a.topics)
    nuts = nutrients(rows)
    heads = headlines(rows, nuts)
    bad = badges(nuts, heads, a.keep_all)

    if a.title:
        print(e["title"]); return
    if a.subtitle:
        print(e["subtitle"]); return
    if a.vitamins:
        print(",".join(heads)); return
    if a.badges:
        print(";".join(",".join(b) for b in bad)); return
    if a.labels:
        # add_labels.py splits on ',' and a food name can contain one - 442 of the
        # app's 2272 do. The labels here are the SHORT ones a person wrote in
        # topics.json, not the database names, so the caller owns the comma and
        # this is where it is checked rather than where it is parsed.
        for r in rows:
            if "," in r["label"] or "|" in r["label"]:
                raise SystemExit(f"'{r['label']}' contains a ',' or a '|', which are "
                                 f"what add_labels.py splits on - shorten it")
        print(",".join(f"{r['label']}|{caption(h)}" for r, h in zip(rows, heads)))
        return
    if a.rows:
        # make_prompt.py here takes 'FOOD' or 'FOOD | rim clause' and nothing
        # else. There is no second noun because the generator is not asked for
        # one: the right circle is the one thing in this variant's prompt that
        # stays empty, and the ball goes on it afterwards.
        for r in rows:
            print(f"{r['food']} | {r['rim']}" if r.get("rim") else r["food"])
        return

    w = max(len(r["label"]) for r in rows)
    print(f"{e['title']} - {e['subtitle']}")
    for r, h, b in zip(rows, heads, bad):
        src = "authored" if r.get("vitamin") else "derived"
        print(f"  {r['label']:<{w}}  {caption(h):<12} ({src})   badges: {', '.join(b)}")


if __name__ == "__main__":
    main()
