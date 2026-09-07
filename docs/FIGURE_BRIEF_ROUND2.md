# Figure Brief — Round 2

Nine figures that need code, one figure to rebuild, four tables to emit, and one diagnostic to
extend. Everything here reads committed files. Nothing here re-runs the model.

**Authority.** `docs/VERIFIED_NUMBERS.md` for every number. `docs/LOCKED_DOCS_ADDENDUM.md` where
it supersedes the exhibit list. `docs/FIGURE_WORK_HANDOFF.md` for what is already finished. If
this file disagrees with any of those, they win — say so and stop rather than resolving it
silently.

**Do not touch** the fourteen finished figures: 2.3 is handled in §3 below, and 2.8, 2.9, 3.1,
3.2, 3.3, 3.5, 3.6, 3.7, 3.9, 3.11, 3.12, 3.13, 3.14 are closed. Their PNGs were confirmed current
on 2026-09-07 and the loose end recorded in the handoff about 3.5 and 3.6 is closed — do not
regenerate them to check.

**Do not read** anything under `figures/archive/`, `results/history_superseded/`,
`results/phaseB/tier2/baseline_rtg/`, `results/phaseB/tier2/ens_test_base/`, or
`results/retrain_v3p1/`. Those hold an earlier configuration. Five figures were already built from
them once.

---

# 1 · Standing rules

1. **Every number is read from a committed file.** If a value has to be typed in for a figure to
   render, the wrong source is being used. Each script keeps a numeric self-check against
   `docs/VERIFIED_NUMBERS.md` and stops rather than drawing a value it cannot confirm.
2. **PNG only.** One file per exhibit. No PDF, no SVG. Two formats drift apart, and already did.
3. **One palette**, `src/figures/palette.py`. Every script in this round imports it and calls
   `apply_rc()`. Interictal, ictal and detected intervals keep their assigned colours throughout.
4. **No confidence intervals** on anything in this round.
5. **No figure number and no descriptive title inside the image.** The report's caption carries
   both, and a figure that repeats them reads as duplicated. Panel labels — `(a)`, `(b)` — axis
   labels, units and legends stay. This is a change from the earlier round; the fourteen finished
   figures will be brought into line in a single later pass, so do not edit them for this now.
6. **The reported operating point is m50 / p2.0**: sensitivity 0.618, precision 0.129, F1 0.213,
   27.4 false alarms per day. Any figure marking an operating point marks this one. The best point
   on the curve, m80 / p5.0, is labelled as located after the fact and never as a result.
7. **Archive, never delete.** Anything superseded moves to `figures/archive/`.
8. **A refusal is a valid answer.** If an instruction here conflicts with a committed value, say
   so and stop rather than changing the number to fit. That has already caught one error in my own
   documents.
9. **Report each instruction as applied or not applied**, naming the file and line. When several
   instructions touch one file, none is skipped because another one in that file needed no change.
   That has already caused four instructions to be dropped in silence.
10. **Check that new scripts are tracked.** `.gitignore` once matched `src/figures/` at any depth
    and every plotting script sat outside version control while appearing to be part of the repo.
    Run `git check-ignore -v` on each new file before assuming an edit is safe.

---

# 2 · Task A — lock the running-example recording (do this first)

Three figures must show **the same recording**, not merely the same patient: Fig 2.10, Fig 3.4 and
Fig 3.10.

The patient is **chb13**. Its window-level discrimination is 0.822, close to the across-patient
value of 0.805, so it represents the system rather than its best case. chb03 is the strongest of
the eight at 0.964 and using it here would be a soft form of selection.

Find one chb13 recording that, at m50/p2.0, contains **at least one correctly detected seizure**
and **at least one false positive**. Print the candidates with their counts, pick one, and write
the chosen file name into `docs/RUNNING_EXAMPLE.md` together with the counts that justified it.
All three captions name that file.

If no single recording satisfies both conditions, say so and stop; do not silently relax one of
them or switch patient.

---

# 3 · Task B — rebuild Fig 2.3

