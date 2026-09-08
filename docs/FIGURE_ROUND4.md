# Figure Work — Round 4

Read this file in full before changing anything. `docs/VERIFIED_NUMBERS.md` remains the authority
for every number. `docs/FIGURE_BRIEF_ROUND2.md` still holds the standing rules — palette, PNG only,
no confidence intervals, no figure titles inside the image, no internal shorthand in a label.

**Order:** §1 and §2 are measurements and questions; do them first because §3 depends on §1 and a
whole subsection of the report depends on §2. Then §3, §4, §5.

**Report every item as applied or not applied**, with file and line. When several items touch one
file, none is skipped because another one in that file needed no change.

---

# 1 · Timeline composition across all eight held-out subjects

The chb13 investigation established that the committed background score array runs out partway
through the reconstructed timeline and every position after that receives a bootstrap-resampled
score. For chb13 the array holds 12,452 entries against 25,224 eligible positions, exhausting at
41.9 % of the recording.

This is not a chb13 property. It has to be quantified for all eight held-out subjects, because the
false-alarm rate of this study is measured on those timelines and the report must state what
fraction of each is substituted rather than measured.

For each of chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18, emit to
`results/diagnostics/timeline_composition.csv`:

| Column | Meaning |
|---|---|
| `subject` | |
| `eligible_windows` | non-ictal, outside the 4 h post-seizure buffer, from the summary files |
| `committed_inter_windows` | `len(ens_seed42_{subj}_inter.npy)` |
| `dropped_windows` | eligible minus committed |
| `dropped_fraction` | |
| `exhaustion_point_fraction` | where in the reconstructed timeline the real scores run out |
| `substituted_fraction` | share of timeline positions carrying a bootstrap-resampled score |
| `ictal_windows` | for reference |

Cross-check `committed_inter_windows` against `data/processed/{subj}_interictal.npy` and report any
subject where the two disagree.

Print the eight-subject mean and range of `substituted_fraction`. Those two numbers go into the
report's limitations section, so they must be read from this file and not from chb13 alone.

**Do not change any committed result.** This measurement characterises a property of the evaluation
that was already in place when the results were produced. It is reported, not repaired.

---

# 2 · Provenance of the channel annotation — one question, blocking

`table_A2_channel_annotation.csv` gives `label_source` as
`AI-DRAFT (attribution_v5 reader pass, verbatim)` on all 76 rows. The report will state plainly that
the annotation was generated automatically and has not been clinically reviewed. Before that
sentence can be written, one thing has to be established:

**What did the reader pass actually read?**

Find the code or specification that produced `results/attribution_v5/labels/labels_*_FINAL.csv` and
`ictal_channels_DRAFT.csv`, and answer:

1. Did it operate on the EEG signal — the recordings, the processed windows, the features?
2. Or did it operate on something else — the recording summary files, patient metadata, published
   descriptions of each patient's focus, or the model's own attribution output?
3. What was its input, exactly, and what did it emit?

Report what the code shows. If the generating code is not in the repository, say so rather than
inferring from the output.

The difference decides the wording of an entire subsection. An annotation derived independently from
the signal is a weak but real reference. An annotation derived from patient metadata or from the
model's own output is circular, and the comparison against it would have to be withdrawn rather
than qualified. Do not guess which it is.

---

# 3 · Fig 2.10, Fig 3.4, Fig 3.10 — build by recomputation

**Approved deviation.** These three figures recompute anomaly scores on a continuous recording
rather than reading the committed score arrays. The committed arrays cannot support a time axis:
they are segment-ordered, half their positions are bootstrap-substituted, and the surviving real
scores drift by the number of rejected windows. A figure drawn from them would present synthesised
values as measurement.

The standing rule that figures read committed results and never recompute exists so that a figure
cannot disagree with the table it illustrates. These three illustrate no table. The deviation is
recorded here, gated in §3.3, and stated in the captions.

## 3.1 What is fixed and what is recomputed

**Recomputed:** the anomaly scores, on every window of one continuous recording, with no window
dropped.

**Taken from committed files, never refitted on the chosen recording:**

- the checkpoint `data/models_retrain/gae_joint_seed42.pt`;
- the per-subject, per-channel z-score statistics from `data/processed/chb13_stats.json`;
- the covariance estimate for the latent readout — load it if it is committed; if it is not, fit it
  on the committed `data/processed/chb13_interictal.npy` array, which is the same data the study
  used, and say which of the two you did;
- the per-branch median and median absolute deviation for the robust standardisation, on the same
  basis;
- equal weights, one third each;
- the change-point stage: `cpd_pipeline_v14.detect_events` at the reported operating point, locked
  defaults, no re-implementation of the smoother or the penalty.

**Dropped for these three figures only:** the ±5 SD artifact rejection. Keeping every window is the
entire point — it is what gives `t_seconds = window_index × 4` and makes the time axis real.

**Forbidden:** `szcore_eval.build_timeline_masked()` anywhere in these three scripts. That function
is what produces the substituted timeline. If a script imports it, the script is wrong.

