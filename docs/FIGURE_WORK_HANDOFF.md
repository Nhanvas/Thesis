# Figure Work — Handoff

Everything a fresh session needs in order to finish the report's figures. No transcript required.

Authority: `docs/VERIFIED_NUMBERS.md` for every number, `FIGURES_TABLES_LIST.md` for what each
exhibit must contain, `docs/LOCKED_DOCS_ADDENDUM.md` where it supersedes the exhibit list. If
this file disagrees with any of those, they win.

---

# 1 · Standing rules

1. **Every number is read from a committed file.** If a value has to be typed in for a figure
   to render, the wrong source is being used. Each script keeps a numeric self-check against
   `VERIFIED_NUMBERS.md` and stops rather than drawing a value it cannot confirm.
2. **The system is the final one.** Grids come from `results/phaseB/tier2/rlg_test/`, score
   arrays from `results/phaseB/tier2/ens_test_tf/rlg/`. Anything under `baseline_rtg`,
   `ens_test_base`, `retrain_v3p1` or `history_superseded` is an earlier configuration. Five
   figures were already built from one of those by mistake; they now sit in `figures/archive/`
   and nothing may reference them.
3. **The reported operating point is m50 / p2.0**: sensitivity 0.618, precision 0.129,
   F1 0.213, 27.4 false alarms per day. Every figure marking an operating point marks this one.
   The best point on the curve, m80 / p5.0 at F1 0.426 and 4.9 false alarms per day, is labelled
   as located after the fact and never as a result.
4. **No confidence intervals on detection figures.** Intervals remain only on the attribution
   agreement figure.
5. **PNG only.** One file per exhibit. A second format drifts out of step with the first, and
   already did once — a figure was reviewed in one format while the other stayed stale.
6. **One palette**, `src/figures/palette.py`, across every figure including hand-drawn ones.
7. **Archive, never delete.** Superseded figures move to `figures/archive/`.
8. **A refusal is a valid answer.** If an instruction conflicts with a committed value, say so
   and stop rather than changing the number to fit. That has already prevented one error, where
   a document held a wrong value and the figure was right.
9. **Report each instruction as applied or not applied**, with the file and line. When several
   instructions touch one file, none is skipped because another one in that file needed no
   change — that has already caused four instructions to be silently dropped.

---

# 2 · Done — do not revisit

Fig 2.3 · 2.8 · 2.9 · 3.1 · 3.2 · 3.3 · 3.5 · 3.6 · 3.7 · 3.9 · 3.11 · 3.12 · 3.13 · 3.14, and
the appendix channel table. All checked against the recorded values and against their
specification.

**One loose end.** After the last round, `fig3_5` and `fig3_6` did not appear as modified in
version control while `fig3_7` and `fig3_9` did. Both were reviewed in a format that has since
been removed. Regenerate them and confirm they carry the last round's corrections: `fig3_6`
must have its legend clear of the annotation box and F1 on both point labels; `fig3_5` must have
two separate tolerance entries, the second reading "+60 s after seizure end".

---

# 3 · Nine figures that need code

All read committed data. None can be drawn by hand.

| | Content | Source |
|---|---|---|
| Fig 1.2 | Two connectivity heatmaps, interictal against ictal, shared scale, one colorbar | `data/processed/{subj}_{interictal,ictal}_adjs_topk20.npy` |
| Fig 2.2 | Histogram of annotated seizure durations, logarithmic horizontal axis | `data/summaries/`, held-out subjects. Recorded values: 76 seizures, minimum 6 s, median 45 s, mean 51.9 s, maximum 205 s, with 23 shorter than 20 s |
| Fig 2.4 | One window becoming a graph, in four panels: signal, band powers, weighted adjacency, resulting graph | `data/processed/` raw windows, features and adjacency for the running-example recording |
| Fig 2.5 | Adjacency and density under both sparsification rules, density printed in each panel title | Same arrays. Recorded densities: fixed threshold 0.921–0.973 varying by patient, proportional rule 0.196 for every patient |
| Fig 2.10 | Change-point detection on an anomaly score series, detected points as vertical lines, annotated seizure shaded | Fused score for the running-example recording |
| Fig 3.4 | Detection output on one full recording: three component scores, the fused score, detected intervals, annotated seizure | Same recording |
| Fig 3.8 | Window-level against event-level performance, one labelled point per patient, reference lines separating the two failure regions | `VERIFIED_NUMBERS.md` §1.2 and §1.1 |
| Fig 3.10 | One false positive with the concurrent signal, score above and signal below | Same recording |
| Fig 3.15 | Diffuseness against the number of annotated channels, a line for the synthetic case and points for the real annotations | `results/attribution_v6/synthetic_spread.csv` and the summary file |

