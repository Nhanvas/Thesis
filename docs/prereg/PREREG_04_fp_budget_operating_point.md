# PRE-REGISTRATION 04 — Per-subject false-alarm-budget operating point (PHA 1.5, step a)

**Status:** DRAFT for author/supervisor sign-off. No selection/evaluation code runs on the 8 TEST
subjects until this is approved. English governance deliverable (thesis convention).
**Author role:** research director (proposes); Boti is final decision-maker (approves, executes).
**Scorer (fixed):** SzCORE event-based protocol via the `timescoring` library. Every sensitivity,
precision, F1 and false-positive-per-day (FP/day) number in this document — including the numbers used
for *calibration* — is the SzCORE any-overlap event score. No non-SzCORE metric is introduced.

---

## 0. Why this exists (motivation is a measured diagnostic, not a hunch)

The `window_event_gap` diagnostic on the rebuilt **deep seed-ensemble** (seed-tag 99) showed that the
loss of event sensitivity is **NOT primarily a signal-quality problem** — it is dominated by the
**single shared operating point** applied to all 8 subjects. At the pooled option-A balanced point
(mag40/pen2, pooled sensitivity 0.618, FP/day 41.6):

| subject | window AUROC | sens @ shared point | subject's own-best sens (anywhere) | gap | reading |
|---|---|---|---|---|---|
| chb16 | 0.827 | 0.100 | 0.600 | +0.500 | signal strong, shared point strangles it |
| chb06 | 0.442 | 0.200 | 0.500 | +0.300 | signal-limited (chb06 inverted connectivity) |
| chb13 | 0.811 | 0.667 | 0.917 | +0.250 | signal strong, operating-point cost |
| chb18 | 0.892 | 0.833 | 1.000 | +0.167 | operating-point cost |
| chb15 | 0.830 | 0.950 | 1.000 | +0.050 | near ceiling |
| chb03 | 0.912 | 1.000 | 1.000 | 0 | ceiling |
| chb14 | 0.545 | 0.375 | 0.375 | 0 | signal-limited |
| chb17 | 0.706 | 0.667 | 0.667 | 0 | ceiling (only 3 sz) |

**Pooled sensitivity if each subject used its own best point = 0.789 vs 0.618 shared** → the single
shared operating point costs **+0.171 sensitivity** at matched pooled FP/day. That 0.789 is an *oracle*
(it peeks at seizure labels) and is therefore **NOT attainable**; the question this pre-registration
answers is: *how much of it can a legitimate, label-free, per-subject FALSE-ALARM-RATE calibration
recover?*

Signal-limited subjects (chb06, chb14) are explicitly OUT of scope here — they need a better signal
(the separate SSL pre-registration, step b), not a better operating point.

---

## 1. The intervention (precise, and deliberately minimal)

Replace the **single shared** operating point with a **per-subject** operating point chosen to hit a
**pre-specified false-alarm budget B (FP/day)**, where the budget is fixed *before* looking at any test
sensitivity and equals the current headline FP levels:

- **Balanced:** B = 40 FP/day.
- **High-sensitivity:** B = 75 FP/day.

For each subject *s*, over the existing (mag_pct, pen_mult) grid already scored for the deep ensemble
(`final_eval_seed99.csv`), select the operating point by this rule, **fixed here, before running**:

```
choose (mag, pen) for subject s that MINIMISES | FP_per_day_SzCORE(s, mag, pen) − B |
tie-break (within 2 FP/day of the minimum):
   choose the point closest to the pooled-shared reference point (mag_ref, pen_ref),
   by |mag − mag_ref| + 10·|pen − pen_ref|      # deterministic, fixed reference
NEVER break ties using sensitivity / TP / any seizure-derived quantity.
```

- `FP_per_day_SzCORE(s, mag, pen)` is the SzCORE-scored FP/day on subject *s*'s **interictal
  (seizure-free) windows** — i.e. the false-alarm rate on baseline data. `(mag_ref, pen_ref)` is the
  pooled option-A point for the same budget (the current shared point).
- The **model is untouched** (same GAE/LSTM/gamma deep ensemble; no retraining; no per-subject
  training). Only the *decision threshold* is calibrated per subject.

### Why the selection is label-free with respect to seizures (the crux)
The selection quantity is FP/day **on interictal data**, which is the alarm rate on seizure-free
baseline. It does **not** use seizure timing, seizure counts, or sensitivity in any way — the tie-break
is explicitly forbidden from using them. This mirrors standard clinical deployment: a per-patient alarm
threshold is set to a target false-alarm rate on that patient's baseline recording, *before* any
seizure occurs. It is therefore attainable in real use, unlike the 0.789 oracle.

---

## 2. Integrity framing — is this still "patient-independent"? (state this in the thesis verbatim)

Yes, with a precise qualifier that must be reported honestly:

- The **detection model remains fully patient-independent**: it never trains on any test subject and
  never uses any test subject's seizures.
