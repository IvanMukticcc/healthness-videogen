#!/usr/bin/env python3
"""
copy.py - the two things that get handed to the generator, onto the clipboard.

`grab.py` is the way back: the poster the generator returned, out of Downloads
and into the variant. This is the way out. A topic costs two paste actions - the
base image and the prompt - and both of them were being done by hand: opening
INPUT in Finder and dragging a file, and selecting a hundred and fifty lines of
terminal output with a mouse without catching the shell prompt at the end.

    ../../engine/copy.py image <topic>      base_<topic>.png -> clipboard
    ../../engine/copy.py prompt             the last prompt handed over -> clipboard
    ... | ../../engine/copy.py prompt -     hand one over: copy it, and remember it

Run from a variant's work/, like every other engine tool. The base resolves at
../INPUT/base_<topic>.png, which is the one place rule 7 allows it to be.

## The prompt is still not a file

Rule 8 says the prompt is written in the terminal for the topic at hand and
handed over whole, because a saved copy goes stale in an afternoon. That rule is
about *per-topic* files - prompt_liver.txt, three revisions old, pasted again
because it was lying there. It is not about the clipboard, and `copy.py prompt`
does not create one of those files: there is a single buffer, in the system
temp directory, holding only the last prompt handed over. It is overwritten by
the next one, it does not survive a reboot, and every re-copy prints its age and
its topic so a stale one announces itself rather than being pasted quietly.

Over --stale-after minutes it refuses. If a prompt is an hour old the topic has
moved on, and the right answer is to have the agent write it again rather than
to reach for a buffer.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BUF = Path(tempfile.gettempdir()) / "healthness_last_prompt.json"
SIZE = (1536, 2752)
KIND = {".png": "PNGf", ".jpg": "JPEG", ".jpeg": "JPEG"}


def to_clipboard_image(path):
    """AppleScript is the only way to put a *picture* on the macOS clipboard;
    pbcopy would put the bytes there as text and the generator would refuse it."""
    kind = KIND.get(path.suffix.lower())
    if kind is None:
        raise SystemExit(f"{path.name} is not a png or a jpeg")
    p = str(path.resolve()).replace("\\", "\\\\").replace('"', '\\"')
    script = f'set the clipboard to (read (POSIX file "{p}") as \u00ab' \
             f'class {kind}\u00bb)'
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"could not reach the clipboard: {r.stderr.strip()}")


def cmd_image(args):
    base = Path(args.dir).expanduser() / f"base_{args.topic}.png"
    if not base.exists():
        have = sorted(p.name[5:-4] for p in Path(args.dir).glob("base_*.png"))
        raise SystemExit(f"no {base}\n  topics in {args.dir}: "
                         + (", ".join(have) if have else "none"))
    # The same safety net grab.py has, pointing the other way. A base that is not
    # the poster's size is a base the mask will not fit, and finding that out
    # after a generation costs the generation.
    try:
        from PIL import Image
        with Image.open(base) as im:
            size = im.size
    except ImportError:
        size = SIZE
    if size != SIZE and not args.any_size:
        raise SystemExit(f"{base.name} is {size[0]}x{size[1]}, not "
                         f"{SIZE[0]}x{SIZE[1]} - --any-size to send it anyway")
    to_clipboard_image(base)
    print(f"  {base.name} on the clipboard  ({size[0]}x{size[1]}, "
          f"{base.stat().st_size / 1e6:.1f} MB)")
    print("  attach it to the generator, then paste the prompt")


def cmd_prompt(args):
    # Only ever stdin when asked for it by name. The first version guessed, with
    # `not sys.stdin.isatty()`, and that is false in every script, pipeline and
    # agent subprocess - which is exactly where this runs. A bare `copy.py
    # prompt` then tried to read a prompt nobody was sending and failed instead
    # of re-copying the last one.
    if args.text == "-":
        text = sys.stdin.read()
        if not text.strip():
            raise SystemExit("nothing on stdin")
        subprocess.run(["pbcopy"], input=text, text=True, check=True)
        BUF.write_text(json.dumps(dict(text=text, at=time.time(),
                                       topic=args.topic or "", cwd=os.getcwd())))
        n = len(text.splitlines())
        print(f"  prompt on the clipboard, {n} line{'s' * (n != 1)}"
              + (f", {args.topic}" if args.topic else ""))
        return

    if not BUF.exists():
        raise SystemExit("no prompt has been handed over yet - pipe one in with "
                         "`| copy.py prompt -`")
    d = json.loads(BUF.read_text())
    age = (time.time() - d["at"]) / 60.0
    where = Path(d.get("cwd", "")).parent.name or "?"
    if age > args.stale_after:
        raise SystemExit(
            f"  the last prompt is {age:.0f} minutes old ({d.get('topic') or 'no topic'},"
            f" {where})\n"
            f"  Rule 8: a saved prompt goes stale. Ask for it to be written again\n"
            f"  rather than pasting this one. --stale-after to override.")
    subprocess.run(["pbcopy"], input=d["text"], text=True, check=True)
    print(f"  prompt on the clipboard again  ({d.get('topic') or 'no topic'}, {where}, "
          f"{age:.0f} min old, {len(d['text'].splitlines())} lines)")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = p.add_subparsers(dest="what", required=True)

    i = sub.add_parser("image", help="the topic's base image onto the clipboard")
    i.add_argument("topic")
    i.add_argument("--dir", default="../INPUT", help="where the bases are")
    i.add_argument("--any-size", action="store_true",
                   help="send a base that is not 1536x2752")
    i.set_defaults(fn=cmd_image)

    q = sub.add_parser("prompt", help="the prompt onto the clipboard")
    q.add_argument("text", nargs="?", help="'-' to read the prompt from stdin")
    q.add_argument("--topic", help="what it is for, printed back on a re-copy")
    q.add_argument("--stale-after", type=float, default=45.0,
                   help="minutes after which a stored prompt is refused")
    q.set_defaults(fn=cmd_prompt)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
