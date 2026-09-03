# WEB_DEMO_DESIGN_SYSTEM.md — SzScan Visual Design System (v1, chốt)

**Trạng thái: KHÓA để build.** File này định nghĩa bảng màu, typography, spacing, và các quy tắc thị giác
cho SzScan. Bổ sung cho `WEB_DEMO_SPEC_v4.md` (hành vi/logic) — file đó định nghĩa CÁI GÌ xảy ra, file này
định nghĩa TRÔNG NHƯ THẾ NÀO. Nếu 2 file mâu thuẫn, `WEB_DEMO_SPEC_v4.md` thắng về mặt hành vi/logic; file
này thắng về mặt màu sắc/thị giác.

**Nguồn:** tổng hợp từ tư vấn Perplexity (định hướng bảng màu tổng thể, tốt) + hiệu đính lại theo đúng
`WEB_DEMO_SPEC_v4.md` đã chốt (Perplexity không có context đầy đủ về wireframe/spec nên có vài điểm lệch
hoặc đề xuất tính năng mới ngoài scope — đã sửa, ghi chú rõ bên dưới).

---

## 0. NGUYÊN TẮC CHỈ ĐẠO (giữ nguyên tinh thần, đã hiệu đính)

1. **EEG là nội dung trung tâm.** UI không cạnh tranh với waveform — nền/card/border tiết chế, màu đậm chỉ
   dành cho event, selection, và trạng thái quan trọng.
2. **Không dùng tím làm màu cảnh báo/trạng thái.** Tím chỉ dùng cho logo/brand accent và cho **playhead +
   đối tượng đang được chọn** (event đang xem, channel đang hover trên Attribution) — đây là 1 vùng ngữ
   nghĩa DUY NHẤT ("đang tương tác/đang focus"), tách biệt hoàn toàn khỏi review status (Accept/Reject/
   Uncertain dùng xanh lá/đỏ/cam, không liên quan tím).
3. **AI vs Human phải phân biệt màu NGAY LẬP TỨC, tách biệt hoàn toàn khỏi review status.** Đây là 2 trục
   thông tin độc lập (nguồn gốc event vs. đánh giá của bác sĩ) — không được trộn. Một event Human không
   mặc định "đúng"/"xanh lá"; nó vẫn cần hiển thị màu nguồn gốc (blue) tách biệt với màu trạng thái review.
4. **Màu trạng thái nhất quán ở mọi panel.** Event Accept phải cùng 1 màu ở Event Panel, Timeline, và vùng
   Event Time dưới EEG.
5. **Không dùng màu đơn độc để truyền đạt ý nghĩa.** Luôn kết hợp màu với text/icon/label — đặc biệt quan
   trọng cho colorblind-safety và cho việc tránh hiểu lầm khi trình chiếu (máy chiếu có thể làm sai lệch
   màu sắc).
6. **Không over-claim qua màu sắc.** "Alert" (số event chờ review) không mặc định đỏ — đỏ chỉ dành cho
   review status "Reject" hoặc lỗi hệ thống. Một alert chưa review không đồng nghĩa "chắc chắn có seizure".

---

## 1. BẢNG MÀU — NỀN & THƯƠNG HIỆU

| Vai trò | Tên | Hex | Dùng ở đâu |
|---|---|---|---|
| Primary | SzScan Blue | `#2563EB` | Nút hành động chính (Process, Save, Open), link, Human-event |
| Primary hover | Blue Dark | `#1D4ED8` | Hover/focus của nút primary |
| Brand accent | SzScan Violet | `#7C3AED` | Logo, playhead, "đang được chọn" (event/channel) — KHÔNG dùng cho status |
| App background | Slate 50 | `#F8FAFC` | Nền toàn trang (Database + Analysis) |
| Surface | White | `#FFFFFF` | Card, panel, table, popover |
| Border | Slate 200 | `#E2E8F0` | Viền card, divider, grid EEG (đường phụ) |
| Border strong | Slate 300 | `#CBD5E1` | Grid EEG (đường chính, mỗi giờ/major gridline) |
| Text primary | Slate 900 | `#0F172A` | Tiêu đề, dữ liệu chính, tên kênh |
| Text secondary | Slate 600 | `#475569` | Label, metadata, Memo |
| Text muted | Slate 500 | `#64748B` | Hint, timestamp phụ, empty-state text |

