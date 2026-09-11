#!/usr/bin/env python3
"""foods.py - the numbers on screen, taken from the app's own database.

Every figure a Macro clip shows is a fact about a food, and the app already
holds all of them: `fitcircle/Resources/en.lproj/foods.json`, 2272 foods, each
carrying calories, carbs, protein and fat per 100 g, a `dataSource` and - for
the ones that came from USDA FoodData Central - an `fdcId`.

WHY IT READS THE APP'S FILE RATHER THAN A LIST OF ITS OWN

Because the clip advertises the app. A viewer who looks up Greek yogurt in
Healthness after watching a Macro clip has to see the number the clip showed
them. A second copy of nutrition data, however carefully typed, is a promise
that those two numbers will drift - and the day they drift is the day the clip
is an advertisement for a product that disagrees with it.

So this is the same shape as `Longevity/work/fasting.py`: extract from the app,
cache as `macros.json`, and let `check.py` re-extract and compare. The cache is
what renders read, so a render works with no app checkout; the comparison is
what stops the cache quietly becoming fiction.

THE REFUSAL

`dataSource` is `usda` for most foods and `estimate` for some - "Greek salad"
is an estimate, "Greek yogurt" is USDA 330137. An estimate is fine in an app,
where it is one row among thousands and the user is logging their own lunch. It
is not fine at 1080x1920 with nothing else on screen. **A Macro row shows one
number very large, so the food behind it must be sourced.**

    ./foods.py "Greek yogurt"                       one food
    ./foods.py --meal "200 Greek yogurt,80 Blueberries,20 Honey,60 Oats"
    ./foods.py --refresh                            rewrite macros.json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "macros.json")

# Five levels up from Macro/work lands on Documents/test, where fitcircle sits
# beside Healtness. Resolved rather than absolute, so another checkout finds it.
APP = os.path.normpath(os.path.join(
    HERE, "..", "..", "..", "..", "..",
    "fitcircle", "Resources", "en.lproj", "foods.json"))

KEEP = ("id", "name", "calories", "carbs", "protein", "fat",
        "category", "dataSource", "fdcId")


def extract(path=APP):
    """The app's foods, trimmed to what a clip can show and prove."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out = []
    for f in raw:
        if not all(k in f for k in ("name", "calories", "carbs", "protein", "fat")):
            continue
        out.append({k: f.get(k) for k in KEEP})
    return {"source": os.path.relpath(path, HERE), "foods": out}


def _load():
    if not os.path.exists(CACHE):
        raise SystemExit(f"no {os.path.basename(CACHE)}. Run ./foods.py --refresh "
                         f"with the app checked out at {APP}")
    return json.load(open(CACHE, encoding="utf-8"))


_DATA = None


def all_foods():
    global _DATA
    if _DATA is None:
        _DATA = _load()
    return _DATA["foods"]


