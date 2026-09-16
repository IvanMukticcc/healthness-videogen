#!/usr/bin/env bash
# render2.sh - the turn and the card: act one, the window turning over, the numbers.
#
#   ./render.sh demo            the whole clip - this is what you want
#   ./render2.sh demo           the turn and the card onto an act one already rendered
#   OUT=somewhere/else.mp4 ./render2.sh demo
#
# `render.sh` calls this as its last step, so it is rarely run by hand. On its own
# it is what re-cuts act two - a different card, a different length, a fixed
# score - without spending the ninety seconds act one costs.
#
# WHERE ACT ONE'S PICTURE AND ITS SOUND EACH COME FROM, AND WHY THEY DIFFER
#
# The PICTURE is trimmed from `<topic>_silent.mp4`, which render.sh has just
# written: the badges and the balls are baked into it and nothing here can or
# should redraw them.
#
# The SOUND is rebuilt from `<topic>_cues.txt` rather than lifted off a finished
# mix. That is not a convenience. Taking the mix whole is what once kept act one
# byte-identical through a retrofit, and it is also what made the water
# untouchable, because bed, pops and riser are one stream in a finished file and
# no filter separates them. The cues are on disk, the synthesis is deterministic
# from them, so the mix can be made again with the same badge landings and a
# different bed. This file inherited that arrangement from Micro's two-act cut,
# where act one was a clip that had already shipped; here act one is ninety
# seconds old, and the arrangement is still the right one for the second reason.
#
# The finished clip goes to ../../OUTPUT/VITAMINS/ (../../CLAUDE.md rule 12):
# flat, per category, no dates. ../../OUTPUT/DONE/VITAMINS/ is what has gone out,
# the user fills it by hand, and nothing here writes to it.
set -euo pipefail
cd "$(dirname "$0")"

TOPIC="${1:?usage: ./render2.sh <topic>}"
FPS="${FPS:-24}"
# 6.4 rather than 7.0: the chord has decayed by 13.6s of the finished clip and
# 7.0 left 1.4s of dead air under a picture that had stopped moving. 6.4 holds
# the finished card for 2.2s after the last thing lands, which is long enough to
# read the score and short enough not to be silence. ACT2_S=7.0 puts it back.
# `auto`: micro_card works out where the last visible change is and makes act
# two one second longer than that. A fixed length was what left the picture
# finished and the clip still running - the user counted three seconds of it.
ACT2_S="${ACT2_S:-auto}"
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

# WHERE ACT ONE COMES FROM, IN ORDER, AND NEVER FROM WHERE WE WRITE.
#
# Under rule 12 the deliverable is `OUTPUT/VITAMINS/<topic>_vitamins.mp4` and it
# is the TWO-ACT cut, so act one and the finished clip share a filename - and
# reading act one from the folder this script writes into would be the same fault
# that once produced clips turning in front of their own previous turn. The
# folder used to be per-variant and per-day, which made that read safe; rule 12
# made it flat and shared, and nobody edited a line of this script. When a folder
# changes hands, re-ask what reads it.
#
#   1. work/<topic>_silent.mp4   the real intermediate, and since the sound is
#                                rebuilt from the cue files this is all that is
#                                needed - the picture
#   2. OUTPUT/DONE/VITAMINS/     the user's published copy. Read-only by rule 12,
#                                which makes it safe to read
#   3. ACT1=... given explicitly, for anything else
#
# OUTPUT/VITAMINS is deliberately NOT in the list. Pass ACT1= if you mean it.
ACT1="${ACT1:-}"
if [ -z "$ACT1" ]; then
    for c in "${TOPIC}_silent.mp4" ../../OUTPUT/DONE/VITAMINS/"${TOPIC}_vitamins.mp4"; do
        [ -f "$c" ] && ACT1="$c" && break
    done
fi
[ -f "$ACT1" ] || { echo "no act one for $TOPIC - looked in ../OUTPUT and work/"; exit 1; }
# The cut now comes from the badge cues, not from a finale instant.
[ -f "${TOPIC}_cues.txt" ] || { echo "no ${TOPIC}_cues.txt - it says where the badges land"; exit 1; }

OUT="${OUT:-../../OUTPUT/VITAMINS/${TOPIC}_vitamins.mp4}"
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

