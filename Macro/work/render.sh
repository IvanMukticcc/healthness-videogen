#!/usr/bin/env bash
# render.sh - two acts and the turn between them: the poster, the card, the meal.
#
#   ./render.sh breakfast breakfast_labelled.png \
#       'Greek yogurt,Blueberries,Honey,Oats,Almonds' \
#       '200 Greek yogurt,80 Blueberries,20 Honey,60 Oats,15 Almonds'
#
#   ./render.sh breakfast '' '<foods>' '<meal>'      preview, never into OUTPUT/
#
# The four arguments are the topic, the generated poster, act one's five foods
# and act two's meal. Anything after them goes straight to flowanim.py.
#
# WITHOUT A POSTER this renders a PREVIEW from the base itself, into
# work/<topic>_preview.mp4, and refuses to write to OUTPUT/. A clip in OUTPUT/
# came from a generated poster; that is what the folder means.
#
# THE THREE STEPS AGREE THROUGH FILES, NEVER THROUGH TYPING. flowanim.py writes
# the badge landings and the finale instant; meal.py writes act two's timeline as
# json; macro_audio.py reads all three. The one number typed twice in this
# repository's history put a pop half a frame off the badge it belonged to, and
# nobody could say why it felt wrong.
set -euo pipefail
cd "$(dirname "$0")"