**Tỷ lệ sử dụng đề xuất:** 70–75% trắng/slate nhạt, 15–20% text/border xám, 5–10% blue/violet/status-color.
Không để đỏ/cam/tím chiếm diện tích lớn trên 1 màn hình phân tích EEG.

---

## 2. BẢNG MÀU — EVENT & REVIEW STATUS (2 trục độc lập)

### Trục 1 — Nguồn gốc event (AI vs Human)

| Nguồn | Màu | Hex | Icon |
|---|---|---|---|
| AI-detected | Charcoal | `#334155` | icon "AI" |
| Human-added | Blue | `#2563EB` | icon người |

### Trục 2 — Review status (chỉ áp dụng cho AI event — Human tự confirm khi tạo, không có 3 nhãn này)

| Status | Màu | Hex | Background nhạt (card) |
|---|---|---|---|
| Accept | Green | `#16A34A` | `#F0FDF4` |
| Reject | Red | `#DC2626` | `#FEF2F2` |
| Uncertain | Amber | `#D97706` | `#FFFBEB` |
| Unseen (chưa xem) | Neutral | `#94A3B8` | `#F8FAFC` |

### Trục 3 — Tương tác (playhead + đang chọn — 1 vùng ngữ nghĩa, dùng tím)

| Đối tượng | Màu | Hex |
|---|---|---|
| Playhead (đường dọc vị trí đang xem) | Violet | `#7C3AED` |
| Event đang được chọn (viền/outline) | Violet | `#7C3AED` |
| Channel đang hover/chọn trên Attribution | Violet | `#7C3AED` |

**Quy tắc kết hợp 3 trục:** 1 event AI đã Accept hiển thị = **thanh dọc bên trái màu green** (trạng thái)
+ **icon "AI"** (nguồn gốc) + **background card xanh lá rất nhạt**. Nếu đang được chọn, THÊM viền ngoài
tím (không thay thế thanh dọc green). 3 trục luôn hiển thị đồng thời, không trục nào ghi đè trục nào.

### Áp dụng trên Event Panel

```
| green  Seizure 1   15:16:35   [AI icon]      <- Accept, AI
| red    Seizure 2   16:19:24   [AI icon]      <- Reject, AI
| blue   Seizure 3   16:20:02   [person icon]  <- Human (không có status riêng)
| amber  Seizure 4   16:16:01   [AI icon]      <- Uncertain, AI
```

Thanh dọc rộng ~4–5px ở cạnh trái mỗi dòng event. Nền dòng event chỉ tô màu RẤT nhạt (theo bảng trên),
không tô đậm toàn bộ dòng — tránh làm Event Panel "loang lổ" khi có nhiều event.

### Áp dụng trên Panel Timeline (hàng "Seizure Detections") và vùng "Event Time" dưới EEG

- AI-detected, chưa review (Unseen): block màu charcoal `#334155`, đặc.
- Human-added: block màu blue `#2563EB`, đặc.
- Đã Accept: block màu green, opacity ~75%.
- Đã Reject: block màu red, opacity ~55%, thêm gạch chéo nhẹ (pattern) để không chỉ dựa vào màu.
- Uncertain: block màu amber, opacity ~75%.
- Event đang được chọn: thêm viền ngoài tím `#7C3AED` (không đổi màu nền gốc).

---

## 3. EEG WAVEFORM

| Đối tượng | Màu | Hex/Opacity |
|---|---|---|
| Raw EEG (khi filter tắt hoặc làm nền khi filter bật) | Slate | `#64748B`, opacity 50% |
| Filtered EEG (nổi bật khi bật lff/hff/60) | Navy | `#0F172A` hoặc `#1D4ED8`, opacity 100% |
| Grid phụ (mỗi giây) | Slate 200 | `#E2E8F0` |
| Grid chính (mỗi phút/mốc lớn) | Slate 300 | `#CBD5E1` |
| Playhead | Violet | `#7C3AED` |
| Vùng nền event AI (overlay dưới sóng) | Charcoal | `#334155`, opacity 8–10% |
| Vùng nền event Human (overlay dưới sóng) | Blue | `#2563EB`, opacity 8–10% |

**Quy tắc bật/tắt filter (đã chốt ở spec v4):** khi bật lff/hff/60, sóng filtered hiển thị nổi bật (navy,
opacity 100%), sóng raw lùi làm nền mờ (opacity 50%) — KHÔNG ẩn hẳn raw.

