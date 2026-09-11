#!/usr/bin/env bash
# render2.sh - the two-act cut: act one, the card turning over, the numbers.
#
# render.sh is untouched and still makes the one-act clip. This puts a second act
# behind a shipped one WITHOUT rebuilding the first: act one's video and its
# audio come straight out of the finished clip.
#
#   ./render2.sh pressure
#   OUT=somewhere/else.mp4 ./render2.sh liver
#
# WHY IT READS THE SHIPPED CLIP RATHER THAN RE-RENDERING
#
# Nine of the twenty-five topics still have `<topic>_silent.mp4` and their pop
# and riser wavs in work/; sixteen do not, and rebuilding those from the labelled
# poster would run them through an engine that has moved a long way since
# 9 September - a different finale, different badge timing, a different mix. The
# clip would gain a second act and quietly lose the first one it shipped with.
#
# The finished clip already IS act one: the badges are baked into its picture and
# its sound is the mix that was approved. So the video is trimmed from it, the
# audio is taken whole and faded through the turn, and the first act of the new
# cut is the first act of the old one, frame for frame. Only `<topic>_finale.txt`
# is needed from work/, for the instant to cut on.
#
# Nothing lands in a day folder. ../OUTPUT/two_acts/ sits beside Done/, so 09.09
# and 10.09 keep holding exactly what shipped (../CLAUDE.md rule 5).
set -euo pipefail
cd "$(dirname "$0")"