if [ $# -lt 4 ]; then
    sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
fi

TOPIC="$1"; POSTER="$2"; FOODS="$3"; MEAL="$4"; shift 4

BASE="../INPUT/base_${TOPIC}.png"
CLEAN="base_${TOPIC}_clean.png"
LAYOUT="base_${TOPIC}_layout.json"
BED="${BED:-../../engine/sfx/flow_soft_warmer_8s.m4a}"
BED_GAIN="${BED_GAIN:-0.8}"
POP_GAIN="${POP_GAIN:-0.85}"
WIDTH="${WIDTH:-1080}"
DEFAULT_TITLE="TODAY'S BOWL"   # its own variable: an apostrophe inside a
TITLE="${TITLE:-$DEFAULT_TITLE}"  # ${x:-...} default is not worth the quoting
ACT1_S="${ACT1_S:-8}"
ACT2_S="${ACT2_S:-7.5}"
FLIP_N="${FLIP_N:-14}"           # frames of turn; 14 at 24fps is 0.583s
FPS=24
DAY="$(date +%d.%m)"

if [ -n "$POSTER" ] && [ -f "$POSTER" ]; then
    OUT="${OUT:-../OUTPUT/$DAY/${TOPIC}_macro.mp4}"
    mkdir -p "$(dirname "$OUT")"
    echo "== clip: $POSTER"
else
    POSTER="$CLEAN"
    OUT="${TOPIC}_preview.mp4"
    echo "== PREVIEW - no poster, so this does not go to OUTPUT/"
fi

for f in "$POSTER" "$CLEAN" "$BASE" "$LAYOUT" "$BED"; do
    [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
done

W="$WIDTH"; H=$(( WIDTH * 2752 / 1536 ))
H=$(( H - H % 2 ))
TMP="${TMPDIR:-/tmp}/macro_${TOPIC}_$$"
mkdir -p "$TMP"
trap 'rm -rf "$TMP"' EXIT

echo "== act one: liquid, macros, calories"
../.venv/bin/python ../../engine/flowanim.py "$POSTER" \
    --width "$W" --seconds "$ACT1_S" \
    --overlay macro_overlay \
    --base "$CLEAN" --anchored "$BASE" --layout "$LAYOUT" \
    --drops 0 --reach 0 \
    --macro "$FOODS" --macro-cues "${TOPIC}_cues.txt" \
    --finale auto --finale-cue "${TOPIC}_finale.txt" \
    --surge 0.30 --surge-dur 0.34 --surge-stagger 0.05 \
    -o "$TMP/act1.mp4" "$@"

ACT1_USED=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/act1.mp4")

# Act one is a SEAMLESS LOOP, which is what makes the glass affordable: the
# frames behind act two are act one's own, continuing from where the turn left
# it, so nothing has to be rendered twice. ACT1_N frames of act one, FLIP_N of
# turn, so act two's first frame sits over act one's frame (ACT1_N + FLIP_N) mod
# ACT1_N - and the liquid carries on as though it had never stopped.
ACT1_N=$(ffprobe -v error -select_streams v:0 -count_frames \
    -show_entries stream=nb_read_frames -of csv=p=0 "$TMP/act1.mp4")
OFFSET=$(( (ACT1_N + FLIP_N) % ACT1_N ))

echo "== act two: the meal, on glass"
../.venv/bin/python meal.py --meal "$MEAL" --title "$TITLE" \
    --seconds "$ACT2_S" --fps "$FPS" --width "$W" --height "$H" \
    --behind "$TMP/act1.mp4" --behind-offset "$OFFSET" \
    --cues "${TOPIC}_act2.json" --first-frame "$TMP/b.png" -o "$TMP/act2.mp4"

echo "== the turn"
# The two faces are the frames either side of the cut: act one's last and act
# two's first. Taking act one's last frame from the ENCODED clip rather than
# re-rendering it means the card that starts turning is the card that was on
# screen a frame earlier, x264 artefacts and all.
ffmpeg -v error -sseof -0.05 -i "$TMP/act1.mp4" -frames:v 1 -update 1 "$TMP/a.png" -y
# and the frames the card turns IN FRONT of - act one continuing past its last,
# which for a seamless loop is its own beginning.
mkdir -p "$TMP/bd"
ffmpeg -v error -i "$TMP/act1.mp4" -vf "select=lt(n\,${FLIP_N})" -vsync 0 "$TMP/bd/f%03d.png" -y
../.venv/bin/python flip.py "$TMP/a.png" "$TMP/b.png" \
    --out-dir "$TMP/turn" --frames "$FLIP_N" --backdrop-dir "$TMP/bd"
ffmpeg -v error -framerate "$FPS" -i "$TMP/turn/f%05d.png" \
    -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p "$TMP/turn.mp4" -y
FLIP_S=$(awk -v n="$FLIP_N" -v f="$FPS" 'BEGIN{printf "%.4f", n/f}')

echo "== joining"
printf "file '%s'\nfile '%s'\nfile '%s'\n" "$TMP/act1.mp4" "$TMP/turn.mp4" "$TMP/act2.mp4" > "$TMP/list"
ffmpeg -v error -f concat -safe 0 -i "$TMP/list" -c:v copy "$TMP/silent.mp4" -y

echo "== sound"
rm -f "${TOPIC}_riser.wav"
../.venv/bin/python macro_audio.py \
    --cues-file "${TOPIC}_cues.txt" --finale-file "${TOPIC}_finale.txt" \
    --act2-cues "${TOPIC}_act2.json" \
    --act1-seconds "$ACT1_USED" --flip-seconds "$FLIP_S" --act2-seconds "$ACT2_S" \
    -o "${TOPIC}_pops.wav" --finale-out "${TOPIC}_riser.wav" \
    --act2-out "${TOPIC}_act2.wav"

# duration=longest and apad, NOT duration=first. The bed is an 8 second file
# and act one is an 8 second act, so `first` measures the bed, `-shortest` then
# trims the VIDEO to it, and a sixteen second clip is written eight seconds long
# with no error anywhere. It reads as the concat having failed. It had not.
#
# The water belongs to act one. It fades through the turn rather than stopping
# at it, because a bed that cuts on the frame the card starts moving tells the
# ear the file changed; one that fades tells it the room did.
FADE0=$(awk -v a="$ACT1_USED" 'BEGIN{printf "%.3f", a - 0.15}')
DUCK="anull"
if [ -s "${TOPIC}_finale.txt" ]; then
    T="$(cat "${TOPIC}_finale.txt")"
    D0="$(awk -v t="$T" 'BEGIN{printf "%.2f", t - 0.28}')"
    D1="$(awk -v t="$T" 'BEGIN{printf "%.2f", t + 1.12}')"
    DUCK="volume='1-0.28*clip(min((t-${D0})/0.20,(${D1}-t)/0.35),0,1)':eval=frame,"
fi
A2_AT=$(awk -v a="$ACT1_USED" -v f="$FLIP_S" 'BEGIN{printf "%.3f", a}')

FIN_IN=(); FIN_F=""; FIN_MIX=""
if [ -f "${TOPIC}_riser.wav" ]; then
    FIN_IN=(-i "${TOPIC}_riser.wav"); FIN_F="[4:a]volume=1.0[f];"; FIN_MIX="[f]"
fi
ffmpeg -y -loglevel error \
    -i "$TMP/silent.mp4" -i "$BED" -i "${TOPIC}_pops.wav" -i "${TOPIC}_act2.wav" "${FIN_IN[@]}" \
    -filter_complex "\
[1:a]volume=${BED_GAIN},${DUCK}afade=t=out:st=${FADE0}:d=${FLIP_S}[w];\
[2:a]volume=${POP_GAIN}[p];\
[3:a]adelay=$(awk -v t="$A2_AT" 'BEGIN{printf "%d", t*1000}')|$(awk -v t="$A2_AT" 'BEGIN{printf "%d", t*1000}'),volume=1.0[q];\
${FIN_F}[w][p][q]${FIN_MIX}amix=inputs=$(( 3 + ${#FIN_IN[@]} / 2 )):duration=longest:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled,apad[a]" \
    -map 0:v -map "[a]" -shortest \
    -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"

echo "wrote $OUT  ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s)"
