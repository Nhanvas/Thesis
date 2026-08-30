# TIER-2 LOCK & CLEANUP — final pipeline = rlg (recon+latent+gamma, temporal-free)
**Run this ONCE now that rlg is locked. Two tracks: (A) Claude Project, (B) local repo. Order matters —
finish local pin/commit BEFORE editing the Project so the Project points at committed artifacts.**

Final result of record: see `docs/RESULTS_OF_RECORD_phaseB.md`. §0 (recon+temp+gamma) = HISTORICAL
baseline; rlg = optimized pipeline of record for report + web demo.

---

## 0 · FINAL LOCKED NUMBERS (single source once reconciled)
- Pipeline: per-window graph (wPLI+AEC top-k20) → GAE seed42 → {zrecon, zlatent, zgamma} robust-z →
  equal-weight (1/3) ensemble → PELT CPD → label-free FP-budget OP → SzCORE.
- Window: macro AUROC **0.805**, AUPRC **0.125**.
- Event matched-§0 cells: balanced **0.645 / prec 0.099 / F1 0.172 @ 38.4**; high-sens 0.763/0.120 @72.0.
- Event held-out (VAL-derived, triage): **F1 0.361 @ 3.6 FP/day** (SOTA band); sweep → 0.284@7.5, 0.213@27.4.
- Reproducible from committed GAE ckpt + gamma + adj/feat; temporal branch dropped (unreproducible).

---

## A · CLAUDE PROJECT UPDATE

### A1 · Upload (knowledge)
ADD/REPLACE: `RESULTS_OF_RECORD_phaseB.md`, `PREREG_TIER2_amendment_A1.md`, and scripts
`build_ens_tier2.py`, `ensemble_recipe.py` (updated), `g2_val_gate.py`, `tier2_oneshot_compare.py`,
`tier2_final_report.py`, `per_subject_op_check.py`, `latent_anomaly.py`.
DO NOT upload temporal/GSL/compact scripts (noise); their status is recorded in the amendment.

### A2 · PROJECT_INSTRUCTIONS.md — precise edits
- **CURRENT STATUS:** replace the "Phase B IN PROGRESS / Tier-2 next" block with:
  > **Tier-2 COMPLETE, LOCKED.** Optimized pipeline = **rlg (recon+latent+gamma, temporal-free)**.
  > Temporal (LSTM) branch DROPPED — unreproducible (corr 0.1–0.4 vs §0, 218σ; code lost). rlg matches
  > §0 at §0's cells and Pareto-improves precision/F1 at low FP (held-out F1 0.361 @ 3.6 FP/day, SOTA
  > band); window macro AUROC 0.805. Fully reproducible. Source: `docs/RESULTS_OF_RECORD_phaseB.md`.
- **METHOD (locked):** change branch set from `recon + LSTM + gamma` to
  `recon-MSE + latent-Mahalanobis + gamma (equal weight)`; note temporal removed.
- **LOCKED NUMBERS:** headline = §0 numbers become HISTORICAL baseline; rlg numbers (A0) are the
  reported optimized result. Keep §0 for the "vs baseline" comparison only.
- **COMMON PITFALLS:** add "Report rlg (temporal-free); §0/temporal = historical. Never cite the
  temporal-bearing E1/E2 window WIN (0.918/0.931) — computed on the broken temporal branch, retired."

### A3 · Proposed_solution_updated_v*.md — rewrite for report framing
- Proposed method = **rlg**: GAE with DUAL anomaly readout (reconstruction-MSE + latent-manifold
  Mahalanobis) + gamma-AEC, equal-weight ensemble → CPD → FP-budget OP → SzCORE.
- Move LSTM/temporal, S2 learned graph, S3 compactness, S5 multiband into **method development /
  ablation / negative results** (contributions, not the proposed method).
- Narrative hook: "reconstruction anomaly inverts under ictal hypersynchrony; a latent-manifold readout
  on the same GAE fixes it; the temporal branch was dropped for reproducibility with no performance
  cost — the readout, not architecture/temporal capacity, was the lever."

---

## B · LOCAL REPO CLEANUP (do FIRST)

### B1 · Pin the exact inputs (closes the recon-0.99 / data-drift risk permanently)
The rlg event results are reproducible from the COMMITTED frozen artifacts:
- `results/phaseB/tier2/ens_test_tf/{rlg,lg}/` (ensembles) + `components/` — CPD+SzCORE from these is exact.
COMMIT these (they are the crown result). For FULL raw-to-result reproduction, also snapshot the Kaggle
inputs actually used into a pinned dataset/folder and record the version in REPO_MAP:
- `chbmit-ckpt-canon` (GAE+—unused—LSTM canonical ckpts, already made).
- the adj (`*_adjs_topk20.npy`) + features + gamma versions used → note the exact Kaggle dataset
  version hash in REPO_MAP so the ~0.99 recon input is pinned, not floating.

### B2 · Directory layout (create + git add)
```
results/phaseB/tier2/
├─ ens_val_tf/{rlg,rg,lg}/ + components/        # VAL ensembles (gate)
├─ ens_test_tf/{rlg,lg}/  + components/         # TEST ensembles (one-shot) — CROWN
├─ {rlg,rg,lg}/final_eval_seed42.csv            # VAL grids
├─ {rlg,lg}_test/final_eval_seed42.csv          # TEST grids
├─ G2prime_val.csv, ONESHOT_rlg_vs_s0.csv, FINAL_report.csv
src/phaseB/  ← build_ens_tier2, g2_val_gate, tier2_oneshot_compare, tier2_final_report,
               per_subject_op_check, latent_anomaly, dump_val_components, branch_ablation, val_gate
docs/        ← RESULTS_OF_RECORD_phaseB.md, PREREG_TIER2_amendment_A1.md
```

### B3 · Archive (archive-don't-delete → results/history_superseded/tier2_temporal/)
- Temporal-bearing candidates: `baseline_rtg/`, `rltg/`, `ltg/` grids + their ens (contaminated by the
  broken temporal branch — keep for provenance, mark RETIRED).
- The E1/E2 temporal window numbers (0.866/0.918/0.931) — flag RETIRED in 01_EXPERIMENT_LOG.md.

### B4 · REPO_MAP.md — one scan-all pass
- Add every path in B2 as AUTHORITATIVE (final pipeline).
- Mark §0 `results/retrain_v3p1/*` as HISTORICAL baseline (kept, not headline).
- Record the pinned Kaggle dataset versions (B1) so nothing floats.

### B5 · Commit
```
git add results/phaseB/tier2 src/phaseB docs/RESULTS_OF_RECORD_phaseB.md \
        docs/PREREG_TIER2_amendment_A1.md docs/REPO_MAP.md
git commit -m "Tier-2 FINAL LOCK: rlg optimized pipeline (temporal-free, reproducible); archive temporal; repo-map scan-all"
```

---

## C · WHAT'S DEFERRED (not part of the lock)
- Reconcile `docs/RESULTS_OF_RECORD.md` main §0↔phaseB in one edit (fold rlg in; keep §0 as history).
- Supervisor (cô) brief (Boti will cue).
- Report writing + web demo (both read the SAME committed rlg artifacts — never a Kaggle path).
