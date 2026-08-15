# WEB_DEMO_SPEC — Demo hỗ trợ đọc long-term EEG
### Thay thế PHASE_C_PLAN_v2.md. Trạng thái: chờ (phụ thuộc rebuild ổn định + attribution xong).

---

## 1. Mục tiêu
Web hỗ trợ **bác sĩ/kỹ thuật viên** đọc record trong quy trình long-term EEG — tiết kiệm thời gian/công sức,
giảm gánh nặng review. Dựng trên **2 tính năng lõi đã có**: (1) seizure detection + CPD, (2) channel attribution.

## 2. User flow
1. Truy cập web → **Add subject**.
2. Upload **toàn bộ file .edf của subject đó** + điền thông tin subject.
3. Hệ thống **chạy full pipeline** (graph → GAE/LSTM/gamma → ensemble → PELT → attribution).
4. **Màn hình kết quả** (theo TỪNG file .edf):
   - **Timeline** đánh dấu vị trí các seizure được detect.
   - **Raw EEG** đầy đủ 18 kênh, cuộn theo timeline.
   - **Channel attribution**: hiển thị kênh bị flag (ánh xạ sang sơ đồ 10–20).
5. Chuyển subject khác → về trang chủ, chọn subject (đã lưu thông tin).

## 3. Chức năng (tùy chọn trên màn kết quả)
- Chọn từng file .edf của cùng subject (màn chỉ hiển thị 1 file).
- **Chấp nhận / nghi ngờ** kết quả hệ thống (đánh dấu).
- **Tự add label** theo mắt bác sĩ.
- **Lưu** kết quả sau khi review; **xuất file báo cáo**.
- Điều hướng bản ghi: kéo theo timeline, chỉnh **độ rộng cửa sổ / biên độ / filter**.
- **Comment** trong từng event.

## 4. Data
- Dùng **23 sub CHB-MIT** (PhysioNet), **KHÔNG** có data bệnh viện thực tế.
- **⚠️ Cần thảo luận:** 23 sub có thể chưa đủ phong phú cho trải nghiệm demo → cần chốt phạm vi.

## 5. Ràng buộc kỹ thuật & rủi ro (phải nắm)
- **"Chạy full pipeline khi upload" rất nặng** (graph build + GAE inference + PELT). Với CHB-MIT nên
  **PRE-COMPUTE sẵn** kết quả cho 23 sub, KHÔNG hứa real-time. Demo trình bày kết quả đã tính.
- **Over-claim:** ghi rõ đây là **proof-of-concept trên CHB-MIT, chưa validate lâm sàng**.
- **Attribution còn khiêm tốn** (MAP@3~0.26, 53% diffuse): hiển thị "kênh nghi ngờ" phải kèm cảnh báo
  độ tin cậy, đặc biệt cơn diffuse (không nên vẽ kênh flag khi cơn không localize được).

## 6. Thứ tự & phụ thuộc
- **Prerequisite:** rebuild pipeline ổn định (multiseed, không bug) + attribution xong.
- **Làm trước được:** UX/UI design, dựng khung front-end, logo/tên.
- **Vị trí ưu tiên:** item CUỐI — KHÔNG được ăn vào thời gian viết report. Nếu runway ép → demo cắt trước report.
- Demo phục vụ **defense** (điểm nhấn), không nằm trên critical path của báo cáo.
