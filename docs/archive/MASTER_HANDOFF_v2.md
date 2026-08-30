# MASTER HANDOFF v2 — bản onboarding DUY NHẤT cho chat/Project mới
*Đọc hết trước khi hành động. Cập nhật 2026-08-15 sau khi lock baseline v3.1 + reorg repo.*

Vai trò assistant kế tiếp: **research director kiểu Stanford/MIT** — sở hữu mạch narrative khoa học.
Boti (Nguyen Quoc Trung Nhan, BEBEIU22184) là **người quyết cuối**; chạy trên Kaggle (GPU) + Cursor
(`F:/Study/Thesis/Code`, git, `main`, `github.com/Nhanvas/Thesis`) và dán output về. Chat **tiếng Việt**;
code/deliverable/governance **tiếng Anh**.

Kỷ luật: rigour > tốc độ; pre-register (giả thuyết + tiêu chí bác bỏ) trước khi chạy; **KHÔNG BAO GIỜ tune
trên 8 subject test**; báo cáo as-is (âm/một phần thì nói thẳng); **archive-not-delete** (`git mv`/`mv` +
git, không hard-delete cái là provenance). **Đọc method/docs trước khi đề xuất — đừng suy từ trí nhớ.**

**Deadline:** IELTS 9/10 · nộp 15/10 · defense 2–3/11. Khi hụt thời gian: **viết > demo > thí nghiệm thêm**.

---

## 0. TRẠNG THÁI NGAY LÚC NÀY

**Detection pipeline = REBUILD XONG, BASELINE ĐÃ KHÓA (2026-08-14, v3.1).** Không còn "hai lớp số".
Chỉ MỘT bộ số chính thức, ở `RESULTS_OF_RECORD.md` **§0** + `docs/REBUILD_BASELINE_LOCK.md`.

- Rebuild **bỏ test-tuning** (weight + operating-point bản cũ được chọn trên 8 test subject, §13) và **sửa
  bug normalization** ở nhánh LSTM (train trên znorm-Z nhưng chấm trên raw-Z). Kết quả honest **thấp hơn**
  số cũ nhưng **tái lập được từ clone sạch** và code đủ đầu→cuối cho web demo.
- **§1–§16 của RESULTS_OF_RECORD = LỊCH SỬ, KHÔNG báo cáo.** Số retired 0.750/0.829 là test-tuned +
  components đã mất → không tái lập (A0 xác nhận: weight cũ trên components rebuild chỉ ~0.63–0.645).
- **Cô CHƯA được brief** về headline thấp hơn. Khung khi nói với cô: "phát hiện test-leakage + bug ở
  pipeline cũ; sửa cả hai; số honest thấp hơn nhưng bảo vệ được và tái lập được." → **gate trước Giai đoạn B.**
- **Attribution:** redefine & khóa (per-node recon-z, MAP@K); kết quả PROVISIONAL, chờ **nhãn blind của cô**.
  Nguồn: `ATTRIBUTION_SPEC.md`. Không bị ảnh hưởng bởi rebuild detection.

---

## 1. THESIS IDENTITY (immutable)
- **Title:** *Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder and Change Point Detection.*
- **Student/Supervisor/School:** Nguyen Quoc Trung Nhan (BEBEIU22184) / Hà Thị Thanh Hương / BME, IU VNU-HCM (ABET).
- **Dataset:** CHB-MIT, 18-ch bipolar, 256 Hz. **Test = 8 subject** (chb03,06,13,14,15,16,17,18), **76 cơn**,
  278.2 h interictal. Split cố định (seed 42): train 12 / val 3 (chb10,11,22) / test 8.
- **Framing (khóa):** POST-HOC EEG review triage, KHÔNG real-time alarm → FP/day cao hơn chấp nhận được.
- **Interpretability:** per-node GAE recon-error → xếp hạng dominant channel, validate MAP@K vs nhãn chuyên gia.
  Là attribution — KHÔNG onset, KHÔNG SOZ.
- **Proof-of-concept** cho sản phẩm phần mềm lâm sàng → provenance/reproducibility quan trọng vượt defense.

## 2. SỐ BÁO CÁO — BASELINE-OF-RECORD (trích RESULTS_OF_RECORD §0)
- **Weight:** equal `(1/3, 1/3, 1/3)` (uninformative prior). Single source: `src/ensemble_recipe.ENS_WEIGHTS`.
- **Model:** canonical seed 42 (deep 5-seed mean ĐÃ BỎ — làm loãng peak).
- **Operating point:** label-free per-subject FP-budget (PREREG_04); report SHARED (held-out) primary.
- **Balanced (PRIMARY):** Sensitivity **0.632** [0.519, 0.731], FP/day **38.6** — mag70/pen0.5, TP/FN/FP 48/28/447.
- **High-sens:** Sensitivity **0.776** [0.671, 0.855], FP/day **72.7** — mag55/pen0.3, TP/FN/FP 59/17/843.
- **Window tier:** macro AUROC **0.775**. **Seed stability:** 5-seed VAL AUROC 0.648 ± 0.011 (Gate PASS).
- **Baselines:** Yildiz 2022 unsupervised CHB-MIT AUROC ≈ 0.68 (window 0.775 vượt). Transformer 0.765/40.6 = TUH, không so được.
- **Attribution (PROVISIONAL):** MAP@3 0.262 / MAP@5 0.303 (chance 0.102/0.128); 36 focal, 40 diffuse.
- **RETIRED (KHÔNG report):** 0.750 / 0.829 (weight+OP test-selected §13; components mất).