def find(name):
    """Exact name first, then unique case-insensitive prefix, then unique substring.

    Deliberately refuses an ambiguous match instead of picking the first. "Oat"
    matches Oats, Oatmeal and Oat milk, and those are 379, 76 and 46 kcal - a
    silent pick among them is a wrong number on screen with nothing to notice it
    by.
    """
    foods = all_foods()
    n = name.strip().lower()
    exact = [f for f in foods if f["name"].lower() == n]
    if len(exact) == 1:
        return exact[0]
    for pick in (lambda f: f["name"].lower().startswith(n),
                 lambda f: n in f["name"].lower()):
        hits = [f for f in foods if pick(f)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            names = ", ".join(sorted(h["name"] for h in hits)[:8])
            raise SystemExit(f"'{name}' matches {len(hits)} foods: {names}"
                             f"{' ...' if len(hits) > 8 else ''}. Use the full name.")
    raise SystemExit(f"no food called '{name}' in the app's database")


def refuse_unsourced(f):
    """No USDA id, no row. See the module docstring for why this is stricter
    than the app itself needs to be."""
    if f.get("dataSource") != "usda" or not f.get("fdcId"):
        raise SystemExit(
            f"'{f['name']}' is dataSource={f.get('dataSource')!r} with "
            f"fdcId={f.get('fdcId')!r}. A Macro row puts one number on screen at "
            f"full size, so the food behind it carries a USDA id or it does not "
            f"ship. Pick a sourced food, or drop the row.")
    return f


def source_line(f):
    return f"USDA FoodData Central, FDC {f['fdcId']}"


# Atwater's factors: a gram of carbohydrate or protein carries 4 kcal, a gram of
# fat 9. Kept here as well as in macro_overlay because both need it and neither
# should be the other's dependency for three numbers that have not moved since
# 1900. If a third caller appears, it moves to one of them and the other imports.
ATWATER = {"carbs": 4.0, "protein": 4.0, "fat": 9.0}


def dominant(f):
    """Which macro this food's calories mostly are - the caption for the ring.

    The ring already shows the split; this names it, so a viewer who reads the
    words and not the colours gets the same fact. Under half and it is MIXED,
    because "mostly" about a 44% share is a word doing more work than the number
    behind it.
    """
    e = {k: f[k] * v for k, v in ATWATER.items()}
    total = sum(e.values())
    if total <= 0:
        return "MIXED", 0.0
    key = max(e, key=e.get)
    share = e[key] / total
    return (f"MOSTLY {key.upper()}" if share >= 0.5 else "MIXED"), share


def labels_for(names):
    """The add_labels string for act one: the food, and what its calories are.

    Built from the database rather than typed, for the reason every cue file in
    this repository exists: the alternative is the same fact written twice and
    free to disagree with itself.
    """
    out = []
    for n in names:
        f = refuse_unsourced(find(n))
        d, _ = dominant(f)
        out.append(f"{caption_name(f['name'])}|{d}")
    return ",".join(out)


def caption_name(name):
    """The database name, safe to put in add_labels' comma-separated string.

    `add_labels.py` takes one argument - five `FOOD|SIDE` pairs joined by
    commas - and parses it with a bare `split(",")`. There is no escape and no
    other input, so a caption may not contain a comma. That is the engine's
    contract and it is this folder's job not to violate it.

    442 of the app's 2272 foods have a comma in the name and every one of them
    is USDA-sourced, so every one can legitimately reach a Macro row: "Bell
    pepper, red", "Apple, with skin", "Anchovy, canned in olive oil". A fifth of
    the database. The first to arrive was bell pepper on the sandwich topic, and
    it failed loudly - "6 label pairs for 5 rows" - which is the good case. The
    quiet one is a name whose comma splits it into a pair that still parses.

    The comma is dropped rather than the words reordered. USDA writes the
    qualifier last, so "Bell pepper, red" would read better as "RED BELL PEPPER"
    - but the same rule turns "Apple, with skin" into "WITH SKIN APPLE", and a
    transform that is right on one pattern and wrong on the next is worse than
    one that is plain everywhere. Dropping the comma leaves BELL PEPPER RED and
    APPLE WITH SKIN, both of which read, and neither of which invents or
    reorders anything the database said.
    """
    return name.replace(",", "").upper()


def portion(name, grams):
    """One food at a real weight - what act two is made of."""
    f = refuse_unsourced(find(name))
    k = grams / 100.0
    return {"name": f["name"], "grams": float(grams), "fdcId": f["fdcId"],
            "kcal": f["calories"] * k, "carbs": f["carbs"] * k,
            "protein": f["protein"] * k, "fat": f["fat"] * k}


def meal(items):
    """items: [(name, grams), ...] -> the portions and their totals.

    The totals are summed from the portions and never carried separately. A
    meal whose parts do not add up to its own total is the one arithmetic
    failure a viewer can check with a phone calculator.
    """
    rows = [portion(n, g) for n, g in items]
    tot = {k: sum(r[k] for r in rows) for k in ("kcal", "carbs", "protein", "fat")}
    return rows, tot


def parse_meal(spec):
    """'200 Greek yogurt,80 Blueberries' -> [('Greek yogurt', 200.0), ...]"""
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        head, _, rest = part.partition(" ")
        g = head.rstrip("g").rstrip()
        try:
            grams = float(g)
        except ValueError:
            raise SystemExit(f"'{part}' does not start with a weight in grams")
        if not rest.strip():
            raise SystemExit(f"'{part}' has a weight and no food")
        out.append((rest.strip(), grams))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", nargs="?", help="a food to look up")
    ap.add_argument("--meal", help="'200 Greek yogurt,80 Blueberries,20 Honey'")
    ap.add_argument("--refresh", action="store_true", help="rewrite macros.json from the app")
    ap.add_argument("--labels", help="five food names -> the add_labels string")
    a = ap.parse_args()

    if a.refresh:
        if not os.path.exists(APP):
            raise SystemExit(f"the app is not checked out at {APP}")
        d = extract()
        json.dump(d, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        usda = sum(1 for f in d["foods"] if f.get("dataSource") == "usda" and f.get("fdcId"))
        print(f"{len(d['foods'])} foods -> {os.path.basename(CACHE)}  "
              f"({usda} USDA-sourced, {len(d['foods']) - usda} not usable by a clip)")
        return 0

    if a.labels:
        print(labels_for([n.strip() for n in a.labels.split(",") if n.strip()]))
        return 0

    if a.meal:
        rows, tot = meal(parse_meal(a.meal))
        for r in rows:
            print(f"  {r['grams']:6.0f} g  {r['name']:<24} {r['kcal']:7.1f} kcal  "
                  f"C {r['carbs']:6.1f}  P {r['protein']:6.1f}  F {r['fat']:6.1f}   FDC {r['fdcId']}")
        print(f"  {'':6}    {'TOTAL':<24} {tot['kcal']:7.1f} kcal  "
              f"C {tot['carbs']:6.1f}  P {tot['protein']:6.1f}  F {tot['fat']:6.1f}")
        e = tot["carbs"] * 4 + tot["protein"] * 4 + tot["fat"] * 9
        print(f"  macros account for {e:.0f} kcal against {tot['kcal']:.0f} stated "
              f"({100 * e / tot['kcal'] - 100:+.1f}%)")
        return 0

    if not a.name:
        ap.print_help()
        return 1
    f = refuse_unsourced(find(a.name))
    print(f"  {f['name']}  ({f.get('category')})")
    print(f"  per 100 g: {f['calories']:.0f} kcal   C {f['carbs']:.1f} g   "
          f"P {f['protein']:.1f} g   F {f['fat']:.1f} g")
    print(f"  {source_line(f)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
