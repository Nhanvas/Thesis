# SZSCAN_SPEC_v5.md — bản chốt để BUILD

**Trạng thái: KHÓA.** File này **thay thế hoàn toàn** `WEB_DEMO_SPEC_v4.md` và
`WEB_DEMO_CONTEXT_BOUNDARY.md`. Hai file đó chuyển sang `docs/archive/demo_v4/`, **không dùng để code**.

**Thứ tự thẩm quyền cho mọi việc liên quan web demo:**
`UI/` (PNG bản chốt — thắng về mọi thứ nhìn thấy được) > file này (hành vi/logic/ranh giới) >
`SZSCAN_DESIGN_v2.md` (token màu/chữ/khoảng cách) > `DEMO_BUILD_HANDOFF.md` (stack/quy trình).

Với các quyết định khoa học (không phải demo), thẩm quyền vẫn là
`docs/RESULTS_OF_RECORD_phaseB.md` > `docs/PROVENANCE.md` > `docs/REPO_MAP.md`.

**Lịch sử:** v5 = v4 + 11 điểm chốt UI (phiên audit 2026-09) + 13 điểm sửa M1–M13 (phiên này) +
kiến trúc label-free liên tục (mới, dựa trên phép đo — xem §1).

---

## 0 · SCOPE VÀ FRAMING

Đây là **demo phục vụ bảo vệ thesis**, không phải sản phẩm lâm sàng. Framing bắt buộc:
**post-hoc EEG review triage** — hỗ trợ bác sĩ rà lại bản ghi đã có, **KHÔNG phải cảnh báo real-time**.

Nguyên tắc chống dàn dựng: không thêm bất kỳ thuật toán/bước xử lý nào không có trong pipeline thật.
Thà thiếu 1 nút còn hơn có 1 nút không phản ánh gì thật.

**Guardrail chống over-claim — ĐỔI SO VỚI v4:** v4 cấm hiển thị trên UI. **Nay hiển thị thường trực**
ở footer mọi màn hình (trừ màn Log in, là màn tiền-ứng-dụng):

> `SzScan is an AI-assisted tool designed to support clinicians, not replace them.`

Lý do đảo: minh bạch bằng sản phẩm tốt hơn minh bạch bằng lời, và buổi bảo vệ có thể không đủ thời gian
để nói. (Quyết định của tác giả, 2026-09.)

**Đăng nhập — ĐỔI SO VỚI v4:** v4 nói không cần. **Nay có** 1 màn Log in, 1 tài khoản admin cố định.
Không có đăng ký, không quên/đổi mật khẩu. Lý do: truy cập dữ liệu bệnh nhân nên cần 1 bước chặn; đây là
bước tượng trưng cho đúng hình hài sản phẩm, **không phải cơ chế bảo mật thật**.

---

## 1 · KIẾN TRÚC XỬ LÝ — ĐỌC TRƯỚC KHI VIẾT BẤT KỲ DÒNG BACKEND NÀO

### 1.1 Vì sao không thể phát lại kết quả đã khóa của thesis

Đo ngày 2026-09-03, từ chính code trong repo:

| # | Sự thật đo được | Nguồn |
|---|---|---|
| F1 | `results/phaseB/tier2/ens_test_tf/rlg/ens_seed42_{subj}_{inter,ictal}.npy` là mảng **theo segment**, không theo thời gian. Không tồn tại index window→giây | liệt kê thư mục |
| F2 | `szcore_eval.build_timeline_masked()` dựng lại timeline **bằng ground-truth annotation** — đọc `edf['seizures']` rồi đặt score ictal vào đúng vị trí nhãn | `src/szcore_eval.py:98–109` |
| F3 | Window trong buffer 4h và window interictal thiếu được **lấp bằng bootstrap resample** từ phân phối interictal — giá trị tổng hợp, không phải score thật tại vị trí đó | `src/szcore_eval.py:90, 111–113, 120–123` |
| F4 | `preprocessing.py` Step 4 **loại** window vượt ±5 SD khỏi `{subj}_interictal.npy`; con trỏ `inter_ptr` chạy tuần tự → score interictal thật **trôi vị trí thời gian** đúng bằng `n_rejected` | `preprocessing.py` Step 4 + `szcore_eval.py:117–119` |

**Hệ quả:** thông tin vị trí thời gian đã mất từ bước preprocessing. Không có cách khôi phục bằng code
thêm. Mọi phương án "cache kết quả thesis rồi vẽ lên trục thời gian" đều **sai về mặt dữ liệu**.

### 1.2 Điều cấm tuyệt đối

