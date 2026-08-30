# PRE-REGISTRATION 08 — Window-metric suite threshold (Phase-B · W1)

**Status:** COMMITTED before touching test. Covers only the *thresholded* window metrics; the headline
window metrics (AUROC, AUPRC) are **threshold-free** and need no pre-registration.

## Scope
Complete the window-level half of the mandate, comparably to segment/window SOTA (which reports
AUROC + AUC-PR, e.g. CSBrain AUC-PR 0.516, CBraMod 0.369). Inputs: per-window ensemble scores
`ens_seed42_{subj}_{inter,ictal}.npy` (robust-z ensemble; higher = more anomalous), seed 42, equal weights.

## Metrics
- **Primary (threshold-free):** per-subject and **macro** AUROC + **AUPRC**, with **AUPRC lift = AUPRC /
  prevalence** (chance AUPRC = prevalence). Pooled (concatenated) reported as secondary with a scale caveat.
- **Secondary (thresholded):** window precision / recall / F1 at a single **VAL-derived** threshold.

## Committed threshold rule (no test-tuning)
Concatenate the VAL subjects' window scores+labels (chb10,chb11,chb22; inter=0, ictal=1). Sweep candidate
thresholds over the pooled-VAL score range; select **t\*** = the threshold maximizing **VAL window F1**
(tie → higher recall). Freeze t\* and apply it unchanged to every test subject; report per-subject and
macro window precision/recall/F1 at t\*. AUROC/AUPRC do not use t\*.

## Sanity gate
Macro AUROC recomputed from the arrays must reproduce §0's window macro-AUROC 0.775 (±0.01), else the
array/scoring path is inconsistent — stop and investigate.

## Falsification / honesty
Report AUPRC as-is even if low; for imbalanced windows AUPRC near prevalence = weak, well above = strong.
No metric is dropped for being unflattering.

*End PREREG_08. Runs inside `window_metric_suite.py`.*
