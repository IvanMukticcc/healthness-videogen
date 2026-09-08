#!/usr/bin/env bash
# render.sh - a protocol in, a finished clip out: the room, the fast, the hours.
#
#   ./render.sh hour168 16_8 hour168_labelled.png
#   ./render.sh hour168 16_8                       <- preview, no OUTPUT
#
# The third argument is the generated poster. Without one this renders a
# PREVIEW into work/<topic>_preview.mp4 and refuses to write to OUTPUT/, the
# distinction Biohacks had to learn on 8 September when three previews shipped
# as clips. A clip in OUTPUT/ came from a generated poster. Always.
#
# Anything after the third argument goes straight to flowanim.py.
set -euo pipefail
cd "$(dirname "$0")"

if [ $# -lt 2 ]; then
    sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
fi

TOPIC="$1"; PROTOCOL="$2"; POSTER="${3:-}"
[ $# -ge 3 ] && shift 3 || shift 2

BASE="../INPUT/base_${TOPIC}.png"
CLEAN="base_${TOPIC}_clean.png"
LAYOUT="base_${TOPIC}_layout.json"
BED="${BED:-../../engine/sfx/flow_soft_warm_8s.m4a}"
BED_GAIN="${BED_GAIN:-1.0}"
SURGE="${SURGE:-0.30}"
DAY="$(date +%d.%m)"

if [ -n "$POSTER" ] && [ -f "$POSTER" ]; then
    OUT="${OUT:-../OUTPUT/$DAY/${TOPIC}_longevity.mp4}"
    mkdir -p "$(dirname "$OUT")"
    echo "== clip: $POSTER"
else
    POSTER="$BASE"
    OUT="${TOPIC}_preview.mp4"
    echo "== PREVIEW - no poster, so this does not go to OUTPUT/"
    echo "   For a clip, hand over the prompt, grab the image back, caption it,"
    echo "   and pass it as the third argument."
fi

for f in "$POSTER" "$CLEAN" "$BASE" "$LAYOUT" "$BED"; do
    [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
done

echo "== the fast"
../.venv/bin/python ../../engine/flowanim.py "$POSTER" \
    --width 1080 --seconds 8 \
    --overlay fast_overlay --protocol "$PROTOCOL" \
    --base "$CLEAN" --anchored "$BASE" --layout "$LAYOUT" \
    --drops 0 --reach 0 \
    --finale auto --surge "$SURGE" \
    --fast-cues "${TOPIC}_cues.txt" --finale-cue "${TOPIC}_finale.txt" \
    -o "${TOPIC}_silent.mp4" "$@"

SECONDS_USED=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${TOPIC}_silent.mp4")

# The lock a dial makes when it arrives on its hour, and the chord at the end.
# Only reached rows sound: an unreached row is drawn but nothing happens there,
# and a sound would be the one thing that turns "the fast stops before here"
# into a claim about the stage.
echo "== locks and the chord"
../.venv/bin/python - "$TOPIC" "$SECONDS_USED" <<'PY'
import sys, os, wave
import numpy as np
sys.path.insert(0, os.path.join("..", "..", "engine"))
import impact
topic, seconds = sys.argv[1], float(sys.argv[2])
cues = [float(c) for c in open(f"{topic}_cues.txt").read().strip().split(",") if c]
per_row = [(i, 0) for i in range(len(cues))]
x = impact.build(cues, seconds, per_row, root=420.0)
t0 = float(open(f"{topic}_finale.txt").read().strip())
for path, arr in ((f"{topic}_locks.wav", x), (f"{topic}_chord.wav", impact.finale(t0, seconds))):
    d = (np.clip(arr, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(impact.SR)
        f.writeframes(d.tobytes())
print(f"  {len(cues)} locks, chord at {t0:.2f}s")
PY

FIN="$(cat "${TOPIC}_finale.txt")"
D0=$(awk -v t="$FIN" 'BEGIN{printf "%.2f", t-0.28}')
D1=$(awk -v t="$FIN" 'BEGIN{printf "%.2f", t+1.12}')
DUCK="volume='1-0.28*clip(min((t-${D0})/0.20,(${D1}-t)/0.35),0,1)':eval=frame"

echo "== water, locks, chord and picture"
ffmpeg -y -loglevel error \
    -i "${TOPIC}_silent.mp4" -i "$BED" -i "${TOPIC}_locks.wav" -i "${TOPIC}_chord.wav" \
    -filter_complex "[1:a]volume=${BED_GAIN},${DUCK}[w];[2:a]volume=0.62[p];\
[3:a]volume=1.0[f];[w][p][f]amix=inputs=3:duration=first:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[a]" \
    -map 0:v -map "[a]" -shortest \
    -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"

echo "wrote $OUT"