**Demo KHÔNG ĐƯỢC:**
1. gọi `szcore_eval.build_timeline_masked()` hoặc bất kỳ hàm nào dựng timeline từ nhãn;
2. đọc trường `seizures` / `Seizure Start Time` / `Seizure End Time` từ `chb*-summary.md` lúc runtime;
3. dùng `{subj}_interictal.npy` / `{subj}_ictal.npy` (hai mảng này được tách **bằng nhãn**);
4. ghi vào `results/`, `data/models_retrain/`, `docs/`, hay bất kỳ artifact khóa nào của thesis.

Điểm 1–3 không phải quy ước phong cách. Vi phạm = rò ground-truth vào một sản phẩm được giới thiệu là
label-free. Đó là lỗi liêm chính, và là câu hỏi đầu tiên một hội đồng tinh ý sẽ hỏi.

`chb*-summary.md` **vẫn được đọc** cho: danh sách file, `File Start Time`, `File End Time`, duration.
Chỉ trường seizure là cấm.

### 1.3 Kiến trúc chốt: chạy lại thật, label-free, liên tục

Demo chạy **cùng mô hình đã khóa** (`data/models_retrain/gae_joint_seed42.pt`) trên **bản ghi liên tục**,
không tách interictal/ictal, không loại window, không dùng nhãn ở bất kỳ đâu.

```
file .edf
 → đọc 18 kênh chuẩn (bỏ EKG/EOG/Ref nếu file gốc có)
 → bandpass 0.5–60 Hz + notch 60 Hz          (giống thesis)
 → cắt window 4 s không chồng lấn @256 Hz    (giống thesis, KHÔNG bỏ window nào)
 → z-score per-channel                        (⚠ xem §1.6)
 → CAR → wPLI + AEC → top-k 20%
 → band-powers 5 dải → node feat [adj-row 18 | bp 5]
 → Joint GAE seed42 → zrecon + zlatent(⚠ §1.6) ; gamma-AEC → zgamma
 → robust-z từng nhánh (⚠ §1.6) → ensemble equal 1/3
 → [ghép mọi file của subject theo thứ tự TÊN FILE]
 → PELT (cpd_pipeline_v14) chạy MỘT lần trên timeline ghép
 → operating point label-free (FP-budget)
 → gán event global về đúng file bằng offset tích lũy (§1.5)
```

**Không có window nào bị bỏ** ⇒ chỉ số window ↔ giây trong file là ánh xạ 1-1 tuyệt đối:
`t_giây = window_index × 4`. Đây chính là thứ mà đường xử lý của thesis đã đánh mất.

### 1.5 Gán event về file — không cần module tra cứu

Vì mảng score của mỗi file có độ dài **đúng bằng số window của chính file đó**, offset của từng file
suy ra được **theo cấu tạo**:

```python
offsets, cur = {}, 0
for f in files_sorted_by_name:
    offsets[f] = cur
    cur += len(score[f])
# event global (on, off) thuộc file f khi  offsets[f] <= on < offsets[f] + len(score[f])
# offset cục bộ = on - offsets[f]
```

Không parse file nào, không đọc summary, không cần module phụ — **và điều này tự động thỏa guard số 2
ở §1.2**, vì không còn đọc `chb*-summary.md` lúc chạy.

⚠️ **`edf_index.py` không tồn tại trong repo và không cần viết lại.** Nó thuộc kiến trúc v3 (khi score
là mảng theo segment nên phải dựng bảng tra `global_offset → file`) và đã bị xóa. Tài liệu cũ
`WEB_DEMO_CODE_MIGRATION_NOTES.md` mô tả nó như module sẵn có — tài liệu đó đã archive, đừng dùng.
`edf_order.py` thì **vẫn giữ** (`web_demo/backend/edf_order.py`): vấn đề khác hẳn — thứ tự **hiển thị**
file trên UI theo giờ thật trong header EDF, khác thứ tự **xử lý** theo tên file.

### 1.6 Divergence có chủ đích khỏi pipeline thesis — ĐÃ ĐƯỢC TÁC GIẢ DUYỆT

Có **hai nhóm divergence**, cùng một nguyên nhân gốc: bệnh nhân mới không có nhãn.

#### (a) Bốn bước fit trên "mảng interictal"

Bệnh nhân mới không có mảng đó. Demo fit cả bốn trên **toàn bộ window của subject**:

| Bước | Thesis fit trên | Demo fit trên |
|---|---|---|
| z-score stats (mean/std per channel) | interictal | toàn bộ window |
| ngưỡng artifact 5 SD | interictal | **bỏ hẳn** (không loại window nào — cần giữ vị trí thời gian) |
| `LedoitWolf().fit(Zi)` cho `zlatent` | latent của interictal | latent của toàn bộ window |
| ~~robust-z median/MAD từng nhánh~~ | **toàn bộ window** | **toàn bộ window** — *không phải divergence* |

