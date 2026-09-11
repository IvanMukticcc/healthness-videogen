#!/usr/bin/env python3
"""
micro_result.py - the app's own micronutrient maths, for act two.

Act one names five foods. Act two says what they add up to, and the number it
says has to be the number the app would say - otherwise the clip is a drawing of
the app rather than the app. So nothing here is invented:

  goals      Sources/Models/MicronutrientGoals.swift   NIH DRI by sex and age
  groups     Sources/Models/MicronutrientType.swift    which colour a row takes
  score      Sources/Models/MicroState.swift:122       mean of the targets,
                                                       minus 0.1 per limit blown
  amounts    Resources/en.lproj/foods.json             per 100 g, USDA-backed

Three things about the score are easy to get wrong and all three are the app's:

1. **It is not an average of everything.** Sugar and sodium are limits, not
   targets. They never raise the score; going over either costs a flat 0.1. A
   plate can be perfect on sixteen targets and still show 80%.
2. **A nutrient with no data is skipped, not zeroed** - when food was logged.
   `progress(type)` returns nil for an unknown nutrient and the loop appends
   nothing. Zeroing them would punish a plate for the database's gaps.
3. **Below 30% coverage the app refuses to score at all** (`coverageThreshold`),
   because a low number there reads as a deficiency rather than as "we don't
   know". A clip whose foods are all in the database is at 100% coverage, but
   the guard is here so the one case that would lie cannot.

`Gender.none` is a real case in the app and it is the one a video wants: it
averages the male and female goal for every nutrient, so the clip does not
address half its audience with the other half's iron.

    python3 micro_result.py --find beetroot          # ids, to fill meals.json
    python3 micro_result.py --topic pressure         # the whole result
    python3 micro_result.py --topic pressure --json  # for the overlay
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MEALS = os.path.join(HERE, "meals.json")
# The app's own food table, read from the app rather than copied here: these
# numbers move when the app's data moves, and a stale copy would be a clip
# quoting a number the app no longer shows. --foods overrides it.
FOODS = os.path.expanduser(
    "~/Documents/test/fitcircle/Resources/en.lproj/foods.json")

# MicronutrientType.swift, in its own order: the eighteen, their group, their
# unit and whether the goal is something to reach or something to stay under.
TARGET, LIMIT = "target", "limit"
VIT, MIN, OTH = "vitamins", "minerals", "other"
TYPES = [
    # key            label        group unit    kind
    ("fiber",       "Fibre",      OTH, "g",   TARGET),
    ("sugar",       "Sugar",      OTH, "g",   LIMIT),
    ("sodium",      "Sodium",     OTH, "mg",  LIMIT),
    ("potassium",   "Potassium",  MIN, "mg",  TARGET),
    ("calcium",     "Calcium",    MIN, "mg",  TARGET),
    ("iron",        "Iron",       MIN, "mg",  TARGET),
    ("magnesium",   "Magnesium",  MIN, "mg",  TARGET),
    ("zinc",        "Zinc",       MIN, "mg",  TARGET),
    ("vitaminA",    "Vitamin A",  VIT, "µg",  TARGET),
    ("vitaminC",    "Vitamin C",  VIT, "mg",  TARGET),
    ("vitaminD",    "Vitamin D",  VIT, "µg",  TARGET),
    ("vitaminE",    "Vitamin E",  VIT, "mg",  TARGET),
    ("vitaminK",    "Vitamin K",  VIT, "µg",  TARGET),
    ("thiamin",     "B1",         VIT, "mg",  TARGET),
    ("riboflavin",  "B2",         VIT, "mg",  TARGET),
    ("vitaminB6",   "B6",         VIT, "mg",  TARGET),
    ("vitaminB12",  "B12",        VIT, "µg",  TARGET),
    ("folate",      "Folate",     VIT, "µg",  TARGET),
]
BY_KEY = {t[0]: t for t in TYPES}

# The three family colours, sampled off the app's Micronutrients screen. They
# are micro_icons.py's FAMILY, deliberately: the badges that pop in act one and
# the ring that fills in act two are then the same blue, green and orange, and a
# viewer who has the app recognises the ring before reading a word of it.
COLOUR = {VIT: "#3E85F6", MIN: "#69C66C", OTH: "#EF9749"}

COVERAGE_THRESHOLD = 0.3       # MicroState.coverageThreshold
LIMIT_PENALTY = 0.1            # per limit nutrient exceeded


def goal(key, age=30, gender="none"):
    """MicronutrientGoals.dailyGoal, ported whole. gender: male|female|none."""
    if gender == "none":
        return (goal(key, age, "male") + goal(key, age, "female")) / 2
    m = gender == "male"
    if key == "fiber":      return (30 if age >= 51 else 38) if m else (21 if age >= 51 else 25)
    if key == "sugar":      return 50
    if key == "sodium":     return 2300
    if key == "potassium":  return 3400 if m else 2600
    if key == "calcium":    return (1200 if age >= 71 else 1000) if m else (1200 if age >= 51 else 1000)
    if key == "iron":       return 8 if m else (8 if age >= 51 else 18)
    if key == "magnesium":  return (420 if age >= 31 else 400) if m else (320 if age >= 31 else 310)
    if key == "zinc":       return 11 if m else 8
    if key == "vitaminA":   return 900 if m else 700
    if key == "vitaminC":   return 90 if m else 75
    if key == "vitaminD":   return 20 if age >= 71 else 15
    if key == "vitaminE":   return 15
    if key == "vitaminK":   return 120 if m else 90
    if key == "thiamin":    return 1.2 if m else 1.1
    if key == "riboflavin": return 1.3 if m else 1.1
    if key == "vitaminB6":  return (1.7 if age >= 51 else 1.3) if m else (1.5 if age >= 51 else 1.3)
    if key == "vitaminB12": return 2.4
    if key == "folate":     return 400
    raise KeyError(key)


def load_foods(path=FOODS):
    if not os.path.exists(path):
        raise SystemExit(f"the app's foods.json is not at {path} - pass --foods")
    with open(path) as fh:
        return json.load(fh)


def find(foods, needle):
    n = needle.lower()
    return [f for f in foods if n in f["name"].lower()]


def total(meal, foods):
    """Sum a meal's micros. Every food in foods.json is per 100 g.

    Returns (totals, coverage, rows). A nutrient absent from every food stays
    absent from `totals` rather than arriving as 0 - the app's nil, and the
    difference between "none of it" and "nobody measured".
    """
    by_id = {f["id"]: f for f in foods}
    totals, known_cal, all_cal, rows = {}, 0.0, 0.0, []
    for item in meal:
        f = by_id.get(item["id"])
        if f is None:
            raise SystemExit(f"no food with id {item['id']} in foods.json")
        g = item["grams"] / 100.0
        cal = (f.get("calories") or 0) * g
        all_cal += cal
        micros = f.get("micros") or {}
        if micros:
            known_cal += cal
        for k, v in micros.items():
            if k in BY_KEY and v is not None:
                totals[k] = totals.get(k, 0.0) + v * g
        rows.append({"id": f["id"], "name": f["name"], "grams": item["grams"],
                     "calories": round(cal, 1), "label": item.get("label", f["name"])})
    coverage = (known_cal / all_cal) if all_cal else 0.0
    return totals, coverage, rows


def score(totals, coverage, age=30, gender="none", has_logged_food=True):
    """MicroState.score. Returns None where the app returns nil."""
    if not totals:
        return None
    scores_every_target = not has_logged_food
    if not scores_every_target and coverage < COVERAGE_THRESHOLD:
        return None
    ratios, penalty = [], 0.0
    for key, _lbl, _grp, _unit, kind in TYPES:
        g = goal(key, age, gender)
        have = totals.get(key)
        if kind == TARGET:
            if have is not None and g > 0:
                ratios.append(min(have / g, 1.0))
            elif scores_every_target:
                ratios.append(0.0)
        else:
            if have is not None and g > 0 and have / g > 1:
                penalty += LIMIT_PENALTY
    if not ratios:
        return None
    return max(0.0, sum(ratios) / len(ratios) - penalty)


def rings(totals, age=30, gender="none"):
    """Per-group completion, for the segmented ring: each group's mean
    min(progress, 1) over the targets it actually carries, plus how many of its
    nutrients had data. Limits are excluded - they do not fill anything."""
    out = {}
    for grp in (VIT, MIN, OTH):
        vals = [min(totals[k] / goal(k, age, gender), 1.0)
                for k, _l, g, _u, kind in TYPES
                if g == grp and kind == TARGET and totals.get(k) is not None]
        n = len([1 for _k, _l, g, _u, kind in TYPES if g == grp and kind == TARGET])
        out[grp] = {"value": (sum(vals) / len(vals)) if vals else 0.0,
                    "known": len(vals), "of": n, "colour": COLOUR[grp]}
    return out


def lines(totals, age=30, gender="none"):
    """Every nutrient with data, as the screen would list it."""
    out = []
    for key, label, grp, unit, kind in TYPES:
        have = totals.get(key)
        if have is None:
            continue
        g = goal(key, age, gender)
        out.append({"key": key, "label": label, "group": grp, "unit": unit,
                    "kind": kind, "amount": have, "goal": g,
                    "pct": (have / g) if g else 0.0, "colour": COLOUR[grp]})
    return out


def attention(ls):
    """MicroState.attentionNutrients: blown limits first, then the lowest
    targets, three of them."""
    over = sorted([l for l in ls if l["kind"] == LIMIT and l["pct"] > 1],
                  key=lambda l: -l["pct"])
    low = sorted([l for l in ls if l["kind"] == TARGET], key=lambda l: l["pct"])
    return (over + low)[:3]


def result(topic, age=30, gender="none", foods_path=FOODS, meals_path=MEALS):
    with open(meals_path) as fh:
        meals = json.load(fh)
    if topic not in meals:
        raise SystemExit(f"{topic} is not in {os.path.basename(meals_path)} - "
                         f"have: {', '.join(sorted(k for k in meals if not k.startswith('_')))}")
    meal = meals[topic]["foods"]
    foods = load_foods(foods_path)
    totals, coverage, rows = total(meal, foods)
    ls = lines(totals, age, gender)
    return {
        "topic": topic,
        "title": meals[topic].get("title", topic),
        "rows": rows,
        "coverage": coverage,
        "calories": round(sum(r["calories"] for r in rows)),
        "score": score(totals, coverage, age, gender),
        "rings": rings(totals, age, gender),
        "lines": ls,
        "attention": attention(ls),
        "age": age, "gender": gender,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--topic")
    p.add_argument("--find", help="search the app's food table by name")
    p.add_argument("--age", type=int, default=30)
    p.add_argument("--gender", default="none", choices=["male", "female", "none"])
    p.add_argument("--foods", default=FOODS)
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    if a.find:
        for f in find(load_foods(a.foods), a.find)[:20]:
            n = len(f.get("micros") or {})
            print(f"  {f['id']:5d}  {f['name'][:44]:44} {f.get('calories', 0):6.0f} kcal/100g  "
                  f"{n:2d} micros")
        return
    if not a.topic:
        raise SystemExit("--topic or --find")

    r = result(a.topic, a.age, a.gender, a.foods)
    if a.json:
        json.dump(r, sys.stdout, indent=1)
        print()
        return

    print(f"{r['title']}  ({r['topic']})   {r['calories']} kcal, "
          f"coverage {r['coverage'] * 100:.0f}%   goals: {a.gender}, {a.age}")
    for row in r["rows"]:
        print(f"  {row['grams']:5.0f} g  {row['label'][:28]:28} {row['name'][:30]:30} "
              f"{row['calories']:6.1f} kcal")
    print()
    for grp in (VIT, MIN, OTH):
        g = r["rings"][grp]
        print(f"  {grp:9} {g['value'] * 100:5.1f}%   {g['known']}/{g['of']} measured   {g['colour']}")
    print()
    for l in r["lines"]:
        bar = "#" * int(min(l["pct"], 1) * 20)
        flag = "  OVER" if l["kind"] == LIMIT and l["pct"] > 1 else ""
        print(f"  {l['label']:10} {l['amount']:8.1f} {l['unit']:2} of {l['goal']:7.1f}  "
              f"{l['pct'] * 100:5.0f}%  {bar:20}{flag}")
    print()
    s = r["score"]
    print(f"  MIKRO REZULTAT: {'-' if s is None else f'{s * 100:.0f}%'}"
          f"     (mean of the targets with data, minus 0.1 per limit over)")
    print(f"  worth surfacing: {', '.join(l['label'] for l in r['attention'])}")


if __name__ == "__main__":
    main()
