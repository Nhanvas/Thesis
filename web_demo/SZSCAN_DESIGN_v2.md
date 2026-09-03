# SZSCAN_DESIGN_v2.md — hệ thống thị giác (bản chốt để build)

**Trạng thái: KHÓA.** Thay thế hoàn toàn `WEB_DEMO_DESIGN_SYSTEM.md` (v1 → `docs/archive/demo_v4/`).

**Thẩm quyền:** `UI/` (PNG bản chốt) thắng file này về mọi thứ nhìn thấy được. File này ghi lại **giá trị
đo được** từ chính bộ PNG đó + các quy tắc ngữ nghĩa mà ảnh tĩnh không thể hiện được.
`SZSCAN_SPEC_v5.md` thắng về hành vi/logic.

**Nguồn giá trị:** các hex dưới đây được **đọc trực tiếp bằng pixel sampling từ PNG bản chốt**
(2026-09-03), không phải đoán bằng mắt và không kế thừa từ v1. Chỗ nào v1 khác với ảnh, **ảnh thắng** và
được ghi chú rõ.

---

## 0 · Nguyên tắc

1. **EEG là nội dung trung tâm.** Chrome không cạnh tranh với waveform.
2. **Ba trục thông tin độc lập, không trộn:** nguồn gốc event (AI/Human) · review status
   (Accept/Reject/Uncertain/Unseen) · trạng thái tương tác (đang chọn/playhead).
3. **Không truyền đạt ý nghĩa chỉ bằng màu.** Luôn kèm text/icon — quan trọng cho colorblind và cho máy
   chiếu (máy chiếu làm lệch màu).
4. **Không over-claim bằng màu.** Alert chưa review **không** mặc định đỏ. Đỏ chỉ dành cho review status
   `Reject` và lỗi hệ thống.
5. **Attribution không dùng thang nhiệt đỏ.** Đó là interpretability, không phải mức độ nguy hiểm/SOZ.

---

## 1 · Token nền & thương hiệu (đo từ PNG)

| Vai trò | Hex | Ghi chú |
|---|---|---|
| Header gradient | `#624C8A` → `#10182B` | trái sang phải, dùng ở cả Log in / Database / Analysis |
| Brand violet (nút primary) | `#776399` | ⚠ **khác v1** — v1 ghi `#7C3AED`, ảnh thật muted hơn hẳn |
| Nền trang | `#FFFFFF` | ⚠ **khác v1** — v1 ghi `#F8FAFC` |
| Canvas EEG | `#FEFBEF` | **token mới**, nền kem kiểu máy đọc EEG |
| Footer bar | `#0F172A` | chữ trắng, disclaimer thường trực |
| Surface (card/panel/table) | `#FFFFFF` | |
| Border | `#E2E8F0` | viền card, divider |
| Border strong | `#CBD5E1` | grid chính |
| Text primary | `#0F172A` | |
| Text secondary | `#475569` | |
| Text muted | `#64748B` | hint, empty-state |

### Violet có HAI vai trò tách biệt — đọc kỹ

v1 quy định violet **chỉ** mang nghĩa "đang tương tác". UI thật dùng violet cho cả header và nút primary.
Chốt: **tách thành 2 vai trò, không nhập nhằng vì chúng không bao giờ xuất hiện cùng ngữ cảnh.**

| Vai trò | Màu | Xuất hiện ở |
|---|---|---|
| **Chrome / brand** | `#776399`, header gradient | Ngoài canvas nội dung: header, nút Create new / Save / Log in |
| **Tương tác** | violet bão hòa hơn, dùng cho playhead + viền "đang chọn" | Trong canvas nội dung: playhead, viền event đang chọn, channel đang hover |

**Blue `#2563EB` giữ độc quyền cho một nghĩa duy nhất: event nguồn Human.** Không dùng blue cho nút.

---

## 2 · Event & review status (3 trục)

### Trục 1 — nguồn gốc

| Nguồn | Hex | Icon |
|---|---|---|
| AI-detected | `#334155` charcoal | icon "AI" |
| Human-added | `#2563EB` blue | icon người |

### Trục 2 — review status (chỉ áp cho event AI)

| Status | Màu | Nền nhạt |
|---|---|---|
| Accept | `#16A34A` | `#F0FDF4` |
| Reject | `#DC2626` | `#FEF2F2` |
| Uncertain | `#D97706` | `#FFFBEB` |
| Unseen | `#94A3B8` | `#F8FAFC` |

### Trục 3 — tương tác

Playhead · viền event đang chọn · channel đang hover trên Attribution → **violet bão hòa**.

**Quy tắc kết hợp:** 1 event AI đã Accept = thanh dọc trái xanh lá (status) + icon "AI" (nguồn) + nền card
xanh lá rất nhạt. Nếu đang được chọn thì **thêm** viền violet, **không thay thế** thanh dọc. Ba trục luôn
hiển thị đồng thời, không trục nào ghi đè trục nào.

