# TIER-2 HANDOFF — Phase B (fresh chat)
**Purpose:** start Tier-2 integration in a new chat with full context of what this session did.
When any NUMBER here disagrees with `docs/RESULTS_OF_RECORD.md` §0, §0 wins for the *locked baseline*;
the numbers below are the *Phase-B experiment results* produced this session.

---

## 0 · MISSION (the new chat's single job)
The window-level anomaly signal has been improved (see §3 WIN). Now run **Tier-2**: turn that into
**event-level** results and decide the final ensemble.
```
build ensemble (with the new latent branch) → CPD (cpd_pipeline_v14) → SzCORE (timescoring)
→ mag/pen grid on VAL → derive operating point on VAL (PRE-REGISTER)
→ ONE-SHOT TEST (8 subjects) → compare event metrics vs locked baseline (0.632 / 0.776)
→ reconcile RESULTS_OF_RECORD → report + web demo
```
Integrity (hard): **VAL (chb10/11/22) gates everything; TEST (chb03,06,13,14,15,16,17,18) touched
ONCE at the very end, as-is.** Never tune on TEST. All new scripts carry a TEST-guard already.

---

## 1 · WHERE WE ARE IN PHASE B
```
Diagnosis: is graph structure the lever? ........ DONE → NO
S2 learned graph (multiband / GSL-gated / forced)  REJECTED (3 negatives)
E2 latent-manifold readout on the SAME GAE ....... WIN  ← the Phase-B result
E1 branch ablation (with zlatent) ................ confirms the WIN at ensemble level
S3 compactness (Deep-SVDD retrain) ............... NEGATIVE → stop GAE upgrades
SSL/masked (heavier S3) .......................... DECLINED (ROI + timeline)
──────────────────────────────────────────────────────────────
► TIER-2 INTEGRATION ← START HERE
  Report + web demo
```

---

## 2 · THE KEY FINDING / WIN (locked this session)
**GAE reconstruction-MSE anomaly INVERTS under ictal hypersynchrony.** For chb10 the GAE (trained on
interictal) reconstructs *ictal* better than interictal → recon-error is anti-correlated with seizure
(chb10 recon AUROC **0.268**, inverted). **Fix (0 retrain): read anomaly as DISTANCE in the GAE latent
space** (Mahalanobis of graph-mean-pooled Z=16-d to the interictal manifold, LedoitWolf covariance).
Same GAE, different readout. This is GAE-centric and publishable:
> "Reconstruction anomaly fails under ictal hypersynchrony; a latent-manifold readout on the same GAE
> fixes it. Graph-structure learning and a compactness objective did not improve further → the readout,
> not the architecture/objective, was the lever."

**Latent vs recon readout (VAL, GAE-recon branch, seed 42):**
| subj | recon_AUROC | latent_AUROC |
|---|---|---|
| chb10 | 0.268 (inverted) | **0.816** |
| chb11 | 0.852 | 0.641 |
| chb22 | 0.656 | 0.736 |
| **macro** | 0.592 | **0.731** |
(latent macro AUPRC 0.059.)

---

## 3 · ALL EXPERIMENTS THIS SESSION (numbers = VAL, seed 42, GAE-recon branch or ensemble as noted)

### S5 multiband GAE — REVERT (negative)
Retrained GAE on multiband adjacency. VAL macro AUROC **0.581** vs baseline 0.592; AUPRC 0.021 vs 0.050;
chb11 dropped 0.852→0.709. Multiband adjacency does not beat top-k20.

### S2 GSL residual-gated — NULL (gate collapsed)
Per-window learned graph, residual gate. Gate `g→0.0000` by ep40 → reduced to baseline (macro 0.5921 ≈
baseline 0.5920). Side-benefit: proved the dense-GCN reimplementation == baseline at g=0.

### S2 GSL force_g=1 (pure learned graph) — REJECTED
Forced learned graph. recon worse (train 0.028 vs 0.016), chb10 still inverted 0.269, macro **0.579**.
→ **Graph structure is NOT the lever** (recon objective gives no signal to learn a discriminative graph;
inversion is objective/nonstationarity, not capacity).

### E2 latent-anomaly — WIN (see §2).

