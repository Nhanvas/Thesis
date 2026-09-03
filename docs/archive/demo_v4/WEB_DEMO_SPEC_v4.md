# WEB_DEMO_SPEC v4 — SzScan (bản chốt cuối, thay thế toàn bộ WEB_DEMO_SPEC_v3.md)

**Trạng thái: KHÓA để build.** File này là kết quả của 1 phiên làm việc chuyên biệt (product-spec session)
đối chiếu wireframe thật do tác giả tự thiết kế + userflow tự viết + tài liệu Persyst tham khảo. Mọi quyết
định trong file này đã được tác giả xác nhận trực tiếp, từng điểm một — không suy đoán, không kế thừa mù
quáng từ `WEB_DEMO_SPEC_v3.md` (bản đó **RÚT LẠI HOÀN TOÀN**, giữ lại trong `archive/` chỉ để tra cứu lịch
sử, không dùng để code).

**Nếu tài liệu này mâu thuẫn với bất kỳ file `.md`/`.py` nào khác nói về web demo, tài liệu này THẮNG.**

**Timeline ràng buộc:** report nộp 15/10, IELTS 9/10 → deadline cứng cho web chạy hoàn chỉnh = ~2 tuần
trước nộp report. Trình tự bắt buộc: **Phase B (tối ưu pipeline detection) xong → attribution (dựa trên
pipeline đã tối ưu) → build web demo.** Không build song song vì sợ 2 kết quả khác nhau giữa thesis và demo.

**Nguyên tắc xuyên suốt:** ưu tiên chạy được, đơn giản trước phức tạp, phần khó/không cần thiết cho 1 buổi
demo 15 phút → đẩy sang Future Work. Không thêm bất kỳ thuật toán/bước xử lý nào KHÔNG có trong pipeline
thesis thật, kể cả khi UI nhìn "thiếu" — thà thiếu 1 nút còn hơn có 1 nút không phản ánh gì thật (nguyên
tắc chống dàn dựng, vì đây là buổi bảo vệ học thuật, không phải demo sản phẩm thương mại).

---

## 0. SCOPE — không phải sản phẩm hoàn chỉnh

Đây là **demo phục vụ bảo vệ thesis + tư liệu viết report**, KHÔNG phải sản phẩm lâm sàng thương mại. Vai
trò của người review tài liệu này (Claude hoặc bất kỳ ai) là giữ đúng scope này — không đề xuất thêm tính
năng "cho đủ bộ sản phẩm thật" nếu nó không phục vụ trực tiếp mục tiêu demo/report.

**Guardrail chống over-claim** (PoC chưa validate lâm sàng; hậu-kiểm không phải real-time; latency ~0-7s
không phải "pre-ictal"; attribution PROVISIONAL chưa có groundtruth) — **KHÔNG thể hiện trên UI**, chỉ nói
bằng lời lúc bảo vệ. Không cần build panel/tooltip riêng cho việc này.

**Đăng nhập:** không cần (không có giá trị bảo mật thật cho 1 demo 15 phút, tốn công không cần thiết).

**Kích thước màn hình:** cả 2 trang (Database, Analysis) dùng đúng 1 khung website chuẩn (giống trang
Database) — Analysis chỉ dài hơn vì có nhiều panel, xử lý bằng cuộn dọc trong trình duyệt, không phải
layout đặc biệt hay responsive phức tạp.

---

## 1. CHIẾN LƯỢC DỮ LIỆU DEMO

- Phạm vi: **8 subject test** (chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18) — đúng 8 case
  held-out sinh ra số liệu locked của thesis (`RESULTS_OF_RECORD.md` §0).
- **Toàn bộ file .edf của cả 8 subject được chạy qua full pipeline thật trước, kết quả lưu cache local.**
  Đây không phải giả lập — là kết quả thật tính trước để tiết kiệm thời gian chờ lúc demo trực tiếp.
- Lúc demo: **nửa số subject upload trực tiếp** (khớp cache có sẵn → xử lý nhanh, ra kết quả gần như ngay
  lập tức), **nửa còn lại để sẵn trong Database từ trước** (phòng khi hội đồng muốn xem thao tác upload
  thật mà không cần chờ, hoặc phòng sự cố kỹ thuật lúc demo).
