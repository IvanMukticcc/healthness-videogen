# What survives of Foods' posters, and what does not

Written when the archival rule landed in `../../CLAUDE.md` rule 9, because this
folder is the worst case in the repository and the reason is worth recording
before it is fixed by somebody guessing.

## The state

**Ten clips shipped from this folder on 6 September. Not one of them can be
rebuilt.** `OUTPUT/06.09/` holds bloodflow, bones, eyehealth, immune, skin and
superfoods 1 through 4; none of their posters, bases or labelled posters is on
disk under any name. Those clips are the only record that those topics existed.

Six other topics have working files and were rendered on the 9th — bloodsugar,
heart, liver, lungs, superfoods5, superfoods6 — and of those six, **one still has
its original.**

## Matched by content, not by name

Eleven browser-named downloads sit in this folder. Each was compared against
every labelled poster with the caption bars masked out, since captions are the
only thing `add_labels.py` changes:

    superfoods5    diff 0.00   Posters_with_food_and_organs_2K_202609070813.jpeg
    bloodsugar     diff 22.28  no original on disk
    heart          diff 25.18  no original on disk
    liver          diff 24.62  no original on disk
    lungs          diff 28.65  no original on disk
    superfoods6    diff 23.08  no original on disk

A 0.00 is an exact match outside the caption bars. Everything above 22 is a
different poster entirely — the remaining ten downloads are drafts and rejects
from the sessions that produced the finished ones, not the finished ones.

## What is carried, and what it costs

    superfoods5_poster.jpeg     the original, 1.7 MB
    bloodsugar_poster.png       the LABELLED poster, captions burned in
    heart_poster.png            same
    liver_poster.png            same
    lungs_poster.png            same
    superfoods6_poster.png      same

**Five of these are not what `_poster` means anywhere else in this repository.**
Elsewhere it is the un-captioned image the generator returned. Here, for five
topics, the un-captioned image no longer exists in any form, and the labelled
poster is the only surviving artefact — so it is what gets carried, at 3.4 MB
each instead of 1.7, and it carries captions that cannot be changed.

That is a worse archive than every other folder has and it is the honest one.
Re-captioning those five is no longer possible; re-rendering them is.

19 MB in total, against ten topics that are already unrecoverable.

## The rule this folder is the argument for

`grab.py` writes `<topic>_poster.jpeg` and the ignore file carries it, so nothing
grabbed from now on can end up here. What produced this state was the poster
being the one artefact the loop never wrote down: bases are derived, labelled
posters are derived, clips are derived, and the thing all three derive *from* was
ignored by name.
