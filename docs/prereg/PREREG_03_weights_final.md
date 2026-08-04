# PRE-REGISTRATION 03 — Ensemble weights + final evaluation + re-lock (PHA 1, step 3)

**Status:** DRAFT for review. Both model gates PASSED (Gate R-GAE, Gate R-LSTM). This is the last design
document before the rebuilt pipeline's headline is produced. No weight-search / final-eval code runs until
this is approved. One decision (operating-point selection, §3) needs Boti's sign-off.

---

## 0. Non-negotiables

- Ensemble weights are derived on **NON-TEST data only** (VAL, cross-checked on TRAIN). The 8 test subjects
  are touched exactly once, at the final evaluation, and the result is reported as-is (multi-seed mean±SD).
- No design is re-spun after seeing test numbers. If the temporal weight comes out small, that is the honest
  result — report it, do not inflate it back toward the old 0.35.

## 1. Inputs (adopted, gate-verified)

- GAE-joint seed-42 (Gate R-GAE PASS: macro recon AUROC 0.669, per-subject within 0.006 of locked).
- LSTM temporal seed-42 (Gate R-LSTM PASS: L1 0.661, L2 Δ +0.006, L3 SD 0.019, L4 ok).
- Gamma AEC (deterministic, retained).
- Components: zrecon, ztemp, zgamma — each **robust-z** (median/MAD, inter+ictal pooled, per subject).
  ztemp warm-up (first 15 windows/array) filled with the per-subject interictal median before robust-z
  (proven ΔTP=0 on the frozen pipeline).

## 2. Weight derivation (on NON-TEST)

- **Search space:** simplex grid `w_recon + w_temporal + w_gamma = 1`, step 0.05, all ≥ 0.
- **Objective:** VAL macro **window AUROC** (rank-based → stable on 3 subjects; the event tier is the headline
  but is too noisy to tune on 3 VAL subjects).
- **Anti-overfit tie-break:** among weights within 0.005 AUROC of the best, pick the one **closest to equal
  (1/3,1/3,1/3)** — regularises against extreme weights fit to only 3 VAL subjects. This is the concrete
  repair for Decision #19's fragile margin: the choice is non-test + regularised, not a thin test-set win.
- **TRAIN cross-check (12 subjects, ictal never seen in training):** recompute the objective on TRAIN. If the
  VAL-optimal weights are near-optimal on TRAIN too, adopt them; if they disagree sharply, fall back to
  **equal weights** (documented). Report both.
- **Report weight-sensitivity:** how much the final operating point moves under ±0.05 weight perturbations
  (robustness evidence, replaces the old thin-margin concern).

## 3. Operating-point (mag_pct / pen_mult) selection — DECIDED: (A)

The CPD stage exposes two knobs (magnitude percentile, PELT penalty) trading sensitivity vs FP/day. The OLD
locked points were chosen from a Pareto grid **on the 8 test subjects** (test-selection). For the rebuild we
adopt **option (A), pre-registered rule on the test frontier** (Boti approved):
report the FULL Pareto frontier (transparent), and pick the two reported points by a rule fixed HERE, before
seeing numbers: *balanced* = frontier point with FP/day nearest 40; *high-sens* = max sensitivity subject to
FP/day ≤ 75. Rule-based selection removes the cherry-picking objection while staying stable and honest.
(Options B = select on VAL, C = keep old mag/pen — considered and NOT chosen.)

## 4. Final evaluation (ONE pass on the 8 test subjects)

- Build zrecon/ztemp/zgamma for the 8 test subjects (adopted seed-42 models) → weighted ensemble (§2 weights)
  → `cpd_pipeline_v14` → `szcore_eval`. Report sensitivity, FP/day, precision, F1 + 95% CIs at the two
  operating points (§3), and window macro AUROC.
- **Multi-seed mean±SD:** run the full pipeline for all 5 seeds (GAE seed k + LSTM seed k) → report the
  headline as canonical seed-42 point estimate **plus** 5-seed mean±SD (the rubric's mean±SD, at the
  meaningful pipeline level).
- This is the new headline, whatever it is. It may differ from 0.750/0.791 — reported honestly.

## 5. Re-lock

- New numbers → `RESULTS_OF_RECORD.md` §16 (new headline). Frozen-component results (§1–§15) → archived as
  historical, **not deleted**. `PROVENANCE_MAP`, `PLAN_AND_STATUS` updated (Decision #25 closed).
- `ensemble_recipe.py` weight updated to the derived values (single source).

## 6. Approval gate

Boti confirms: (a) weight-derivation procedure §2; (b) **operating-point option A / B / C** (§3);
(c) 5-seed pipeline mean±SD at final eval. On approval → I write `derive_weights.py` (non-test) and
`final_eval.py` (one test pass), smoke-tested, run on Kaggle.
