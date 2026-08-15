# Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG
### using Graph Autoencoder and Change Point Detection

**Student:** Nguyen Quoc Trung Nhan (BEBEIU22184) · **Supervisor:** Hà Thị Thanh Hương (Assoc. Prof.)

**Status:** Detection pipeline **REBUILT and BASELINE LOCKED (2026-08-14, v3.1)**. The rebuild removed
test-set tuning of the ensemble weight/operating-point and fixed a train/eval normalization bug in the
temporal branch; every stage is now reproducible from a clean clone and callable for inference on a new
recording (web demo). **Report the §0 numbers only.** Everything pre-rebuild (`RESULTS_OF_RECORD.md`
§1–§16) is history. Active phase = report writing + attribution freeze (pending supervisor) + web demo,
over the locked baseline.

> Numbers + method + rationale: `docs/REBUILD_BASELINE_LOCK.md` and `docs/RESULTS_OF_RECORD.md` §0.
> Where files live: `docs/REPO_MAP.md`. Attribution: `docs/ATTRIBUTION_SPEC.md`.
> If this README disagrees with `RESULTS_OF_RECORD.md` §0 on a number, **§0 wins.**

---

## ⚠️ Read before touching any code

1. **Ensemble weight lives in exactly ONE place: `src/ensemble_recipe.py` (`ENS_WEIGHTS`).** Current
   value: **`(0.3334, 0.3333, 0.3333)` (equal — uninformative prior)**. The old `(0.40,0.35,0.25)` was
   **test-selected (§13) and is retired** — do not restore it as production.
2. **Detection algorithm lives in exactly ONE place: `src/cpd_pipeline_v14.py`.** Evaluation and the
   web-demo export both call it. Do not re-implement PELT elsewhere.
3. **Authoritative scorer = `timescoring`.** Any new harness must reproduce the locked baseline:
   balanced **0.632 @ 38.6 FP/day** (mag70/pen0.5), high-sens **0.776 @ 72.7** (mag55/pen0.3). Rebuild
   path: `src/retrain/build_ens.py` (equal weight) → `src/retrain/score_ens.py` →
   `src/retrain/fp_budget_operating_point.py`.
4. **Never tune on the 8 test subjects.** Derive on non-test; report test once. (The retired 0.750/0.829
   came from weight+OP selected on test — the exact mistake this rebuild corrects.)
5. **Single model = canonical seed 42.** The deep 5-seed mean is dropped (it dilutes anomaly peaks;
   underperforms the canonical seed at event level). Report 5-seed spread only as a stability caveat.
6. **GPU (Kaggle) is not bit-reproducible.** Use one self-consistent component set per analysis;
   relative deltas (ablations) stay valid across drift, absolute numbers do not. Checkpoints in
   `data/models_retrain/` are authoritative.
7. **Decision #24 (CUSUM FP-persistence filter) = TESTED and REJECTED**, not in the pipeline
   (`archive/fp_reduction_prior/` is the rejection record only).

---

## Two environments

Hard split: **CPU analysis** (this repo — evaluation, statistics, attribution, CPD) vs **GPU
training/export** (Kaggle notebooks that produce GAE/LSTM/gamma component z-scores this repo consumes).
The CPU side never needs `torch`.

| Environment | Installs from | Used for |
|---|---|---|
| **CPU (local / Cursor)** | `requirements.txt` | `src/` (PELT detection, SzCORE scoring, stats, attribution, weight/OP derivation, demo backend) |
| **GPU (Kaggle)** | `requirements-kaggle.txt` | GAE + LSTM + gamma inference + component export (`src/retrain/build_ens.py`, `train_lstm_temporal_v3.py`) |

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# run everything from the repo ROOT (flat imports + data/ paths resolve):
python src/retrain/score_ens.py --ens_dir results/retrain_v3p1/ens --seed 42 \
    --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary" --out_dir results/retrain_v3p1
