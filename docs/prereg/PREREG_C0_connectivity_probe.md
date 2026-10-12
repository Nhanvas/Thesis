# PREREG_C0 — chb06 diagnosis + directed nonlinear connectivity feasibility (CCM vs TE vs symmetric)
**Status:** binding pre-registration. Cheap probe that gates the whole Phase-C connectivity thread AND
diagnoses chb06. Supervisor-motivated (CCM/EDM slides). NO TEST exposure — VAL/diagnostic subjects only.

## Motivation
rlg is the locked optimized baseline. Phase C reopens the REPRESENTATION frontier (features / GAE /
connectivity), previously under-explored. chb06 window AUROC ~0.44 is **below chance** = the symmetric
linear connectivity (wPLI/AEC) anomaly is INVERTED, yet seizures are real → classic "causation without
correlation" (Sugihara). Directed nonlinear connectivity (CCM / transfer entropy) is theory-matched to
exactly this failure. Both wPLI and AEC are symmetric (no direction); CCM/TE are directed + nonlinear.

## Subjects
chb06 (the failing case) + chb03 (good-signal control, expect all methods high). Diagnostic only — NOT
the 8-subject TEST set for headline claims. (chb06 IS in TEST, but here it is used ONLY for a
mechanism/feasibility diagnosis on connectivity, no operating-point selection, no metric that feeds the
locked rlg comparison — this is representation R&D, and any resulting pipeline gets its own VAL-gated,
one-shot evaluation later.)

## Hypotheses + criteria (stated before running)
- **H1 CONVERGENCE (kill switch for CCM):** CCM cross-map skill INCREASES with library size L within a
  4 s / 1024-sample window. PASS = monotone-ish rise then plateau. **FAIL → CCM invalid at 4 s** →
  either drop CCM or run connectivity on a longer window for that branch only.
- **H2 SEPARATION:** on chb06, a DIRECTED method (CCM or TE) gives ictal-vs-interictal anomaly AUROC
  **> 0.5** (above chance) and materially **> the symmetric baseline** (which reproduces the ~0.44
  failure). Control chb03 stays high for all methods (sanity).
- **Falsification:** if H2 fails for BOTH CCM and TE on chb06 (directed ≤ symmetric, still ≤0.5), then
  directed connectivity does NOT recover chb06 → chb06 is confirmed signal/representation-limited beyond
  connectivity → drop the connectivity thread, report as a clean negative, keep rlg.

## Decision table
| convergence | separation (chb06) | action |
|---|---|---|
| CCM converges | CCM or TE AUROC > 0.5 & > sym | **PURSUE directed connectivity** (C4): build directed graph, directed encoder |
| CCM fails | TE AUROC > 0.5 & > sym | pursue **TE** (cheaper, no convergence dependency); shelve CCM or move to longer window |
| either | both ≤ sym / ≤0.5 | **DROP** thread; chb06 confirmed limited; keep rlg |

## Method (self-contained, validated by --smoke on synthetic driver systems)
Minimal simplex-CCM + binned-TE (numpy); symmetric baseline = |corr| (proxy for wPLI/AEC, both
symmetric). Per-window 18×18 connectivity → LedoitWolf-Mahalanobis anomaly to interictal manifold →
AUROC. Standard CHB-MIT 18-ch bipolar montage. Script: `src/phaseC/connectivity_probe.py`.

## Cost / integrity
CPU (Cursor), ~minutes, no GPU. Uses raw EDF (chb06/chb03) + committed summaries. No operating-point
selection, no TEST headline touched. Result logged whatever the outcome (negative = contribution).