# WHERE ACT ONE ENDS, NOW THAT IT HAS NO FINALE.
#
# It used to end a beat after the finale settled. The finale is gone from the
# two-act cut - it announced an ending in the middle of a clip, and the user was
# hearing act one's chord as the real one - so the cut is measured from the last
# badge instead: **half a second after it is ON SCREEN**, not after its cue.
#
# The two are 0.47s apart and that gap is the whole reason this rule is written
# this way. Measured on part 24: the last cue is 5.780 and the badge band stops
# changing at 6.25, so the badge is still arriving for nearly half a second after
# the sound that announces it. Cutting at cue + 0.5 would start the turn while
# the thing the viewer is watching is still moving.
SETTLE="${SETTLE:-0.47}"          # cue -> fully on screen, measured
# 0.25 from 0.50 on 12 September, and the reason it moved is not that half a
# second was always wrong - it is that what fills the space changed. The gap used
# to be measured from the end of the finale surge, so the eye had just watched
# something large finish; now it is measured from one small badge settling, and
# half a second after that is a different half-second entirely.
#
# 0.12 is the floor and it is known rather than guessed: at that value this
# morning the turn read as no pause at all. Two frames is a cut; six is a beat.
GAP="${GAP:-0.25}"
LASTCUE=$(awk -F, '{print $NF}' "${TOPIC}_cues.txt")
ACT1_S_RAW=$(awk -v c="$LASTCUE" -v s="$SETTLE" -v g="$GAP" 'BEGIN{printf "%.4f", c + s + g}')
ACT1_N=$(awk -v t="$ACT1_S_RAW" -v r="$FPS" 'BEGIN{printf "%d", int(t * r + 0.5)}')
FINALE_N=$(( ACT1_N - 1 ))        # the walk's floor: the last frame of act one

# A finale file means act one was rendered WITH the surge, and the glow is in the
# picture - cutting at 6.75 would show it and then cut away from it. Refuse
# rather than ship a clip that announces an ending it does not have.
if [ -s "${TOPIC}_finale.txt" ]; then
    echo "${TOPIC}_finale.txt exists, so act one carries the finale glow." >&2
    echo "  FINALE=off ./render.sh ${TOPIC} <poster> <badges>   re-render it without" >&2
    exit 1
fi
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
# No finale means no riser and no duck: the duck existed to step the water back
# under the chord, and there is no chord in act one any more. Act two's landing
# is the clip's only one, which is the point of the change.
$PY ../../engine/micro_audio.py --cues-file "${TOPIC}_cues.txt" --seconds 8 \
    -o "$TMP/pops.wav" >/dev/null
ffmpeg -v error -i "$BED" -i "$TMP/pops.wav" \
    -filter_complex "[0:a]volume=${BED_GAIN}[w];[1:a]volume=${POP_GAIN}[p];\
[w][p]amix=inputs=2:duration=first:normalize=0[m];\
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

# micro_card decides the length when ACT2_S is `auto`, so the real number comes
# back out of the cue file it just wrote rather than being assumed here.
ACT2_S=$($PY -c "import json;print(json.load(open('${TOPIC}_act2.json'))['seconds'])")
$PY ../../engine/micro_audio.py --act2-cues "${TOPIC}_act2.json" --act2-seconds "$ACT2_S" \
    --flip-seconds "$FLIP_S" --act2-out "${TOPIC}_act2.wav"

# Act one's sound is the shipped mix, unchanged, and it fades THROUGH the turn
# rather than stopping at the cut: a bed that ends on act one's last frame makes
# the join audible as a join. Act two comes in at unity behind it.
# The chord is still ringing when the clip ends - it has to be, since the clip
# ends one second after the chord lands and the chord runs 2.6. Cutting it there
# is audible at about -9 dB; 0.15s of fade takes the rest without reading as a
# cut. Fade AFTER the limiter, or the limiter puts back what the fade removed.
TOTAL=$(awk -v a="$ACT1_S" -v f="$FLIP_S" -v b="$ACT2_S" 'BEGIN{printf "%.4f", a+f+b}')
FADE_END=$(awk -v t="$TOTAL" 'BEGIN{printf "%.4f", t - 0.15}')
DELAY=$(awk -v s="$ACT1_S" 'BEGIN{printf "%d", s * 1000}')
FADE0=$(awk -v s="$ACT1_S" 'BEGIN{printf "%.3f", s - 0.10}')
ffmpeg -v error -i "$TMP/silent.mp4" -i "$TMP/act1.wav" -i "${TOPIC}_act2.wav" \
    -filter_complex "\
[1:a]afade=t=out:st=${FADE0}:d=0.75[w];\
[2:a]volume=${ACT2_GAIN},adelay=${DELAY}|${DELAY}[c];\
[w][c]amix=inputs=2:duration=longest:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[l];\
[l]afade=t=out:st=${FADE_END}:d=0.15[a]" \
    -map 0:v -map "[a]" -shortest \
    -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT" -y

echo "   -> $OUT  (act one ${ACT1_S}s + turn ${FLIP_S}s + act two ${ACT2_S}s)"
