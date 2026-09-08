#!/usr/bin/env python3
"""
longevity.py - the vocabulary. Five points on one fast, and what is true at each.

This is `Biohacks/work/hacks.py` generalised, and the generalisation is smaller
than it looks: that file answers "what does this habit change", this one answers
"what is happening at this hour". Both are a table with a value, a direction and
a source; everything else in the folder reads them and nothing else defines them.

**The five rows are one thing that runs.** In all four child categories the rows
are five parallel facts - shuffle them and you lose only rhythm. Here row 1 and
row 5 are the same fast at different hours, so the order is the content. Top to
bottom is time elapsed.

The axis is HOURS, and it was chosen against a five-decades version that did not
survive its own check. Two reasons, and the first is the one that settles it:

  - **"the lever that buys most in your 40s" cannot be sourced.** Cohort studies
    give population effect sizes, not decade-indexed rankings. Every row would
    have been refused by `refuse_unsourced` below - the concept failing the
    safety machinery it was built around
  - **four rows out of five would be addressed to somebody else.** A 35-year-old
    sees one row that is theirs. Every clip this repository makes works because
    all five apply to the viewer today, and the format's whole pull is in the
    first second and a half

Hours fix both: you pass through every row of a fast, and the thresholds are the
app's own.

## Two fields that hacks.py does not have

**`claim`.** In Biohacks every value is `measured` - a number from a study. Here
most are `described`: the app's own copy about what typically happens, which is
not a study and must not be dressed as one. So a described row **may not carry a
signed or percentage value**, and `check_value` refuses one. That is the exact
path by which a descriptive stage becomes a medical claim by accident, and it is
the only failure in this category that could reach the app's health disclaimer.

**Stage colour instead of direction.** `hacks.py` colours by whether something
rises, falls or shifts. On a fast everything is time, so that collapses; the
colour carries the stage instead, which is the vocabulary anyway.

## The summaries are verbatim and must stay that way

`STAGES` below is copied word for word from
`fitcircle/Sources/Models/Fasting.swift:219-303`, whose own comment reads:

    Phrased descriptively with "typically" / "commonly" - never as medical
    claims (see privacy policy §11 Health Disclaimer)

**Do not paraphrase them.** The compliant language IS the source. "Fat stores
typically become a primary energy source" is defensible; "burns fat from hour
12" is the same sentence with the defence removed, and rewriting for the caption
bar is how it would happen. If a summary does not fit, shorten the caption -
never the claim.

    python3 longevity.py                  the stages and the protocols
    python3 longevity.py 16_8             one protocol, and what it reaches
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = ("fitcircle/Sources/Models/Fasting.swift", "219-303 and 18-58")

# The colour of a stage. Warm while the body is still on the last meal, cooling
# as it moves onto its own stores - so the poster reads as one temperature
# falling rather than as five unrelated hues. Nothing here is the app's palette;
# the app draws its own stages and this is a video.
STAGE_COLOUR = {
    "anabolic":     (0xE8, 0x8B, 0x2E),   # still digesting
    "catabolic":    (0xD6, 0xB0, 0x3A),   # glycogen
    "fat_burning":  (0x5F, 0xB5, 0x6A),   # lipolysis
    "ketosis":      (0x3A, 0x9B, 0xC4),   # ketones
    "autophagy":    (0x6F, 0x74, 0xD6),   # clean-up
    "deep_ketosis": (0x8E, 0x5A, 0xC8),   # beyond 48 h
}

# Verbatim from Fasting.swift:232-281. `summary` is the app's one-line
# description; `detail` is its learn-more text. Neither is edited here.
STAGES = [
    dict(id="anabolic", name="Anabolic", h0=0, h1=4,
         summary="Your body is digesting your last meal.",
         detail="During the first few hours after eating, the body typically "
                "absorbs nutrients and uses glucose for energy."),
    dict(id="catabolic", name="Catabolic", h0=4, h1=12,
         summary="Stored glycogen typically becomes the main fuel.",
         detail="Once digestion finishes, the body commonly switches to drawing "
                "on stored glycogen for energy."),
    dict(id="fat_burning", name="Fat Burning", h0=12, h1=16,
         summary="Fat stores typically become a primary energy source.",
         detail="When glycogen reserves run lower, the body commonly increases "
                "lipolysis — releasing stored fat for fuel."),
    dict(id="ketosis", name="Ketosis", h0=16, h1=24,
         summary="Ketones typically rise as a fuel source.",
         detail="Extended fasting commonly leads to ketone production from fat "
                "metabolism. Levels vary widely between individuals."),
    dict(id="autophagy", name="Autophagy", h0=24, h1=48,
         summary="Cellular clean-up is typically more active.",
         detail="Longer fasts have been associated with autophagy — the cellular "
                "process of recycling damaged components. Research is ongoing."),
    dict(id="deep_ketosis", name="Deep ketosis", h0=48, h1=None,
         summary="Prolonged ketosis. Consult a clinician for fasts this long.",
         detail="Fasts beyond 48 hours are advanced and should be undertaken "
                "only with appropriate guidance."),
]

# Verbatim from Fasting.swift:18-58.
PROTOCOLS = [
    dict(id="13_11", name="13:11", fast=13, eat=11, summary="A gentle starting protocol."),
    dict(id="14_10", name="14:10", fast=14, eat=10, summary="An easy daily reset."),
    dict(id="16_8", name="16:8", fast=16, eat=8, summary="The most popular intermittent fast."),
    dict(id="18_6", name="18:6", fast=18, eat=6, summary="A focused six-hour eating window."),
    dict(id="20_4", name="20:4", fast=20, eat=4, summary="Advanced — one tight eating window."),
    dict(id="23_1", name="OMAD (23:1)", fast=23, eat=1, summary="One meal a day."),
]

_signed = re.compile(r"[%+]|(?<![A-Za-z])-\d")


def stage_at(hours):
    """The stage a fast is in at `hours`. The app's own lookup, in Python:
    half-open intervals, and the last stage is open-ended."""
    h = max(0.0, float(hours))
    for s in STAGES:
        if s["h1"] is None:
            if h >= s["h0"]:
                return s
        elif s["h0"] <= h < s["h1"]:
            return s
    return STAGES[0]


def protocol(pid):
    for p in PROTOCOLS:
        if p["id"] == pid or p["name"] == pid:
            return p
    raise SystemExit(f"no protocol '{pid}' - one of "
                     f"{', '.join(p['id'] for p in PROTOCOLS)}")


def check_value(row):
    """A described row may not carry a signed or percentage number.

    This is the whole safety case of the category in four lines. A stage's
    summary is the app's descriptive copy - "fat stores typically become a
    primary energy source" - and it is defensible precisely because it does not
    quantify. Put `-18%` on the dial beside it and the row has made a medical
    claim that nothing in the app supports, in the same frame as the app's own
    words, which is worse than making it alone.

    A `measured` row may carry any number it likes, because it arrived with a
    study attached. That is what `measured` means.
    """
    if row.get("claim") == "described" and _signed.search(str(row.get("value", ""))):
        raise SystemExit(
            f"'{row.get('name', '?')}' is a described row and its value is "
            f"'{row['value']}'. A described row takes its words from the app's "
            f"own copy, which does not quantify - so it may not carry a signed "
            f"or percentage number. Either give it a measured source, or make "
            f"the value plain (an hour, a stage name, a duration).")
    return row


def refuse_unsourced(row):
    """No source, no row. Taken whole from `hacks.resolve`, which is the reason
    the Biohacks category can put numbers on a health brand's feed at all."""
    if not row.get("source"):
        raise SystemExit(f"'{row.get('name', '?')}' has no source. Every value on "
                         f"screen carries where it came from - a study for a "
                         f"measured row, {SOURCE[0]} for a described one.")
    if row.get("claim") not in ("measured", "described"):
        raise SystemExit(f"'{row.get('name', '?')}' has claim "
                         f"'{row.get('claim')}'; it is 'measured' or 'described'")
    return row


