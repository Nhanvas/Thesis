# PRE-REGISTRATION — TIER-2: latent-manifold ensemble → event-level, one-shot TEST

**Status:** DRAFT for author/supervisor sign-off. NO ensemble-build / CPD / SzCORE code runs on the 8
TEST subjects until this is approved and the VAL guardrail (§4) passes.
**Author role:** research director (proposes); Boti = final decision-maker (approves, executes).
**Scorer (fixed, unchanged from §0):** SzCORE event-based via `timescoring` (any-overlap; 30 s pre /
60 s post tolerance; merge < 90 s; split > 5 min). FP/day denominator = interictal hours. Every
sensitivity / precision / F1 / FP-day below is that SzCORE score. No new metric is introduced.
**Baseline to beat (locked §0, reproduced in-harness before writing this):**
balanced 0.632 @ 38.6 FP/day (mag70/pen0.5, TP/FN/FP 48/28/447);
high-sens 0.776 @ 72.7 FP/day (mag55/pen0.3, 59/17/843); window macro AUROC 0.775. ✔ reproduced exactly.

---

## 0. Claim under test (single sentence)
> The GAE **latent-manifold** anomaly readout (Mahalanobis of graph-mean-pooled Z to the per-subject
> interictal manifold), which fixed the recon-anomaly inversion under ictal hypersynchrony at the
> WINDOW level (chb10 VAL AUROC 0.268→0.816; ensemble VAL window 0.866→0.918/0.931), also improves
> **event-level** detection over the recon-based §0 baseline on held-out TEST, at matched FP/day.

This is the ONLY thing Tier-2 tests. Everything else (weights, OP rule, scorer, splits) is held fixed.

---

## 1. What changes vs §0, and what is frozen
**Changes (exactly one thing):** the GAE branch anomaly component. §0 uses recon-MSE (`zrecon`).
Tier-2 adds/substitutes the latent-Mahalanobis component (`zlatent`) from `latent_anomaly.py`,
robust-z'd identically to the other branches. Latent center + LedoitWolf covariance are fit
**per-subject on that subject's INTERICTAL only** — label-free, so valid on TEST with no leakage.

**Frozen (identical to §0, no re-tuning):**
- Ensemble weights = **equal** (1/N). NO weight learning on the 3 VAL subjects (prior lesson).
- Operating-point rule = **PREREG_04** label-free FP-budget (B=40 balanced, B=75 high-sens;
  `min|FP/day_interictal − B|`, tie-break by distance to shared reference, **never** by sensitivity).
- CPD = `cpd_pipeline_v14` (PELT), unchanged. Scorer = `timescoring`, unchanged.
- Splits: VAL = chb10/11/22 gates; TEST = chb03,06,13,14,15,16,17,18 touched **once**, as-is. Seed 42.

---

## 2. Candidate ensembles (pre-designated — headline fixed BEFORE any TEST exposure)
To avoid selecting the candidate on TEST, the headline candidate is fixed **now**, on narrative +
VAL-window evidence already in hand, not chosen later on TEST:

- **PRIMARY (headline):** `recon + latent + temp + gamma` — GAE dual-readout; keeps every branch; best
  4-branch VAL AUPRC (0.280); best-narrative (GAE-centric: same net, two readouts). Weights 1/4 each.
- **SECONDARY (lean alternative, pre-declared):** `latent + temp + gamma` — highest VAL window AUROC
  (0.931) but lower AUPRC. Weights 1/3 each.
- Both are carried through the VAL event pipeline and, if the guardrail (§4) passes, **both** are
  scored on TEST in the single one-shot pass. The PRIMARY is the reported headline regardless of which
  reads higher on TEST (reporting the secondary alongside is disclosure, not selection).
- `recon+latent+gamma` (drop temporal) is **exploratory only** — VAL-side sanity, NOT taken to TEST.

Rationale for fixing the headline rather than letting VAL event F1 pick: 3 VAL subjects give a noisy
F1; the prior chat already burned a lesson on VAL-lucky gamma. Minimizing VAL-based selection DOF is
the more defensible choice.

---

## 3. Operating-point derivation (VAL-derived, frozen, then one-shot TEST)
For each candidate, on the VAL mag/pen grid:
1. **Shared cell** = the single (mag,pen) whose **VAL pooled** FP/day is nearest B (B=40, then B=75).
   This is stricter than §0's shared cell and fully held-out. Freeze the cell.