### E1 branch ablation (VAL, equal-weight mean of robust-z components; zlatent added)
| ensemble | macroAUROC | macroAUPRC | chb10 | chb11 | chb22 |
|---|---|---|---|---|---|
| **latent+temp+gamma** | **0.931** | 0.245 | 0.909 | 0.930 | 0.956 |
| recon+**latent**+temp+gamma (GAE dual-readout) | 0.918 | 0.280 | 0.826 | 0.956 | 0.970 |
| recon+latent+gamma | 0.928 | **0.329** | 0.850 | 0.956 | 0.979 |
| latent+gamma | 0.939 | 0.288 | 0.931 | 0.925 | 0.960 |
| temp+gamma (drop GAE) | 0.902 | 0.231 | 0.808 | 0.939 | 0.959 |
| **recon+temp+gamma (LOCKED baseline ensemble)** | 0.866 | 0.277 | 0.658 | 0.965 | 0.975 |
| gamma (single) | 0.906 | 0.264 | 0.822 | 0.931 | 0.965 |
| recon (single) | 0.592 | 0.050 | 0.268 | 0.852 | 0.656 |

**Reads:** (1) replacing recon→latent lifts the ensemble +0.065 macro AUROC (0.866→0.931). (2) **Keeping
recon (dual-readout) raises AUPRC** (recon+latent+gamma 0.329 vs latent+temp+gamma 0.245) — matters for
the event precision / FP-day side. (3) gamma is very strong on VAL alone (0.906) — but VAL is only 3
subjects; do NOT over-index on VAL-lucky gamma; TEST decides.

### S3 compactness (Deep-SVDD retrain) — NEGATIVE
Retrained GAE + compactness term (auto-balanced, warmup-frozen center). Latent macro **0.686** < 0.731
(chb10 0.747, chb11 0.531, chb22 0.781). `comp` term ~0.0005 flat over 200 ep → interictal manifold was
already compact. Recon slightly worse. → stop GAE upgrades.

---

## 4 · TIER-2 CANDIDATES (let EVENT metrics decide, not VAL window)
Carry these into CPD+SzCORE on VAL, then one-shot TEST:
1. **recon+latent+temp+gamma** — GAE dual-readout, keeps everything, best-narrative (GAE-centric), best
   AUPRC among 4-branch; VAL window 0.918.
2. **latent+temp+gamma** — leanest strong option; VAL window 0.931 but lower AUPRC.
3. (optional) **recon+latent+gamma** — highest VAL AUPRC (0.329); test if temporal branch is dead weight.
Recommendation: primary = **recon+latent+temp+gamma** (dual-readout; AUPRC + narrative), report
latent+temp+gamma as the lean alternative. Decide on TEST event F1 / FP-day, not VAL window.

**Equal-weight (1/3 or 1/4) stays the default** — do NOT learn weights on 3 VAL subjects (prior lesson).

---

## 5 · TIER-2 BUILD PLAN (what the new chat writes)
1. **Make `zlatent` a first-class component.** Bake the latent-Mahalanobis readout into the component
   builder (`retrain_io.build_subject_components` or a sibling), robust-z'd like the others, so
   `build_ens.py`/`score_ens.py`/`ensemble_recipe.py` can produce ensembles that include it. Latent
   center+cov are fit per-subject on that subject's INTERICTAL only (unsupervised, label-free — valid
   on TEST too, no leakage).
2. **VAL event pipeline:** ensemble scores → `cpd_pipeline_v14` (PELT) → `szcore_eval`/`timescoring`
   → mag/pen grid on VAL → derive operating point (PRE-REGISTER the rule before looking at TEST).
   Reuse the harness that produced `results/retrain_v3p1/final_eval_seed42.csv` (read it + `szcore_eval.py`
   + `evaluation_protocol.py` + `fp_budget_operating_point.py` to reproduce the locked baseline first).
3. **Harness must reproduce the LOCKED baseline** (window macro-AUROC 0.775; event mag70/pen0.5 →
   0.632/38.6; mag55/pen0.3 → 0.776/72.7) before trusting any new number.
4. **One-shot TEST** with the VAL-derived OP → full Pareto + balanced + high-sens → compare to §6.
5. Reconcile `RESULTS_OF_RECORD.md` in one pass; then report + web demo.

---