## 3. METHOD (locked pipeline)
Unsupervised, patient-independent; train chỉ trên interictal của 12 train subject.
1. Preprocess: 0.5–60 Hz zero-phase → notch → CAR → artifact reject → z-score/kênh → cửa sổ 4 s.
2. Graph/window: node = 5 band-power; `A = 0.5·wPLI + 0.5·AEC`; **top-k 20%**.
3. Joint GAE (GCN 23→64→16, adj + feature decoder), seed 42.
4. Temporal LSTM trên flat-Z(288), L=16, **train trên raw-Z (normfix)**, schedule PREREG_02 §2 (200 ep, cosine, batch 64), seed 42.
5. Gamma AEC 30–60 Hz, top-20%.
6. Robust-z per branch → **equal-weight** ensemble → PELT (`cpd_pipeline_v14`) → label-free FP-budget OP.

## 4. CẤU TRÚC REPO (sau reorg — chi tiết: `docs/REPO_MAP.md`)
Chạy mọi thứ từ REPO ROOT (`python src/<name>.py`, flat-import).
```
src/            code active (flat) + retrain/ (chuỗi v3.1) + dataprep/
docs/           REBUILD_BASELINE_LOCK · RESULTS_OF_RECORD(§0) · REPO_MAP · ATTRIBUTION_SPEC · WEB_DEMO_SPEC · PREREG_0{1..4} · Proposed_solution_v5
data/           models_retrain/ (v3.1 .pt, CANONICAL) · models/ · processed/ · splits/
results/        retrain_v3p1/ (BASELINE) · attribution_v5/ (attribution) · history_superseded/ (KHÔNG cite) · history_topology/
archive/        code superseded (+ fp_reduction_prior, thesis_repro_lock, orphan checkpoint)
```

## 5. ĐÃ XONG
1. Provenance audit + reorg repo; tự reproduce từ clone sạch.
2. **Rebuild full pipeline (v3.1):** GAE + LSTM (normfix, 200/cosine/batch64, 5 seed) + gamma → equal-weight
   ensemble → PELT → label-free FP-budget OP. Baseline khóa (§0). Diagnosis: LSTM/window signal **không** phải
   bottleneck (window 0.775 ≈ pre-rebuild); regression cũ = **weight+OP test-tuned + components mất**.
3. **Deep-mean bỏ** (0.618 < seed42 0.658, làm loãng peak) → canonical seed42.
4. Decision #24 (FP filter) tested & rejected → archive.
5. Attribution redefine & khóa (per-node recon-z, MAP@K); PROVISIONAL chờ cô.
6. Governance: RoR §0, REBUILD_BASELINE_LOCK, REPO_MAP, PROJECT_INSTRUCTIONS cập nhật; archive pre-rebuild.

## 6. CÒN LẠI (thứ tự ở `NEXT_TASKS_AND_PLAN.md`)
- **Brief cô** về baseline honest (gate). → **Giai đoạn B (optimize)**: headroom = per-subject signal
  (chb06 inverted connectivity, chb14 representation), KHÔNG phải LSTM capacity (loss phẳng từ epoch 10) hay weight (flat).
- **Attribution:** chờ cô label blind → chạy `validate_dominant_hitk_FINAL.py` → thay số PROVISIONAL trong ATTRIBUTION_SPEC.
- **Report:** Intro + Method viết được từ giờ (dùng §0). Result/Discussion sau khi cô OK baseline.
- **Slide/Web demo:** khung/UX trước; demo chạy đúng chuỗi inference v3.1.
- **Scope (GVHD OK):** GIỮ web demo + attribution; CẮT LOSO / Siena / SSL → Future Work.

## 7. CAVEAT
- GPU (Kaggle) không bit-reproducible → dùng 1 bộ component nhất quán/analysis; checkpoint `data/models_retrain/` authoritative.
- chb06 = signal-limited thật (inverted connectivity), không phải bug.
- Window vs event luôn báo cùng nhau (window ~0.38 vs event ~0.63–0.78 — gap kỳ vọng).
- `src/thesis_repro_lock.py` đã ARCHIVE (reproduce số RETIRED; hỏng do assert weight cũ). Repro baseline mới: build_ens→score_ens (hoặc viết `repro_lock_v3p1.py` sau).

## 8. BẮT ĐẦU CHAT MỚI
`docs/REBUILD_BASELINE_LOCK.md` → `RESULTS_OF_RECORD.md` §0 → `docs/REPO_MAP.md` → `ATTRIBUTION_SPEC.md`.
KHÔNG re-derive kết quả khóa. KHÔNG cite §1–§16. Việc kế mặc định: viết Methods (unblocked).
