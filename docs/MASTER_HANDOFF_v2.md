# MASTER HANDOFF v2 — bản onboarding DUY NHẤT cho chat/Project mới
*Hợp nhất MASTER_HANDOFF cũ + PROJECT_HANDOFF (đã gỡ khỏi project). Đọc hết trước khi hành động.*

Vai trò của assistant kế tiếp: **research director kiểu Stanford/MIT** — sở hữu mạch narrative khoa học.
Boti (Nguyen Quoc Trung Nhan, BEBEIU22184) là **người quyết cuối**; chạy trên Kaggle (GPU) + Cursor
(`F:/Study/Thesis/Code`, git, branch `main`, `github.com/Nhanvas/Thesis`) và dán output về. Chat bằng
**tiếng Việt**; code/deliverable/governance bằng **tiếng Anh**.

Kỷ luật: rigour > tốc độ; pre-register (giả thuyết + tiêu chí bác bỏ) trước khi chạy; **không bao giờ
tune trên 8 subject test**; báo cáo kết quả as-is (âm/một phần thì nói thẳng); **archive-not-delete**
(mọi bỏ file = `git mv`, không hard-delete). **Đọc method/docs trước khi đề xuất — đừng suy từ trí nhớ**
(đây là failure mode có thật; Boti sẽ push back và điều đó là đúng — hãy đón nhận).

**Deadline:** IELTS 9/10 · nộp 15/10 · defense 2–3/11. Khi hụt thời gian: **viết > demo > thí nghiệm thêm**.

---

## 0. TRẠNG THÁI NGAY LÚC NÀY (đọc kỹ — đây là điểm dễ nhầm nhất)

Method của pipeline **đã khóa và KHÔNG đổi**: đồ thị connectivity per-window (wPLI+AEC, top-k 20%) →
GAE recon + LSTM temporal + gamma-AEC → robust-z ensemble → PELT CPD (`cpd_pipeline_v14`) → SzCORE.

**Có HAI lớp số đang cùng tồn tại — phải phân biệt:**

- **(1) Số PRE-REBUILD = số báo cáo hiện hành.** Đây là bộ số dùng cho **slide/report/demo với cô** cho
  tới khi rebuild reconcile xong. Nguồn: `RESULTS_OF_RECORD.md` §1. Weight `(0.40,0.35,0.25)`.
- **(2) Số REBUILD = ĐANG TIẾN HÀNH, CHƯA ADOPT.** Rebuild đã chạy **một vòng** ra `RESULTS_OF_RECORD`
  §16 (weight đều `1/3`, deep seed-ensemble), nhưng ra **thấp hơn** pre-rebuild và đang được coi là
  **regression cần resolve** (LSTM branch) → **CHƯA phải số chính thức, KHÔNG báo cáo cô bằng bộ này.**

