# WEB_DEMO_CONTEXT_BOUNDARY — đọc TRƯỚC mọi câu hỏi về web demo (SzScan)
**(Bản cập nhật — thay thế hoàn toàn bản cũ, đồng bộ với `WEB_DEMO_SPEC_v4.md`)**

**Mục đích file này:** project hiện gộp chung 2 việc khác nhau — (1) thesis/evaluation khoa học (§0,
FP/day, sensitivity, operating point mag/pen...) và (2) sản phẩm demo phục vụ bảo vệ SzScan. Đây là 2 bộ
quy tắc KHÁC NHAU, không được trộn. File này là ranh giới bắt buộc đọc trước khi trả lời bất kỳ câu hỏi
nào về web demo.

---

## QUY TẮC TUYỆT ĐỐI

**Khi câu hỏi liên quan đến web demo / SzScan / UX / UI / backend demo:**
- **CHỈ đọc `WEB_DEMO_SPEC_v4.md`** làm nguồn sự thật duy nhất. `WEB_DEMO_SPEC_v3.md` đã RÚT LẠI HOÀN
  TOÀN — nếu còn tồn tại trong project, chỉ giữ để tra cứu lịch sử, KHÔNG dùng để trả lời hay code.
- **KHÔNG mang các con số/khái niệm sau vào bàn về demo, dưới bất kỳ hình thức nào:**
  - Số liệu §0 (`sensitivity 0.632/0.776`, `FP/day 38.6/72.7`, `AUROC 0.775`...) — đây là số liệu ĐÁNH
    GIÁ khoa học cho thesis, không hiển thị trên UI sản phẩm, không cần và KHÔNG NÊN ép demo khớp số này.
  - `operating point` (mag_pct/pen_mult, balanced/high-sensitivity) — khái niệm evaluation, không xuất
    hiện trong sản phẩm demo.
  - `ground truth` / annotation CHB-MIT hiển thị trên UI — KHÔNG có trong scope demo (muốn đối chiếu thì tự
    mở file `chbXX-summary.txt` gốc song song, không xây tính năng riêng).
  - Bất kỳ file nào thuộc nhóm "thesis/evaluation" (danh sách ở cuối file này).

**Khi câu hỏi liên quan đến thesis/evaluation/báo cáo khoa học:**
- Dùng đúng bộ quy tắc trong PROJECT INSTRUCTIONS gốc (`RESULTS_OF_RECORD.md` §0 thắng nếu có mâu thuẫn
  số liệu).
- KHÔNG áp dụng bất kỳ quyết định UX/UI của web demo vào đây.

---

## CÁC QUYẾT ĐỊNH ĐÃ CHỐT VỀ WEB DEMO (tóm tắt — bản đầy đủ ở `WEB_DEMO_SPEC_v4.md`)

1. **Chỉ 2 trang:** Database (trang chủ) và Analysis (xem EEG/review). Không có trang thứ 3.
2. **8 subject test, xử lý trước toàn bộ, cache local.** Nhận diện file trùng cache = so tên file. Nửa
   subject demo bằng upload live, nửa để sẵn trong Database.
3. **Kiến trúc backend 2 giai đoạn:** (1) mỗi file upload xong → chạy full pipeline trừ CPD ngay; (2) đủ
   hết file của subject → bấm "Process" → ghép toàn bộ ensemble score thành 1 timeline liên tục → chạy CPD
   1 lần → trả kết quả event về đúng từng file tương ứng theo vị trí thời gian.
4. **UI hiển thị theo TỪNG FILE** (Panel Timeline, Panel EEG) — không ghép hiển thị nhiều file liên tục.
   Đây là điểm khác biệt quan trọng so với bản `v3` cũ (v3 dùng cơ chế `locate_range()` để "cắt ngược" từ
   timeline ghép về từng file cho mục đích hiển thị — cơ chế này **không còn cần thiết** vì kết quả CPD
   được trả thẳng theo từng file ngay từ backend).
5. **Không có chế độ Edit.** Muốn sửa → xóa cả subject, tạo lại từ đầu.
6. **Xóa (Delete) chỉ áp dụng cấp Subject**, không xóa được file lẻ (nút không phản hồi nếu chọn file).
   Xóa subject có màn hình xác nhận.
7. **Panel EEG cố định đúng 18 kênh chuẩn** (lọc bỏ kênh phụ như EKG/EOG/Ref-channel nếu file gốc có).
8. **Toolbar Panel EEG:** giữ `⊲▷ [X] hr` (cửa sổ thời gian), `⇕ [X] uV` (biên độ, cho tùy chỉnh dropdown),
   `Select Range` (tạo event thủ công), `lff/hff/60` (3 filter thật khớp preprocessing). **Đã bỏ "All"**
   (không cần vì kênh đã cố định) **và "ar"** (không có bước tương ứng trong pipeline thật).
9. **Panel Timeline chỉ hiển thị phạm vi 1 file**, mặc định 1 giờ / 6 ô 10 phút, KHÔNG tương tác được (chỉ
   Panel EEG mới click được để di chuyển playhead).
10. **Panel Event** là nguồn điều khiển chính — click 1 event đồng bộ cả Panel EEG, Timeline, Attribution.
    Filter 2 tầng: All/Human/AI, rồi AI có thêm Accept/Reject/Uncertain/Unseen.
