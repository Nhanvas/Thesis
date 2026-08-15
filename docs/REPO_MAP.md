# REPO_MAP — folder nào có file nào + trạng thái (nguồn DUY NHẤT để onboard/dọn)

**Generated:** 2026-08-15 · từ `_project_audit/00_overview.md` (cây tươi, 1157 file) + delta rebuild v3.1.
**Nhãn:** `KEEP` (canonical/active) · `ARCHIVE` (superseded NHƯNG là provenance của số/decision từng báo cáo → `results/history_superseded/`, không xoá) · `DELETE` (scratch/trùng-y-hệt/chết, xoá hẳn) · `VERIFY` (phải mở xem trước khi quyết).
**Nguyên tắc vàng (Boti):** trùng TÊN ≠ trùng NỘI DUNG — luôn phân loại theo **folder**. Provenance của số đã đưa cô thì ARCHIVE, không DELETE.

---

## A. VAI TRÒ TỪNG FOLDER (mặc định nhãn cho file bên trong)

| Folder | Vai trò | Nhãn mặc định |
|---|---|---|
| `results/retrain_v3p1/` | **BASELINE-OF-RECORD** (v3.1: equal-weight, seed42, FP-budget OP) | **KEEP** |
| `data/models_retrain/` | Checkpoint v3.1 canonical (GAE seed42 + LSTM ×5) | **KEEP** |
| `src/` (core) + `src/retrain/` + `src/dataprep/` | Code active, chuỗi inference đầu→cuối | **KEEP** |
| `src/attribution*` / `results/attribution`, `results/attribution_v5` | Attribution ACTIVE (per-node recon-z, MAP@K) | **KEEP** |
| `data/processed/{components, temporal_zscores}`, `data/splits/` | Input processed + split cố định | **KEEP** |
| `docs/` | Governance + reference | **KEEP** (trừ file lỗi thời, §E) |
| `results/history_superseded/` (249 file) | Đã archive sẵn (round-1, 2026-07-25, oldweight...) | **KEEP as archive** (không cite) |
| `archive/` (81 file) | Đã archive sẵn (scaffolding, rejected, cpd_history...) | **KEEP as archive** |
| `results/{cpd, phaseB, phaseB_newweight, phaseA_appendix, locked, figures}` | Kết quả **pre-rebuild** (nguồn §1–§14, số 0.750/0.829 đã đưa cô) | **ARCHIVE** (§F) |
| `results/attrib_w403525/` | Eval ở weight 0.40/0.35/0.25 (trùng tên round-1) | **VERIFY→ARCHIVE** (§C) |
| `results/logs/` (44 file, April) | Log train GAE cũ (`model_info.json`×17, `results.json`×8) | **ARCHIVE** (provenance GAE) |
| `results/attribution_v3/` (25) | Attribution bản cũ (v5 là bản hiện hành?) | **VERIFY→ARCHIVE** |
| `results/history_topology/` (17) | Topology extension đã bác (A.5) | **KEEP as archive** |
| `src/fp_reduction_prior/` (7) | FP-filter (Decision #24, TESTED & REJECTED) | **ARCHIVE** |
| `data/processed/_superseded_components_retrain_round1/` | Components round-1 (đã đổi tên hôm nay) | **KEEP as archive** |
| `seizure_segments/` (229, 162MB) + `topo_features/` (16) | Ảnh/raw cho attribution labeling | **KEEP** (cân nhắc gitignore, §H) |

---

## B. EXTERNAL DEPENDENCIES (không nằm trong repo — script CẦN, ghi để clone máy mới chạy được)

| Path / nguồn | Dùng cho |
|---|---|
| `F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary/` (`chb*-summary.txt`) | `score_ens.py --summary_dir`, `szcore_eval` dựng timeline seizure (SzCORE) |
| CHB-MIT EDF gốc (PhysioNet) | preprocessing đầu vào (chỉ khi chạy lại từ EDF) |
| Kaggle datasets: graph/feature `_topk20`, gamma, GAE+LSTM checkpoints (`nhn2mm`, `norncreades/thesis-code-fix`) | build_ens / train trên Kaggle GPU |

> Ghi rõ trong README: pipeline cần `--summary_dir` trỏ đúng path trên; graphs 32.9GB **gitignored** (không trong repo).

---

## C. FILE TRÙNG TÊN — phân loại THEO FOLDER (phần rủi ro nhất)

**`final_eval_seed42.csv` (5 bản — 3 bản v3p1 KHÁC NỘI DUNG, giữ cả 3):**
| Path | Nội dung | Nhãn |
|---|---|---|
| `results/retrain_v3p1/final_eval_seed42.csv` | test grid, equal-weight — **baseline** | **KEEP (canonical)** |
| `results/retrain_v3p1/dec19/final_eval_seed42.csv` | test grid, weight 0.40/0.35/0.25 — **A0** | **KEEP** (provenance A0) |
| `results/retrain_v3p1/val/final_eval_seed42.csv` | VAL grid (chb10/11/22) — PREREG_04 | **KEEP** |
| `history_superseded/2026-08-14_rebuild_round1/retrain/…` | round-1 buggy | KEEP as archive |
| `history_superseded/2026-08-14_rebuild_round1/retrain_normfix/…` | normfix-40ep | KEEP as archive |

**`final_eval_{window_auroc,multiseed,persubject,locked}.csv` (2 bản mỗi tên):** một ở `attrib_w403525/`, một ở `history_superseded/.../retrain/`. → bản history = archive; **`attrib_w403525/` = VERIFY** (weight-0.40 attribution eval; nếu không còn dùng cho attribution hiện hành → ARCHIVE cùng pre-rebuild).

**`final_eval_seed99.csv` (3):** `retrain_v3p1/` = **KEEP** (deep-mean, đã supersede nhưng là bằng chứng "deep-mean tệ hơn"); 2 bản trong history = archive.

**`locked_phaseA_event_results.csv` (3):** `cpd/evaluation/`, `locked/`, `phaseB_newweight/` — **tất cả pre-rebuild → ARCHIVE** (nguồn §1). Giữ 1 bản canonical-lịch-sử (khuyến nghị bản `locked/`), 2 bản kia là copy lạc chỗ → gộp về archive.

**`szcore_event_level_mag60/mag70.csv`, `event_ablation_*.csv`, `window_event_gap.csv`, `szcore_summary_macro.csv`:** đa số đã nằm trong `history_superseded/2026-07-25/…` (archive rồi); bản còn ngoài ở `phaseB_newweight/` → **ARCHIVE** (dồn về history).

**`best_model.pt` (6) / `model_weights.pt` (3):** 5–3 bản trong `archive/scaffolding/checkpoints/` (smoke/E5 — đã archive, KEEP-as-archive). **`results/best_model.pt` (lạc ở root results) = VERIFY**: nếu trùng `data/models/best_model_joint_lambda01.pt` → DELETE; nếu là checkpoint khác → chuyển `data/models_history/`.

**`model_info.json` ×17 / `results.json` ×8:** đều trong `results/logs/<timestamp>/` (log train GAE April) — **ARCHIVE cả cụm** (`results/logs/` → history).

---

## D. FILE `.py` LẠC Ở ROOT REPO → gom về `src/` (đúng quy ước code-in-src)

| File | Vai trò | Chuyển về |
|---|---|---|
| `attribution_detail.py` | attribution | `src/attribution/` |
| `compare_labels_pernode.py` | attribution (so nhãn) | `src/attribution/` |
| `validate_dominant_hitk_FINAL.py` | attribution (MAP@K validate) | `src/attribution/` |
| `label_eeg_pilot.py` | attribution (labeling tool) | `src/attribution/` |
| `dump_components.py` | dump component arrays | `src/tools/` |
| `project_inventory.py` | audit tool (đã dời `_project_audit/`) | giữ ở `_project_audit/` |

Đồng thời gom trong `src/` (nếu muốn gọn): `attribution_gae_pernode.py` → `src/attribution/`; `edf_index.py`, `consolidate_outputs.py` → `src/tools/`; `mag_pen_grid_sweep_v2.py`, `rebuild_ensemble_new_weight.py`, `weight_*.py`, `window_tier_newweight.py`, `eval_multiseed.py` (provenance one-offs pre-rebuild) → `src/_superseded/` hoặc `archive/`.

---

## E. DELETE THẲNG (scratch/chết — không phải provenance của số nào)

| Path | Lý do |
|---|---|
| `scan_out.txt` (root, 34KB) | Output scan cũ, đã thay bằng `_project_audit/` |
| `Dockerfile`, `entry.sh`, `Makefile` (root, 0B) | File rỗng, chưa dùng (giữ lại cũng vô hại — DELETE tuỳ ý) |
| `src/thesis_repro_lock.py` → **KHÔNG delete** | Nó reproduce số **retired 0.750/0.829** → **giữ + đánh dấu HISTORICAL** trong docstring (đừng để ai tưởng verify baseline mới) |

> Ngoài ra: bản **copy lạc chỗ** của các CSV pre-rebuild (khi đã có 1 bản canonical trong `locked/` hoặc đã archive) → DELETE bản thừa. Nhưng chỉ sau khi xác nhận nội dung trùng (VERIFY từng cặp trước khi xoá).

---

## F. ARCHIVE (superseded nhưng là provenance — dồn về `results/history_superseded/pre_rebuild_detection/`)

`results/cpd/`, `results/phaseB/`, `results/phaseB_newweight/`, `results/phaseA_appendix/`, `results/locked/`, `results/figures/`, `results/logs/`, `results/attrib_w403525/` (sau VERIFY), `results/attribution_v3/` (sau VERIFY), `src/fp_reduction_prior/`.

> Đây là nguồn của §1–§14 (số 0.750/0.829 đã đưa cô) + log train GAE + FP-filter bác bỏ → **giữ làm bằng chứng, không xoá**.

---

## G. CẤU TRÚC ĐÍCH (gom theo mục đích — đề xuất)

```
src/
  (core)      ensemble_recipe · cpd_pipeline_v14 · szcore_eval · evaluation_protocol · stat_validation
  retrain/    (v3.1 chain — CANONICAL)
  dataprep/   preprocess→graph→feature→gamma→splits
  attribution/ attribution_gae_pernode + 4 script attribution từ root
  tools/      dump_components · edf_index · consolidate_outputs
  _superseded/ provenance one-offs (mag_pen_grid_v2, weight_*, rebuild_ensemble_new_weight, fp_reduction_prior)
results/
  retrain_v3p1/   ← GIỮ NGUYÊN TÊN (RoR §0 + REBUILD_BASELINE_LOCK trỏ vào đây; đổi tên = phải sửa pointer)
  attribution/ + attribution_v5/
  history_superseded/
     ├── 2026-08-14_rebuild_round1/   (đã có)
     ├── 2026-07-25/ , oldweight_ens_scores/  (đã có)
     └── pre_rebuild_detection/       (MỚI: cpd, phaseB*, phaseA_appendix, locked, figures, logs, attrib_w403525)
data/
  models_retrain/ (v3.1) · models/ (GAE gốc) · processed/ · splits/
```

`retrain_v3p1` **không đổi tên** để khỏi vỡ pointer — caution > cosmetic. Nếu sau muốn tên đẹp hơn, đổi kèm sửa `RoR §0` + `REBUILD_BASELINE_LOCK.md` trong cùng 1 commit.

---

## H. CANONICAL QUICK-REF (mở nhanh khi cần)

- **Số báo cáo:** `docs/REBUILD_BASELINE_LOCK.md` + `RESULTS_OF_RECORD.md` §0.
- **Grid baseline:** `results/retrain_v3p1/final_eval_seed42.csv`; **OP:** `fp_budget_locked.csv`.
- **Checkpoint chạy inference:** `data/models_retrain/lstm_temporal_seed42.pt` + `gae_joint_seed42.pt`.
- **Chuỗi code demo:** `src/dataprep/*` → `src/retrain/gae_joint.py` → `lstm_temporal.py` → `build_ens.py` → `src/cpd_pipeline_v14.py` → `fp_budget_operating_point.py`.
- **Gitignore cân nhắc:** `seizure_segments/*_raw.npy` (162MB) + `results/attribution_v5/labels/*.png` nếu repo phình.

---

## I. CẦN VERIFY trước khi chốt script reorg (mở 1 file/cặp là xong)
1. `results/attrib_w403525/*` — còn dùng cho attribution hiện hành không? (nếu không → ARCHIVE)
2. `results/attribution_v3/` vs `attribution_v5/` — v3 đã bị v5 thay hẳn chưa?
3. `results/best_model.pt` — có trùng `data/models/best_model_joint_lambda01.pt` không? (trùng → DELETE)
4. Các cặp CSV pre-rebuild trùng tên (locked_phaseA…, window_event_gap…) — nội dung có y hệt để DELETE bản thừa, hay khác để giữ?
