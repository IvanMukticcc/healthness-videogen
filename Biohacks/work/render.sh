#!/usr/bin/env bash
# render.sh - a topic in, a finished clip out: liquid, glyphs, chips, dials,
# the day bar, the bed, the counters and the chord.
#
#   ./render.sh day 'auto:MORNING LIGHT,COLD FINISH,WALK AFTER LUNCH,LAST COFFEE,LIGHTS DOWN'
#
# **There is no poster argument.** That is the difference between this variant
# and the two beside it. Both circles are drawn here - a lucide glyph on the
# left, a dial on the right - so the base built by recolor_base.py and captioned
# by add_labels.py is the whole input, and nothing has to be generated, checked,
# fetched out of Downloads or looked at by eye before the render starts.
#
# SCENE MODE: for a topic whose rows are photographs, pass the labelled poster
# as $3. That alone switches it - glass discs, glass dials, and the guide-circle
# wipe off, because the generator paints around our marks rather than over them.
#
#   ./render.sh firsthour 'auto:...' firsthour_labelled.png
#
# Everything after that goes straight to flowanim.py, so --hack-times,
# --dial-count, --chip-h, --daybar and the rest are available untouched.
#
# THE THREE STEPS AGREE THROUGH FILES, NEVER THROUGH TYPING. flowanim.py writes
# the chip landings, the dial counts and the finale's instant; biohack_audio.py
# reads all three. A tick train typed a second time drifts by a frame, and half
# a frame of drift on a counter is the one thing an ear hears immediately.
set -euo pipefail
cd "$(dirname "$0")"          # work/, where this variant's own code lives

if [ $# -lt 2 ]; then
    sed -n '2,23p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
fi

TOPIC="$1"; HACKS="$2"; shift 2
# A poster given as $3 IS scene mode - it is the only reason to pass one - so the
# four flags that mode needs are switched on here rather than remembered. Anything
# after it still goes to flowanim.py and still wins, argparse taking the last
# value it is given.
#
#   --scene-disc glass  the row is a photograph and has no colour for a disc to
#   --dial-disc glass   take: sampled at the left margin it returns a pixel of
#                       sky or grass and our components end up wearing the scene
#   --anchor-r 0        the generator paints AROUND the guide circles rather than
#                       over them, so the poster still matches the anchored base
#                       inside them - and the wipe would then punch a disc of
#                       flat row colour into the photograph. Measured on the
#                       first scene poster: |poster - base| is 2-3 levels inside
#                       every circle, against std 47 in the photograph beside it
PHOTO=""
POSTER="${1:-}"
if [ -n "$POSTER" ] && [ -f "$POSTER" ]; then
    shift
    PHOTO="--scene-disc glass --dial-disc glass --anchor-r 0"
    echo "== scene mode: $POSTER"
else
    POSTER="${TOPIC}_labelled.png"
fi

# The base itself lives in INPUT and only there - it is the file a person opens.
# Its clean copy and its layout are working files and stay here.
BASE="${BASE:-../INPUT/base_${TOPIC}.png}"
CLEAN="base_${TOPIC}_clean.png"
LAYOUT="base_${TOPIC}_layout.json"
BED="${BED:-biohack_bed_8s.m4a}"
WIDTH="${WIDTH:-1080}"        # 540 while tuning: same timing, a third of the wait

# Fixed gains and a limiter rather than loudnorm, for the reason both other
# variants give: the bed is already normalised to -18.4 LUFS and everything else
# in here is a transient, and single-pass loudnorm pumps the bed down under every
# one of them.
#
# 0.62 for the chips, not Micro's 0.85. There is more going on per row here - a
# chip, sixteen ticks and a lock - and at 0.85 the chip masked the first four
# ticks of its own counter, which is the half of the sound that is new.
CHIP_GAIN="${CHIP_GAIN:-0.62}"
TICK_GAIN="${TICK_GAIN:-0.30}"
SFX_GAIN="${SFX_GAIN:-0.80}"
BED_GAIN="${BED_GAIN:-1.0}"
DAY="$(date +%d.%m)"
OUT="../OUTPUT/$DAY/${TOPIC}_biohack.mp4"

for f in "$POSTER" "$CLEAN" "$BASE" "$LAYOUT" "$BED"; do
    [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
done
mkdir -p "../OUTPUT/$DAY"

echo "== liquid, glyphs, chips, dials and the day bar"
# --overlay order is the order they draw in, and it is left circle, right circle,
# then everything that is not in a circle. The chip is last so it is never behind
# anything; the day bar is in the same module because it is the same idea - the
# two elements that are about the viewer's day rather than about a row.
#
# --finale-lead 0.50, not the engine's 0.60. The lead exists to clear whatever
# the last cue started, and here the last cue *is* the dial settling - the count
# is already over when it is reported, so there is nothing left to clear but the
# 0.06s the lock rings for.
../../.venv/bin/python ../../engine/flowanim.py "$POSTER" \
    --width "$WIDTH" --seconds 8 \
    --overlay scene_overlay,dial_overlay,day_overlay \
    --base "$CLEAN" --anchored "$BASE" --layout "$LAYOUT" \
    --drops 0 --reach 0 \
    --hacks "$HACKS" \
    --chip-cues "${TOPIC}_chips.txt" \
    --dial-cues "${TOPIC}_dials.txt" \
    --finale auto --finale-lead 0.50 --finale-cue "${TOPIC}_finale.txt" \
    --surge 0.30 --surge-dur 0.34 --surge-stagger 0.05 \
    $PHOTO -o "${TOPIC}_silent.mp4" "$@"

SECONDS_USED=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${TOPIC}_silent.mp4")

echo "== chips, counters and the chord"
../../.venv/bin/python biohack_audio.py \
    --cues-file "${TOPIC}_chips.txt" \
    --dials "${TOPIC}_dials.txt" \
    --finale-cue "${TOPIC}_finale.txt" \
    --chip-gain "$CHIP_GAIN" --tick-gain "$TICK_GAIN" \
    --seconds "$SECONDS_USED" -o "${TOPIC}_sfx.wav"

# The bed steps back under the finale and comes straight back, on a window read
# from the instant flowanim wrote rather than typed again here - so the duck
# cannot drift away from the thing it is ducking for.
DUCK="anull"
if [ -s "${TOPIC}_finale.txt" ]; then
    T="$(cat "${TOPIC}_finale.txt")"
    D0="$(awk -v t="$T" 'BEGIN{printf "%.2f", t - 0.28}')"
    D1="$(awk -v t="$T" 'BEGIN{printf "%.2f", t + 1.12}')"
    DUCK="volume='1-0.28*clip(min((t-${D0})/0.20,(${D1}-t)/0.35),0,1)':eval=frame"
    echo "   bed ducked 2.9 dB over ${D0}-${D1}s, around the finale at ${T}s"
fi

echo "== bed, sfx and picture"
# level=disabled matters. alimiter auto-levels its output back to 0 dB unless it
# is told not to, so without it the limit is applied and then immediately undone.
ffmpeg -y -loglevel error \
    -i "${TOPIC}_silent.mp4" -i "$BED" -i "${TOPIC}_sfx.wav" \
    -filter_complex "[1:a]volume=${BED_GAIN},${DUCK}[w];[2:a]volume=${SFX_GAIN}[p];\
[w][p]amix=inputs=2:duration=first:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[a]" \
    -map 0:v -map "[a]" -shortest \
    -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"

echo "wrote $OUT"
