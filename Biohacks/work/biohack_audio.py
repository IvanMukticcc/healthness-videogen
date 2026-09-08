#!/usr/bin/env python3
"""
biohack_audio.py - the chip landing, the counter running, and the day under it.

Three layers, and only the middle one is new.

THE CHIP is the engine's strike, at a higher root. `engine/impact.py` says a
variant that wants a different sound passes a different `root` and one that wants
a different instrument writes its own and says why. This is the first case: what
lands here is a small glass capsule, not a bowl of lentils and not a barbell, so
the note sits an octave and a bit above theirs and the sub under it is pulled
back. Nothing else about it changes, and nothing about it is copied - it is
imported.

THE COUNTER is the one that is written here, and the reason is the picture. This
is the only variant where something on screen *counts*, over half a second, five
times. Silence under a running number reads as a rendering artefact; a single
sound at the start of it reads as a sound that has come loose from its picture.
So the count has a tick train under it whose spacing follows exactly the ease the
digits are drawn on - dense while the number is moving fast, thinning as it
settles - and then a lock at the end. Sixteen clicks over 0.50s is a mechanical
counter; four is a woodpecker; forty is a buzz.

    tick    0.9 ms of differenced noise, high-passed by construction
    lock    one short FM partial on the row's own pentatonic degree

THE BED is a pad, not water and not a low fifth. Built in the frequency domain
for the same reason `muscle_audio.bed` is: noise cut in the time domain does not
loop, and a click every eight seconds is a click for as long as anyone watches.

    python3 biohack_audio.py --bed --seconds 8 -o ../../engine/sfx/... (no: see below)
    python3 biohack_audio.py --cues-file day_chips.txt --dials day_dials.txt \\
        --finale-cue day_finale.txt --seconds 8 -o day_sfx.wav

The bed is written into this folder, not into `engine/sfx/`. The shelf there is
shared and this bed is this variant's; a third file in a shared folder that only
one caller ever reads is the beginning of the same drift every other copy in this
repository started as.
"""
import argparse
import os
import struct
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "engine"))
import impact                                        # noqa: E402  the engine's own

SR = impact.SR
ROOT = 520.0        # the chip. Above the 420 the other two share: a capsule of
                    # glass, not a bowl or a plate
LOCK_ROOT = 1040.0  # the counter settling, an octave over the chip
TICKS = 16          # clicks in one count


# ------------------------------------------------------------------ the counter

def tick(sr=SR, f=2600.0):
    """0.9 ms. Differenced noise is all top end by construction, so it cuts
    through a pad without needing a filter and without needing a level."""
    n = max(4, int(sr * 0.0009))
    rng = np.random.default_rng(int(f))
    x = np.diff(rng.standard_normal(n + 1))
    x *= np.hanning(len(x))
    t = np.arange(len(x)) / sr
    x += 0.35 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.0004)
    return x / np.abs(x).max()


def lock(f0, sr=SR, dur=0.30):
    """The counter arriving on its number. One FM partial, short, the same
    inharmonic 1.41 ratio the engine's chord is built on - so the five locks and
    the finale are the same instrument, and the finale is then a chord of a sound
    the ear has already been taught five times."""
    t = np.arange(int(sr * dur)) / sr
    m = np.sin(2 * np.pi * f0 * 1.41 * t) * 2.1 * np.exp(-t / 0.045)
    v = np.sin(2 * np.pi * f0 * t + m) * np.exp(-t / 0.085)
    return v * np.clip(t / 0.0008, 0, 1)


def counter(t0, dur, row, sr=SR, seconds=8.0, n=TICKS, gain=0.30):
    """A tick train over one dial's count, spaced on the count's own ease.

    The digits are drawn on easeOutCubic - fast, then settling - so the ticks are
    laid at the times the *value* passes each of n equal steps, not at equal
    times. Laid evenly they are a metronome running under a number that is
    slowing down, and the two pull apart in the last tenth of a second, which is
    exactly where the eye is.
    """
    out = np.zeros(int(sr * seconds) + sr, np.float64)
    tk = tick(f=2200.0 + 220.0 * row)
    for i in range(1, n + 1):
        v = i / n
        # invert easeOutCubic: v = 1-(1-p)^3  ->  p = 1-(1-v)^(1/3)
        p = 1.0 - (1.0 - v) ** (1.0 / 3.0)
        i0 = int(round((t0 + p * dur) * sr))
        i1 = min(len(out), i0 + len(tk))
        if i1 > i0:
            # Falling away as it settles: the first click is the needle leaving
            # zero and the last is it arriving, and an even train has no shape.
            out[i0:i1] += tk[:i1 - i0] * gain * (1.0 - 0.55 * v)
    f0 = LOCK_ROOT * 2 ** (impact.SCALE[row % len(impact.SCALE)] / 12.0)
    lk = lock(f0, sr)
    i0 = int(round((t0 + dur) * sr))
    i1 = min(len(out), i0 + len(lk))
    if i1 > i0:
        out[i0:i1] += lk[:i1 - i0] * gain * 1.9
    return out[:int(sr * seconds)]


# ------------------------------------------------------------------ the bed

