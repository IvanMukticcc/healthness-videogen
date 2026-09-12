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
# 0.40, not 0.80. The water is a bed and the badge pops were not getting in
# front of it: measured on a shipped clip, badge windows against the gaps
# between them, the pop sat only 5.0 dB above the water. Five decibels is
# "slightly louder", not "something landed", which is why a pop that is doing
# its job still read as part of the room.
#
#   BED_GAIN 0.80   water -20.9   pop -15.9    5.0 dB
#   BED_GAIN 0.55   water -24.1   pop -16.6    7.6 dB
#   BED_GAIN 0.40   water -26.9   pop -16.9   10.0 dB
#   BED_GAIN 0.30   water -29.4   pop -17.1   12.3 dB
#
# THE POP BARELY MOVES ACROSS THAT RANGE - -15.9 to -17.1 - so this foregrounds
# the badges rather than quietening the clip. The bed was eating the headroom
# the pops needed and the limiter was holding the mix on top of it.
#
# 0.30 IS THE FLOOR AND THIS IS IT. The user asked for one more step after
# hearing 0.40 and this is the last one on the table above. The bed is normalised
# to -18 LUFS, so at 0.30 it is more than 11 dB under its own reference: below
# this it stops reading as a room and starts sounding like an effect somebody
# left on, which is a different fault from the one being fixed. If the water
# should be further away again, the answer is a different bed rather than a
# smaller number - `engine/sfx/` has four that have never been tried this low.
BED_GAIN="${BED_GAIN:-0.30}"
POP_GAIN="${POP_GAIN:-0.85}"
# 0.82, the same ceiling as every other variant. It was briefly 0.74 here, to
# buy headroom against an AAC overshoot that does not exist - I had measured the
# decoded clip with `-ac 1`, and downmixing a stereo file whose two channels are
# identical (this mix is mono sources fanned out) rematrixes them UP by 2.0 dB.
# Native-layout decode: peak 0.7323, RMS -23.6. With `-ac 1`: 0.9212 and -20.8,
# on the same bytes. macro-c1 could not reproduce my figures, which is what
# found it.
#
# What survives is the finding underneath. This rhythm is the first thing in the
# repository to ENGAGE the limiter - 36 samples over 0.82 before limiting, where
# Micro's render.sh still says "the limiter is still not engaged" - and the
# limiter holds it exactly, verified by writing the same graph to pcm_f32le with
# and without it: 1.0787 against 0.8200. So the ceiling works and has now been
# tested, which it never had been.
CEIL="${CEIL:-0.82}"
WIDTH="${WIDTH:-1080}"
# Whose day the meal is measured against. dailygoal.py computes it the way the app
# does; these are its inputs and they are printed on screen, which is what keeps
# a personal goal from reading as advice to whoever is watching.
SEX="${SEX:-male}"; AGE="${AGE:-30}"; HEIGHT="${HEIGHT:-172}"; WEIGHT="${WEIGHT:-66}"
ACTIVITY="${ACTIVITY:-light}"; FITGOAL="${FITGOAL:-mild_gain}"
DEFAULT_TITLE="TODAY'S BOWL"   # its own variable: an apostrophe inside a
TITLE="${TITLE:-$DEFAULT_TITLE}"  # ${x:-...} default is not worth the quoting
ACT1_S="${ACT1_S:-8}"
# 6.2, not 7.5. The user asked for one second after everything has appeared.
#
# MEASURED ON THE RENDER, not assumed, and measured TWICE because the first
# answer was the wrong kind of number. Act two's last big change is the third
# chip landing at 4.33s; the verdict text then fades in from its cue at 4.78.
# That fade is nominally 0.4s, so 5.18 looks like the moment everything has
# appeared - and sizing from it left a 1.42s hold, because the last four-fifths
# of an ease-out is below anything an eye can see. The last whole-frame step
# above four times the drift floor is at 4.80. That is when everything HAS
# appeared, as opposed to when the animation stops computing. 4.80 + 1.0 = 5.8.
#
# The hold was 2.62 seconds. Not three, but it reads as longer than it is,
# because the chord lands at 10.86 and the picture is not finished until 10.96 -
# the ear is told the clip is over while the eye is still being given something.
#
# This is a FIVE-FOOD number. `verdict` is ring0 + ring_dur + 0.25 and ring0
# comes off the last food row, so a meal of a different length moves it and this
# has to move with it. `meal.py` prints the cues it used.
ACT2_S="${ACT2_S:-6.15}"          # land (4.78 + 0.35) + 1.0, see meal.py Plan.land
FLIP_N="${FLIP_N:-14}"           # frames of turn; 14 at 24fps is 0.583s
# 0.5, not 0.12. The measurement said the dead hold was 1.08s and I removed 1.00
# of it, which left two frames - and two frames is not a pause, it is a cut. A
# user looking at a held poster asking for "much faster" means the hold should
# stop being the point, not that the transition should stop existing.
# 0.25, and the reason it changed is worth more than the number. At 0.5 it was
# measured from the SURGE's end, so the eye had just watched something large
# finish and half a second read as a breath. With the finale gone it is measured
# from one small badge settling, and half a second of nothing after a small
# event is a different half second entirely. Same number, different content.
#
# 0.12 IS THE FLOOR AND IT IS ALREADY KNOWN. That was the value this morning
# before the finale went, and the user's words for it were that the turn arrived
# as if there were no pause at all. Two frames is a cut, not a beat.
BEAT="${BEAT:-0.25}"             # the beat after the last badge has settled
# The rhythm. The overlay still defaults to 1,2,3.2,4.4,5.6 for anyone calling it
# directly; this is the shipped one and it starts at half a second. A viewer
# gives a vertical clip about that long before deciding, and the first second
# used to be five bare rings and a poster - nothing had happened yet at the only
# moment it mattered. 1.1 apart is Micro's spacing, which is the one this
# repository has the most clips behind.
# 0.25, not 0.5. The user asked for the first pop no later than 0.3s in. Same
# 1.1 spacing, shifted a quarter second earlier.
#
# WORTH KNOWING IF THEY ASK AGAIN: the cue is when the pop STARTS, not when the
# badge is on screen. At 0.25 it finishes arriving around 0.72, and no cue can
# put a badge fully on screen by 0.3 - that would be a faster `POP` in
# macro_overlay.py, which is this folder's own file and not shared with Micro.
MACRO_TIMES="${MACRO_TIMES:-0.25,1.35,2.45,3.55,4.65}"
FPS=24
# No DAY. Clips go to one flat folder per category - `../CLAUDE.md` rule 12 -
# because the day folder came off the clock, so a session that spanned midnight
# wrote into a new one and the previous day looked abandoned. That is exactly
# what happened here on 11 September and nothing had been misfiled. What a clip
# is called says which topic it is; the day it was cut said nothing anyone
# needed.

