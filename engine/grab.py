#!/usr/bin/env python3
"""
grab.py - take the newest generated poster out of Downloads.

The generator hands back a file called something like
Athletes_exercising_on_poster_2K_202609071322.jpeg, in whatever folder the
browser downloads to, and every step after that wants it here under a name the
topic owns. Doing that by hand is two Finder windows and a rename, and the one
time it went wrong the poster from the previous topic got animated with this
topic's base - which check_base.py catches only because the palette differs.

So: newest image in Downloads whose size is exactly the poster's, moved in as
<topic>.jpeg. The size check is the whole safety net. A screenshot, an app icon
or a photo is not 1536x2752, and refusing is better than renaming the wrong file
into place. All three variants generate at that size, so the default fits them
all; the poster lands where the caller stands, which is the variant's work/.

    ../.venv/bin/python ../../engine/grab.py forgotten
    ../.venv/bin/python ../../engine/grab.py forgotten --dir ~/Desktop --keep

It moves, and `--keep` is not for routine use. The point of moving is that
Downloads is left empty, so the next poster is the only thing in it and there is
nothing to pick between - which is most of what makes the newest-file rule safe
in the first place. A folder filling with copies is the thing this was written to
stop somebody doing by hand.

`--keep` was reached for once, in September, when four sessions were generating
into one Downloads and a move took one session's poster away from another. That
loss is real, but it is now caught at the next step instead: `check_base.py`
compares the title band and refuses a poster from another base before any time is
spent on it. Prevention moved downstream, so the flag went back to being what it
is for - a one-off, when you know somebody else is mid-generation.

**Putting a file back must not restamp it.** Newest-first is the whole ordering
here, so a poster returned to Downloads has to keep the modification time it
arrived with, or it jumps to the head of the queue and the next grab takes it
instead of the one that was actually just generated. This is not hypothetical: it
is how a poster taken by the wrong variant got back to its owner in September,
and nobody had designed it. `mv`, `shutil.move` and `shutil.copy2` all preserve
the stamp. Plain `cp` does not - it writes the current time - and neither does
generating the file again. Measured, not assumed.
"""
import argparse
import os
import shutil
from pathlib import Path

from PIL import Image

SIZE = (1536, 2752)
EXTS = {".jpeg", ".jpg", ".png", ".webp"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("topic", help="the poster becomes <topic>.jpeg here")
    p.add_argument("--dir", default="~/Downloads", help="where the browser puts it")
    p.add_argument("--size", default="x".join(map(str, SIZE)),
                   help="what a poster measures; anything else is refused")
    p.add_argument("--keep", action="store_true", help="copy instead of move")
    p.add_argument("-n", "--dry-run", action="store_true")
    args = p.parse_args()

    want = tuple(int(v) for v in args.size.lower().split("x"))
    src_dir = Path(os.path.expanduser(args.dir))
    if not src_dir.is_dir():
        raise SystemExit(f"{src_dir} is not a folder")

    found = []
    for f in src_dir.iterdir():
        if not f.is_file() or f.suffix.lower() not in EXTS:
            continue
        try:
            with Image.open(f) as im:
                size = im.size
        except Exception:
            continue                      # not an image the way we need it
        if size == want:
            found.append((f.stat().st_mtime, f))
    if not found:
        raise SystemExit(f"nothing {want[0]}x{want[1]} in {src_dir} - was the poster "
                         f"generated at that size?")

    found.sort()
    _, src = found[-1]
    dst = Path(f"{args.topic}.jpeg")
    if dst.exists():
        print(f"  replacing {dst} from {os.path.getmtime(dst):.0f}")
    print(f"  {src.name}  ({src.stat().st_size / 1e6:.1f} MB, {want[0]}x{want[1]})")
    if len(found) > 1:
        print(f"  {len(found) - 1} older poster-sized file(s) in there, left alone")
    if args.dry_run:
        return
    (shutil.copy2 if args.keep else shutil.move)(str(src), str(dst))
    print(f"  -> {dst.resolve()}")


if __name__ == "__main__":
    main()