- **Nhận diện file trùng cache: so tên file** (không cần checksum nội dung — đơn giản, đủ dùng vì phạm vi
  chỉ 8 subject cố định đã biết trước).
- File lỗi định dạng/channel không khớp chuẩn CHB-MIT → **loại hoàn toàn khỏi pipeline và Database**, có
  toast báo ngắn lúc upload (vì demo dùng đúng 8 subject đã kiểm định trước, tình huống này gần như không
  xảy ra thật, nhưng vẫn cần xử lý cơ bản để tránh crash).

---

## 2. CẤU TRÚC — CHỈ 2 TRANG

1. **Database** (trang chủ) — quản lý danh sách subject/file, tạo mới, xóa, mở.
2. **Analysis** — xem EEG, timeline, review event, xem channel attribution. Vào từ Database bằng nút
   "Open".

Không có trang thứ 3. Mọi thao tác review/tạo event/export đều nằm trong trang Analysis.

---

## 3. TRANG DATABASE

### 3.1 Bảng chính (dạng cây/expandable)

| Cột | Ý nghĩa |
|---|---|
| ID | Tên subject (VD `chb02`), bấm ▶ để mở rộng ra danh sách file .edf con |
| No. files | Tổng số file .edf của subject |
| **Start Date** | *(đổi tên từ "Test Date" cho rõ nghĩa)* — ngày giờ bắt đầu của FILE ĐẦU TIÊN trong subject, format `YYYY.MM.DD HH:MM:SS` |
| Duration | Khoảng thời gian: `HH:MM:SS` nếu < 24h, `Nd:HH:MM:SS` nếu ≥ 24h (subject = tổng duration mọi file; file = end − start của chính nó) |
| Alert | Tổng số event hiện có (AI chưa Reject + User-added); subject = tổng của các file con |
| Status | `View` / `Viewing (x/N)` / `Viewed` — xem quy tắc §3.2 |
| Memo | Text tự do (giới tính/tuổi/loại cơn/ghi chú kỹ thuật...) |

Dòng con (file .edf) hiển thị cùng cấu trúc cột, trừ Status không có phân số (chỉ `View`/`Viewing`/`Viewed`
trơn) vì file không có "con" để tính tỷ lệ.

**Trong lúc 1 subject đang được xử lý (upload + preprocess + CPD), subject đó KHÔNG xuất hiện trên bảng.**
Chỉ khi toàn bộ pipeline (kể cả CPD) chạy xong, dòng subject + các dòng file con mới hiện lên cùng lúc. Nếu
đã có subject khác tồn tại từ trước, chúng vẫn hiển thị bình thường — chỉ riêng subject đang tạo mới thì ẩn.

### 3.2 Quy tắc Status (3 mức, áp dụng khác nhau ở 2 cấp)

**Cấp File:**
- `View` — đã xử lý xong (có kết quả CPD), chờ user xem
- `Viewing` — user đang xem dở, tiến độ tự lưu
- `Viewed` — user đã confirm/save xong (kể cả trường hợp chỉ reject hết hoặc chỉ thêm event mới, miễn đã
  bấm nút "Viewed" ở trang Analysis)

**Cấp Subject** (suy ra từ trạng thái các file con):
- `View` — TẤT CẢ file đều đang `View`
- `Viewed` — TẤT CẢ file đều đang `Viewed`
- `Viewing (x/N)` — mọi trường hợp còn lại (có ít nhất 1 file `Viewing` hoặc `Viewed`, nhưng chưa phải toàn
  bộ `Viewed`); **x = số file đã `Viewed`**, N = tổng số file. Hiển thị số này để phân biệt rõ với Status
  của file con (vốn không có phân số), tránh nhầm lẫn cấp subject vs cấp file khi nhìn bảng.

### 3.3 Công thức Alert

`Alert = (số event AI-detect CHƯA bị Reject) + (số event User-added)`

- Khi Reject 1 event AI → event đó không còn tính là seizure → Alert giảm 1.
- Event ở trạng thái `Uncertain` hoặc `Unseen` (chưa xem) vẫn được tính vào Alert (giữ nguyên như mặc định
  ban đầu trước khi review).
