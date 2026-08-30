# PHASE_C_HANDOFF — representation optimization (fresh chat)
**Purpose:** start Phase C in a new chat with full context. Tier-2 is DONE and LOCKED (rlg). Phase C
reopens the REPRESENTATION frontier (front-end: connectivity / features / GAE), previously under-explored.
When a NUMBER here disagrees with `docs/RESULTS_OF_RECORD_phaseB.md`, that file wins for locked rlg.

---

## 0 · STATUS
- **Tier-2 LOCKED:** optimized pipeline = **rlg (recon+latent+gamma, temporal-free)**. Window macro AUROC
  0.805; event matched-§0 balanced 0.645/F1 0.172 @38.4 (≥§0); held-out triage F1 0.361 @ 3.6 FP/day
  (SOTA band). Fully reproducible. Temporal branch dropped (unreproducible, LSTM code lost). §0 =
  historical baseline. Source: `docs/RESULTS_OF_RECORD_phaseB.md`, `PREREG_TIER2_amendment_A1.md`.
- **rlg is the baseline to beat.** Phase C develops CHALLENGERS on VAL; the SINGLE best challenger (if it
  beats rlg on VAL) gets ONE one-shot TEST. Never iterate on TEST.
- **Front-end is REPRODUCIBLE and OWNED** (this was verified, not lost): `src/dataprep/{preprocessing,
  graph_construction, feature_extraction, compute_gamma_aec, create_splits}.py`. preprocessing.py outputs
  z-scored artifact-clean raw windows `{subj}_{interictal,ictal}.npy [N,18,1024]`, aligned by construction
  to features/adj. (Earlier apparent interictal-count mismatch = Step-4 5×SD artifact rejection.)

## 1 · PHASE C PLAN (ranked, gated; rlg is the bar)
| # | thread | cost | gate | note |
|---|---|---|---|---|
| **C0** | chb06 diag + CCM/TE/wPLI probe | cheap | convergence+separation | **DONE — see §2** |
| **C4-lite** | add **TE directed-connectivity ANOMALY BRANCH** → `recon+latent+gamma+TE` | low | VAL event F1 ≥ rlg | **NEXT** |
| C1 | temporal smoothing of anomaly (HMM/smooth pre-CPD) | low | VAL event F1 | independent; targets FP/precision |
| C2 | richer node features (line-length/Hjorth/entropy) | med | VAL window AUROC | edit feature_extraction.py |
| C3 | stronger GAE (VGAE/GAT/deeper) | med-high | VAL window AUROC | "GAE too basic" |
| C4-full | TE as 2nd directed edge in GAE (multi-relational) | high | after C4-lite | if lite promising, higher novelty |
Sequencing: **C4-lite next** (probe already green). C1 can run in parallel. C2/C3 after. C4-full only if lite warrants.

## 2 · C0 PROBE RESULT (DONE — trustworthy; null~0.5 validated)
Directed nonlinear connectivity **recovers the symmetric-inverted subjects**; TE ≥ symmetric almost
everywhere; CCM rejected (no convergence at 4 s, inverts on chb10/chb22). Held-out anomaly AUROC
(script `src/phaseC/connectivity_probe.py`, PREREG `docs/PREREG_C0_connectivity_probe.md`):
| subj | sym | **te** | ccm | note |
|---|---|---|---|---|
| chb06 | 0.370 (inv) | **0.733** | 0.545 | te fixes inversion |
| chb22 | 0.216 (inv) | **0.827** | 0.193 | te fixes inversion |
| chb14 | 0.765 | **0.888** | 0.877 | te best |
| chb03 | 0.462 | 0.578 | 0.394 | te best |
| chb11 | 0.510 | 0.627 | 0.516 | te best |
| chb10 | **0.752** | 0.517 | 0.786 | te WORSE (sym already good) |
**Read:** TE is COMPLEMENTARY, not a replacement (mirrors recon↔latent). It rescues inverted subjects
(chb06/chb22 — the pipeline ceiling) but loses on chb10 where sym is strong → **keep both** = add TE as a
branch, don't replace wPLI. Decision: **C4-lite = `recon+latent+gamma+TE` equal-weight (1/4)**.