def _periodic_noise(n, sr, lo, hi, rng, tilt=1.0):
    """Band-limited noise that joins sample n-1 to sample 0, because it is built
    as a spectrum and transformed back rather than cut out of a longer take."""
    spec = np.zeros(n // 2 + 1, complex)
    f = np.fft.rfftfreq(n, 1.0 / sr)
    band = (f >= lo) & (f <= hi)
    mag = np.zeros_like(f)
    mag[band] = (f[band] / max(lo, 1.0)) ** (-tilt)
    ph = rng.uniform(0, 2 * np.pi, len(f))
    spec = mag * np.exp(1j * ph)
    spec[0] = 0
    x = np.fft.irfft(spec, n)
    m = np.abs(x).max()
    return x / m if m > 0 else x


def bed(seconds, sr=SR, root=58.0, gain=0.48, seed=19):
    """Low, still, and awake. A root, its fifth and its octave, a slow breath
    across them, and a thin band of air on top.

    Not water: water is the food version's, and it says *pouring*. Not the
    exercise version's low fifth on its own, which says *effort*. This clip is a
    day passing in a body that is working properly, so the bed is a held chord
    that swells twice and a floor of air - the sound a room makes, not the sound
    a thing makes.

    Whole numbers of cycles for every component, so the last sample joins the
    first. The clip loops in a feed and a discontinuity is a click on every lap.
    """
    n = int(round(sr * seconds))
    t = np.arange(n) / sr
    rng = np.random.default_rng(seed)

    def whole(f):
        """The nearest frequency that fits a whole number of cycles in the clip."""
        return max(1, round(f * seconds)) / seconds

    x = np.zeros(n)
    for mult, g in ((1.0, 1.00), (1.5, 0.42), (2.0, 0.30), (3.0, 0.11)):
        f = whole(root * mult)
        x += g * np.sin(2 * np.pi * f * t)
    # Two breaths across the clip. Two rather than one: one is a fade and reads
    # as the track starting; two is a rhythm and reads as something alive.
    x *= 0.72 + 0.28 * np.sin(2 * np.pi * whole(2.0 / seconds) * t - np.pi / 2)

    air = _periodic_noise(n, sr, 900.0, 9000.0, rng, tilt=0.9) * 0.10
    air *= 0.80 + 0.20 * np.sin(2 * np.pi * whole(1.0 / seconds) * t)

    y = x / np.abs(x).max() * 0.86 + air
    y *= gain / max(np.abs(y).max(), 1e-9) * 0.98
    # 12 ms at both ends is not a fade, it is a guard: the components are whole
    # cycles so the join is already continuous, and anything longer would be
    # audible as the bed ducking on every lap.
    e = int(sr * 0.012)
    y[:e] *= np.linspace(0, 1, e)
    y[-e:] *= np.linspace(1, 0, e)
    return y


# ------------------------------------------------------------------ assembly

def write_wav(path, x, sr=SR):
    x = np.clip(x, -1.0, 1.0)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(struct.pack(f"<{len(x)}h", *(np.int16(x * 32767))))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cues-file", help="the chip landings flowanim.py wrote")
    p.add_argument("--dials", help="'t:dur,...' - the dial counts flowanim.py wrote")
    p.add_argument("--finale-cue", help="the finale's instant, its own file")
    p.add_argument("--seconds", type=float, default=8.0)
    p.add_argument("--bed", action="store_true", help="write the bed instead")
    p.add_argument("--bed-gain", type=float, default=0.48,
                   help="0.48 lands the bed on -18.4 LUFS, which is where both "
                        "engine beds are normalised - so the mix numbers in "
                        "render.sh mean the same here as they do next door")
    p.add_argument("--chip-gain", type=float, default=0.60)
    p.add_argument("--tick-gain", type=float, default=0.30)
    # 1.00 rather than the engine's 0.316 default and Micro's 0.62. A row here is
    # a chip, sixteen ticks and a lock - a thinner, higher event than a badge
    # thudding - so the chord has to come in over a busier and brighter texture
    # than it does next door. Measured in the first finished cut; see flow.md.
    p.add_argument("--finale-gain", type=float, default=1.00)
    p.add_argument("-o", "--out", required=True)
    a = p.parse_args()

    if a.bed:
        write_wav(a.out, bed(a.seconds, gain=a.bed_gain))
        print(f"  bed, {a.seconds}s, seamless -> {a.out}")
        return

    n = int(SR * a.seconds)
    out = np.zeros(n, np.float64)

    if a.cues_file and os.path.exists(a.cues_file):
        cues = [float(v) for v in open(a.cues_file).read().split(",") if v.strip()]
        out += impact.build(cues, a.seconds, per_row=[(i, 0) for i in range(len(cues))],
                            root=ROOT, gain=a.chip_gain)[:n]
        print(f"  {len(cues)} chips at {', '.join(f'{c:.2f}' for c in cues)}s, "
              f"root {ROOT:.0f}Hz")

    if a.dials and os.path.exists(a.dials):
        spec = [s for s in open(a.dials).read().strip().split(",") if s.strip()]
        for row, s in enumerate(spec):
            t0, dur = (float(v) for v in s.split(":"))
            out += counter(t0, dur, row, seconds=a.seconds, gain=a.tick_gain)
        print(f"  {len(spec)} counts of {TICKS} ticks and a lock, "
              f"{', '.join(s.split(':')[0] for s in spec)}s")

    if a.finale_cue and os.path.exists(a.finale_cue):
        t0 = float(open(a.finale_cue).read().strip())
        out += impact.finale(t0, a.seconds, root=ROOT * 0.5, gain=a.finale_gain)[:n]
        print(f"  finale chord at {t0:.2f}s, gain {a.finale_gain:.2f}")

    peak = np.abs(out).max()
    if peak > 0.97:
        out *= 0.97 / peak
        print(f"  scaled {0.97 / peak:.2f}x off a {peak:.2f} peak")
    write_wav(a.out, out)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