**robust-z không phải divergence.** `retrain_io.robust_z(raw_i, raw_c)` dòng 56–60 đã fit median/MAD
trên `np.concatenate([raw_i, raw_c])` — tức toàn bộ window. Demo làm y hệt thesis. Bảng trên giữ dòng này
gạch ngang để phiên sau không đi kiểm tra lại.

**Biện minh:** tỷ lệ window ictal cực thấp — đo trên chb06: 45 / (19826 + 45) = **0.23 %**. Không đủ để
kéo lệch covariance, median hay MAD một cách có ý nghĩa.

**ĐÃ KIỂM CHỨNG BẰNG PHÉP ĐO — 2026-09-03. Không cần chạy lại.**

Tiêu chí đặt trước khi chạy: PASS nếu Spearman ≥ 0.98 **và** |ΔAUROC| ≤ 0.02 trên cả hai subject.

| subject | AUROC (fit interictal — thesis) | AUROC (fit toàn bộ — demo) | Spearman | n_int / n_ict |
|---|---|---|---|---|
| chb06 | 0.6066 | 0.6051 | **1.0000** | 19826 / 45 |
| chb13 | 0.6493 | 0.6408 | **0.9999** | 12452 / 144 |

→ **PASS.** Đổi cách fit LedoitWolf gần như không làm đổi `zlatent` (thứ hạng gần như đồng nhất,
ΔAUROC 0.0015 / 0.0085). Divergence (a) là vô hại về mặt đo lường.

⚠️ Phép đo này **chỉ** phủ `zlatent`. Ba thứ còn lại — z-score stats, bỏ lọc artifact, và **hậu-cơn (b)**
— cần tiền xử lý liên tục từ EDF nên chỉ quan sát được ở bước 1 của thứ tự build.

#### (b) Đoạn hậu-cơn không bị loại — nguồn khác biệt LỚN HƠN nhóm (a)

`preprocessing.py` loại **4 giờ sau mỗi cơn** khỏi mảng interictal của thesis (`BUFFER_H`). Demo không
biết cơn ở đâu nên **không loại được gì** — toàn bộ đoạn hậu-cơn đi thẳng qua PELT.

EEG hậu-cơn bất thường thật (chậm khu trú, suy giảm biên độ, kết nối chức năng thay đổi). Nhiều khả năng
demo sẽ **gắn cờ các đoạn đó**, trong khi thesis chưa từng chấm điểm chúng.

Về lượng, đây là nguồn khác biệt lớn hơn hẳn nhóm (a): 4 giờ × số cơn, so với 0.23 % window ictal.

**Đây không phải lỗi.** Trong khung post-hoc review triage, đưa đoạn hậu-cơn ra cho bác sĩ xem là hành vi
hợp lý về lâm sàng — bác sĩ vẫn muốn nhìn đoạn đó. Nhưng nó phải được:
1. **quan sát ở bước 1** của thứ tự build (chạy 1 subject, xem event rơi vào đâu so với cơn đã biết —
   *chỉ để mắt người kiểm tra tính hợp lý, tuyệt đối không đưa nhãn vào code*);
2. **nói ra khi bảo vệ**, không để hội đồng tự phát hiện.

**Hệ quả bắt buộc ghi nhận (cho cả (a) và (b)):**
- **Số của demo sẽ KHÁC số của thesis.** Không được ép khớp, không được điều chỉnh gì để khớp.
- Demo **không** hiển thị bất kỳ metric đánh giá nào (sensitivity, FP/day, AUROC, operating point
  mag_pct/pen_mult). Những con số đó thuộc thesis, không thuộc sản phẩm.
- Divergence này phải được **báo cô** (Assoc. Prof. Hà Thị Thanh Hương) vì là quyết định phương pháp.

**Câu trả lời chuẩn bị sẵn cho hội đồng** — *"tại sao demo tìm ra event khác bảng trong report?"*:
> Report đánh giá trên phân đoạn interictal đã lọc nhiễu, đã loại 4 giờ hậu-cơn, và có nhãn, theo giao
> thức SzCORE. Demo chạy hoàn toàn không nhãn trên bản ghi liên tục nguyên vẹn — kể cả đoạn hậu-cơn —
> vì đó mới là tình huống của một bệnh nhân mới. Cùng một mô hình, cùng trọng số, hai điều kiện đầu vào
> khác nhau, nên hai tập kết quả không đồng nhất là đúng như dự kiến, không phải bất thường. Cụ thể,
> demo có thể gắn cờ đoạn hậu-cơn mà report không hề chấm điểm; trong bối cảnh rà soát hậu kỳ thì đó là
> hành vi hợp lý, không phải dương tính giả.

### 1.7 Chi phí — đã đo, quyết định chạy live

