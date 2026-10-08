# HANDOFF_REPORT — report phase (rev 2, 2026-10-08)

Entry point for every report and demo session. Every number below is read from a committed result file;
on any conflict `docs/PERF_PHASE_RECORD.md` (rev R) wins. Rev 1 (2026-10-07) is superseded: it paired the
seed-42 look-#6 sensitivity with the 4-seed subject-mean (0.498); the seed-42 subject-mean is 0.508.

Deadlines: IELTS 09/10 · **report submission 15/10** · defense 05–06/11.

## 0 · State and order of work (author, 2026-10-08)

Performance work is closed (P1–P3, external validation X1). The supervisor reviewed the briefing on 08/10
and asked to write the report with the current numbers. The author decides; the supervisor reviews.

| step | content | status |
|---|---|---|
| 1 | project and repo sync (this file, record rev R, instructions, corrections, status) | done 08/10 |
| 2 | channel attribution of the final system (A5) | done 08/10 (section 3) |
| 3 | web demo rebuilt on the final system, application tier re-run | via Project 2, `docs/DEMO_REBUILD_BRIEF.md`; run in parallel with 4–6 |
| 4 | exhibit set v5 (every figure and table, its committed source file) | next |
| 5 | Chapters 1–5, front matter rewritten | after 4 |
| 6 | figures and tables generated from committed results only (rule 13) | parallel with 5 |
| 7 | checks: Grammarly, rubric, paper-review protocol, page count (≤ 50, measured) | last |

Proposed fallback (author to confirm): if the rebuilt demo has not completed its application run by the
evening of 12/10, the report presents the demo as a prototype running the earlier system and reports no
application-tier number for the final system.

## 1 · The final system (tag `p3-frozen`) — what Chapter 2 describes

1. Preprocessing and graphs unchanged: CHB-MIT, 18 bipolar channels, 0.5–60 Hz band-pass, 60 Hz notch,
   4-s non-overlapping windows at 256 Hz, per-subject z-score; per window CAR → wPLI + AEC → top-k 20 %.
2. GAE v2: node input 30 = adjacency row 18 + band powers 5 + 7 added features (log band power ×5,
   log line length, signed-log kurtosis; training-set z, clip ±4 → [0, 1]); decoder reconstructs 12;
   3,964 parameters; trained on clean training windows. Seeds 42, 1, 2, 3; **headline seed 42**.
3. Readout, per patient, label-free: per channel, LedoitWolf Mahalanobis distance of the 16-d node latent,
   fitted on all non-signal-loss windows of the patient → per-channel robust-z → order statistics 6, 9, 12
   of 18 and the channel mean → each minus its centred ±15-min running median inside each file
   (non-causal: post-hoc review, not a real-time alarm) → patient percentiles → equal mean =
   **one ensemble anomaly score**.
4. Detection: per-file centred moving average of 5 windows (20 s); threshold = the patient's own top-p_i
   of time, **p_i = clip(q_i, 0.005, 0.02)**, q_i = share of the patient's smoothed mean robust-z of the
   four members above k = 4.0677 (k calibrated once on the 15 non-test patients, seed 42, so that the
   median q_i = 0.005). Contiguous supra-threshold runs, merge gaps ≤ 90 s.
5. Localization: kernel CPD (ruptures KernelCPD, rbf, min_size 2, exactly 2 change points) on the
   unsmoothed score over each event ± 60 s inside the file; accepted when the inner segment spans ≥ 2
   windows and its mean is above both outer segments, else the detector's boundaries; events merged again.

Not in the final system: the reconstruction and gamma-AEC readouts, PELT. Goal 1 of the registration
form is quoted verbatim ("spatial-temporal features") and qualified beside it.

## 2 · Results (continuous timeline, SzCORE scorer; precision/F1 from the scorer's counts)

| set | system | seed 42 pooled | seed 42 subject-mean | 4 seeds pooled · subject-mean | onset / offset |
|---|---|---|---|---|---|
| non-test (15) | final, after CPD | — | — | 0.670 @ 23.25 · 0.832 | — |
| test, look #6 (clean) | P2 frozen | 26/76 = 0.342 @ 22.22, prec 0.092, F1 0.145 | 0.508 | 0.336 ± 0.008 @ 23.88 · 0.498 ± 0.010 | CPD 8 / 20 s (detector 28 / 16 s), n = 103 |
| test, look #7 (test-informed) | **final (P3)** | **37/76 = 0.487 @ 27.49**, prec 0.104, F1 0.172 | **0.577** | 0.477 ± 0.022 @ 29.15 · 0.567 ± 0.019 | CPD 12 / 24 s (detector 32 / 20 s; contiguous-run offset 16 s), n = 146 |

Sources: `results/p3c_freeze/SUMMARY.md`, `results/e22_test_oneshot/SUMMARY.md`, `results/e23_test_look7/SUMMARY.md`.