- We add a **per-patient false-alarm-rate calibration on seizure-free (interictal) data**. This is a
  *threshold* calibration, not model personalisation, and uses **no seizure labels**. In the seizure-
  detection literature this is standard and is not what "patient-specific training" means (that phrase
  denotes fitting the model to a patient's own seizures).
- It uses **strictly less** label information than the current shared operating point already does: the
  shared option-A point is chosen on the pooled **sensitivity-vs-FP/day** test frontier (it reads test
  sensitivity to build the frontier); the per-subject rule here reads **only interictal FP/day** and
  never sensitivity.

**We report BOTH numbers, never one instead of the other:**
1. **Strict held-out (no test-subject calibration):** the shared option-A operating point — the number
   from PREREG 03 / the deep-ensemble lock. This stays the primary "patient-independent, no per-subject
   calibration" headline.
2. **Per-subject FP-budget calibrated:** this pre-registration's result, clearly labelled as using
   per-patient false-alarm calibration on baseline data.

A reviewer must be able to see exactly what the calibration buys, and to take either number.

---

## 3. Non-test development + single test evaluation (discipline)

Although the rule is **parameter-free given B** (there is no free hyper-parameter to fit, so the
structural risk of test-overfitting is near zero), we still validate its BEHAVIOUR on non-test data
before the single test pass:

- **VAL (chb10, chb11, chb22):** build the deep-ensemble grid for the VAL subjects (same build_ens →
  build_seed_ensemble → score_ens chain, VAL only), apply the §1 rule, and check the two behavioural
  guarantees in §4. VAL is only 3 subjects, so this is a **sanity guardrail, not tuning**.
- **TEST (8 subjects):** apply the identical, already-fixed rule **once**. Report as-is.

No aspect of the rule (budget, tie-break, reference point) is adjusted after seeing test numbers.

---

## 4. Acceptance criteria (falsifiable, decided on VAL before the test pass)

Let *shared* = pooled sensitivity at the shared option-A point; *calib* = pooled sensitivity under the
per-subject FP-budget rule; both SzCORE-scored, at matched pooled FP/day ≈ B.

- **A1 (budget is respected):** pooled FP/day under the calibrated rule is within ±15% of B on VAL
  (confirms the calibration actually controls the false-alarm rate).
- **A2 (does no harm):** VAL pooled sensitivity under calibration is **≥** VAL shared sensitivity − 0.02
  (the rule must not degrade sensitivity at matched FP/day; a small tolerance for 3-subject noise).
- **A3 (mechanism sanity):** on VAL, no subject's calibrated FP/day exceeds 1.5·B (no subject is pushed
  to a pathological high-alarm point by the rule).

If **A1–A3 hold on VAL** → apply once to TEST and report *calib* alongside *shared* (§2).
If **A2 fails on VAL** (calibration hurts even the held-out subjects) → the intervention is rejected;
keep the shared operating point; record as a falsified prediction (like Decision #24). Do not re-tune to
pass.

**Honesty clause:** the recoverable gain is expected to be **a fraction** of the +0.171 oracle gap,
because the oracle uses seizure labels and the calibration does not. If the calibrated test gain is
small, report it small. The number is whatever it is.

---

## 5. What gets computed (cheap — mostly re-selection on existing scores)

- TEST: the deep-ensemble grid `final_eval_seed99.csv` already contains per-subject SzCORE FP/day and
  sensitivity for every (mag, pen). The rule is a **pure re-selection** over existing rows — no new
  scoring on test. (One script, CPU, seconds.)
- VAL: requires generating the VAL deep-ensemble grid first (build_ens VAL → build_seed_ensemble VAL →
  score_ens VAL), then the same re-selection. (~20–30 min, one Kaggle build + CPU scoring.)

Outputs (fresh, versioned; nothing overwritten):
```
results/retrain/fp_budget_val_check.csv       # per-VAL-subject chosen point, FP/day, sens; A1–A3 verdicts
results/retrain/fp_budget_test_persubject.csv # per-TEST-subject chosen (mag,pen), FP/day, sensitivity
results/retrain/fp_budget_locked.csv          # pooled balanced + high-sens: shared vs calibrated, +95% CIs
```

---

## 6. Relationship to step (b) SSL

This step (a) targets the **operating-point** loss (chb13/16/18 — signal-strong, mis-served by the
shared point). Step (b), a separate pre-registration (`PREREG_SSL.md`), targets the **signal** loss
(chb06/chb14 — genuinely weak window AUROC) via self-supervised pretraining of the learned branches,
with its own VAL go/no-go gate and a hard time-box (IELTS 9 Oct, submit 15 Oct). (a) is cheap and runs
first; (b) is expensive and runs only if (a) leaves signal-limited headroom worth the deadline risk.

---

## 7. Approval gate

Boti confirms: (a) budgets B = 40 (balanced) / 75 (high-sens); (b) the §1 selection rule + label-free
tie-break; (c) VAL guardrail A1–A3 before the single test pass; (d) both *shared* and *calibrated*
numbers are reported, never one silently replacing the other. On approval → I write
`fp_budget_operating_point.py` (re-selection + VAL check + test pass), smoke-tested, and the VAL-grid
build commands.
