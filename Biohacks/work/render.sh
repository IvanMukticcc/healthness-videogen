#!/usr/bin/env bash
# render.sh - a topic in, a finished clip out: liquid, glyphs, chips, dials,
# the day bar, the bed, the counters and the chord.
#
#   ./render.sh <topic> 'auto:HACK,...' <topic>_labelled.png
#
# **A CLIP IS ONLY A CLIP IF IT CAME FROM A GENERATED POSTER.** The loop is the
# same one every other variant in this repository follows:
#
#     1. build base_<topic>.png          recolor_base.py
#     2. write the prompt                ImageSwap.txt, filled, handed over whole
#     3. the user returns the image      grab.py, check_base, check_scene
#     4. caption it and render           add_labels.py, then this
#
# Without a poster this script renders a PREVIEW into work/ and refuses to touch
# OUTPUT/. The preview is worth having - it shows the layout, the rhythm and the
# dials before a generation is spent on the topic - but it is not the deliverable
# and OUTPUT/ is not where it goes. Three of them ended up in there on 8
# September because this script wrote to the same place either way.
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
#   --scene poster      the generator owns the left circle. Once the prompt was
#                       fixed to paint over the four alignment marks rather than
#                       around them, there is nothing left to cover and a disc
#                       there would only hide the photograph we asked for. Pass
#                       --scene glyph --scene-disc glass to put it back, which is
#                       what a poster that kept its marks needs
#   --dial-disc glass   the row is a photograph and has no colour for a disc to
#                       take: sampled at the left margin it returns a pixel of
#                       sky or grass and our components end up wearing the scene
#   --anchor-tol 0      no restoring the base. Both of the animator's base-repair
#   --halo 0            passes exist to remove a guide mark the artwork failed to
#                       cover, and both put the CLEAN BASE back where they fire -
#                       which is a flat row colour, and on a photograph that is a
#                       hard pale patch. --halo left pale rectangles lying on the
#                       liquid at the left tip of rows 2, 3 and 4; --anchor-tol
#                       left a flat rounded bar behind a caption. A faint grey
#                       mark the generator did not quite cover is a far smaller
#                       fault than a block of flat colour cut into the picture.
#
#                       (--anchor-r looks like the flag for this and is not:
#                       flowanim.py never reads it. The wipe is driven by
#                       --anchor-tol and the seal inside a circle by --halo.)
PHOTO=""
POSTER="${1:-}"
if [ -n "$POSTER" ] && [ -f "$POSTER" ]; then
    shift
    PHOTO="--scene poster --dial-disc glass --anchor-tol 0 --halo 0"
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
if [ -n "$PHOTO" ]; then
    OUT="../OUTPUT/$DAY/${TOPIC}_biohack.mp4"
    mkdir -p "../OUTPUT/$DAY"
else
    OUT="${TOPIC}_preview.mp4"
    echo "== PREVIEW: no poster, so this is not a deliverable"
    echo "   Glyphs stand in for the photographs, and it is written to work/."
    echo "   For a clip in OUTPUT/, hand over the prompt, grab the image back,"
    echo "   caption it, and pass it as the third argument."
fi

for f in "$POSTER" "$CLEAN" "$BASE" "$LAYOUT" "$BED"; do
    [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
done
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