**Chế độ "đang xem 1 event" (MỚI, đã chốt bổ sung trong phiên thiết kế màu):** khi user click chọn 1 event
ở Event Panel, các event KHÁC trên Panel Timeline / vùng Event Time giảm còn opacity ~40% (không đổi màu,
chỉ giảm độ nổi bật), còn event đang chọn giữ nguyên độ đậm + viền tím. Đây là tính năng bổ sung ngoài
`WEB_DEMO_SPEC_v4.md` gốc — ghi nhận vào spec khi build.

**Không dùng:** màu đỏ cho waveform bất thường (không có threshold lâm sàng nào biện minh việc này); màu
riêng cho từng kênh trong 18 kênh (rainbow chart gây khó đọc, không phản ánh gì thêm); gradient mạnh trong
waveform; nền đen toàn trang (không hợp với 1 giao diện web sáng, nhiều bảng dữ liệu như Database).

---

## 4. "SEIZURE PROBABILITY" → ĐỔI TÊN THÀNH "SEIZURE DETECTION SCORE"

**Quyết định đã chốt (khác với nhãn cũ trên wireframe):** hàng đầu tiên của Panel Timeline đổi tên từ
**"Seizure Probability"** thành **"Seizure Detection Score"** (hoặc tên tương đương không dùng chữ
"Probability"). Lý do: ensemble score trong pipeline là **robust z-score** (median/MAD normalize), có thể
âm hoặc dương, KHÔNG phải xác suất chuẩn hóa [0,1]. Dùng chữ "Probability" sẽ ngụ ý sai bản chất số liệu
và có nguy cơ bị hội đồng bắt lỗi over-claim lúc bảo vệ.

Áp dụng thêm cho việc vẽ line chart này (bổ sung mục "việc còn treo" §6.1 của spec v4):
- Trục Y auto-scale theo percentile P1–P99 của CHÍNH FILE đang xem (tránh 1 outlier kéo giãn toàn trục).
- Có đường zero (score có thể âm).
- Dùng 1 màu line duy nhất (navy hoặc blue đậm), KHÔNG dùng gradient xanh→vàng→đỏ theo giá trị (chưa có
  threshold lâm sàng nào được kiểm định để biện minh việc tô màu theo mức độ "nguy hiểm").

---

## 5. CHANNEL ATTRIBUTION (đường nối bipolar — đã chốt Phương án A ở spec v4)

| Mức Score | Màu đường nối | Hex |
|---|---|---|
| Thấp | Slate nhạt | `#CBD5E1` |
| Trung bình | Blue nhạt | `#60A5FA` |
| Cao | Blue đậm | `#1D4ED8` |
| Đang hover/chọn (bảng ↔ sơ đồ đồng bộ 2 chiều) | Violet | `#7C3AED` |
| Channel đã Reject (ở bảng Status) | Giữ nguyên đường, opacity ~35% hoặc nét đứt | — |

**Interaction 2 chiều (tùy chọn, tăng UX — không bắt buộc cho bản demo tối giản):** hover 1 dòng trong bảng
Rank/Channel/Score → đường nối tương ứng trên sơ đồ sáng lên (tím), các đường khác giảm opacity; hover
ngược lại trên sơ đồ cũng highlight đúng dòng bảng. Đây là bổ sung UX, có thể để Future Work nếu thời gian
build gấp — không phải yêu cầu bắt buộc của `WEB_DEMO_SPEC_v4.md`.

**Không dùng:** gradient đỏ cho "channel quan trọng" (ngụ ý sai — attribution là interpretability, không
phải mức độ nguy hiểm/SOZ, đúng theo giới hạn đã ghi trong `ATTRIBUTION_SPEC.md` của thesis).

---

## 6. TRANG DATABASE

| Thành phần | Màu/style |
|---|---|
| Header bảng | nền `#F1F5F9` |
| Row mặc định | trắng |
| Row hover | `#F8FAFC` |
| Row đang chọn | nền `#EFF6FF`, viền trái blue `#2563EB` |
| Dòng subject (cha) | `font-weight: 600` |
| Dòng file (con) | thụt lề nhẹ, text màu secondary |

### Status badge (3 mức, theo §3.2 spec v4)

