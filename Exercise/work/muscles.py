#!/usr/bin/env python3
"""
muscles.py - the vocabulary. One place that says what a muscle is called, how
hard it is working, and which shapes on the body light up for it.

Three files read this and none of them may disagree: the badge builder needs the
label and the colour, the body map needs the regions, and the overlay needs to
know whether a row is a front view or a back view. Held in three places it
drifted within an afternoon - `Front Delts` on the badge, `front_delt` on the
body, and a row that lit nothing at all.

A muscle is written in a row as `Name` or `Name:tier`. Without a tier it takes
the one in DEFAULT_TIER below, which is what it usually is for the exercise that
names it first - so `auto:` rows come out right without spelling a tier out.

    p   primary mover     the muscle the set is for
    s   synergist         helping, and it knows it the next morning
    t   stabiliser        holding the shape while the other two work
"""

# The tier colours, shared by the badge and by the muscle on the body. That they
# are the same three values is the whole reason a viewer connects the two: a red
# ball lands saying CHEST and the chest goes red in the same frame. Split them
# into two palettes and the clip becomes two unrelated animations playing at once.
TIER = {
    "p": (0xFF, 0x45, 0x3A),     # primary mover
    "s": (0xFF, 0x9F, 0x0A),     # synergist
    "t": (0x0A, 0x84, 0xFF),     # stabiliser
}
TIER_NAME = {"p": "primary", "s": "synergist", "t": "stabiliser"}

# name -> (label on the badge, default tier, view it reads best from, body regions)
#
# `view` is a vote, not a verdict: a row shows the back only if the muscles it
# lights vote for it (see `view_for`). A row of Chest, Triceps, Front Delts is a
# front view even though the triceps would rather be seen from behind.
MUSCLES = {
    "CHEST":       ("Chest",       "p", "front", ["chest"]),
    "FRONTDELTS":  ("Front Delts", "s", "front", ["front_delt"]),
    "SIDEDELTS":   ("Side Delts",  "p", "front", ["side_delt"]),
    "REARDELTS":   ("Rear Delts",  "p", "back",  ["rear_delt"]),
    "DELTS":       ("Delts",       "p", "front", ["front_delt", "side_delt"]),
    "BICEPS":      ("Biceps",      "p", "front", ["biceps"]),
    "TRICEPS":     ("Triceps",     "p", "back",  ["triceps"]),
    "FOREARMS":    ("Forearms",    "s", "front", ["forearm"]),
    "GRIP":        ("Grip",        "t", "front", ["forearm"]),
    "LATS":        ("Lats",        "p", "back",  ["lats"]),
    "TRAPS":       ("Traps",       "s", "back",  ["traps"]),
    "RHOMBOIDS":   ("Rhomboids",   "s", "back",  ["rhomboids"]),
    "UPPERBACK":   ("Upper Back",  "p", "back",  ["traps", "rhomboids"]),
    "LOWERBACK":   ("Lower Back",  "t", "back",  ["erectors"]),
    "SPINALERECTORS": ("Erectors", "p", "back",  ["erectors"]),
    "ABS":         ("Abs",         "p", "front", ["abs"]),
    "OBLIQUES":    ("Obliques",    "s", "front", ["obliques"]),
    "CORE":        ("Core",        "t", "front", ["abs", "obliques"]),
    "SERRATUS":    ("Serratus",    "s", "front", ["serratus"]),
    "GLUTES":      ("Glutes",      "p", "back",  ["glutes"]),
    "QUADS":       ("Quads",       "p", "front", ["quads"]),
    "HAMSTRINGS":  ("Hamstrings",  "p", "back",  ["hamstrings"]),
    "ADDUCTORS":   ("Adductors",   "s", "front", ["adductors"]),
    "CALVES":      ("Calves",      "s", "back",  ["calves"]),
    "HIPFLEXORS":  ("Hip Flexors", "s", "front", ["hip_flexors"]),
    "NECK":        ("Neck",        "t", "front", ["neck"]),
    "ROTATORCUFF": ("Rotator Cuff", "t", "back", ["rear_delt"]),
    "FULLBODY":    ("Full Body",   "p", "front",
                    ["chest", "front_delt", "side_delt", "biceps", "abs",
                     "obliques", "quads", "forearm"]),
}