11. **Panel Channel Attribution:** dùng ĐƯỜNG NỐI giữa 2 điện cực (khớp bản chất bipolar của CHB-MIT), vẽ
    trên nền hình đầu đơn giản — KHÔNG dùng chấm tròn tại 1 điểm. Chưa có dữ liệu thật (chờ Phase B).
12. **Export:** 1 file `.txt`/subject, gộp mọi file .edf con, giữ khung gốc `chbXX-summary.txt`, chèn xen
    kẽ thông tin Source/Review/Comment/Channel Attribution ngay sau mỗi event. Định dạng thời gian trong
    export = giây tính từ đầu file (giống CHB-MIT gốc), khác với `HH:MM:SS` dùng trên UI.
13. **Định dạng thời gian trên UI:** `HH:MM:SS` (thêm tiền tố `Nd:` nếu ≥24h) cho mọi thời điểm/khoảng thời
    gian hiển thị trực quan (Database Duration, Panel Timeline, Panel EEG, Onset/Offset của event).
14. **Không đăng nhập.** Không có guardrail chống over-claim trên UI (chỉ nói bằng lời lúc bảo vệ).
15. **Giới hạn xử lý song song:** toàn hệ thống chỉ 1 subject (upload hoặc Process) chạy nền tại 1 thời
    điểm, kể cả khi đã minimize.

---

## DANH SÁCH FILE — PHÂN LOẠI

**Nhóm DEMO (dùng cho web demo, đọc khi làm việc về SzScan):**
`WEB_DEMO_SPEC_v4.md` (⚠️ nguồn duy nhất — KHÔNG dùng `WEB_DEMO_SPEC_v3.md` nữa), `evaluation_protocol.py`
(chỉ phần logic ghép timeline dùng chung, KHÔNG lấy ngưỡng/tham số đã tune riêng cho §0),
`cpd_pipeline_v14.py` (thuật toán CPD dùng chung), `ensemble_recipe.py` (công thức ensemble dùng chung),
`attribution_gae_pernode.py` / `gae_joint.py` / `lstm_temporal.py` / `retrain_io.py` (khi có dữ liệu
attribution thật từ Phase B), `chb01-summary.txt` → `chb23-summary.txt` (chỉ dùng để đối chiếu thủ công
lúc cần, KHÔNG hiển thị trên UI sản phẩm).

**Cần rà soát lại vai trò (xem khuyến nghị chi tiết trong phần "code cũ" đi kèm bản cập nhật này):**
`edf_order.py`, `edf_index.py` — 2 file này được viết cho kiến trúc `v3` (ghép-rồi-cắt-ngược). Với kiến
trúc `v4` (backend trả kết quả trực tiếp theo từng file), vai trò của 2 file này cần xác nhận lại — xem
tài liệu khuyến nghị riêng.

**Nhóm THESIS/EVALUATION (KHÔNG mang vào bàn luận demo):**
`RESULTS_OF_RECORD.md`, `REBUILD_BASELINE_LOCK.md`, `PROVENANCE_MAP.md`, `RUBRIC_TRACKING.md`,
`PLAN_AND_STATUS.md`, `NEXT_TASKS_AND_PLAN.md`, `MASTER_HANDOFF_v2.md`, `Proposed_solution_updated_v5.md`,
`REPO_MAP.md`, `ATTRIBUTION_SPEC.md`,
`Spatial_Localization__Channel_Attribution___Explainability_for_EEG_Seizure_Detection.md`,
`Literature_Review_and_Novelty_Assessment...md`, `Lit review.txt`, `PHASE_B_OPTIMIZATION_PLAN.md`,
`PREREG_01/02/03/04/05_*.md`, `PREREG_TIER2_*.md`, `README.md`, `szcore_eval.py`, `stat_validation.py`,
`duration_stratified_sensitivity.py`, `event_ablation.py`, `window_event_gap.py`,
`consolidate_outputs.py`, `mag_pen_grid_sweep_v2.py`, `rebuild_ensemble_new_weight.py`,
`weight_sensitivity_sweep.py`, `weight_seed_robustness_check.py`, `weight_candidate_crosscheck.py`,
`fp_budget_operating_point.py`, `derive_weights.py`, `build_ens*.py`, `score_ens.py`,
`train_lstm_temporal_v3.py`, `final_eval_seed42.csv`, `fp_budget_locked.csv`, `report_metrics.csv`,
`2024__SzCORE.pdf`, `syllabus_Thesis.pdf`, `Thesis_Rubric.pdf`, `Thesis_report_format.pdf`,
`Thesis_..._Registration_Form_signed.pdf`, `RESULTS_OF_RECORD_phaseB.md`, `PHASE_C_HANDOFF.md`,
`PREREG_C0_connectivity_probe.md`, `S2_S3_negatives.md`, mọi file `.csv` kết quả thí nghiệm.

**Lưu ý:** một số file trong nhóm DEMO (`evaluation_protocol.py`, `cpd_pipeline_v14.py`,
`ensemble_recipe.py`...) VẪN được dùng bởi cả 2 phía (thesis lẫn demo) vì đây là code gốc dùng chung. Khi
đọc các file này trong ngữ cảnh DEMO, chỉ lấy phần LOGIC (hàm ghép timeline, thuật toán PELT, công thức
ensemble) — KHÔNG lấy các con số/ngưỡng đã tune riêng cho §0 (mag_pct, pen_mult cụ thể) làm chuẩn hiển thị
demo. Demo chạy label-free (không có `inter_mask`), vì bệnh nhân/subject mới không có annotation.