2. **Calibrated (per-subject)** = PREREG_04 per-subject rule on VAL guardrail → then TEST re-select on
   each TEST subject's own interictal FP/day (label-free). Report alongside shared, per §0 convention.
3. Apply the frozen shared cell + the per-subject calibrated points to TEST **once**. Report pooled
   sensitivity, precision, F1, FP/day, all with 95% CIs (Wilson for proportions, exact Poisson FP/day).

---

## 4. VAL GUARDRAIL / STOP-CONDITION (must pass before TEST is touched)
Pre-specified, checked on VAL only:
- **G1 (window, already in hand):** PRIMARY VAL window macro AUROC ≥ §0 baseline-ensemble 0.866.
  (Observed 0.918 ✔ — recorded, not re-litigated.)
- **G2 (event, must be run):** PRIMARY VAL **event** F1 at B=40 ≥ the §0 baseline ensemble
  (`recon+temp+gamma`) VAL event F1 at B=40, computed in the SAME harness in the same run.
- **STOP:** if G2 fails (latent-ensemble is not ≥ baseline-ensemble on VAL event F1), **do NOT touch
  TEST.** Report: "window improvement did not survive CPD+SzCORE on VAL" — a clean negative, logged,
  §0 stays the reported baseline.

---

## 5. PRIMARY ENDPOINT + falsification (stated before the one-shot)
- **Primary endpoint:** TEST pooled event **sensitivity at the frozen balanced cell**, with its FP/day.
- **Success:** point estimate **> 0.632** at FP/day within ±5 of 38.6 (i.e. not bought with extra FPs).
  A CI lower bound approaching/exceeding 0.632 is the strong form; with 76 seizures CIs are wide, so
  the point-estimate-at-matched-FP/day rule is the pre-registered decision, CI reported honestly.
- **Falsification:** if TEST balanced pooled sensitivity **≤ 0.632** at comparable FP/day (±5), the
  latent readout did **not** improve event detection → reported as a **falsified prediction**: the WIN
  remains a window-level finding, §0 remains the reported event baseline, no reframing.
- **Secondary endpoint (disclosure):** high-sens cell (B=75) sensitivity/FP-day vs §0 0.776/72.7;
  window macro AUROC vs 0.775; per-subject deltas (esp. the two representation-limited subjects
  chb06/chb14 — expected NOT to be rescued by a readout change; if they are, that is a bonus, flagged).

---

## 6. Harness fidelity gate (before trusting ANY Tier-2 number)
The Tier-2 harness must first reproduce the LOCKED baseline in-run: window macro AUROC 0.775;
event mag70/pen0.5 → 0.632 @ 38.6 (48/28/447); mag55/pen0.3 → 0.776 @ 72.7 (59/17/843).
✔ Already reproduced from `final_eval_seed42.csv` + `fp_budget_locked.csv` on CPU (this session).
The Kaggle build must reproduce the same §0 event rows from the recon-ensemble path before the
latent path is trusted.

---

## 7. Provenance (local-first, non-negotiable)
Every artifact lands at a `REPO_MAP` path and is committed the SAME day. Kaggle is compute-only.
Declare paths BEFORE the run:
- `results/phaseB/tier2/val_event_grid_{candidate}.csv` — VAL mag/pen event grid per candidate.
- `results/phaseB/tier2/val_op_verdict.json` — frozen shared cells + calibrated points + G2 verdict.
- `results/phaseB/tier2/test_oneshot_{candidate}.csv` — one-shot TEST event rows (the crown result).
- `results/phaseB/RESULTS_OF_RECORD_phaseB.md` — reconcile pass, then fold into §0 in ONE edit.
- `zlatent` components committed under `data/processed/components/` (VAL + TEST).

---

## 8. Sign-off
- [ ] Boti approves candidate designation (§2), OP rule (§3), guardrail (§4), endpoint/falsification (§5).
- [ ] Supervisor (cô) briefed that this is a Phase-B event-level test against the honest §0 baseline.
- On approval: build `zlatent` component builder (VAL first) → G2 guardrail → (if PASS) one-shot TEST.
