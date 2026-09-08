# What the evidence actually says, and what that costs the poster

Researched before any row was written, because this is the first category whose
subject can hurt somebody and the first whose parent app carries a health
disclaimer it must not contradict.

The rule this produces: **the strongest row is the least evidenced one**, and the
whole discipline of this folder exists so that it can be shown at all.

---

## The hour thresholds

`fitcircle/Sources/Models/Fasting.swift` is the source for the poster, and it is
conservative in the right direction on every stage:

| stage | the app | what the literature supports |
| --- | --- | --- |
| anabolic | 0-4 h | uncontroversial. Digestion and absorption |
| catabolic | 4-12 h | uncontroversial. Glycogen as the main fuel |
| fat burning | 12-16 h | supported. Lipolysis rises as glycogen falls |
| ketosis | 16-24 h | **the app is later than the literature.** Ketosis begins to some degree at about 12 h and varies widely between individuals |
| autophagy | 24-48 h | **the app is earlier than human evidence supports.** See below |
| deep ketosis | 48+ h | flagged in the app as advanced, consult a clinician |

Two of the six are worth care, and only one is a problem.

**Ketosis at 16 h** is the app being cautious — the literature puts the onset
earlier and more variable. Being late is a safe direction to be wrong in, and
"typically" already carries the variance.

**Autophagy at 24 h is the row to be careful with, and it is also the row that
will travel furthest.** That is not a coincidence: it is the most striking claim
in the set, which is exactly why it is the one everybody repeats and the one with
the thinnest human evidence.

## Autophagy, specifically

What is actually established:

- autophagy is well demonstrated in **animal models** and in **cultured human
  cells** — neutrophils show it after about 24 h
- in living humans the measurements are mostly **autophagy-related gene
  expression** in muscle and peripheral blood, not autophagic flux itself
- a 2025 exploratory analysis reports that intermittent time-restricted eating
  **may** increase autophagic flux in humans, and describes itself as exploratory
- estimates for *significant* autophagy from fasting alone in humans run to
  **two to four days**, not 24 hours

So the popular "autophagy at 16 hours" and even "at 24 hours" are ahead of the
human evidence. The app's own wording already handles it and is the reason this
category can exist:

> "Longer fasts have been associated with autophagy — the cellular process of
> recycling damaged components. **Research is ongoing.**"

Three things in one sentence: *associated with* rather than *causes*, *longer
fasts* rather than an hour, and the state of the field stated out loud.

## What this decides in the design

1. **"Research is ongoing" is drawn on the poster, not buried in a caption
   nobody reads.** The autophagy row carries it visibly. A category that shows
   its own uncertainty is more shareable, not less — it is the difference
   between a clip somebody sends to their doctor and one they send instead of
   asking.

2. **`claim: measured | described` is the field the checker turns on.** A stage
   is `described`: the app's own careful sentence, copied verbatim. A protocol's
   hours are `measured`: 16:8 is arithmetic. Nothing on the poster is a study
   result presented as a promise, because we are not in a position to present
   one.

3. **The checker refuses a `described` row whose value carries `%` or `+`/`-`.**
   That is exactly how a descriptive stage becomes a medical claim by accident —
   "autophagy" becomes "+40% autophagy" in somebody's rewrite at two in the
   morning, and the sign is the tell. Biohacks' idea, and this is the evidence
   that makes it load-bearing rather than tidy.

4. **Never paraphrase the app's stage summaries.** Copy them. The compliant
   phrasing *is* the source, and a paraphrase is a new claim with no source
   behind it. This is the one place in the repository where copying text is the
   careful option rather than the lazy one.

5. **The hours are the app's, not the literature's.** Where they differ, the app
   is what the product tells its users, and a Short that contradicts the app it
   advertises is worse than one that is a little conservative. Ketosis stays at
   16.

## Sources

- [A Biochemical View on Intermittent Fasting's Effects on Human Physiology](https://pmc.ncbi.nlm.nih.gov/articles/PMC12190167/)
- [Intermittent fasting: a comprehensive review of cellular mechanisms, metabolic processes, and organ health](https://link.springer.com/article/10.1007/s44361-025-00007-z)
- [Intermittent time-restricted eating may increase autophagic flux in humans: an exploratory analysis](https://physoc.onlinelibrary.wiley.com/doi/full/10.1113/JP287938)
- [Intermittent fasting improves metabolic outcomes in metabolic syndrome: a systematic review and meta-analysis with GRADE evaluation](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12738305/)
- [How Long Do You Need to Fast for Autophagy?](https://www.medicinenet.com/how_long_do_you_need_to_fast_for_autophagy/article.htm)
- `fitcircle/Sources/Models/Fasting.swift`, lines 219-303
