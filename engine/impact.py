#!/usr/bin/env python3
"""
impact.py - the sound a badge makes when it lands. Synthesised, not sampled.

A pop off a sample library arrives with a room on it, and five of them in eight
seconds start sounding like five different rooms. This is one oscillator with a
falling pitch, a click on the front, a sub under it and a breath of air behind,
so every strike is the same strike and only its note changes. Nothing is
licensed, because nothing was downloaded.

    click     1.2 ms of noise, differenced        the contact
    body      sine sweeping 1.0 -> 0.35 of f0     the arrival
    sub       sine an octave below, 90 ms         the weight of it
    air       band-passed noise, 35 ms            the room, briefly

The note climbs: one degree of a pentatonic per row, two semitones per badge
inside a row. Five identical thuds read as a machine; five rising ones read as a
list being counted, which is what the poster is.

It lives in the engine because both variants make the same sound. Micro had its
own, thinner - no sub, root at 760 - and the two drifted the way every other
copy in this repository drifted. A variant that wants a different one passes a
different `root`, or writes its own and says why.
"""
import numpy as np

SR = 48000
SCALE = [0, 2, 4, 7, 9]          # major pentatonic, one degree per row
STEP = 2.0                       # semitones between badges inside a row


def strike(f0, sr=SR, dur=0.40):
    n = int(sr * dur)
    t = np.arange(n) / sr

    # Body. The pitch falls by a factor of about three inside 30 ms - that fall
    # is what the ear hears as an impact rather than a note, and it has to be
    # exponential: a linear glide reads as a slide whistle.
    tau_f = 0.030
    f = f0 * (0.35 + 0.65 * np.exp(-t / tau_f))
    phase = 2 * np.pi * np.cumsum(f) / sr
    body = np.sin(phase) + 0.22 * np.sin(2 * phase)
    body *= np.exp(-t / 0.055) * np.clip(t / 0.0015, 0, 1)   # 1.5 ms, or it clicks twice

    # Sub. An octave down, flat, and longer than the body - this is the whole
    # difference between a bubble and a weight. Sine only: a harmonic down here
    # is mud on a phone speaker and thump on anything else.
    sub = np.sin(2 * np.pi * f0 * 0.5 * t) * np.exp(-t / 0.090) * 0.42
    sub *= np.clip(t / 0.004, 0, 1)

    rng = np.random.default_rng(int(f0))

    # Click. A millisecond of noise, differenced so it is all top end.
    click = np.zeros(n)
    k = int(sr * 0.0012)
    click[:k] = np.diff(rng.standard_normal(k + 1))
    click *= np.exp(-t / 0.0016) * 0.62

    # Air. Band-passed noise, one pole each way, gone in 35 ms.
    air = rng.standard_normal(n)
    lo = np.zeros(n)
    a = np.exp(-2 * np.pi * 2200 / sr)
    for i in range(1, n):                            # one-pole low pass
        lo[i] = (1 - a) * air[i] + a * lo[i - 1]
    air = (air - lo) * np.exp(-t / 0.035) * 0.11

    s = body + sub + click + air
    return s / np.abs(s).max()



def build(cues, seconds, per_row=None, sr=SR, root=420.0, gain=0.72):
    """Lay a strike at every cue.

    `per_row` groups the cues so the note can climb by row; without it the cues
    are taken in order. `root` is the only thing a variant normally sets, and
    they currently share 420: the badge landing sounds the same whether what
    landed is a vitamin or a muscle."""
    out = np.zeros(int(sr * seconds) + sr, np.float64)
    cache = {}
    for idx, t in enumerate(cues):
        row, j = per_row[idx] if per_row else (idx, 0)
        semi = SCALE[row % len(SCALE)] + STEP * j
        f0 = root * 2 ** (semi / 12.0)
        key = round(f0, 2)
        if key not in cache:
            cache[key] = strike(f0, sr)
        p = cache[key]
        i0 = int(round(t * sr))
        i1 = min(len(out), i0 + len(p))
        if i1 > i0:
            # Later badges in a row a touch quieter, so the row reads as one set
            # instead of three separate lifts.
            out[i0:i1] += p[:i1 - i0] * gain * (1.0 - 0.13 * j)
    out = out[:int(sr * seconds)]
    peak = np.abs(out).max()
    if peak > 0.97:
        out *= 0.97 / peak
    return out
