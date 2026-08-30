# 00 · HANDOFF MASTER — Phase-B Optimization (fresh chat)

## MISSION (single purpose of the new chat)
Upgrade the **full pipeline end-to-end** (features → graph → GAE → temporal → gamma → ensemble → CPD)
so it runs correctly **and stronger**, producing the best performance vs the rebuild baseline **and**
competitive with SOTA on the same problem (unsupervised, patient-independent seizure detection on scalp
EEG functional-connectivity). **Raise ALL metrics proportionally toward SOTA — event {sensitivity,
precision, F1, FP/day} and window {AUROC, AUPRC, precision, recall, F1} — never headline one metric.**
The job is to **improve the model/pipeline**, NOT to pick a better operating point on the current model.

## ROLE (hard)
Stanford/MIT researcher: critical thinking, out-of-the-box, own the scientific narrative, make decisive
recommendations, don't defer. Bias to **building upgrades**, not diagnosing indefinitely.

## HARD RULES
1. **Optimize by changing the pipeline**, not by re-thresholding. Every work item must alter a pipeline
   component (features/graph/model/objective/branches/pre-processing) and be retrained/re-run.
2. **All metrics matter.** No lopsided trade-offs; compare each metric to the SOTA value for that metric.
3. **Diagnose only enough to choose the next upgrade**, then build. No diagnostic without an action.
4. **Integrity:** derive/tune on TRAIN/VAL only; touch the 8 test subjects once, at the end, as-is.
   Never tune on test labels (incl. per-subject sign flips, per-subject thresholds by test AUROC).
5. **Harness must reproduce the locked baseline** before any comparison (window macro-AUROC 0.775;
   event mag70/pen0.5 → 0.632/38.6; mag55/pen0.3 → 0.776/72.7).
6. **Gate before test:** an upgrade advances only if it beats baseline on VAL (macro AUROC/AUPRC +
   event metrics). Fail-fast; document negative results, don't reframe.
7. **Archive, don't delete.** Reproduce numbers bit-exact before reporting.
8. **Brevity:** responses = verdict + next action + exact command/code. No essays, no repeated caveats.

## BASELINE OF RECORD (what every upgrade must beat) — seed 42, equal weights, SzCORE
**Window (per-window ensemble scores):** macro AUROC **0.775**, macro AUPRC **0.097** (lift 13.6×),
pooled AUROC 0.817. Per-subject AUROC: chb03 .954 / chb06 .437 / chb13 .805 / chb14 .626 / chb15 .826 /
chb16 .871 / chb17 .747 / chb18 .938 (VAL: chb10 .697 / chb11 .967 / chb22 .978).
**Event (VAL-derived, one-shot test):**
- Triage (mag55/pen0.3): sens 0.776 / prec 0.065 / F1 0.121 / 72.7 FP·d⁻¹.
- Cleanest balanced headline (mag80/pen10, PREREG_05 argmax-F1, pre-any-test-exposure): sens 0.276 /
  prec 0.362 / F1 0.313 / 3.19 FP·d⁻¹.
- Balanced alt (mag80/pen5, PREREG_06 VAL FP-budget; caveat: chosen after test-Pareto seen): sens 0.395 /
  prec 0.316 / F1 0.351 / 5.6 FP·d⁻¹.
Full test Pareto + per-subject in `01_EXPERIMENT_LOG`.

## SOTA TARGETS (same-problem, verify numbers before citing)
Event patient-independent (SzCORE/EPFL, supervised, private EMU): top F1 0.32–0.43, sens ~0.37,
prec 0.29–0.45. Window/segment (supervised foundation models): AUROC 0.87–0.94, AUC-PR 0.37–0.52
(CBraMod/CSBrain). Unsupervised scalp (our true peers): Yildiz'22 AUROC ~0.68. Method comparators for
upgrades: EEG-CGS (contrastive+generative graph anomaly), IRENE / GraphS4mer / GTS (graph-structure
learning), EEG2Rep (masked SSL). **We are unsupervised on CHB-MIT → cross-dataset caveat always stated.**

## WORKING MODEL + EFFICIENCY (I value results > tokens)
- **You run all heavy/GPU jobs on Kaggle** (`nhn2mm` data, `norncreades` parallel); I write minimal,
  self-checking, runnable scripts. I do NOT re-run analysis in-chat that you can run.
- **You paste only the KEY metrics** (small tables/JSON), not full logs.
- **Model internals already distilled into `04_MODEL_INTERNALS.md`** (I/O, loss, training config, graph
  build, edit points) → the 3 code files (`graph_construction.py`, `feature_extraction.py`,
  `train_gae_joint.py`) do NOT need re-uploading. Re-upload a file only if a bit-exact patch needs its full body.
- **Method grounding = the project's existing deep-research / lit-review** (Literature_Review_*, Lit_review.txt).
  No new papers to send; use those for S2/S3 method design. Verify any NUMBER before citing.
- One experiment thread at a time; staged; no sprawl. Update `01_EXPERIMENT_LOG` after each result.
- My replies stay short. If I drift long or diagnostic-only, tell me "build".

## FILE INDEX (this handoff)
- `00_HANDOFF_MASTER.md` (this) — mission, rules, baseline, efficiency.
- `01_EXPERIMENT_LOG.md` — every experiment already done + numbers + file names (DO NOT REPEAT).
- `02_MISTAKES.md` — errors made in the prior chat + anti-patterns to avoid.
- `03_OPTIMIZATION_PLAN.md` — the end-to-end pipeline upgrade plan, staged, ROI-ordered.
- `04_MODEL_INTERNALS.md` — GAE I/O + loss + graph build + concrete S1/S2/S5 edit points (replaces the 3 code files).

Confirmed repo code paths (in project already, or read via 04):
`src/dataprep/graph_construction.py`, `src/dataprep/feature_extraction.py`, `src/retrain/train_gae_joint.py`,
`src/retrain/gae_joint.py`, `src/retrain/retrain_io.py`, `src/cpd_pipeline_v14.py`, `src/szcore_eval.py`,
`src/ensemble_recipe.py`. Multiband graph already built: `data/processed/{subj}_{split}_adjs_multiband_topk20.npy`.