## 6 · LOCKED BASELINE OF RECORD (unchanged — the bar to beat)
- Balanced: sensitivity **0.632** [0.519,0.731] @ **38.6** FP/day (shared mag70/pen0.5, TP/FN/FP 48/28/447)
- High-sens: sensitivity **0.776** [0.671,0.855] @ **72.7** FP/day (shared mag55/pen0.3, 59/17/843)
- Window macro AUROC **0.775**; 5-seed VAL AUROC 0.648 ± 0.011
- Ensemble = equal weights (1/3 each: recon+temp+gamma), canonical **seed 42**.
- SOTA context: beats Yildiz'22 unsup CHB-MIT (~0.68); event F1 0.31–0.35 already in supervised
  patient-independent band (0.32–0.43). Cross-dataset caveat always stated.

---

## 7 · KAGGLE ENVIRONMENT (exact)
Mount prefix: `/kaggle/input/datasets/<owner>/<slug>`.
Datasets:
- `nhn2mm/chbmit-processed` — features `{subj}_{interictal|ictal}_features.npy` (band-agnostic; shared).
- `nhn2mm/chbmit-topk20` — baseline adjacency `{subj}_{interictal|ictal}_adjs_topk20.npy`.
- `nhn2mm/gamma-aec-scores` — gamma branch `gamma_aec_{subj}_{inter|ictal}.npy`.
- `norncreades/chbmit-multiband` — `{subj}_{split}_adjs_multiband_topk20.npy` (S5, REJECTED — ignore).
- `norncreades/gae-s5` — all `.py` + **`gae_joint_seed42.pt`** + **`lstm_temporal_seed42.pt`**.
Notebooks: `nhn2mm/thesis-s2-learned-graph`, `norncreades/thesis-s5-multiband`.

**GOTCHA (must handle):** Kaggle UNZIPS uploaded `.pt` files into nested folders (a `.pt` is a zip).
`gae_joint_seed42.pt` and `lstm_temporal_seed42.pt` appear as `…/<name>/<name>/{data.pkl,data/,version,
byteorder,.data,…}`. Rebuild at runtime with the marker-based helper (in `dump_val_components.py` /
`latent_anomaly.py`): find the dir containing `data.pkl` whose path contains the marker, re-zip to a
`.pt`. Works; tested. Requires `torch_geometric` (pip install; Internet ON for save-version).

---

## 8 · SCRIPTS FROM THIS SESSION (in `gae-s5` dataset + /mnt outputs)
KEEP (active / Tier-2 relevant):
- `latent_anomaly.py` — E2 WIN. Latent Mahalanobis anomaly. Has `--ckpt` override, TEST-guard.
- `dump_val_components.py` — dumps zrecon/ztemp/zgamma/**zlatent** for VAL (torch.load; marker rebuild).
- `branch_ablation.py` — E1. Auto-discovers branches, equal-weight subset leaderboard, decision rows.
- `val_gate.py` — VAL-only GAE-recon gate, `--gae_module` switch, TEST-guard.
ARCHIVE (provenance; negative/superseded — do not delete):
- `gae_joint_gsl.py`, `train_gae_gsl.py` — S2 GSL (REJECTED).
- `train_gae_compact.py` + `gae_compact/` ckpt — S3 compactness (NEGATIVE).
REPO CODE (unchanged pipeline): `gae_joint.py`, `lstm_temporal.py`, `retrain_io.py`, `train_gae_joint.py`,
`ensemble_recipe.py`, `cpd_pipeline_v14.py`, `szcore_eval.py`, `evaluation_protocol.py`,
`fp_budget_operating_point.py`, `build_ens.py`, `score_ens.py`.

---

## 9 · WORKING RULES (carry over)
- Researcher/mentor role; propose with paper grounding; user decides; no autonomous action.
- Vietnamese replies; code/English deliverables in English. Concise; verdict + next action + command.
- User runs all GPU on Kaggle; local CPU (Cursor, `F:/Study/Thesis/Code`) for numpy/scoring.
- Fail-fast precheck cell before any long run (12h Kaggle timeout; save-version = rerun from scratch).
- Archive-don't-delete; reproduce numbers before reporting; state hypothesis + falsification up front.
- Web demo (SzScan) governed separately by WEB_DEMO_SPEC — do NOT mix §0 numbers into demo UI.
