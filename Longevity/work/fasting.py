#!/usr/bin/env python3
"""
fasting.py - the app's stages and protocols, extracted rather than copied.

`fasting.json` is the data this category is built on: six metabolic stages with
hour thresholds and six protocols, all of it belonging to
`fitcircle/Sources/Models/Fasting.swift`. This file is how it gets here and how
it is kept honest.

## Why not just type it in

Because that is the mistake this repository keeps paying for. Every copy in here
has drifted: the tools drifted to three generations in one morning, the badge
synthesis drifted between two variants, the prompt template drifted four ways.
A hand-typed `fasting.json` is a fifth copy, and the thing it is a copy of lives
in **another repository that this one does not build, test or watch**. It would
drift silently, and the drift would be a number about somebody's body.

So the JSON is generated, and `--verify` re-extracts and compares. If Swift moves
and the JSON does not, that is a failing check rather than a stale poster.

    python3 fasting.py --write     regenerate fasting.json from the app
    python3 fasting.py --verify    does the JSON still match the app?
    python3 fasting.py             show what is in the app right now

## What it does not do

It does not paraphrase, reformat, sentence-case or trim anything. The summaries
carry the app's compliant phrasing - "typically", "commonly", "associated with"
- and that phrasing IS the source; see `longevity.py`. The extractor takes the
string between the quotes and nothing else, so there is no step at which a claim
could be softened or sharpened by accident.

It also does not follow the app's `.custom(hours:)` protocol, which has no fixed
hours and therefore no poster.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fasting.json")

# Five levels up from Longevity/work: ShortPrompt -> SHorts -> Healtness ->
# test -> and fitcircle sits beside Healtness. Resolved rather than hardcoded
# absolute, so a checkout somewhere else still finds it.
SWIFT = os.path.normpath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "fitcircle", "Sources", "Models", "Fasting.swift"))

_STAGE = re.compile(
    r'\.init\(\s*id:\s*"(?P<id>[^"]+)",\s*'
    r'name:\s*"(?P<name>[^"]+)",\s*'
    r'startHour:\s*(?P<h0>[\d.]+),\s*'
    r'endHour:\s*(?P<h1>[\d.]+|nil),\s*'
    r'summary:\s*"(?P<summary>[^"]*)",\s*'
    r'learnMoreDetail:\s*"(?P<detail>[^"]*)"', re.S)

_PROTO = re.compile(
    r'\.init\(\s*id:\s*"(?P<id>[^"]+)",\s*'
    r'name:\s*"(?P<name>[^"]+)",\s*'
    r'fastHours:\s*(?P<fast>\d+),\s*'
    r'eatHours:\s*(?P<eat>\d+),\s*'
    r'summary:\s*"(?P<summary>[^"]*)"', re.S)


def extract(path=SWIFT):
    if not os.path.exists(path):
        raise SystemExit(
            f"cannot find {path}.\nThe app repository is where this data lives; "
            f"without it fasting.json cannot be verified, and an unverifiable "
            f"copy of somebody's health thresholds is exactly what this file "
            f"exists to prevent.")
    src = open(path, encoding="utf-8").read()

    # Scoped to each `static let library: [...] = [ ... ]` block, not to the
    # whole file. `stage(forElapsedHours:)` ends with a fallback `.init(...)`
    # that matches the stage pattern exactly - same fields, empty summary - and
    # without this it comes through as a seventh stage carrying no words. The
    # count assertion below caught it on the first run, which is the only reason
    # it is not in fasting.json now.
    def library(kind):
        i = src.index(f"static let library: [{kind}]")
        # From the `= [` that opens the array, not from the `[` in the type
        # annotation two characters earlier - which is what the first version
        # did, and it returned an empty slice rather than failing.
        depth, j = 0, src.index("[", src.index("=", i))
        for k in range(j, len(src)):
            if src[k] == "[":
                depth += 1
            elif src[k] == "]":
                depth -= 1
                if depth == 0:
                    return src[j:k]
        raise SystemExit(f"unbalanced brackets in {kind}'s library")

    stage_src, proto_src = library("FastingBodyStage"), library("FastingProtocol")

    stages = [dict(id=m["id"], name=m["name"],
                   h0=float(m["h0"]), h1=None if m["h1"] == "nil" else float(m["h1"]),
                   summary=m["summary"], detail=m["detail"])
              for m in _STAGE.finditer(stage_src)]
    protocols = [dict(id=m["id"], name=m["name"],
                      fast=int(m["fast"]), eat=int(m["eat"]), summary=m["summary"])
                 for m in _PROTO.finditer(proto_src)]

    # A silent zero is the failure mode that matters: the regex stops matching
    # after a refactor upstream, an empty list is written, and the category
    # quietly has no stages. Both counts are asserted against what the app ships.
    if len(stages) != 6 or len(protocols) != 6:
        raise SystemExit(
            f"extracted {len(stages)} stages and {len(protocols)} protocols; "
            f"the app ships 6 and 6. Either Fasting.swift changed shape or the "
            f"patterns in here did - read the file before touching the regex.")
    return dict(source=os.path.relpath(path, os.path.join(HERE, "..", "..", "..", "..")),
                stages=stages, protocols=protocols)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true")
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    got = extract()

    if a.write:
        json.dump(got, open(OUT, "w"), indent=1, ensure_ascii=False)
        print(f"  {len(got['stages'])} stages, {len(got['protocols'])} protocols "
              f"-> {os.path.basename(OUT)}")
        return

    if a.verify:
        if not os.path.exists(OUT):
            sys.exit(f"no {os.path.basename(OUT)} - run --write")
        have = json.load(open(OUT, encoding="utf-8"))
        if have == got:
            print(f"  fasting.json matches {os.path.basename(SWIFT)}")
            return
        print(f"  fasting.json NO LONGER MATCHES {os.path.basename(SWIFT)}\n")
        for key in ("stages", "protocols"):
            for h, g in zip(have.get(key, []), got.get(key, [])):
                for f in g:
                    if h.get(f) != g.get(f):
                        print(f"    {key[:-1]} {g['id']}.{f}")
                        print(f"      app  {g[f]!r}")
                        print(f"      here {h.get(f)!r}")
            if len(have.get(key, [])) != len(got.get(key, [])):
                print(f"    {key}: {len(have.get(key, []))} here, "
                      f"{len(got.get(key, []))} in the app")
        print("\n  The app is the source. Re-run --write, then look at every row "
              "of\n  every poster that used the old thresholds before shipping "
              "anything else.")
        sys.exit(1)

    print(f"{got['source']}\n")
    for s in got["stages"]:
        end = f"-{int(s['h1'])}" if s["h1"] else "+"
        print(f"  {str(int(s['h0'])) + end:>7} h  {s['name']:<13} {s['summary']}")
    print()
    for pr in got["protocols"]:
        print(f"  {pr['name']:<12} {pr['fast']:>2}:{pr['eat']:<2}  {pr['summary']}")


if __name__ == "__main__":
    main()