Đo trên máy dev (Dell Latitude 3590, CPU): `build_adjacency` **13.2 ms/window** + `compute_band_powers`
**3.7 ms/window** = **16.9 ms/window** → **~15 s cho 1 giờ EEG** (chưa kể đọc EDF, gamma-AEC, GAE
forward — đều nhỏ hơn nhiều).

**Chốt:**
- Upload → chạy pipeline **thật**, không giả lập, không replay. Mâu thuẫn "nửa cache / nửa live" của v4
  biến mất: cả hai nửa đều thật.
- Vẫn dựng **cache trước cho 8 subject** nhưng chỉ làm **bảo hiểm** lúc bảo vệ (máy trục trặc / hội đồng
  không muốn chờ). Cache chứa output thật của chính pipeline demo, chỉ là tính sớm.
- Khớp cache **bằng tên file** (không checksum) — phạm vi 8 subject cố định đã biết trước.
- Bước "Process" (PELT toàn subject) là chỗ tốn thời gian nhất. Kịch bản demo trực tiếp nên chọn subject
  **ít file nhất**; con số cụ thể đo lúc dựng cache.

---

## 2 · PHẠM VI DỮ LIỆU

- **Allowlist cứng 8 subject TEST:** `chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18`.
- File thuộc subject ngoài danh sách → **từ chối**, toast:
  `This demo is restricted to the held-out test subjects.`
- **Lý do (quan trọng, không được nới):** live compute nay chạy được mọi file CHB-MIT. Nếu không chặn,
  hội đồng upload `chb01` là demo đang chạy trên **dữ liệu huấn luyện** — tự đâm vào câu hỏi khó nhất mà
  cả thesis đã cẩn thận tránh. Bảng mock trong `UI/A4a` có chb01/02/04… chỉ là **dữ liệu minh họa**.
- File sai định dạng / thiếu kênh chuẩn → loại khỏi pipeline và Database, toast:
  `File rejected — unsupported format or channel configuration.`

---

## 3 · CẤU TRÚC — 3 MÀN

1. **Log in** — 1 tài khoản admin cố định.
2. **Database** (trang chủ) — danh sách subject/file, tạo mới, xóa, mở.
3. **Analysis** — xem EEG, timeline, review event, channel attribution.

Không có màn thứ 4. Cả Database và Analysis dùng chung một khung website chuẩn; Analysis dài hơn và cuộn
dọc bình thường, không phải layout đặc biệt.

---

## 4 · MÀN LOG IN

- 1 tài khoản duy nhất, **ID và mật khẩu đặt trong `.env` của backend** — không hardcode ở frontend
  (devtools đọc được). Không đăng ký, không quên/đổi mật khẩu.
- Ô mật khẩu **phải mask** (`type="password"`). Ảnh mock hiện chữ rõ chỉ để minh họa.
- Không có footer disclaimer ở màn này (màn tiền-ứng-dụng).
- Avatar góc phải header sau khi đăng nhập → dropdown **Log out** (xem `UI/A0b`).
- Đây **không phải** cơ chế bảo mật thật. Không lưu gì nhạy cảm, session đơn giản là đủ.

---

## 5 · MÀN DATABASE

### 5.1 Bảng chính (dạng cây, mở rộng được)

| Cột | Ý nghĩa |
|---|---|
| ID | Tên subject (vd `chb06`), bấm ▶ mở rộng ra danh sách file .edf con |
| No. files | Tổng số file .edf của subject |
| Start date | Ngày giờ bắt đầu của **file đầu tiên**, format `YYYY.MM.DD HH:MM:SS`. **Tự suy ra từ header EDF**, không có ô nhập tay |
| Duration | `HH:MM:SS` nếu < 24 h, `Nd:HH:MM:SS` nếu ≥ 24 h. Subject = tổng duration mọi file; file = end − start của chính nó |
| Alert | Tổng số event hiện có (xem §5.3) |
| Status | `View` / `Viewing (x/N)` / `Viewed` (xem §5.2) |
| Memo | Text tự do do người dùng nhập (giới tính/tuổi/ghi chú). **Không bao giờ được sinh tự động** từ mô hình |

Dòng file con dùng cùng cấu trúc cột, riêng Status không có phân số.

**Trong lúc 1 subject đang xử lý (upload + pipeline + CPD), subject đó KHÔNG xuất hiện trên bảng.** Chỉ
khi toàn bộ chạy xong, dòng subject + mọi dòng file con mới hiện lên cùng lúc. Subject khác đã có từ
trước vẫn hiển thị bình thường.

### 5.2 Quy tắc Status

**Cấp file:** `View` (đã xử lý xong, chờ xem) / `Viewing` (đang xem dở, tiến độ tự lưu) / `Viewed` (đã
bấm nút "Viewed" ở màn Analysis).

