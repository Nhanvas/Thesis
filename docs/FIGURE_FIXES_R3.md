# Figure Fixes — Round 3

Read this file in full before changing anything. It supersedes nothing: `docs/VERIFIED_NUMBERS.md`
remains the authority for every number, `docs/FIGURE_BRIEF_ROUND2.md` still holds the standing
rules and the per-figure specifications, and this file only records what came back from round two
and what is still open.

**Order of work.** §3 first — it is unfinished round-two work and three figures depend on it. Then
§1, then §2, then §4.

**Report every item as applied or not applied**, with the file and line. When several items touch
one file, none is skipped because another one in that file needed no change.

---

# 1 · Six figures came back close. Fix list.

## Fig 3.15 — conceptual error, fix this one first

The figure plots only the 36 seizures that carry a channel set. The 40 seizures annotated as
diffuse have no channel count and are therefore **absent from the plot entirely**. But the caption's
claim is about focal against generalized, and the generalized group is exactly the missing 40. As
drawn, the figure cannot show the result it is captioned with.

- Add a separate categorical position on the horizontal axis, to the right of 18 and visually
  detached from the numeric part, holding the diffuse group as a strip of points with its group
  mean marked. Mark the focal group mean as well.
- The two means are 0.9693 and 0.9594. A reader must be able to see that the generalized group
  sits **lower**, which is the wrong direction, which is the entire point of the figure.
- Integer ticks at 1, 2, 4, 8, 12, 18 only. Fractional channel counts are meaningless.
- State in the console output whether the real points are jittered and by how much.

## Fig 2.3 — two fixes

- Panel (c) spans twenty-one decades of vertical axis, nearly all of it empty, which leaves the
  60 Hz notch almost invisible. Clip the vertical range to about six decades around the data.
- Panels (a) and (b) carry no vertical scale, and their units differ — microvolts against z-score.
  Add a scale bar with its unit to each panel, or label the axis. A reader currently cannot tell
  that the two panels are on different scales, which is the one thing that panel pair must convey.

## Fig 2.2 — the overlay cannot be read

The two series are drawn overlaid with transparency, so it cannot be told whether the held-out set
is a subset of the 182 or a separate group. In at least one bin the held-out bar appears to exceed
the total, which is impossible and is an artefact of the overlay.

- Redraw as a **stacked** histogram: held-out subjects at the bottom, training and validation
  subjects above, summing to 182. The legend states both counts, 76 and 106.
- Clip the horizontal axis to the data range. It currently runs past 500 s when the maximum is
  205 s.
- Move the "23 of 76" annotation clear of the 4 s line.

## Fig 2.4 — four fixes

- Node labels in panel (d) are unreadable at print size. Place them outside the node circles, or
  enlarge the panel. Panel (d) is the payoff of the figure and is currently its least legible part.
- Panels (b) and (c) use different colormaps. Use **one** sequential colormap across (b), (c),
  Fig 1.2 and Fig 2.5, and add it to `palette.py` as a named constant so it cannot drift apart
  again.
- Panel (b)'s colorbar has no label. Name the quantity and its units.
- Panel (a) has no amplitude scale — same fix as Fig 2.3.

## Fig 2.5 — one real issue, two cosmetic

The densities printed in the panel titles are subject-level values from the diagnostic, but the
matrices displayed are a **single window**. Those are two different quantities, and a reader
counting the non-zero cells would not reproduce the printed number.

- Print the **displayed window's own** density in each panel title, and report both numbers to the
  console so the caption can state the subject-level value separately.
- If the two differ by more than 0.01 for the fixed-threshold rule, say so. That is worth knowing
  and belongs in the caption rather than being smoothed over.
- Cosmetic: one shared colorbar per row rather than two identical ones; print the density label
  once per row rather than twice.
- Node labels: same legibility fix as Fig 2.4.

## Fig 1.2 — one word

The colorbar label reads "unsparsified". Use "before sparsification". Otherwise finished.

## Fig 3.8 — internal notation is leaking into the report

The vertical axis label and the legend both contain `m50/p2.0`, which is this project's own
shorthand and appears nowhere in the thesis text. Replace with "at the reported operating point".
Otherwise finished — the chb06 treatment and the chb17 position are both correct and were reported
honestly.

---

# 2 · Naming and location pass

Four figures still carry their working names and sit in a subdirectory while every other figure
sits at the root of `figures/` under its exhibit number. A writer looking for Figure 3.13 cannot
find it. Fix both at once:

| Current | Becomes |
|---|---|
| `figures/attribution/attribution_fig1_synthetic.png` | `figures/fig3_11_attribution_synthetic.png` |
| `figures/attribution/attribution_fig2_seed_robustness.png` | `figures/fig3_12_attribution_seed_stability.png` |
| `figures/attribution/attribution_fig3_rank_heatmap.png` | `figures/fig3_13_attribution_rank_heatmap.png` |
| `figures/attribution/attribution_fig4_persubject_forest.png` | `figures/fig3_14_attribution_persubject_forest.png` |
| `figures/attribution/attribution_top3_channels.csv` | `results/report_tables/tableA7_top_channels.csv` |