# What a muscle may also be called. The badge label is one of these by
# construction - `Erectors` is the label on SPINALERECTORS - so a table that
# writes what the badge says finds the muscle without having to know the key.
ALIAS = {
    "PECS": "CHEST", "PECTORALS": "CHEST",
    "ANTERIORDELTS": "FRONTDELTS", "FRONTDELT": "FRONTDELTS",
    "LATERALDELTS": "SIDEDELTS", "MEDIALDELTS": "SIDEDELTS",
    "POSTERIORDELTS": "REARDELTS",
    "SHOULDERS": "DELTS", "DELTOIDS": "DELTS",
    "LATISSIMUS": "LATS", "TRAPEZIUS": "TRAPS",
    "ERECTORS": "SPINALERECTORS", "SPINALERECTOR": "SPINALERECTORS",
    "ABDOMINALS": "ABS", "RECTUSABDOMINIS": "ABS",
    "GLUTS": "GLUTES", "QUADRICEPS": "QUADS", "HAMS": "HAMSTRINGS",
    "CALF": "CALVES", "FOREARM": "FOREARMS",
}


def key(name):
    """'Front Delts', 'front-delts' and 'FRONTDELTS' are one muscle."""
    k = "".join(ch for ch in str(name).upper() if ch.isalnum())
    return ALIAS.get(k, k)


def parse(spec):
    """'Chest:p' -> ('CHEST', 'p'). A bare name takes its default tier."""
    s = str(spec).strip()
    tier = None
    if ":" in s:
        s, tier = s.rsplit(":", 1)
        tier = tier.strip().lower()[:1]
    k = key(s)
    if k not in MUSCLES:
        raise SystemExit(f"'{spec.strip()}' is not a muscle - the vocabulary is in "
                         f"muscles.py: {', '.join(sorted(MUSCLES))}")
    if tier not in TIER:
        tier = MUSCLES[k][1]
    return k, tier


def label(k):
    return MUSCLES[k][0]


def regions(k):
    return MUSCLES[k][3]


def shows(k, view):
    """Does any part of this muscle show from that side?

    The geometry lives in bodymap, which imports this module, so the import is
    done here rather than at the top. It is the only edge between the two and
    pointing it the other way would mean the vocabulary owning the drawing.
    """
    import bodymap
    defs = bodymap.FRONT if view == "front" else bodymap.BACK
    return any(defs.get(r) for r in regions(k))


def view_for(keys):
    """Front or back, decided by what the row lights rather than by hand.

    Two questions, in this order.

    How much of the row can each side actually show? A jump rope is Calves,
    Quads, Forearms; all three read from the front and only the calves from
    behind, so it is a front view whatever the calves would prefer. Deciding on
    direction alone made 18 of the 130 lifts land a badge over a body where
    nothing happened - a dead beat in a row of three, with the hit still
    sounding under it.

    Then, only if the two sides show the same amount: which way does the row
    face? The first muscle counts triple, because it is the one the lift is for -
    so a pull-up is Lats, Biceps, Forearms and shows the back, even though two of
    those three read from the front. Ties go to the front; a viewer reads a chest
    faster than a back, and a tie means it does not matter.
    """
    weights = [(3 if i == 0 else 1) * (2 if tier == "p" else 1)
               for i, (_, tier) in enumerate(keys)]
    lit = {v: sum(w for w, (k, _) in zip(weights, keys) if shows(k, v))
           for v in ("front", "back")}
    if lit["front"] != lit["back"]:
        return "front" if lit["front"] > lit["back"] else "back"

    score = 0
    for w, (k, _) in zip(weights, keys):
        score += w if MUSCLES[k][2] == "back" else -w
    return "back" if score > 0 else "front"