**Cấp subject:** `View` nếu TẤT CẢ file đều `View`; `Viewed` nếu TẤT CẢ đều `Viewed`; còn lại là
`Viewing (x/N)` với **x = số file đã `Viewed`**, N = tổng số file. Phân số chỉ có ở cấp subject — để phân
biệt rõ với cấp file khi nhìn bảng.

### 5.3 Công thức Alert

```
Alert = (số event AI-detect CHƯA bị Reject) + (số event User-added)
```

- Reject 1 event AI → Alert giảm 1.
- `Uncertain` và `Unseen` **vẫn tính** vào Alert.
- Alert luôn phản ánh trạng thái review mới nhất, không khóa cứng theo số AI gốc.
- Hiển thị màu trung tính (không amber, không đỏ) — xem `SZSCAN_DESIGN_v2.md`.

### 5.4 Ô Search

- Lọc theo **tên file hoặc tên subject**. Gõ xong bấm **nút search** — không auto-filter theo từng ký tự.
- Khớp tên 1 file con → bảng chỉ còn subject chứa file đó, subject **tự expand**, và **chỉ hiện file
  khớp** (file khác của subject đó tạm ẩn; xóa search thì hiện lại đủ).
- Khớp tên subject → hiện subject đó với đầy đủ file con, trạng thái collapsed.
- Không khớp → khối "No data" nhưng đổi chữ thành `No results for '...'`.
- Không phân biệt hoa/thường, cho phép khớp một phần.

### 5.5 Tạo subject mới ("Create new")

Panel overlay bên phải (`UI/A1a`):
- **Project ID** (text input)
- **Memo** (text area, optional)
- Vùng kéo-thả **Browse Files** (nét đứt) — chọn tất cả file .edf của subject cùng lúc
- **Không có ô "Test date"** — giá trị này tự suy ra từ header EDF và chỉ xuất hiện ở cột `Start date`
  trên bảng Database *(đổi so với v4, nơi nó còn là 1 ô trong panel)*
- Danh sách file đã chọn hiện bên dưới, mỗi file 1 icon trạng thái:
  - vòng tròn xoay = đang tải; **bấm ô vuông giữa vòng tròn để DỪNG** upload file đó
  - dấu ✕ = đã tải xong (bấm để bỏ khỏi danh sách)
- Nút đen **Process** + 1 dòng ghi chú nhỏ bên dưới. **Disabled cho tới khi mọi file đã tải xong.**

**Hai giai đoạn xử lý:**

1. **Ngay khi 1 file tải xong** (không đợi bấm Process): backend chạy pipeline §1.3 cho riêng file đó,
   **dừng trước CPD**, ra 1 mảng ensemble score liên tục theo thời gian của file.
2. **Bấm Process:** ghép ensemble score của **tất cả file theo đúng thứ tự TÊN FILE** thành 1 timeline
   liên tục → chạy PELT **một lần duy nhất** trên toàn bộ timeline (thuật toán cần đủ nền để ước lượng
   ổn định, không tách chạy từng file ngắn) → dùng `edf_index.locate_range()` gán mỗi event global về
   đúng file theo vị trí thời gian.
3. Trong lúc chạy: loading full-panel (spinner + progress bar đơn giản, **không** phân biệt 2 giai đoạn
   con, **không** hiện % giả).
4. Xong → Database hiện subject mới + mọi file con, Status = `View`.

**Minimize giữa chừng (nút "−"):** không hủy. Thu thành toast góc dưới phải —
`Create New (draft)` khi đang upload, `Processing...` khi đang chạy Process. Chạy tiếp ngầm, bấm toast để
quay lại.

**Giới hạn song song:** toàn hệ thống **chỉ đúng 1 subject** được xử lý tại một thời điểm, kể cả đã
minimize. Bấm "Create new" khi đang có subject chạy → chặn, hiện thông báo yêu cầu chờ (`UI/A1d`).

**Không có chế độ Edit.** Muốn sửa → xóa cả subject rồi tạo lại. Lý do: sửa buộc phải chạy lại CPD trên
toàn timeline ghép, kéo theo mất mọi review cũ; "sửa = tạo lại" đơn giản hơn nhiều so với thiết kế cơ chế
bảo toàn review.

### 5.6 Xóa

- **Chỉ xóa được cấp Subject.** Chọn dòng file con rồi bấm Delete → không phản hồi.
- Có màn xác nhận. **Dùng chung 1 câu cho mọi trường hợp xóa** (đang xử lý dở hay đã hoàn tất) — không
  tách 2 câu *(chốt của tác giả, khác v4)*.

### 5.7 Nút khác

