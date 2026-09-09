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
# Discovered, not listed. A variant is a folder here with an INPUT/ and a work/.
# It was a hardcoded list of four until 9 September and Longevity - the fifth,
# added the day before - was never checked by it: the loop skips a name with no
# folder, so the omission could not announce itself. A check whose coverage is
# typed by hand goes quietly out of date on the day somebody adds the thing it
# was supposed to cover.
discover() {
    local d
    for d in "$ROOT"/*/; do
        d="${d%/}"
        [ -d "$d/INPUT" ] && [ -d "$d/work" ] && basename "$d"
    done
}
if [ $# -ge 1 ]; then VARIANTS=($1); else VARIANTS=($(discover)); fi
[ ${#VARIANTS[@]} -gt 0 ] || { echo "no variants found under $ROOT" >&2; exit 2; }
FILES=(make_base.py recolor_base.py grab.py clip.py add_labels.py caption_glass.py
       check_base.py flowanim.py
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
# Does anything here shadow the standard library? engine/ is on the import path of
# every tool in engine/, because Python searches a script's own directory first;
# and flowanim.py does sys.path.insert(0, os.getcwd()) for --overlay, which puts
# a variant's work/ ahead of the stdlib for the whole render. So a file called
# copy.py, json.py or types.py in either place breaks tools that never mention
# it, at import time, before any of them can report anything. engine/copy.py did
# exactly that to all four variants on 8 September and it took somebody noticing
# a render that would not start. This is the check that was missing.
#
# Test it in a throwaway tree, never by planting a file in a live work/. The
# obvious way to check a check is to trigger it where it runs, and here that
# takes down every session importing scipy for as long as the file exists -
# which is the very failure being tested for.
shadow=$(python3 - "$ROOT" "${VARIANTS[@]}" <<'PYEOF'
import sys, os, glob
root, variants = sys.argv[1], sys.argv[2:]
std = sys.stdlib_module_names
where = [os.path.join(root, "engine")] + [os.path.join(root, v, "work") for v in variants]
for d in where:
    for f in sorted(glob.glob(os.path.join(d, "*.py"))):
        n = os.path.basename(f)[:-3]
        if n in std:
            print(f"      {os.path.relpath(f, root)}  shadows the stdlib module '{n}'")
PYEOF
)
if [ -n "$shadow" ]; then
    printf "\n  a filename here is on the import path of every tool that runs from it:\n"
    printf "%s\n" "$shadow"
fi

echo
if [ "$status" -eq 0 ] && [ -z "$shadow" ]; then
    echo "  every variant is on the current engine"
fi
if [ "$status" -ne 0 ]; then
    echo "  a stale copy is a variant running yesterday's fixes; a diverged one is a fork."
    echo "  Read the diff and decide per change: engine improvement -> engine/,"
    echo "  variant behaviour -> that variant's own module. Do not copy over."
fi
if [ -n "$shadow" ]; then
    echo "  Rename it. Every tool that imports scipy fails at import time, saying"
    echo "  nothing about the file that caused it, so this never presents as a"
    echo "  naming problem - it presents as the engine being broken."
fi
exit 0
