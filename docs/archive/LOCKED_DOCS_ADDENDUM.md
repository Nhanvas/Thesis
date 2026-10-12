# Addendum to the Locked Planning Documents

Issued 2026-09-06, after the verification pass closed.

`THESIS_OUTLINE_FINAL.md`, `FIGURES_TABLES_LIST.md`, `CHAPTER_WRITING_BRIEF.md` and
`CHAPTER_REVIEW_PROTOCOL.md` remain in force. This file supersedes the specific lines listed
below and nothing else. Where this file and one of those four disagree, **this file wins**;
everywhere else they are unchanged.

Each item exists because a value or a claim in the planning documents was checked against the
result files and did not hold. The evidence for every one is in `docs/VERIFIED_NUMBERS.md`,
which is the source for all numbers from here on.

Read this before writing or revising any chapter.

---

# 1 · Corrections that change what a chapter says

## 1.1 Detection latency — Chapter 4, discussion of the first result section

**Superseded:** the sentence stating that under event-level scoring the latency sits at or
after onset.

**Replacement claim.** It does not. At the reported operating point, 25 of 48 matched
detections have negative latency and the median is **−4 s**. The earlier informal claim of
detection before onset is still withdrawn, but for a different reason: the matching rule
permits a detected interval beginning up to 30 s before the annotation to count as matched, and
the distribution stops at exactly −28 s, truncated at that boundary. The negative values come
from the rule, not from anticipation. Write it that way.

Two facts travel with any latency number. The latency matcher is a separate implementation from
the scoring framework's own matcher, and its match count exceeds the true-positive count by
exactly one at every operating point. And the 4 s window quantises everything, so values of
−4, 0 and +4 carry no information.

## 1.2 Sparsification verdict — Chapter 2, edge sparsification decision

**Superseded:** the third numbered reason, citing a measured gain in separation between ictal
and interictal connectivity.

**Why.** The raw measure does not show one — it appears worse for six of eight subjects. That
appearance is an artefact: the proportional rule removes about eighty percent of the entries the
measure sums over, so it shrinks arithmetically whatever happens to separation. The two rules
are not comparable on that measure.

**Replacement.** Two reasons, both supported.

First, the proportional rule gives an identical density for every patient and both states
(0.196), while the fixed threshold leaves the graph almost fully connected at a density that
varies from patient to patient (0.921 to 0.973). For a patient-independent system, comparability
across patients is the stronger argument, and the outline does not currently make it.

Second, on two measures that are independent of how many edges survive — relative Frobenius
distance and cosine distance — the proportional rule increases separation on **eight of eight**
subjects. Cite those, name which one the figure plots, and say in the caption why the raw
measure is not used.

**Do not cite** the range "+88 % to +411 %" from the graph-construction module's docstring or
the earlier solution document. Its per-subject output was never committed and it has not been
reproduced.

## 1.3 Ensemble weighting — Chapter 2, ensemble section

**Superseded:** the attribution of equal weighting to a measured flat weight surface.

**Why.** The surface is not flat for the branch set actually used. On the validation subjects
the optimum sits at (0.10, 0.45, 0.45) with 0.9405, against 0.9283 at equal weights — a gap of
**0.0122**, against a spread across independently trained models of 0.0025. Equal weighting
falls outside the 0.005 tolerance band that holds 29 of 231 grid points.

**Replacement claim.** Equal weighting was inherited from the earlier three-branch configuration
and applied unchanged. A post-hoc sweep places the window-tier optimum elsewhere by an amount
above the noise threshold. The weights were not re-derived, because doing so after the held-out
set had been scored would be selection on the final result.

Two limits belong in the same paragraph. The original derivation procedure also required a
cross-check on the training subjects with a documented fallback to equal weights; the training
components are not committed, so that step could not be run. And the gap is at the window tier,
where differences in this project have repeatedly failed to reach the event tier — the optimum
reduces the reconstruction weight to 0.10, the same direction as removing that branch entirely,
which is known to lose at the event tier.

## 1.4 Number of design alternatives — Chapter 4

**Superseded:** any statement of seven falsified alternatives.

**Replacement.** Seven were registered; **six were measured**. The seventh, additional
per-channel time-domain features, was never built and belongs in future work, not in the count.
Take the count from the alternatives table itself, counting only rows that were evaluated.

## 1.5 Channel annotation — Chapters 2, 3 and 4

**Superseded:** every description of the channel annotation as expert, as a reader's, or as a
clinical reference; and the claim that the model's ranking is consistent with a human reader.

**Why.** The annotation file records, for all 76 seizures, that it was machine-generated from an
earlier automated pass. It was not produced by a human reader and has not been reviewed by the
supervising clinician.

**Replacement.** Chapter 2's annotation subsection states plainly how the annotation was
produced and that it has not undergone clinical review. Chapter 3's agreement subsection is
titled as agreement with a **draft** annotation. Chapter 4 states the limitation as a property
of the annotation, not a failure of the method: no channel-level ground truth exists for this
corpus, so the comparison establishes that the ranking is not arbitrary with respect to visible
discharge morphology, and does not establish clinical correctness.

The label-free half is unaffected and is not provisional. It carries the third objective on its
own: the synthetic gates, the permutation null, and the ranking agreement across independently
trained models.

A fallback that does not depend on the supervisor's answer is set out in
`docs/VERIFIED_NUMBERS.md` §7.1. Chapter 3 is not blocked.

## 1.6 The unsupervised comparator — Chapters 1 and 4

**Superseded:** the instruction to use 0.68 for the unsupervised CHB-MIT comparator.