**Trên Event Panel:** thanh dọc ~4–5 px cạnh trái mỗi dòng. Nền dòng chỉ tô rất nhạt, tránh "loang lổ".

**Trên mini-timeline và hàng Event Time:** AI chưa review = charcoal đặc · Human = blue đặc ·
Accept = green opacity ~75 % · Reject = red opacity ~55 % + gạch chéo nhẹ (để không chỉ dựa vào màu) ·
Uncertain = amber opacity ~75 % · đang chọn = thêm viền violet, không đổi màu nền gốc.

**Khi đang xem 1 event:** các event khác giảm còn opacity ~40 % (không đổi màu), event đang chọn giữ
nguyên độ đậm + viền violet.

---

## 3 · EEG waveform

| Đối tượng | Giá trị |
|---|---|
| Nền canvas | `#FEFBEF` |
| Raw EEG (filter tắt, hoặc làm nền khi filter bật) | `#64748B`, opacity 50 % |
| Filtered EEG (nổi bật khi bật lff/hff/60) | `#0F172A`, opacity 100 % |
| Grid phụ | `#E2E8F0` |
| Grid chính | `#CBD5E1` |
| Playhead | violet |
| Overlay nền event AI | `#334155`, opacity 8–10 % |
| Overlay nền event Human | `#2563EB`, opacity 8–10 % |

**Không dùng:** màu đỏ cho waveform bất thường (không có ngưỡng lâm sàng nào biện minh) · màu riêng cho
từng kênh trong 18 kênh (rainbow gây khó đọc, không thêm thông tin) · gradient mạnh trong waveform ·
nền đen toàn trang.

---

## 4 · Channel Attribution — thang teal

| Mức | Hex | Ghi chú |
|---|---|---|
| Thấp | `#CBD5E1` | slate trung tính |
| Trung bình | `#2DD4BF` | teal-400 |
| Cao | `#0F766E` | teal-700 |
| Đang hover/chọn | violet | |
| Channel đã Reject | giữ đường, opacity ~35 % hoặc nét đứt | |

Colorbar trên đầu người: `linear-gradient(to right, #CBD5E1, #2DD4BF, #0F766E)`.

**Vì sao teal, và vì sao chỉ 3 mốc:**
- Không dùng **đỏ-vàng-xanh lá**: ngụ ý mức độ nguy hiểm/SOZ — sai bản chất, attribution là
  interpretability (`docs/ATTRIBUTION_SPEC.md`).
- Không dùng **blue**: chìm trên nền trắng, và blue đã có chủ (event Human).
- Không dùng **tím**: sẽ đụng trực tiếp với "đang hover" — một channel điểm cao sẽ không phân biệt được
  với channel đang được hover.
- Teal là hue duy nhất trong bảng màu hiện tại **chưa bị gán nghĩa nào**.
- 3 mốc là đủ cho biểu diễn bằng đường mảnh; nhiều mốc hơn thì mắt không phân biệt được.

**Interaction 2 chiều** (hover dòng bảng → sáng đường tương ứng và ngược lại): tăng UX, **không bắt buộc**.
Bỏ được nếu gấp thời gian.

---

## 5 · Database

| Thành phần | Style |
|---|---|
| Header bảng | nền `#F1F5F9` |
| Row mặc định / hover | trắng / `#F8FAFC` |
| Row đang chọn | nền `#EFF6FF`, viền trái blue |
| Dòng subject | `font-weight: 600` |
| Dòng file con | thụt lề nhẹ, text secondary |

**Status badge:** `View` → chữ `#475569`, icon vòng tròn rỗng · `Viewing (x/N)` → `#B45309`, icon nửa đầy
· `Viewed` → `#15803D`, icon check.

**Alert:** hiển thị **màu chữ trung tính** (`#0F172A`), không amber, không đỏ.
⚠ **Khác v1** — v1 quy định amber khi > 0. Ảnh thật để đen trơn; rule cũ sinh ra để cấm **đỏ**, và đen
trung tính đã thỏa mục đích đó, đồng thời tránh nhiễu khi mọi dòng đều amber.

---

## 6 · Typography

| Vai trò | Font |
|---|---|
| UI chung (label, button, table) | Inter |
| Dữ liệu kỹ thuật (tên file, tên kênh, timestamp, score) | IBM Plex Mono |

Monospace cho dữ liệu kỹ thuật là **bắt buộc**: bảng số liệu phải thẳng hàng, và `FP1-F7` vs `FP1-F3`
không được nhìn nhầm. Cả hai font đều miễn phí trên Google Fonts.

**Cỡ chữ:** page title 20–24 · section title 15–16 · body 13–14 · table 12–13 · timestamp 12 ·
button 13–14 · badge 11–12 (px).

---

## 7 · Spacing

