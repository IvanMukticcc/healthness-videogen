#!/usr/bin/env bash
# sync.sh - what has the base generator changed that this folder has not taken?
#
# This folder is a copy of a checkpoint with the micronutrient badges added, and
# the base generator keeps moving underneath it. It moved three times in one
# morning and nothing said so: the prompt gained clear glass bowls and 3D organs,
# add_labels.py started sizing all ten captions together, and flowanim.py grew
# --halo. This folder went on using the old ones, and a poster was generated from
# a stale prompt before anybody noticed.
#
# So: the newest CHECKPOINT_* is upstream, by name, and this reports the drift.
# It never writes - what to take is a judgement, because some of these files are
# deliberately different here.
#
#   ./sync.sh            what differs, and how much
#   ./sync.sh <file>     the actual diff for one file
#   ./sync.sh --all      every diff, in one go
set -uo pipefail
cd "$(dirname "$0")"

UP=$(ls -d ../CHECKPOINT_* 2>/dev/null | sort | tail -1)
[ -n "$UP" ] || { echo "no CHECKPOINT_* alongside this folder" >&2; exit 1; }

# Shared with the base generator, so a difference is drift unless it is listed
# as ours below.
SHARED="base_layer.png ribbon_mask.png ribbon_rgba.png source_wave_poster.jpeg
        make_base.py recolor_base.py check_base.py add_labels.py
        BasePoster.txt"
# Ours on purpose: flowanim.py carries the badge overlay, and the three docs
# carry the badge sections. They still have to be merged when upstream moves,
# which is what the diff is for.
MINE="flowanim.py ImageSwap.txt flow.md Prompts.txt README.md"

echo "upstream: $UP"
echo

if [ $# -gt 0 ] && [ "$1" != "--all" ]; then
    diff -u "$UP/$1" "$1"
    exit 0
fi

for f in $SHARED; do
    if [ ! -f "$UP/$f" ]; then echo "  gone upstream   $f"; continue; fi
    if cmp -s "$UP/$f" "$f"; then
        printf '  same            %s\n' "$f"
    else
        n=$(diff "$UP/$f" "$f" 2>/dev/null | grep -c '^[<>]' || true)
        printf '  TAKE UPSTREAM   %-22s %s\n' "$f" \
               "${n:-binary} line(s) - this folder should not differ here"
        [ "${1:-}" = "--all" ] && diff -u "$UP/$f" "$f"
    fi
done
echo
for f in $MINE; do
    [ -f "$UP/$f" ] || continue
    if cmp -s "$UP/$f" "$f"; then
        printf '  same            %s\n' "$f"
    else
        n=$(diff "$UP/$f" "$f" | grep -c '^[<>]' || true)
        printf '  MERGE           %-22s %s line(s) - ours plus theirs\n' "$f" "$n"
        [ "${1:-}" = "--all" ] && diff -u "$UP/$f" "$f"
    fi
done
echo
echo "  ./sync.sh <file>   to read one of them"