| Status | Text color | Background |
|---|---|---|
| `View` | `#475569` | `#F1F5F9` |
| `Viewing` / `Viewing (x/N)` | `#B45309` | `#FFFBEB` |
| `Viewed` | `#15803D` | `#F0FDF4` |

### Alert (theo công thức §3.3 spec v4 — KHÔNG mặc định đỏ)

| Điều kiện | Màu |
|---|---|
| Alert = 0 | Slate muted `#64748B` |
| Alert > 0, chưa review nhiều | Amber `#D97706` |
| Alert cao | Amber đậm hơn — KHÔNG chuyển sang đỏ (đỏ chỉ dành cho Reject/lỗi) |

---

## 7. TYPOGRAPHY

| Vai trò | Font | Ghi chú |
|---|---|---|
| UI chung (label, button, table text) | Inter (hoặc IBM Plex Sans / Source Sans 3) | Sans-serif dễ đọc, phổ biến, có sẵn trên Google Fonts |
| Dữ liệu kỹ thuật (tên file, tên kênh, timestamp, score) | IBM Plex Mono (hoặc bất kỳ monospace nào) | Độ rộng ký tự cố định giúp bảng số liệu thẳng hàng, dễ đối chiếu — quan trọng cho `FP1-F7` vs `FP1-F3` không bị nhầm |

### Kích thước

| Thành phần | Size |
|---|---|
| Page title | 20–24px |
| Section title (VD "Seizure detection", "Channel contribute to...") | 15–16px |
| Body text | 13–14px |
| Table text (Database, Rank/Channel/Score) | 12–13px |
| Timestamp / dữ liệu kỹ thuật | 12px |
| Button label | 13–14px |
| Status badge | 11–12px |

---

## 8. SPACING

Hệ thống dựa trên bội số 4px.

| Vị trí | Giá trị |
|---|---|
| Page padding | 24px |
| Khoảng cách giữa panel (Timeline/EEG/Event/Attribution) | 16px |
| Panel padding (nội dung bên trong 1 panel) | 16–20px |
| Khoảng cách giữa nhóm toolbar (Navigation/Display/Annotation) | 12–16px |
| Chiều cao 1 dòng event (Event Panel, chưa mở rộng) | 48–56px |
| Chiều cao event đã mở rộng (hiện Onset/Offset/Comment/Save) | 140–180px tùy nội dung |

**Lưu ý:** trang Analysis được phép dài và cuộn dọc (đã xác nhận ở bước 3-4 của phiên thiết kế UX) — không
cần ép mọi panel vừa 1 viewport. Ưu tiên khoảng thở, không nén layout.

---

## 9. TOOLBAR PANEL EEG — SẮP XẾP LẠI THEO NHÓM CHỨC NĂNG

**Cải tiến so với wireframe (đề xuất mới, cần xác nhận riêng nếu áp dụng — KHÔNG có trong `WEB_DEMO_SPEC_v4.md` gốc):**
chia toolbar thành 3 nhóm trực quan thay vì xếp ngang 1 hàng đều nhau:

```
[Window: 1 hr]  [Amplitude: 7 uV]   |   [lff 0.5Hz] [hff 60Hz] [notch 60Hz]   |   [Select Range]
   Navigation                              Display filters                        Annotation
```

- Nhóm Navigation (trái): độ dài cửa sổ + biên độ.
- Nhóm Display (giữa): 3 filter thật khớp pipeline (đã chốt bỏ "ar"/"All").
- Nhóm Annotation (phải): Select Range — dùng màu primary blue để nổi bật vì đây là hành động tạo dữ liệu
  mới (khác các nút xem/điều chỉnh hiển thị bên trái).

**Trạng thái "đang Select Range" (đề xuất mới):** khi bấm Select Range, nút chuyển nền blue đậm + hiện dòng
hướng dẫn ngắn ngay dưới toolbar (VD: "Click để đặt điểm onset, sau đó click lần nữa để đặt offset") kèm
nút "Cancel" nhỏ. Đây là cải tiến UX giúp người dùng (đặc biệt hội đồng lần đầu thấy) hiểu ngay thao tác,
không bắt buộc nhưng khuyến khích nếu thời gian cho phép.

---

## 10. CÁC TRẠNG THÁI ĐẶC BIỆT — WORDING (tránh over-claim)