Chọn 1 dòng → tô đậm. **Open** → sang Analysis đúng subject/file đã chọn. **Cancel** → chỉ bỏ chọn dòng.

---

## 6 · MÀN ANALYSIS

### 6.1 Header

| Thành phần | Ý nghĩa |
|---|---|
| `<ID> (<N> alerts to check)` | N = Alert của **file đang xem**, đồng bộ theo review mới nhất |
| Previous / Next | Chuyển **file** trước/sau trong cùng subject (không phải chuyển event) |
| Viewed | Đánh dấu file đang xem là `Viewed` |
| Export | Xuất báo cáo `.txt` cho **toàn bộ subject**. **Chỉ enable khi mọi file của subject đã `Viewed`** |
| Dropdown chọn file | Liệt kê mọi file .edf của subject, kèm số event trong ngoặc: `chb06_06.edf (2)` |
| Progress | `x/N` = số file đã `Viewed` / tổng số file |

### 6.2 Định dạng thời gian — một rule duy nhất

Áp dụng **đồng bộ cho mọi trục thời gian cấp file** (mini-timeline và trục dưới Panel EEG):

- `HH:MM:SS` nếu file < 24 h
- `dN:HH:MM:SS` nếu ≥ 24 h

*(Bỏ ngoại lệ cũ của v4 "mini-timeline không bao giờ dùng dN".)* Ảnh mock hiện `d1 …` chỉ là chọn ví dụ
minh họa cho trường hợp ≥ 24 h; `UI/B0b` minh họa trường hợp < 24 h.

### 6.3 Panel Timeline (mini, trên cùng)

- **Chỉ hiển thị phạm vi file đang xem**, không ghép toàn subject.
- Mặc định 1 giờ, chia 6 ô × 10 phút.
- Hai hàng: **Seizure Detection Score** (line chart theo ensemble score) và **Detections** (block chữ
  nhật dài/ngắn theo duration mỗi event).
  - Tên hàng thứ nhất **không được** dùng chữ "Probability": ensemble score là robust z-score, có âm có
    dương, không phải xác suất [0,1].
  - Trục Y: **không hiện số** ở hai đầu. Chỉ vẽ **đường zero** + chiều cao tương đối, auto-scale theo
    percentile P1–P99 của **chính file đang xem** (tránh 1 outlier kéo giãn trục). Lý do bỏ số: ô này
    nhỏ, vai trò là nhìn nhanh; và z-score không có ý nghĩa lâm sàng tuyệt đối để đọc số.
- Có playhead (▼) đồng bộ với Panel EEG.
- **Chỉ để xem, không tương tác.** Click chỉ hoạt động trên Panel EEG.

### 6.4 Panel EEG

- **Cố định đúng 18 kênh chuẩn** của pipeline. Lọc bỏ mọi kênh phụ (EKG/EOG/Ref) nếu file gốc có —
  vd chb13/14 có thêm EKG, chb15 có thêm 8 kênh FC/CP-Ref. Lý do: mọi thứ hiển thị phải là dữ liệu thật
  sự đi vào tính toán.

**Toolbar** (trái → phải, xem `UI/B1a`):

| Nút | Chức năng |
|---|---|
| `⊲▷ [X] hr` | Độ dài cửa sổ hiển thị trên Panel EEG, **độc lập** với zoom 1 giờ của mini-timeline. Bấm số → popover trượt dọc 24hr → 1min (`UI/B1b`) |
| `⇕ [X] uV` | Thang biên độ, dropdown mức cố định 5/7/10/15/20/30 µV. Thuần frontend, không đụng backend |
| `⏮⏭ Select Range` | Bật chế độ tạo event thủ công (§6.6) |
| `lff 0.5 Hz` · `hff 60 Hz` · `60` | 3 filter khớp đúng bước preprocessing thật |

**Đã bỏ khỏi toolbar** (so với Persyst/wireframe gốc): nút **All** (kênh đã cố định, không cho chọn) và
nút **ar** (Artifact Reduction — pipeline không có bước tương ứng; giữ chỉ để "giống Persyst" là tính năng
không phản ánh gì thật). Cũng bỏ nút **Comment** trên toolbar vì đã có Comment gắn theo từng event.

**Toggle filter:** khi bật, sóng đã lọc nổi bật, sóng raw lùi làm nền mờ — **không ẩn hẳn raw**.

**Playhead:** chỉ click được trên Panel EEG. Click 1 điểm → playhead nhảy tới đó, mini-timeline đồng bộ.

**Thanh scrub dưới cùng:** có dropdown tốc độ phát `1x / 2x / 4x / 8x`, mặc định **1x**
*(mới so với v4, nơi tốc độ bị cố định)*. Dừng ở 8x vì cao hơn thì mắt không đọc được waveform nữa.

