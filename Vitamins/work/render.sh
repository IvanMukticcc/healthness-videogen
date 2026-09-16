#!/usr/bin/env bash
# render.sh - poster in, finished two-act clip out.
#
# Act one is the poster: five bowls, the liquid running, the headline vitamin
# lighting in each right circle, the other two badges popping on the row. It has
# NO finale - no surge, no chord, nothing that announces an ending - because in
# this variant act one is not the end. The card turns over and act two answers
# the question act one raises: if you ate these five, what did you actually get?
#
#   ./render.sh demo
#   ./render.sh demo demo_labelled.png        an explicitly named poster
#   ACT1_ONLY=1 ./render.sh demo              stop after act one, for auditioning
#
# Anything after the second argument goes straight to flowanim.py, so --micro-d,
# --vitamin-d, --seconds and the rest are available untouched.
#
# NOTHING HERE RETYPES A FOOD, A VITAMIN OR A BADGE. vitamins.py derives all
# three from topics.json, which is the one place a topic is authored
# (../../CLAUDE.md rule 13). A spec typed on a command line is a spec that can
# disagree with the poster it is being drawn on, and there is no file to check it
# against afterwards - which is exactly how Micro's badge lists came to exist
# only in the pixels of finished clips.
set -euo pipefail
cd "$(dirname "$0")"          # work/, where this variant's own code lives

if [ $# -lt 1 ]; then
    sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
fi

TOPIC="$1"; shift
POSTER="${1:-${TOPIC}_labelled.png}"
[ $# -gt 0 ] && shift
DIR="$(dirname "$POSTER")"
PY=../.venv/bin/python

# The base image itself lives in INPUT and only there - it is the file that gets
# attached to the prompt, and INPUT holds nothing else (../../CLAUDE.md rule 7).
# Its clean copy and its layout are working files and stay beside the poster.
BASE="${BASE:-../INPUT/base_${TOPIC}.png}"
ANCHORED="$DIR/base_${TOPIC}.png"
[ -f "$ANCHORED" ] || ANCHORED="../INPUT/base_${TOPIC}.png"
WIDTH="${WIDTH:-1080}"          # 540 while tuning: 26s a render against 66s, same timing

for f in "$POSTER" "$DIR/base_${TOPIC}_clean.png" "$ANCHORED" \
         "$DIR/base_${TOPIC}_layout.json"; do
    [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
done

# ONE RHYTHM, TWO FLAGS, AND THAT IS ON PURPOSE.
#
# Both overlays want the same five instants. The obvious economy is for one of
# them to read the flag the other declares, and Biohacks did exactly that: its
# three overlays stopped being runnable separately at all, throwing
# `AttributeError: 'Namespace' object has no attribute 'dial_lead'` from a module
# that had declared nothing wrong. So each declares its own and this variable is
# the single source they are both filled from.
#
# 0.25,1.35,2.45,3.55,4.65 is Organs' rhythm and Macro's spacing, so the three
# read as one series. The first pop lands inside 0.3s, which is most of the
# window a vertical feed gives a clip before the thumb moves.
TIMES="${TIMES:-0.25,1.35,2.45,3.55,4.65}"

VITAMINS="${VITAMINS:-$($PY vitamins.py "$TOPIC" --vitamins)}"
BADGES="${BADGES:-$($PY vitamins.py "$TOPIC" --badges)}"
echo "== $TOPIC: right circles $VITAMINS"
echo "   badges $BADGES"

# A finale file left over from a single-act experiment would make render2.sh
# refuse, and rightly - it means act one carries the surge glow. --finale off
# writes none, so the file's presence can only ever mean a previous run did.
rm -f "${TOPIC}_finale.txt"

echo "== liquid, balls and badges"
# vitamin_overlay FIRST: overlays draw in the order they are named, and a badge
# that ever reaches the right circle should be in front of the ball rather than
# behind it. They do not overlap today - the badges live in the gap between the
# two circles - but the order costs nothing and the day one of them shrinks to
# fit is not the day to discover it.
$PY ../../engine/flowanim.py "$POSTER" \
    --width "$WIDTH" --seconds 8 \
    --overlay vitamin_overlay,micro_overlay \
    --base "$DIR/base_${TOPIC}_clean.png" \
    --anchored "$ANCHORED" \
    --layout "$DIR/base_${TOPIC}_layout.json" \
    --drops 0 --reach 0 \
    --vitamin "$VITAMINS" --vitamin-times "$TIMES" \
    --micro "$BADGES" --micro-cues "${TOPIC}_cues.txt" \
    --micro-times "$TIMES" \
    --micro-organ 0 \
    --finale off \
    -o "${TOPIC}_silent.mp4" "$@"

# --micro-organ 0 is not an optimisation. micro_overlay finds the right circle's
# artwork by difference from the clean base and lights it; in this variant there
# IS no artwork there, the circle is empty by construction, and the search would
# print "nothing found in the right circle" five times and do nothing. The ball
# is vitamin_overlay's and it is drawn, not found.

if [ "${ACT1_ONLY:-0}" = 1 ]; then
    OUT="${OUT:-${TOPIC}_act1.mp4}"
    SECONDS_USED=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${TOPIC}_silent.mp4")
    $PY ../../engine/micro_audio.py --cues-file "${TOPIC}_cues.txt" \
        --seconds "$SECONDS_USED" -o "${TOPIC}_pops.wav"
    ffmpeg -y -loglevel error -i "${TOPIC}_silent.mp4" \
        -i ../../engine/sfx/flow_soft_warmer_8s.m4a -i "${TOPIC}_pops.wav" \
        -filter_complex "[1:a]volume=0.30[w];[2:a]volume=0.85[p];\
[w][p]amix=inputs=2:duration=first:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[a]" \
        -map 0:v -map "[a]" -shortest \
        -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"
    echo "act one only -> $OUT  (NOT a deliverable: rule 6 wants the whole clip)"
    exit 0
fi

echo "== the turn and the card"
exec ./render2.sh "$TOPIC"
