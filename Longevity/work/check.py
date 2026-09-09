#!/usr/bin/env python3
"""check.py - does this clip say only what the app says, and does it move?

Longevity's own rule is that every row carries a source and an unsourced row
does not ship. Until now nothing enforced it after a render: `longevity.py`
refuses at BUILD time, which protects the render that is about to happen and
says nothing at all about the mp4 already on disk.

WHERE THIS TAKES ITS SPEC, AND WHY IT MATTERS MORE HERE THAN ANYWHERE

From the files `render.sh` wrote, never from the command line. On 9 September
Biohacks discovered `check.py --hacks` was documented as "the same spec render.sh
was given" - a promise by whoever typed it - and verified another topic's five
numbers against the shipped `defence` clip, sources and all, CLEAN. The same
evening `Micro/work/audit.py` was measured printing `clean` from three sampled
frame pairs when the spec was omitted and `clean` from twelve when it was not,
in identical words.

So: the protocol comes from `<topic>_protocol.txt`. The flags exist for
re-checking an older clip by hand, and when one is used this says so on its own
line, because a spec that came from a person confirms nothing about a clip.

    ./check.py hour168_longevity.mp4
    ./check.py hour168                      the artwork checks, no clip needed
    ./check.py old.mp4 --protocol 16_8      an older clip, and it will say so

WHAT IT CHECKS

  sources    every row of the protocol passes the build guards again, now
             against what shipped: sourced, claim in (measured, described), no
             signed or percentage value on a described row
  verbatim   each row's summary is character-for-character the app's, AND
             fasting.json still matches Fasting.swift when re-extracted. That
             second half is the one worth having: hand-edit fasting.json and
             every other check in here still passes, because they all read it
  reached    the count of NOT REACHED rows is what the protocol's hours give.
             A row saying AUTOPHAGY over a fast that stops at 16 h is the one
             failure here that is a medical claim rather than a bug
  motion     stray movement outside the wave between badge landings, with the
             SAMPLE COUNT printed beside the verdict - `clean` from three pairs
             and `clean` from twelve are the same word about different amounts
             of looking

It fails toward alarm. Where it cannot establish something it says NOT CHECKED
and exits non-zero, rather than printing a verdict it did not earn.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import longevity                                                   # noqa: E402


def _topic(s):
    b = os.path.basename(s)
    for suf in ("_longevity.mp4", "_preview.mp4", "_silent.mp4", ".mp4"):
        if b.endswith(suf):
            return b[: -len(suf)]
    return b


def spec(topic, flag, kind):
    """The protocol, and an honest sentence about where it came from."""
    path = os.path.join(HERE, f"{topic}_{kind}.txt")
    if flag:
        on_disk = open(path).read().strip() if os.path.exists(path) else None
        note = f"  {kind} from --{kind} ({flag})"
        if on_disk and on_disk != flag:
            note += f"\n  ON DISK IT IS {on_disk} - render.sh was given something else"
        elif not on_disk:
            note += "\n  nothing on disk confirms this is the clip's"
        return flag, note
    if os.path.exists(path):
        return open(path).read().strip(), f"  {kind} from {topic}_{kind}.txt (what render.sh was given)"
    return None, (f"  NO {topic}_{kind}.txt. Re-render, or pass --{kind} and accept "
                  f"that nothing then ties the spec to the clip.")


def sources(rows):
    """The build guards, re-run against what shipped. They exit on failure."""
    for r in rows:
        longevity.check_value(longevity.refuse_unsourced(r))
    return len(rows)


def verbatim(rows):
    """Two halves, and only the second is load-bearing.

    Comparing each row's summary against `STAGES` catches little, because
    `rows_for` builds the row FROM `STAGES` - both sides move together. It
    survives because one path does not: a `rows_for` that ever transforms the
    text on its way in (`.title()`, a truncation, an f-string) breaks that
    equality, and that is precisely how a verbatim quote stops being one.

    The half that can catch a real edit is the second: re-extract
    `Fasting.swift` and compare it with `fasting.json`. Hand-edit the json and
    every other check in this file still passes, because they all read it.
    """
    bad = []
    by_id = {s["id"]: s for s in longevity.STAGES}
    for r in rows:
        want = by_id[r["stage"]]["summary"]
        if r["summary"] != want:
            bad.append(f"{r['name']}: summary is not the app's copy")

    import fasting
    if not os.path.exists(fasting.SWIFT):
        bad.append("app source not on this machine - fasting.json NOT CHECKED "
                   "against it, so 'verbatim' here means only that the rows match "
                   "the json they were built from")
        return bad, "NOT CHECKED against the app"
    fresh = fasting.extract()
    live = {s["id"]: s for s in fresh["stages"]}
    for sid, s in by_id.items():
        f = live.get(sid)
        if f is None:
            bad.append(f"{sid}: no longer in Fasting.swift")
        elif f["summary"] != s["summary"]:
            bad.append(f"{sid}: fasting.json disagrees with Fasting.swift")
    where = os.path.relpath(fasting.SWIFT, HERE)
    return bad, (f"fasting.json matches {where}" if not bad
                 else f"{len(bad)} disagreement(s) with {where}")


def reached(pid, rows):
    """Two comparisons, and only the first of them is worth much.

    Counting `hour > fast` and counting NOT REACHED labels is the SAME predicate
    computed twice - they drift together and catch nothing, which is what the
    first version of this function did. The load-bearing one is against
    `stage_at`, an independent transcription of the app's own half-open lookup
    (`safeHours >= startHour && safeHours < endHour`): the last lit row must be
    the stage the APP reports at this protocol's hours. That is the comparison
    that would have caught the `<` which lit three rows for a 16:8 and told its
    user the fast stopped before the hour it ends on.

    The count survives as the weaker second check, because it does catch
    `labels_for` drifting from `rows_for` - a real regression, just a smaller one.
    """
    p = longevity.protocol(pid)
    lit = [r for r in rows if r["reached"]]
    app = longevity.stage_at(p["fast"])
    agrees = bool(lit) and lit[-1]["stage"] == app["id"]

    want = sum(1 for r in rows if r["hour"] > p["fast"])
    got = sum(1 for l in longevity.labels_for(pid).split(",") if l.endswith("NOT REACHED"))
    return p, [r["name"] for r in lit], app, agrees, want, got


def frames(path, t, w, h):
    import numpy as np
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True).stdout
    if len(raw) < w * h * 3:
        return None
    return np.frombuffer(raw[: w * h * 3], "u1").reshape(h, w, 3).astype("i2")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clip", help="the mp4, or just the topic for the artwork checks")
    ap.add_argument("--protocol", help="override; only for re-checking an older clip")
    ap.add_argument("--tol", type=int, default=10)
    ap.add_argument("--slack", type=int, default=15)
    a = ap.parse_args()

    topic = _topic(a.clip)
    clip = a.clip if a.clip.endswith(".mp4") and os.path.exists(a.clip) else None
    print(f"{topic}" + (f"  {os.path.relpath(clip, HERE)}" if clip else "  (no clip - artwork checks only)"))

    pid, note = spec(topic, a.protocol, "protocol")
    print(note)
    if pid is None:
        raise SystemExit("NOT CHECKED - no protocol")

    p, rows = longevity.rows_for(pid)
    n = sources(rows)
    print(f"  sources: {n}/{n} rows sourced, claims valid, no number on a described row")

    bad, msg = verbatim(rows)
    print(f"  verbatim: {msg}")
    for b in bad:
        print(f"    {b}")

    p, lit, app, agrees, want, got = reached(pid, rows)
    ok = agrees and want == got
    print(f"  reached: {p['name']} fasts {p['fast']:g} h -> {len(lit)} lit, "
          f"{got} NOT REACHED")
    print(f"    the app puts {p['fast']:g} h in {app['name']}; last lit row is "
          f"{lit[-1] if lit else 'NONE'}" + ("" if agrees else "   <-- DISAGREES WITH THE APP"))
    if want != got:
        print(f"    labels_for says {got} NOT REACHED, rows_for says {want}   <-- WRONG")

    pairs = 0
    if clip:
        import numpy as np
        from PIL import Image
        from scipy import ndimage
        pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                             "-show_entries", "stream=width,height",
                             "-show_entries", "format=duration", "-of", "csv=p=0", clip],
                            capture_output=True, text=True).stdout.split()
        w, h = (int(x) for x in pr[0].split(",")[:2])
        seconds = float(pr[-1])
        m = Image.open(os.path.join(HERE, "..", "..", "engine", "ribbon_mask.png")).convert("L")
        mask = np.array(m.resize((w, h), Image.LANCZOS)) > 128
        allowed = ndimage.binary_dilation(mask, np.ones((a.slack * 2 + 1,) * 2))

        cues, _ = spec(topic, None, "cues")
        fin, _ = spec(topic, None, "finale")
        cut = [(float(c) - 0.05, float(c) + 0.40)
               for c in (cues or "").split(",") if c.strip()]
        if fin:
            cut.append((float(fin) - 0.05, seconds))
        wins, t = [], 0.05
        for c0, c1 in sorted(cut):
            if c0 - t > 0.25:
                wins.append((t, c0))
            t = max(t, c1)
        if seconds - t > 0.25:
            wins.append((t, seconds - 0.05))
        worst, step = 0, 1.0 / 12
        for w0, w1 in wins:
            for tt in np.linspace(w0, max(w0, w1 - step), 3):
                f0, f1 = frames(clip, tt, w, h), frames(clip, tt + step, w, h)
                if f0 is None or f1 is None:
                    continue
                pairs += 1
                d = np.abs(f0 - f1).max(axis=2) > a.tol
                worst = max(worst, int((d & ~allowed).sum()))
        print(f"  motion: {len(wins)} quiet windows, {pairs} frame pairs sampled, "
              f"worst {worst} px outside the wave")
        if not pairs:
            print("    NOT CHECKED - no frame pair was readable")

    fail = bool(bad) or not ok or (clip and not pairs) or (clip and worst >= 400)
    print("LOOK AT IT" if fail else ("CLEAN" if clip else f"CLEAN (artwork only, {pairs} frame pairs)"))
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