- Con số Alert trên Database **luôn phản ánh trạng thái review mới nhất** (không khóa cứng theo số AI gốc).

### 3.4 Tạo subject mới ("Create new")

Panel bên phải (giống overlay, không phải trang riêng):
- **Project ID** (text input)
- **Test date**: tự động lấy từ header của file .edf đầu tiên được upload (không cần nhập tay)
- **Memo** (text area, optional)
- Vùng kéo-thả **"Browse Files"** (nét đứt) — chọn TẤT CẢ file .edf liên quan của subject cùng lúc
- Danh sách file đã chọn hiện bên dưới, mỗi file có icon trạng thái riêng:
  - Vòng tròn xoay = đang tải lên. **Bấm vào ô vuông giữa vòng tròn để DỪNG upload file đó.**
  - Dấu ✕ = đã tải xong (bấm để xóa khỏi danh sách nếu chọn nhầm)
- Nút đen **"Process"** *(đổi tên từ "UPLOADS" để tránh nhầm lẫn với hành động chọn file)* — có 1 dòng ghi
  chú nhỏ bên dưới giải thích tác dụng (VD: "Sẽ xử lý toàn bộ file đã upload"). Nút này **disabled cho đến
  khi mọi file trong danh sách đều đã tải xong** (không còn vòng tròn xoay nào).

**Quan trọng — 2 giai đoạn xử lý:**
1. **Ngay khi 1 file .edf tải lên xong** (không cần đợi bấm Process): backend chạy full pipeline cho RIÊNG
   file đó — preprocessing → graph construction → GAE → LSTM → gamma AEC → ensemble score. **Chưa chạy
   CPD.** Đây là bước độc lập theo từng file, chạy càng sớm càng tốt để tiết kiệm thời gian tổng.
2. **Khi bấm "Process"** (chỉ khả dụng khi mọi file đã xong bước 1): backend **ghép ensemble score của
   TẤT CẢ file theo đúng thứ tự thời gian thành 1 timeline liên tục**, chạy PELT (CPD) **1 lần duy nhất**
   trên toàn bộ timeline này (đúng cách thuật toán cần đủ dữ liệu nền để ước lượng ổn định — không thể
   tách CPD ra chạy riêng từng file ngắn). Sau đó **kết quả event/detection được trả về đúng cho từng file
   tương ứng** dựa trên vị trí thời gian của event đó.
   - Ví dụ: nếu ensemble score ghép từ file 1→2→3, và CPD phát hiện 1 event nằm trong khoảng thời gian
     tương ứng với file 2, thì event đó được gán vào danh sách event của file 2.
3. Trong lúc bước 2 chạy: hiện màn hình loading full-panel (spinner + progress bar đơn giản, không phân
   biệt 2 giai đoạn con).
4. Xong → Database hiện subject mới (kèm mọi file con), Status = `View` cho tất cả.

**Đóng panel giữa chừng (bấm "−" minimize) khi đang upload hoặc đang Process:** không hủy — chuyển thành 1
toast nhỏ ở góc dưới phải ("Create New (draft)" khi đang upload, "Processing..." khi đang chạy Process),
tiếp tục chạy ngầm, user có thể quay lại xem tiếp bất kỳ lúc nào bằng cách bấm vào toast đó.

**Giới hạn xử lý song song toàn hệ thống:** tại 1 thời điểm, **chỉ CHÍNH XÁC 1 subject** (dù đang ở giai
đoạn upload hay Process) được phép chạy trên toàn hệ thống — không phân biệt có minimize hay không. Nếu
đang có 1 subject xử lý (kể cả đã minimize thành toast), bấm "Create new" cho subject khác sẽ bị chặn, hiện
thông báo yêu cầu chờ subject hiện tại xử lý xong.

**Không có chế độ Edit.** Muốn sửa thông tin/danh sách file của 1 subject đã tạo → xóa cả subject đó rồi
tạo lại từ đầu (lý do: sửa bắt buộc phải chạy lại CPD từ đầu — vì CPD phụ thuộc toàn bộ timeline ghép nối —
kéo theo mất mọi review cũ; giữ logic "sửa = tạo lại" đơn giản hơn nhiều so với việc thiết kế cơ chế bảo
toàn review khi CPD phải tính lại).