def rows_for(pid, table=None, rows=5):
    """The rows of a protocol's poster, each carrying whether the fast reaches it.

    **No protocol reaches five stages**, which is the first thing writing this
    file found and it changes the shape. 13:11 through 16:8 reach three;
    18:6 through OMAD reach four. Only a fast past 24 h reaches five, and the
    stage after that is the one whose own summary says *consult a clinician* -
    so five-rows-are-five-stages cannot be a routine topic.

    Two ways out and they are not equivalent:

      - five evenly spaced hour marks (0, 4, 8, 12, 16 for a 16:8), each
        labelled with the stage it falls in. Every protocol gives exactly five
        rows. It also puts two rows in the same stage - 4 h and 8 h are both
        catabolic - and a poster with a repeated caption is a poster the eye
        stops reading, which this repository has already learned once
      - **five stages, with the ones beyond the fast drawn UNREACHED.** A 16:8
        lights three rows and leaves two dim; a 20:4 lights four. The gap is the
        content: it is what a longer protocol buys, shown rather than argued,
        and it is the day bar's four-fifths-full idea applied to a whole poster

    The second is what `reached` is for. Showing an unreached stage is not
    claiming it - the row says the fast stops before here, which is the opposite
    of a claim - and it is the only version where the six protocols compare.

    `rows` is a cap rather than a target: five of the six stages, because the
    sixth is the clinician one.
    """
    p = protocol(pid)
    shown = [s for s in STAGES if s["id"] != "deep_ketosis"][:rows]
    out = []
    for s in shown:
        out.append(check_value(refuse_unsourced(dict(
            id=s["id"], name=s["name"], stage=s["id"],
            hour=s["h0"], value=f"{int(s['h0'])} H",
            metric=s["name"].upper(), summary=s["summary"],
            claim="described", reached=s["h0"] < p["fast"],
            colour=STAGE_COLOUR[s["id"]],
            source=f"{SOURCE[0]}:{SOURCE[1]}, verbatim"))))
    return p, out


