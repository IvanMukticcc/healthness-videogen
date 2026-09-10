#!/usr/bin/env python3
"""dailygoal.py - whose day is this?

Named `profile.py` for about an hour, which shadows the stdlib `profile`
module - the same fault as `copy.py` on 8 September, which broke four variants
for half an hour because every tool importing scipy failed at import time
saying nothing about the file that caused it. `engine-status.sh` grew a check
for exactly this after that, and it caught this one. I had simply not run it
after adding the file, which is the only reason it survived an hour. The app's own goal, for a stated person.

Act two used to measure a meal against the EU reference intake: 2000 kcal, C
260, P 50, F 70. That is the labelling yardstick and it is honest, but it is not
what the app shows anybody. A viewer who opens Healthness sees a goal computed
from their body, and a clip that measures the same food against a different
denominator is advertising a product it disagrees with - which is exactly the
argument that put `foods.py` on the app's own database.

THE CHAIN, AND WHERE EACH LINK LIVES

    BodyEnergy.basalRate         10*kg + 6.25*cm - 5*age, +5 male / -161 female
    BodyEnergy.manualTDEE        basalRate * Activity.activityFactor
    BodyEnergy.dailyCalorieGoal  tdee * FitnessGoal.dailyCalorieFactor
    User.dailyCarbsGoal          kcal * carbsRatio / 4
    User.dailyProteinGoal        weight * proteinRatio
    User.dailyFatGoal            kcal * fatRatio / 9

Adults get Mifflin-St Jeor; under 18 is Schofield, which is weight-only and the
accepted equation for 10-17 year olds. Both are in `BodyEnergy.swift`, whose own
comment records that this used to live in four places with three different sets
of numbers.

**PROTEIN IS GRAMS PER KILOGRAM AND DOES NOT COME OFF THE CALORIE GOAL.** Carbs
and fat are shares of the daily calories; protein is bodyweight times a factor.
So the three goals do not add up to the calorie goal and are not meant to - at a
typical maintenance profile they account for about 93% of it. Anybody checking
our arithmetic with Atwater's 4/4/9 will find that gap. It is the app's design,
it is the number the user sees in the product, and `--check` prints it rather
than leaving it to be discovered.

    ./dailygoal.py --sex male --age 30 --height 172 --weight 66 --goal mild_gain
    ./dailygoal.py --verify        the constants, against the app's source
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "..", "fitcircle"))
BODY = os.path.join(APP, "Sources", "Services", "BodyEnergy.swift")
STATE = os.path.join(APP, "Sources", "Modules", "Onboarding", "OnboardingState.swift")

ACTIVITY = {"bmr": 1.0, "sedentary": 1.2, "light": 1.375, "moderate": 1.465,
            "active": 1.55, "very_active": 1.725}

# name -> (dailyCalorieFactor, carbsRatio, proteinRatio g/kg, fatRatio)
GOALS = {
    "extreme_gain": (1.32, 0.60, 2.0, 0.20),
    "gain":         (1.16, 0.55, 1.8, 0.25),
    "mild_gain":    (1.08, 0.50, 1.7, 0.25),
    "maintain":     (1.00, 0.45, 1.6, 0.25),
    "mild_loss":    (0.92, 0.40, 1.7, 0.25),
    "loss":         (0.84, 0.35, 1.8, 0.25),
    "extreme_loss": (0.68, 0.30, 2.0, 0.35),
}
GOAL_LABEL = {"extreme_gain": "EXTREME WEIGHT GAIN", "gain": "WEIGHT GAIN",
              "mild_gain": "MILD WEIGHT GAIN", "maintain": "MAINTAIN WEIGHT",
              "mild_loss": "MILD WEIGHT LOSS", "loss": "WEIGHT LOSS",
              "extreme_loss": "EXTREME WEIGHT LOSS"}


def basal_rate(weight_kg, height_cm, age, sex):
    """BodyEnergy.basalRate, transcribed."""
    if weight_kg <= 0:
        return 0.0
    if age < 18:
        return {"male": 17.686 * weight_kg + 658.2,
                "female": 13.384 * weight_kg + 692.6}.get(
                    sex, 15.535 * weight_kg + 675.4)
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + {"male": 5.0, "female": -161.0}.get(sex, -78.0)


def goals(weight_kg, height_cm, age, sex, activity="moderate", goal="maintain"):
    if goal not in GOALS:
        raise SystemExit(f"goal '{goal}' is one of {', '.join(GOALS)}")
    if activity not in ACTIVITY:
        raise SystemExit(f"activity '{activity}' is one of {', '.join(ACTIVITY)}")
    cal_f, carb_r, prot_r, fat_r = GOALS[goal]
    bmr = basal_rate(weight_kg, height_cm, age, sex)
    tdee = bmr * ACTIVITY[activity]
    kcal = round(tdee * cal_f)
    return {
        "bmr": bmr, "tdee": tdee, "kcal": float(kcal),
        "carbs": kcal * carb_r / 4.0,
        "protein": weight_kg * prot_r,
        "fat": kcal * fat_r / 9.0,
        "who": f"{sex.upper()} · {age} · {height_cm:g} CM · {weight_kg:g} KG",
        "goal": GOAL_LABEL[goal],
        "activity": activity.replace("_", " ").upper(),
    }


def verify():
    """The constants, against the app's source. Transcription is the risk here."""
    bad = []
    if not os.path.exists(BODY):
        return ["the app is not checked out at " + APP]
    body = open(BODY, encoding="utf-8").read()
    for frag in ("10 * weightKG + 6.25 * heightCM - 5 * Double(age)",
                 "17.686 * weightKG + 658.2", "13.384 * weightKG + 692.6",
                 "15.535 * weightKG + 675.4"):
        if frag not in body:
            bad.append(f"BodyEnergy.swift no longer contains: {frag}")
    if "base + 5" not in body or "base - 161" not in body or "base - 78" not in body:
        bad.append("BodyEnergy.swift's sex terms have changed")

    state = open(STATE, encoding="utf-8").read()

    def block(name):
        m = re.search(rf"var {name}: Double \{{(.*?)\n    \}}", state, re.S)
        return [float(x) for x in re.findall(r"^\s+([0-9.]+)$", m.group(1), re.M)] if m else []

    for name, idx in (("dailyCalorieFactor", 0), ("carbsRatio", 1),
                      ("proteinRatio", 2), ("fatRatio", 3)):
        found = block(name)
        want = [GOALS[k][idx] for k in ("extreme_gain", "gain", "mild_gain",
                                        "maintain", "mild_loss", "loss",
                                        "extreme_loss")]
        if found != want:
            bad.append(f"{name}: app has {found}, this file has {want}")
    found = block("activityFactor")
    want = list(ACTIVITY.values())
    if found[:len(want)] != want:
        bad.append(f"activityFactor: app has {found}, this file has {want}")
    return bad


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sex", default="male", choices=("male", "female", "none"))
    p.add_argument("--age", type=int, default=30)
    p.add_argument("--height", type=float, default=172)
    p.add_argument("--weight", type=float, default=66)
    p.add_argument("--activity", default="moderate")
    p.add_argument("--goal", default="maintain")
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()

    if a.verify:
        bad = verify()
        for b in bad:
            print(f"  {b}")
        print("  constants match the app" if not bad else "  DRIFTED")
        return 1 if bad else 0

    g = goals(a.weight, a.height, a.age, a.sex, a.activity, a.goal)
    print(f"  {g['who']} · {g['activity']} · {g['goal']}")
    print(f"  BMR {g['bmr']:.0f}  ->  TDEE {g['tdee']:.0f}  ->  goal {g['kcal']:.0f} kcal")
    print(f"  C {g['carbs']:.0f} g   P {g['protein']:.0f} g   F {g['fat']:.0f} g")
    e = g["carbs"] * 4 + g["protein"] * 4 + g["fat"] * 9
    print(f"  those macros are {e:.0f} kcal against a {g['kcal']:.0f} goal "
          f"({100 * e / g['kcal']:.0f}%) - protein is g/kg and does not come off "
          f"the calorie goal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
