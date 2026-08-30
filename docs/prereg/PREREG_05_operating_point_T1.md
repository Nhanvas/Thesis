# PRE-REGISTRATION 05 — VAL-derived operating points (Phase-B · T1)

**Status:** COMMITTED before any test-set selection. D4 is Boti-locked (pure technical decision);
cô ratification pending only for the *reporting framing* (D1–D3), not for this derivation rule.
**Author role:** research director (proposes rule); Boti = final decision-maker (executes).
**Scorer (fixed):** SzCORE any-overlap event score via `timescoring`. Every sensitivity, precision,
F1 and FP/day below is the SzCORE event number. No new metric is introduced.
**Authority:** This SUPPLEMENTS `RESULTS_OF_RECORD.md` §0. The two operating points defined here are
ADDED alongside §0; they do NOT replace the §0 balanced (0.632/38.6) or high-sens (0.776/72.7) points.

---

## 0. What this pre-registration fixes (and why it exists)

Phase-B diagnosis (§3.1 of `PHASE_B_OPTIMIZATION_PLAN.md`) established **Cause A — operating-point
placement**: the §0 headline precision (~0.10) is measured at ~38.6 FP/day, whereas SzCORE-convention
event-level SOTA is reported at 1.3–14 FP/day. We have been reporting the wrong point on our own
Pareto curve. T1 corrects this **for free** (no retraining, no weight change, no algorithm change) by
deriving an F1-oriented operating point on **VAL only** and applying it to test **once**.

The mag80/pen5 cell named in §3.1 as "F1-optimal" was found by **inspecting test** — that is diagnosis
only and is NOT reportable. This document commits the *legitimate* VAL-derived selection rule **before**
the test grid is touched, so the reported number is test-clean.

**This is a pure decision-layer change.** Unchanged: ensemble weights (equal 1/3,1/3,1/3),
`cpd_pipeline_v14.py`, `ensemble_recipe.py`, seed 42, the scorer. Only the reported (mag,pen) changes.

---

## 1. Data

- **Derivation set (VAL):** chb10, chb11, chb22 — the `VAL_SUBJS` in `retrain_io.py` (single source).
  Grid: `results/retrain_v3p1/val/final_eval_seed42.csv` — verified 3 subjects × 8 mag × 6 pen = 144 rows,
  columns `seed,subject,mag_pct,pen_mult,tp,fp,n_seizures,n_inter_h,sensitivity,precision,fp_per_day,window_auroc`.
- **Test set (touched once):** chb03,06,13,14,15,16,17,18 — grid `results/retrain_v3p1/final_eval_seed42.csv`
  (8 × 8 × 6 = 384 rows). Harness sanity-checked: pooling reproduces §0 exactly
  (mag70/pen0.5 → sens 0.632, FP/day 38.6; mag55/pen0.3 → sens 0.776, FP/day 72.7).
- **Grid axes:** mag_pct ∈ {40,50,55,60,65,70,75,80}; pen_mult ∈ {0.3,0.5,1,2,5,10}.

---

## 2. Pooling definition (identical for VAL and test)

For each (mag,pen) cell, pool across the split's subjects:

    TP = Σ tp,  FP = Σ fp,  N = Σ n_seizures,  H = Σ n_inter_h
    sensitivity = TP / N
    precision   = TP / (TP + FP)          (0 if TP+FP = 0)
    F1          = 2·P·S / (P + S)         (0 if P+S = 0)
    FP/day      = FP / H · 24

This is the SHARED (held-out) pooled convention used for the §0 primary points.

---

## 3. Selection rule (COMMITTED — deterministic, computed on VAL only)

**OP-F1 · F1-optimal (VAL):**
`argmax` pooled F1 over the 48 VAL cells.
Tie-break order: (1) higher pooled sensitivity, (2) lower pooled FP/day, (3) lower mag_pct, (4) lower pen_mult.
*(Note: the pooled-F1 maximum is provably attained on the sensitivity/FP Pareto frontier, so no separate
frontier restriction is needed.)*

**OP-5 · fixed ~5 FP/day budget (VAL):**
Among VAL cells with pooled FP/day ≤ 5.0, `argmax` pooled sensitivity (SzCORE fixed-budget convention).
Tie-break order: (1) higher pooled F1, (2) lower FP/day, (3) lower mag_pct, (4) lower pen_mult.
**Fallback** (only if no VAL cell has FP/day ≤ 5.0): select the cell with the smallest FP/day > 5.0
(closest to 5 from above) and flag `fallback=True` in the output. The branch taken is reported.

Both selected (mag,pen) pairs are frozen at this step and **printed before the test grid is loaded**.

---

## 4. Application to test (ONE shot) and reporting

Apply the two frozen (mag,pen) pairs to the 8 test subjects, pooled, exactly once. Report:
- pooled sensitivity + **Wilson 95% CI**, precision + Wilson 95% CI, F1, FP/day + **Poisson (Garwood) 95% CI**
  (identical CI machinery to `stat_validation.py`, i.e. consistent with §0);
- per-subject breakdown at each selected point;
- the **full test Pareto frontier** (deliverable curve).

No point is re-selected on test under any outcome.

---

## 5. Falsification criteria (stated before results)

**H1 (primary — OP-F1 transfers):** the VAL-derived OP-F1 yields **test pooled event F1 ≥ 0.30**
(up from §0 balanced F1 = 0.168).
- **Confirmed ⇒** Cause-A diagnosis validated; Phase-0 free win banked; the point is reportable and
  added alongside §0.
- **Falsified** (test F1 < 0.30, OR the VAL cell lands far off the test F1 ridge): report the number
  **as-is**, do NOT re-select, and open a VAL→test operating-point *transfer* investigation. A falsified
  H1 is reported as a falsified prediction (operating-point transfer failure), not reframed.

**H2 (secondary — OP-5 is a usable low-FP point):** OP-5 yields a reportable SzCORE-convention point
(test sensitivity at ~5 FP/day). Descriptive; no pass/fail gate, reported for the Pareto/SzCORE table.

**Transfer sanity (descriptive):** record whether the VAL-selected (mag,pen) sits on the pen=5 ridge
that §3.1 observed on test (mag 65–80 / pen 5). Agreement corroborates the "broad stable ridge"
claim; disagreement is itself an honest finding about VAL→test operating-point shift.

---

## 6. Integrity guardrails honored
- Derivation on VAL only; test touched once, as-is (Guardrail §8.1).
- Rule + falsification committed before test selection (Guardrail §8.2).
- Harness reproduces §0 before use (Guardrail §8.4).
- Weights untouched (equal, `ensemble_recipe.py`), algorithm untouched (`cpd_pipeline_v14.py`) (§8.5).
- Result ADDED alongside §0 with provenance; nothing in §0 is overwritten (§12).

*End PREREG_05. Next: run `t1_derive_operating_point.py` (VAL-derive → print frozen points → one-shot test).*