`figures/raw_vs_preprocessed.png` does not meet its specification and must be rebuilt. Generator:
`src/dataprep/plot_raw_vs_preprocessed.py`. Move the current PNG to `figures/archive/` first.

What is wrong with it: it shows a **single channel**, so it cannot illustrate referencing at all;
and its two panels are identical in shape, differing only in the vertical scale, so a reader sees
a rescaling rather than filtering. Its title says `SUBJECT 10` where the rest of the report says
`chb10`, it uses a double hyphen, and the script does not import the shared palette.

The rebuilt figure:

- **Six channels**, stacked with a constant vertical offset, labelled with their bipolar
  derivation names, on a shared time axis of about 10 s.
- **Two panels side by side or stacked**: raw on the left or top, preprocessed on the right or
  bottom, same channels, same time span.
- **A third panel showing the power spectrum** of one channel before and after, on a logarithmic
  vertical axis, with the 60 Hz line visible in the raw trace and suppressed in the preprocessed
  one. Without this panel the effect of the filtering stage is not visible at all, which is the
  reason the current figure fails.
- Patient **chb10 or chb11** — a validation patient, per the illustration policy in §4.
- Choose a segment where something is visible: drift, a movement artifact, or mains interference.
  Print which segment was chosen and why.
- Import `palette.py`; use the interictal colour for the traces.

---

# 4 · Task C — nine figures

**Illustration policy, decided and not open for reinterpretation.** Chapters 1 and 2 illustrate on
a **validation** patient, `chb11`, so that no figure preceding the results can be read as having
looked at held-out data. The single exception is the running example, Fig 2.10 · 3.4 · 3.10, which
uses **chb13** because those three must be one recording and two of them are results figures. Fig
2.10's caption states that it shows a held-out recording, presented to illustrate the mechanism,
with no parameter chosen from it.

**The adjacency trap.** `data/processed/` contains only `*_adjs_topk20.npy`. There is **no
committed fixed-threshold adjacency array**. Figures 1.2, 2.4 and 2.5 therefore rebuild the
adjacency from the stored windows using `src/dataprep/graph_construction.py` —
`compute_wpli`, `compute_aec`, `combine_adjacency` at `DEFAULT_ALPHA`, then `apply_fixed_threshold`
at `FIXED_THRESHOLD` or `apply_topk_threshold` at `DEFAULT_KEEP_RATIO`. Do not write new
implementations of any of these. This is legitimate because these three figures illustrate a
construction rule rather than reporting a measurement; every *number* printed on them still comes
from a committed file.

**The time-axis trap.** The committed score arrays are ordered by segment and carry no index into
recording time. A figure with a time axis rebuilds that axis with
`szcore_eval.build_timeline_masked()`, which reconstructs it from the annotation file. That is
legitimate here — this is offline scoring with labels available. It is forbidden only in the web
application. Expect to need it for Fig 2.10, 3.4 and 3.10.

## Fig 1.2 — Connectivity during interictal and ictal windows

Two adjacency heatmaps side by side, **shared colour scale, one colorbar**, 18×18, channels
labelled on both axes.

Patient **chb11**. Use the **weighted adjacency before sparsification** — sparsification is a
Chapter 2 concept and this figure sits in Chapter 1. Average over windows: mean interictal
adjacency on the left, mean ictal on the right.

Source: `data/processed/chb11_{interictal,ictal}.npy`, adjacency rebuilt as described above.
Print the number of windows averaged in each panel.

## Fig 2.2 — Distribution of annotated seizure durations

Histogram, **logarithmic horizontal axis**, seconds.

Plot **all 182 seizures of the 23 patients**, with the 76 held-out seizures drawn as a
distinguishable series on the same axes. The exhibit list specifies the held-out set alone, but
this figure sits beside two tables that describe the whole corpus, and a histogram of a subset
next to them is an internal inconsistency. Showing both keeps the limitation argument and removes
the mismatch.

Mark the 4 s analysis window as a vertical line, and annotate the count of seizures shorter than
20 s.

