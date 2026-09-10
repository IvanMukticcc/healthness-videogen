# Where each topic's poster came from, and which of them the repository carries

The poster the generator hands back is **the one artefact in this folder that no
command can remake**. Everything else in the loop is derivable: the base, its
clean copy and its layout come out of one `recolor_base.py` call whose palette is
written down in `Prompts.txt`; the labelled poster is `add_labels.py` over the
poster; the silent pass, the pops, the riser and the cues are `render.sh`. The
poster is the only step whose input is a model and whose output is a roll of the
dice.

## All nineteen now carry the name git carries

Renamed on 9 September to `<topic>_poster.jpeg`, and `grab.py` writes that name
itself since 548f5f6, so nothing here depends on remembering to rename.

The sequence is worth keeping, because it is the same fault twice. The root
un-ignored `*_poster.jpeg` and `*_poster.png` in the morning - but `grab.py` was
still writing `<topic>.jpeg`, which `*.jpeg` ignores, so a commit whose entire
subject was carrying the posters carried none of them. Found by running
`git check-ignore` on an actual poster rather than reading the pattern. Then
`grab.py` was fixed, which made the `mv` this file had just told everyone to add
both unnecessary and wrong - found the same way, by running `grab.py -n` and
reading what it printed.

The conversion to PNG that used to follow the grab is also gone: every tool reads
the jpeg, and a labelled poster built from `<topic>_poster.jpeg` is byte-identical
to one built from a PNG copy. The assumption that downstream wanted a lossless
file was never checked until it was.

## The seven that predate grab.py

Until `grab.py` landed, the download kept the browser's name and was saved beside
the poster under a second name. Both files are still here, and they are the same
image - matched by content on 9 September, mean difference 0.0 on every pair:

| the download, before renaming | is now |
| --- | --- |
| `Arranging_bowls_and_organs_poster_2K_202609070853.jpeg` | thyroid |
| `Instructions_for_image_generation_2K_202609071006.jpeg` | hair |
| `Bowls_and_organs_poster_design_2K_202609071113.jpeg` | superfoods7 |
| `Instructions_for_composing_image…_2K_202609071207.jpeg` | superfoods8 |
| `Design_poster_with_bowls_and_2K_202609071246.jpeg` | superfoods9 |
| `Bowls_and_organs_poster_design_2K_202609071318.jpeg` | superfoods10 |
| `Bowls_and_biological_organs_2K_202609071423.jpeg` | superfoods11 |

## liver and lungs have neither

No `.jpeg` and no `_poster.png`. `liver_labelled.png` and `lungs_labelled.png`
are the only surviving artwork for those two topics, which is why they are not
treated as derived files here even though every other `_labelled.png` is.

## What the repository carries now

Nineteen originals are carried as `<topic>_poster.jpeg`. Seven of those topics
also have a tracked `_poster.png` from before the rename; they are the same image
at twice the size, kept because they are what history already holds.

**liver and lungs still have no original.** Their posters were lost before any of
this, and `liver_labelled.png` and `lungs_labelled.png` - captions already burnt
in - are the only artwork that exists. They are the reason the archival rule
exists rather than an argument about it.

The four topics with no poster at all in here (`bloodsugar`, `heart`,
`superfoods5`, `superfoods6`) cannot be rendered again and were not
reconstructed on 9 September when every other topic was rebuilt.