**Baselines on the same continuous timeline (test):** earlier system V1 + PELT 23/76 @ 73.3 FP/day (look #2,
same operating point as the offline headline) and 0.079 @ 19.2 (low-FA cell); V1 with the threshold
detector 2/76 @ 24.2; GAE v2 with the threshold detector (E9) 3/76 @ 24.1; earlier web application
0.211 @ 52.4.

**Uncertainty:** look #6, 4 seeds, patient bootstrap: pooled 0.336 [0.133, 0.670], subject-mean 0.498
[0.226, 0.770]. Look #7 − look #6 (4-seed means, B = 10,000): pooled +0.141 [0.000, 0.333], subject-mean
+0.070 [0.000, 0.201], FP/day +5.27 [+0.37, +13.60]. Seed SD is not uncertainty (rule 21).

**Presentation rule (fixed).** Look #6 is the clean held-out evaluation. Look #7 is the final system,
labelled test-informed, with its bootstrap interval and the statement that its gain is one patient
(chb15, 0 → 11/20) at a budget cap that binds only on test. Pooled and subject-mean side by side;
subject-mean is SzCORE's official aggregate. Per patient (seed 42, look #7): chb03 7/7, chb06 2/10,
chb13 1/12, chb14 6/8, chb15 11/20, chb16 2/10, chb17 3/3, chb18 5/6.

**External validation (clean, record 9.9; `results/x1_external/SUMMARY.md`).**

| set | seed 42 | 4 seeds | comparator on the same data (SzCORE benchmark, subject-mean) |
|---|---|---|---|
| chb24 (16 seizures, 21.3 h) | 14/16 = 0.875 @ 29.5, F1 0.500 | 0.828 ± 0.060 @ 28.4 | — |
| Siena (14 adults, 47 seizures) | 33/47 = 0.702 @ 44.0; subject-mean 0.748 | subject-mean 0.633 ± 0.079, prec 0.160, F1 0.226 @ 41.0 | DynaSD (only unsupervised entry) 0.664, prec 0.126, F1 0.170 @ 77.7 |

Caveats: our own scorer implementation and signal path, not run inside the benchmark; Siena FP/day above
40; PN06, PN07, PN16 above 70 FP/day; PN05 0/3.

**Reference, never part of the system:** a supervised feature classifier on the 15 non-test patients
(leave-one-patient-out) reached 0.702 @ 20.5 FP/day — what seizure labels buy (Discussion only).
**Review burden:** event time / recorded time 0.0162 on non-test (after CPD), 0.0215 on look #7 (seed 42).

## 3 · Channel attribution (`results/attribution_v7/` A4, `results/attribution_v8/` A5)

Same blind, supervisor-approved annotation (62 focal + 14 generalized test seizures), same method
(p95 of |robust-z| over the seizure, macro-AUROC over 62 focal seizures, L1 chance → L2 anatomical prior
→ L3 seizure-specific, Holm over L2/L3).

| readout | L1 macro-AUROC [95 % CI], p | L2 Δ vs prior (0.7387) [CI] | L3 T, p | without chb15 |
|---|---|---|---|---|
| A4: reconstruction anomaly of the earlier GAE | 0.5694 [0.5097, 0.6321], p 0.001 | −0.1694 [−0.2553, −0.0804] | +0.0064, p_holm 0.68 | 0.5011 |
| **A5: per-channel latent anomaly of the final system** | **0.5473 [0.4992, 0.5971], p 0.018** | **−0.1914 [−0.2618, −0.1182]** | −0.0017, p 0.53 | 0.4864 (p 0.71) |

A5 descriptive: seeds 1/2/3 0.543 / 0.588 / 0.545; mean aggregation 0.556; only chb15 is above chance
(0.675, p 0.001); D7 −0.075. Reading (spec 4.7, "L1 passes, L2 fails"): the channel ranking concentrates
on annotated channels only weakly, far below a fixed anatomical rule, with no seizure-specific
information. **Two different readouts give the same pre-registered negative**: the per-channel anomaly
ranking of this GAE is not a guide to where a reader sees the discharge. Framing: XAI concordance, not
localization, not SOZ. The demo panel shows the final readout as `Channel-level latent anomaly — Event N`,
neutral, with no localization claim.

## 4 · The offline protocol (author decision 2026-10-08)

Not a result: no table, no figure. One short paragraph (Methods, evaluation; or Discussion) says: an
earlier evaluation rebuilt the timeline from the annotations and filled the gaps with resampled windows
from which high-amplitude windows had been removed; on the continuous recording the same earlier system at
the same operating point fell from sensitivity 0.618 at 27.4 FP/day to 23/76 (0.303) at 73.3 FP/day; the
continuous timeline is therefore the protocol of record. Sources: `RESULTS_OF_RECORD_phaseB.md` (0.618 @
27.4) and `results/continuous_eval/` (23/76 @ 73.3). Never merge the two protocols in one number.

## 5 · Disclosures the report must carry

