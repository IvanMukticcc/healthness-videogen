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

`finale` is the other sound in here: the chord the climbing rows resolve onto,
with 260 ms of riser in front of it. Same argument as the strike - both variants
arrive at the same moment and it should not be two different sounds.

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



# The finale. The rows climb a pentatonic one degree at a time, which leaves the
# ear counting and waiting; this is the cadence that answers it. Not five strikes
# at once - five of these on the same frame is a stack of clicks and a peak the
# limiter flattens - but one chord, struck once, with the five rows' own notes
# spread across three octaves so no two of them cluster.
CHORD = [-12, 2, 7, 12, 16, 21]     # rows 1-5 spread out, plus the octave over the root


def swell(f0, sr=SR, dur=0.75):
    """One voice of the chord. A tone, not an impact: the pitch does not fall.

    `strike` falls by a factor of three in 30 ms and that is what makes it read
    as something landing. Nothing lands here - everything that was going to land
    already has - so the voice holds its pitch and decays, and the arrival is
    carried by the attack the caller puts in front of it.
    """
    n = int(sr * dur)
    t = np.arange(n) / sr
    ph = 2 * np.pi * f0 * t
    v = np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.11 * np.sin(3 * ph)
    # Slower attack than a strike's 1.5 ms: six of these opening together on the
    # same sample is a click nobody asked for.
    v *= np.exp(-t / (0.34 + 0.16 * (220.0 / max(f0, 60.0)))) * np.clip(t / 0.006, 0, 1)
    return v


def riser(sr=SR, dur=0.26):
    """The 260 ms before the chord: noise climbing into it.

    This is the part that buys the watch. Everything else in the clip is an
    event that has already happened by the time it is heard; this is the only
    sound that says something is about to.
    """
    n = int(sr * dur)
    t = np.arange(n) / sr
    rng = np.random.default_rng(11)
    x = rng.standard_normal(n)
    # One pole, its corner climbing 300 -> 5200 Hz. Filtering with a fixed band
    # and fading it up reads as someone turning a knob; moving the corner reads
    # as something approaching.
    fc = 300.0 * (5200.0 / 300.0) ** (t / dur)
    a = np.exp(-2 * np.pi * fc / sr)
    lo = np.zeros(n)
    for i in range(1, n):
        lo[i] = (1 - a[i]) * x[i] + a[i] * lo[i - 1]
    hp = x - lo                                  # what the moving corner lets through
    return hp * (t / dur) ** 2.2 * 0.30


def finale(t0, seconds, sr=SR, root=420.0, gain=0.62, lead=0.26, dur=0.75):
    """The riser, the chord and the weight under it, laid at `t0`.

    The tail is cut to what is left of the clip and faded, never left to run off
    the end: the clip loops in a feed, and a chord still ringing on the last
    sample is a click on every lap.
    """
    out = np.zeros(int(sr * seconds), np.float64)
    room = seconds - t0
    if room <= 0.05:
        return out
    dur = min(dur, room)
    n = int(sr * dur)
    t = np.arange(n) / sr

    body = np.zeros(n)
    for semi in CHORD:
        f = root * 2 ** (semi / 12.0)
        v = swell(f, sr, dur)
        body += v[:n] * (0.62 if semi < 0 else 1.0)      # the low voice is weight, not melody
    body += np.sin(2 * np.pi * root * 0.5 * t) * np.exp(-t / 0.16) * 0.5 * np.clip(t / 0.004, 0, 1)
    rng = np.random.default_rng(23)
    k = int(sr * 0.0012)
    body[:k] += np.diff(rng.standard_normal(k + 1)) * 0.45
    body /= np.abs(body).max()

    if dur < 0.75:                                        # truncated: land it softly
        f = int(sr * 0.06)
        body[-f:] *= np.linspace(1.0, 0.0, f)

    i0 = int(round(t0 * sr))
    out[i0:i0 + n] += body[:len(out) - i0] * gain

    if lead > 0:
        r = riser(sr, min(lead, t0))
        j0 = max(0, i0 - len(r))
        out[j0:i0] += r[len(r) - (i0 - j0):] * gain
    return out


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