| Tình huống | Wording đề xuất | KHÔNG dùng |
|---|---|---|
| File không có event AI nào | "No detected events in this file. You can still add an event manually with Select Range." | "No seizure detected" (ngụ ý kết luận y khoa) |
| Event AI chưa review | Badge "Unseen", màu neutral/amber nhạt | Màu đỏ (gây cảm giác báo động giả) |
| Đang chạy Process (CPD) | "Processing subject — combining files and detecting change points..." | Progress % giả (backend không có cách tính % chính xác theo từng bước nhỏ) |
| Upload file lỗi | "File rejected — unsupported format or channel configuration." | "Upload failed" (không rõ lỗi ở đâu) |

---

## 11. DESIGN TOKENS (CSS variables — điểm khởi đầu khi code)

```css
:root {
  /* nền & brand */
  --color-bg: #F8FAFC;
  --color-surface: #FFFFFF;
  --color-border: #E2E8F0;
  --color-border-strong: #CBD5E1;

  --color-text: #0F172A;
  --color-text-secondary: #475569;
  --color-text-muted: #64748B;

  --color-primary: #2563EB;
  --color-primary-hover: #1D4ED8;
  --color-brand-violet: #7C3AED;   /* playhead + "đang chọn" — KHÔNG dùng cho status */

  /* nguồn gốc event */
  --color-ai: #334155;
  --color-human: #2563EB;

  /* review status */
  --color-accept: #16A34A;
  --color-accept-bg: #F0FDF4;
  --color-reject: #DC2626;
  --color-reject-bg: #FEF2F2;
  --color-uncertain: #D97706;
  --color-uncertain-bg: #FFFBEB;
  --color-unseen: #94A3B8;

  /* EEG waveform */
  --color-eeg-raw: #64748B;
  --color-eeg-filtered: #1D4ED8;
  --color-grid: #E2E8F0;
  --color-grid-strong: #CBD5E1;
  --color-playhead: #7C3AED;

  /* attribution */
  --color-attr-low: #CBD5E1;
  --color-attr-mid: #60A5FA;
  --color-attr-high: #1D4ED8;
  --color-attr-selected: #7C3AED;

  /* layout */
  --radius-panel: 10px;
  --radius-control: 6px;
  --shadow-panel: 0 1px 3px rgb(15 23 42 / 8%);

  /* typography */
  --font-ui: 'Inter', sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
}
```

---

## 12. TÓM TẮT — NHỮNG GÌ ĐÃ SỬA SO VỚI ĐỀ XUẤT GỐC CỦA PERPLEXITY

Perplexity tư vấn tốt về định hướng tổng thể (bảng màu, tránh tím-làm-cảnh-báo, AI/Human tách biệt review
status) nhưng thiếu context về wireframe/spec đã chốt. Các điểm đã hiệu đính:

| Đề xuất gốc Perplexity | Vấn đề | Đã sửa thành |
|---|---|---|
| Playhead = tím, Selected = tím (không giải thích rõ có phải cùng 1 khái niệm không) | Mơ hồ, đọc như 2 quyết định tách rời gây rối | Xác nhận rõ: đây là 1 trục ngữ nghĩa DUY NHẤT ("đang tương tác"), cùng dùng tím — đã xác nhận với tác giả |
| Toolbar gợi ý "Window \| Amplitude" ngầm định vẫn có nút All/ar | Không biết 2 nút này đã bị loại bỏ khỏi `WEB_DEMO_SPEC_v4.md` | Toolbar chỉ còn đúng các control đã chốt: Window, Amplitude, Select Range, lff/hff/notch |
| Đề xuất "2 chế độ hiển thị EEG" như 1 given | Đây thực chất là tính năng MỚI ngoài spec gốc | Đã xác nhận với tác giả là tính năng bổ sung, ghi rõ vào §3 để backend/frontend biết đây là phần thêm |
| Không nhắc gì đến quy tắc "Event vs Seizure" trong export | Thiếu — đây là quy tắc quan trọng đã chốt riêng trong `WEB_DEMO_SPEC_v4.md` §5.2 | Không cần sửa màu (export là văn bản thuần túy, không có màu), nhưng ghi chú tránh nhầm lẫn khi thiết kế toast/label liên quan "Seizure" xuất hiện ở đâu trên UI (chỉ ở Export, không ở màn hình review) |
| Interaction 2 chiều hover bảng↔sơ đồ Attribution | Trình bày như bắt buộc | Đánh dấu là tùy chọn/Future Work nếu gấp thời gian |