Use `git mv`. In the **same commit**, update the output paths inside
`src/figures/attribution_figures.py` so that a regeneration does not recreate the old names beside
the new ones — that is exactly how two versions of one figure end up in a repository.

Then check the rest of `figures/` for any file that still does not begin with its exhibit number,
and report anything found rather than renaming it unasked.

Do not change the figures' contents. All four are finished and verified.

---

# 3 · Unfinished round-two work

## Task A — lock the running-example recording

This is the blocker for the three figures below and was not reported back. Restated:

The patient is **chb13**. Find one chb13 recording that, at the reported operating point, contains
**at least one correctly detected seizure** and **at least one false positive**. Print the
candidates with their counts, pick one, and write the chosen file name into
`docs/RUNNING_EXAMPLE.md` together with the counts that justified it. All three captions name that
file.

If no single recording satisfies both conditions, **say so and stop**. Do not relax a condition and
do not switch patient. That outcome is a finding about the system, not a failure of the task, and
it needs a decision rather than a workaround.

## Fig 2.10 — change point detection on an anomaly score series

The locked recording. Fused anomaly score against time in minutes; detected change points as
vertical lines; the annotated seizure shaded.

Use `cpd_pipeline_v14.detect_events` with its locked defaults — do not re-implement the smoother or
the penalty. Print the number of change points found and the seizure onset and offset in seconds.

Source: `results/phaseB/tier2/ens_test_tf/rlg/ens_seed42_chb13_*.npy`, time axis via
`szcore_eval.build_timeline_masked()`.

## Fig 3.4 — detection output on one full recording

The same recording. Stacked panels on a shared time axis: the three component scores, the fused
score, detected intervals shaded in the detected-interval colour, the annotated seizure shaded in
the ictal colour. Print the detected interval boundaries in seconds.

Sources: `results/phaseB/tier2/ens_test_tf/components/{zrecon,zlatent,zgamma}_chb13_*.npy` and the
fused array.

## Fig 3.10 — a false positive with the concurrent EEG

Two stacked panels on a shared time axis, the same recording: the fused score above, the raw signal
below, six channels. Centre the view on one false-positive interval with about a minute of context
on each side, and shade that interval. Print the interval boundaries and confirm from the
annotation that no seizure overlaps them.

## The time-axis trap, restated

The committed score arrays are ordered by segment and carry no index into recording time. A figure
with a time axis rebuilds that axis with `szcore_eval.build_timeline_masked()`, which reconstructs
it from the annotation file. That is legitimate here — this is offline scoring with the labels
available. It is forbidden only in the web application.

## Task D — emit four tables

`src/figures/emit_tables.py`, writing CSV to `results/report_tables/`. No values typed in.

**Table 3.4 — event performance per patient** at the reported operating point, from
`results/phaseB/tier2/rlg_test/final_eval_seed42.csv`: patient, seizures, sensitivity, precision,
F1, false alarms per day. Write chb06's F1 as the string `undefined`, not as 0 and not as `nan`.
Self-check against these values, printed earlier by `src/figures/plot_event_level.py`:

```
chb03 1.000 0.152 0.264 24.7      chb15 0.900 0.286 0.434 27.4
chb06 0.000 0.000 undef  19.4     chb16 0.200 0.105 0.138 21.5
chb13 0.750 0.220 0.340 23.4      chb17 1.000 0.115 0.207 26.4
chb14 0.375 0.049 0.087 53.6      chb18 0.833 0.091 0.164 33.8
```

**Table A.1 — corpus metadata for all subjects**, from `data/summaries/*.txt`: subject, set,
recordings, recorded hours, seizures, total seizure duration. Self-check the per-set totals against
`docs/VERIFIED_NUMBERS.md` Part 3 — 12 / 342 / 566.43 / 93, then 3 / 91 / 115.82 / 13, then
8 / 231 / 279.39 / 76.

**Table A.2 — channel annotation for every held-out seizure**, from
`results/attribution_v6/labels/ictal_channels_DRAFT.csv`: subject, seizure index, annotated
channels, and the `label_source` field **carried through verbatim**, all 76 rows. The provenance of
this annotation determines the wording of a whole subsection of the report, so the column must come
from the file rather than from anybody's recollection. After emitting, print the distinct values of
`label_source` and their counts.

**Table A.3 — the full parameter grid**, from the same final evaluation file: all rows, columns as
committed, a pass-through with a row-count assertion of 384 rows, 8 subjects, 48 cells each.

---

# 4 · What to report back

For each item above: applied or not applied, with the file and line.

Then, before calling anything done:

- print the values each figure plots and check them line by line against
  `docs/VERIFIED_NUMBERS.md`, stopping on any disagreement;
- confirm `find figures -iname "*.pdf"` returns nothing;
- confirm every new or renamed file is tracked by git and not matched by an ignore rule;
- print the chosen running-example recording and the two counts that justified it;
- print the distinct values of `label_source` from Table A.2 and their counts.

Two things to push back on rather than accommodate: any instruction here that disagrees with a
committed number, and any figure that cannot be built from the sources it names. Report either as
a blocker and stop.
