#!/usr/bin/env bash
# render.sh - poster in, finished clip out: liquid, badges, water and pops.
#
# The three steps have to agree on when the badges land, and they do it through
# one file: flowanim.py writes the landing times it actually used, micro_audio.py
# reads them. Typing the times twice is how a pop ends up half a frame off the
# badge it belongs to, which reads as a sync fault even when nobody can say why.
#
#   ./render.sh liver work/liver_labelled.png 'auto:LEAFY GREENS,BEETROOT,TURMERIC,BROCCOLI,COFFEE'
#
# Anything after the third argument goes straight to flowanim.py, so
# --micro-d, --micro-times, --seconds and the rest are available untouched.
set -euo pipefail
cd "$(dirname "$0")"

if [ $# -lt 3 ]; then
    sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
fi

TOPIC="$1"; POSTER="$2"; MICRO="$3"; shift 3
DIR="$(dirname "$POSTER")"
BED="${BED:-ASSETS/flow_soft_8s.m4a}"
POP_GAIN="${POP_GAIN:-0.6}"
BED_GAIN="${BED_GAIN:-1.0}"
DAY="$(date +%d.%m)"
OUT="OUTPUT/$DAY/${TOPIC}_micro.mp4"

for f in "$POSTER" "$DIR/base_${TOPIC}_clean.png" "$DIR/base_${TOPIC}.png" \
         "$DIR/base_${TOPIC}_layout.json" "$BED"; do
    [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
done
mkdir -p "OUTPUT/$DAY" work

echo "== liquid and badges"
.venv/bin/python ../engine/flowanim.py "$POSTER" \
    --width 1080 --seconds 8 \
    --overlay micro_overlay \
    --base "$DIR/base_${TOPIC}_clean.png" \
    --anchored "$DIR/base_${TOPIC}.png" \
    --layout "$DIR/base_${TOPIC}_layout.json" \
    --drops 0 --reach 0 \
    --micro "$MICRO" --micro-cues "work/${TOPIC}_cues.txt" \
    -o "work/${TOPIC}_silent.mp4" "$@"

SECONDS_USED=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "work/${TOPIC}_silent.mp4")

echo "== pops"
.venv/bin/python micro_audio.py --cues-file "work/${TOPIC}_cues.txt" \
    --seconds "$SECONDS_USED" -o "work/${TOPIC}_pops.wav"

echo "== water, pops and picture"
# Fixed gains and a limiter rather than loudnorm: the bed is already normalised
# to -18 LUFS and the pops are transients, and single-pass loudnorm pumps the
# water down under every one of them. These three numbers were measured, not
# guessed: they land the finished clip on -18 LUFS with about -1.4 dBTP, which is
# where the water beds were normalised in the first place.
# level=disabled matters. alimiter auto-levels its output back to 0 dB unless it
# is told not to, so without it the limit is applied and then immediately undone
# - the first cut of this measured -0.1 dBTP with the limiter apparently on.
ffmpeg -y -loglevel error \
    -i "work/${TOPIC}_silent.mp4" -i "$BED" -i "work/${TOPIC}_pops.wav" \
    -filter_complex "[1:a]volume=${BED_GAIN}[w];[2:a]volume=${POP_GAIN}[p];\
[w][p]amix=inputs=2:duration=first:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[a]" \
    -map 0:v -map "[a]" -shortest \
    -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"

echo "wrote $OUT"
