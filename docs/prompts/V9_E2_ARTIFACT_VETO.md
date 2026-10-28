# V9-E2 — Paired comparison + competing-anomaly (artifact) veto (Claude Code, laptop)

Estimated runtime: Part 0 ≈ 15 min; Part A 2–4 h (estimated, not measured). One patient at a time, single worker, as in V9_T4. Smoke first and report the projected total.

## Part 0 — fixes and paired statistics on the existing V9_E1b outputs (no new model)
1. In `results/v9_e1b/`, the duration-bin table counts G and F over **4 seeds** (e.g. 26/96) but B4 over one (7/24). Re-print every duration-bin table at **seed 42 only** for all arms (B4 is deterministic).
2. Paired patient bootstrap (B = 10,000, same resampled patients for both arms) of the **difference** in per-patient-mean sensitivity, at matched FP/day 20 / 27.5 / 44 on the system-stage curve, for B4 − G and F − G, per set (development, CHB-MIT test, chb24 excluded as n = 1, Siena 14). Report mean difference, 95% CI, share of resamples > 0.
3. Same paired bootstrap for per-patient-mean F1 at each arm's own calibrated point.
Output `results/v9_e2/paired/`.

## Part A — veto of competing anomalies (pre-registered)
Hypothesis: many top false alarms are muscle/movement/electrode events (V9_T3, V9_T4, V9_C1: 80–89% of false alarms have high-amplitude channels; top channel FP1-F7; the worst ones are dense fast activity on all 18 channels). A post-hoc veto on events can remove part of them while keeping most true detections.

Candidate event features (computed on the filtered 18-channel signal of the event, label-free; reuse `filter_window_mem` from `src/raw_eeg_view.py` / the X1 loader for external sets):
- f1 high-frequency share: median over channels of power 30–60 Hz / power 1–60 Hz;
- f2 spatial extent: share of channels with median |z| > 5 (label-free per-patient statistics);
- f3 frontal-polar dominance: power in FP1-F7, FP1-F3, FP2-F4, FP2-F8 / power of all channels;
- f4 single-channel dominance: max channel power / median channel power;
- f5 event duration.

Selection protocol (fixed now; development patients only):
1. For each arm (G, B4, F) at its own calibrated point, collect every event on development patients, labelled TP or FP by the scorer.
2. Per feature, AUROC (TP vs FP) on development. Pick the **single** feature with the highest AUROC averaged over the three arms, and its direction.
3. Threshold = the most aggressive value that keeps **≥ 95% of development true detections** for that arm (one threshold per arm).
4. Apply once to CHB-MIT test, chb24, Siena 14. Vetoed events are deleted (no refilling of the budget).
Report per set and arm, before and after veto: tp/ref, FP, sensitivity, precision, F1, FP/day (pooled and per-patient mean), 4 seeds for G and F; which seizures were lost (subject, duration); the AUROC table on development; and the same AUROCs measured on test/Siena (descriptive only, not used).
Disclose in the summary: the veto threshold uses development labels (a validation-set hyperparameter), the model itself never sees seizures.

## Rules
Read-only on frozen scripts and committed results. New code `src/v9_e2_veto.py`; outputs `results/v9_e2/`. Commit only these paths, plus — now that V9_T4 is finished — `src/v9_anatomy.py`, `src/v9_eeg_samples.py` and `results/v9_anatomy/siena14/` (explicitly staged). Do not touch `web_demo/`.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_E2_REPORT.md`.
