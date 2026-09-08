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
an FM bell an octave over the root with a sine under it. Same argument as the
strike - both variants arrive at the same moment and it should not be two
different sounds.

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
# The finale. The rows climb a pentatonic one degree at a time, which leaves the
# ear counting and waiting; this is the cadence that answers it. Struck once, not
# five strikes on the same frame - that is a stack of clicks and a peak the
# limiter flattens.
#
# Chosen off nine candidates auditioned in the finished clip, six of them real
# recordings: crotales playing these exact five notes, a tuned Thai gong on the
# root, a 40-inch tam-tam, cymbal rolls. The synthesis won, and the measurement
# that killed the best of the recordings is worth keeping: a phone speaker is
# gone below about 500 Hz, and the tam-tam lost 7.6 dB of itself through a
# fourth-order high pass there. It is the most impressive of the nine in
# headphones and the weakest of them in a feed. This one loses 0.8.
CHORD = [0, 2, 4, 7, 9, 12, 16]                    # the pentatonic, then its octave and third
CHORD_GAIN = [0.5, 0.7, 0.8, 0.85, 0.8, 0.7, 0.5]  # loudest in the middle, so it is a chord
SPREAD = 0.012                                     # seconds per degree, so it opens upward


def bell(f0, sr=SR, dur=1.5, ratio=1.41, index=3.2):
    """One voice: two-operator FM, which is how a bell is made.

    `strike` falls by a factor of three in 30 ms and that is what makes it read
    as something landing. Nothing lands here - everything that was going to land
    already has - so the voice holds its pitch and rings.

    The modulator sits at 1.41 x the carrier. An integer ratio gives a harmonic
    tone, which is an organ; the irrational one gives the inharmonic partials
    that say metal, and 1.41 is close enough to root two to have no common
    factor with anything. The index falls faster than the amplitude does, so the
    voice is bright on arrival and pure while it rings - a bell that keeps its
    clang all the way down is a doorbell.
    """
    t = np.arange(int(sr * dur)) / sr
    m = np.sin(2 * np.pi * f0 * ratio * t) * index * np.exp(-t / 0.22)
    return np.sin(2 * np.pi * f0 * t + m) * np.exp(-t / (0.20 + 0.5 * (440.0 / f0)))


def riser(sr=SR, dur=0.26):
    """Noise climbing into the chord. Off by default - `lead=0` - and here
    because it is the only sound in the clip that says something is *about* to
    happen; everything else is heard after it has already landed.

    One pole, its corner climbing 300 -> 5200 Hz. Filtering with a fixed band
    and fading it up reads as someone turning a knob; moving the corner reads as
    something approaching.
    """
    n = int(sr * dur)
    t = np.arange(n) / sr
    rng = np.random.default_rng(11)
    x = rng.standard_normal(n)
    fc = 300.0 * (5200.0 / 300.0) ** (t / dur)
    a = np.exp(-2 * np.pi * fc / sr)
    lo = np.zeros(n)
    for i in range(1, n):
        lo[i] = (1 - a[i]) * x[i] + a[i] * lo[i - 1]
    return (x - lo) * (t / dur) ** 2.2 * 0.30


def finale(t0, seconds, sr=SR, root=420.0, gain=0.316, lead=0.0, dur=1.5):
    """The chord, and the weight under it, laid at `t0`.

    The voices are an octave over the root the badges use, so the finale answers
    them from above rather than in among them. Underneath, one sine an octave
    *below* the root: on a phone it is felt rather than heard, and on anything
    else it is the difference between a chime and an arrival.

    The tail is cut to what is left of the clip and faded, never left to run off
    the end: the clip loops in a feed, and a chord still ringing on the last
    sample is a click on every lap.
    """
    out = np.zeros(int(sr * seconds), np.float64)
    room = seconds - t0
    if room <= 0.05:
        return out

    span = int(sr * (dur + SPREAD * max(CHORD)))
    body = np.zeros(span)
    for semi, g in zip(CHORD, CHORD_GAIN):
        v = bell(root * 2 ** (semi / 12.0) * 2.0, sr, dur)
        i0 = int(sr * SPREAD * abs(semi))
        body[i0:i0 + len(v)] += v * g
    t = np.arange(int(sr * 0.5)) / sr
    body[:len(t)] += (np.sin(2 * np.pi * root * 0.5 * t) * np.exp(-t / 0.13)
                      * np.clip(t / 0.004, 0, 1) * 0.9)
    body /= np.abs(body).max()

    n = min(len(body), int(sr * room))
    body = body[:n].copy()
    if n < span:                                   # truncated: land it softly
        f = min(n, int(sr * 0.06))
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
