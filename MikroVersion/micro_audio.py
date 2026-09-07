#!/usr/bin/env python3
"""
micro_audio.py - the pop under each badge, synthesised rather than sampled.

A pop off a sample library arrives with a room on it, and five of them in eight
seconds start sounding like five different rooms. This is one oscillator with a
falling pitch, a click on the front and a breath of air behind it, so every pop
is the same pop and only its note changes. Nothing is licensed, because nothing
was downloaded.

    click     1.2 ms of noise, high-passed        the lips parting
    body      sine sweeping 1.0 -> 0.42 of f0     the bubble collapsing
    air       band-passed noise, 45 ms            the spray after it

The note rises through the clip. Row 1 lands on the root and rows 2-5 climb a
major pentatonic, and the badges inside a row step up two semitones each. Five
identical thuds read as a machine; five rising ones read as a list being counted
off, and a viewer waits for the next one. That wait is the whole point.

    python3 micro_audio.py --cues 1,1.09,1.18,2,... -o work/pops.wav
    python3 micro_audio.py --cues-file work/liver_cues.txt -o work/pops.wav
"""
import argparse
import wave

import numpy as np

SR = 48000
SCALE = [0, 2, 4, 7, 9]          # major pentatonic, one degree per row
STEP = 2.0                       # semitones between badges inside a row


def one_pop(f0, sr=SR, dur=0.30):
    n = int(sr * dur)
    t = np.arange(n) / sr

    # Body. The pitch falls by a factor of 2.4 inside 45 ms - that fall is what
    # the ear hears as "pop" rather than "beep", and it has to be exponential:
    # a linear glide reads as a slide whistle.
    tau_f = 0.045
    f = f0 * (0.42 + 0.58 * np.exp(-t / tau_f))
    phase = 2 * np.pi * np.cumsum(f) / sr
    body = np.sin(phase) + 0.28 * np.sin(2 * phase)

    env = np.exp(-t / 0.038)
    attack = np.clip(t / 0.0015, 0, 1)              # 1.5 ms, or it clicks twice
    body *= env * attack

    # Click. Two milliseconds of noise, differenced so it is all top end.
    rng = np.random.default_rng(int(f0))
    click = np.zeros(n)
    k = int(sr * 0.0012)
    click[:k] = np.diff(rng.standard_normal(k + 1))
    click *= np.exp(-t / 0.0016) * 0.55

    # Air. Band-passed noise, one pole each way, decaying over 45 ms.
    air = rng.standard_normal(n)
    lo = np.zeros(n)
    a = np.exp(-2 * np.pi * 1800 / sr)
    for i in range(1, n):                            # one-pole low pass
        lo[i] = (1 - a) * air[i] + a * lo[i - 1]
    air = (air - lo) * np.exp(-t / 0.045) * 0.16

    s = body + click + air
    return s / np.abs(s).max()


def build(cues, seconds, per_row=None, sr=SR, root=760.0, gain=0.72):
    """Lay a pop at every cue. `per_row` groups the cues so the note can climb by
    row; without it the cues are simply taken in order."""
    out = np.zeros(int(sr * seconds) + sr, np.float64)
    cache = {}
    for idx, t in enumerate(cues):
        row, j = per_row[idx] if per_row else (idx, 0)
        semi = SCALE[row % len(SCALE)] + STEP * j
        f0 = root * 2 ** (semi / 12.0)
        key = round(f0, 2)
        if key not in cache:
            cache[key] = one_pop(f0, sr)
        p = cache[key]
        i0 = int(round(t * sr))
        i1 = min(len(out), i0 + len(p))
        if i1 > i0:
            # Later badges in a row a touch quieter, so the row reads as one
            # gesture instead of three separate events.
            out[i0:i1] += p[:i1 - i0] * gain * (1.0 - 0.13 * j)
    out = out[:int(sr * seconds)]
    peak = np.abs(out).max()
    if peak > 0.97:
        out *= 0.97 / peak
    return out


def write_wav(path, x, sr=SR):
    d = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(d.tobytes())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cues", help="comma separated seconds")
    p.add_argument("--cues-file", help="the file flowanim.py --micro-cues wrote")
    p.add_argument("--times", default="1,2,4,5.5,7", help="row times, if no cues given")
    p.add_argument("--counts", default="3,3,3,3,3", help="badges per row, if no cues given")
    p.add_argument("--stagger", type=float, default=0.09)
    p.add_argument("--seconds", type=float, default=8.0)
    p.add_argument("--root", type=float, default=760.0, help="row 1's note, in Hz")
    p.add_argument("--gain", type=float, default=0.72)
    p.add_argument("-o", "--out", required=True)
    args = p.parse_args()

    if args.cues_file:
        args.cues = open(args.cues_file).read().strip()
    if args.cues:
        cues = sorted(float(c) for c in args.cues.split(","))
        # Regroup by row so the notes still climb: cues that share a landing
        # window belong to the same row.
        per_row, row, j, last = [], 0, 0, None
        for t in cues:
            if last is not None and t - last > args.stagger * 2.5:
                row, j = row + 1, 0
            per_row.append((row, j))
            j += 1
            last = t
    else:
        times = [float(t) for t in args.times.split(",")]
        counts = [int(c) for c in args.counts.split(",")]
        cues, per_row = [], []
        for r, (t0, n) in enumerate(zip(times, counts)):
            for j in range(n):
                cues.append(t0 + j * args.stagger)
                per_row.append((r, j))

    x = build(cues, args.seconds, per_row, root=args.root, gain=args.gain)
    write_wav(args.out, x)
    print(f"  {len(cues)} pops over {args.seconds}s -> {args.out}")


if __name__ == "__main__":
    main()
