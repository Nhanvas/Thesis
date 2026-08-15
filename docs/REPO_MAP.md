# REPO_MAP — hiện trạng repo sau lock baseline v3.1 (nguồn DUY NHẤT: folder nào có gì)

**Cập nhật:** 2026-08-15 · sau reorg (archive pre-rebuild + round-1 + early-attribution + retired repro-lock).
**Nhãn:** `CANONICAL` (đang dùng/cite) · `ARCHIVE` (`results/history_superseded/` hoặc `archive/`, không cite) · `EXTERNAL` (ngoài repo, script cần).

---

## A. CANONICAL — dùng/cite cái này

| Path | Vai trò |
|---|---|
| `docs/REBUILD_BASELINE_LOCK.md` | **Số + method + rationale rebuild — đọc trước tiên** |
| `docs/RESULTS_OF_RECORD.md` §0 | Baseline-of-record (report §0; §1–§16 = history) |
| `docs/ATTRIBUTION_SPEC.md` | Định nghĩa attribution (per-node recon-z, MAP@K) |
| `results/retrain_v3p1/` | **BASELINE grids + OP** (`final_eval_seed42.csv`, `fp_budget_locked.csv`, `fp_budget_val_verdict.json`, `ens/`, `val_ens/`, `dec19/` = A0) |
| `results/attribution_v5/labels/` | Attribution HIỆN HÀNH (`labels_*_FINAL.csv`, `rank_per_seizure.csv`) — nhãn AI-draft, chờ cô freeze |
| `data/models_retrain/` | Checkpoint v3.1 canonical: `gae_joint_seed42.pt` + `lstm_temporal_seed{42,1,2,3,4}.pt` |
| `data/models/best_model_joint_lambda01.pt` | GAE joint gốc (17.1KB, có x_decoder) |
| `data/processed/`, `data/splits/` | Input processed + split cố định (seed 42) |
| `src/` (flat) | Code active — chạy `python src/<name>.py` từ root (flat-import) |
| `src/retrain/` | Chuỗi v3.1: `gae_joint · lstm_temporal · train_lstm_temporal_v3 · build_ens · build_seed_ensemble · score_ens · fp_budget_operating_point · derive_weights · retrain_io · aggregate_final` |
| `src/dataprep/` | `preprocessing · graph_construction · feature_extraction · compute_gamma_aec · create_splits` |
| `src/` (đã gom từ root) | `attribution_gae_pernode · attribution_detail · compare_labels_pernode · validate_dominant_hitk_FINAL · label_eeg_pilot · dump_components` |
| `seizure_segments/`, `topo_features/` | Raw + ảnh cho attribution labeling (cân nhắc gitignore nếu repo phình) |

**Chuỗi inference cho web demo (đầu→cuối):**
`src/dataprep/{preprocessing→graph_construction→feature_extraction→compute_gamma_aec}` → `src/retrain/gae_joint` (encode Z) → `src/retrain/lstm_temporal` (temporal) → gamma → `src/ensemble_recipe.build_ensemble` (equal 1/3) → `src/cpd_pipeline_v14` (PELT) → `src/retrain/fp_budget_operating_point` (OP label-free).

---

## B. ENSEMBLE WEIGHT (single-source) — đã khớp baseline

`src/ensemble_recipe.py` → `ENS_WEIGHTS = (0.3334, 0.3333, 0.3333)` (equal). Khớp `ens_weights.json` trong mọi folder `retrain_v3p1/*`. **Đừng đổi về `1/3` chính xác** (sẽ buộc build lại). Weight cũ `(0.40,0.35,0.25)` = retired (test-tuned §13).

---

## C. ARCHIVE — KHÔNG cite (đã dời, còn trong git history)

| Path | Là gì |
|---|---|
| `results/history_superseded/2026-08-14_rebuild_round1/` | `retrain/` (round-1 znorm-bug) + `retrain_normfix/` (40ep) + `attrib_w403525/` (seed42 @ w403525, round-1 era) |
| `results/history_superseded/pre_rebuild_detection/` | `cpd/ · phaseB/ · phaseB_newweight/ · phaseA_appendix/ · figures/ · logs/ · locked/` — nguồn §1–§14 (số 0.750/0.829 đã đưa cô) |
| `results/history_superseded/pre_rebuild_detection/attribution_v3/` + `attribution/` | Attribution khung CŨ (Gini/eigencentrality, consistency/lateralization) — thay bởi `attribution_v5` |
| `data/processed/_superseded_components_retrain_round1/` | Components round-1 (08-13, không phải v3.1) |
| `results/history_superseded/{2026-07-25, oldweight_ens_scores}/` | Cache old-weight, grid cũ (đã có sẵn từ trước) |
| `results/history_topology/` | Topology extension đã bác (A.5) |
| `archive/` | Code superseded: `scaffolding/`, `rejected/`, `cpd_history/`, `probes_old/`, `attribution_superseded/`, **`fp_reduction_prior/`** (Decision #24 bác), **`orphan_best_model_20260509.pt`**, **`thesis_repro_lock.py`** (reproduce số RETIRED; đã hỏng do assert weight cũ) |

---

## D. EXTERNAL DEPENDENCIES (ngoài repo — clone máy mới cần)

| Path / nguồn | Dùng cho |
|---|---|
| `F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary/` (`chb*-summary.txt`) | `score_ens.py --summary_dir`, `szcore_eval` dựng timeline seizure |
| CHB-MIT EDF gốc (PhysioNet) | preprocessing từ EDF (chỉ khi chạy lại từ đầu) |
| Kaggle datasets (`nhn2mm`, `norncreades/thesis-code-fix`): graph/feature `_topk20`, gamma, GAE+LSTM `.pt` | build_ens / train trên Kaggle GPU |
| Graphs 32.9GB | **gitignored** — không trong repo |

---

## E. TÊN TRÙNG — quy tắc (trùng TÊN ≠ trùng NỘI DUNG)

- `final_eval_seed42.csv`: `retrain_v3p1/` (baseline) ≠ `retrain_v3p1/dec19/` (A0, weight cũ) ≠ `retrain_v3p1/val/` (VAL) — **3 bản khác nội dung, giữ cả 3**. Bản trong `history_superseded/` = archive.
- Các CSV pre-rebuild trùng tên khác (`locked_phaseA_event_results`, `szcore_event_level_*`, `eval_*`, `event_ablation_*`) → đã dồn vào `history_superseded/`. Không còn bản active nào.

---

## F. VIỆC CÒN NGỎ (không gấp)
- `src/repro_lock_v3p1.py` (chưa có): viết sau — assert equal-weight + reproduce §0 (0.632/0.776) từ 5 `.pt`, để giữ claim "reproducible from clean clone" cho baseline mới.
- Cân nhắc gitignore `seizure_segments/*_raw.npy` + `results/attribution_v5/labels/*.png` nếu repo nặng.
