# REPO_MAP — where every file lives (post Phase-C reorg)
**Replaces the pre-Phase-C version of this file.** If a path below doesn't exist yet in a given
checkout, it reflects where things *should* go per the locked convention — check `PROJECT_STATUS.md`
for what's actually been executed vs. pre-registered-but-not-run (Phase D).

---

## Top-level layout

```
.
├── src/                          # ACTIVE code (flat within each subfolder; run as `python src/<name>.py`)
│   ├── ensemble_recipe.py        #   SINGLE SOURCE: ensemble weight (equal 1/3) + build_ensemble()
│   ├── cpd_pipeline_v14.py       #   SINGLE SOURCE: detection algorithm (PELT + magnitude filter + optional slope-gate/smoother, both default OFF)
│   ├── retrain_io.py             #   shared helpers: robust_z, window_auroc, checkpoint/data discovery
│   ├── gae_joint.py              #   GAE model class (single-relation — the ONE used by rlg)
│   ├── latent_anomaly.py         #   latent-Mahalanobis readout (THE core of rlg's zlatent branch)
│   ├── lstm_temporal.py, train_lstm_temporal_v3.py   # LSTM branch — DROPPED from rlg, kept as historical/methodological record (Amendment A1)
│   ├── build_ens.py, build_seed_ensemble.py, score_ens.py, fp_budget_operating_point.py, derive_weights.py
│   │                              #   PREREG 01-04 chain: build components → CPD grid → SzCORE scoring → weight/OP derivation
│   ├── build_ens_tier2.py        #   Tier-2/Phase-C variant of build_ens (supports rlg / rg / lg / rlg-lg subsets)
│   ├── attribution_gae_pernode.py, attribution_detail.py, compare_labels_pernode.py, label_eeg_pilot.py
│   │                              #   attribution pipeline (per-node GAE recon-z; MUST point at gae_joint_seed42.pt, not the C4-full multirel checkpoint)
│   └── dataprep/                 #   preprocessing.py → graph_construction.py → feature_extraction.py → create_splits.py
│
├── docs/                         # governance (authoritative)
│   ├── PROJECT_STATUS.md         #   ★★ READ FIRST — current phase, deadlines, what's active
│   ├── RESULTS_OF_RECORD_phaseB.md  #   ★★ THE single source of truth for every locked number (§1-§9)
│   ├── PHASE_C_FULL_AUDIT.md     #   detailed reasoning trail behind every Phase-C verdict (companion to RESULTS §8-9)
│   ├── PHASE_D_HANDOFF.md        #   Phase-D hypothesis + staged plan + why it was NOT executed
│   ├── LOCKED_METRICS_REFERENCE.md  #   flat table reference for every locked CSV-level number (grid cells, per-seed, per-subject)
│   ├── REPO_MAP.md               #   this file
│   ├── ATTRIBUTION_SPEC.md       #   channel-attribution spec (locked method, PROVISIONAL results)
│   ├── WEB_DEMO_SPEC_v4.md       #   ★ wins on any web-demo conflict
│   ├── WEB_DEMO_CONTEXT_BOUNDARY.md  #   which files are "demo" vs "thesis/evaluation" — do not cross-contaminate
│   ├── WEB_DEMO_DESIGN_SYSTEM.md #   visual design tokens for the demo
│   ├── THESIS_REPORT_WRITING_GUIDE.md, RUBRIC_TRACKING.md, Report_format.md, Thesis_Registration_Form.md
│   │                              #   report-writing structure/style + rubric checklist + formal format rules
│   ├── PREREG_01_GAE_joint_retrain.md, PREREG_02_LSTM_temporal.md, PREREG_03_weights_final.md, PREREG_04_fp_budget_operating_point.md
│   │                              #   original architecture/weight/OP pre-registrations (still the legal basis for the current design)
│   ├── PREREG_TIER2_amendment_A1.md   #   the LSTM-drop / latent-readout-promotion decision (rlg's origin)
│   ├── PHASE_C_FINAL_HANDOFF.md, PHASE_C_CLOSEOUT_provenance.md   #   Phase-C closure documents (paste-in provenance blocks)
│   ├── S2_S3_negatives.md        #   Phase-B representation-search negative results (precedent for any future architecture change)
│   ├── Literature_Review_and_Novelty_Assessment...md, Lit_review.txt, Spatial_Localization...md
│   │                              #   literature review raw material (compress into report shape per writing guide §2)
│
├── notebooks/kaggle_gpu/         # GPU training notebooks (GAE, LSTM, C4-full multi-relational GAE)
├── data/
│   ├── models_retrain/           #   gae_joint_seed{42,1,2,3}.pt (rlg — CANONICAL), lstm_temporal_seed{42,1,2,3,4}.pt (historical),
│   │                              #   gae_multirel_seed42.pt (Phase-C C4-full — TESTED, KILLED, do not use downstream)
│   └── processed/ · splits/      #   components + fixed split (graphs gitignored, 32.9 GB local only)
├── results/
│   ├── phaseB/tier2/             #   ★ rlg provenance: ens_val_tf/, ens_test_tf/, {rlg,rg,lg}/ VAL grids, {rlg,lg}_test/ TEST grids
│   ├── phaseC/                   #   C4-lite (build_te_branch outputs), C4-full (stage0/stage1 verdicts, train logs), artifact-gate, slope-gate seed-check
│   ├── retrain_v3p1/              #   the rebuild-baseline (§0) grids — historical comparator only
│   ├── attribution_v6/            #   current attribution execution (ictal-set labels, once frozen)
│   ├── attribution_v5/            #   superseded attribution (dominant-channel/MAP@K) — archive, don't cite
│   └── history_superseded/       #   pre-rebuild + round-1 + early-attribution — DO NOT cite
├── archive/                      # superseded code + rejection records (fp_reduction_prior, S2/S5 GSL code, etc.)
├── seizure_segments/ · topo_features/   # attribution labeling raw/figures
└── requirements.txt · requirements-kaggle.txt · README.md
```

