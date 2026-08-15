# NEXT_TASKS_AND_PLAN — Kế hoạch đi tới (đến 15/10 nộp, defense 2–3/11)
### Bổ sung cho PLAN_AND_STATUS.md (phần lịch sử giữ nguyên). Không chứa số detection (chờ rebuild).

---

## 0. NGUYÊN TẮC CHỐNG XUNG ĐỘT SỐ (quan trọng nhất)
- `RESULTS_OF_RECORD.md` = **nguồn sự thật DUY NHẤT** cho mọi con số. Không nơi nào ghi số mâu thuẫn nó.
- **Trong lúc rebuild:** slide/report/demo dùng **số cũ đã khóa làm placeholder**, ghi nhãn "pre-rebuild".
  KHÔNG bake số mới vào đâu.
- **Rebuild xong → MỘT lượt reconcile:** cập nhật RESULTS_OF_RECORD (kèm decision #) → rồi mới quét sang slide/report.
- **Attribution:** số hiện tại là PROVISIONAL (chờ cô). Reconcile sau khi cô trả nhãn.

## 1. DANH SÁCH VIỆC
- **Rebuild:** rebuild full pipeline → dọn code → chốt result.
- **Defense:** soạn slide → soạn script/QA → luyện defense.
- **Report:** viết outline → deep-research paper → viết report → check Grammarly.
- **Channel attribution:** (đã chốt bài toán/method/metric — xem ATTRIBUTION_SPEC.md) → chờ cô label → chốt số.
- **Web demo:** UX/UI design → build → test → logo/tên (xem WEB_DEMO_SPEC.md).

## 2. THỨ TỰ & PHỤ THUỘC (làm được từ giờ)
- **Attribution:** phải **đợi cô label groundtruth** xong mới chốt tiếp.
- **Web demo:** phải **đợi rebuild ổn định (multiseed, không bug) + attribution xong** (web dựa vào 2 tính năng này).
  → **UX/UI design làm trước** trong lúc chờ.
- **Slide:** làm trước được (báo cáo phản biện). Method không đổi; chỉ **result đợi rebuild+attribution**
  (tạm dùng số cũ). Defense sẽ sửa slide — chủ yếu sửa **result**; discussion/conclusion ảnh hưởng ít;
  intro/method ảnh hưởng ít nhất.
- **Report:** viết từ giờ được. **Outline soạn full trước.** Intro + Method viết trước được;
  Result/Discussion/Conclusion **đợi rebuild+attribution xong**.

### Có thể chạy SONG SONG ngay bây giờ (không phụ thuộc số biến động):
1. Outline report (full) → Intro + Method.
2. Slide method + khung slide.
3. UX/UI design cho web demo (+ logo/tên).
4. Rebuild pipeline (khi xong → reconcile số).

## 3. SCOPE — CHỐT (GVHD đồng ý)
- **GIỮ (từ plan):** web demo, channel attribution.
- **CẮT (thời gian có hạn):** LOSO, external validation (Siena), SSL → **Future Work**.
  - Lý do LOSO: pipeline đã patient-independent → LOSO chỉ trình bày lại tính đó, giá trị biên thấp.
  - Lý do Siena/SSL: effort/rủi ro cao, thuộc pha journal; form đăng ký KHÔNG yêu cầu.

## 4. MỐC THỜI GIAN (tham chiếu)
- Nay → đầu/giữa 9: cửa sổ research (rebuild + viết Methods/Intro + UX/UI + slide method) song song.
- Tháng 9: **IELTS-dominant** (thi 9/10). Research ở chế độ maintenance.
- 1–15/10: viết Result/Discussion/Conclusion + polish. Coi 9/10 là ngày mất trắng.
- 2–3/11: defense → sửa slide (chủ yếu result) + demo làm điểm nhấn.

## 5. RÀNG BUỘC PHẠM VI (dán lên tường)
- **CORE (form bắt buộc):** unsupervised temporal detection + CPD trên CHB-MIT, event-level, + lit review,
  models/flowcharts, implementation, validation, **so sánh method khác**, discussion. → đã có.
- **BONUS (giữ):** channel attribution/XAI, web demo.
- **FUTURE WORK:** LOSO, Siena, SSL.