Bội số 4 px. Page padding 24 · khoảng cách giữa panel 16 · panel padding 16–20 · khoảng cách nhóm toolbar
12–16 · chiều cao dòng event 48–56 · dòng event đã mở rộng 140–180.

Màn Analysis **được phép dài và cuộn dọc**. Không ép mọi panel vừa 1 viewport; ưu tiên khoảng thở.

---

## 8 · Wording — bảng tra nhanh (chống over-claim)

| Tình huống | Dùng | KHÔNG dùng |
|---|---|---|
| File không có event AI nào | `No detected events in this file. You can still add an event manually with Select Range.` | `No seizure detected` |
| Event AI chưa review | badge `Unseen`, màu trung tính | màu đỏ |
| Đang chạy Process | `Processing subject — combining files and detecting change points...` | % giả |
| Upload file lỗi | `File rejected — unsupported format or channel configuration.` | `Upload failed` |
| Subject ngoài allowlist | `This demo is restricted to the held-out test subjects.` | im lặng bỏ qua |
| Tiêu đề panel Attribution | `Channel-level reconstruction anomaly — Event N` | `Channel contribute to ...` |
| Nhãn block trên hàng Event Time | `Event N` | `seizure N` |
| Hàng thứ 2 mini-timeline | `Detections` | `Seizure Detections` |
| Footer mọi màn (trừ Log in) | `SzScan is an AI-assisted tool designed to support clinicians, not replace them.` | — |

---

## 9 · Design tokens — điểm khởi đầu khi code

```css
:root {
  /* nền & chrome */
  --color-bg:              #FFFFFF;
  --color-surface:         #FFFFFF;
  --color-eeg-canvas:      #FEFBEF;
  --color-footer:          #0F172A;
  --color-border:          #E2E8F0;
  --color-border-strong:   #CBD5E1;

  --header-gradient:       linear-gradient(90deg, #624C8A 0%, #10182B 100%);
  --color-brand:           #776399;   /* chrome: header, nút primary */
  --color-interaction:     #7C3AED;   /* playhead + đang chọn (chỉ trong canvas nội dung) */

  --color-text:            #0F172A;
  --color-text-secondary:  #475569;
  --color-text-muted:      #64748B;

  /* nguồn gốc event */
  --color-ai:              #334155;
  --color-human:           #2563EB;   /* độc quyền cho event Human, KHÔNG dùng cho nút */

  /* review status */
  --color-accept:          #16A34A;  --color-accept-bg:    #F0FDF4;
  --color-reject:          #DC2626;  --color-reject-bg:    #FEF2F2;
  --color-uncertain:       #D97706;  --color-uncertain-bg: #FFFBEB;
  --color-unseen:          #94A3B8;

  /* EEG */
  --color-eeg-raw:         #64748B;
  --color-eeg-filtered:    #0F172A;
  --color-grid:            #E2E8F0;
  --color-grid-strong:     #CBD5E1;

  /* attribution (teal) */
  --color-attr-low:        #CBD5E1;
  --color-attr-mid:        #2DD4BF;
  --color-attr-high:       #0F766E;

  /* layout */
  --radius-panel:          10px;
  --radius-control:        6px;
  --shadow-panel:          0 1px 3px rgb(15 23 42 / 8%);

  --font-ui:               'Inter', sans-serif;
  --font-mono:             'IBM Plex Mono', monospace;
}
```

---

## 10 · Những gì đã đổi so với v1 (để không dùng nhầm)

| Hạng mục | v1 | v2 (file này) | Vì sao |
|---|---|---|---|
| Nền trang | `#F8FAFC` | `#FFFFFF` | đo từ ảnh chốt |
| Nút primary | blue `#2563EB` | violet `#776399` | đo từ ảnh chốt |
| Nền canvas EEG | (không có token) | `#FEFBEF` | đo từ ảnh chốt; kem là quy ước máy đọc EEG, tương phản tốt hơn cho nét sẫm |
| Vai trò violet | chỉ "đang tương tác" | tách chrome / tương tác | ảnh dùng violet làm brand; hai vai trò không cùng ngữ cảnh nên không nhập nhằng |
| Attribution | blue nhạt → blue đậm | teal 3 mốc | blue chìm trên nền trắng + blue đã có chủ |
| Alert | amber khi > 0 | trung tính | ảnh chốt; rule cũ chỉ nhằm cấm đỏ |
| Trục Y Detection Score | auto-scale P1–P99 (có số) | auto-scale P1–P99, **không hiện số**, chỉ zero-line | ô nhỏ, vai trò nhìn nhanh; z-score không có ý nghĩa tuyệt đối để đọc số |
| Header | (không mô tả) | gradient `#624C8A → #10182B` | đo từ ảnh chốt |
| Footer | (không có) | bar `#0F172A` thường trực | quyết định minh bạch của tác giả |

---

*Hết SZSCAN_DESIGN_v2.md.*