**Why.** In that paper's results table, 0.68 is the accuracy and also the discrimination value.
The sensitivity is **0.64**. Putting 0.68 in a sensitivity column is an error.

Two further limits, from the paper's own description. Its folds partition **windows**, not
patients, so it is not patient-independent in the sense this thesis uses. And it reports no
false-alarm rate, so **it cannot appear on the sensitivity-against-false-alarms figure at all**.
It belongs in the comparison table with its scoring level stated.

## 1.7 The patient-independent band — Chapter 4

The 2025 challenge report gives, for the winning submission, F1 0.43 at 1.34 false alarms per
day, with sensitivity 0.37 and precision 0.45, scored at event level on a held-out
patient-independent dataset. A commercial system in the same comparison reached 0.441.

The honest positioning, both halves together: the reported headline of F1 0.213 at 27.4 false
alarms per day sits below that band; the trade-off curve reaches F1 0.426 at 4.9, matching the
winning submission's F1 but at nearly four times its false-alarm rate, on a different dataset,
and at a point located after the held-out set had been scored.

## 1.8 The attribution comparator

The cited figures 0.704, 0.551, 0.432 and 0.775 are the stronger of two variants reported in
that paper; the other gives 0.667, 0.433, 0.424, 0.745. Name the variant. The dataset is not
CHB-MIT, so this is a reference for scale and never a like-for-like comparison.

## 1.9 Corpus scope

The report uses 23 subjects and **says nothing about the twenty-fourth**. Every corpus figure
comes from this project's own parse of the 23 summary files, recorded in
`docs/VERIFIED_NUMBERS.md` Part 3 — never from a corpus description quoted out of a cited paper.
Published descriptions give 23 in some places and 24 in others; copying one into a chapter whose
tables say 23 is a contradiction inside a single chapter.

## 1.10 Two corrected constants

The model has **3,285** parameters. The figure of approximately 8.7k that circulates in this
project's notes is wrong and is inconsistent with the checkpoint's own file size.

There are **twelve** training subjects. The split file's first key holds fifteen because it
includes the three validation subjects; the twelve-subject set is the inner key.

---

# 2 · Corrections that change an exhibit

## 2.1 Confidence intervals are dropped from the detection results

Tables 3.3 and 3.4 and Figures 3.6 and 3.7 report sensitivity, precision, F1 and false alarms
per day with **no intervals**. The interval column of the metrics table is removed, as are the
interval sentences in the methodology and validity sections, and the two interval references
become unused — nothing is renumbered until the consolidation pass.

Intervals remain in two places only, because removing them would make a provisional result look
settled: the attribution agreement table and its forest plot keep their bootstrap intervals, and
the permutation result and the across-model spread are reported as single values.

## 2.2 Table 3.3 gains a fifth row and its fourth row is fixed

Row 4 is the final system at **m50 / p0.5**: 0.711, 0.068, 0.123, 64.4.

Row 5 is the final system at the low false-alarm budget, **m75 / p10.0**: 0.342, 0.382, 0.361,
3.6. It is added because the design alternatives were all gated at that budget, and without it
Chapter 4 would cite a figure Chapter 3 never reported.

## 2.3 Five existing figures must be rebuilt before use

`E1_operating_curve.png`, `E2_persubject_breakdown.png`, `W1_roc_curves.png`,
`W2_pr_curves.png` and `W3_score_distribution.png` were built from the **earlier
configuration**. Their status in the figure list changes from existing to rebuild. Evidence and
the rebuild specification are in `docs/FIGURE_REBUILD_BRIEF.md`.

The old files move to `figures/archive/`. They are not deleted — this project archives rather
than deletes, and keeping them lets the two versions be compared. **No chapter may reference a
file in that folder.**

Two existing figures were checked and are correct: the synthetic-injection figure, whose warning
in the figure list was a false alarm, and the per-subject attribution forest plot. The forest
plot's title refers to a reader and must be relabelled per §1.5.

## 2.4 The methodology figure showing reconstruction polarity

Use the two **validation** subjects: one whose reconstruction discrimination is 0.8517 and one
where it inverts to 0.2680. Do not use a held-out subject to illustrate a design decision in the
methodology chapter — it invites an avoidable question about what informed the design.

## 2.5 The variant-effect figure

Shade the band from −0.034 to +0.034 around zero. That is the spread across four independently
trained models — **0.0338**, drawn rounded — and any variant inside it is a tie rather than a
result. The reconstruction-removal variant sits at +0.012, inside the band. Directed connectivity
sits at −0.0339, on the boundary; the caption says so rather than presenting it as a rejection.

An earlier draft of `VERIFIED_NUMBERS.md` gave this spread as 0.0345, which was wrong. The band
itself was always drawn correctly at 0.034.

---

# 3 · Conventions confirmed

**Objectives.** Two objectives were registered; two further goals were added during the work.
Chapters 3 and 5 must make the two registered objectives unmistakable, and mark the other two as
extensions.

**Cross-chapter references.** Still not permitted — five accounts write in parallel and each
chapter must stand alone. Referring to a figure, table or section **inside the chapter being
written** is normal and expected.

**Citations.** Fixed numbered brackets against the distributed reference list. The institutional
template asks for author-date ordering; the numbering is already fixed across the whole list and
will not be changed.

**Length.** No hard page limit. Write what the material needs and cut what it does not. Length
is judged by whether a reader can follow it, not by a count.

---

# 4 · What has not changed

The outline's structure, the figure and table numbering, the reference numbering, the chapter
scope boundaries, the eleven review steps and the severity classes are all unchanged. Nothing in
this file authorises adding, removing or reordering a section.