TOPIC="${1:?usage: ./render2.sh <topic>}"
FPS="${FPS:-24}"
# 6.4 rather than 7.0: the chord has decayed by 13.6s of the finished clip and
# 7.0 left 1.4s of dead air under a picture that had stopped moving. 6.4 holds
# the finished card for 2.2s after the last thing lands, which is long enough to
# read the score and short enough not to be silence. ACT2_S=7.0 puts it back.
ACT2_S="${ACT2_S:-6.4}"
FLIP_N="${FLIP_N:-14}"                  # 0.583s at 24fps, as Macro's turn
LANG_="${LANG_:-en}"
ACT2_GAIN="${ACT2_GAIN:-1.0}"
# THE WATER IS BACKGROUND AND WAS NOT BEHAVING LIKE IT. Measured on the shipped
# mix, the bed sat 5.0 dB under the badge pops; at 0.40 it sits 10.0 dB under,
# and the pops themselves barely move (-15.9 to -16.9 across the whole range).
# So this foregrounds the badges rather than quietening the clip - the bed was
# eating the headroom they needed. render.sh takes the same number for new clips.
#
# 0.30 after hearing 0.40, and this is the floor. The beds are normalised to
# -18 LUFS, so at 0.30 the water sits more than 11 dB under its own reference:
# below this it stops reading as a room and starts sounding like an effect left
# on by mistake. If it is still too present, the answer is a different bed -
# there are four in engine/sfx/ and none has been tried this quiet - not a
# smaller number.
BED="${BED:-../../engine/sfx/flow_soft_warmer_8s.m4a}"
BED_GAIN="${BED_GAIN:-0.30}"
POP_GAIN="${POP_GAIN:-0.85}"
PY=../.venv/bin/python
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# The shipped clip, wherever it is. Falls back to the silent pass for a topic
# that has not shipped yet.
# DAY FOLDERS ONLY, and never the folder this script writes into.
#
# `../OUTPUT/*/` used to be the search and it started matching ../OUTPUT/two_acts/
# the moment that folder existed. For the eight topics that shipped inside
# 09.09/FOOD/ - not directly in a day folder - the day-folder pattern missed and
# the two-act pattern hit, so a re-render read its own previous output as act
# one. The trim still produced act one's frames, so the clip looked plausible;
# what came out wrong was everything downstream of it - the flip turned in front
# of the PREVIOUS TURN's frames, and act two's frosted backdrop walked into the
# previous act two, so the old card was ghosting behind the new one.
#
# `[0-9]*` matches 09.09 and 10.09 and cannot match two_acts or Done.
ACT1="${ACT1:-}"
if [ -z "$ACT1" ]; then
    for c in ../OUTPUT/[0-9]*/"${TOPIC}_micro.mp4" ../OUTPUT/[0-9]*/*/"${TOPIC}_micro.mp4"; do
        [ -f "$c" ] && ACT1="$c" && break
    done
fi
[ -n "$ACT1" ] || ACT1="${TOPIC}_silent.mp4"
[ -f "$ACT1" ] || { echo "no act one for $TOPIC - looked in ../OUTPUT and work/"; exit 1; }
[ -f "${TOPIC}_finale.txt" ] || { echo "no ${TOPIC}_finale.txt - it says where to cut"; exit 1; }

OUT="${OUT:-../OUTPUT/two_acts/${TOPIC}_micro.mp4}"
mkdir -p "$(dirname "$OUT")"
# And a belt to the braces above: reading the file we are about to overwrite
# produces a clip that is wrong in ways no check here would catch.
if [ "$(cd "$(dirname "$ACT1")" && pwd)" = "$(cd "$(dirname "$OUT")" && pwd)" ]; then
    echo "act one would be read from the folder OUT writes into: $ACT1" >&2
    exit 1
fi

# ACT TWO IS RENDERED AT ACT ONE'S SIZE, WHICH IS NOT 1080x1920.
#
# The poster is 1536x2752, so act one is 1080x1934 - fourteen pixels taller than
# a phone frame. Rendered at 1080x1920 and concatenated with -c copy, which does
# not resample, the container keeps 1934 and every frame after the turn arrives
# at 1920. ffmpeg decodes that happily, so every check passes and every frame
# grab looks right; QuickTime holds act two's FIRST frame to the end of the clip.
W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$ACT1")
H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$ACT1")

FIN=$(cat "${TOPIC}_finale.txt")
ACT1_N=$(awk -v f="$FIN" -v r="$FPS" 'BEGIN{printf "%d", int((f + 1.0) * r + 0.5)}')
FINALE_N=$(awk -v f="$FIN" -v r="$FPS" 'BEGIN{printf "%d", int(f * r + 0.5)}')
ACT1_S=$(awk -v n="$ACT1_N" -v r="$FPS" 'BEGIN{printf "%.4f", n / r}')
FLIP_S=$(awk -v n="$FLIP_N" -v r="$FPS" 'BEGIN{printf "%.4f", n / r}')

# Act one is cut a beat after it stops moving rather than at its loop point: the
# loop existed so the clip could repeat, and nothing repeats once a second act
# follows it. The finale settles ~0.8s after its instant, so +1.0s is the beat.
echo "== $TOPIC: act one from $(basename "$(dirname "$ACT1")")/$(basename "$ACT1"), cut at ${ACT1_S}s"
ffmpeg -v error -i "$ACT1" -frames:v "$ACT1_N" -an -c:v libx264 -preset slow -crf 16 \
    -pix_fmt yuv420p "$TMP/act1shown.mp4" -y
# ACT ONE'S SOUND IS REBUILT FROM ITS CUES, NOT LIFTED OFF THE CLIP.
#
# Taking the finished mix whole is what kept act one identical, and it is also
# what made the water untouchable: bed, pops and riser are one stream in there
# and no filter separates them. Every topic still has `<topic>_cues.txt` and
# `<topic>_finale.txt`, and the synthesis is deterministic from those, so the
# mix can be made again with the same badge landings and a quieter bed. The
# PICTURE is still the shipped one, frame for frame - only the sound is rebuilt.
$PY micro_audio.py --cues-file "${TOPIC}_cues.txt" --seconds 8 \
    --finale-file "${TOPIC}_finale.txt" --finale-out "$TMP/riser.wav" \
    -o "$TMP/pops.wav" >/dev/null
DUCK="anull"
if [ -s "${TOPIC}_finale.txt" ]; then
    D0="$(awk -v t="$FIN" 'BEGIN{printf "%.2f", t - 0.28}')"
    D1="$(awk -v t="$FIN" 'BEGIN{printf "%.2f", t + 1.12}')"
    DUCK="volume='1-0.28*clip(min((t-${D0})/0.20,(${D1}-t)/0.35),0,1)':eval=frame"
fi
ffmpeg -v error -i "$BED" -i "$TMP/pops.wav" -i "$TMP/riser.wav" \
    -filter_complex "[0:a]volume=${BED_GAIN},${DUCK}[w];[1:a]volume=${POP_GAIN}[p];\
[2:a]volume=1.0[f];[w][p][f]amix=inputs=3:duration=first:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[a]" \
    -map "[a]" -ac 2 -ar 48000 "$TMP/act1.wav" -y

# Face A is the last frame the viewer saw; the backdrops are act one CONTINUING
# past it, so the poster keeps moving while the card turns in front of it.
ffmpeg -v error -i "$TMP/act1shown.mp4" -vf "select=eq(n\,$((ACT1_N - 1)))" \
    -vsync 0 -frames:v 1 "$TMP/a.png" -y
mkdir -p "$TMP/bd"
ffmpeg -v error -i "$ACT1" -vf "select=between(n\,${ACT1_N}\,$((ACT1_N + FLIP_N - 1)))" \
    -vsync 0 "$TMP/bd/f%05d.png" -y

# --behind-lo is the finale frame, and the walk bounces inside [finale, end]
# rather than wrapping: act one loops in liquid but NOT in content - the badges
# accumulate and never reset - so frame 0 and the last frame differ by a whole
# poster's worth of badges. Every frame from the finale on carries all fifteen.
$PY micro_card.py --topic "$TOPIC" --lang "$LANG_" \
    --seconds "$ACT2_S" --fps "$FPS" --width "$W" --height "$H" \
    --behind "$ACT1" --behind-offset "$(( ACT1_N + FLIP_N ))" --behind-lo "$FINALE_N" \
    --cues "${TOPIC}_act2.json" --first-frame "$TMP/b.png" -o "$TMP/act2.mp4"

$PY ../../engine/flip.py "$TMP/a.png" "$TMP/b.png" \
    --out-dir "$TMP/turn" --frames "$FLIP_N" --backdrop-dir "$TMP/bd" >/dev/null
ffmpeg -v error -framerate "$FPS" -i "$TMP/turn/f%05d.png" \
    -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p "$TMP/turn.mp4" -y

printf "file '%s'\nfile '%s'\nfile '%s'\n" \
    "$TMP/act1shown.mp4" "$TMP/turn.mp4" "$TMP/act2.mp4" > "$TMP/list"
ffmpeg -v error -f concat -safe 0 -i "$TMP/list" -c:v copy "$TMP/silent.mp4" -y

$PY micro_audio.py --act2-cues "${TOPIC}_act2.json" --act2-seconds "$ACT2_S" \
    --flip-seconds "$FLIP_S" --act2-out "${TOPIC}_act2.wav"

# Act one's sound is the shipped mix, unchanged, and it fades THROUGH the turn
# rather than stopping at the cut: a bed that ends on act one's last frame makes
# the join audible as a join. Act two comes in at unity behind it.
DELAY=$(awk -v s="$ACT1_S" 'BEGIN{printf "%d", s * 1000}')
FADE0=$(awk -v s="$ACT1_S" 'BEGIN{printf "%.3f", s - 0.10}')
ffmpeg -v error -i "$TMP/silent.mp4" -i "$TMP/act1.wav" -i "${TOPIC}_act2.wav" \
    -filter_complex "\
[1:a]afade=t=out:st=${FADE0}:d=0.75[w];\
[2:a]volume=${ACT2_GAIN},adelay=${DELAY}|${DELAY}[c];\
[w][c]amix=inputs=2:duration=longest:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[a]" \
    -map 0:v -map "[a]" -shortest \
    -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT" -y

echo "   -> $OUT  (act one ${ACT1_S}s + turn ${FLIP_S}s + act two ${ACT2_S}s)"
