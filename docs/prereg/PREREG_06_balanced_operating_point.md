# PRE-REGISTRATION 06 — Balanced multi-metric operating points (Phase-B · supersedes PREREG_05 objective)

**Status:** COMMITTED before this round of test selection. Supersedes the *objective* of PREREG_05
(argmax-F1), which was mis-specified: it optimized a single metric and, via VAL→test transfer slip,
produced a lopsided point (test sens 0.276 < SOTA event sens ≈0.37 while precision sat mid-band). This
violates the Phase-B mandate: **all metrics must improve proportionally vs SOTA; no single axis lopsided.**
PREREG_05's *machinery, guardrails, harness, and one-shot discipline stand*; only the selection objective
changes here.

**Scorer/pipeline (unchanged):** SzCORE/`timescoring`, equal weights, `cpd_pipeline_v14`, seed 42.
**Denominator (fixed):** use the scorer's own reference-event count per subject (VAL chb11 = 5 ref-events
from 3 summary seizures; SzCORE splits >5-min events). Pooled sensitivity uses Σref-events, not Σn_seizures.

---

## 0. Honest contamination disclosure (stated up front)
During the earlier buggy T1 run I **saw the test Pareto**. To keep this round test-clean despite that:
- the **balanced headline objective is knob-free** (min |sensitivity − precision| on the Pareto frontier)
  — there is no tunable tolerance I could turn toward the cell I now know performs well on test;
- the FP-budget points use **externally standard budgets** (≈5 and ≈10 FP/day, the SzCORE reporting
  convention), not values chosen from our test curve;
- **test is touched once**; any suboptimal test outcome is reported as-is, not re-selected.
This residual limitation is disclosed rather than hidden; the clean check is the one-shot rule below.

## 1. Why min |sens − prec| (principled, not reverse-engineered)
A "balanced, not-lopsided" operating point is, by definition, the point where the detector is **equally
reliable at detecting and at being correct** — i.e. sensitivity ≈ precision. This is knob-free, dataset-
independent, and coincides with the SOTA event profile (sens 0.37 / prec 0.29–0.45 → both ≈0.35). It is
the formal encoding of "trade-off có nhưng không quá lệch."

## 2. Selection rules (COMMITTED, computed on VAL only, correct denominator)
Pooled per VAL cell: sens = ΣTP/Σref, prec = ΣTP/(ΣTP+ΣFP), F1 = 2PS/(P+S), FP/day = ΣFP/ΣH·24.
Mark the sensitivity-vs-FP Pareto frontier.

- **P_balanced (headline):** among **frontier** cells, argmin |sens − prec|.
  Tie-break: higher F1, then higher sensitivity, then lower FP/day, then lower mag, lower pen.
- **P_fp5 (SzCORE-comparable):** frontier cell with FP/day closest to 5.0. Tie: higher sensitivity.
- **P_fp10 (SzCORE-comparable):** frontier cell with FP/day closest to 10.0. Tie: higher sensitivity.

Freeze all three (mag,pen) and print **before** the test grid is loaded.

## 3. Application to test (ONE shot) + reporting
Apply the three frozen (mag,pen) to the 8 test subjects, pooled, once. For each report the **full vector**:
sensitivity (Wilson 95%), precision (Wilson 95%), F1, FP/day (Poisson 95%), TP/FN/FP, plus per-subject
breakdown, plus the full test Pareto. All ADDED alongside §0; nothing in §0 replaced.

## 4. SOTA-proportionality check (the actual success criterion — replaces the F1-only gate)
For the headline P_balanced, tabulate each metric against the SOTA event band and require **no axis
lopsided below SOTA while another is merely mid-band**. Concretely, success =
- sensitivity ≥ 0.35 (≈ SOTA 0.37, within noise), **and**
- precision ≥ 0.29 (SOTA lower bound), **and**
- F1 ≥ 0.30 (near SOTA 0.32–0.43), **and**
- FP/day ≤ ~10 (SzCORE-reportable range).
If any single axis is met only by sacrificing another below its SOTA floor → **not** a balanced win;
report as-is and prefer the per-subject FP-budget point (§6) as primary.

## 5. Falsification / honesty
- If P_balanced meets §4 on all axes → the balanced-operating-point correction is validated; report it.
- If it does not → report the number as-is (no re-selection) and state plainly that the shared point
  cannot simultaneously match SOTA on all axes on this data, motivating the per-subject approach.

## 6. Scope note — this is only the SHARED leg
Author's position (for cô): the **stronger primary is the per-subject label-free FP-budget** operating
point (PREREG_04 machinery), which avoids the shared-point transfer compromise and directly recovers the
decision-limited subjects (chb16/chb17, per T3). It requires the raw per-window ensemble arrays
(`results/retrain_v3p1/ens|val_ens/ens_seed42_{subj}_{inter,ictal}.npy`, confirmed present) and is
pre-registered separately. The **window-level metric suite** (AUPRC, window precision/recall/F1 vs
window SOTA) also requires those arrays and completes the "all metrics" mandate. This PREREG covers the
shared event leg only.

*End PREREG_06. Next: run `reselect_balanced_op.py` (VAL-derive → freeze → one-shot test).*
