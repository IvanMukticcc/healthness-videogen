#!/usr/bin/env python3
"""
hacks.py - the vocabulary. What a hack costs, what it changes, and by how much.

Everything else in this folder reads it and nothing else defines it: the dial
needs the value and its direction, the chips need the dose, the day bar needs the
clock, and the prompt needs the icon. Three modules working the same table out
for themselves is how `muscles.py` came to exist next door, and it is the same
answer here.

**The direction is the whole colour system.** A hack either raises something that
should be higher, lowers something that should be lower, or moves a clock. Three
states, three colours, and the viewer learns them in the first two rows without
being told - which is what a colour system is for.

`hacks.json` carries the numbers and the study each one came from. A number
without a source is not shipped: this is a health brand, and a claim nobody can
chase costs more than the view it buys.

    python3 hacks.py                    # what is in the table
    python3 hacks.py 'cold finish'      # one entry, with its source
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(HERE, "hacks.json")

# The three directions, in the app's own accent colours. Green when something
# rises that should rise, blue when something falls that should fall, amber when
# a clock moves. Sampled off the iOS system palette the app is built in, so a
# viewer who has Healthness on their phone recognises the language before they
# read the word under it.
#
# None of them may be a wave colour next door, in Exercise, because there the
# badge sits ON the liquid. Here it does not: the dial has its own disc over the
# right guide circle, and the chips are glass rather than coloured. So this
# variant's wave palette is free - every hue is available, which is the one
# palette freedom the other two do not have. Use it: five topics that look
# alike is five topics nobody scrolls back for.
DIR = {
    "up":   (0x32, 0xD7, 0x4B),      # something rises, and that is the win
    "down": (0x0A, 0x84, 0xFF),      # something falls, and that is the win
    "time": (0xFF, 0x9F, 0x0A),      # a clock moves
}
DIR_NAME = {"up": "rises", "down": "falls", "time": "shifts"}

_num = re.compile(r"[-+]?\d+(?:\.\d+)?")


def load(path=TABLE):
    t = json.load(open(path))
    return {k: v for k, v in t.items() if not k.startswith("_")}


def resolve(spec, table=None):
    """'auto:COLD FINISH,WALK AFTER LUNCH,...' -> one entry per row.

    `NAME@HH:MM` moves that hack's clock for this topic only. The table's clock is
    where a hack usually falls in a day, which is the right default and the wrong
    answer as soon as a topic is not a whole day: cyclic sighing is filed at 17:30
    because that is when most people need it, and in a morning protocol it belongs
    at 07:20. Without the override the day bar under a first-hour clip read 06:40,
    06:50, 07:05, 08:30, 17:30 - four moments and an outlier - and the one thing
    the bar exists to say is that these five belong to the same stretch of time.

    Longest key first, so 'MORNING LIGHT' and 'LIGHTS DOWN' do not both answer to
    'light' and leave the winner to whichever the file happens to list first -
    the same trap `micro_overlay.resolve` fell into and names in its own comment.
    """
    if not spec:
        return []
    table = table or load()
    if not spec.startswith("auto:"):
        raise SystemExit("hacks are looked up by name: 'auto:COLD FINISH,...'")
    keys = sorted(table, key=len, reverse=True)
    rows = []
    for name in spec[5:].split(","):
        name, _, clock = name.partition("@")
        key = name.strip().lower()
        hit = table.get(key)
        if hit is None:
            for k in keys:
                if k in key or key in k:
                    hit = table[k]
                    break
        if hit is None:
            raise SystemExit(f"no hack called '{name.strip()}' - add it to "
                             f"{os.path.basename(TABLE)} with a source")
        if not hit.get("source"):
            raise SystemExit(f"'{name.strip()}' has no source. Every number on "
                             f"screen carries its study; see the header of "
                             f"{os.path.basename(TABLE)}")
        h = dict(hit)
        h["name"] = name.strip().upper()
        h["key"] = key
        if clock.strip():
            clock_minutes(clock.strip())           # raises here rather than in the bar
            h["clock"] = clock.strip()
        rows.append(h)
    return rows


def colour(h):
    d = h.get("dir", "up")
    if d not in DIR:
        raise SystemExit(f"'{h.get('name')}' has dir '{d}'; it is one of "
                         f"{', '.join(DIR)}")
    return DIR[d]


def count_to(value):
    """The number a dial counts up to, and how to print it on the way.

    A dial that counts is the one thing in this repository that nothing else
    does, and it only works if the number on screen is the number at that
    instant. So the value is split into what is countable and what is furniture:
    '+250%' counts 0 -> 250 with a '+' in front and a '%' behind, and 'ALL DAY'
    does not count at all and simply arrives.

    Returns (target, fmt) or (None, None). `fmt` takes the current value and
    gives the string, keeping the sign and the unit exactly as the table wrote
    them - a '-10%' that counts down through '-3%' and not '3%' is the difference
    between a measurement and a slot machine.
    """
    m = _num.search(value or "")
    if not m:
        return None, None
    body = m.group(0)
    head, tail = value[:m.start()], value[m.end():]
    target = float(body)
    dp = len(body.split(".")[1]) if "." in body else 0
    sign = "+" if body.startswith("+") else ""

    def fmt(v, dp=dp, head=head, tail=tail, sign=sign):
        s = f"{abs(v):.{dp}f}"
        return f"{head}{sign if v >= 0 else '-'}{s}{tail}" if not head.strip("+-") \
            else f"{head}{s}{tail}"
    return target, fmt


def clock_minutes(c):
    """'06:40' -> 400. The day bar's only arithmetic."""
    h, m = c.split(":")
    return int(h) * 60 + int(m)


def main():
    table = load()
    if len(sys.argv) > 1:
        for name in sys.argv[1:]:
            h = resolve("auto:" + name)[0]
            t, f = count_to(h["value"])
            print(f"\n{h['name']}  ({h['clock']})")
            print(f"  costs    {', '.join(h['chips'])}")
            print(f"  changes  {h['metric']} {h['value']}  ({DIR_NAME[h['dir']]})"
                  f"{'  counts 0 -> ' + f(t) if t is not None else '  arrives, does not count'}")
            print(f"  icon     {h['icon']}")
            print(f"  source   {h['source']}")
        return
    print(f"{len(table)} hacks in {os.path.basename(TABLE)}\n")
    for k, v in sorted(table.items(), key=lambda kv: clock_minutes(kv[1]["clock"])):
        ok = "ok " if "Placeholder" not in v.get("source", "") else "NO "
        print(f"  {ok}{v['clock']}  {k:<20} {', '.join(v['chips']):<10} "
              f"{v['metric']:<18} {v['value']:>8}  {v['dir']}")
    print("\n'NO' means the source is not a source. Those do not ship.")


if __name__ == "__main__":
    main()