Source: `data/summaries/*.txt`. Self-check against `docs/VERIFIED_NUMBERS.md` Part 3: the held-out
series must give n = 76, minimum 6 s, median 45 s, mean 51.9 s, maximum 205 s, with 23 shorter
than 20 s and 31 shorter than 30 s. Stop if any of these disagree.

## Fig 2.4 — Construction of a connectivity graph from one window

Four panels in sequence, one window of **chb11**:

- **(a)** the 4 s signal segment, all 18 channels, stacked with an offset;
- **(b)** the five log band powers per channel, as an 18×5 heatmap with the band names on one axis;
- **(c)** the weighted adjacency before sparsification, 18×18;
- **(d)** the graph after retaining the strongest 20 % of edges, drawn on a fixed node layout with
  edge width proportional to weight.

Use the same node ordering and the same layout in (c) and (d) so the reader can follow one edge
through. Print the window index chosen and the number of edges in (d) — it should be 30.

Sources: `data/processed/chb11_interictal.npy`, `chb11_interictal_features.npy`, and the graph
construction module.

## Fig 2.5 — Adjacency and graph density under two sparsification rules

Two rows, patient **chb11**. Top row: the fixed correlation threshold. Bottom row: retain the
strongest 20 % of edges. Each row shows the adjacency heatmap and the resulting graph, with the
**density printed in the panel title**.

The density values come from the diagnostic output produced in Task E, not from a value computed
inside this script. If Task E has not been run, stop.

## Fig 2.10 — Change point detection on an anomaly score series

The locked running-example recording. Fused anomaly score against time in minutes; detected change
points as vertical lines; the annotated seizure shaded.

Use `cpd_pipeline_v14.detect_events` with its locked defaults — do not re-implement the smoother
or the penalty. Print the number of change points found and the seizure onset and offset in
seconds.

Sources: `results/phaseB/tier2/ens_test_tf/rlg/ens_seed42_chb13_*.npy`, time axis via
`build_timeline_masked`.

## Fig 3.4 — Detection output on one full recording

The same recording. Stacked panels on a shared time axis:

- the three component scores, one panel each or three lines in one panel with a legend;
- the fused score;
- detected intervals shaded in the detected-interval colour;
- the annotated seizure shaded in the ictal colour.

Sources: `results/phaseB/tier2/ens_test_tf/components/{zrecon,zlatent,zgamma}_chb13_*.npy` and the
fused array. Print the detected interval boundaries in seconds.

## Fig 3.8 — Window-level against event-level performance per patient

Scatter, one labelled point per patient. Horizontal axis: window-level discrimination. Vertical
axis: event-level F1 at m50/p2.0.

Reference lines at the across-patient window value **0.805** and the pooled event F1 **0.213**,
both read from file, not typed.

**chb06 has no F1 at this operating point** — its sensitivity and precision are both zero, so the
harmonic mean is undefined, not zero. Draw it at zero on the vertical axis with an explicit
annotation that F1 is undefined, so it does not read as a plotted value or as missing data.

Print the quadrant each patient falls in. **Expect chb17 to sit just below both reference lines**,
at 0.782 and 0.207, rather than in the high-discrimination quadrant. Report that rather than
adjusting the lines — a claim elsewhere in the project places chb17 with the decision-limited
group, and this figure does not support it. Flag it; do not fix it.

Sources: `results/phaseB/tier2/ens_test_tf/rlg/window_auroc_seed42.json` and
`results/phaseB/tier2/rlg_test/final_eval_seed42.csv` at m50/p2.0.

## Fig 3.10 — A false positive with the concurrent EEG

Two stacked panels on a shared time axis, the same recording: the fused score above, the raw
signal below, six channels. Centre the view on one false-positive interval with about a minute of
context on each side. Shade the false-positive interval.

Print the interval boundaries and confirm from the annotation that no seizure overlaps them.

Sources: as for Fig 3.4, plus `data/processed/chb13_interictal.npy` or the source recording for
the signal panel — state which was used.

## Fig 3.15 — Diffuseness against the number of annotated channels

A line for the synthetic case across the injected-channel counts, and points for the real
annotations at their own channel counts.

