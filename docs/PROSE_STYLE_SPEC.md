# Prose Style Specification

Distilled from the two reference theses read in full: **VBPH (K20)**, 50 pages, and **Tri (K20)**,
75 pages. Both scored well on presentation, and both are inside the scope of this work — one is an
explainability study on a biosignal, the other a deep-learning study with an honest account of what
failed.

This file governs **how the report is written**, not what it says. Content authority stays with
`VERIFIED_NUMBERS.md`, `LOCKED_DOCS_ADDENDUM.md`, `WRITING_PHASE_ADDENDUM.md` and the outline.

Nothing here licenses a number, a citation or a claim. Where this file and an authority document
appear to disagree, the authority document wins and this file is irrelevant.

---

## 1 · The one habit that separates the two references from an ordinary draft

**Every section and every paragraph opens by carrying the previous one forward.** Tri does this
almost without exception:

> "Building upon these concerning statistics, the number of people with Alzheimer's is expected to grow quickly."
> "Given these projections and the limitations of available treatments, it becomes imperative to deepen our understanding of…"
> "Recognizing this critical need, medical professionals emphasize that early detection…"

The rule underneath it is **old information first, new information second**. The first clause of a
paragraph names something the reader already has; the rest of the sentence adds what is new. A
paragraph that opens on a fact the reader has never seen reads as a restart, and five restarts in a
row read as a list of notes rather than an argument.

This is a *within-chapter* device. It does not license cross-chapter narration, which the writing
brief forbids: no "as discussed in Chapter 1", no chapter-opening roadmap, no chapter-closing
summary. Bridge between adjacent paragraphs and adjacent sections, never between chapters.

---

## 2 · Four paragraph patterns, reusable as they stand

**2.1 Praise, then limit, then decide.** Used for every literature subsection and every rejected
design option. VBPH:

> "MFCC was a well thought out and well-tested method… **However**, after multiple steps of computing, the output matrix was no longer intuitive… **Nevertheless**, this method was still tested."

Three beats: what the method is good at, the specific property that makes it unsuitable here, the
decision taken. Every literature subsection in Chapter 1 ends on the limitation, not on a citation.

**2.2 Announce the exhibit, read it, then interpret it.** Tri:

> "**Figure 18 reveals** the results of training a super net using DARTS. *(announce)* The search converged quickly, finishing in just 20 epochs. The plot shows fluctuations in loss, training accuracy, and F1 score towards the end. *(read)* **This suggests that** additional training might not lead to further improvements. *(interpret)*"

No table or figure ever stands alone. The paragraph immediately after it does these three things in
this order, and the interpretation step carries a hedge. In this report, the interpretation beat
belongs to Chapter 4 for most exhibits — Chapter 3 announces and reads, and stops.

**2.3 Two numbers, one relation, then a mechanism.** Tri:

> "The low recall for AD (0.295) **paired with** high specificity (0.908) **indicates that** while the model rarely misclassifies other conditions as AD, it frequently fails to identify actual AD cases, **likely** mislabeling them as MCI."

Two values in one sentence joined by an explicit relation, converted into a statement about
*behaviour*, and only then a hypothesised mechanism carrying "likely". Never a bare list of metrics.

**2.4 The self-limiting sentence.** This is the most important pattern for this report, because the
attribution results are provisional and the false-alarm rate is measured on a partly substituted
timeline. VBPH:

> "It is also worth noting that the inference on CNN classifier **does not necessarily identify entirely** the features for each class, **but only** a number of differences required to differentiate between the classes."

> "…although it could be said that these two frequencies contained most of the distinction, **it did not necessarily mean that** the results would be as good if we only used these two frequencies for input."

The shape is: state what the measurement *does* establish, then state the narrower question it
actually answers. Use it wherever a metric answers less than the reader will assume — every
attribution result, the channel annotation, the latency distribution, the comparison against
published work.

---

## 3 · The hedging ladder

| Strength | Verbs | Use for |
|---|---|---|
| Description only | *It can be seen that · Figure N shows · Table N reports* | reading an exhibit, before any inference |
| Speculation | *may · might · could · potentially* | a mechanism with no direct evidence |
| Evidenced inference | *suggests · indicates · implies · points to* | the default for almost every sentence in Results and Discussion |
| Strong | *demonstrates · reveals · confirms · underscores* | only where several independent measurements converge |

Tri uses *underscoring* once in seventy-five pages, at the point where three metrics agree. Copy
that discipline. In this report the strong verbs are earned in exactly two places: the convergence
of the six falsified design alternatives, and the synthetic validation of the attribution method.
Everywhere else, stay on the third rung.

---

## 4 · Technical conventions