## The running example

**Patient chb13.** Its window-level value is 0.822, close to the across-patient figure of 0.805,
so it represents the system rather than its best case. The strongest patient sits at 0.964 and
using it for three illustrative figures would be a soft form of selection.

Fig 2.10, Fig 3.4 and Fig 3.10 must use **the same recording**, not merely the same patient.
Pick one file from chb13 that contains at least one correctly detected seizure and at least one
false positive at the reported operating point, then fix it and name it in all three captions.

## The one technical trap

The committed score arrays are **ordered by segment and carry no index into recording time**.
A figure with a time axis has to rebuild that axis with `szcore_eval.build_timeline_masked()`,
which reconstructs it from the annotation file. That is legitimate here — this is offline
scoring with labels available. It is forbidden only in the web application, which must never
touch the annotations. Expect to need it for Fig 2.10, 3.4 and 3.10.

---

# 4 · Eight figures to draw by hand

Fig 1.3 pipeline overview · Fig 1.4 timeline · Fig 1.5 research framework · Fig 2.6 autoencoder
architecture · Fig 2.7 the three readouts from one encoder · Fig 2.11 attribution scoring and
the injection scheme · Fig 2.12 application architecture · Fig 2.13 why stored scores cannot be
replayed on a time axis.

None touches data. Both reference theses drew their architecture and framework diagrams the same
way and used code only for results, so this is the normal division, not a shortcut.

Use a technical diagram tool that exports at print resolution. Avoid presentation-design tools:
they produce decorative output that reads as unserious in a technical report.

**Two constraints.**

Numbers on a diagram come from the record, not from memory. Fig 2.6 carries layer dimensions
23 → 64 → 16 with a decoder 16 → 32 → 5, and **3,285** parameters in total; a figure of roughly
8.7k circulates in this project's notes and is wrong. Fig 2.7 shows **three** branches and never
a recurrent one — that branch was removed and must not appear anywhere in the report.

Colours come from `src/figures/palette.py`, so the hand-drawn set and the plotted set look like
one document.

---

# 5 · Three figures adapted from published sources

Fig 1.1 stages of the EEG signal · Fig 2.1 the bipolar montage on a head schematic ·
Fig 2.14 the event-based scoring rules.

Redraw them; do not screenshot. Each caption names the source it is adapted from. Fig 1.1 is
first in the cut order if space runs short, so leave it until last.

---

# 6 · Blocked

**Fig 3.16, 3.17, 3.18** are application screenshots and wait on that build.

**Fig 4.1** places this work's trade-off curve against published reference points and waits on
the first chapter's study set. It will be sparse, and that is correct: only results scored at
event level on patient-independent data can appear, and the unsupervised comparator on this
corpus reports no false-alarm rate at all, so it cannot be plotted. Expect two or three external
points beside this work's curve. Nothing may be added to the plane to make it look fuller.

---

# 7 · Repository notes

`.gitignore` once held a bare pattern that matched the figure source directory at any depth, so
every plotting script sat outside version control while appearing to be part of the repository.
The pattern is now anchored to the root output folder and the scripts are committed. **Check
that new figure scripts are actually tracked before assuming an edit is safe.**

`src/dataprep/plot_raw_vs_preprocessed.py` called a function that did not exist and could not
run at all; it has been repaired. Treat an untracked script as unverified until it has been run.
