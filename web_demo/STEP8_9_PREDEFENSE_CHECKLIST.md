# STEP8_9_PREDEFENSE_CHECKLIST.md — nhu cầu report + luật Tier 2

**Nguồn gốc:** feedback từ project thesis (Project #1), 2026-09-25, sau khi chốt Step 7 round 2
(attribution p95|z|). File này gom lại phần "chưa cần làm ngay" của feedback đó, để không bị quên khi
mở chat mới ở project này. Không phải file build — không đưa cho Claude Code chạy trực tiếp; đây là
tài liệu tham chiếu khi soạn prompt cho Step 8/9.

**Vị trí:** upload cùng chỗ với `CLAUDE.md`/`SZSCAN_SPEC_v5.md`/`PROJECT2_SETUP.md` trong project này.
Không thuộc `web_demo/` repo — chỉ là ghi chú điều phối giữa hai project, giống vai trò của
`PROJECT2_SETUP.md`.

---

## 1 · Report cần gì từ các bước còn lại

Chuẩn bị dần trong lúc build, không đợi xong hết mới làm:

- **Ảnh chụp:**
  - (a) Import và xử lý một recording (upload → Process → subject xuất hiện).
  - (b) Figure 3.6: timeline detection **và** attribution panel của **cùng một** recording, chụp
    **sau** Step 7 round 2 đã đóng (để số liệu attribution đúng công thức mới). Chọn recording có
    event thật, không dùng file synthetic. Không được để lộ bất kỳ ngày lịch nào từ `meas_date`
    (CHB-MIT đã dịch năm giả, khoảng 2057–2075) — chỉ hiện `Recording N, HH:MM:SS` như spec đã quy
    định (C17).

- **Thời gian xử lý theo từng stage**, tính trên mỗi giờ EEG, đo trên **build đã freeze**, chạy lặp
  lại nhiều lần, báo **median và khoảng dao động** (không chỉ một con số điểm):
  - ingest/filter (đọc EDF + bandpass + notch)
  - adjacency + band-power (wPLI/AEC/top-k + 5 band powers)
  - GAE scoring (gồm cả per-node, từ Step 7)
  - CPD (PELT trên toàn timeline)
  - tổng end-to-end
  - *(tham chiếu: số cũ 9.76 s/giờ đo ở Step 1 chỉ là tổng, biến thiên ~5× giữa các lần chạy —
    Step 8/9 cần tách theo stage, không chỉ nhắc lại con số tổng đó.)*

- **Bằng chứng dữ liệu không rời máy:** backend và frontend không gọi request ra ngoài. Cách làm:
  chạy trọn một lượt Create-new → Process → xem Analysis khi đã tắt mạng máy, hoặc log toàn bộ
  network traffic trong một phiên và chỉ ra không có request nào ngoài `localhost`.

- **Operating point:** `SZSCAN_SPEC_v5.md` (mục O1) phải ghi chính xác tham số demo đang dùng
  (mag_pct/pen_mult hay tương đương, đọc từ `fp_budget_operating_point.py`/`RESULTS_OF_RECORD`).
  Report nói đây là operating point đã cố định trên validation — nếu thực tế demo đang dùng khác,
  báo trước khi chạy Tier 2, đừng để lộ ra lúc chấm.

---

## 2 · Luật cố định cho Tier 2 (chạy 8 subject TEST để phục vụ report) — chốt trước, không đổi giữa chừng

1. **Freeze build trước khi chạy** — commit + tag trong git, để mọi số liệu sau này đều truy được về
   đúng phiên bản code đã tạo ra chúng.
2. **DB sạch, chỉ 8 subject TEST** (`chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18`), xử lý
   từ file EDF thật qua đúng luồng Create-new → Process. **Không có file synthetic, không có event
   test nào còn sót lại** trong DB lúc chạy.
3. **Export mỗi subject một file**, gồm: tên file, onset/offset tính bằng giây tương đối trong file
   (không phải HH:MM:SS, không ngày lịch), source. **Export mọi event AI từ trước khi review** — bỏ
   qua trạng thái Accept/Reject/Uncertain (không lọc theo review status), **không lấy event Human**
   (Human event không thuộc kết quả detection).
4. **Demo không tự chấm điểm.** Script chấm nằm ở `src/`, do project thesis viết và giữ — vì nó cần
   đọc annotation (nhãn), mà demo tuyệt đối không được đụng tới (guard #2/#3).
5. **Nếu sau khi chấm phát hiện lỗi build**, chạy lại **toàn bộ** 8 subject, không chạy lại riêng một
   subject lẻ — tránh tình trạng một phần dữ liệu thuộc phiên bản code cũ, phần khác thuộc phiên bản
   mới.
6. **UI vẫn không hiển thị metric nào**, kể cả trong giai đoạn chạy Tier 2 này — luật này không đổi
   dù đang phục vụ report.

**Commit khi tới lúc:** chỉ `git add` các đường dẫn trong `web_demo/`. Không đụng `bme11/` hay các
file/kết quả thuộc project thesis (`rank_readout.py`, `results/attribution_v7/*`, v.v.) — những cái
đó do project thesis tự quản, tự commit.

---

## 3 · Việc cần làm khi bắt đầu Step 8/9

Trước khi soạn prompt cho Step 8 (Export) hoặc Step 9 (cache 8 subject), đọc lại file này trước, đối
chiếu với trạng thái thật của repo lúc đó (DB có đang sạch không, đã freeze chưa, đã có ảnh Figure 3.6
chưa) rồi mới viết prompt — đừng giả định đã làm xong phần nào ở đây chỉ vì file này liệt kê nó.
