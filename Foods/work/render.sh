#!/usr/bin/env bash
# render.sh - poster in, finished clip out: liquid, water and the ending.
#
# Foods was the only variant without one of these. Every step was in flow.md as
# prose and run by hand, which was fine while a clip was liquid and a bed and
# nothing else - and stopped being fine the night the finale, the surge and the
# warm bed arrived and six topics needed all three.
#
#   ./render.sh lungs lungs_labelled.png
#
# Anything after the second argument goes straight to flowanim.py.
#
# WHAT THIS ONE DOES NOT HAVE. There are no badges here and so no pops, which
# makes the sound two tracks rather than three. It also makes the finale a
# different thing than it is next door: there the chord answers a count the ear
# has been following, and here there is no count. It is kept because the clip
# otherwise simply stops - and because with no overlay covering the wave, this is
# the only variant where the surge is visible along its whole length. 22.3% of
# the liquid shows in a Micro clip; here it is all of it.
set -euo pipefail
cd "$(dirname "$0")"

if [ $# -lt 2 ]; then
    sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
fi

TOPIC="$1"; POSTER="$2"; shift 2
DIR="$(dirname "$POSTER")"
BASE="${BASE:-../INPUT/base_${TOPIC}.png}"
CLEAN="$DIR/base_${TOPIC}_clean.png"
LAYOUT="$DIR/base_${TOPIC}_layout.json"
# The warm bed, not flow_soft: the top was taken off the same recording because
# the original reads as a tap running indoors. Shelved -10 dB from 2 kHz and
# re-normalised, which - measured - makes it LOUDER in raw energy than the file
# it came from even at equal LUFS. See engine/README.md, "Damping a bed makes it
# louder".
BED="${BED:-../../engine/sfx/flow_soft_warm_8s.m4a}"
# 1.0, not Micro's 0.8. Theirs is 0.8 because the bed competed with fifteen badge
# pops; there are none here, so the bed is the clip. Measured: at 0.8 this lands
# at -20.1 LUFS, two dB under every other variant, and at 1.0 it lands at -18.3 -
# which is where all three beds are normalised and where the other three ship.
# Carrying a constant across without its argument is the fault of the week.
BED_GAIN="${BED_GAIN:-1.0}"
FINALE="${FINALE:-6.38}"
SURGE="${SURGE:-0.30}"
DAY="$(date +%d.%m)"
OUT="${OUT:-../OUTPUT/$DAY/${TOPIC}_sfx.mp4}"

for f in "$POSTER" "$CLEAN" "$BASE" "$LAYOUT" "$BED"; do
    [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
done
mkdir -p "$(dirname "$OUT")"

echo "== liquid"
../.venv/bin/python ../../engine/flowanim.py "$POSTER" \
    --width 1080 --seconds 8 \
    --base "$CLEAN" --anchored "$BASE" --layout "$LAYOUT" \
    --drops 0 --reach 0 \
    --finale "$FINALE" --surge "$SURGE" --finale-cue "${TOPIC}_finale.txt" \
    -o "${TOPIC}_silent.mp4" "$@"

SECONDS_USED=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${TOPIC}_silent.mp4")

echo "== the chord"
../.venv/bin/python - "$TOPIC" "$SECONDS_USED" <<'PY'
import sys, os, wave
import numpy as np
sys.path.insert(0, os.path.join("..", "..", "engine"))
import impact
topic, seconds = sys.argv[1], float(sys.argv[2])
t0 = float(open(f"{topic}_finale.txt").read().strip())
x = impact.finale(t0, seconds)                     # the engine's level, not ours
d = (np.clip(x, -1, 1) * 32767).astype("<i2")
with wave.open(f"{topic}_chord.wav", "wb") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(impact.SR)
    f.writeframes(d.tobytes())
print(f"  chord at {t0:.2f}s of {seconds:.2f}s")
PY

# The chord is its own input at unity and never summed into another track that
# is about to be scaled - the fault that had it arriving 1.4 to 4.2 dB under the
# level it was chosen at in the two variants that did sum it.
FIN="$(cat "${TOPIC}_finale.txt")"
D0=$(awk -v t="$FIN" 'BEGIN{printf "%.2f", t-0.28}')
D1=$(awk -v t="$FIN" 'BEGIN{printf "%.2f", t+1.12}')
DUCK="volume='1-0.28*clip(min((t-${D0})/0.20,(${D1}-t)/0.35),0,1)':eval=frame"
echo "== water and picture   (bed ducked 2.9 dB over ${D0}-${D1}s)"

ffmpeg -y -loglevel error \
    -i "${TOPIC}_silent.mp4" -i "$BED" -i "${TOPIC}_chord.wav" \
    -filter_complex "[1:a]volume=${BED_GAIN},${DUCK}[w];[2:a]volume=1.0[f];\
[w][f]amix=inputs=2:duration=first:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[a]" \
    -map 0:v -map "[a]" -shortest \
    -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"

echo "wrote $OUT"
