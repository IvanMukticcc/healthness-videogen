#!/usr/bin/env python3
"""
audit.py - does anything move that should not?

The old check was to diff two frames and count the moving pixels that fall
outside the wave mask. With badges on the clip that check fires on every one of
them, and a number that is always wrong is a number nobody reads.

So the frames are chosen instead of filtered. The cues file says when each badge
lands; a badge is finished 0.52 s later, and so is the muscle it lit - 0.42 s of
pop, the ring gone by 0.34 s, the body's flash settled by 0.47 s. Any gap between
one landing finishing and the next one starting is a window where the only thing
in the picture that is allowed to move is the liquid, and inside such a window
the original invariant holds exactly as it did before any of this existed.

The bodies themselves never move, so they need no window: they are outside the
mask and perfectly still, which is what the check is looking for.

The finale is the same argument again and it was missing until 9 September 2026.
It is not a badge cue - it lives in its own file so the sound does not strike it
as a sixth hit - so the windows knew nothing about it, and the stretch after the
last badge ran to the end of the clip with the loudest moving thing in the whole
video inside it. On an 8s cut that put a sample at t=6.91, dead in the surge, and
every Exercise audit this day reported 46000 to 49000 px and the word `look at
it` for a clip that was correct. The reverse is the real hazard: three samples
across a window is a thin search, and had the rhythm placed them either side of
the surge the same window would have printed `clean` while containing it.

So the finale is an event with a settle time like any other, and the file is
found rather than typed: given `<topic>_silent.mp4` the audit reads
`<topic>_cues.txt` and `<topic>_finale.txt` beside it, and says which files it
read. The flags still override, for re-checking an older clip by hand. And the
sample count is printed next to the verdict, because `clean` over twelve pairs
and `clean` over three are not the same sentence.

    ../.venv/bin/python audit.py push_silent.mp4
"""
import argparse
import pathlib
import subprocess

import numpy as np
from PIL import Image
from scipy import ndimage

SETTLED = 0.52          # pop 0.42 + a little; the ring dies at 0.34,
                        # the body's flash at 0.13 + 0.34
FINALE = 0.85           # the surge crosses five rows and the badges catch it:
                        # flowanim prints "settled by 7.20s" for a finale at
                        # 6.38 and its last badge done at 7.21, so 0.82-0.83
                        # measured, 0.85 taken
TAIL = 0.15             # the stretch after the finale is audited however short
                        # it is - the last frame is the one a feed freezes on


def frame(path, t, W, H):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path,
         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.int16)


def windows(events, seconds, fade, need=0.45):
    """Stretches where nothing is landing, fading or surging.

    `events` is (instant, how long it takes to settle) - a badge cue at 0.52, the
    finale at 0.85. The last stretch is kept at any length down to TAIL, because
    a still ending is worth auditing and it is the one thing no window before it
    can tell you about.
    """
    out, prev, end = [], 0.0, seconds - fade
    for t, settle in sorted(events) + [(seconds + 99, 0.0)]:
        a, b = prev, min(t, end)
        want = need if t < seconds else TAIL
        if b - a >= want:
            out.append((a + 0.05, b - 0.05))
        prev = max(prev, t + settle)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--mask",
                   default=str(pathlib.Path(__file__).resolve().parent
                               / ".." / ".." / "engine" / "ribbon_mask.png"),
                   help="the authored mask, which lives in the engine rather than here")
    p.add_argument("--cues", help="the file flowanim.py --muscle-cues wrote. "
                   "Found beside the video from its name when not given")
    p.add_argument("--finale", help="the file flowanim.py --finale-cue wrote. "
                   "Found beside the video from its name when not given")
    p.add_argument("--fade", type=float, default=0.4)
    p.add_argument("--slack", type=int, default=15,
                   help="px of grace around the mask; the silhouette does ripple")
    p.add_argument("--tol", type=int, default=10, help="what counts as a changed pixel")
    args = p.parse_args()

    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height",
                            "-show_entries", "format=duration",
                            "-of", "csv=p=0", args.video],
                           capture_output=True, text=True, check=True).stdout.split()
    W, H = (int(v) for v in probe[0].split(",")[:2])
    seconds = float(probe[1])

    m = Image.open(args.mask).convert("L").resize((W, H), Image.LANCZOS)
    mask = np.array(m) > 128
    allowed = ndimage.binary_dilation(mask, np.ones((args.slack * 2 + 1,) * 2))

    # The spec is found rather than typed. render.sh already wrote both files;
    # asking the typist for them is how a clip gets audited against another
    # clip's timings, or against none at all - and none at all is the dangerous
    # one, because it thins the search instead of widening it.
    stem = pathlib.Path(args.video).name
    for suffix in ("_silent.mp4", "_muscles.mp4", ".mp4"):
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
            break
    here = pathlib.Path(args.video).resolve().parent
    read = []

    def find(flag, name):
        if flag:
            return pathlib.Path(flag)
        for d in (here, pathlib.Path.cwd()):
            c = d / f"{stem}{name}"
            if c.exists():
                return c
        return None

    cue_f, fin_f = find(args.cues, "_cues.txt"), find(args.finale, "_finale.txt")
    cues, t_fin = [], None
    if cue_f and cue_f.exists() and cue_f.read_text().strip():
        cues = sorted(float(c) for c in cue_f.read_text().strip().split(","))
        read.append(str(cue_f.name))
    if fin_f and fin_f.exists() and fin_f.read_text().strip():
        t_fin = float(fin_f.read_text().strip())
        read.append(str(fin_f.name))

    events = [(c, SETTLED) for c in cues]
    if t_fin is not None:
        events.append((t_fin, FINALE))
    wins = windows(events, seconds, args.fade if cues else 0.0)
    if not wins:
        raise SystemExit("no quiet window - the badges never stop landing")

    print(f"{args.video}  {W}x{H}  {seconds:.2f}s")
    print("  timings: " + (", ".join(read) if read else
          "NONE FOUND - every badge and the finale are inside the windows below, "
          "so a number here means nothing and so does a clean"))
    print(f"  {len(wins)} quiet windows: " +
          ", ".join(f"{a:.2f}-{b:.2f}" for a, b in wins))
    worst, pairs = 0, 0
    step = 1.0 / 12                       # two frames apart at 24fps
    for a, b in wins:
        n_s = 3 if b - a >= 0.30 else 2   # a short tail still gets two
        for t in np.linspace(a, max(a, b - step), n_s):
            pairs += 1
            f0 = frame(args.video, t, W, H)
            f1 = frame(args.video, t + step, W, H)
            d = np.abs(f0 - f1).max(axis=2) > args.tol
            stray = d & ~allowed
            lab, n = ndimage.label(stray)
            if n:
                sz = ndimage.sum(stray, lab, range(1, n + 1))
                big = int(sz.max())
            else:
                big = 0
            worst = max(worst, int(stray.sum()))
            print(f"  t={t:5.2f}  moving {int(d.sum()):7d} px, "
                  f"{int(stray.sum()):5d} outside the wave in {n} clusters, largest {big}")
    print(f"  worst frame: {worst} px outside the wave over {pairs} frame pairs "
          f"({'clean' if worst < 400 else 'look at it'})")


if __name__ == "__main__":
    main()
