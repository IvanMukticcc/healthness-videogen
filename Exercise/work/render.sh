#!/usr/bin/env bash
# render.sh - poster in, finished clip out: liquid, badges, bodies, bed and hits.
#
# The three steps have to agree on when a badge lands, because that instant is
# also when the muscle lights on the body and when the hit sounds. They agree
# through one file: flowanim.py writes the landing times it actually used,
# muscle_audio.py reads them. Typing the times twice is how a hit ends up half a
# frame off the badge it belongs to, which reads as a sync fault even when nobody
# can say why.
#
#   ./render.sh push work/push_labelled.png 'auto:BENCH PRESS,PULL-UP,BACK SQUAT,LATERAL RAISE,DEADLIFT'
#
# Anything after the third argument goes straight to flowanim.py, so
# --muscle-d, --muscle-times, --body-scale, --seconds and the rest are available
# untouched.
set -euo pipefail
cd "$(dirname "$0")"          # work/, where this variant's own code lives

if [ $# -lt 3 ]; then
    sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
fi

TOPIC="$1"; POSTER="$2"; MUSCLES="$3"; shift 3
DIR="$(dirname "$POSTER")"
# The base image itself lives in INPUT and only there - it is the file that
# gets attached to the prompt, and INPUT holds nothing else. Its clean copy
# and its layout are working files and stay beside the poster.
BASE="${BASE:-../INPUT/base_${TOPIC}.png}"
# Tighter than the animator's own default, and it is this variant that makes it
# safe. The wipe puts the clean base back wherever the poster still looks like
# the guide mark - and inside the left circle the clean base is the wave, so
# every pixel it takes by mistake is a cyan patch on the lifter. At 20 it took
# 18889 of them, and on the dark rows a black singlet is well within 20 levels of
# the row behind it: the first PULL DAY cut had liquid across his chest. Nothing
# is lost by tightening, because both circles are covered here by construction -
# the athlete's disc is drawn over the left one and clean_poster.py restores the
# right one to the base exactly, so the pixels that should be wiped differ by
# almost nothing anyway. 256454 px still get wiped at 6, against 269416 at 20.
ANCHOR_TOL="${ANCHOR_TOL:-6}"
# The rows move earlier than they used to, and they move to make room. The
# shipped rhythm 1,2,4,5.5,7 puts the last badge at 7.18 of an 8s clip, which
# leaves 0.35s - not enough for anything to arrive in. The finale needs about
# 1.8: 0.65 for the last row to settle, 0.8 for the finale itself and 0.4 of
# hold, because the last frame is the one a feed freezes on. At 1,2,3.2,4.4,5.6
# the last badge lands at 5.78, the finale at 6.38, and 0.8s of settled clip is
# left after it.
#
# It cannot be bought with a longer clip instead. The surface travels a whole
# number of ribbon lengths - that is what makes the loop seamless - so the speed
# is ribbon/seconds and nothing else: 8s is 92px/s, 9s is 82, and there is no
# value between them. The user settled on 92, so the clip is 8 seconds.
MUSCLE_TIMES="${MUSCLE_TIMES:-1,2,3.2,4.4,5.6}"
SURGE="${SURGE:-0.30}"
BED="${BED:-../../engine/sfx/lift_bed_8s.m4a}"
HIT_GAIN="${HIT_GAIN:-0.62}"
# Unity, and it is not a free parameter: impact.finale already returns the chord
# at the level the user picked it at, shared with the other variants. Anything
# but 1.0 here is this folder quietly setting its own. If it is ever wrong, the
# number to change is in engine/impact.py, once, for all of them.
FINALE_GAIN="${FINALE_GAIN:-1.0}"
BED_GAIN="${BED_GAIN:-1.0}"
DAY="$(date +%d.%m)"
OUT="../OUTPUT/$DAY/${TOPIC}_muscles.mp4"

for f in "$POSTER" "$DIR/base_${TOPIC}_clean.png" "$BASE" \
         "$DIR/base_${TOPIC}_layout.json" "$BED"; do
    [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
done
# Is this a generated poster at all? render.sh writes straight into a day folder,
# and a labelled BASE is a file that plausibly exists in here - the six recipes in
# Prompts.txt were captioning the base until 8 September 2026. Handed one, every
# other check passes: the waves are exactly where the mask expects them, because
# they are the base's own waves. What is missing is the only thing a generation
# adds, which is an athlete in each left circle. Measured over the four posters of
# 8 September the left circles differ from the base by 29 to 74; a labelled base
# differs by 0.0 on all five rows. Nothing lives in between, so nothing is tuned.
../.venv/bin/python - "$POSTER" "$BASE" "$DIR/base_${TOPIC}_layout.json" <<'PYCHK' || exit 1
import sys, json, numpy as np
from PIL import Image
poster, base, layout = sys.argv[1:4]
p = np.asarray(Image.open(poster).convert("RGB")).astype(float)
b = np.asarray(Image.open(base).convert("RGB")).astype(float)
L = json.load(open(layout))
H, W = p.shape[:2]
yy, xx = np.mgrid[0:H, 0:W]
d = np.abs(p - b).max(2)
rows = [float(d[np.hypot(xx - L["anchor_l"], yy - r["cy"]) < r["r"]].mean()) for r in L["rows"]]
med = float(np.median(rows))
if med < 10:
    sys.exit("  left circles differ from the base by "
             + ", ".join(f"{v:.1f}" for v in rows)
             + f"\n  There is no athlete in them, so {poster} is not a generated"
               "\n  poster - a labelled base reads 0.0 and a real one 29 to 74."
               "\n  A clip in OUTPUT/ came from a generated poster. Always.")
print(f"  poster carries artwork in all five left circles (median {med:.0f} off the base)")
PYCHK

mkdir -p "../OUTPUT/$DAY"

echo "== liquid, badges and bodies"
../.venv/bin/python ../../engine/flowanim.py "$POSTER" \
    --width 1080 --seconds 8 \
    --overlay body_overlay,muscle_overlay \
    --base "$DIR/base_${TOPIC}_clean.png" \
    --anchored "$BASE" \
    --layout "$DIR/base_${TOPIC}_layout.json" \
    --drops 0 --reach 0 --anchor-tol "$ANCHOR_TOL" \
    --muscles "$MUSCLES" --muscle-times "$MUSCLE_TIMES" \
    --muscle-cues "${TOPIC}_cues.txt" \
    --finale auto --surge "$SURGE" --finale-cue "${TOPIC}_finale.txt" \
    -o "${TOPIC}_silent.mp4" "$@"

SECONDS_USED=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${TOPIC}_silent.mp4")

echo "== hits"
# The finale goes in through its own file, never into ${TOPIC}_cues.txt: the
# cue file is a list of badge landings and muscle_audio.py would sound the
# finale as a sixth badge, on a frame where nothing lands.
# The finale comes out in its own file rather than summed into the hits, and the
# mix takes it at unity. One track gets one gain: summed into ${TOPIC}_hits.wav
# it was multiplied by HIT_GAIN below - 0.62, a number measured for badge hits -
# and the chord arrived 4.15 dB under the level impact.finale returns it at. The
# level the engine returns is the level it has to arrive at.
../.venv/bin/python muscle_audio.py --cues-file "${TOPIC}_cues.txt" \
    --finale-cue "${TOPIC}_finale.txt" --finale-out "${TOPIC}_chord.wav" \
    --seconds "$SECONDS_USED" -o "${TOPIC}_hits.wav"

# The bed steps back 2.9 dB under the finale and comes back up after it. Ducked
# rather than mixed quieter throughout: the riser is the only sound in the clip
# that says something is about to happen, and it needs the floor to itself for
# half a second. The window is read from the finale's own instant, so it follows
# the rhythm instead of being typed a second time.
FIN=$(cat "${TOPIC}_finale.txt")
DUCK_IN=$(awk -v t="$FIN" 'BEGIN{printf "%.2f", t-0.28}')
DUCK_OUT=$(awk -v t="$FIN" 'BEGIN{printf "%.2f", t+1.12}')
DUCK="volume='1-0.28*clip(min((t-${DUCK_IN})/0.20,(${DUCK_OUT}-t)/0.35),0,1)':eval=frame"

echo "== bed, hits and picture"
# Fixed gains and a limiter rather than loudnorm: the bed is already normalised
# to -18.4 LUFS and the hits are transients, and single-pass loudnorm pumps the
# bed down under every one of them. These three numbers were measured, not
# guessed: they land the finished clip where the bed was normalised in the first
# place.
# level=disabled matters. alimiter auto-levels its output back to 0 dB unless it
# is told not to, so without it the limit is applied and then immediately undone
# - the first cut of the food version measured -0.1 dBTP with the limiter
# apparently on.
ffmpeg -y -loglevel error \
    -i "${TOPIC}_silent.mp4" -i "$BED" -i "${TOPIC}_hits.wav" -i "${TOPIC}_chord.wav" \
    -filter_complex "[1:a]volume=${BED_GAIN},${DUCK}[w];[2:a]volume=${HIT_GAIN}[p];\
[3:a]volume=${FINALE_GAIN}[f];\
[w][p][f]amix=inputs=3:duration=first:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[a]" \
    -map 0:v -map "[a]" -shortest \
    -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"

echo "wrote $OUT"
