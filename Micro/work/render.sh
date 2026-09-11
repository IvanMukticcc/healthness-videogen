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
cd "$(dirname "$0")"          # work/, where this variant's own code lives

if [ $# -lt 3 ]; then
    sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
fi

TOPIC="$1"; POSTER="$2"; MICRO="$3"; shift 3
DIR="$(dirname "$POSTER")"
# The base image itself lives in INPUT and only there - it is the file that
# gets attached to the prompt, and INPUT holds nothing else. Its clean copy
# and its layout are working files and stay beside the poster.
BASE="${BASE:-../INPUT/base_${TOPIC}.png}"
# The base WITH the circles is the one the user attaches to the generator, so it
# lives in ../INPUT/ next to the poster they drop back; the clean copy and the
# layout are work's own. Topics rendered before that split kept all three beside
# the poster, and this still finds them there.
ANCHORED="$DIR/base_${TOPIC}.png"
[ -f "$ANCHORED" ] || ANCHORED="../INPUT/base_${TOPIC}.png"
# The bed was flow_soft_8s.m4a until 8 September, when it was rejected for
# sounding like a tap running indoors: 27.2% of its energy sits in 2-8 kHz and
# another 9.1% above that, which is a spout hitting a basin close to the mic.
# flow_soft_warm was the same recording with a -10 dB shelf from 2 kHz; asked to
# damp it once more, flow_soft_warmer takes the shelf to -14 dB. 2-8 kHz goes
# 27.2% -> 8.1% -> 4.8% across the three, above 8 kHz 9.1% -> 1.8% -> 0.9%, and
# the centroid 2838 -> 1404 -> 1157 Hz. Warmer than any of the four field
# recordings on the shelf, which run 15-20% up there. The second shelf needed no
# gain compensation: the first one raised the water 0.95 dB K-weighted because it
# cut the band the meter emphasises, this one only 0.05, because that band was
# already gone. superfoods14 shipped on flow_soft_warm, which is why that file
# stays.
# Four of those are in engine/sfx/ if a different water is ever wanted; flow_shore
# is the one to be careful with, as surf loses 6.8 dB on a phone speaker.
BED="${BED:-../../engine/sfx/flow_soft_warmer_8s.m4a}"
# 0.85, up from Exercise's 0.62, because the badges are the thing the eye is
# following and the hit was sitting under the water. Measured on the part 12 cut:
# the pops come out 1.8 dB louder in RMS and 6.8 dB over the bed instead of 5.4,
# the bed does not move at all in the gaps between them (0.00 dB against the bed
# alone), and the limiter is still not engaged - the mix peaks 0.15 dB UNDER the
# 0.82 ceiling. 1.00 is where it stops being free: the peak goes 0.85 dB over,
# the limiter starts flattening the click, and the hit gets duller as it gets
# louder. Anything above 0.85 wants re-measuring, not guessing.
POP_GAIN="${POP_GAIN:-0.85}"
# 0.8, down from 1.0 on 8 September: the water was asked to sit back a little.
# -1.9 dB on the bed alone, and in the finished mix the badges and the finale do
# not move, so the whole clip comes out about 0.6 LUFS quieter with the same peak.
# 0.40, down from 0.8 on 11 September: the user reported the water drowning the
# badge pops, and the measurement agreed - the bed sat 5.0 dB under them, and at
# 0.40 it sits 10.0. The pops move by 1 dB across that whole range, so this is
# the badges coming forward rather than the clip getting quieter.
BED_GAIN="${BED_GAIN:-0.30}"
WIDTH="${WIDTH:-1080}"          # 540 while tuning: 26s a render against 66s, same timing
DAY="$(date +%d.%m)"
# Overridable so the mix can be re-measured without writing into a day folder:
# what is in ../OUTPUT/<DD.MM>/ has shipped and is never rebuilt (../CLAUDE.md
# rule 5), so a test render points OUT somewhere else and leaves it alone.
OUT="${OUT:-../OUTPUT/$DAY/${TOPIC}_micro.mp4}"
# And the comment above is now a guard, because a comment is not one. A second
# render of a topic on the same day walks straight over the clip already in the
# day folder, which is the one thing rule 5 forbids - and the run that does it
# looks exactly like the run that made it. FORCE=1 is the deliberate way past,
# for the case where the poster was regenerated and the shipped file is known to
# be the wrong one.
if [ -f "$OUT" ] && [ -z "${FORCE:-}" ]; then
    echo "$OUT already exists - that clip has shipped (../CLAUDE.md rule 5)." >&2
    echo "  OUT=somewhere_else.mp4 ./render.sh ...   to render without touching it" >&2
    echo "  FORCE=1 ./render.sh ...                  to overwrite it deliberately" >&2
    exit 1
fi

for f in "$POSTER" "$DIR/base_${TOPIC}_clean.png" "$ANCHORED" \
         "$DIR/base_${TOPIC}_layout.json" "$BED"; do
    [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
done
mkdir -p "$(dirname "$OUT")"

echo "== liquid, badges and finale"
# --micro-times moved in from 1,2,4,5.5,7: at the shipped rhythm the last pop
# settled at 7.60 of an 8s clip, 0.35s from the end, and a finale needs about
# 1.8s after the last row - 0.65 for the row to settle, 0.8 for the finale, 0.4
# of hold, because the last frame is the one a feed freezes on. The room is not
# bought with --seconds: the surface travels a whole number of ribbon lengths, so
# 9s costs 92px/s -> 82 and no flag gives it back.
../.venv/bin/python ../../engine/flowanim.py "$POSTER" \
    --width "$WIDTH" --seconds 8 \
    --overlay micro_overlay \
    --base "$DIR/base_${TOPIC}_clean.png" \
    --anchored "$ANCHORED" \
    --layout "$DIR/base_${TOPIC}_layout.json" \
    --drops 0 --reach 0 \
    --micro "$MICRO" --micro-cues "${TOPIC}_cues.txt" \
    --micro-times 1,2,3.2,4.4,5.6 \
    --finale auto --finale-cue "${TOPIC}_finale.txt" \
    --surge 0.30 --surge-dur 0.34 --surge-stagger 0.05 \
    -o "${TOPIC}_silent.mp4" "$@"

SECONDS_USED=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${TOPIC}_silent.mp4")

echo "== pops and the riser"
# A riser left over from a previous run would be mixed into a clip that has no
# finale, so the presence of the file is only allowed to mean this run wrote it.
rm -f "${TOPIC}_riser.wav"
../.venv/bin/python micro_audio.py --cues-file "${TOPIC}_cues.txt" \
    --finale-file "${TOPIC}_finale.txt" \
    --finale-out "${TOPIC}_riser.wav" \
    --seconds "$SECONDS_USED" -o "${TOPIC}_pops.wav"

# The bed steps back under the finale and comes straight back. Re-measured on the
# energy cut at impact.finale's 0.398 (d1fba5d), riser at unity: the finale's
# half second is -21.4 dB by mean with a -5.8 peak, against badge rows at
# -19.8 to -20.9 - half a decibel under the quietest of them. The
# clip peaks at -2.20 dB, -2.03 before the limiter, 0.3 dB under the 0.82 ceiling
# - it never engages, and the peak is a badge and not the chord.
# The depth stays 0.28, re-checked once more with the riser arriving at unity:
#
#     depth   water steps   chord over the ducked water   finale window
#      0.00        0.0 dB              +2.5 dB               -20.2
#      0.14       -1.3                 +3.8                  -20.7
#      0.21       -2.0                 +4.5                  -21.0
#      0.28       -2.9                 +5.3                  -21.4   <- shipped
#
# It was sized when the chord cleared the water by 1.9 dB and now clears by 5.3,
# so 0.14 would restore that separation with half the dip. Kept at 0.28 anyway,
# and this is the reason rather than taste: the clip the user auditioned the
# finale in had the chord at unity through this duck, so 0.28 is the shape the
# chosen level was chosen through. The mix peak is -2.20 at every depth, so
# nothing is bought or spent by changing it. The numbers below are that duck
# written against the instant flowanim wrote, so the two cannot drift apart.
DUCK="anull"
if [ -s "${TOPIC}_finale.txt" ]; then
    T="$(cat "${TOPIC}_finale.txt")"
    D0="$(awk -v t="$T" 'BEGIN{printf "%.2f", t - 0.28}')"
    D1="$(awk -v t="$T" 'BEGIN{printf "%.2f", t + 1.12}')"
    DUCK="volume='1-0.28*clip(min((t-${D0})/0.20,(${D1}-t)/0.35),0,1)':eval=frame"
    echo "   bed ducked 2.9 dB over ${D0}-${D1}s, around the finale at ${T}s"
fi

echo "== water, pops and picture"
# Fixed gains and a limiter rather than loudnorm: the bed is already normalised
# to -18 LUFS and the pops are transients, and single-pass loudnorm pumps the
# water down under every one of them. These three numbers were measured, not
# guessed: they land the finished clip on -18 LUFS with about -1.4 dBTP, which is
# where the water beds were normalised in the first place.
# level=disabled matters. alimiter auto-levels its output back to 0 dB unless it
# is told not to, so without it the limit is applied and then immediately undone
# - the first cut of this measured -0.1 dBTP with the limiter apparently on.
# The riser is its own input at unity, and POP_GAIN never touches it. It used to
# be summed into the pops wav, which then got volume=${POP_GAIN} over the lot: the
# chord reached the mix at 0.85 of the level impact.finale returns, 1.4 dB under
# what the user picked it at, and Exercise's 0.62 put it 4.2 dB under. One number
# in the engine arriving as three levels is exactly what impact.py exists to stop.
# A badge gain belongs to badges.
FIN_IN=(); FIN_F=""; FIN_MIX=""
if [ -f "${TOPIC}_riser.wav" ]; then
    FIN_IN=(-i "${TOPIC}_riser.wav"); FIN_F="[3:a]volume=1.0[f];"; FIN_MIX="[f]"
fi
ffmpeg -y -loglevel error \
    -i "${TOPIC}_silent.mp4" -i "$BED" -i "${TOPIC}_pops.wav" "${FIN_IN[@]}" \
    -filter_complex "[1:a]volume=${BED_GAIN},${DUCK}[w];[2:a]volume=${POP_GAIN}[p];${FIN_F}\
[w][p]${FIN_MIX}amix=inputs=$(( 2 + ${#FIN_IN[@]} / 2 )):duration=first:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=0.82:level=disabled[a]" \
    -map 0:v -map "[a]" -shortest \
    -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"

echo "wrote $OUT"