---

## Two environments (unchanged discipline)

| Environment | Installs from | Used for |
|---|---|---|
| **CPU (local / Cursor)** | `requirements.txt` | `src/` (PELT detection, SzCORE scoring, stats, attribution scoring, weight/OP derivation, demo backend) |
| **GPU (Kaggle)** | `requirements-kaggle.txt` | GAE + LSTM + gamma inference + component export; C4-full multi-relational training (Phase C, closed) |

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# run everything from the repo ROOT:
python src/score_ens.py --ens_dir results/phaseB/tier2/ens_test_tf --seed 42 \
    --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary" --out_dir results/phaseB/tier2
```

---

## Quick-lookup: "I need to..."

| Task | Read first | Then |
|---|---|---|
| Know the current locked numbers | `RESULTS_OF_RECORD_phaseB.md` §1–§9 | `LOCKED_METRICS_REFERENCE.md` for CSV-level detail |
| Understand why a Phase-C lever was rejected | `RESULTS_OF_RECORD_phaseB.md` §8–9 (verdict) | `PHASE_C_FULL_AUDIT.md` (full reasoning) |
| Write the report | `THESIS_REPORT_WRITING_GUIDE.md` | `RUBRIC_TRACKING.md` for exact numbers per section |
| Run/extend attribution | `ATTRIBUTION_SPEC.md` | ensure checkpoint = `gae_joint_seed42.pt`, never `gae_multirel_seed42.pt` |
| Build/extend the web demo | `WEB_DEMO_SPEC_v4.md` (wins on conflict) | `WEB_DEMO_DESIGN_SYSTEM.md`, `WEB_DEMO_CONTEXT_BOUNDARY.md` |
| Consider a new optimization idea | `PROJECT_STATUS.md` §6 (what NOT to re-propose) | `PHASE_C_FULL_AUDIT.md` to check it wasn't already tested |
| Understand why Phase D wasn't run | `PHASE_D_HANDOFF.md` | — |
| Onboard a new chat from scratch | `PROJECT_STATUS.md` §7 | branches from there by task |

**Do not cite:** anything under `results/history_superseded/` or `results/attribution_v5/`; the old
`RESULTS_OF_RECORD.md` (pre-rebuild, superseded — retired); `REBUILD_BASELINE_LOCK.md` (superseded by
`RESULTS_OF_RECORD_phaseB.md`); `PROVENANCE_MAP.md`, `PLAN_AND_STATUS.md`, `MASTER_HANDOFF_v2.md`,
`NEXT_TASKS_AND_PLAN.md` (all retired, replaced by `PROJECT_STATUS.md`).