def main():
    if len(sys.argv) > 1:
        p, rows = rows_for(sys.argv[1])
        print(f"\n{p['name']}  -  {p['summary']}")
        print(f"  {p['fast']} h fasting, {p['eat']} h eating\n")
        hit = [r for r in rows if r["reached"]]
        print(f"  lights {len(hit)} of {len(rows)} rows:\n")
        for r in rows:
            mark = "  " if r["reached"] else "  ·"
            print(f"  {mark} {r['value']:>5}  {r['metric']:<13} "
                  f"{r['summary'] if r['reached'] else '(the fast stops before here)'}")
        print(f"\n  · = drawn but not reached. Showing it is not claiming it -")
        print(f"    the row says the fast stops short, which is the opposite.")
        return
    print(f"six stages, verbatim from {SOURCE[0]}\n")
    for s in STAGES:
        end = f"-{int(s['h1'])}" if s["h1"] else "+"
        print(f"  {str(int(s['h0'])) + end:>7} h  {s['name']:<13} {s['summary']}")
    print(f"\nsix protocols, and how far each one gets\n")
    for p in PROTOCOLS:
        _, rows = rows_for(p["id"])
        hit = [r for r in rows if r["reached"]]
        print(f"  {p['name']:<12} {p['fast']:>2} h  ->  {hit[-1]['metric'].lower():<12}"
              f"  {len(hit)}/{len(rows)} rows lit")
    print("\nEvery row above is `described`: the words are the app's and carry no")
    print("number, which is what makes them defensible. check_value refuses a")
    print("described row that has grown a percentage.")


if __name__ == "__main__":
    main()