1. Looks at the test set: seven (offline evaluation; continuous re-evaluation of the earlier system; the
   earlier web application; an alarm-filter screen; the first retrained GAE; looks #6 and #7), plus one
   per-seizure read of test information before look #7. External validation is separate. The two channel
   attribution studies use the test channel annotation by design (no event metric).
2. Look #7 is test-informed: the budget cap 0.02 binds only for chb15 and for no non-test patient.
3. About 40 gated design decisions were taken on the 15 non-test patients; non-test over-predicts test
   about 2× (0.662 → 0.336 at look #6).
4. **Normalisation statistics.** The per-subject z-score statistics of the CHB-MIT pipeline (inherited
   from the earlier preprocessing, `stats.json`) are computed after excluding annotated seizure windows and
   the 4-h post-seizure buffer. The detection system itself uses no labels, but this normalisation step
   does, for every CHB-MIT subject including the test patients. The external validation and the web demo
   use label-free statistics (every 10th window of the whole recording). The size of the effect on CHB-MIT
   has not been measured (open item, section 9).
5. Unsolved patients and their mechanisms: chb06 (generalized seizures of 12–20 s, inverted readout),
   chb16 (seizures of 6–14 s, below the 4-s window with 20-s smoothing), chb13 (seizures under the
   patient's own high-amplitude states). Future-work hypotheses are untested.
6. Low precision (≈ 0.1) at ≈ 25–30 FP/day; framing = post-hoc review triage.

## 6 · Writing rules (from the instructions)

No process in the report: no stage, phase, lever, experiment or look numbers, no tag or repository names,
no internal labels (L1/L2/L3, tier, A4/A5). Translate internal names: "per-patient alarm budget" (L2f),
"drift correction" (E16e), "spatial-scale ensemble" (E17b), "clean held-out evaluation" (look #6), "final
evaluation, test-informed" (look #7), "external validation" (X1), "earlier system" (V1). Captions are short
titles; figures and tables numbered consecutively; "Section", not "§"; numeric citations [n]; no
appendix; body ≤ 50 pages measured by building the document.

## 7 · Literature leads (NOT verified; check the PDF before citing — account `norn`)

- Problem framing: Karpov et al. 2023 (artifacts and seizures are both rare high-amplitude peaks);
  Tanaka et al., ICASSP 2024 (two-stage anomaly screening + artifact separation); Ingolfsson et al. 2024
  (artifact detector trained on TUAR cut false alarms).
- Unsupervised / adaptation: DynaSD (Ojemann et al., medRxiv preprint 2026; benchmark entry verified from
  the SzCORE repository); NeuroAdapt-Bench 2026; Tress et al. 2021.
- Protocol row (computed from the seed-42 per-patient table): a 2026 Frontiers in Neuroinformatics paper
  excluded chb06 and chb16 as too short for 4-s windows; under that exclusion look #7 is 33/56 = 0.589 and
  look #6 22/56 = 0.393 (FP/day not computed). Mirzaei & Singh (ISBI 2025) excluded chb06/12/13/14/16/24
  with seizure-tuned thresholds. Such rows only beside the full result.
- Onset/offset latency: Shoeb & Guttag ICML 2010; "ScoreNet" (conflicting venues/values in the leads);
  IRBM 2019; UPCON 2019 — all supervised, 1–2 s resolution.
- Sci Rep 2024 gives a chb06 mean seizure duration of 153.6 s, inconsistent with the summary files (≈ 15 s).

## 8 · Code and results of the final system

Code: `src/p2_scalars.py`, `e16_recording_baseline.py`, `e17b_latent_family.py`, `e18_cpd_localizer.py`,
`e22_test_oneshot.py`, `p3_levers.py`, `p3c_freeze.py` (`results/p3c_freeze/freeze.json`),
`e23_test_look7.py`, `x1_external.py`, `attribution_v8.py`, `p2_test_dump.py`; models
`data/models_v2/` (identity in `PROVENANCE_V2.md`). Results: `results/p3c_freeze/`, `e22_test_oneshot/`,
`e23_test_look7/`, `x1_external/`, `attribution_v8/`, `continuous_eval/`, ledger `results/p2_ledger.csv`
(its `verdict` column is the step's gate outcome, not the final selection; record 10.3).

## 9 · Open items (not performance)

- Measure the normalisation-statistics effect (section 5.4): per-channel mean/SD of `stats.json` vs
  label-free statistics for the 8 test patients (cache-free, minutes). Descriptive only; no re-scoring.
- SzCORE challenge numbers in `Thesis_Reference_Sheet.md` D5, `VERIFIED_NUMBERS.md` 7b.2: verify from PDF.
- Processing time of the final system: measured on the rebuilt demo (10.83 s/h belongs to the earlier system).
- Stale for the report: Chapters v4, `EXHIBIT_SET_v4.md`, `CAPTIONS.md`, `ATTRIBUTION_REPORT_PACK.md`
  (A5 missing), `REPO_MAP.md` (no performance-phase paths), `PROJECT2_SETUP.md` 9.2(B).
