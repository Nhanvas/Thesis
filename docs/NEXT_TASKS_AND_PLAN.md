# NEXT_TASKS_AND_PLAN — Kế hoạch đi tới (đến 15/10 nộp, defense 2–3/11)
### Cập nhật 2026-08-15: rebuild XONG, baseline khóa (§0). Bổ sung cho PLAN_AND_STATUS.md (lịch sử giữ nguyên).

---

## 0. NGUYÊN TẮC SỐ (sau rebuild)
- `RESULTS_OF_RECORD.md` **§0** = nguồn sự thật DUY NHẤT cho mọi con số. §1–§16 = lịch sử, KHÔNG report.
- Baseline đã khóa → slide/report/demo dùng **số §0** (0.632 / 0.776), KHÔNG dùng 0.750/0.829 (retired, test-tuned).
- **KHÔNG tune trên 8 test subject.** Cải tiến (Giai đoạn B) phải derive trên non-test, pre-register, chấm test 1 lần.
- **Attribution:** PROVISIONAL, chờ cô label → reconcile sau.

## 1. DANH SÁCH VIỆC
- **Brief cô** về baseline honest thấp hơn (khung: test-leakage + bug đã sửa; số sạch/tái lập). ← GATE trước Giai đoạn B.
- **Giai đoạn B (optimize):** chỉ sau khi cô OK. Headroom = per-subject signal (chb06/chb14), KHÔNG phải LSTM/weight.
- **Report:** outline full → Intro + Method (viết được từ giờ) → Result/Discussion/Conclusion (sau khi cô OK baseline).
- **Attribution:** chờ cô label groundtruth → chốt số MAP@K.
- **Web demo:** UX/UI design → build (chạy đúng chuỗi inference v3.1) → test → logo/tên.
- **Defense:** slide → script/QA → luyện.

## 2. THỨ TỰ & PHỤ THUỘC (làm được từ giờ)
- **Intro + Method + outline report:** unblocked — dùng §0. **Làm ngay.**
- **Slide method + khung:** unblocked.
- **UX/UI web demo:** unblocked (chờ attribution xong mới build backend).
- **Giai đoạn B:** BLOCKED bởi (a) cô OK baseline, (b) dựng được validation non-test hợp lệ cho subject khó.
- **Result/Discussion:** chờ cô OK baseline + attribution freeze.

### Song song ngay bây giờ (không phụ thuộc số biến động):
1. Outline report (full) → Intro + Method (số §0).
2. Slide method + khung slide.
3. UX/UI design web demo (+ logo/tên).
4. Chuẩn bị nội dung brief cho cô (bảng so 0.750→0.632 + lý do methodological).

## 3. GIAI ĐOẠN B — OPTIMIZE (định hướng, khi mở)
- **O1:** đã loại — LSTM không under-train (loss phẳng epoch 10), seed ổn (VAL SD 0.011). Không thêm capacity.
- **O2 (chính):** representation cho subject signal-limited — chb06 (inverted connectivity), chb14. Cần
  validation non-test hợp lệ (VAL 3-subject/2-bão-hoà không đủ) → nếu không dựng được thì để Future Work.
- **O3:** per-subject FP-budget calibration đã có (+0.066 high-sens); seed-aggregation (median) là dự phòng.
- Mọi cải tiến: pre-register (giả thuyết + tiêu chí bác bỏ) → non-test → test 1 lần → reconcile §0.

## 4. MỐC THỜI GIAN
- Nay → giữa 9: viết Methods/Intro + UX/UI + slide method + brief cô (song song). Giai đoạn B nếu cô OK.
- Tháng 9: IELTS-dominant (thi 9/10). Research maintenance.
- 1–15/10: Result/Discussion/Conclusion + polish.
- 2–3/11: defense → sửa slide (chủ yếu result) + demo điểm nhấn.

## 5. RÀNG BUỘC PHẠM VI
- **CORE (form bắt buộc):** unsupervised temporal detection + CPD trên CHB-MIT, event-level, lit review,
  models/flowcharts, implementation, validation, so sánh method, discussion. → đã có (baseline §0).
- **BONUS (giữ):** channel attribution/XAI, web demo.
- **FUTURE WORK:** LOSO, Siena, SSL, representation cho subject signal-limited.