**Tense.** Present for definitions, background knowledge and what an exhibit shows. Past for what
this study did. VBPH slips here — *"PCA was a statistical technique"* — do not copy that.

**Person.** The subject is *this thesis*, *this study*, *the proposed pipeline*, *the framework*.
Never *my model* (Tri) and never *our dataset*. Never *I* outside the acknowledgements; VBPH's
closing *"I aspire to…"* does not belong in this report.

**Voice.** Passive dominates the methodology — *was applied, were selected, was fitted on*. Active
dominates the introduction and discussion, where an argument is being made.

**Sentence rhythm.** One long sentence carrying the argument, then a short one driving it home.
VBPH does this best: *"The result could always be improved, but explainability could not."* One such
sentence per major section is enough; more and they lose force.

**Numbers.** Always attached to a metric name and a population: *"sensitivity of 0.618 across the
eight held-out patients"*, not *"0.618 sensitivity"*. Parenthesise the exhibit reference at the end
of the sentence, not mid-clause. Three decimals for sensitivity, precision, F1 and AUROC; one for
false alarms per day.

**Paragraph length.** Four to eight sentences, one job each. A two-sentence paragraph is usually an
orphaned thought that belongs to its neighbour.

**Terminology.** One name per concept for the whole report, fixed on first use: one name for the
fused score, one for each of the three component scores, one for the earlier configuration. The
component scores are named by what they measure — reconstruction error, latent distance, spectral
coupling — never by their internal nicknames.

---

## 5 · Writing a negative result

Both references report failures without apologising, and both score well for it. Tri's four-step
formula, which this report should follow every time a design alternative is reported:

1. **State the outcome flatly.** *"Attempts to mitigate this by reducing channel dimensions are complicated by the interdependence between patch embedding and transformer encoder channel sizes."*
2. **Give the mechanism.** *"The failure of this approach can be attributed to persistent numerical instability, potential overflow or underflow in computations…"*
3. **Bound what may be concluded.** *"These issues suggest that the inherent characteristics of MRI data may not be ideally suited for the current KAN architecture implementation."*
4. **Name the condition under which it might work.** *"…a potential alternative approach could involve using KAN in a continuous, multi-layer configuration."*

Banned: *unfortunately*, *we failed*, *sadly*, and any *as expected* attached after the result was
seen. A negative result reported as anything other than a negative result is a blocker.

---

## 6 · Positioning against published work when the number is lower

Two templates, both from the references, both honest.

VBPH concedes then redirects to the contribution:

> "**Admittedly**, this study's task was comparatively easier compared to the other. **However**, this study provided more than just a model with high results, but a framework and methodology…"

Tri names the specific asymmetry rather than complaining about it:

> "The performance gap **might be attributed to** the use of pretrained weights in some of the compared studies, which my model doesn't utilize."

For this report the asymmetry is named precisely and never used as a blanket excuse: the comparators
are supervised and this system uses no seizure label; where a comparator uses a different corpus,
scoring rule or patient split, that difference is stated in the same sentence as the number. The
comparison that needs no such caveat — same corpus, same scoring level, same patient split — is the
one to lead with.

---

## 7 · Faults in the references — do not reproduce them

- **Hien and Tuong are out of scope**; only VBPH and Tri are models for this report.
- Repetition between adjacent subsections, and duplicated section numbers (Hien has two §4.3).
- An empty section with a heading and no text (Hien §2.1).
- Inflated register: *bespoke, encouraging, remarkable, impressive, quite high*. Tri's *"remarkable
  performance"* is the single worst sentence in an otherwise disciplined chapter.
- Typos surviving into the conclusion (Tri: *"a approach"*, *"results shơ"*). The conclusion is the
  last thing a committee reads and the least excusable place for one.
- Broken sentences and imprecise words used as if technical (*"harmful"* where *"negatively
  correlated"* was meant).
- Cost tables presented with more decimal places than the estimate can support.

---

## 8 · Which reference each chapter follows

| Chapter | Model | What to take |
|---|---|---|
| 1 Introduction | **Tri** | statistics → named groups of prior approaches → each group ending on its limitation → a synthesis paragraph that states the gap |
| 2 Methodology | **VBPH** | two beats per method: the general principle, then *"for this study, …"*; decision matrix followed by a verdict paragraph with numbered reasons |
| 3 Results | **VBPH** | flat numbers, exhibit read immediately after it appears, no mechanism, no comparison |
| 4 Discussion | **Tri** | mechanism first, then the comparison table, then honest positioning |
| 5 Conclusion | **VBPH** | short, quotes only numbers already reported, limitations stated plainly, one forward-looking paragraph |
| Attribution sections, wherever they appear | **VBPH** | the self-limiting sentence of §2.4, at every occurrence |