if [ -n "$POSTER" ] && [ -f "$POSTER" ]; then
    OUT="${OUT:-../../OUTPUT/MACRO/${TOPIC}_macro.mp4}"
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

# NOTHING WRITES THE FINALE CUE ANY MORE, SO NOTHING MAY READ AN OLD ONE.
# `--finale off` stops flowanim writing `<topic>_finale.txt`; it does not remove
# the one a previous render left, and `macro_audio` reads that file to place act
# one's chord. The first render after the finale was dropped still had the chord
# in it, at 5.67s - 0.16s before the turn - because a six-byte file from an hour
# earlier was still on disk. Deleting it here makes the absence structural rather
# than a thing housekeeping has to remember.
# A finale cue on disk means act one carries the glow in its PICTURE, so cutting
# after it would show the glow and then cut away from it. Loud failure beats a
# clip that announces an ending it does not have.
if [ -s "${TOPIC}_finale.txt" ] && [ -z "${ALLOW_FINALE:-}" ]; then
    echo "refusing: ${TOPIC}_finale.txt exists, so act one was rendered with a" >&2
    echo "  finale in its picture. This variant ships without one - delete it," >&2
    echo "  or set ALLOW_FINALE=1 if you really mean to keep the glow." >&2
    exit 1
fi
rm -f "${TOPIC}_finale.txt"
echo "== act one: liquid, macros, calories"
../.venv/bin/python ../../engine/flowanim.py "$POSTER" \
    --width "$W" --seconds "$ACT1_S" \
    --overlay macro_overlay \
    --base "$CLEAN" --anchored "$BASE" --layout "$LAYOUT" \
    --drops 0 --reach 0 \
    --macro "$FOODS" --macro-cues "${TOPIC}_cues.txt" \
    --macro-times "$MACRO_TIMES" \
    --finale off \
    -o "$TMP/act1.mp4" "$@" | tee "$TMP/act1.log"

ACT1_FULL=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/act1.mp4")
ACT1_N=$(ffprobe -v error -select_streams v:0 -count_frames \
    -show_entries stream=nb_read_frames -of csv=p=0 "$TMP/act1.mp4")