**Hàng "Event Time"** dưới cùng Panel EEG: block của các event trong tầm nhìn, nhãn ghi `Event N`
(**không** ghi `seizure N` — xem §7.2).

### 6.5 Panel Event

- **Filter 2 tầng lồng nhau:** tầng 1 `All / Human / AI`; tầng 2 chỉ xuất hiện khi chọn AI —
  `Accept / Reject / Uncertain / Unseen`. (Event Human tự confirm khi tạo nên không cần review.)
- **Số đếm:** dạng `x` khi filter là All hoặc Human; dạng `x/y` khi filter là nhãn con của AI
  (x = số khớp nhãn, y = tổng event AI trong file). "All" cộng gộp Human + AI.
- Mỗi dòng: `Event` (tên) / `Onset` / `Type` (icon AI hoặc icon người) / `▼` mở rộng tại chỗ.
- **Event AI mở rộng:** Onset / Offset / Duration (chỉ đọc) + 3 lựa chọn `Accept / Reject / Uncertain`
  + ô Comment + nút Save. **Không sửa được onset/offset của event AI** — muốn sửa thì Reject rồi tự tạo
  event mới bằng Select Range.
- **Event User-added mở rộng:** Onset / Offset / Duration + **Delete / Edit** + Comment + Save. Không có
  Accept/Reject/Uncertain.
- **Click 1 dòng event** → đồng bộ tức thì cả 3 panel còn lại: Panel EEG nhảy tới onset→offset,
  mini-timeline cập nhật playhead, Panel Attribution hiện dữ liệu của event đó.
  **Panel Event là nguồn điều khiển chính.**
- **Trạng thái rỗng:** file không có event AI nào → panel trống, vẫn thêm được event thủ công
  (`UI/B0a`). Wording: `No detected events in this file. You can still add an event manually with Select
  Range.` — **không** dùng `No seizure detected` (ngụ ý kết luận y khoa).

### 6.6 Tạo event thủ công (Select Range)

1. Bấm **Select Range** → bật chế độ đánh dấu.
2. Click điểm 1 trên grid EEG → đặt **onset**, hiện đường mốc dọc.
3. Di chuột sang phải → ô chữ nhật kéo dài theo con trỏ trong hàng "Event Time" (`UI/B3a`).
4. Click điểm 2 → chốt **offset** (`UI/B3b`).
5. Event mới **tự chèn đúng vị trí thời gian** trong danh sách (không phải thêm vào cuối), kèm icon
   người, Onset/Offset/Duration tự tính, không có Accept/Reject/Uncertain.
6. Mini-timeline thêm block mới tại vị trí tương ứng, màu khác block AI.
7. Alert ở header + Database tự động **+1**.

*Lưu ý đọc ảnh:* màu xám trong `UI/B3a` là nhãn **Unseen**, không phải hiệu ứng làm mờ khi đang tạo event.

### 6.7 Panel Channel Attribution

**Framing bắt buộc — đây là ràng buộc khoa học, không phải lựa chọn UI.** Theo
`docs/ATTRIBUTION_SPEC.md`, đây là **XAI cho nhánh reconstruction của GAE**. Nó **KHÔNG phải** localization
và **KHÔNG phải** SOZ. Kết quả đối chiếu nhãn hiện ở trạng thái **PROVISIONAL**.

- **Tiêu đề panel:** `Channel-level reconstruction anomaly — Event N`
  *(sửa từ "Channel contribute to ..." trong mock — cách nói cũ ngụ ý quan hệ nhân quả/định vị.)*
- **Hiển thị:** hình đầu đơn giản (vòng tròn + 18 vị trí điện cực hệ 10-20) làm nền, vẽ đè **18 đường
  thẳng nối 2 điện cực của mỗi kênh bipolar** (vd FP1↔F7 cho kênh `FP1-F7`), tô theo Score.
  - **Bắt buộc dùng đường nối, không dùng chấm tròn**: CHB-MIT là dữ liệu **bipolar**, mỗi kênh là hiệu
    điện thế giữa 2 điện cực, không phải giá trị tại 1 điểm. Chấm tròn sai bản chất dữ liệu.
  - Thang màu **teal**, không đỏ/vàng/xanh-lá — xem `SZSCAN_DESIGN_v2.md` §4.
- **Bảng dưới:** `Rank / Channel / Score / Status`. Rank cố định theo Score, không cho user sắp xếp lại.
  Status là segmented control `Accept | Reject` (loại trừ nhau như radio).
- Nút **Save** + **Clear all** ở cuối bảng.
- Đồng bộ theo event đang chọn, **kể cả event do user tự tạo** — attribution là số per-window tính từ mô
  hình, tổng hợp trên bất kỳ khoảng thời gian nào, không phụ thuộc event đó do AI hay người tạo.