## 3 · C4-lite BUILD SPEC (aligned by construction — no rebuild)
Write `src/phaseC/build_te_branch.py`:
1. Import `src/dataprep/preprocessing.py`; replicate its EXACT window iteration (filename order, 4 s
   non-overlap, ictal=seizure-overlap, interictal=non-buffer + 5×SD artifact-clean, z-score w/ subject
   stats). Reuse its functions (`open_edf, filter_window, build_labels, build_buffer_mask`, stats) so the
   window SET and ORDER are identical to features/adj. (Or read the raw-window `.npy` if present.)
2. Per accepted window: `graph_construction.apply_car` → **compute TE 18×18 directed** (binned TE from
   `connectivity_probe.transfer_entropy`, validated) → vectorize.
3. Anomaly readout = Mahalanobis of the TE-vector to the per-subject INTERICTAL manifold (LedoitWolf,
   interictal-fit only — label-free, valid on TEST) → raw TE-anomaly per window.
4. `retrain_io.robust_z(raw_i, raw_c)` → `zTE_{subj}_{inter,ictal}`, saved to
   `data/processed/components/`. **ASSERT** len == features n_win per subject (alignment gate).
5. Add candidate `rltg_te = ("zrecon","zlatent","zgamma","zTE")` to `ensemble_recipe.CANDIDATES`; build
   ensemble via `build_ensemble_subset` (equal 1/4) → `score_ens` VAL grid → `g2_val_gate` vs rlg.
6. If VAL event F1 ≥ rlg (G2') → PREREG_C4 → ONE-shot TEST vs rlg/§0 via `tier2_oneshot_compare` /
   `tier2_final_report`. Else negative, rlg stands, TE is a reported analysis/future-work contribution.
Runtime note: TE is 306 directed pairs/window; per-subject pass ~minutes-to-tens; run per subject, commit.

## 4 · INTEGRITY / WORKING RULES (carry over — unchanged)
- Researcher/mentor; propose→user approves→user executes (Kaggle GPU / Cursor CPU); no autonomous action.
- Vietnamese replies; code/English deliverables in English; concise (verdict+next+command).
- **State hypothesis + falsification + stop-condition BEFORE running.** Report negatives honestly.
- **Reproduce/validate before trusting any number** (null-checks, alignment asserts, smoke tests). This
  session caught: (a) all-1.0 AUROC = dim>>n Mahalanobis + amplitude artifact; (b) ztemp unreproducible;
  (c) recon-0.99 data drift. Vigilance for "eval bug masquerading as result" is mandatory.
- **VAL gates; TEST one-shot at the very end, as-is.** rlg is the locked bar.
- Local-first provenance: every artifact committed at a REPO_MAP path same day; Kaggle is disposable.
- Do NOT re-propose rejected levers: learned graph (S2), multiband (S5), compactness (S3), ensemble-weight
  learning, per-subject label-free OP (negative on rlg too), operating-point-only tuning.

## 5 · FILES THE NEW CHAT NEEDS (add to Claude project)
Front-end (NEW, essential for C4): `src/dataprep/{preprocessing, graph_construction, feature_extraction,
compute_gamma_aec, create_splits}.py`.
Phase C: `src/phaseC/{connectivity_probe, align_check, align_check2}.py`, `docs/PREREG_C0_connectivity_probe.md`.
Carry: `RESULTS_OF_RECORD_phaseB.md`, `PREREG_TIER2_amendment_A1.md`, `ensemble_recipe.py` (with CANDIDATES),
`retrain_io.py`, `latent_anomaly.py`, `build_ens_tier2.py`, `g2_val_gate.py`, `tier2_oneshot_compare.py`,
`tier2_final_report.py`, `cpd_pipeline_v14.py`, `szcore_eval.py`, `evaluation_protocol.py`,
`RESULTS_OF_RECORD.md`, `REPO_MAP.md`, this handoff.
Opening line for new chat: "Đọc PHASE_C_HANDOFF.md, bắt đầu C4-lite: build TE branch aligned, VAL-gate vs rlg."

## 6 · DEFERRED (not Phase C blockers; do when Boti cues)
- Reconcile `RESULTS_OF_RECORD.md` main + PROJECT_INSTRUCTIONS to rlg (Tier-2 lock cleanup — see
  `TIER2_LOCK_AND_CLEANUP.md`); supervisor brief; report writing; web demo (reads committed rlg artifacts).