# THE TURN COMES BEAT AFTER THE LAST BADGE IS ON SCREEN.
#
# It used to come BEAT after the surge settled, because act one ended on a
# finale - a glow and a chord - and that was the last thing moving. The finale
# is gone: it read as the end of the whole video, which it is not, and the clip
# now has exactly one chord in it, act two's landing, which is the only place
# anything actually ends.
#
# THE CUE IS NOT THE ARRIVAL. A badge is cued at `t` and takes `POP` seconds to
# scale in, so it is ON SCREEN at t+POP - the distinction found this morning
# when the user asked for the first badge at 0.5s and it appeared at 0.7. The
# user asked for half a second after the last badge pops onto the screen, so the
# count starts at the arrival and not at the cue.
#
# TWO NUMBERS, NOT ONE. SETTLE is a measured property of the animation; GAP is
# the beat the user asked for. Adding them gives the cut, but they are not the
# same kind of thing and folding them together loses which one to change.
#
# SETTLE IS MEASURED, NOT `POP`. Reading POP=0.42 out of macro_overlay.py looked
# principled - one number, one file - and it was the wrong number: POP is the
# disc's scale-in, and the badge is not finished arriving until its figure and
# its ring have settled too. Watched on row 5's own band, the last badge to
# land: it leaves the ribbon baseline of 0.738 at its cue and is back to it
# 0.60s later, peaking at 5.5 around 0.31s in. At POP the turn began 0.33s after
# the badge stopped moving, not the half second that was asked for.
#
# Re-measure this if the badge animation changes. It is not derivable from any
# constant in the overlay - three things move and the last of them decides it.
SETTLE="${SETTLE:-0.60}"
GAP="${GAP:-$BEAT}"
LAST_CUE=$(printf '%s' "$MACRO_TIMES" | tr ',' '\n' | tail -1)
ARRIVED=$(awk -v c="$LAST_CUE" -v p="$SETTLE" 'BEGIN{printf "%.3f", c+p}')
CUT="${CUT:-$(awk -v e="$ARRIVED" -v b="$GAP" -v f="$ACT1_FULL" \
    'BEGIN{c=e+b; print (c<f? c : f)}')}"
CUT_N=$(awk -v c="$CUT" -v fps="$FPS" 'BEGIN{printf "%d", int(c*fps+0.5)}')
ACT1_USED=$(awk -v n="$CUT_N" -v fps="$FPS" 'BEGIN{printf "%.4f", n/fps}')
echo "   last badge cued ${LAST_CUE}s, settled ${ARRIVED}s (SETTLE ${SETTLE}); turn ${GAP}s later at ${ACT1_USED}s of ${ACT1_FULL} (${CUT_N} of ${ACT1_N} frames)"
ffmpeg -v error -i "$TMP/act1.mp4" -frames:v "$CUT_N" -c:v copy "$TMP/act1cut.mp4" -y
mv "$TMP/act1cut.mp4" "$TMP/act1shown.mp4"

# Act one is a SEAMLESS LOOP, which is what makes the glass affordable: the
# frames behind act two are act one's own, continuing from where the turn left
# it, so nothing has to be rendered twice. ACT1_N frames of act one, FLIP_N of
# turn, so act two's first frame sits over act one's frame (ACT1_N + FLIP_N) mod
# ACT1_N - and the liquid carries on as though it had never stopped.
# The backdrop continues from where the SHOWN part stopped, and the frames past
# the trim are still there to use. FINALE_N is the earliest frame the walk may
# reach: every frame from the finale on carries all fifteen badges, so bouncing
# inside that window cannot step in content the way a wrap to frame 0 did.
OFFSET=$(( CUT_N + FLIP_N ))
# The floor of the bounce window was the finale frame, because every frame from
# there carried all fifteen badges. With no finale that is the last badge's
# arrival, which is the same guarantee one event earlier.
FINALE_N=$(awk -v t="$ARRIVED" -v fps="$FPS" 'BEGIN{printf "%d", int(t*fps)}')

echo "== act two: the meal, on glass"
../.venv/bin/python meal.py --meal "$MEAL" --title "$TITLE" \
    --seconds "$ACT2_S" --fps "$FPS" --width "$W" --height "$H" \
    --sex "$SEX" --age "$AGE" --body-height "$HEIGHT" --body-weight "$WEIGHT" \
    --activity "$ACTIVITY" --goal "$FITGOAL" \
    --behind "$TMP/act1.mp4" --behind-offset "$OFFSET" --behind-lo "$FINALE_N" \
    --cues "${TOPIC}_act2.json" --first-frame "$TMP/b.png" -o "$TMP/act2.mp4"

echo "== the turn"
# The two faces are the frames either side of the cut: act one's last and act
# two's first. Taking act one's last frame from the ENCODED clip rather than
# re-rendering it means the card that starts turning is the card that was on
# screen a frame earlier, x264 artefacts and all.
ffmpeg -v error -sseof -0.05 -i "$TMP/act1shown.mp4" -frames:v 1 -update 1 "$TMP/a.png" -y
# and the frames the card turns IN FRONT of - act one continuing past its last,
# which for a seamless loop is its own beginning.
mkdir -p "$TMP/bd"
ffmpeg -v error -i "$TMP/act1.mp4" \
    -vf "select='gte(n\,${CUT_N})*lt(n\,${CUT_N}+${FLIP_N})'" -vsync 0 "$TMP/bd/f%03d.png" -y
