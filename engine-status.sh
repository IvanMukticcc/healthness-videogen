#!/usr/bin/env bash
# engine-status.sh - which engine is each variant actually running?
#
# Reads only. It never writes into a variant folder: those are worked on in
# parallel, by other people and other agents, and a sync that overwrites is how
# an afternoon of someone else's work disappears.
#
# For every file that belongs to the engine it reports one of:
#   calls the engine  the variant has no copy - the good case
#   same              a copy, byte for byte identical to the engine
#   stale             a copy of an older engine, and which commit it came from
#   diverged          a copy that has been changed, and by how much
#
# Both the variant folder and its work/ are looked in. The tools are called from
# work/, so that is where a copy lands; until the folders were split on the 7th
# they sat one level up, and old checkouts still have them there.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
ENGINE="$ROOT/engine"
VARIANTS=(${1:-Foods Micro Exercise Biohacks})
FILES=(make_base.py recolor_base.py grab.py add_labels.py check_base.py flowanim.py
       impact.py
       base_layer.png ribbon_mask.png ribbon_rgba.png source_wave_poster.jpeg)

# every past version of engine/<file>, so a stale copy can be dated
past_commit() {                       # $1 file, $2 sha of the variant's copy
    [ -d "$ROOT/.git" ] || return 1
    git -C "$ROOT" rev-list HEAD -- "engine/$1" 2>/dev/null | while read -r c; do
        b=$(git -C "$ROOT" rev-parse "$c:engine/$1" 2>/dev/null) || continue
        if [ "$(git -C "$ROOT" cat-file blob "$b" | shasum -a 256 | cut -c1-64)" = "$2" ]; then
            echo "$(git -C "$ROOT" log -1 --format='%h %ad' --date=short "$c")"
            return 0
        fi
    done
    return 1
}

status=0
for v in "${VARIANTS[@]}"; do
    [ -d "$ROOT/$v" ] || continue
    copies=0; same=0; stale=0; diverged=0; lines=""
    for f in "${FILES[@]}"; do
      for p in "$v/$f" "$v/work/$f"; do
        [ -f "$ROOT/$p" ] || continue
        copies=$((copies + 1))
        a=$(shasum -a 256 "$ENGINE/$f" | cut -c1-64)
        b=$(shasum -a 256 "$ROOT/$p" | cut -c1-64)
        if [ "$a" = "$b" ]; then
            same=$((same + 1)); lines+="      same       $p\n"; continue
        fi
        if from=$(past_commit "$f" "$b"); then
            stale=$((stale + 1)); lines+="      stale      $p  (engine of $from)\n"; continue
        fi
        diverged=$((diverged + 1))
        if [ "${f##*.}" = "py" ]; then
            n=$(diff "$ENGINE/$f" "$ROOT/$p" | grep -c '^[<>]')
            lines+="      diverged   $p  ($n lines apart from the engine)\n"
        else
            lines+="      diverged   $p\n"
        fi
      done
    done
    if [ "$copies" -eq 0 ]; then
        printf "  %-16s calls the engine, keeps no copy\n" "$v"
    else
        printf "  %-16s %d copies: %d same, %d stale, %d diverged\n" "$v" "$copies" "$same" "$stale" "$diverged"
        printf "$lines"
        [ "$stale" -gt 0 ] || [ "$diverged" -gt 0 ] && status=1
    fi
done
echo
if [ "$status" -eq 0 ]; then
    echo "  every variant is on the current engine"
else
    echo "  a stale copy is a variant running yesterday's fixes; a diverged one is a fork."
    echo "  Read the diff and decide per change: engine improvement -> engine/,"
    echo "  variant behaviour -> that variant's own module. Do not copy over."
fi
exit 0
