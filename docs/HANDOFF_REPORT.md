# HANDOFF_REPORT — from the performance phase (closed 2026-10-07) to the report and the demo

Written 2026-10-07 at the close of stage P3. Every number below is in `docs/PERF_PHASE_RECORD.md` (rev Q,
sections 3, 6 and 9); on any conflict the record wins. Deadlines: report submission 15/10, defense 05–06/11.

## 1 · The final system (tag `p3-frozen`) — what Chapter 2 must describe

1. Preprocessing and graphs unchanged (CHB-MIT, 18 bipolar channels, 4-s windows, CAR → wPLI + AEC, top-k 20 %).
2. GAE v2 (node input 30 = adjacency row 18 + band powers 5 + 7 added features: log band power ×5, log line
   length, signed-log kurtosis; training-set z, clip ±4; 3,964 parameters; trained on clean training
   windows). Seeds 42, 1, 2, 3; headline seed 42.
3. Readout, per patient and label-free: per-channel LedoitWolf Mahalanobis distance of the 16-d node latent
   (fitted on all of the patient's windows) → per-channel robust-z → order statistics 6, 9, 12 of 18 and the
   channel mean → each minus its centred ±15-min running median inside each file (non-causal: post-hoc review)
   → patient percentiles → equal mean = **one ensemble anomaly score**.
4. Detection: moving average of 5 windows (20 s); threshold = the patient's own top-p_i of time, with
   **p_i = clip(q_i, 0.005, 0.02)**, q_i = share of the patient's smoothed member-mean robust-z above
   k = 4.0677 (k calibrated once on the 15 non-test patients). Contiguous runs, merge 90 s.
5. Localization: kernel CPD (ruptures KernelCPD, rbf, exactly 2 change points) on the unsmoothed score over
   each event ± 60 s; accepted when the inner segment is a bump, else the detector's boundaries.
Dropped from V1 and never in the final system: reconstruction and gamma-AEC readouts in the score, PELT as a
detector. Chapter 2 Table 5 must be rewritten. Goal 1 is quoted verbatim and qualified beside it.

## 2 · Results to report (continuous timeline, SzCORE scorer)

| set | system | pooled sens @ FP/day | subject-mean sens | onset / offset |
|---|---|---|---|---|
| non-test (15, 4 seeds) | final, after CPD | 0.670 @ 23.3 | 0.832 | — (non-test errors in record 9.7) |
| test, look #6 (clean) | P2 frozen | 0.342 (26/76) @ 22.2 | 0.498 | 8 / 20 s |
| test, look #7 (test-informed) | final (P3) | **0.487 (37/76) @ 27.5** | **0.577** | 12 / 24 s |

4-seed means and bootstrap intervals: record 9.8. Precision/F1 only from the scorer's counts.
**Presentation rule (fixed):** look #6 is the clean held-out evaluation; look #7 is the final system,
labelled test-informed, with its bootstrap interval and the statement that the gain is one patient (chb15,
0 → 11/20) at a budget cap that binds only on test. Report pooled and subject-mean side by side; the
official SzCORE aggregate is the subject-mean. Offline-protocol numbers (RoR) are never merged with these.

## 3 · Disclosures the report must carry

The 7 looks at the test set (record section 3); the test-informed design of P3 (record 9.2, 9.7b); about 40
gated decisions on the 15 non-test subjects (ledger); the non-test set over-predicts test about 2×; the
unsolved patients chb06, chb13, chb16 (record 9.8) and the untested Future Work hypotheses.

## 4 · Supervisor items (record section 7)

Label-free per-patient fitting under "unsupervised" (DynaSD / NDD as precedents, both preprints); the role of
CPD (onset localizer: error halved vs the detector; offset not improved); offline vs continuous protocols;
the disclosure of the test looks.

## 5 · Demo (Project 2)

The demo still runs V1 (application tier 0.211 @ 52.4). Rebuilding it for the final system needs: v2 GAE
inference, per-patient LedoitWolf fits on the whole recording, the non-causal ±15-min running median, the
per-patient budget with k = 4.0677, kernel CPD; CPU cost per patient to be measured. Author decision.

## 6 · Open document fixes (not performance)

SzCORE challenge numbers in `Thesis_Reference_Sheet.md` D5, `VERIFIED_NUMBERS.md` 7b.2 and
`PROJECT_STATUS.md` §7 (reviewer: v2 of the challenge paper differs; verify from the PDF); processing-time
figures (10.83 vs 21.9 s/h) to reconcile; `REPO_MAP.md` lacks E8 onward; chapters v4 describe V1.

## 7 · Code and results of the final system

`src/p2_scalars.py`, `e16_recording_baseline.py`, `e17b_latent_family.py`, `e18_cpd_localizer.py`,
`e22_test_oneshot.py`, `p3_levers.py`, `p3c_freeze.py`, `e23_test_look7.py`; results in
`results/p3c_freeze/` (non-test, `freeze.json`) and `results/e23_test_look7/` (look #7).