../.venv/bin/python ../../engine/flip.py "$TMP/a.png" "$TMP/b.png" \
    --out-dir "$TMP/turn" --frames "$FLIP_N" --backdrop-dir "$TMP/bd"
ffmpeg -v error -framerate "$FPS" -i "$TMP/turn/f%05d.png" \
    -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p "$TMP/turn.mp4" -y
FLIP_S=$(awk -v n="$FLIP_N" -v f="$FPS" 'BEGIN{printf "%.4f", n/f}')

echo "== joining"
printf "file '%s'\nfile '%s'\nfile '%s'\n" "$TMP/act1shown.mp4" "$TMP/turn.mp4" "$TMP/act2.mp4" > "$TMP/list"
ffmpeg -v error -f concat -safe 0 -i "$TMP/list" -c:v copy "$TMP/silent.mp4" -y

echo "== sound"
rm -f "${TOPIC}_riser.wav"
../.venv/bin/python macro_audio.py \
    --cues-file "${TOPIC}_cues.txt" --finale-file "${TOPIC}_finale.txt" \
    --act2-cues "${TOPIC}_act2.json" \
    --act1-seconds "$ACT1_FULL" --flip-seconds "$FLIP_S" --act2-seconds "$ACT2_S" \
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
# EMPTY, not "anull". This is spliced straight into the filter chain as
# `volume=${BED_GAIN},${DUCK}afade=...`, so the string has to end with its own
# comma or be nothing at all. The finale branch below builds one that does;
# "anull" did not, and produced `anullafade` - No such filter. It never fired
# while act one had a finale, because the branch always won. Every one of the
# three faults this change uncovered is the same shape: a fallback that had
# never been taken.
DUCK=""
if [ -s "${TOPIC}_finale.txt" ]; then
    T="$(cat "${TOPIC}_finale.txt")"
    D0="$(awk -v t="$T" 'BEGIN{printf "%.2f", t - 0.28}')"
    D1="$(awk -v t="$T" 'BEGIN{printf "%.2f", t + 1.12}')"
    DUCK="volume='1-0.28*clip(min((t-${D0})/0.20,(${D1}-t)/0.35),0,1)':eval=frame,"
fi
A2_AT=$(awk -v a="$ACT1_USED" -v f="$FLIP_S" 'BEGIN{printf "%.3f", a}')
# THE TAIL FADES INTO THE CUT RATHER THAN BEING CHOPPED. Shortening the hold
# lands the end of the clip while act two's chord is still ringing, and a chord
# cut mid-ring is plainly audible. 0.15s takes what is left of it.
TAIL0=$(awk -v a="$ACT1_USED" -v f="$FLIP_S" -v t="$ACT2_S" \
    'BEGIN{printf "%.3f", a + f + t - 0.15}')

# `${FIN_IN[@]+"${FIN_IN[@]}"}` BELOW, NOT `"${FIN_IN[@]}"`. On an empty array
# the plain form is an unbound-variable error under `set -u` in bash 3.2, which
# is what macOS ships and what this runs under. It never fired while act one had
# a finale, because the riser always existed; `--finale off` is the first run
# that produces no riser, and the script died at the mux with the clip already
# rendered - the most expensive place to fail. The `+` form is safe on old and
# new bash alike. `${#FIN_IN[@]}` further down is fine as it is.
FIN_IN=(); FIN_F=""; FIN_MIX=""
if [ -f "${TOPIC}_riser.wav" ]; then
    FIN_IN=(-i "${TOPIC}_riser.wav"); FIN_F="[4:a]volume=1.0[f];"; FIN_MIX="[f]"
fi
ffmpeg -y -loglevel error \
    -i "$TMP/silent.mp4" -i "$BED" -i "${TOPIC}_pops.wav" -i "${TOPIC}_act2.wav" \
    ${FIN_IN[@]+"${FIN_IN[@]}"} \
    -filter_complex "\
[1:a]volume=${BED_GAIN},${DUCK}afade=t=out:st=${FADE0}:d=${FLIP_S}[w];\
[2:a]volume=${POP_GAIN}[p];\
[3:a]adelay=$(awk -v t="$A2_AT" 'BEGIN{printf "%d", t*1000}')|$(awk -v t="$A2_AT" 'BEGIN{printf "%d", t*1000}'),volume=1.0[q];\
${FIN_F}[w][p][q]${FIN_MIX}amix=inputs=$(( 3 + ${#FIN_IN[@]} / 2 )):duration=longest:normalize=0[m];\
[m]alimiter=level_in=1:level_out=1:limit=${CEIL}:level=disabled,afade=t=out:st=${TAIL0}:d=0.15,apad[a]" \
    -map 0:v -map "[a]" -shortest \
    -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"

echo "wrote $OUT  ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s)"
