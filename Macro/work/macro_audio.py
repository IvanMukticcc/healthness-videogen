#!/usr/bin/env python3
"""macro_audio.py - the sound of both acts, and the turn between them.

Act one is Micro's sound and is not re-invented here: `impact.build` makes the
badge pops from the cue file `flowanim.py` wrote, and `impact.finale` makes the
chord. What this file adds is everything after the turn, which act one has no
concept of.

FOUR SOUNDS, AND WHAT EACH ONE IS FOR

  turn     a riser into the flip and a soft body as the card lands. The riser is
           `impact.riser`, the engine's own, so the gesture is the one the four
           other variants already use to mean "here it comes"
  tick     one per food arriving in the list. Deliberately smaller than a badge
           pop - act one's badges are the event, act two's rows are a list being
           read, and a list that pops as hard as a badge sounds like five more
           badges rather than a summary
  sweep    while the ring fills. A held tone that rises a whole tone over its
           length: the ear tracks a rising pitch as "counting up" without being
           told, which is what the number in the middle is doing
  land     the ring arrives. `impact.bell`, the same FM bell act one's finale is
           built from, so the clip ends on the sound it ended on before

EVERY TIME COMES OFF DISK. The cues are written by `flowanim.py` (act one) and
by `meal.py` (act two, via `render.sh`), and read here. Nothing is typed twice:
that is the rule the whole repository is built on and the reason act one's pops
have never drifted from its badges.
"""
import argparse
import json
import os
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "engine"))
import impact                                                      # noqa: E402

SR = impact.SR


def write_wav(path, x, sr=SR):
    d = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(d.tobytes())


def place(buf, x, t):
    i = int(round(t * SR))
    if i < 0:
        x, i = x[-i:], 0
    n = min(len(x), len(buf) - i)
    if n > 0:
        buf[i:i + n] += x[:n]


def tick(f0, dur=0.26, gain=0.5):
    """A small wooden click - a row being set down, not a badge landing."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 26.0)
    x = (np.sin(2 * np.pi * f0 * t) * 0.7
         + np.sin(2 * np.pi * f0 * 2.02 * t) * 0.22
         + np.sin(2 * np.pi * f0 * 3.01 * t) * 0.08)
    click = np.random.default_rng(int(f0)).normal(0, 1, n) * np.exp(-t * 420.0) * 0.25
    return (x * env + click) * gain


def sweep(dur, f0=232.0, rise=2.0, gain=0.16):
    """A held tone climbing `rise` semitones - the number counting up."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * 2 ** (rise * (t / dur) / 12.0)
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.minimum(1.0, t / 0.18) * np.minimum(1.0, (dur - t) / 0.30)
    x = (np.sin(ph) * 0.55 + np.sin(2 * ph) * 0.28 + np.sin(3 * ph) * 0.10)
    return x * np.clip(env, 0, 1) * gain


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cues-file", required=True, help="act one's badge landings")
    p.add_argument("--finale-file", help="act one's finale instant")
    p.add_argument("--act2-cues", required=True, help="the json meal.py's Plan wrote")
    p.add_argument("--act1-seconds", type=float, required=True)
    p.add_argument("--flip-seconds", type=float, required=True)
    p.add_argument("--act2-seconds", type=float, required=True)
    p.add_argument("--root", type=float, default=420.0)
    p.add_argument("--gain", type=float, default=0.72)
    p.add_argument("-o", "--out", required=True, help="act one's pops")
    p.add_argument("--finale-out", help="act one's chord, at unity, its own file")
    p.add_argument("--act2-out", required=True, help="everything after the turn")
    a = p.parse_args()

    # ---- act one, exactly as Micro makes it ----------------------------------
    cues = sorted(float(c) for c in open(a.cues_file).read().strip().split(",") if c)
    # three badges a row: the row is the degree, the badge within it the step
    per_row = [(i // 3, i % 3) for i in range(len(cues))]
    write_wav(a.out, impact.build(cues, a.act1_seconds, per_row,
                                  root=a.root, gain=a.gain))
    if a.finale_out and a.finale_file and os.path.exists(a.finale_file):
        t0 = float(open(a.finale_file).read().strip())
        write_wav(a.finale_out, impact.finale(t0, a.act1_seconds, root=a.root))

    # ---- the turn and act two, on one timeline starting at the flip ---------
    c = json.load(open(a.act2_cues))
    total = a.flip_seconds + a.act2_seconds
    buf = np.zeros(int(total * SR) + SR, dtype=np.float64)

    # the riser leads the turn: it has to be arriving as the card starts moving
    r = impact.riser(dur=max(0.18, a.flip_seconds * 0.8))
    place(buf, r * 0.55, max(0.0, a.flip_seconds - len(r) / SR))
    # and the card lands: a low body on the half-turn, when the back face appears
    place(buf, tick(96.0, dur=0.42, gain=0.55), a.flip_seconds * 0.52)

    off = a.flip_seconds
    for i, t in enumerate(c["foods"]):
        place(buf, tick(impact.SR and 300.0 * 2 ** (impact.SCALE[i % len(impact.SCALE)] / 12.0),
                        gain=0.42), off + t)
    for i, t in enumerate(c["chips"]):
        place(buf, tick(520.0 * 2 ** (i * 2 / 12.0), dur=0.18, gain=0.26), off + t)

    ring_len = max(0.4, c["verdict"] - c["ring"])
    place(buf, sweep(ring_len), off + c["ring"])

    # THE ENDING IS ACT ONE'S CHORD, not a bell of its own.
    #
    # It was `impact.bell` - one FM voice - and the user's word for it was
    # "dong". Six candidates went out and this is the one they picked: the same
    # chord act one ends on, which means the clip closes on the sound it already
    # closed its first act with. They chose it knowing it repeats.
    #
    # `impact.finale` is called rather than a chord being assembled here, and
    # that is the whole point of impact.py: one number in the engine once
    # reached the mix at three different levels because three callers each
    # scaled it, which is what Micro's render.sh records. It goes in at its
    # natural gain, the same as act one's, and render.sh mixes this wav at unity.
    # Generated in its own 2.6s buffer and PLACED, rather than asked for at an
    # offset inside a buffer of act two's length: `finale` returns an array of
    # `seconds`, and act two's buffer is longer than that by design, so adding
    # them directly is a shape mismatch waiting on whichever is longer today.
    place(buf, impact.finale(0.0, 2.6, root=a.root), off + c["verdict"])

    write_wav(a.act2_out, buf[:int(total * SR)])
    print(f"  act one: {len(cues)} pops"
          + (f", chord at {t0:.2f}s" if a.finale_out and a.finale_file else "")
          + f"  |  act two: {len(c['foods'])} ticks, ring {ring_len:.2f}s, bell at "
            f"{c['verdict']:.2f}s")


if __name__ == "__main__":
    main()
