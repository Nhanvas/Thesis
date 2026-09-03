# WEB_DEMO_CODE_MIGRATION_NOTES.md — khuyến nghị xử lý code cũ sau khi chốt spec v4

**Bối cảnh:** `edf_order.py` và `edf_index.py` được viết dựa trên kiến trúc của `WEB_DEMO_SPEC_v3.md`
(ghép toàn subject thành 1 timeline liên tục để chạy CPD, rồi **cắt ngược kết quả về từng file để hiển
thị** bằng `EdfIndex.locate_range()`). Kiến trúc `v4` (đã chốt) vẫn giữ **backend ghép để chạy CPD**
(không đổi phần này), nhưng **bỏ bước "cắt ngược để hiển thị"** vì UI vốn đã hiển thị theo từng file —
kết quả CPD chỉ cần được backend gán thẳng vào đúng file tương ứng khi trả về, không cần 1 module riêng
để "cắt lại" cho mục đích render.

File này rà từng hàm, kết luận rõ: **giữ nguyên / sửa nhẹ / không còn cần thiết**, kèm lý do.

---

## 1. `edf_index.py` — GIỮ LẠI, VẪN CẦN THIẾT (không đổi logic)

**Vai trò thật của file này không phải "cắt để hiển thị"** như mô tả nhầm trong docstring gốc của nó
(hoặc trong cách `WEB_DEMO_SPEC_v3.md` §11 diễn giải) — nó là bảng tra cứu **(global_offset_s) → (file
nào, offset cục bộ trong file đó)**. Đây chính xác là thứ backend CẦN dùng ở bước 2 của kiến trúc v4: sau
khi CPD chạy ra danh sách event theo tọa độ global (giây tính từ đầu subject, do ghép nhiều file), backend
phải biết **event đó rơi vào file nào** để gán đúng — đây chính là việc `EdfIndex.locate_range()` làm.

| Hàm | Kết luận | Ghi chú |
|---|---|---|
| `EdfIndex.__init__` | **GIỮ NGUYÊN** | Xây time-index 1 lần cho mỗi subject, dùng đúng parser đã khóa (`evaluation_protocol.parse_summary_edf_list`) — không đổi gì. |
| `EdfIndex.locate()` | **GIỮ NGUYÊN** | Cần dùng để map 1 điểm thời gian (VD onset của 1 event global) về đúng file + offset cục bộ. |
| `EdfIndex.locate_range()` | **GIỮ NGUYÊN, nhưng đổi MỤC ĐÍCH SỬ DỤNG** | Trước đây (v3) dùng để cắt lại đoạn EEG hiển thị cho UI theo từng file. Nay (v4) dùng để: với 1 event global (onset_s, offset_s) do CPD trả ra, xác định event đó **thuộc file nào** (và offset cục bộ trong file đó) để backend gán event vào đúng danh sách event của file tương ứng trước khi trả response cho frontend. Bản chất thuật toán không đổi, chỉ đổi ngữ cảnh gọi hàm. |

**Hành động cụ thể:** không cần sửa 1 dòng code nào trong `edf_index.py`. Chỉ cần viết lại phần
docstring/comment ở đầu file cho đúng vai trò mới (nói rõ: dùng để gán event global về đúng file, không
phải để "cắt EEG hiển thị"), tránh gây hiểu nhầm cho người đọc code sau này.

---

## 2. `edf_order.py` — GIỮ LẠI, VAI TRÒ KHÔNG ĐỔI

File này giải quyết vấn đề: **thứ tự HIỂN THỊ file trên UI** (Previous/Next, dropdown chọn file, progress
dots) có thể khác thứ tự file dùng để build timeline chạy CPD (vì CPD sort theo TÊN FILE — quy ước đã khóa
để khớp mọi kết quả locked của thesis — trong khi hiển thị nên sort theo GIỜ THẬT ghi trong header EDF, vì
có trường hợp lệch tên/giờ như `chb03_24.edf`/`chb03_25.edf`).

Vai trò này **không hề bị ảnh hưởng** bởi việc bỏ cơ chế "cắt ngược để hiển thị" — đây là 2 vấn đề độc
lập nhau:
- `edf_index.py` giải quyết: "event này thuộc file nào" (thời gian → file)
- `edf_order.py` giải quyết: "file này nên hiện ở vị trí thứ mấy trên danh sách UI" (thứ tự hiển thị)

| Hàm | Kết luận | Ghi chú |
|---|---|---|
| `parse_summary_sorted_by_header()` | **GIỮ NGUYÊN** | Vẫn cần đúng như thiết kế ban đầu — sort hiển thị theo header time, có heuristic hoán đổi cặp liền kề lệch giờ nhỏ. |
| `_hms_to_seconds()` | **GIỮ NGUYÊN** | Hàm phụ trợ thuần túy, không đổi. |

**Hành động cụ thể:** không cần sửa gì. File này độc lập với thay đổi kiến trúc v3→v4, tiếp tục dùng đúng
như thiết kế ban đầu.

---

## 3. Điểm MỚI cần code — chưa có file nào đảm nhiệm (do kiến trúc v4 phát sinh)

Kiến trúc v4 rõ ràng hơn v3 ở việc tách 2 giai đoạn xử lý (per-file trước, CPD ghép sau) — nhưng **chưa có
module nào trong project hiện tại đảm nhiệm bước "gộp ensemble score của N file theo đúng thứ tự TÊN FILE
thành 1 mảng liên tục"** trước khi đưa vào `cpd_pipeline_v14.detect_events`. Đây là phần code MỚI cần viết
khi bắt đầu build backend demo (không phải sửa file cũ), gợi ý luồng:

```
for mỗi file .edf đã upload (theo đúng thứ tự TÊN FILE, không phải thứ tự hiển thị):
    ensemble_score_theo_file[i] = kết quả bước 1 (đã tính sẵn lúc upload)

toàn_bộ_ensemble_score = nối tất cả ensemble_score_theo_file[i] theo đúng thứ tự trên
events_global = cpd_pipeline_v14.detect_events(toàn_bộ_ensemble_score, ...)   # label-free, không inter_mask

for mỗi event trong events_global:
    file_tương_ứng, offset_cục_bộ = EdfIndex(subject).locate_range(event.onset_s, event.offset_s)
    gán event vào danh_sách_event[file_tương_ứng]   # <-- đây là chỗ edf_index.py phát huy tác dụng
```

Đây là logic nghiệp vụ (business logic) của bước "Process", nên đặt trong 1 module backend mới của demo
(VD `pipeline_service.py` theo đúng tên đã có sẵn trong khung thư mục cũ), KHÔNG viết đè lên
`cpd_pipeline_v14.py`/`edf_index.py`/`edf_order.py` (3 file này là single-source dùng chung với thesis,
không được sửa nội dung thuật toán).

---

## 4. Tóm tắt hành động

| File | Hành động | Lý do |
|---|---|---|
| `edf_index.py` | Giữ nguyên code, sửa lại docstring/comment cho đúng vai trò mới | Logic không đổi, chỉ đổi ngữ cảnh sử dụng (gán event→file thay vì cắt EEG hiển thị) |
| `edf_order.py` | Giữ nguyên hoàn toàn | Vai trò độc lập với thay đổi kiến trúc, không bị ảnh hưởng |
| Module ghép ensemble + gọi CPD + gán event về file | **Cần viết mới** | Chưa tồn tại trong project, là phần lõi của bước "Process" trong kiến trúc v4 |
| `WEB_DEMO_SPEC_v3.md` | Archive, không dùng để code | Đã bị thay thế hoàn toàn bởi `WEB_DEMO_SPEC_v4.md` |
