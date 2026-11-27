# Hướng dẫn buổi gặp bác sĩ An (dành cho tác giả)

Giao thức: `results/c5_szscan/step3/PROTOCOL_STEP3.md` (đã duyệt 27/11). Mức báo cáo: **đánh giá khám phá của chuyên
gia** (exploratory expert review) — một người đọc, hai bản ghi, chỉ đếm; không tính độ nhạy, không gọi là thẩm định lâm
sàng.

## Trước buổi gặp (trên laptop, terminal của bạn)

1. Chọn phiên bản theo thời gian bác sĩ dành ra: khoảng 1 giờ → `--version 24` (16 clip bệnh viện + 8 clip neo); ít hơn
   → `--version 18` (12 + 6). Quy tắc chọn chạy **một lần**; thư mục đầu ra phải trống.
2. Tạo clip và trang đánh giá (vài phút):
   `cd /f/Study/Thesis/Code && PYTHONUTF8=1 python src/c5_step3_clips.py --chb F:/Study/Thesis/Dataset/CHB-MIT --siena F:/Study/Thesis/Dataset/siena --version 24`
   Nếu lệnh dừng giữa chừng (thư mục đã có một phần file): gửi thông báo lỗi cho chat (không gửi clip hay `key.csv`),
   tự xóa thư mục `C5_review` rồi chạy lại một lần; lần chạy lỗi được ghi vào giao thức.
3. Mở `F:/Study/Thesis/Eureka/C5_review/review.html` bằng Chrome, xem thử clip C01 rồi **đóng mà không trả lời**. Không
   mở `key.csv` trước buổi gặp (để bạn cũng không biết clip nào là clip nào khi ngồi cạnh bác sĩ).
4. Mở sẵn SzScan (`bash web_demo/start_demo.sh`) với study riêng tư clin01 cho phần demo; in sẵn `DONG_Y.md`,
   `PHIEU_DANH_GIA.md` (phiếu giấy dự phòng) và `HUONG_DAN_PHONG_VAN.md`.

## Trong buổi gặp (khoảng 60 phút)

1. **Đồng ý (5 phút):** đọc cùng bác sĩ các điểm trong `DONG_Y.md`, ghi lại lựa chọn của bác sĩ.
2. **Xem clip mù (30 phút):** bác sĩ tự thao tác trên `review.html`. Bạn không bình luận về clip, không gợi ý. Nhấn
   **“Tải kết quả (CSV)”** sau khoảng mỗi 6 clip và ở cuối (trình duyệt có thể không giữ kết quả nếu trang bị tải lại;
   file tải sau cùng là file dùng). Nếu trang lỗi, dùng phiếu giấy và ghi giờ bắt đầu / kết thúc từng clip.
3. **Demo SzScan (10 phút)** trên clin01 — sau phần xem clip.
4. **Phỏng vấn (15 phút):** theo `HUONG_DAN_PHONG_VAN.md`; ghi chép tay; không ghi âm nếu bác sĩ không đồng ý.

## Sau buổi gặp

1. Chép file CSV tải về vào `F:/Study/Thesis/Eureka/C5_review/c5_review_answers.csv`.
2. Đọc kết quả thành số đếm:
   `cd /f/Study/Thesis/Code && PYTHONUTF8=1 python src/c5_step3_report.py --private F:/Study/Thesis/Eureka/C5_review --answers F:/Study/Thesis/Eureka/C5_review/c5_review_answers.csv`
3. Kiểm tra `results/c5_szscan/step3/REVIEW.md` không có thông tin nào của bản ghi bệnh viện ngoài số đếm, rồi commit
   (chỉ hai file công khai):
   `git add results/c5_szscan/step3/REVIEW.md results/c5_szscan/step3/anchors.csv`
   `git commit -m "C5 Step 3: exploratory expert review (counts)"`
   `git push`
4. Ghi chép phỏng vấn: chỉ những câu bác sĩ đồng ý cho trích dẫn, ở mức bác sĩ chọn trong phần đồng ý; đưa cho C8 cùng
   `REVIEW.md`.