Source: `results/attribution_v6/synthetic_spread.csv` for the line, and the per-seizure attribution
file for the real points. If that file has no diffuseness column, **stop and report it** rather
than computing the measure inside the plotting script.

Self-check against `docs/VERIFIED_NUMBERS.md` Part 7.6: on the real annotations, focal 0.9693
against generalized 0.9594, one-sided p = 0.984. The caption states that the measure is U-shaped
in the number of channels and runs the wrong way on real annotations, and that it is therefore
reported as a methodological negative and never used to classify.

---

# 5 · Task D — emit four tables

One script, `src/figures/emit_tables.py`, writing CSV files to `results/report_tables/`. No
values typed in; each table read from the committed file named below.

**Table 3.4 — event-level performance per patient**, at m50/p2.0, from
`results/phaseB/tier2/rlg_test/final_eval_seed42.csv`: patient, seizures, sensitivity, precision,
F1, false alarms per day. Write chb06's F1 as the string `undefined`, not as 0 and not as `nan`.

Self-check against these values, which were printed by `src/figures/plot_event_level.py` and are
recorded here so the emitted file can be verified rather than trusted:

```
chb03 1.000 0.152 0.264 24.7      chb15 0.900 0.286 0.434 27.4
chb06 0.000 0.000 undef  19.4     chb16 0.200 0.105 0.138 21.5
chb13 0.750 0.220 0.340 23.4      chb17 1.000 0.115 0.207 26.4
chb14 0.375 0.049 0.087 53.6      chb18 0.833 0.091 0.164 33.8
```

**Table A.1 — corpus metadata for all subjects**, from `data/summaries/*.txt`: subject, set,
recordings, recorded hours, seizures, total seizure duration. Self-check the per-set totals
against `docs/VERIFIED_NUMBERS.md` Part 3 — 12 / 342 / 566.43 / 93, 3 / 91 / 115.82 / 13,
8 / 231 / 279.39 / 76.

**Table A.2 — channel annotation for every held-out seizure**, from
`results/attribution_v6/labels/ictal_channels_DRAFT.csv`: subject, seizure index, annotated
channels, and the `label_source` field **carried through verbatim**. All 76 rows. The report's
version of this table carries a mandatory banner stating that the annotation was generated
automatically and has not been clinically reviewed; emit the `label_source` column so that banner
can be justified from the file rather than asserted.

**Table A.3 — the full parameter grid**, from `results/phaseB/tier2/rlg_test/final_eval_seed42.csv`:
all 384 rows, columns as committed. This one is a pass-through with a row-count assertion — 384
rows, 8 subjects, 48 cells each.

---

# 6 · Task E — sparsification diagnostic for the validation patient

`src/dataprep/density_frobenius_diagnostic.py` currently covers the eight held-out patients only,
and its committed output is at `results/diagnostics/density_frobenius_v2/`. Fig 2.5 needs the same
quantities for **chb11**.

Run it for chb11 with output to **`results/diagnostics/density_frobenius_v2_val/`** — a separate
directory. Do not write into `density_frobenius_v2/`: that directory holds committed values that
appear in Table 3.1 and Fig 3.1, and it was overwritten once already by a run at the wrong stride,
which put the documents and the source file out of step.

Use the same stride as the committed run. Print the stride you used and confirm it matches.

Sanity expectation, not an assertion: under the proportional rule the density should come out at
about 0.196 for chb11 as it does for every held-out patient, and under the fixed threshold it
should be far higher. If chb11 behaves differently, report it — that is information, not an error.

---

# 7 · What to report back

For each of the fifteen items above: **applied or not applied**, with the file and line changed.
If you decide any item needs no change, say so and say why — do not skip in silence.

Then, before calling anything done:

- print the values each figure plots and check them line by line against
  `docs/VERIFIED_NUMBERS.md`, stopping on any disagreement;
- confirm `find figures -iname "*.pdf"` returns nothing;
- confirm every new script is tracked by git, not matched by an ignore rule;
- list the chosen running-example recording and the two counts that justified it.

Two things I expect you to push back on rather than accommodate: any instruction here that
disagrees with a committed number, and any figure that cannot be built from the sources named.
Report either as a blocker.