```

> **External dep:** `--summary_dir` must point at the CHB-MIT summary files
> (`F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary/`). Graphs (32.9 GB) are gitignored.

---

## Repository layout (post-reorg)

```
.
├── src/                         # ACTIVE code (flat; run as `python src/<name>.py` from root)
│   ├── ensemble_recipe.py       #   SINGLE SOURCE: ensemble weight (equal) + build_ensemble()
│   ├── cpd_pipeline_v14.py      #   SINGLE SOURCE: detection (PELT + magnitude filter)
│   ├── szcore_eval.py · evaluation_protocol.py · stat_validation.py
│   ├── attribution_gae_pernode.py · attribution_detail.py · compare_labels_pernode.py
│   ├── validate_dominant_hitk_FINAL.py · label_eeg_pilot.py · dump_components.py · edf_index.py
│   ├── retrain/                 #   v3.1 chain: gae_joint, lstm_temporal, train_lstm_temporal_v3,
│   │                            #     build_ens, build_seed_ensemble, score_ens,
│   │                            #     fp_budget_operating_point, derive_weights, retrain_io, aggregate_final
│   └── dataprep/                #   preprocessing → graph_construction → feature_extraction → compute_gamma_aec → create_splits
│
├── docs/                        # governance (authoritative)
│   ├── REBUILD_BASELINE_LOCK.md #   ★ locked method + numbers + rebuild rationale — READ FIRST
│   ├── RESULTS_OF_RECORD.md     #   §0 = baseline-of-record; §1–§16 = history
│   ├── REPO_MAP.md              #   where every file lives + status
│   ├── ATTRIBUTION_SPEC.md · WEB_DEMO_SPEC.md · TIEU_CHI_LABEL_dominant_channel_v2.md
│   ├── PREREG_0{1..4}.md · Proposed_solution_updated_v5.md
│   └── MASTER_HANDOFF_v2.md · NEXT_TASKS_AND_PLAN.md   (onboarding + plan)
│
├── notebooks/kaggle_gpu/        # GPU notebooks
├── data/
│   ├── models_retrain/          #   v3.1 checkpoints (GAE seed42 + LSTM ×5) — CANONICAL
│   ├── models/best_model_joint_lambda01.pt   #   joint GAE (gốc)
│   └── processed/ · splits/     #   components + fixed split (graphs gitignored)
├── results/
│   ├── retrain_v3p1/            #   ★ BASELINE-OF-RECORD (grids, fp_budget, ens/, val_ens/, dec19/=A0)
│   ├── attribution_v5/          #   attribution hiện hành (labels + rank_per_seizure)
│   ├── history_superseded/      #   pre-rebuild + round-1 + early-attribution — DO NOT cite
│   └── history_topology/        #   rejected topology extension
├── archive/                     # superseded code (+ fp_reduction_prior, thesis_repro_lock, orphan checkpoint)
├── seizure_segments/ · topo_features/   # attribution labeling raw/figures
└── requirements.txt · requirements-kaggle.txt · README.md
```

---

## Locked headline numbers (baseline-of-record — verify against `RESULTS_OF_RECORD.md` §0)

- **Ensemble weight:** `(recon, temporal, gamma) = (1/3, 1/3, 1/3)` · **model:** canonical seed 42.
- **Balanced (primary):** sensitivity **0.632** [0.519, 0.731], FP/day **38.6** (shared mag70/pen0.5).
- **High-sensitivity:** sensitivity **0.776** [0.671, 0.855], FP/day **72.7** (shared mag55/pen0.3).
- **Window-tier macro AUROC:** **0.775** · **seed stability:** 5-seed VAL AUROC 0.648 ± 0.011.
- **Baselines:** exceeds Yildiz 2022 unsupervised CHB-MIT AUROC 0.68. The 0.765/40.6 SzCORE
  Transformer figure is **TUH**, not CHB-MIT — never cite as comparable.
- **Retired (do NOT report):** pre-rebuild 0.750 / 0.829 (weight+OP test-selected; components lost).

---

## Where to start in a new session

1. `docs/REBUILD_BASELINE_LOCK.md` (method + numbers + why the rebuild) → `RESULTS_OF_RECORD.md` §0.
2. `docs/REPO_MAP.md` (where files live) · `docs/ATTRIBUTION_SPEC.md` (attribution).
3. Do not re-derive locked results; do not cite §1–§16 numbers.