- **Trạng thái rỗng:** chưa chọn event nào → placeholder `Select an event to view attribution`, không tự
  động hiện event đầu tiên.
- **Không** hiển thị metric đánh giá attribution (AUROC, khoảng tin cậy, p-value) trên UI.

---

## 7 · EXPORT

### 7.1 Phạm vi

**1 file `.txt` duy nhất cho toàn bộ subject**, gộp mọi file .edf con — giống hệt cấu trúc gốc
`chbXX-summary.txt` của CHB-MIT (vốn cũng gộp nhiều file trong 1 file text).

### 7.2 Quy tắc chữ "Event" vs "Seizure"

- **Trên UI khi đang review:** mọi thứ AI phát hiện gọi là **Event** / **Alert**. Không bao giờ gọi một
  phát hiện đơn lẻ là "seizure".
- **Hai nhãn được phép chứa chữ "Seizure" trên UI:** `Seizure Detection Score` và tiêu đề panel EEG —
  vì chúng chỉ **đầu ra của hệ thống nói chung**, không gán nhãn y khoa cho một mục cụ thể.
- **Trong file export:** giữ dòng `Number of Seizures in File: N` đúng quy ước CHB-MIT gốc (để đối chiếu
  máy), nhưng các mục con vẫn đánh số `Event 1`, `Event 2`… khớp đúng số hiệu bác sĩ đã thấy trên UI.
  Hai cách gọi cùng tồn tại là **có chủ đích**, không phải lỗi.

### 7.3 Cấu trúc

Giữ khung gốc CHB-MIT, chèn thông tin mới ngay sau mỗi event (xem `UI/Annotaiton (format_ ID-summary.txt).png`):

```
Data Sampling Rate: 256 Hz
Channels in EDF Files:
Channel 1: FP1-F7
...
Channel 18: CZ-PZ

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
    Comment: (nội dung nếu có)
    Channel Attribution (rank/channel/score/status):
      1  FP1-F7  3.5  Accept
      2  F7-T7   3.4  Reject
      ...

Event 2
    Source: Human
    Start Time: ...
```

**Thời gian trong export dùng giây tính từ đầu FILE** (giống annotation gốc CHB-MIT), **không** dùng
`HH:MM:SS` như trên UI — đây là file kỹ thuật để xử lý tiếp, không tối ưu cho đọc bằng mắt.

---

## 8 · VIỆC CÒN TREO — phải xử lý lúc build, không được đoán

| # | Việc | Cách xử lý |
|---|---|---|
| O1 | **Operating point của demo** (ngưỡng phát hiện event). Thủ tục FP-budget là label-free nên dùng được, nhưng **giá trị budget cụ thể** phải **đọc từ file** (`src/retrain/fp_budget_operating_point.py` + `docs/RESULTS_OF_RECORD_phaseB.md`) lúc build — **tuyệt đối không gõ lại từ trí nhớ** | đọc file |
| O2 | **Tham số PELT** (penalty, model, min_size) — lấy đúng từ `src/cpd_pipeline_v14.py`, không tự chọn lại | đọc file |
| ~~O3~~ | ~~robust-z của demo fit trên gì~~ — **ĐÓNG 2026-09-03**: `retrain_io.robust_z` đã fit trên toàn bộ window (dòng 56–60). Không phải divergence, không cần xử lý | đã đóng |
| O4 | **Subject nào dùng cho kịch bản upload live** — chọn theo số file thật, đo lúc dựng cache | đo |
| O4b | **Mức độ gắn cờ đoạn hậu-cơn** (§1.6b) — quan sát ở bước 1, quyết định có nói riêng trong slide bảo vệ hay không. Không chỉnh mô hình, không chỉnh ngưỡng để "sửa" | quan sát |
| O5 | **Gamma-AEC trong đường liên tục** — `dataprep/compute_gamma_aec.py` hiện chạy trên mảng đã tách; cần bản liên tục | viết mới trong `pipeline_demo.py` |

| O6 | **`evaluation_protocol.py` và `stat_validation.py` vừa được khôi phục về `src/`** (2026-09-03, tag `repo-deps-fixed`) sau khi bị archive nhầm dù vẫn đang được import. `fp_budget_operating_point.py` phụ thuộc chuỗi này — kiểm tra `import` chạy được trước khi lấy tham số cho O1 | 1 lệnh |

Không mục nào chặn việc bắt đầu dựng frontend.

---

*Hết SZSCAN_SPEC_v5.md. Thay thế hoàn toàn `WEB_DEMO_SPEC_v4.md` và `WEB_DEMO_CONTEXT_BOUNDARY.md`.*