### 3.5 Xóa (Delete)

- **Chỉ xóa được ở cấp Subject** (xóa nguyên "folder" gồm mọi file con) — vì lý do kỹ thuật CPD nêu trên
  (không tách được 1 file ra khỏi timeline đã ghép mà không ảnh hưởng toàn bộ kết quả).
- Nếu đang chọn 1 dòng **file con** rồi bấm Delete → **không có gì xảy ra** (nút không phản hồi ở cấp file).
- Bấm Delete ở dòng **subject** → hiện màn hình xác nhận ("Bạn có chắc muốn xóa subject này? Toàn bộ dữ
  liệu và review sẽ mất, không thể khôi phục.") → Confirm mới xóa thật.

### 3.6 Các nút thao tác khác

- Chọn 1 dòng (subject hoặc file) → tô đậm.
- **Open** → sang trang Analysis, mở đúng subject/file đã chọn.
- **Cancel** → chỉ bỏ chọn dòng, không có tác dụng khác.

---

## 4. TRANG ANALYSIS

### 4.1 Header

| Thành phần | Ý nghĩa |
|---|---|
| `<ID> (<N> alerts to check)` | N = Alert của FILE ĐANG XEM (không khóa cứng, đồng bộ theo review mới nhất — giống số trên Database) |
| Previous / Next | Chuyển sang FILE trước/sau trong cùng subject (không phải chuyển event) |
| Nút "Viewed" | Bấm khi user xác nhận đã xem xong file này — cập nhật Status file đó thành `Viewed` |
| Nút "Export" | Xuất báo cáo `.txt` cho TOÀN BỘ subject (không phải chỉ file đang xem) — chỉ **enable khi TẤT CẢ file của subject đã `Viewed`** |
| Dropdown chọn file | Liệt kê toàn bộ file .edf của subject, mỗi dòng kèm số event trong ngoặc (VD "chb06_06.edf (2)"), bấm để nhảy trực tiếp sang file đó |
| Progress | `x/N` = số file đã `Viewed` trên tổng số file .edf của subject |

### 4.2 Panel Timeline (mini-timeline trên cùng)

- **Chỉ hiển thị phạm vi của FILE ĐANG XEM** (không ghép toàn subject).
- Mặc định hiển thị **1 giờ**, chia **6 ô, mỗi ô 10 phút**.
- 2 hàng: **Seizure Probability** (line chart theo ensemble score) + **Seizure Detections** (ô hình chữ
  nhật dài/ngắn theo duration của mỗi event).
- Trục thời gian: format `HH:MM:SS`, tính từ `File Start Time` (giờ thật trong file, KHÔNG dùng tiền tố
  ngày "dN" — vì đây là timeline của 1 file, không phải toàn subject).
  - *Range trục Seizure Probability: cần backend/CPD team xác nhận range thật của ensemble score (không
    mặc định cứng 0-1) — xem mục 6.1 "việc còn treo".*
- Có playhead (▼) đồng bộ với vị trí đang xem ở Panel EEG.
- Chỉ để XEM, **không tương tác được trực tiếp** — click chỉ hoạt động trên Panel EEG (mục 4.3).

### 4.3 Panel EEG

- Hiển thị raw EEG, **cố định đúng 18 kênh chuẩn** dùng trong pipeline (lọc bỏ mọi kênh phụ như
  EKG/EOG/Ref-channel nếu file gốc có thêm — VD chb13/14 có thêm EKG, chb15 có thêm 8 kênh FC/CP-Ref).
  Lý do: mọi thứ hiển thị phải là dữ liệu thật sự đi vào tính toán, tránh gây hiểu nhầm khi hội đồng hỏi.

**Toolbar** (từ trái sang phải):
| Nút | Chức năng |
|---|---|
| `⊲▷ [X] hr/min/sec` | Độ dài cửa sổ thời gian đang hiển thị TRÊN PANEL EEG này (độc lập với độ zoom 1 giờ của Panel Timeline). Bấm vào số để mở popover trượt dọc chọn nhanh (24hr → 1min). |
| `⇕ [X] uV` | Thang biên độ hiển thị sóng. **Cho tùy chỉnh** qua dropdown mức cố định sẵn (5/7/10/15/20/30 µV) — thuần frontend render lại, không đụng backend. |
| `⏮⏭ Select Range` | Kích hoạt chế độ tạo event thủ công (xem §4.5). |
| `lff 0.5 Hz` | Bandpass low-cut filter — khớp bước preprocessing thật (0.5–60 Hz). |
| `hff 60 Hz` | Bandpass high-cut filter — khớp bước preprocessing thật. |
| `60` (notch) | Notch filter 60Hz — khớp bước preprocessing thật. |

**Đã loại bỏ khỏi toolbar** (so với wireframe gốc/Persyst):
- Nút **"All"** — trong Persyst dùng để chọn/lọc kênh hiển thị; vì đã chốt cố định 18 kênh (không cho
  chọn/bớt), nút này không còn cần thiết.
- Nút **"ar" (Artifact Reduction)** — pipeline thesis KHÔNG có bước "làm sạch tín hiệu" tương ứng (chỉ có
  bước preprocessing "Amplitude artifact rejection" loại BỎ CẢ WINDOW vượt 5×SD, khác bản chất với 1 filter
  hiển thị bật/tắt được). Giữ nút này chỉ để "cho giống Persyst" sẽ là 1 tính năng UI không phản ánh gì
  thật — vi phạm nguyên tắc chống dàn dựng. Đã bỏ hẳn.
- Nút **"Comment" trên toolbar** (ghi chú tự do không gắn event) — không cần, vì đã có Comment gắn theo
  từng event trong Panel Event (đủ dùng cho mục đích demo).

**Trục thời gian dưới cùng:** format `HH:MM:SS` nếu file dưới 24 giờ, `Nd:HH:MM:SS` nếu file dài ≥ 24 giờ
(hiếm khi xảy ra ở cấp 1 file .edf, nhưng vẫn cần xử lý đúng theo quy tắc chung).

**Thanh scrub dưới cùng:** cố định 1 tốc độ phát lại — *(số giây/tốc độ cụ thể cần đề xuất thêm, xem mục
6.1 "việc còn treo")*, không cho user tùy chỉnh tốc độ.

**Tương tác Playhead:** chỉ click được trên Panel EEG (không click được trên Panel Timeline). Click vào 1
điểm trên grid EEG → playhead nhảy tới đó, đồng bộ cả Panel Timeline.

**Toggle filter (lff/hff/60):** khi bật, sóng đã lọc (filtered) hiển thị NỔI BẬT, sóng gốc (raw) hiển thị
MỜ làm nền phía sau — không ẩn hẳn raw, giống cách Persyst thể hiện.

### 4.4 Panel Event

- **2 tầng filter lồng nhau:**
  - Tầng 1: **All / Human / AI**
  - Tầng 2 (chỉ xuất hiện khi chọn "AI", vì event Human tự động coi là đã confirm khi tạo, không cần
    review thêm): **Accept / Reject / Uncertain / Unseen**
- Số đếm bên cạnh filter: format `x` (số đơn) khi filter = All hoặc Human; format `x/y` khi filter là 1
  nhãn con của AI (x = số event khớp nhãn đó, y = tổng số event AI trong file). VD: filter "Reject" hiện
  "1/3" nghĩa là 1 trong 3 event AI đang ở trạng thái Reject.
  - "All" cộng gộp cả Human + AI (VD 3 AI + 1 Human = hiện "4").
- Mỗi dòng event: cột Event (tên, VD "Seizure 1") / Onset (format `HH:MM:SS`) / Type (icon "AI" hoặc icon
  người cho Human) / mũi tên `▼` để mở rộng tại chỗ.
- **Event AI-detect, khi mở rộng:** Onset / Offset / Duration (đọc, không sửa được) + 3 lựa chọn
  **Accept / Reject / Uncertain** + ô Comment (text tự do) + nút **Save**.
  - **Không có chức năng sửa onset/offset của event AI.** Muốn sửa thì Reject event đó rồi tự tạo 1 event
    mới thay thế bằng "Select Range".
- **Event User-added, khi mở rộng:** Onset / Offset / Duration (đọc) + 2 nút **Delete / Edit** *(đã bỏ nút
  thứ 3 "??" từng thấy trong wireframe gốc — đó là sai sót cần xóa)* + ô Comment + nút **Save**.
- Sau khi Save: màu thanh dọc bên trái ô event đổi theo nhãn đã chọn (đề xuất: Accept = xanh lá, Reject =
  đỏ, Uncertain = vàng/cam, chưa chọn = không màu/xám trung tính). Event User-added mặc định có 1 màu riêng
  để phân biệt nguồn gốc (đề xuất: xanh dương) ngay cả trước khi có review status riêng.
- **Click 1 dòng event** (hoặc block tương ứng trên Panel Timeline/khu vực "Event Time" dưới Panel EEG) →
  đồng bộ ngay lập tức: Panel EEG nhảy tới đúng đoạn onset→offset, Panel Timeline cập nhật playhead, Panel
  Attribution hiện đúng dữ liệu của event đó. **Panel Event là nguồn điều khiển chính cho 3 panel còn lại.**
- **Trạng thái rỗng:** nếu file không có event nào do AI phát hiện (Alert = 0), Panel Event hiện trống,
  nhưng user vẫn có thể tự thêm event bằng "Select Range" như bình thường.

### 4.5 Tạo event thủ công (Select Range)

1. Bấm "Select Range" trên toolbar Panel EEG → kích hoạt chế độ đánh dấu.
2. Click 1 điểm trên grid EEG để đặt **onset** → xuất hiện 1 đường mốc dọc tại điểm đó.
3. Di chuột sang phải → 1 ô hình chữ nhật (màu xám, phân biệt với ô AI-detect màu đen/đậm hơn) kéo dài
   theo con trỏ trong khu vực "Event Time" dưới Panel EEG.
4. Click điểm thứ 2 để chốt **offset**.
5. Event mới **tự động chèn đúng vị trí thời gian** trong danh sách Panel Event (không phải luôn thêm vào
   cuối) — kèm icon người (Type = Human), Onset/Offset/Duration tự tính, không có Accept/Reject/Uncertain
   (vì tự tạo = tự confirm).
6. Panel Timeline cũng thêm 1 block mới tại vị trí tương ứng, màu khác với block AI để phân biệt nguồn.
7. Alert trên header + Database tự động +1 (vì đây là 1 User-added event mới).

### 4.6 Panel Channel Attribution

- **Chưa có kết quả thật tại thời điểm soạn spec này** — phụ thuộc Phase B (tối ưu pipeline detection)
  hoàn tất trước, sau đó mới chạy attribution trên pipeline cuối cùng. Phần dưới đây mô tả THIẾT KẾ UI,
  không phải dữ liệu đã có.
- **Hiển thị:** hình đầu đơn giản (vòng tròn ngoài + 18 vị trí điện cực chuẩn hệ 10-20, KHÔNG cần ảnh chi
  tiết/phức tạp) làm nền, vẽ đè lên **18 đường thẳng nối giữa 2 điện cực tương ứng mỗi kênh bipolar** (VD
  đường nối FP1↔F7 cho kênh "FP1-F7"), tô màu/độ đậm theo Score của kênh đó.
  - Lý do bắt buộc dùng đường nối thay vì chấm tròn tại 1 điểm: dữ liệu CHB-MIT là **bipolar** — mỗi kênh
    là hiệu điện thế giữa 2 điện cực, không phải giá trị tại 1 điểm đơn lẻ. Biểu diễn bằng chấm tròn sẽ sai
    bản chất dữ liệu.
- **Bảng bên dưới:** Rank / Channel / Score / Status. Rank **cố định theo thứ tự Score** (không cho user tự
  sắp xếp lại). Status là **segmented control Accept | Reject** (chỉ 1 lựa chọn/kênh — Accept và Reject
  không thể cùng chọn, giống radio button).
- Nút **Save** + **Clear all** ở cuối bảng.
- Đồng bộ theo event đang được chọn ở Panel Event — kể cả event do user tự tạo (vì attribution là số tính
  sẵn từ model, chỉ hiển thị lại, không phụ thuộc việc event đó có phải AI-detect hay không).
- **Trạng thái rỗng:** khi chưa click chọn event nào (VD vừa mở file lần đầu), Panel Attribution hiện
  trống/placeholder, không tự động hiện event đầu tiên.

---

## 5. EXPORT

### 5.1 Phạm vi

**1 file `.txt` duy nhất cho TOÀN BỘ subject** (gộp mọi file .edf con vào 1 file, giống hệt cấu trúc gốc
`chbXX-summary.txt` của CHB-MIT vốn cũng gộp nhiều file trong 1 file text).

### 5.2 Quy tắc ngôn ngữ: "Event" vs "Seizure"

Xuyên suốt UI lúc đang review, mọi thứ AI phát hiện được gọi là **"Event"** (vì AI không chắc chắn 100% —
đúng nguyên tắc đặt tên đã chốt ở đầu dự án). Nhưng trong **file export**, tại thời điểm export (chỉ khả
dụng khi toàn bộ file đã `Viewed` — tức bác sĩ đã xác nhận xong), mọi entry còn lại trong danh sách đã được
bác sĩ **chốt là seizure thật** (Accept/Uncertain giữ lại, Reject đã bị loại khỏi Alert, User-added coi như
tự confirm ngay khi tạo). Vì vậy:

- **Trong UI (Panel Event, Database, header...):** luôn dùng chữ **"Event"** / "Alert".
- **Trong file export `.txt`:** dùng chữ **"Seizure"** (VD `Number of Seizures in File`, giữ nguyên đúng
  quy ước của CHB-MIT gốc) — vì đây là bản ghi SAU-review, không còn là "nghi ngờ" của AI nữa.

### 5.3 Cấu trúc — kế thừa khung gốc CHB-MIT, chèn xen kẽ thông tin mới

Giữ nguyên định dạng gốc (Sampling Rate, Channel list, File Name/Start/End Time, Number of Seizures) để dễ
đối chiếu, **chèn thêm thông tin mới ngay sau mỗi event** (không tách thành phụ lục riêng):

```
Data Sampling Rate: 256 Hz
Channels in EDF Files:
Channel 1: FP1-F7
Channel 2: F7-T7
... (18 kênh chuẩn) ...

File Name: chb06_06.edf
File Start Time: 15:10:23
File End Time: 16:10:23
Number of Seizures in File: 2

Event 1
  Source: AI
  Review Status: Accept
  Start Time: 1230 seconds
  End Time: 1265 seconds
  Duration: 35 seconds
  Comment: (nội dung comment nếu có, để trống nếu không)
  Channel Attribution:
    Rank  Channel   Score   Status
    1     FP1-F7    3.5     Accept
    2     F7-T7     3.4     Reject
    3     T7-P7     2.6     Accept
    ...

Event 2
  Source: Human
  Start Time: 3480 seconds
  End Time: 3520 seconds
  Duration: 40 seconds
  Comment: (...)
  Channel Attribution:
    (giống cấu trúc trên — attribution vẫn tính cho event User-added)

File Name: chb06_07.edf
...
```

**Lưu ý định dạng thời gian trong export:** dùng **giây tính từ đầu FILE** (giống hệt annotation gốc
CHB-MIT: `Start Time: 1230 seconds`), KHÔNG dùng `HH:MM:SS` như trên UI — vì đây là file kỹ thuật để đối
chiếu/xử lý tiếp, không cần tối ưu cho việc đọc bằng mắt như màn hình xem trực tiếp.

---

## 6. VIỆC CÒN TREO — cần xử lý trước khi code

### 6.1 Cần xác nhận thêm (không phải mâu thuẫn, chỉ là quyết định kỹ thuật nhỏ chưa chốt số cụ thể)

- **Range trục "Seizure Probability"** trên Panel Timeline: giá trị ensemble score thật không cố định
  trong khoảng [0,1] (nó là z-score robust, có thể âm/dương tùy phân phối) — cần xác nhận cách hiển thị
  trục Y hợp lý (VD tự động scale theo percentile P1-P99 của chính file đó, tránh outlier kéo giãn trục).
- **Tốc độ cố định của thanh scrub** dưới Panel EEG — cần đề xuất 1 con số cụ thể (VD tốc độ phát = thời
  gian thật, hay nhanh hơn/chậm hơn 1 hệ số nào đó) trước khi code phần phát lại tự động (nếu có).
- Cả 2 điểm trên **không chặn việc bắt đầu code các phần khác** — có thể để giá trị mặc định tạm rồi tinh
  chỉnh sau khi có dữ liệu thật từ Phase B.

### 6.2 Phụ thuộc bên ngoài (blocking)

- Toàn bộ Panel Attribution (§4.6) đang ở dạng thiết kế UI, CHƯA có dữ liệu/API thật — chờ Phase B (tối ưu
  pipeline) hoàn tất, sau đó attribution chạy trên pipeline cuối cùng mới có số liệu để nối vào UI này.
- Wireframe cập nhật (bổ sung màn hình xác nhận xóa subject, sửa các nút đã đổi tên/loại bỏ) — tác giả sẽ
  gửi bản mới; khi có, đối chiếu lại phần trực quan (không ảnh hưởng nội dung logic đã chốt trong file này).

---

## 7. TÓM TẮT NHỮNG THAY ĐỔI SO VỚI WEB_DEMO_SPEC_v3.md (để tránh dùng nhầm thông tin cũ)

| Chủ đề | v3 (RÚT LẠI) | v4 (CHỐT — file này) |
|---|---|---|
| Kiến trúc timeline | Ghép toàn subject để chạy CPD, **cắt ngược `locate_range()` để hiển thị theo từng file** | Ghép toàn subject để chạy CPD (giữ nguyên) — nhưng **UI vốn đã hiển thị theo từng file từ đầu, không cần bước "cắt ngược"** vì kết quả CPD được backend trả thẳng theo từng file khi trả response |
| Edit subject | Có (không mô tả rõ) | **Không có** — sửa = xóa cả subject rồi tạo lại |
| Xóa | Không đề cập rõ cấp độ | Chỉ xóa được cấp Subject, không xóa được file lẻ, có confirm dialog |
| Nút "UPLOADS" | Tên "UPLOADS" | Đổi tên **"Process"**, có ghi chú nhỏ |
| Alert ở header Analysis | Ngụ ý khóa cứng (để so sánh AI gốc vs đã sửa) | **Không khóa cứng** — đồng bộ số hiện tại giống Database |
| Toolbar Panel EEG | Có "ar" (Artifact Reduction) | **Bỏ "ar"** — không khớp bước nào trong pipeline thật |
| Chọn kênh hiển thị | Không đề cập | **Cố định 18 kênh chuẩn**, không cho chọn/lọc (bỏ luôn nút "All") |
| Amplitude (uV) | Không đề cập | Cho tùy chỉnh qua dropdown mức cố định, thuần frontend |
| Panel Attribution | Chấm tròn tại điện cực | **Đường nối giữa 2 điện cực** (đúng bản chất bipolar) |
| Status subject | 3 mức đơn giản | Giữ 3 mức, thêm hiển thị tỷ lệ `Viewing (x/N)` ở cấp subject |
| Cột "Test date" | Giữ tên gốc | Đổi tên **"Start Date"** cho rõ nghĩa |
| Nhận diện cache | Không đề cập | So tên file (không checksum) |
| Giới hạn upload | Đề xuất ~50 file/lần | Không giới hạn cứng, chỉ cảnh báo mềm |
| Export format | Chỉ nói "tương tự chbXX-summary.txt" | Có cấu trúc chi tiết đầy đủ (§5.3) |
| Thuật ngữ Event vs Seizure | Không phân biệt | UI dùng "Event" (chưa chắc chắn); Export dùng "Seizure" (đã qua review — §5.2) |
| Giới hạn xử lý song song | Không rõ | Toàn hệ thống chỉ 1 subject xử lý nền tại 1 thời điểm |

---

*Hết WEB_DEMO_SPEC_v4.md. File này thay thế hoàn toàn WEB_DEMO_SPEC_v3.md làm nguồn duy nhất cho mọi quyết
định về web demo SzScan.*