**Quy tắc chống xung đột số (bất di bất dịch):** `RESULTS_OF_RECORD.md` là **nguồn sự thật duy nhất**.
Mọi nơi khác (handoff này, slide, report, PROJECT_INSTRUCTIONS) dùng **số pre-rebuild làm placeholder**,
ghi nhãn "pre-rebuild". **Không bake số mới vào đâu.** Khi rebuild xong → **một lượt reconcile** cập nhật
ROR (kèm decision #) → rồi mới quét sang slide/report. (Chi tiết kế hoạch: `NEXT_TASKS_AND_PLAN.md` §0.)

Việc kế tiếp (chat riêng): **§7 channel attribution** — đã redefine & khóa bài toán/method/metric, kết
quả PROVISIONAL, chờ **nhãn blind của cô**. Nguồn duy nhất: `ATTRIBUTION_SPEC.md`.

---

## 1. THESIS IDENTITY (immutable)
- **Title:** *Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder and Change Point Detection.*
- **Student:** Nguyen Quoc Trung Nhan (BEBEIU22184). **Supervisor:** Hà Thị Thanh Hương (Assoc. Prof.). **School:** BME, International University VNU-HCM (ABET).
- **Dataset:** CHB-MIT scalp EEG, 18-ch bipolar, 256 Hz. **Test = 8 subject** (chb03,06,13,14,15,16,17,18), **76 cơn**. Split cố định (seed 42): train 12 / val 3 (chb10,11,22) / test 8.
- **Framing (khóa):** POST-HOC EEG review triage, **KHÔNG** real-time alarm → FP/day cao hơn là chấp nhận được.
- **Interpretability:** per-node GAE recon-error → xếp hạng **dominant channel**, validate bằng **MAP@K** vs nhãn chuyên gia. Là attribution — **KHÔNG** onset, **KHÔNG** SOZ. Xem `ATTRIBUTION_SPEC.md`.
- **Proof-of-concept** cho sản phẩm phần mềm lâm sàng lớn hơn → provenance/reproducibility quan trọng vượt ngoài defense.

## 2. SỐ PRE-REBUILD — placeholder báo cáo (trích từ ROR §1; xác thực bằng `src/thesis_repro_lock.py`)
- **Weight:** `(recon, temporal, gamma) = (0.40, 0.35, 0.25)` (Decision #19). Single source: `src/ensemble_recipe.ENS_WEIGHTS`.
- **Balanced (PRIMARY):** Sensitivity **0.750** [0.642, 0.834], FP/day **39.77** [36.22, 43.57] — mag60/pen1.0, TP/FN/FP = 57/19/461, macro 0.732 ± 0.257.
- **High-sensitivity:** Sensitivity **0.829** [0.729, 0.897], FP/day **71.25** [66.48, 76.28] — mag50/pen0.5, TP/FN/FP = 63/13/826, macro 0.807 ± 0.159.
- **Window tier:** macro AUROC **0.791**; component standalone AUROC recon 0.671 / temporal 0.647 / gamma 0.755 (weight-independent; khớp `auroc_verification.csv`).
- **Latency** ≈ 0 → +7 s (hơi sau onset). **KHÔNG claim "pre-ictal".**
- **Decision #24 — FP-reduction filter: TESTED & REJECTED.** Pipeline không đổi; FP/day là giới hạn được chấp nhận. (Đừng wire `results/**/fp_filter_*` vào pipeline — đó là hồ sơ bác bỏ.)
- **Baselines:** Transformer 0.765/40.6 = **TUH**, KHÔNG phải CHB-MIT. Yildiz unsupervised CHB-MIT = **0.68** ở docs pre-rebuild; recheck lit của rebuild sửa thành ≈**0.61** (ROR §16.7) → coi là **đang chờ reconcile**, chốt lúc viết, trích ROR.

## 3. SỐ REBUILD — ĐANG TIẾN HÀNH, CHƯA ADOPT (ROR §16; **không báo cáo cô bằng bộ này**)
Deep seed-ensemble (mean 5 seed {42,1,2,3,4}, tag 99), weight đều `(1/3,1/3,1/3)`.
- Shared: balanced mag40/pen2 **0.618** @ 41.6 FP/day; high-sens mag60/pen0.3 **0.711** @ 70.1.
- Calibrated (PREREG_04, label-free, VAL-gated): balanced **0.632** @ 40.3; high-sens **0.776** @ 76.1.
- Window macro AUROC **0.746**; 5-seed 0.739 ± 0.037. Single-seed SD lớn (balanced 0.513 ± 0.178) — báo cáo minh bạch, không giấu.
- **Lý do chưa adopt:** thấp hơn pre-rebuild; đang resolve LSTM regression (correctness, KHÔNG chase số cao hơn). Khi ổn định (multiseed, không bug) → reconcile 1 pass → lúc đó §16 mới thành số chính thức.

## 4. METHOD (locked pipeline)
Unsupervised, patient-independent; train chỉ trên cửa sổ interictal của 12 subject inner-train.
1. Preprocess: 0.5–60 Hz band-pass zero-phase → notch 60 Hz → CAR → artifact reject (interictal) → z-score/kênh → cửa sổ 4 s.
2. Graph/window: node = 5 band-power [18×5]; `A = 0.5·A_wPLI + 0.5·A_AEC`; **top-k 20%** (phát hiện lõi: threshold cố định làm GCN thoái hoá về mean-pooling).
3. Joint GAE: GCN 23→64→16; inner-product adj decoder + MLP feature decoder; score = MSE(A,Â)+0.1·MSE(X,X̂). Model authoritative: `data/models/best_model_joint_lambda01.pt` (có `x_decoder`).
4. Temporal LSTM trên latent z(t)∈R¹⁶; score = prediction MSE. (**LSTM giữ** — là nhánh mạnh DUY NHẤT cho chb14.)
5. Gamma AEC 30–60 Hz Hilbert envelope corr, top-20%.
6. Ensemble robust-z → PELT CPD (`cpd_pipeline_v14`, seed-independent penalty + magnitude filter, label-free).

## 5. CẤU TRÚC REPO (github.com/Nhanvas/Thesis, `main`) — chạy mọi thứ từ REPO ROOT
```
Code/
├── src/                      # code active, phẳng: `python src/<n>.py`
│   ├── ensemble_recipe.py    #   SINGLE SOURCE: weight + build_ensemble
│   ├── cpd_pipeline_v14.py   #   SINGLE SOURCE: detection (PELT + magnitude filter)
│   ├── szcore_eval.py · evaluation_protocol.py · window_tier_newweight.py
│   ├── thesis_repro_lock.py  #   reproduce điểm khóa pre-rebuild bit-exact (0.750/39.77 + 0.829/71.25)
│   ├── stat_validation.py · event_ablation.py · duration_stratified_sensitivity.py
│   ├── mag_pen_grid_sweep_v2.py · rebuild_ensemble_new_weight.py · weight_*.py  (provenance one-offs)
│   ├── eval_multiseed.py · window_event_gap.py · consolidate_outputs.py · edf_index.py
│   ├── attribution_gae_pernode.py   #   PRIMARY attribution (per-node recon-z) — xem ATTRIBUTION_SPEC
│   ├── retrain/              #   REBUILD (chưa adopt): gae_joint, lstm_temporal, build_ens,
│   │                         #     build_seed_ensemble, score_ens, aggregate_final,
│   │                         #     fp_budget_operating_point, window_event_gap_new, derive_weights
│   └── dataprep/             #   preprocessing, graph_construction, feature_extraction, gamma, splits
├── docs/                     # governance + reference (AUTHORITATIVE)
│   ├── RESULTS_OF_RECORD.md  #   ★ MỌI SỐ. §1–§15 = pre-rebuild (báo cáo); §16 = rebuild (chưa adopt)
│   ├── MASTER_HANDOFF_v2.md  #   ★ file này — onboarding
│   ├── NEXT_TASKS_AND_PLAN.md#   ★ kế hoạch/scope/thứ tự — đọc sau ROR
│   ├── ATTRIBUTION_SPEC.md   #   ★ nguồn DUY NHẤT attribution (problem/method/metric MAP@K/status)
│   ├── TIEU_CHI_LABEL_dominant_channel_v2.md  #   tiêu chí nhãn cho cô
│   ├── WEB_DEMO_SPEC.md      #   spec demo (sẽ merge PHASE_C_PLAN_v2 ở phiên demo-design)
│   ├── PLAN_AND_STATUS.md    #   log phase + decision #1–#27 (số = pre-rebuild)
│   ├── PROVENANCE_MAP.md · Proposed_solution_updated_v5.md · RUBRIC_TRACKING.md
│   ├── PREREG_01..04.md      #   pre-registration cho rebuild
│   └── Spatial_Localization...md   #   field survey (metric SUPERSEDED bởi ATTRIBUTION_SPEC)
├── notebooks/kaggle_gpu/     # thesis-cpd-final.ipynb (components+pernode)
├── demo/                     # PHASE_C_PLAN_v2 material (wireframe, brief, mock JSON) — merge sau
├── archive/                  # superseded: PHASE_A/B_AUDIT_handoff, PROJECT_HANDOFF, attribution_c1/c2/c3, ...
├── data/                     # models/*.pt, processed/components/, pernode/, splits/ (committed); graphs gitignored
└── results/
    ├── locked/ · phaseB_newweight/ · attribution/ · cpd/evaluation/*_newweight.csv   (CITED)
    ├── retrain/              #   rebuild artifacts (chưa adopt)
    └── history_superseded/   #   old-weight caches, buggy grids — DO NOT cite
```

## 6. ĐÃ XONG (giai đoạn provenance/consolidation)
1. **Provenance audit + reorg repo:** kiểm kê mọi file, dựng provenance map, dồn về `src/` phẳng + `dataprep` + `archive/*`, quarantine old-weight về `results/history_superseded/`. Repo tự reproduce từ clone sạch.
2. **Reproducibility chứng minh 2 lần:** `thesis_repro_lock.py` reproduce headline pre-rebuild bit-exact trước & sau reorg.
3. **Model provenance:** authoritative = JOINT `best_model_joint_lambda01.pt`; 10 checkpoint A-only trong `archive/scaffolding/` là superseded; **LSTM training code KHÔNG được giữ** (documented provenance gap — đây là gốc của rebuild).
4. **Decision #24** (FP filter) tested & rejected → ROR §15.
5. **Rubric gap** đóng bằng DM6 (Deployment Strategy) trong `Proposed_solution_updated_v5.md` (ABET PI 4C).
6. **Rebuild chạy 1 vòng** → ROR §16 (chưa adopt, xem §3 trên).

## 7. CÒN LẠI (thứ tự chi tiết ở `NEXT_TASKS_AND_PLAN.md`)
- **Rebuild** full pipeline → dọn code → reconcile số (1 pass vào ROR).
- **§7 attribution:** chờ cô label blind (`TIEU_CHI...v2.md`) → chạy `validate_dominant_hitk_FINAL.py` → thay số PROVISIONAL trong ATTRIBUTION_SPEC §5.
- **Report:** outline full + Intro + Method **viết được từ giờ**; Result/Discussion/Conclusion chờ rebuild + attribution.
- **Slide:** khung + method làm trước (báo cáo phản biện, số pre-rebuild); defense sửa chủ yếu result.
- **Web demo:** item CUỐI, không ăn thời gian viết report; prerequisite = rebuild ổn định + attribution xong; UX/UI làm trước. Spec: `WEB_DEMO_SPEC.md`.
- **Scope chốt (GVHD OK):** GIỮ web demo + attribution; **CẮT** LOSO / Siena / SSL → Future Work.

## 8. CAVEAT / CHƯA VERIFY (thành thật)
- **GPU (Kaggle) không bit-reproducible** → đừng train lại để "khớp" số khóa; model + components đã release là authoritative.
- Upstream GAE/LSTM/gamma chưa được audit riêng (nhận cached components as-given, nhưng đã chứng minh reproduce số khóa pre-rebuild).
- **chb06** = detection-limited thật (inverted connectivity), không phải bug — báo cáo như giới hạn.
- **Window vs event luôn báo cùng nhau**: window sens ~0.38 vs event sens ~0.75–0.82 — gap kỳ vọng (bắt trúng bất kỳ window nào trong cơn = TP lâm sàng).

## 9. REPRODUCE / VERIFY (từ repo root, CPU)
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/thesis_repro_lock.py     # phải in: LOCKED HEADLINE REPRODUCES (0.750/39.77 + 0.829/71.25)
```
Rebuild (khi cần): Kaggle `src/retrain/build_ens.py` → Cursor `build_seed_ensemble.py` → `score_ens.py --seed 99`
(`--verify chbNN` xác nhận bit-identity) → `aggregate_final.py` → `fp_budget_operating_point.py`. Weight arg `0.3334,0.3333,0.3333`.
**Không chạy 4 process CPD song song trên laptop** (contention làm treo chb06) — chạy tuần tự.

## 10. BẮT ĐẦU CHAT MỚI
Đọc `NEXT_TASKS_AND_PLAN.md` (plan/scope) → `RESULTS_OF_RECORD.md` (số + trạng thái reconcile) →
`ATTRIBUTION_SPEC.md` (attribution). Demo: `WEB_DEMO_SPEC.md`. Viết: `Proposed_solution_updated_v5.md`.
**Không re-derive kết quả khóa trừ khi được yêu cầu.** Việc kế tiếp mặc định: viết Methods (unblocked, ổn định).
