#!/usr/bin/env python3
"""
muscle_audio.py - the hit under each badge, and the bed under all of them.
Both synthesised rather than sampled.

A pop off a sample library arrives with a room on it, and five of them in eight
seconds start sounding like five different rooms. And the bed the food version
used is running water, which is the right sound for a clip about what you drink
and the wrong one for a clip about what you lift.

THE HIT. One oscillator with a falling pitch, a click on the front, a sub under
it and a breath of air behind, so every hit is the same hit and only its note
changes:

    click     1.2 ms of noise, differenced        the plate touching down
    body      sine sweeping 1.0 -> 0.35 of f0     the weight arriving
    sub       sine an octave below, 90 ms         what it weighs
    air       band-passed noise, 35 ms            the room, briefly

The note rises through the clip. Row 1 lands on the root and rows 2-5 climb a
major pentatonic, and the badges inside a row step up two semitones each. Five
identical thuds read as a machine; five rising ones read as a set being counted
off, and a viewer waits for the next one. That wait is the whole point.

THE BED. A low fifth and a slow filtered swell, both built in the frequency
domain so they are exactly periodic over the clip and the loop has no seam. Cut
noise in the time domain and the eighth second does not join the first, which on
a feed that loops is a click every eight seconds forever.

    ../.venv/bin/python muscle_audio.py --cues-file push_cues.txt \
        --finale-cue push_finale.txt --finale-out push_chord.wav -o push_hits.wav
    ../.venv/bin/python muscle_audio.py --bed --seconds 8 -o lift_bed_8s.wav

The bed on the shelf, ../../engine/sfx/lift_bed_8s.m4a, is that second command's
output and reproduces from it at waveform correlation 0.999983. Regenerate it
here if it is ever needed; replacing the shelf copy is the engine's to do, not
this folder's.
"""
import argparse
import sys
import wave
from pathlib import Path

import numpy as np

# The riser and the chord live in the engine, because both variants make the
# same one. Called, never copied: a second generation of it here is exactly how
# every other copy in this repository drifted.
sys.path.insert(0, str(Path(__file__).resolve().parent / ".." / ".." / "engine"))
import impact

SR = 48000
SCALE = [0, 2, 4, 7, 9]          # major pentatonic, one degree per row
STEP = 2.0                       # semitones between badges inside a row


def one_hit(f0, sr=SR, dur=0.40):
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
    """Lay a hit at every cue. `per_row` groups the cues so the note can climb by
    row; without it the cues are simply taken in order."""
    out = np.zeros(int(sr * seconds) + sr, np.float64)
    cache = {}
    for idx, t in enumerate(cues):
        row, j = per_row[idx] if per_row else (idx, 0)
        semi = SCALE[row % len(SCALE)] + STEP * j
        f0 = root * 2 ** (semi / 12.0)
        key = round(f0, 2)
        if key not in cache:
            cache[key] = one_hit(f0, sr)
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


# ---------------------------------------------------------------------- bed

def _periodic_noise(n, sr, lo, hi, rng, tilt=1.0):
    """Band-limited noise that is exactly periodic over n samples.

    Built by shaping the spectrum and transforming back, so sample n-1 joins
    sample 0. Filtering white noise in the time domain and cutting it to length
    leaves a step at the seam, which on an eight-second loop is a click every
    eight seconds for as long as anyone watches.
    """
    m = n // 2 + 1
    f = np.arange(m) * sr / n
    mag = np.exp(-0.5 * (np.log(np.maximum(f, 1e-6) / np.sqrt(lo * hi))
                         / np.log(hi / lo)) ** 2) / np.maximum(f, 20.0) ** (tilt * 0.5)
    mag[0] = 0.0
    spec = mag * np.exp(2j * np.pi * rng.random(m))
    x = np.fft.irfft(spec, n)
    return x / max(np.abs(x).max(), 1e-9)