## 3.2 Choosing the recording

Any chb13 file containing at least one seizure. Prefer one that contains several — from the earlier
per-file audit, `chb13_62.edf` holds three and `chb13_55.edf` holds two.

Detections are recomputed, so the earlier finding that no seizure-containing file produced a false
positive does not carry over: that finding was an artefact of the substituted timeline. Recompute
and look again.

If the chosen file yields at least one detected seizure **and** at least one false positive, all
three figures use it. If it yields no false positive, Fig 3.10 uses a second chb13 file, and **both
captions name both files and say why two were needed**. Report which case occurred.

Write the outcome into `docs/RUNNING_EXAMPLE.md`, replacing the current contents. The current file
states that the zero-false-positive pattern is "not a bug" and "a real structural property of the
chb13 detections" — that conclusion was disproved by the exhaustion measurement and must not remain
in a project document.

## 3.3 Acceptance gate — state the result before drawing anything

Ictal windows are never artifact-rejected, so the committed ictal array is complete and its rows
follow seizure order. That gives an independent check on the recomputation.

Align the recomputed scores at the chosen recording's seizure windows against the corresponding
rows of `results/phaseB/tier2/ens_test_tf/rlg/ens_seed42_chb13_ictal.npy`, and report **Pearson
correlation per seizure and pooled**.

**Gate: pooled correlation ≥ 0.99.** Below that, stop and report. Do not adjust the recomputation to
pass, and do not draw the figures anyway with a caveat. A correlation below the gate means the
recomputation is not reproducing the study's own pipeline, and that is a finding about the pipeline
worth more than three figures.

Report the correlation whatever it is, including if it passes.

## 3.4 The three figures

Standing rules apply: palette, PNG, no title inside the image, no internal shorthand in any label —
write "at the reported operating point", never the grid notation.

**Fig 2.10 — change point detection on an anomaly score series.** The fused score against time in
minutes; detected change points as vertical lines; the annotated seizure shaded. Print the number of
change points and the seizure onset and offset in seconds.

**Fig 3.4 — detection output on one full recording.** Stacked panels, shared time axis: the three
component scores, the fused score, detected intervals shaded in the detected-interval colour, the
annotated seizure in the ictal colour. Print the detected interval boundaries in seconds.

**Fig 3.10 — a false positive with the concurrent EEG.** Two stacked panels, shared time axis: the
fused score above, the raw signal below, six channels with a labelled amplitude scale. Centre on one
false-positive interval with about a minute of context each side; shade that interval. Print the
boundaries and confirm from the annotation that no seizure overlaps them.

## 3.5 Captions

Each of the three carries, in the caption text you write into the console output for me to use:
the recording name, and one sentence stating that the scores were recomputed on the continuous
recording with every window retained, using the study's fitted parameters, and that they are not the
source of any reported number.

---

# 4 · Table formatting

`results/report_tables/table_3_4_event_level_per_patient.csv` writes `1.0`, `0.75`, `0.9` where the
report's convention is three decimals for sensitivity, precision, F1 and discrimination, and one
decimal for false alarms per day. Fix the formatting in `emit_tables.py` and regenerate. `undefined`
stays as it is.

Rename `tableA7_top_channels.csv` to `table_A7_top_channels.csv` so all five files share one scheme.
Use `git mv` and update whatever writes it.

---

# 5 · Finish the figure directory consolidation

`figures/` still has six subdirectories — `alternatives/`, `event_level/`, `graph/`,
`reconstruction/`, `weights/`, `window_level/` — holding Fig 2.8, 2.9, 3.1 through 3.7 and 3.9 under
working names, while eleven figures sit at the root under their exhibit numbers. A writer looking
for Figure 3.6 cannot find it.

Move every remaining exhibit to the root of `figures/` under `figNN_MM_slug.png`, matching the
existing names. Rename `raw_vs_preprocessed.png` to `fig2_3_raw_vs_preprocessed.png`.

Use `git mv`, and in the **same commit** update the output path inside every generating script so a
regeneration cannot recreate the old path beside the new one. `figures/archive/` stays as it is.

Do not change any figure's contents. Then list anything left in `figures/` that does not begin with
its exhibit number, and report it rather than renaming it unasked.

---

# 6 · What to report back

Each item applied or not applied, with file and line. Then:

- the eight-subject mean and range of `substituted_fraction` from §1;
- the answer to §2, with the file the answer came from;
- the per-seizure and pooled correlation from §3.3, whether or not it passes;
- which recording was chosen, and whether one file or two were needed;
- confirmation that none of the three new scripts imports `build_timeline_masked`;
- `find figures -iname "*.pdf"` returning nothing, and every renamed file tracked by git.

Push back rather than accommodate on two things: any instruction here that disagrees with a
committed number, and any figure that cannot be built from the sources it names. Report either as a
blocker and stop. The last round's blocker report was the right call and produced the measurement
that changed the plan.