def bed(seconds, sr=SR, root=55.0, gain=0.39, seed=7):
    """A low fifth with a slow swell over it. Everything periodic in `seconds`.

    Quiet and wide rather than musical: it has to sit under five hits and a
    voice-over that may or may not be added later, and anything with a melody in
    it competes with the hits for the same attention the badges are asking for.
    """
    n = int(round(sr * seconds))
    t = np.arange(n) / sr
    rng = np.random.default_rng(seed)

    # Only frequencies that complete a whole number of cycles in the clip, or
    # the drone itself steps at the seam.
    def whole(f):
        return max(1, round(f * seconds)) / seconds

    x = np.zeros(n)
    for f, a in ((root, 0.55), (root * 1.5, 0.30), (root * 2, 0.16), (root * 3, 0.06)):
        fw = whole(f)
        x += a * np.sin(2 * np.pi * fw * t + rng.random() * 6.283)

    # Two swells over the clip, so the loop point falls where it is quietest.
    swell = 0.5 - 0.5 * np.cos(2 * np.pi * 2 * t / seconds)
    x += _periodic_noise(n, sr, 180.0, 2600.0, rng) * (0.10 + 0.22 * swell)
    x += _periodic_noise(n, sr, 40.0, 160.0, rng) * 0.20

    # A slow breath on the whole thing, one cycle per clip.
    x *= 0.80 + 0.20 * (0.5 - 0.5 * np.cos(2 * np.pi * t / seconds))
    x /= max(np.abs(x).max(), 1e-9)
    return np.tanh(x * 1.4) * gain


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
    p.add_argument("--cues-file", help="the file flowanim.py --muscle-cues wrote")
    p.add_argument("--times", default="1,2,4,5.5,7", help="row times, if no cues given")
    p.add_argument("--counts", default="3,3,3,3,3", help="badges per row, if no cues given")
    p.add_argument("--stagger", type=float, default=0.09)
    p.add_argument("--seconds", type=float, default=8.0)
    p.add_argument("--root", type=float, default=420.0, help="row 1's note, in Hz")
    p.add_argument("--gain", type=float, default=0.72)
    p.add_argument("--bed", action="store_true", help="write the bed instead of the hits")
    p.add_argument("--bed-gain", type=float, default=0.39)
    p.add_argument("--finale-cue", help="the file flowanim.py --finale-cue wrote. Its "
                                        "instant is NOT in the badge cues and must not "
                                        "be: laid there it would be sounded as a sixth "
                                        "badge, on a frame where nothing lands")
    p.add_argument("--finale-gain", type=float, default=None,
                   help="an override, and normally not given. Unset, impact.finale "
                        "keeps its own gain - the level the finale was chosen at, out "
                        "of nine candidates, in a finished clip. The sound is shared "
                        "with the other variants, so its level is one number in the "
                        "engine rather than one per variant: two folders tuning it "
                        "separately is exactly the drift impact.py exists to prevent. "
                        "Measure it on an Exercise cut by all means, but report the "
                        "number rather than setting it here")
    p.add_argument("--finale-out",
                   help="write the finale to its own file instead of summing it into "
                        "the hits. It has to be its own file, because the mixer applies "
                        "one gain to everything in a track: summed in here, the chord "
                        "was multiplied by render.sh's 0.62 - a number chosen for badge "
                        "hits - and arrived 4.15 dB under the level impact.finale "
                        "returns it at. The level the engine returns is the level it "
                        "has to arrive at, so this file is mixed at unity")
    p.add_argument("-o", "--out", required=True)
    args = p.parse_args()

    if args.bed:
        write_wav(args.out, bed(args.seconds, gain=args.bed_gain))
        print(f"  bed, {args.seconds}s, seamless -> {args.out}")
        return

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
    fin = None
    if args.finale_cue:
        fin = float(open(args.finale_cue).read().strip())
        # No gain unless one was asked for: the engine's own default is the
        # level the sound was picked at, and passing a number here would make
        # this variant's finale a different loudness from everyone else's.
        gain_kw = {} if args.finale_gain is None else {"gain": args.finale_gain}
        chord = impact.finale(fin, args.seconds, root=args.root, **gain_kw)
        if args.finale_out:
            write_wav(args.finale_out, chord)
        else:
            x = x + chord
    write_wav(args.out, x)
    print(f"  {len(cues)} hits over {args.seconds}s"
          + (f", finale at {fin:.2f}s" if fin is not None else "")
          + f" -> {args.out}"
          + (f", chord -> {args.finale_out} (mix it at unity)"
             if fin is not None and args.finale_out else ""))


if __name__ == "__main__":
    main()
